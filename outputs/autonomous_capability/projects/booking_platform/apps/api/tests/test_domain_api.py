from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Membership, Tenant


client = TestClient(app)
DOMAIN_ID = "booking"
ENTITY_TYPE = "resource"


def setup_module() -> None:
    Base.metadata.create_all(bind=engine)


def _register_owner() -> tuple[str, str]:
    unique = uuid4().hex
    response = client.post(
        "/auth/register",
        json={"email": f"owner-{unique}@example.com", "password": "correct-horse-battery-staple"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    tenants = client.get("/tenants", headers={"Authorization": f"Bearer {token}"})
    assert tenants.status_code == 200
    assert len(tenants.json()) == 1
    return token, tenants.json()[0]["id"]


def test_authenticated_tenant_scoped_crud_and_rbac() -> None:
    token, tenant_id = _register_owner()
    headers = {"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant_id}
    collection = f"/{DOMAIN_ID}/records/{ENTITY_TYPE}"

    assert client.get(collection, headers={"X-Tenant-ID": tenant_id}).status_code == 401

    created = client.post(
        collection,
        headers=headers,
        json={"name": "Verified domain record", "status": "active", "payload": {"priority": 3}},
    )
    assert created.status_code == 201
    record_id = created.json()["id"]
    assert created.json()["tenant_id"] == tenant_id

    listed = client.get(collection, headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [record_id]

    with SessionLocal() as db:
        membership = db.scalar(select(Membership).where(Membership.tenant_id == tenant_id))
        assert membership is not None
        membership.role = "viewer"
        outsider = Tenant(name="Isolated Workspace", slug=f"isolated-workspace-{uuid4().hex}")
        db.add(outsider)
        db.commit()
        outsider_id = outsider.id

    forbidden_write = client.post(
        collection,
        headers=headers,
        json={"name": "Must not be written"},
    )
    assert forbidden_write.status_code == 403
    assert client.get(collection, headers={**headers, "X-Tenant-ID": outsider_id}).status_code == 403

    with SessionLocal() as db:
        membership = db.scalar(select(Membership).where(Membership.tenant_id == tenant_id))
        assert membership is not None
        membership.role = "owner"
        db.commit()

    item_url = f"{collection}/{record_id}"
    updated = client.patch(item_url, headers=headers, json={"status": "approved"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "approved"

    dashboard = client.get(f"/{DOMAIN_ID}/dashboard", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["counts"][ENTITY_TYPE] == 1

    deleted = client.delete(item_url, headers=headers)
    assert deleted.status_code == 204
    assert client.get(item_url, headers=headers).status_code == 404
