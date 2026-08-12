# API

`POST /v1/routes/optimize` accepts nodes, weighted directed edges, source,
target, K, blocked nodes, and an optional maximum cost. The response includes
ordered loopless routes, cost, graph size, measured latency, and complexity.
