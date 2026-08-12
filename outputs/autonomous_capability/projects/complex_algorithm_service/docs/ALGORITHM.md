# Algorithm

The service uses Dijkstra's algorithm as the shortest-path primitive and Yen's
algorithm to enumerate K loopless alternatives. Inputs are validated before
execution. Negative or non-finite weights, duplicate edges, unknown nodes, and
blocked endpoints are rejected.

Worst-case complexity is conservatively bounded by `O(K * V * (E log V))`.
The implementation uses deterministic tie-breaking so equal-cost graphs produce
stable outputs.
