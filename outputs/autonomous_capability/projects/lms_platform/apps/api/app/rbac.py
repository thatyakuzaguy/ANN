from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Membership, User
from .security import decode_token
from .tenancy import TenantContext, require_tenant

AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {"*"},
    "admin": {"billing:*", "tenant:*", "crm:*", "domain:*", "workflow:*", "integration:*", "dashboard:*"},
    "manager": {"crm:*", "domain:*", "workflow:read", "dashboard:*"},
    "contributor": {"crm:write", "crm:read", "domain:write", "domain:read", "dashboard:read"},
    "viewer": {"crm:read", "domain:read", "dashboard:read"},
}


def has_permission(role: str, permission: str) -> bool:
    grants = ROLE_PERMISSIONS.get(role, set())
    namespace = permission.split(":", 1)[0]
    return "*" in grants or permission in grants or f"{namespace}:*" in grants


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str | None
    role: str | None


def _token_subject(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is required.")
    try:
        return decode_token(authorization.split(" ", 1)[1])
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token is invalid.") from exc


def require_authenticated_user(
    authorization: AuthorizationHeader = None,
    db: Session = Depends(get_db),
) -> Principal:
    user_id = _token_subject(authorization)
    if db.scalar(select(User.id).where(User.id == user_id)) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user no longer exists.")
    return Principal(user_id=user_id, tenant_id=None, role=None)


def require_permission(permission: str) -> Callable[..., Principal]:
    def dependency(
        tenant: TenantContext = Depends(require_tenant),
        authorization: AuthorizationHeader = None,
        db: Session = Depends(get_db),
    ) -> Principal:
        user_id = _token_subject(authorization)
        membership = db.scalar(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.tenant_id == tenant.tenant_id,
            )
        )
        if membership is None or not has_permission(membership.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant permission denied.",
            )
        return Principal(user_id=user_id, tenant_id=tenant.tenant_id, role=membership.role)

    return dependency
