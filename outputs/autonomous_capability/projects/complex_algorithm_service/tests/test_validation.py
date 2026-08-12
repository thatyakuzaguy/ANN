import pytest

from app.schemas import EdgeInput, RouteRequest
from app.validation import normalize_request


def test_duplicate_edge_is_rejected() -> None:
    payload = RouteRequest(
        nodes=["a", "b"],
        edges=[EdgeInput(source="a", target="b", weight=1), EdgeInput(source="a", target="b", weight=2)],
        source="a",
        target="b",
    )
    with pytest.raises(ValueError, match="duplicate"):
        normalize_request(payload)


def test_unknown_endpoint_is_rejected_by_contract() -> None:
    with pytest.raises(ValueError, match="edge endpoint"):
        RouteRequest(
            nodes=["a", "b"],
            edges=[EdgeInput(source="a", target="c", weight=1)],
            source="a",
            target="b",
        )
