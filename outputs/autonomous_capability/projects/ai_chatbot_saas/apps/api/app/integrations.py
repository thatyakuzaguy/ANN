from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel


router = APIRouter(prefix="/integrations", tags=["integrations"])


class IntegrationConnection(BaseModel):
    provider: str
    status: str = "configured"
    config: dict[str, Any] = {}


def sign_payload(payload: bytes) -> str:
    secret = os.environ.get("WEBHOOK_SIGNING_SECRET", "dev").encode("utf-8")
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def verify_signature(payload: bytes, signature: str) -> bool:
    return hmac.compare_digest(sign_payload(payload), signature)


@router.get("/providers")
def providers() -> list[dict[str, object]]:
    return [
        {"name": "stripe", "type": "billing", "configured": bool(os.environ.get("STRIPE_SECRET_KEY"))},
        {"name": "sendgrid", "type": "email", "configured": bool(os.environ.get("SENDGRID_API_KEY"))},
        {"name": "google_calendar", "type": "calendar", "configured": bool(os.environ.get("GOOGLE_CLIENT_ID"))},
        {"name": "slack", "type": "notification", "configured": bool(os.environ.get("SLACK_BOT_TOKEN"))},
    ]


@router.post("/connections")
def upsert_connection(payload: IntegrationConnection) -> dict[str, Any]:
    return {"connection": payload.model_dump(), "secret_storage": "environment-or-vault-required"}


@router.post("/webhooks/{provider}")
async def signed_webhook(provider: str, request: Request, x_signature: str | None = Header(default=None)) -> dict[str, str]:
    body = await request.body()
    if not x_signature or not verify_signature(body, x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature.")
    return {"status": "accepted", "provider": provider}
