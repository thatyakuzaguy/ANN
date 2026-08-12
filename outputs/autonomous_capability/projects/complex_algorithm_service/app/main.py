from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .algorithm import k_shortest_paths
from .metrics import measure
from .schemas import RouteRequest, RouteResponse, RouteResult
from .validation import normalize_request


app = FastAPI(title="Constraint-Aware Route Optimizer", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "algorithm": "yen-k-shortest-loopless-paths"}


@app.post("/v1/routes/optimize", response_model=RouteResponse)
def optimize_routes(payload: RouteRequest) -> RouteResponse:
    try:
        nodes, edges = normalize_request(payload)
        with measure() as timer:
            routes = k_shortest_paths(
                nodes,
                edges,
                payload.source,
                payload.target,
                payload.k,
                blocked_nodes=frozenset(payload.blocked_nodes),
                max_cost=payload.max_cost,
            )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RouteResponse(
        routes=[RouteResult(nodes=list(route.nodes), cost=route.cost) for route in routes],
        algorithm="yen-k-shortest-loopless-paths",
        complexity="O(K * V * (E log V))",
        graph_nodes=len(nodes),
        graph_edges=len(edges),
        elapsed_ms=round(timer.elapsed_ms, 3),
    )
