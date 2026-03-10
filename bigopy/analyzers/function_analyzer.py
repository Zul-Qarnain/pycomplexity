"""
bigopy.analyzers.function_analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Orchestrates the full analysis pipeline per function:
AST node → LoopDetector → RecursionDetector → GraphDetector
         → BuiltinDetector → ComplexityEstimator → FunctionResult
"""

from __future__ import annotations
import ast
from typing import Optional

from bigopy.analyzers.estimator import ComplexityEstimator
from bigopy.detectors.builtin_detector import find_known_calls
from bigopy.detectors.loop_detector import LoopDetector
from bigopy.detectors.recursion_detector import RecursionDetector
from bigopy.detectors.graph_detector import detect_graph_traversal
from bigopy.models import FunctionResult


class FunctionAnalyzer:

    def __init__(self, class_name: Optional[str] = None) -> None:
        self._loop_detector      = LoopDetector()
        self._recursion_detector = RecursionDetector()
        self._estimator          = ComplexityEstimator()
        self._class_name         = class_name

    def analyze(self, func_node: ast.FunctionDef) -> FunctionResult:
        name = func_node.name
        if self._class_name:
            name = f"{self._class_name}.{name}"

        start_line = func_node.lineno
        end_line   = getattr(func_node, "end_lineno", None)

        loops           = self._loop_detector.analyze(func_node)
        recursion       = self._recursion_detector.analyze(func_node)
        builtin_calls   = find_known_calls(func_node)
        graph_traversal = detect_graph_traversal(func_node)

        result = self._estimator.estimate(
            name            = name,
            loops           = loops,
            recursion       = recursion,
            builtin_calls   = builtin_calls,
            graph_traversal = graph_traversal,
            start_line      = start_line,
            end_line        = end_line,
        )
        return result
