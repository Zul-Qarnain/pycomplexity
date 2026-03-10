# pycomplexity 🔍

> **Automatic Big-O time complexity estimation for Python code via AST analysis.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-13%2F13%20passing-brightgreen.svg)]()
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

`pycomplexity` statically analyzes Python source files using the **Abstract Syntax Tree (AST)** and applies heuristic pattern detection to estimate the Big-O time complexity of every function and method — no runtime required.

```
$ pycomplexity analyze bubble_sort.py

============================================================
📂  bubble_sort.py
============================================================

  Function:      bubble_sort()  (line 1)
  Complexity:    O(n²)
  Confidence:    [█████████████████░░░] 85%
  Reasons:
    • doubly-nested loops (depth=2)
    • inner for-loop (line 4)
```

---

## Features

| Complexity Class | Pattern Detected |
|---|---|
| `O(1)` | No loops, no recursion, no expensive builtins |
| `O(log n)` | Halving `while` loops (`n //= 2`, `n >>= 1`), binary-search recursion |
| `O(n)` | Single `for`/`while` over input, `sorted()`, `max()`, `sum()` etc. |
| `O(n log n)` | Divide-and-conquer recursion, `sorted()` inside a loop |
| `O(n²)` | Doubly-nested loops |
| `O(n³)` | Triply-nested loops |
| `O(2^n)` | Branching recursion (Fibonacci, subsets), result-doubling patterns |

Additional capabilities:
- **Confidence scoring** – each estimate comes with a `[0.0, 1.0]` confidence value
- **Evidence trail** – human-readable reasons explaining every estimate
- **JSON output** – machine-readable for CI pipelines and tooling
- **Zero dependencies** – pure Python standard library
- **Public Python API** – embed in your own tools

---

## Installation

```bash
pip install pycomplexity
```

---

## Quick Start

### CLI

```bash
# Analyze a single file
pycomplexity analyze my_module.py

# Verbose mode (shows all evidence)
pycomplexity analyze my_module.py --verbose

# Analyze an entire directory
pycomplexity analyze src/

# JSON output (great for CI)
pycomplexity analyze src/ --format json --output report.json

# Only specific functions
pycomplexity analyze my_module.py --only bubble_sort merge_sort
```

### Python API

```python
from pycomplexity import analyze_file, analyze_source

# From a file
result = analyze_file("my_module.py")
for func in result.functions:
    print(f"{func.name}: {func.complexity.label}  (confidence: {func.confidence:.0%})")

# From a source string
source = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
result = analyze_source(source)
func = result.functions[0]
print(func.complexity.label)   # O(n²)
print(func.confidence)         # 0.85
print(func.reasons)            # ['[O(n²)] doubly-nested loops (depth=2)', ...]
```

---

## How It Works

### Architecture

```
Source Code (.py)
      │
      ▼
 ast.parse()          ← Python's built-in AST parser
      │
      ▼
 ModuleAnalyzer       ← walks the module, finds all functions/methods
      │
      ├── FunctionAnalyzer (per function)
      │         │
      │         ├── LoopDetector      → LoopInfo[]
      │         │     • for-loop depth
      │         │     • while-loop halving (n //= 2, n >>= 1)
      │         │     • input dependency (range(n), len(arr))
      │         │
      │         ├── RecursionDetector → RecursionInfo?
      │         │     • call-site count (branching)
      │         │     • argument halving (divide-and-conquer)
      │         │     • result-doubling pattern (subsets)
      │         │
      │         ├── BuiltinDetector   → [(Complexity, desc, line)]
      │         │     • sorted(), heapq, bisect, max, sum, etc.
      │         │
      │         └── ComplexityEstimator → FunctionResult
      │               (rule-based decision tree)
      │
      ▼
 ModuleResult
      │
      ├── TerminalReporter  → colored CLI output
      └── JsonReporter      → machine-readable JSON
```

### Decision Tree

The estimator applies rules in this priority order:

```
1. Recursion detected?
   ├── has_halving=True, call_sites≥2  → O(n log n)  [divide-and-conquer]
   ├── has_halving=True, call_sites=1  → O(log n)    [binary search style]
   ├── call_sites ≥ 2                  → O(2^n)      [branching recursion]
   └── call_sites = 1                  → O(n)        [linear recursion]

2. Loops detected?
   ├── logarithmic while + outer loop  → O(n log n)
   ├── logarithmic while only          → O(log n)
   ├── max_depth ≥ 3                   → O(n³)
   ├── max_depth = 2                   → O(n²)
   └── single loop                     → O(n)

3. Expensive builtin calls (sorted, heapq, etc.) → per lookup table

4. None of the above                   → O(1)
```

---

## Project Structure

```
pycomplexity/
├── pycomplexity/
│   ├── __init__.py              # Public API: analyze_file(), analyze_source()
│   ├── models.py                # Complexity enum, FunctionResult, ModuleResult
│   ├── cli.py                   # argparse CLI entry point
│   ├── analyzers/
│   │   ├── module_analyzer.py   # Parses files, walks ClassDef/FunctionDef
│   │   ├── function_analyzer.py # Orchestrates the detector pipeline
│   │   └── estimator.py         # Rule-based complexity decision tree
│   ├── detectors/
│   │   ├── loop_detector.py     # For/while loop classification
│   │   ├── recursion_detector.py# Recursive call pattern detection
│   │   └── builtin_detector.py  # Known-complexity stdlib call lookup
│   └── reporters/
│       ├── terminal.py          # Colored ANSI terminal output
│       └── json_reporter.py     # JSON serialization
├── tests/
│   ├── fixtures/algorithms.py   # Reference algorithms at every O class
│   └── unit/test_estimator.py   # Full test suite (13 fixture tests + unit)
├── examples/
│   └── demo_algorithms.py       # Showcase file for demos
├── pyproject.toml               # Modern packaging (PEP 517/621)
└── README.md
```

---

## Roadmap

### ✅ MVP (v0.1) – Shipped
- AST-based loop & recursion detection
- All major complexity classes (O(1) through O(2^n))
- Confidence scoring
- CLI with terminal and JSON output
- Zero-dependency implementation

### 🚧 v0.2 – Precision
- [ ] Symbolic loop bound analysis (detect `range(n*m)` → O(n·m))
- [ ] Context-sensitive input-size tracking
- [ ] Better mutual recursion detection
- [ ] `--fail-above O(n²)` CI guard flag

### 🔭 v0.3 – Visualization
- [ ] ASCII complexity growth chart per function
- [ ] HTML report with syntax-highlighted annotations
- [ ] VS Code extension integration

### 🔭 v0.4 – Ecosystem
- [ ] GitHub Action for PR complexity regression checks
- [ ] `pycomplexity scan github:user/repo` remote scanning
- [ ] Pre-commit hook support
- [ ] Jupyter notebook magic: `%%complexity`

### 🔭 v1.0 – Symbolic Analysis
- [ ] Integration with `sympy` for algebraic loop-bound inference
- [ ] Master Theorem solver for recurrence relations
- [ ] Amortized analysis for data structure methods

---

## Known Limitations

- **Heuristic-based**: estimates are best-effort, not proofs.
- **No data-flow analysis**: loop bounds expressed through intermediate variables may be missed (though many common patterns are handled).
- **No amortized analysis**: `list.append()` is treated as O(1) even though amortized analysis is more nuanced.
- **External calls**: if your function calls a user-defined O(n²) helper, that helper's complexity is not propagated upward.

---

## Contributing

1. Fork the repository
2. Add your algorithm to `tests/fixtures/algorithms.py` with a comment indicating its expected complexity
3. Add a test case to `tests/unit/test_estimator.py`
4. Run `python -m pytest tests/ -v`
5. Submit a PR

---

## License

MIT © 2024 pycomplexity contributors
