from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class EdgeInput(BaseModel):
    source: str = Field(min_length=1, max_length=120)
    target: str = Field(min_length=1, max_length=120)
    weight: float = Field(ge=0, le=1_000_000)


class RouteRequest(BaseModel):
    nodes: list[str] = Field(min_length=2, max_length=10_000)
    edges: list[EdgeInput] = Field(min_length=1, max_length=100_000)
    source: str
    target: str
    k: int = Field(default=3, ge=1, le=25)
    blocked_nodes: set[str] = Field(default_factory=set)
    max_cost: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_contract(self) -> "RouteRequest":
        node_set = set(self.nodes)
        if len(node_set) != len(self.nodes):
            raise ValueError("nodes must be unique")
        if self.source not in node_set or self.target not in node_set:
            raise ValueError("source and target must exist in nodes")
        if self.source in self.blocked_nodes or self.target in self.blocked_nodes:
            raise ValueError("source and target cannot be blocked")
        if not self.blocked_nodes.issubset(node_set):
            raise ValueError("blocked_nodes must exist in nodes")
        for edge in self.edges:
            if edge.source not in node_set or edge.target not in node_set:
                raise ValueError("every edge endpoint must exist in nodes")
        return self


class RouteResult(BaseModel):
    nodes: list[str]
    cost: float


class RouteResponse(BaseModel):
    routes: list[RouteResult]
    algorithm: str
    complexity: str
    graph_nodes: int
    graph_edges: int
    elapsed_ms: float
