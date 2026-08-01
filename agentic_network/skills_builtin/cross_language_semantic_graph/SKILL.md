# Cross Language Semantic Graph

Bounded symbols, imports, language boundaries, and cross-language impact evidence.

## Actions

- scan: Index bounded symbols and imports across Python, TypeScript, JavaScript, Go, Rust, Java, and C#.
- impact: Rank cross-language files and boundaries affected by supplied target paths or symbols.

## Safety

- Permissions are evaluated by the persistent ANN skill permission store.
- Mutating, terminal, Git-write, or network actions require Approval Center.
- Commands are fixed shell=False recipes; raw shell input is rejected.
- Project paths are normalized and protected ANN paths remain blocked.
- Every execution writes an audit record and bounded evidence artifacts.
