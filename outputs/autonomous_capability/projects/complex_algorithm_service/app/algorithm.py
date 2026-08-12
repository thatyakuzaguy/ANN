from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from collections.abc import Iterable


@dataclass(frozen=True, order=True)
class Edge:
    source: str
    target: str
    weight: float


@dataclass(frozen=True)
class PathResult:
    nodes: tuple[str, ...]
    cost: float


def _adjacency(nodes: Iterable[str], edges: Iterable[Edge]) -> dict[str, tuple[Edge, ...]]:
    graph: dict[str, list[Edge]] = {node: [] for node in nodes}
    for edge in edges:
        if edge.weight < 0 or not math.isfinite(edge.weight):
            raise ValueError("edge weights must be finite and non-negative")
        if edge.source not in graph or edge.target not in graph:
            raise ValueError("edge endpoint is not present in nodes")
        graph[edge.source].append(edge)
    return {node: tuple(sorted(outgoing, key=lambda item: (item.target, item.weight))) for node, outgoing in graph.items()}


def shortest_path(
    nodes: Iterable[str],
    edges: Iterable[Edge],
    source: str,
    target: str,
    *,
    banned_nodes: frozenset[str] = frozenset(),
    banned_edges: frozenset[tuple[str, str]] = frozenset(),
) -> PathResult | None:
    """Return a deterministic Dijkstra path in O((V + E) log V)."""

    node_tuple = tuple(dict.fromkeys(nodes))
    if source not in node_tuple or target not in node_tuple:
        raise ValueError("source and target must exist in nodes")
    if source in banned_nodes or target in banned_nodes:
        return None
    graph = _adjacency(node_tuple, edges)
    queue: list[tuple[float, tuple[str, ...], str]] = [(0.0, (source,), source)]
    best: dict[str, float] = {source: 0.0}
    while queue:
        cost, path, current = heapq.heappop(queue)
        if cost > best.get(current, math.inf):
            continue
        if current == target:
            return PathResult(path, cost)
        for edge in graph[current]:
            if edge.target in banned_nodes or (edge.source, edge.target) in banned_edges:
                continue
            if edge.target in path:
                continue
            candidate = cost + edge.weight
            if candidate <= best.get(edge.target, math.inf):
                best[edge.target] = candidate
                heapq.heappush(queue, (candidate, (*path, edge.target), edge.target))
    return None


def _path_cost(path: tuple[str, ...], edge_weights: dict[tuple[str, str], float]) -> float:
    try:
        return sum(edge_weights[(source, target)] for source, target in zip(path, path[1:]))
    except KeyError as exc:
        raise ValueError("path contains an edge that is not present in the graph") from exc


def k_shortest_paths(
    nodes: Iterable[str],
    edges: Iterable[Edge],
    source: str,
    target: str,
    k: int,
    *,
    blocked_nodes: frozenset[str] = frozenset(),
    max_cost: float | None = None,
) -> list[PathResult]:
    """Return up to K loopless paths using Yen's algorithm.

    Complexity is O(K * V * (E log V)) in the conservative worst case.
    Candidate ordering is deterministic by total cost and node sequence.
    """

    if k < 1 or k > 25:
        raise ValueError("k must be between 1 and 25")
    node_tuple = tuple(dict.fromkeys(nodes))
    edge_tuple = tuple(edges)
    first = shortest_path(
        node_tuple,
        edge_tuple,
        source,
        target,
        banned_nodes=blocked_nodes,
    )
    if first is None or (max_cost is not None and first.cost > max_cost):
        return []
    accepted = [first]
    candidates: list[tuple[float, tuple[str, ...]]] = []
    candidate_paths: set[tuple[str, ...]] = set()
    edge_weights = {(edge.source, edge.target): edge.weight for edge in edge_tuple}

    for _rank in range(1, k):
        previous = accepted[-1].nodes
        for spur_index in range(len(previous) - 1):
            root = previous[: spur_index + 1]
            removed_edges = {
                (path.nodes[spur_index], path.nodes[spur_index + 1])
                for path in accepted
                if len(path.nodes) > spur_index and path.nodes[: spur_index + 1] == root
            }
            spur = shortest_path(
                node_tuple,
                edge_tuple,
                root[-1],
                target,
                banned_nodes=frozenset({*blocked_nodes, *root[:-1]}),
                banned_edges=frozenset(removed_edges),
            )
            if spur is None:
                continue
            total_nodes = (*root[:-1], *spur.nodes)
            if total_nodes in candidate_paths or any(item.nodes == total_nodes for item in accepted):
                continue
            total_cost = _path_cost(total_nodes, edge_weights)
            if max_cost is not None and total_cost > max_cost:
                continue
            candidate_paths.add(total_nodes)
            heapq.heappush(candidates, (total_cost, total_nodes))
        if not candidates:
            break
        cost, selected = heapq.heappop(candidates)
        candidate_paths.discard(selected)
        accepted.append(PathResult(selected, cost))
    return accepted
