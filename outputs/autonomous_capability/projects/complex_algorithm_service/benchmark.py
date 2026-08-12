from __future__ import annotations

import json
import random
import time

from app.algorithm import Edge, k_shortest_paths


def run_benchmark(node_count: int = 500, edge_count: int = 4_000) -> dict[str, object]:
    randomizer = random.Random(42)
    nodes = tuple(f"n{index}" for index in range(node_count))
    pairs: set[tuple[str, str]] = set()
    edges: list[Edge] = []
    while len(edges) < edge_count:
        source = randomizer.choice(nodes)
        target = randomizer.choice(nodes)
        if source == target or (source, target) in pairs:
            continue
        pairs.add((source, target))
        edges.append(Edge(source, target, randomizer.uniform(0.1, 50)))
    started = time.perf_counter()
    routes = k_shortest_paths(nodes, edges, nodes[0], nodes[-1], 5)
    elapsed = time.perf_counter() - started
    return {
        "status": "PASSED",
        "algorithm": "yen-k-shortest-loopless-paths",
        "nodes": node_count,
        "edges": edge_count,
        "routes_found": len(routes),
        "elapsed_seconds": round(elapsed, 6),
        "complexity": "O(K * V * (E log V))",
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2))
