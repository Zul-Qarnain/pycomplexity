#!/bin/bash
set -e
PYBIN="python3"

echo ""
echo "========================================"
echo "  pycomplexity – Fix & Install Script"
echo "========================================"
echo ""

if [ ! -f "pyproject.toml" ]; then
  echo "ERROR: Run from inside the pycomplexity root folder."
  exit 1
fi

echo "[1/3] Installing pycomplexity..."
if pip3 install -e . 2>/dev/null; then
  echo "      ✓ Installed via pip3"
elif pip install -e . 2>/dev/null; then
  echo "      ✓ Installed via pip"
else
  echo "      ⚠  pip failed – using PYTHONPATH fallback"
  export PYTHONPATH="$(pwd):$PYTHONPATH"
fi

echo ""
echo "[2/3] Running smoke test..."
PYTHONPATH="$(pwd):$PYTHONPATH" $PYBIN - << 'PYEOF'
import sys, os
sys.path.insert(0, os.getcwd())

from pycomplexity import analyze_source, Complexity

source = """
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
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def find_max(arr):
    best = arr[0]
    for x in arr:
        if x > best:
            best = x
    return best

def constant_swap(a, b):
    return b, a
"""

result = analyze_source(source)
expected = {
    "bubble_sort":   Complexity.O_N2,
    "binary_search": Complexity.O_LOG_N,
    "fibonacci":     Complexity.O_2N,
    "find_max":      Complexity.O_N,
    "constant_swap": Complexity.O_1,
}

print("")
print("  Function              Complexity     Confidence  Status")
print("  " + "-"*58)
passed = failed = 0
for f in result.functions:
    exp = expected.get(f.name)
    if exp is None:
        continue
    ok = f.complexity == exp
    status = "✓ PASS" if ok else f"✗ FAIL (expected {exp.label})"
    bar = "█" * int(f.confidence * 15) + "░" * (15 - int(f.confidence * 15))
    print(f"  {f.name:20s}  {f.complexity.label:12s}  [{bar}] {f.confidence:.0%}  {status}")
    if ok: passed += 1
    else:  failed += 1

print("  " + "-"*58)
print(f"  Result: {passed} passed, {failed} failed")
if failed == 0:
    print("  ✓ Library is working correctly!")
else:
    sys.exit(1)
PYEOF

echo ""
echo "[3/3] Testing CLI on demo file..."
PYTHONPATH="$(pwd):$PYTHONPATH" $PYBIN -m pycomplexity.cli analyze examples/demo_algorithms.py

echo ""
echo "========================================"
echo "  ALL DONE! Use it like this:"
echo "  python3 -m pycomplexity.cli analyze yourfile.py"
echo "  python3 -m pycomplexity.cli analyze yourfile.py --verbose"
echo "  python3 -m pycomplexity.cli analyze yourfile.py --format json"
echo "========================================"
