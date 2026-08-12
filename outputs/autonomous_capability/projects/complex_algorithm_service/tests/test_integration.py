from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_route_optimizer_api() -> None:
    response = client.post(
        "/v1/routes/optimize",
        json={
            "nodes": ["a", "b", "c"],
            "edges": [
                {"source": "a", "target": "b", "weight": 1},
                {"source": "b", "target": "c", "weight": 1},
                {"source": "a", "target": "c", "weight": 3},
            ],
            "source": "a",
            "target": "c",
            "k": 2,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["routes"][0] == {"nodes": ["a", "b", "c"], "cost": 2.0}
    assert payload["complexity"].startswith("O(")
