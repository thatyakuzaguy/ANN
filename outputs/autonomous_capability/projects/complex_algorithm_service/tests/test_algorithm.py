from app.algorithm import Edge, k_shortest_paths, shortest_path


NODES = ("a", "b", "c", "d")
EDGES = (
    Edge("a", "b", 1),
    Edge("b", "d", 1),
    Edge("a", "c", 1),
    Edge("c", "d", 2),
    Edge("b", "c", 0.5),
)


def test_shortest_path_is_optimal() -> None:
    result = shortest_path(NODES, EDGES, "a", "d")
    assert result is not None
    assert result.nodes == ("a", "b", "d")
    assert result.cost == 2


def test_k_shortest_paths_are_cost_ordered_and_unique() -> None:
    routes = k_shortest_paths(NODES, EDGES, "a", "d", 3)
    assert len({route.nodes for route in routes}) == len(routes)
    assert [route.cost for route in routes] == sorted(route.cost for route in routes)
    assert routes[0].nodes == ("a", "b", "d")
