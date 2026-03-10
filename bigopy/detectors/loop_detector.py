"""
bigopy.detectors.loop_detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Detects for/while loops and classifies each one.
Now includes range-power analysis to distinguish:
    range(i)   → adds 1 power
    range(i*i) → adds 2 powers  (key fix for O(n³) detection)
"""

from __future__ import annotations
import ast
from typing import List, Set
from bigopy.models import LoopInfo
from bigopy.detectors.range_analyzer import get_range_power

_INPUT_SIZE_CALLS: Set[str] = {"len", "range", "enumerate", "zip"}


def _is_input_dependent_iter(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Call):
        func = node.func
        func_name = ""
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr
        if func_name in _INPUT_SIZE_CALLS:
            return True
        for arg in node.args:
            if _is_input_dependent_iter(arg):
                return True
    if isinstance(node, ast.Subscript):
        return _is_input_dependent_iter(node.value)
    if isinstance(node, ast.Attribute):
        return _is_input_dependent_iter(node.value)
    return False


def _is_logarithmic_while(body: List[ast.stmt]) -> bool:
    for stmt in body:
        if isinstance(stmt, ast.AugAssign):
            op = stmt.op
            if isinstance(op, (ast.FloorDiv, ast.RShift)):
                return True
            if isinstance(op, ast.Mult):
                if isinstance(stmt.value, ast.Constant):
                    if isinstance(stmt.value.value, (int, float)):
                        if stmt.value.value > 1:
                            return True
            if isinstance(op, ast.LShift):
                return True
        if isinstance(stmt, ast.Assign):
            val = stmt.value
            if isinstance(val, ast.BinOp):
                op    = val.op
                left  = val.left
                right = val.right
                if isinstance(op, (ast.FloorDiv, ast.RShift)):
                    return True
                if isinstance(op, ast.Mult):
                    if isinstance(right, ast.Constant):
                        if isinstance(right.value, (int, float)):
                            if right.value > 1:
                                return True
                    if isinstance(left, ast.Constant):
                        if isinstance(left.value, (int, float)):
                            if left.value > 1:
                                return True
                if isinstance(op, ast.LShift):
                    return True
    return False


class LoopDetector(ast.NodeVisitor):

    def __init__(self) -> None:
        self.loops: List[LoopInfo] = []
        self._depth: int = 0

    def analyze(self, func_node: ast.FunctionDef) -> List[LoopInfo]:
        self.loops = []
        self._depth = 0
        self.visit(func_node)
        return self.loops

    def visit_For(self, node: ast.For) -> None:
        self._depth += 1

        # Get how many powers of n this range contributes
        range_power = get_range_power(node.iter)
        input_dep   = _is_input_dependent_iter(node.iter)

        loop = LoopInfo(
            kind="for",
            depth=self._depth,
            line=node.lineno,
            is_input_dependent=input_dep,
            is_logarithmic=False,
        )
        # Store range power as extra attribute
        loop.range_power = range_power
        self.loops.append(loop)
        self.generic_visit(node)
        self._depth -= 1

    def visit_While(self, node: ast.While) -> None:
        self._depth += 1
        is_log = _is_logarithmic_while(node.body)
        loop = LoopInfo(
            kind="while",
            depth=self._depth,
            line=node.lineno,
            is_input_dependent=not is_log,
            is_logarithmic=is_log,
        )
        loop.range_power = 1
        self.loops.append(loop)
        self.generic_visit(node)
        self._depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self._depth == 0 and not self.loops:
            self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef
