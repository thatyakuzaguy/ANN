from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    industry: str = "General"
    website: str | None = None


class AccountRead(AccountCreate):
    id: str

    model_config = {"from_attributes": True}


class ContactCreate(BaseModel):
    account_id: str
    name: str
    email: EmailStr
    role: str = "Decision maker"


class ContactRead(ContactCreate):
    id: str

    model_config = {"from_attributes": True}


class DealCreate(BaseModel):
    account_id: str
    name: str
    stage: str = "qualified"
    value: float = 0
    notes: str | None = None


class DealRead(DealCreate):
    id: str

    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    account_id: str
    kind: str = "note"
    summary: str = Field(min_length=2, max_length=240)


class ActivityRead(ActivityCreate):
    id: str

    model_config = {"from_attributes": True}


class DashboardMetrics(BaseModel):
    accounts: int
    contacts: int
    open_deals: int
    activities: int
    pipeline_value: float
