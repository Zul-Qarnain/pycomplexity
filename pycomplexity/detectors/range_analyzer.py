"""
pycomplexity.detectors.range_analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Analyzes the BOUND of a loop's range() to detect
how many extra powers of n the inner loop adds.

Examples:
    range(n)        → power=1  (linear inner loop)
    range(i)        → power=1  (depends on outer var)
    range(i*i)      → power=2  (quadratic inner loop)
    range(i**2)     → power=2  (quadratic inner loop)
    range(i*i*i)    → power=3  (cubic inner loop)
    range(n*n)      → power=2  (quadratic inner loop)
"""

import ast
from typing import Optional

# Names that represent loop variables or input size
_LOOP_VAR_NAMES = {
    "i", "j", "k", "n", "m", "x", "y", "z",
    "idx", "index", "count", "size", "num"
}


def _count_variable_multiplications(node: ast.expr) -> int:
    """
    Count how many times a variable is multiplied together.

    range(i)        → 1   (just i)
    range(i*i)      → 2   (i multiplied twice)
    range(i*i*i)    → 3   (i multiplied three times)
    range(i**2)     → 2   (i squared)
    range(i**3)     → 3   (i cubed)
    range(n*m)      → 2   (two variables)
    """
    if isinstance(node, ast.Name):
        if node.id in _LOOP_VAR_NAMES:
            return 1
        return 0

    # i ** 2  or  i ** 3
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        base  = node.left
        exp   = node.right
        if isinstance(base, ast.Name) and base.id in _LOOP_VAR_NAMES:
            if isinstance(exp, ast.Constant) and isinstance(exp.value, int):
                return exp.value

    # i * i   or   i * i * i   (left-recursive AST)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        left_power  = _count_variable_multiplications(node.left)
        right_power = _count_variable_multiplications(node.right)
        if left_power > 0 or right_power > 0:
            return left_power + right_power

    return 0


def get_range_power(iter_node: ast.expr) -> int:
    """
    Given the iterator expression of a for-loop, return the
    'power' contributed by the inner loop bound.

    Returns:
        0 → constant bound (not input-dependent)
        1 → linear bound   range(n), range(i), range(len(arr))
        2 → quadratic bound range(i*i), range(i**2), range(n*n)
        3 → cubic bound    range(i*i*i), range(i**3)
    """
    # range(...)
    if isinstance(iter_node, ast.Call):
        func = iter_node.func
        func_name = ""
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr

        if func_name == "range":
            # range(stop)  or  range(start, stop)  or  range(start, stop, step)
            # The stop argument is the one that determines iterations
            args = iter_node.args
            if len(args) == 1:
                stop = args[0]
            elif len(args) >= 2:
                stop = args[1]
            else:
                return 1

            power = _count_variable_multiplications(stop)
            return max(power, 1) if power > 0 else 0

        # len(arr), enumerate(arr), etc.
        if func_name in {"len", "enumerate", "zip"}:
            return 1

    # bare variable: for x in arr
    if isinstance(iter_node, ast.Name):
        return 1

    return 1
