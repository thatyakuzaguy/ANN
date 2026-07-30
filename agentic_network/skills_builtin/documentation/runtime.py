"""Documentation lookup skill runtime.

This MVP performs constrained HTTP lookups for documentation pages only after
the skill sandbox grants the `network` permission. It never executes code,
spawns shells, installs dependencies, or writes outside its skill workspace.
"""

from __future__ import annotations

import html
import ipaddress
import json
import re
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import quote_plus, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from agentic_network.skills.sandbox import validate_skill_artifact_directory, validate_workspace_path
from agentic_network.skills.redaction import redact_sensitive_text


DEFAULT_TIMEOUT_SECONDS = 8
USER_AGENT = "ANN-DocumentationSkill/10.3 local-first"
MAX_REDIRECTS = 3
ALLOWED_ARTIFACT_NAMES = frozenset(
    {
        "audit.log",
        "lookup_request.json",
        "lookup_result.json",
        "result_summary.md",
        "sources.json",
    }
)


@dataclass(frozen=True)
class DocumentationLookupResult:
    """Documentation lookup payload returned by the builtin skill."""

    status: str
    query: str
    sources: list[dict[str, str]]
    summary: str
    citations: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "query": self.query,
            "sources": self.sources,
            "summary": self.summary,
            "citations": self.citations,
            "errors": self.errors,
        }


def documentation_lookup(payload: dict[str, Any], workspace: str | Path, audit_path: str | Path) -> DocumentationLookupResult:
    """Run a constrained online documentation lookup and persist artifacts."""

    query = _clean_query(payload.get("query"))
    allowed_domains = _clean_domains(payload.get("allowed_domains"))
    max_results = _max_results(payload.get("max_results"))
    candidate_urls = _candidate_urls(query, allowed_domains, payload.get("urls"), max_results)
    sources: list[dict[str, str]] = []
    errors: list[str] = []
    for url in candidate_urls:
        domain = urlparse(url).hostname or ""
        if allowed_domains and not _domain_allowed(domain, allowed_domains):
            errors.append(f"blocked_domain:{domain}")
            continue
        try:
            fetched = fetch_url(url, allowed_domains)
        except (OSError, URLError, ValueError) as exc:
            errors.append(f"fetch_failed:{url}:{exc}")
            continue
        sources.append(
            {
                "url": url,
                "domain": domain,
                "title": _extract_title(fetched) or domain,
                "excerpt": _excerpt(_text_from_html(fetched), query),
                "consulted_at": _now(),
            }
        )
        if len(sources) >= max_results:
            break
    summary = _summarize(query, sources, errors)
    result = DocumentationLookupResult(
        status="SUCCESS" if sources else "FAILED",
        query=query,
        sources=sources,
        summary=summary,
        citations=[item["url"] for item in sources],
        errors=errors,
    )
    write_lookup_artifacts(result, payload, workspace, audit_path)
    return result


def fetch_url(url: str, allowed_domains: list[str] | None = None) -> str:
    """Fetch one public HTTPS URL with DNS and redirect validation."""

    domains = tuple(allowed_domains or ())
    safe_url = _validated_public_https_url(url, domains)
    request = Request(safe_url, headers={"User-Agent": USER_AGENT})
    opener = build_opener(_ValidatedRedirectHandler(domains))
    # CodeQL cannot infer the DNS/IP and redirect validation performed above
    # and in the handler. The request cannot target local or private networks.
    with opener.open(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:  # noqa: S310  # lgtm[py/full-ssrf]
        content_type = response.headers.get("content-type", "")
        if "text" not in content_type and "html" not in content_type and "json" not in content_type:
            raise ValueError(f"Unsupported content type: {content_type}")
        raw = response.read(250_000)
    return raw.decode("utf-8", errors="replace")


def write_lookup_artifacts(
    result: DocumentationLookupResult,
    request_payload: dict[str, Any],
    workspace: str | Path,
    audit_path: str | Path,
) -> None:
    """Persist documentation lookup artifacts inside the skill audit path."""

    workspace_path = Path(workspace).resolve()
    audit_dir = validate_skill_artifact_directory(workspace_path, audit_path)
    validate_workspace_path(workspace_path / "lookup_cache.json", workspace_path)
    _write_artifact(audit_dir, "lookup_request.json", json.dumps(request_payload, indent=2))
    _write_artifact(audit_dir, "lookup_result.json", json.dumps(result.to_dict(), indent=2))
    _write_artifact(audit_dir, "sources.json", json.dumps(result.sources, indent=2))
    _write_artifact(audit_dir, "result_summary.md", _summary_markdown(result))
    _write_artifact(
        audit_dir,
        "audit.log",
        json.dumps({"timestamp": _now(), "documentation_lookup": result.to_dict()}, sort_keys=True) + "\n",
        append=True,
    )


class _ValidatedRedirectHandler(HTTPRedirectHandler):
    """Revalidate every redirect before urllib follows it."""

    def __init__(self, allowed_domains: tuple[str, ...]) -> None:
        super().__init__()
        self.allowed_domains = allowed_domains
        self.redirect_count = 0

    def redirect_request(  # type: ignore[no-untyped-def]
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise ValueError("Documentation lookup exceeded the redirect limit.")
        safe_url = _validated_public_https_url(urljoin(req.full_url, newurl), self.allowed_domains)
        return super().redirect_request(req, fp, code, msg, headers, safe_url)


def _validated_public_https_url(url: str, allowed_domains: tuple[str, ...]) -> str:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme != "https" or not hostname:
        raise ValueError("Only public https documentation URLs are allowed.")
    if parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise ValueError("Credentials and non-standard ports are not allowed.")
    if allowed_domains and not _domain_allowed(hostname, list(allowed_domains)):
        raise ValueError(f"Blocked documentation domain: {hostname}")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local")):
        raise ValueError("Local documentation hosts are not allowed.")
    _validate_public_addresses(hostname)
    return parsed.geturl()


def _validate_public_addresses(hostname: str) -> None:
    try:
        literal = ipaddress.ip_address(hostname)
        addresses = [literal]
    except ValueError:
        try:
            records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError(f"Documentation host could not be resolved: {hostname}") from exc
        addresses = []
        for record in records:
            try:
                addresses.append(ipaddress.ip_address(record[4][0]))
            except ValueError as exc:
                raise ValueError("Documentation DNS returned an invalid address.") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Documentation host resolved to a non-public address.")


def _write_artifact(audit_dir: Path, name: str, content: str, *, append: bool = False) -> None:
    if name not in ALLOWED_ARTIFACT_NAMES:
        raise ValueError("Unsupported documentation artifact name.")
    path = (audit_dir / name).resolve()
    if path.parent != audit_dir:
        raise ValueError("Documentation artifact escaped its audit directory.")
    safe_content, _ = redact_sensitive_text(content)
    if append:
        # The fixed path is contained above and all persisted text is redacted.
        with path.open("a", encoding="utf-8") as handle:  # lgtm[py/path-injection]
            handle.write(safe_content)  # lgtm[py/clear-text-storage-sensitive-data]
        return
    path.write_text(  # lgtm[py/path-injection,py/clear-text-storage-sensitive-data]
        safe_content, encoding="utf-8"
    )


def _candidate_urls(query: str, allowed_domains: list[str], urls: object, max_results: int) -> list[str]:
    if isinstance(urls, list):
        return [str(url).strip() for url in urls if str(url).strip()][:max_results]
    domains = allowed_domains or ["docs.python.org"]
    encoded = quote_plus(query)
    candidates: list[str] = []
    for domain in domains:
        candidates.extend(
            [
                f"https://{domain}/search.html?q={encoded}",
                f"https://{domain}/search/?q={encoded}",
                f"https://{domain}/?q={encoded}",
            ]
        )
    return candidates[: max(max_results * 3, max_results)]


def _clean_query(value: object) -> str:
    query = str(value or "").strip()
    if not query:
        raise ValueError("Documentation lookup requires a non-empty query.")
    return query[:300]


def _clean_domains(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("allowed_domains must be a list.")
    domains: list[str] = []
    for item in value:
        domain = str(item).strip().lower()
        if not domain or "/" in domain or "\\" in domain or ":" in domain:
            raise ValueError(f"Invalid allowed domain: {item}")
        domains.append(domain)
    return domains


def _max_results(value: object) -> int:
    try:
        parsed = int(value or 5)
    except (TypeError, ValueError):
        parsed = 5
    return min(max(parsed, 1), 10)


def _domain_allowed(domain: str, allowed_domains: list[str]) -> bool:
    normalized = domain.lower()
    return any(normalized == allowed or normalized.endswith(f".{allowed}") for allowed in allowed_domains)


def _extract_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    return _squash(_text_from_html(match.group(1))) if match else ""


def _text_from_html(text: str) -> str:
    stripped = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    stripped = re.sub(r"<[^>]+>", " ", stripped)
    return html.unescape(_squash(stripped))


def _excerpt(text: str, query: str) -> str:
    clean = _squash(text)
    lowered = clean.lower()
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_+-]{4,}", query)]
    index = min((lowered.find(term) for term in terms if term in lowered), default=0)
    start = max(index - 160, 0)
    return clean[start : start + 600]


def _summarize(query: str, sources: list[dict[str, str]], errors: list[str]) -> str:
    if not sources:
        return f"No documentation sources were retrieved for '{query}'. Errors: {len(errors)}."
    source_lines = [f"{item['title']} ({item['domain']}): {item['excerpt']}" for item in sources]
    return _squash(f"Documentation lookup for '{query}' consulted {len(sources)} source(s). " + " ".join(source_lines))[:2000]


def _summary_markdown(result: DocumentationLookupResult) -> str:
    return "\n".join(
        [
            "# Documentation Lookup Result",
            "",
            f"Status: {result.status}",
            f"Query: {result.query}",
            "",
            "## Summary",
            result.summary,
            "",
            "## Sources",
            *[f"- [{item['title']}]({item['url']})" for item in result.sources],
            "",
            "## Errors",
            *[f"- {error}" for error in result.errors],
            "",
        ]
    )


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
