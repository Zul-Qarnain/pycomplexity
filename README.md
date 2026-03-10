# bigopy 🔍

> **Static Big-O complexity estimation for Python code via AST analysis.**
> No code execution needed — just point it at your source file.

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-bigopy-orange.svg)](https://pypi.org/project/bigopy)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

`bigopy` statically analyzes Python source files using the **Abstract Syntax Tree (AST)**
and estimates the Big-O time complexity of every function — without running your code.
```
$ bigopy analyze bubble_sort.py

============================================================
📂  bubble_sort.py
============================================================

  Function:      bubble_sort()  (line 1)
  Complexity:    O(n²)
  Confidence:    [█████████████████░░░] 85%
  Reasons:
    • doubly-nested loops (depth=2)
```

---

## Why bigopy is different

| | bigopy | Other tools |
|---|---|---|
| **Approach** | Static AST analysis | Runtime measurement |
| **Runs your code?** | ❌ Never | ✅ Must execute |
| **Works on broken code?** | ✅ Yes | ❌ No |
| **Dependencies** | Zero | numpy, etc. |
| **Graph algorithms** | ✅ O(V+E), O((V+E)logV) | ❌ No |
| **Safe for CI/CD** | ✅ Yes | ⚠️ Maybe |

---

## Installation
```bash
pip install bigopy
```

---

## Quick Start

### CLI
```bash
bigopy analyze my_module.py
bigopy analyze my_module.py --verbose
bigopy analyze src/ --format json
bigopy analyze my_module.py --only bubble_sort
```

### Python API
```python
from bigopy import analyze_file, analyze_source

# From a file
result = analyze_file("my_module.py")
for func in result.functions:
    print(f"{func.name}: {func.complexity.label} ({func.confidence:.0%})")

# From a string
source = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
result = analyze_source(source)
print(result.functions[0].complexity.label)  # O(n²)
```

---

## Detected Complexity Classes

| Class | Pattern Detected |
|---|---|
| `O(1)` | No loops, no recursion |
| `O(log n)` | Halving/doubling while loops |
| `O(n)` | Single loop over input |
| `O(n log n)` | Divide-and-conquer, sorted() |
| `O(n²)` | Doubly-nested loops |
| `O(n³)` | Triple loops, range(i*i) |
| `O(2^n)` | Branching recursion |
| `O(V+E)` | DFS, BFS graph traversal |
| `O((V+E) log V)` | Dijkstra, Prim |

---

## Project Structure
```
bigopy/
├── bigopy/
│   ├── analyzers/      # estimation engine
│   ├── detectors/      # loop, recursion, graph, builtin
│   └── reporters/      # terminal, json output
├── tests/              # test suite
├── examples/           # demo algorithms
└── README.md
```

---

## License

MIT © 2024 Zul-Qarnain
