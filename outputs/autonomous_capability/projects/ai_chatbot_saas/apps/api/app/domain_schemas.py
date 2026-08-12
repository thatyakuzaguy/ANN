from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DomainRecordCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    status: str = Field(default="active", min_length=2, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)


class DomainRecordUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    status: str | None = Field(default=None, min_length=2, max_length=80)
    payload: dict[str, Any] | None = None


class DomainRecordRead(DomainRecordCreate):
    id: str
    tenant_id: str
    entity_type: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DomainDashboard(BaseModel):
    domain: str
    tenant_id: str
    counts: dict[str, int]
    workflows: list[str]
    integrations: list[str]
