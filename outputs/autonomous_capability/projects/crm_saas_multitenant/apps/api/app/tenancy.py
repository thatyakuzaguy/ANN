from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException, status


TenantHeader = Annotated[str | None, Header(alias="X-Tenant-ID")]


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str


def require_tenant(tenant_id: TenantHeader = None) -> TenantContext:
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required for tenant-scoped operations.",
        )
    return TenantContext(tenant_id=tenant_id)


def tenant_scope(model: object, tenant_id: str) -> object:
    return getattr(model, "tenant_id") == tenant_id
