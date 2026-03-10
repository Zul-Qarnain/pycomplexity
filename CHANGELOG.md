# Changelog

All notable changes to pycomplexity are documented here.

## [0.1.0] - 2024-03-10

### Added
- AST-based complexity analysis engine
- Loop detector: for/while loops, nested loops, logarithmic loops
- Recursion detector: linear, branching, divide-and-conquer
- Graph detector: DFS, BFS → O(V+E), Dijkstra → O((V+E) log V)
- Builtin detector: sorted, heapq, bisect, max, sum, etc.
- Complexity classes: O(1), O(log n), O(n), O(n log n), O(n²), O(n³), O(2^n)
- Confidence scoring for every estimate
- Evidence trail explaining each estimate
- CLI: pycomplexity analyze file.py
- JSON output format
- Terminal color output
- Zero dependencies (pure Python stdlib)

## [Unreleased]

### Planned
- Symbolic loop bound analysis (range(i*i) → O(n³))
- HTML report output
- VS Code extension
- GitHub Action for CI complexity checks
