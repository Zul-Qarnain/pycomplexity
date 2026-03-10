"""
tests/unit/test_estimator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the full analysis pipeline using fixture algorithms.
Each test asserts the expected ``Complexity`` class is produced.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
import sys
import os

import pytest

# Make sure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pycomplexity import analyze_source, Complexity
from pycomplexity.analyzers.function_analyzer import FunctionAnalyzer
from pycomplexity.detectors.loop_detector import LoopDetector
from pycomplexity.detectors.recursion_detector import RecursionDetector
import tests.fixtures.algorithms as alg_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_func_node(source: str, func_name: str) -> ast.FunctionDef:
    """Parse *source* and return the AST node for *func_name*."""
    tree = ast.parse(textwrap.dedent(source))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return node
    raise ValueError(f"Function '{func_name}' not found in source")


def analyze_func_source(source: str, func_name: str) -> "FunctionResult":
    """Analyze a single function from source and return its FunctionResult."""
    result = analyze_source(textwrap.dedent(source))
    for func in result.functions:
        if func.name == func_name:
            return func
    raise ValueError(f"Function '{func_name}' not found in results")


def analyze_fixture(func_name: str) -> "FunctionResult":
    """Analyze a fixture function from the algorithms module."""
    source = inspect.getsource(alg_module)
    result = analyze_source(source, filepath="algorithms.py")
    for func in result.functions:
        if func.name == func_name:
            return func
    raise ValueError(f"Fixture function '{func_name}' not found")


# ---------------------------------------------------------------------------
# O(1) tests
# ---------------------------------------------------------------------------

class TestConstant:
    def test_constant_lookup(self):
        r = analyze_fixture("constant_lookup")
        assert r.complexity == Complexity.O_1

    def test_swap(self):
        r = analyze_fixture("swap")
        assert r.complexity == Complexity.O_1

    def test_confidence_high_for_constant(self):
        r = analyze_fixture("constant_lookup")
        assert r.confidence >= 0.90

    def test_simple_arithmetic(self):
        source = """
        def add(a, b):
            return a + b
        """
        r = analyze_func_source(source, "add")
        assert r.complexity == Complexity.O_1


# ---------------------------------------------------------------------------
# O(log n) tests
# ---------------------------------------------------------------------------

class TestLogarithmic:
    def test_binary_search(self):
        r = analyze_fixture("binary_search")
        assert r.complexity == Complexity.O_LOG_N

    def test_power_of_two(self):
        r = analyze_fixture("power_of_two")
        assert r.complexity == Complexity.O_LOG_N

    def test_explicit_halving_while(self):
        source = """
        def count_bits(n):
            count = 0
            while n > 0:
                n >>= 1
                count += 1
            return count
        """
        r = analyze_func_source(source, "count_bits")
        assert r.complexity == Complexity.O_LOG_N


# ---------------------------------------------------------------------------
# O(n) tests
# ---------------------------------------------------------------------------

class TestLinear:
    def test_linear_search(self):
        r = analyze_fixture("linear_search")
        assert r.complexity == Complexity.O_N

    def test_compute_sum(self):
        r = analyze_fixture("compute_sum")
        assert r.complexity == Complexity.O_N

    def test_range_n_loop(self):
        source = """
        def fill(n):
            result = []
            for i in range(n):
                result.append(i * 2)
            return result
        """
        r = analyze_func_source(source, "fill")
        assert r.complexity == Complexity.O_N


# ---------------------------------------------------------------------------
# O(n log n) tests
# ---------------------------------------------------------------------------

class TestLinearithmic:
    def test_merge_sort(self):
        r = analyze_fixture("merge_sort")
        assert r.complexity == Complexity.O_N_LOG_N

    def test_sort_and_count(self):
        r = analyze_fixture("sort_and_count")
        assert r.complexity == Complexity.O_N_LOG_N


# ---------------------------------------------------------------------------
# O(n²) tests
# ---------------------------------------------------------------------------

class TestQuadratic:
    def test_bubble_sort(self):
        r = analyze_fixture("bubble_sort")
        assert r.complexity == Complexity.O_N2

    def test_has_duplicate(self):
        r = analyze_fixture("has_duplicate")
        assert r.complexity == Complexity.O_N2

    def test_explicit_nested_for(self):
        source = """
        def matrix_print(matrix):
            for row in matrix:
                for val in row:
                    print(val)
        """
        r = analyze_func_source(source, "matrix_print")
        assert r.complexity == Complexity.O_N2


# ---------------------------------------------------------------------------
# O(n³) tests
# ---------------------------------------------------------------------------

class TestCubic:
    def test_triple_sum(self):
        r = analyze_fixture("triple_sum")
        assert r.complexity == Complexity.O_N3


# ---------------------------------------------------------------------------
# O(2^n) tests
# ---------------------------------------------------------------------------

class TestExponential:
    def test_fibonacci_naive(self):
        r = analyze_fixture("fibonacci_naive")
        assert r.complexity == Complexity.O_2N

    def test_all_subsets(self):
        r = analyze_fixture("all_subsets")
        assert r.complexity == Complexity.O_2N


# ---------------------------------------------------------------------------
# Loop detector unit tests
# ---------------------------------------------------------------------------

class TestLoopDetector:
    def test_detects_single_for_loop(self):
        source = """
        def fn(arr):
            for x in arr:
                pass
        """
        node = get_func_node(source, "fn")
        detector = LoopDetector()
        loops = detector.analyze(node)
        assert len(loops) == 1
        assert loops[0].kind == "for"
        assert loops[0].depth == 1

    def test_detects_nested_loops(self):
        source = """
        def fn(n):
            for i in range(n):
                for j in range(n):
                    pass
        """
        node = get_func_node(source, "fn")
        loops = LoopDetector().analyze(node)
        depths = sorted(l.depth for l in loops)
        assert depths == [1, 2]

    def test_detects_logarithmic_while(self):
        source = """
        def fn(n):
            while n > 1:
                n = n // 2
        """
        node = get_func_node(source, "fn")
        loops = LoopDetector().analyze(node)
        assert len(loops) == 1
        assert loops[0].is_logarithmic is True

    def test_right_shift_is_logarithmic(self):
        source = """
        def fn(n):
            while n > 0:
                n >>= 1
        """
        node = get_func_node(source, "fn")
        loops = LoopDetector().analyze(node)
        assert loops[0].is_logarithmic is True


# ---------------------------------------------------------------------------
# Recursion detector unit tests
# ---------------------------------------------------------------------------

class TestRecursionDetector:
    def test_detects_simple_recursion(self):
        source = """
        def factorial(n):
            if n == 0:
                return 1
            return n * factorial(n - 1)
        """
        node = get_func_node(source, "factorial")
        info = RecursionDetector().analyze(node)
        assert info is not None
        assert info.call_sites == 1
        assert info.has_halving is False

    def test_detects_branching_recursion(self):
        source = """
        def fib(n):
            if n <= 1:
                return n
            return fib(n-1) + fib(n-2)
        """
        node = get_func_node(source, "fib")
        info = RecursionDetector().analyze(node)
        assert info is not None
        assert info.call_sites == 2

    def test_detects_halving_recursion(self):
        source = """
        def bin_search(arr, lo, hi, target):
            if lo > hi:
                return -1
            mid = (lo + hi) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                return bin_search(arr, mid + 1, hi, target)
            else:
                return bin_search(arr, lo, mid - 1, target)
        """
        node = get_func_node(source, "bin_search")
        info = RecursionDetector().analyze(node)
        assert info is not None
        assert info.has_halving is True

    def test_no_recursion_returns_none(self):
        source = """
        def greet(name):
            return f"Hello, {name}"
        """
        node = get_func_node(source, "greet")
        info = RecursionDetector().analyze(node)
        assert info is None


# ---------------------------------------------------------------------------
# Complexity ordering
# ---------------------------------------------------------------------------

class TestComplexityOrdering:
    def test_ordering(self):
        assert Complexity.O_1 < Complexity.O_LOG_N
        assert Complexity.O_LOG_N < Complexity.O_N
        assert Complexity.O_N < Complexity.O_N_LOG_N
        assert Complexity.O_N_LOG_N < Complexity.O_N2
        assert Complexity.O_N2 < Complexity.O_N3
        assert Complexity.O_N3 < Complexity.O_2N

    def test_dominant(self):
        assert Complexity.dominant(Complexity.O_1, Complexity.O_N2) == Complexity.O_N2
        assert Complexity.dominant(Complexity.O_N_LOG_N, Complexity.O_N) == Complexity.O_N_LOG_N


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
