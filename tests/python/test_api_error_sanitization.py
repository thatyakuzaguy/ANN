from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import HTTPException

from app.api import routes
from app.schemas.runs import BillingCheckoutRequest, BillingPortalRequest, ModelRuntimePolicyUpdate


_SENSITIVE_ERROR = r"provider failed at C:\Users\private\stripe.json with api_key=secret"


class _FailingBillingService:
    def create_checkout_session(self, customer_email: str, tenant_id: str) -> dict[str, object]:
        raise RuntimeError(_SENSITIVE_ERROR)

    def create_customer_portal(self, customer_id: str) -> dict[str, object]:
        raise RuntimeError(_SENSITIVE_ERROR)

    def handle_webhook(self, payload: bytes, signature: str | None) -> dict[str, object]:
        raise RuntimeError(_SENSITIVE_ERROR)


class _Request:
    headers = {"stripe-signature": "test-signature"}

    async def body(self) -> bytes:
        return b"{}"


class _AuditRecorder:
    def __init__(self) -> None:
        self.events: list[tuple[object, ...]] = []

    def record(self, *args: object) -> None:
        self.events.append(args)


def _install_failing_billing_service(monkeypatch: pytest.MonkeyPatch) -> _AuditRecorder:
    audit = _AuditRecorder()
    monkeypatch.setattr(routes, "StripeBillingService", _FailingBillingService)
    monkeypatch.setattr(routes, "audit_logger", audit)
    return audit


@pytest.mark.parametrize(
    ("call", "expected_detail"),
    [
        (
            lambda: routes.billing_checkout(
                BillingCheckoutRequest(customer_email="user@example.com", tenant_id="tenant")
            ),
            "Billing checkout could not be created.",
        ),
        (
            lambda: routes.billing_portal(BillingPortalRequest(customer_id="cus_test")),
            "Customer portal could not be opened.",
        ),
    ],
)
def test_billing_api_does_not_expose_provider_exception(
    monkeypatch: pytest.MonkeyPatch,
    call: object,
    expected_detail: str,
) -> None:
    audit = _install_failing_billing_service(monkeypatch)

    with pytest.raises(HTTPException) as captured:
        call()

    assert captured.value.status_code == 400
    assert captured.value.detail == expected_detail
    assert _SENSITIVE_ERROR not in str(captured.value.detail)
    assert audit.events
    assert _SENSITIVE_ERROR not in json.dumps(audit.events)
    assert audit.events[-1][-1] == {"error_type": "RuntimeError"}


def test_billing_webhook_does_not_expose_provider_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audit = _install_failing_billing_service(monkeypatch)

    with pytest.raises(HTTPException) as captured:
        asyncio.run(routes.billing_webhook(_Request()))

    assert captured.value.status_code == 400
    assert captured.value.detail == "Invalid billing webhook."
    assert _SENSITIVE_ERROR not in str(captured.value.detail)
    assert _SENSITIVE_ERROR not in json.dumps(audit.events)


def test_model_runtime_policy_omits_private_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    private_diagnostic = {
        "errors": [_SENSITIVE_ERROR],
        "safe_load_configuration": {"model_path": r"D:\private\model.gguf"},
    }

    monkeypatch.setattr(
        routes,
        "configure_real_model_runtime",
        lambda **_kwargs: {
            "status": "enabled",
            "backend": "llama_cpp",
            "active_models": 0,
            "parallel_llm_loads": 0,
            "vram_policy": "SEQUENTIAL",
            "model_load_performed": False,
            "diagnostic": private_diagnostic,
        },
    )
    monkeypatch.setattr(routes, "audit_logger", _AuditRecorder())

    result = routes.update_model_runtime_policy(
        ModelRuntimePolicyUpdate(enabled=True, confirmed=True, risk_acknowledged=True)
    )
    serialized = json.dumps(result)

    assert result == {
        "status": "enabled",
        "backend": "llama_cpp",
        "active_models": 0,
        "parallel_llm_loads": 0,
        "vram_policy": "SEQUENTIAL",
        "model_load_performed": False,
    }
    assert "diagnostic" not in result
    assert _SENSITIVE_ERROR not in serialized
    assert "model.gguf" not in serialized
