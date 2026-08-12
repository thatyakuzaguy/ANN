"""Tenant-scoped Booking SaaS API with authenticated RBAC boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import get_db
from .domain_config import DOMAIN_ID, ENTITIES, ENTITY_TYPES, INTEGRATIONS, WORKFLOWS
from .domain_models import DomainRecord
from .domain_schemas import DomainDashboard, DomainRecordCreate, DomainRecordRead, DomainRecordUpdate
from .models import Membership
from .rbac import has_permission
from .security import decode_token
from .tenancy import TenantContext, require_tenant


router = APIRouter(prefix=f"/{DOMAIN_ID}", tags=[DOMAIN_ID])
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]


@dataclass(frozen=True)
class DomainPrincipal:
    user_id: str
    tenant_id: str
    role: str


def require_domain_permission(permission: str):
    def dependency(
        tenant: TenantContext = Depends(require_tenant),
        authorization: AuthorizationHeader = None,
        db: Session = Depends(get_db),
    ) -> DomainPrincipal:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Bearer token is required.")
        try:
            user_id = decode_token(authorization.split(" ", 1)[1])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="Bearer token is invalid.") from exc
        membership = db.scalar(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.tenant_id == tenant.tenant_id,
            )
        )
        if membership is None or not has_permission(membership.role, permission):
            raise HTTPException(status_code=403, detail="Tenant permission denied.")
        return DomainPrincipal(user_id=user_id, tenant_id=tenant.tenant_id, role=membership.role)

    return dependency


def _validate_entity(entity_type: str) -> str:
    if entity_type not in ENTITY_TYPES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown {DOMAIN_ID} entity '{entity_type}'. Allowed: {', '.join(ENTITIES)}",
        )
    return entity_type


def _record_or_404(db: Session, principal: DomainPrincipal, entity_type: str, record_id: str) -> DomainRecord:
    record = db.scalar(
        select(DomainRecord).where(
            DomainRecord.id == record_id,
            DomainRecord.tenant_id == principal.tenant_id,
            DomainRecord.entity_type == entity_type,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Domain record not found in tenant.")
    return record


@router.get("/contract")
def domain_contract() -> dict[str, object]:
    return {
        "domain": DOMAIN_ID,
        "entities": ENTITIES,
        "workflows": WORKFLOWS,
        "integrations": INTEGRATIONS,
    }


@router.post("/records/{entity_type}", response_model=DomainRecordRead, status_code=201)
def create_record(
    entity_type: str,
    payload: DomainRecordCreate,
    principal: DomainPrincipal = Depends(require_domain_permission("domain:write")),
    db: Session = Depends(get_db),
) -> DomainRecord:
    selected = _validate_entity(entity_type)
    record = DomainRecord(
        tenant_id=principal.tenant_id,
        entity_type=selected,
        created_by=principal.user_id,
        **payload.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/records/{entity_type}", response_model=list[DomainRecordRead])
def list_records(
    entity_type: str,
    principal: DomainPrincipal = Depends(require_domain_permission("domain:read")),
    db: Session = Depends(get_db),
) -> list[DomainRecord]:
    selected = _validate_entity(entity_type)
    query = (
        select(DomainRecord)
        .where(
            DomainRecord.tenant_id == principal.tenant_id,
            DomainRecord.entity_type == selected,
        )
        .order_by(DomainRecord.updated_at.desc())
    )
    return list(db.scalars(query).all())


@router.get("/records/{entity_type}/{record_id}", response_model=DomainRecordRead)
def get_record(
    entity_type: str,
    record_id: str,
    principal: DomainPrincipal = Depends(require_domain_permission("domain:read")),
    db: Session = Depends(get_db),
) -> DomainRecord:
    return _record_or_404(db, principal, _validate_entity(entity_type), record_id)


@router.patch("/records/{entity_type}/{record_id}", response_model=DomainRecordRead)
def update_record(
    entity_type: str,
    record_id: str,
    payload: DomainRecordUpdate,
    principal: DomainPrincipal = Depends(require_domain_permission("domain:write")),
    db: Session = Depends(get_db),
) -> DomainRecord:
    record = _record_or_404(db, principal, _validate_entity(entity_type), record_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/records/{entity_type}/{record_id}", status_code=204)
def delete_record(
    entity_type: str,
    record_id: str,
    principal: DomainPrincipal = Depends(require_domain_permission("domain:write")),
    db: Session = Depends(get_db),
) -> Response:
    record = _record_or_404(db, principal, _validate_entity(entity_type), record_id)
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/dashboard", response_model=DomainDashboard)
def domain_dashboard(
    principal: DomainPrincipal = Depends(require_domain_permission("domain:read")),
    db: Session = Depends(get_db),
) -> DomainDashboard:
    rows = db.execute(
        select(DomainRecord.entity_type, func.count(DomainRecord.id))
        .where(DomainRecord.tenant_id == principal.tenant_id)
        .group_by(DomainRecord.entity_type)
    ).all()
    observed = {entity_type: int(count) for entity_type, count in rows}
    return DomainDashboard(
        domain=DOMAIN_ID,
        tenant_id=principal.tenant_id,
        counts={entity: observed.get(entity, 0) for entity in ENTITIES},
        workflows=WORKFLOWS,
        integrations=INTEGRATIONS,
    )
