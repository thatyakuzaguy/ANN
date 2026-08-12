import pytest

from app.algorithm import Edge, k_shortest_paths, shortest_path


def test_unreachable_target_returns_no_path() -> None:
    assert shortest_path(("a", "b", "c"), (Edge("a", "b", 1),), "a", "c") is None


def test_blocked_node_is_excluded() -> None:
    edges = (Edge("a", "b", 1), Edge("b", "d", 1), Edge("a", "c", 2), Edge("c", "d", 2))
    routes = k_shortest_paths(("a", "b", "c", "d"), edges, "a", "d", 2, blocked_nodes=frozenset({"b"}))
    assert [route.nodes for route in routes] == [("a", "c", "d")]


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        shortest_path(("a", "b"), (Edge("a", "b", -1),), "a", "b")
