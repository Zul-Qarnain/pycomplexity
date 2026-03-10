#!/bin/bash
# ============================================================
# fix_structure.sh
# Rebuilds the correct pycomplexity project structure
# from a flat folder of files.
# Run from inside ~/Data_Science/pycomplexity/
# ============================================================

set -e  # Stop immediately if any command fails

echo "========================================"
echo "  pycomplexity structure fixer"
echo "========================================"
echo ""

# ── Step 1: Create all required directories ──────────────────
echo "[1/5] Creating directory structure..."

mkdir -p pycomplexity/analyzers
mkdir -p pycomplexity/detectors
mkdir -p pycomplexity/reporters
mkdir -p tests/fixtures
mkdir -p tests/unit
mkdir -p examples

echo "      ✓ Directories created"

# ── Step 2: Move core package files ──────────────────────────
echo "[2/5] Moving core package files..."

# __init__.py  (file manager shows it as "__init__")
[ -f __init__.py ]    && mv __init__.py    pycomplexity/__init__.py
[ -f __init___py ]    && mv __init___py    pycomplexity/__init__.py
[ -f "__init__.py" ]  && mv "__init__.py"  pycomplexity/__init__.py

# cli and models
[ -f cli.py ]    && mv cli.py    pycomplexity/cli.py
[ -f models.py ] && mv models.py pycomplexity/models.py

echo "      ✓ Core files moved"

# ── Step 3: Move detector files ───────────────────────────────
echo "[3/5] Moving detector files..."

[ -f loop_detector.py ]      && mv loop_detector.py      pycomplexity/detectors/loop_detector.py
[ -f recursion_detector.py ] && mv recursion_detector.py pycomplexity/detectors/recursion_detector.py
[ -f builtin_detector.py ]   && mv builtin_detector.py   pycomplexity/detectors/builtin_detector.py

echo "      ✓ Detectors moved"

# ── Step 4: Move analyzer files ───────────────────────────────
echo "[4/5] Moving analyzer and reporter files..."

[ -f estimator.py ]        && mv estimator.py        pycomplexity/analyzers/estimator.py
[ -f function_analyzer.py ] && mv function_analyzer.py pycomplexity/analyzers/function_analyzer.py
[ -f module_analyzer.py ]  && mv module_analyzer.py  pycomplexity/analyzers/module_analyzer.py

[ -f terminal.py ]      && mv terminal.py      pycomplexity/reporters/terminal.py
[ -f json_reporter.py ] && mv json_reporter.py pycomplexity/reporters/json_reporter.py

[ -f algorithms.py ]       && mv algorithms.py       tests/fixtures/algorithms.py
[ -f test_estimator.py ]   && mv test_estimator.py   tests/unit/test_estimator.py
[ -f demo_algorithms.py ]  && mv demo_algorithms.py  examples/demo_algorithms.py

echo "      ✓ Analyzers and reporters moved"

# ── Step 5: Create all required __init__.py files ─────────────
echo "[5/5] Creating __init__.py files for all sub-packages..."

# Create them only if they don't exist yet
[ ! -f pycomplexity/analyzers/__init__.py ] && echo '"""Analyzer modules."""' > pycomplexity/analyzers/__init__.py
[ ! -f pycomplexity/detectors/__init__.py ] && echo '"""Detector modules."""' > pycomplexity/detectors/__init__.py
[ ! -f pycomplexity/reporters/__init__.py ] && echo '"""Reporter modules."""' > pycomplexity/reporters/__init__.py
[ ! -f tests/__init__.py ]                  && touch tests/__init__.py
[ ! -f tests/fixtures/__init__.py ]         && touch tests/fixtures/__init__.py
[ ! -f tests/unit/__init__.py ]             && touch tests/unit/__init__.py

echo "      ✓ __init__.py files created"

# ── Final: Print the resulting tree ───────────────────────────
echo ""
echo "========================================"
echo "  Final structure:"
echo "========================================"
find . -not -path './.git/*' \
       -not -name '__pycache__' \
       -not -path '*/__pycache__/*' \
       -not -name 'fix_structure.sh' \
  | sort | sed 's|[^/]*/|  |g'

echo ""
echo "========================================"
echo "  Now installing the package..."
echo "========================================"
pip install -e . --quiet && echo "  ✓ Installation successful!"

echo ""
echo "========================================"
echo "  Running a quick smoke test..."
echo "========================================"
python -c "
from pycomplexity import analyze_source, Complexity

source = '''
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target: return mid
        elif arr[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1

def fibonacci(n):
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)
'''

result = analyze_source(source)
print('')
for f in result.functions:
    conf_bar = '█' * int(f.confidence * 20) + '░' * (20 - int(f.confidence * 20))
    print(f'  {f.name:20s}  {f.complexity.label:12s}  [{conf_bar}] {f.confidence:.0%}')
print('')
print('  ✓ Library is working correctly!')
"

echo ""
echo "========================================"
echo "  Try it yourself:"
echo "  pycomplexity analyze examples/demo_algorithms.py"
echo "========================================"
