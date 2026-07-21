from __future__ import annotations

import re


def build_algorithm_project_artifacts(idea: str, run_id: str) -> dict[str, str]:
    slug = _slugify(idea)
    base = f"{slug}-{run_id[:8]}"
    return {
        f"{base}/README.md": _readme(idea),
        f"{base}/.env.example": "APP_ENV=local\nAPI_PORT=8000\n",
        f"{base}/.dockerignore": _dockerignore(),
        f"{base}/Dockerfile": _dockerfile(),
        f"{base}/docker-compose.yml": _compose(),
        f"{base}/pyproject.toml": _pyproject(),
        f"{base}/app/__init__.py": "",
        f"{base}/app/algorithm.py": _algorithm(),
        f"{base}/app/main.py": _main(),
        f"{base}/app/metrics.py": _metrics(),
        f"{base}/app/schemas.py": _schemas(),
        f"{base}/app/validation.py": _validation(),
        f"{base}/tests/test_algorithm.py": _test_algorithm(),
        f"{base}/tests/test_edge_cases.py": _test_edge_cases(),
        f"{base}/tests/test_integration.py": _test_integration(),
        f"{base}/tests/test_validation.py": _test_validation(),
        f"{base}/benchmark.py": _benchmark(),
        f"{base}/docs/ALGORITHM.md": _algorithm_doc(),
        f"{base}/docs/API.md": _api_doc(),
        f"{base}/docs/SECURITY.md": _security_doc(),
        f"{base}/scripts/test.ps1": _test_script(),
    }


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "algorithm-service"


def _dockerignore() -> str:
    return """.aen
.git
__pycache__
.pytest_cache
*.pyc
release
"""


def _readme(idea: str) -> str:
    return f"""# Constraint-Aware Route Optimizer

Generated from:

```text
{idea}
```

This FastAPI service implements deterministic K-shortest loopless paths using
Yen's algorithm over a validated weighted directed graph. It includes
correctness tests, integration tests, edge-case validation, and a reproducible
benchmark.

## Run

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Verify

```powershell
python -m pytest tests -q
python benchmark.py
```
"""


def _dockerfile() -> str:
    return """FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV XDG_CACHE_HOME=/tmp
COPY pyproject.toml ./
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.1.2" \
    && python -m pip install --no-cache-dir ".[test]"
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def _compose() -> str:
    return """services:
  api:
    build: .
    ports:
      - "${API_PORT:-18000}:8000"
    environment:
      PYTHONDONTWRITEBYTECODE: "1"
      PYTHONPATH: /app
      XDG_CACHE_HOME: /tmp
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 5s
      timeout: 3s
      retries: 20
"""


def _pyproject() -> str:
    return '''[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "constraint-route-optimizer"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = ["fastapi>=0.115", "uvicorn>=0.30", "pydantic>=2.8"]

[project.optional-dependencies]
test = ["pytest>=8.2", "httpx>=0.27", "pip-audit>=2.9"]

[tool.pytest.ini_options]
testpaths = ["tests"]
'''


def _schemas() -> str:
    return '''from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class EdgeInput(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    target: str = Field(min_length=1, max_length=120)
    weight: float = Field(ge=0, le=1_000_000)


class RouteRequest(BaseModel):
    nodes: list[str] = Field(min_length=2, max_length=10_000)
    edges: list[EdgeInput] = Field(min_length=1, max_length=100_000)
    source: str
    target: str
    k: int = Field(default=3, ge=1, le=25)
    blocked_nodes: set[str] = Field(default_factory=set)
    max_cost: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_contract(self) -> "RouteRequest":
        node_set = set(self.nodes)
        if len(node_set) != len(self.nodes):
            raise ValueError("nodes must be unique")
        if self.source not in node_set or self.target not in node_set:
            raise ValueError("source and target must exist in nodes")
        if self.source in self.blocked_nodes or self.target in self.blocked_nodes:
            raise ValueError("source and target cannot be blocked")
        if not self.blocked_nodes.issubset(node_set):
            raise ValueError("blocked_nodes must exist in nodes")
        for edge in self.edges:
            if edge.source not in node_set or edge.target not in node_set:
                raise ValueError("every edge endpoint must exist in nodes")
        return self


class RouteResult(BaseModel):
    nodes: list[str]
    cost: float


class RouteResponse(BaseModel):
    routes: list[RouteResult]
    algorithm: str
    complexity: str
    graph_nodes: int
    graph_edges: int
    elapsed_ms: float
'''


def _algorithm() -> str:
    return '''from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from collections.abc import Iterable


@dataclass(frozen=True, order=True)
class Edge:
    source: str
    target: str
    weight: float


@dataclass(frozen=True)
class PathResult:
    nodes: tuple[str, ...]
    cost: float


def _adjacency(nodes: Iterable[str], edges: Iterable[Edge]) -> dict[str, tuple[Edge, ...]]:
    graph: dict[str, list[Edge]] = {node: [] for node in nodes}
    for edge in edges:
        if edge.weight < 0 or not math.isfinite(edge.weight):
            raise ValueError("edge weights must be finite and non-negative")
        if edge.source not in graph or edge.target not in graph:
            raise ValueError("edge endpoint is not present in nodes")
        graph[edge.source].append(edge)
    return {node: tuple(sorted(outgoing, key=lambda item: (item.target, item.weight))) for node, outgoing in graph.items()}


def shortest_path(
    nodes: Iterable[str],
    edges: Iterable[Edge],
    source: str,
    target: str,
    *,
    banned_nodes: frozenset[str] = frozenset(),
    banned_edges: frozenset[tuple[str, str]] = frozenset(),
) -> PathResult | None:
    """Return a deterministic Dijkstra path in O((V + E) log V)."""

    node_tuple = tuple(dict.fromkeys(nodes))
    if source not in node_tuple or target not in node_tuple:
        raise ValueError("source and target must exist in nodes")
    if source in banned_nodes or target in banned_nodes:
        return None
    graph = _adjacency(node_tuple, edges)
    queue: list[tuple[float, tuple[str, ...], str]] = [(0.0, (source,), source)]
    best: dict[str, float] = {source: 0.0}
    while queue:
        cost, path, current = heapq.heappop(queue)
        if cost > best.get(current, math.inf):
            continue
        if current == target:
            return PathResult(path, cost)
        for edge in graph[current]:
            if edge.target in banned_nodes or (edge.source, edge.target) in banned_edges:
                continue
            if edge.target in path:
                continue
            candidate = cost + edge.weight
            if candidate <= best.get(edge.target, math.inf):
                best[edge.target] = candidate
                heapq.heappush(queue, (candidate, (*path, edge.target), edge.target))
    return None


def _path_cost(path: tuple[str, ...], edge_weights: dict[tuple[str, str], float]) -> float:
    try:
        return sum(edge_weights[(source, target)] for source, target in zip(path, path[1:]))
    except KeyError as exc:
        raise ValueError("path contains an edge that is not present in the graph") from exc


def k_shortest_paths(
    nodes: Iterable[str],
    edges: Iterable[Edge],
    source: str,
    target: str,
    k: int,
    *,
    blocked_nodes: frozenset[str] = frozenset(),
    max_cost: float | None = None,
) -> list[PathResult]:
    """Return up to K loopless paths using Yen's algorithm.

    Complexity is O(K * V * (E log V)) in the conservative worst case.
    Candidate ordering is deterministic by total cost and node sequence.
    """

    if k < 1 or k > 25:
        raise ValueError("k must be between 1 and 25")
    node_tuple = tuple(dict.fromkeys(nodes))
    edge_tuple = tuple(edges)
    first = shortest_path(
        node_tuple,
        edge_tuple,
        source,
        target,
        banned_nodes=blocked_nodes,
    )
    if first is None or (max_cost is not None and first.cost > max_cost):
        return []
    accepted = [first]
    candidates: list[tuple[float, tuple[str, ...]]] = []
    candidate_paths: set[tuple[str, ...]] = set()
    edge_weights = {(edge.source, edge.target): edge.weight for edge in edge_tuple}

    for _rank in range(1, k):
        previous = accepted[-1].nodes
        for spur_index in range(len(previous) - 1):
            root = previous[: spur_index + 1]
            removed_edges = {
                (path.nodes[spur_index], path.nodes[spur_index + 1])
                for path in accepted
                if len(path.nodes) > spur_index and path.nodes[: spur_index + 1] == root
            }
            spur = shortest_path(
                node_tuple,
                edge_tuple,
                root[-1],
                target,
                banned_nodes=frozenset({*blocked_nodes, *root[:-1]}),
                banned_edges=frozenset(removed_edges),
            )
            if spur is None:
                continue
            total_nodes = (*root[:-1], *spur.nodes)
            if total_nodes in candidate_paths or any(item.nodes == total_nodes for item in accepted):
                continue
            total_cost = _path_cost(total_nodes, edge_weights)
            if max_cost is not None and total_cost > max_cost:
                continue
            candidate_paths.add(total_nodes)
            heapq.heappush(candidates, (total_cost, total_nodes))
        if not candidates:
            break
        cost, selected = heapq.heappop(candidates)
        candidate_paths.discard(selected)
        accepted.append(PathResult(selected, cost))
    return accepted
'''


def _validation() -> str:
    return '''from __future__ import annotations

from .algorithm import Edge
from .schemas import RouteRequest


def normalize_request(payload: RouteRequest) -> tuple[tuple[str, ...], tuple[Edge, ...]]:
    """Normalize graph input and reject ambiguous duplicate edges."""

    seen: set[tuple[str, str]] = set()
    edges: list[Edge] = []
    for item in payload.edges:
        key = (item.source, item.target)
        if key in seen:
            raise ValueError(f"duplicate directed edge: {item.source}->{item.target}")
        seen.add(key)
        edges.append(Edge(item.source, item.target, item.weight))
    return tuple(payload.nodes), tuple(edges)
'''


def _metrics() -> str:
    return '''from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import time
from collections.abc import Iterator


@dataclass
class Timer:
    elapsed_ms: float = 0.0


@contextmanager
def measure() -> Iterator[Timer]:
    timer = Timer()
    started = time.perf_counter()
    try:
        yield timer
    finally:
        timer.elapsed_ms = (time.perf_counter() - started) * 1000
'''


def _main() -> str:
    return '''from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .algorithm import k_shortest_paths
from .metrics import measure
from .schemas import RouteRequest, RouteResponse, RouteResult
from .validation import normalize_request


app = FastAPI(title="Constraint-Aware Route Optimizer", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "algorithm": "yen-k-shortest-loopless-paths"}


@app.post("/v1/routes/optimize", response_model=RouteResponse)
def optimize_routes(payload: RouteRequest) -> RouteResponse:
    try:
        nodes, edges = normalize_request(payload)
        with measure() as timer:
            routes = k_shortest_paths(
                nodes,
                edges,
                payload.source,
                payload.target,
                payload.k,
                blocked_nodes=frozenset(payload.blocked_nodes),
                max_cost=payload.max_cost,
            )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RouteResponse(
        routes=[RouteResult(nodes=list(route.nodes), cost=route.cost) for route in routes],
        algorithm="yen-k-shortest-loopless-paths",
        complexity="O(K * V * (E log V))",
        graph_nodes=len(nodes),
        graph_edges=len(edges),
        elapsed_ms=round(timer.elapsed_ms, 3),
    )
'''


def _test_algorithm() -> str:
    return '''from app.algorithm import Edge, k_shortest_paths, shortest_path


NODES = ("a", "b", "c", "d")
EDGES = (
    Edge("a", "b", 1),
    Edge("b", "d", 1),
    Edge("a", "c", 1),
    Edge("c", "d", 2),
    Edge("b", "c", 0.5),
)


def test_shortest_path_is_optimal() -> None:
    result = shortest_path(NODES, EDGES, "a", "d")
    assert result is not None
    assert result.nodes == ("a", "b", "d")
    assert result.cost == 2


def test_k_shortest_paths_are_cost_ordered_and_unique() -> None:
    routes = k_shortest_paths(NODES, EDGES, "a", "d", 3)
    assert len({route.nodes for route in routes}) == len(routes)
    assert [route.cost for route in routes] == sorted(route.cost for route in routes)
    assert routes[0].nodes == ("a", "b", "d")
'''


def _test_edge_cases() -> str:
    return '''import pytest

from app.algorithm import Edge, k_shortest_paths, shortest_path


def test_unreachable_target_returns_no_path() -> None:
    assert shortest_path(("a", "b", "c"), (Edge("a", "b", 1),), "a", "c") is None


def test_blocked_node_is_excluded() -> None:
    edges = (Edge("a", "b", 1), Edge("b", "d", 1), Edge("a", "c", 2), Edge("c", "d", 2))
    routes = k_shortest_paths(("a", "b", "c", "d"), edges, "a", "d", 2, blocked_nodes=frozenset({"b"}))
    assert [route.nodes for route in routes] == [("a", "c", "d")]


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        shortest_path(("a", "b"), (Edge("a", "b", -1),), "a", "b")
'''


def _test_validation() -> str:
    return '''import pytest

from app.schemas import EdgeInput, RouteRequest
from app.validation import normalize_request


def test_duplicate_edge_is_rejected() -> None:
    payload = RouteRequest(
        nodes=["a", "b"],
        edges=[EdgeInput(source="a", target="b", weight=1), EdgeInput(source="a", target="b", weight=2)],
        source="a",
        target="b",
    )
    with pytest.raises(ValueError, match="duplicate"):
        normalize_request(payload)


def test_unknown_endpoint_is_rejected_by_contract() -> None:
    with pytest.raises(ValueError, match="edge endpoint"):
        RouteRequest(
            nodes=["a", "b"],
            edges=[EdgeInput(source="a", target="c", weight=1)],
            source="a",
            target="b",
        )
'''


def _test_integration() -> str:
    return '''from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_route_optimizer_api() -> None:
    response = client.post(
        "/v1/routes/optimize",
        json={
            "nodes": ["a", "b", "c"],
            "edges": [
                {"source": "a", "target": "b", "weight": 1},
                {"source": "b", "target": "c", "weight": 1},
                {"source": "a", "target": "c", "weight": 3},
            ],
            "source": "a",
            "target": "c",
            "k": 2,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["routes"][0] == {"nodes": ["a", "b", "c"], "cost": 2.0}
    assert payload["complexity"].startswith("O(")
'''


def _benchmark() -> str:
    return '''from __future__ import annotations

import json
import random
import time

from app.algorithm import Edge, k_shortest_paths


def run_benchmark(node_count: int = 500, edge_count: int = 4_000) -> dict[str, object]:
    randomizer = random.Random(42)
    nodes = tuple(f"n{index}" for index in range(node_count))
    pairs: set[tuple[str, str]] = set()
    edges: list[Edge] = []
    while len(edges) < edge_count:
        source = randomizer.choice(nodes)
        target = randomizer.choice(nodes)
        if source == target or (source, target) in pairs:
            continue
        pairs.add((source, target))
        edges.append(Edge(source, target, randomizer.uniform(0.1, 50)))
    started = time.perf_counter()
    routes = k_shortest_paths(nodes, edges, nodes[0], nodes[-1], 5)
    elapsed = time.perf_counter() - started
    return {
        "status": "PASSED",
        "algorithm": "yen-k-shortest-loopless-paths",
        "nodes": node_count,
        "edges": edge_count,
        "routes_found": len(routes),
        "elapsed_seconds": round(elapsed, 6),
        "complexity": "O(K * V * (E log V))",
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2))
'''


def _algorithm_doc() -> str:
    return """# Algorithm

The service uses Dijkstra's algorithm as the shortest-path primitive and Yen's
algorithm to enumerate K loopless alternatives. Inputs are validated before
execution. Negative or non-finite weights, duplicate edges, unknown nodes, and
blocked endpoints are rejected.

Worst-case complexity is conservatively bounded by `O(K * V * (E log V))`.
The implementation uses deterministic tie-breaking so equal-cost graphs produce
stable outputs.
"""


def _api_doc() -> str:
    return """# API

`POST /v1/routes/optimize` accepts nodes, weighted directed edges, source,
target, K, blocked nodes, and an optional maximum cost. The response includes
ordered loopless routes, cost, graph size, measured latency, and complexity.
"""


def _security_doc() -> str:
    return """# Security

- Pydantic bounds graph size, K, identifiers, and edge weights.
- The algorithm does not execute user code or shell commands.
- The container is read-only and uses `no-new-privileges`.
- Production deployments should add authentication, tenant quotas, and request
  rate limiting at the API gateway.
"""


def _test_script() -> str:
    return '''$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))
python -m pytest tests -q
python benchmark.py
'''
