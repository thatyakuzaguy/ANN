from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

try:
    import stripe
except ModuleNotFoundError:
    stripe = None


router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    tenant_id: str
    customer_email: str
    price_id: str | None = None


class BillingPortalRequest(BaseModel):
    customer_id: str


def _stripe_ready() -> bool:
    return stripe is not None and bool(os.environ.get("STRIPE_SECRET_KEY"))


@router.get("/status")
def billing_status() -> dict[str, object]:
    return {
        "provider": "stripe",
        "configured": _stripe_ready(),
        "package_available": stripe is not None,
        "required_env": ["STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID", "PUBLIC_APP_URL"],
    }


@router.post("/checkout-session")
def create_checkout_session(payload: CheckoutRequest) -> dict[str, Any]:
    if not _stripe_ready():
        return {
            "mode": "configuration_required",
            "message": "Install stripe and set STRIPE_SECRET_KEY and STRIPE_PRICE_ID to create real checkout sessions.",
        }
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    app_url = os.environ.get("PUBLIC_APP_URL", "http://localhost:3000").rstrip("/")
    price_id = payload.price_id or os.environ.get("STRIPE_PRICE_ID")
    if not price_id:
        raise HTTPException(status_code=400, detail="No Stripe price id configured.")
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=payload.customer_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{app_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{app_url}/billing/cancelled",
        metadata={"tenant_id": payload.tenant_id},
    )
    return {"id": session.id, "url": session.url}


@router.post("/portal-session")
def create_portal_session(payload: BillingPortalRequest) -> dict[str, Any]:
    if not _stripe_ready():
        return {"mode": "configuration_required", "message": "Install stripe and set STRIPE_SECRET_KEY to create billing portal sessions."}
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    app_url = os.environ.get("PUBLIC_APP_URL", "http://localhost:3000").rstrip("/")
    session = stripe.billing_portal.Session.create(customer=payload.customer_id, return_url=f"{app_url}/settings/billing")
    return {"url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str | None = Header(default=None)) -> dict[str, str]:
    payload = await request.body()
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not _stripe_ready() or not secret:
        return {"status": "ignored", "reason": "Stripe webhook secret is not configured."}
    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=stripe_signature or "", secret=secret)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid Stripe webhook: {exc}") from exc
    return {"status": "received", "event_type": str(event["type"])}
