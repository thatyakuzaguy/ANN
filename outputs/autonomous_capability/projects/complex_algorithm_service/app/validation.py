from __future__ import annotations

from .algorithm import Edge
from .schemas import RouteRequest


def normalize_request(payload: RouteRequest) -> tuple[tuple[str, ...], tuple[Edge, ...]]:
    """Normalize graph input and reject ambiguous duplicate edges."""

    seen: set[tuple[str, str]] = set()
    edges: list[Edge] = []
    for item in payload.edges:
        key = (item.source, item.target)
        if key in seen:
            raise ValueError(f"duplicate directed edge: {item.source}->{item.target}")
        seen.add(key)
        edges.append(Edge(item.source, item.target, item.weight))
    return tuple(payload.nodes), tuple(edges)
