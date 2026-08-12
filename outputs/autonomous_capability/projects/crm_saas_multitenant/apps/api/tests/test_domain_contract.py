from app.domain_config import DOMAIN_ID, ENTITIES, INTEGRATIONS, WORKFLOWS
from app.domain_seed import seed_records


def test_domain_contract_is_specific() -> None:
    assert DOMAIN_ID == "crm"
    assert len(ENTITIES) >= 5
    assert len(WORKFLOWS) >= 3
    assert len(INTEGRATIONS) >= 3


def test_seed_covers_each_domain_entity() -> None:
    assert {item["entity_type"] for item in seed_records()} == set(ENTITIES)
