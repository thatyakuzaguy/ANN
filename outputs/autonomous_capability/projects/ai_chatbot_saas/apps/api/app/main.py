from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .billing import router as billing_router
from .domain_router import router as domain_router
from .integrations import router as integrations_router
from .models import Account, Activity, Contact, Deal, Membership, Tenant, User
from .rbac import Principal, require_authenticated_user, require_permission
from .security_headers import security_headers_middleware
from .schemas import AccountCreate, AccountRead, ActivityCreate, ActivityRead, AuthResponse, ContactCreate, ContactRead, DashboardMetrics, DealCreate, DealRead, LoginRequest
from .security import decode_token, hash_password, issue_token, verify_password
from .tenancy import TenantContext, require_tenant
from .workflows import router as workflows_router

app = FastAPI(title="AI Chatbot SaaS API", version="0.1.0")
app.middleware("http")(security_headers_middleware)
origins = [origin.strip() for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(billing_router)
app.include_router(domain_router)
app.include_router(workflows_router)
app.include_router(integrations_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-chatbot-saas-api"}


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email, name=payload.email.split("@")[0], password_hash=hash_password(payload.password))
    tenant_slug = payload.email.split("@")[0].lower().replace(".", "-").replace("_", "-")
    tenant = Tenant(name=f"{user.name} Workspace", slug=f"{tenant_slug}-{os.urandom(2).hex()}")
    db.add(user)
    db.add(tenant)
    db.flush()
    db.add(Membership(user_id=user.id, tenant_id=tenant.id, role="owner"))
    db.commit()
    return AuthResponse(access_token=issue_token(user.id))


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthResponse(access_token=issue_token(user.id))


@app.get("/tenants", response_model=list[dict[str, str]])
def list_tenants(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_authenticated_user),
) -> list[dict[str, str]]:
    query = (
        select(Tenant)
        .join(Membership, Membership.tenant_id == Tenant.id)
        .where(Membership.user_id == principal.user_id)
        .order_by(Tenant.created_at.desc())
    )
    return [
        {"id": tenant.id, "name": tenant.name, "slug": tenant.slug}
        for tenant in db.scalars(query).all()
    ]


@app.get("/dashboard", response_model=DashboardMetrics)
def dashboard(
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("dashboard:read")),
    db: Session = Depends(get_db),
) -> DashboardMetrics:
    accounts = db.scalar(select(func.count(Account.id)).where(Account.tenant_id == tenant.tenant_id)) or 0
    contacts = db.scalar(select(func.count(Contact.id)).where(Contact.tenant_id == tenant.tenant_id)) or 0
    activities = db.scalar(select(func.count(Activity.id)).where(Activity.tenant_id == tenant.tenant_id)) or 0
    open_deals = db.scalar(select(func.count(Deal.id)).where(Deal.tenant_id == tenant.tenant_id, Deal.stage != "won")) or 0
    pipeline_value = db.scalar(select(func.coalesce(func.sum(Deal.value), 0)).where(Deal.tenant_id == tenant.tenant_id)) or 0
    return DashboardMetrics(accounts=accounts, contacts=contacts, open_deals=open_deals, activities=activities, pipeline_value=float(pipeline_value))


@app.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("crm:write")),
    db: Session = Depends(get_db),
) -> Account:
    account = Account(**payload.model_dump(), tenant_id=tenant.tenant_id)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.get("/accounts", response_model=list[AccountRead])
def list_accounts(
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("crm:read")),
    db: Session = Depends(get_db),
) -> list[Account]:
    return list(db.scalars(select(Account).where(Account.tenant_id == tenant.tenant_id).order_by(Account.created_at.desc())).all())


@app.post("/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("crm:write")),
    db: Session = Depends(get_db),
) -> Contact:
    account = db.scalar(select(Account).where(Account.id == payload.account_id, Account.tenant_id == tenant.tenant_id))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found in tenant.")
    contact = Contact(**payload.model_dump(), tenant_id=tenant.tenant_id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@app.get("/contacts", response_model=list[ContactRead])
def list_contacts(
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("crm:read")),
    db: Session = Depends(get_db),
) -> list[Contact]:
    return list(db.scalars(select(Contact).where(Contact.tenant_id == tenant.tenant_id).order_by(Contact.created_at.desc())).all())


@app.post("/deals", response_model=DealRead, status_code=status.HTTP_201_CREATED)
def create_deal(
    payload: DealCreate,
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("crm:write")),
    db: Session = Depends(get_db),
) -> Deal:
    account = db.scalar(select(Account).where(Account.id == payload.account_id, Account.tenant_id == tenant.tenant_id))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found in tenant.")
    deal = Deal(**payload.model_dump(), tenant_id=tenant.tenant_id)
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@app.get("/deals", response_model=list[DealRead])
def list_deals(
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("crm:read")),
    db: Session = Depends(get_db),
) -> list[Deal]:
    return list(db.scalars(select(Deal).where(Deal.tenant_id == tenant.tenant_id).order_by(Deal.created_at.desc())).all())


@app.post("/activities", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate,
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("crm:write")),
    db: Session = Depends(get_db),
) -> Activity:
    account = db.scalar(select(Account).where(Account.id == payload.account_id, Account.tenant_id == tenant.tenant_id))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found in tenant.")
    activity = Activity(**payload.model_dump(), tenant_id=tenant.tenant_id)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@app.get("/activities", response_model=list[ActivityRead])
def list_activities(
    tenant: TenantContext = Depends(require_tenant),
    role: str = Depends(require_permission("crm:read")),
    db: Session = Depends(get_db),
) -> list[Activity]:
    return list(db.scalars(select(Activity).where(Activity.tenant_id == tenant.tenant_id).order_by(Activity.created_at.desc())).all())
