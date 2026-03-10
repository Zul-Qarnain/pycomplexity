"""
bigopy.analyzers.module_analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parses a Python source file (or source string) and runs
``FunctionAnalyzer`` on every top-level function and every method in
every class.

The result is a ``ModuleResult`` containing one ``FunctionResult`` per
analysed callable.
"""

from __future__ import annotations

import ast
import traceback
from pathlib import Path
from typing import List, Optional, Union

from bigopy.analyzers.function_analyzer import FunctionAnalyzer
from bigopy.models import FunctionResult, ModuleResult


class ModuleAnalyzer:
    """
    Entry-point for file-level analysis.

    Usage::

        analyzer = ModuleAnalyzer()

        # From a file path
        result = analyzer.analyze_file("my_module.py")

        # From a source string
        result = analyzer.analyze_source(source_code, filepath="<string>")
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_file(self, filepath: Union[str, Path]) -> ModuleResult:
        """
        Parse *filepath* and return a ``ModuleResult``.

        If the file cannot be read or parsed, the error is captured in
        ``ModuleResult.errors`` and an empty function list is returned –
        this keeps the CLI from crashing on syntax errors in user code.
        """
        path = Path(filepath)
        result = ModuleResult(filepath=str(path))

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            result.errors.append(f"Cannot read file: {exc}")
            return result

        return self.analyze_source(source, filepath=str(path))

    def analyze_source(
        self,
        source: str,
        filepath: str = "<string>",
    ) -> ModuleResult:
        """
        Parse *source* and return a ``ModuleResult``.

        Parameters
        ----------
        source:
            Raw Python source code.
        filepath:
            Label used in the result (does not need to be a real path).
        """
        result = ModuleResult(filepath=filepath)

        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError as exc:
            result.errors.append(f"SyntaxError: {exc}")
            return result

        result.functions = self._walk_tree(tree)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _walk_tree(self, tree: ast.Module) -> List[FunctionResult]:
        """Walk *tree* and return one ``FunctionResult`` per callable."""
        results: List[FunctionResult] = []

        for node in ast.walk(tree):
            # ── Top-level functions ────────────────────────────────────────
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip methods – they are handled inside ClassDef processing
                if not self._is_method(node, tree):
                    analyzer = FunctionAnalyzer()
                    try:
                        results.append(analyzer.analyze(node))
                    except Exception:  # pylint: disable=broad-except
                        # Never let one broken function crash the whole run
                        results.append(self._error_result(node))

            # ── Classes ───────────────────────────────────────────────────
            elif isinstance(node, ast.ClassDef):
                results.extend(self._walk_class(node))

        return results

    def _walk_class(self, class_node: ast.ClassDef) -> List[FunctionResult]:
        """Analyze all methods in *class_node*."""
        results: List[FunctionResult] = []
        analyzer = FunctionAnalyzer(class_name=class_node.name)

        for item in ast.walk(class_node):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only direct methods, not doubly-nested functions
                if self._direct_child_of(item, class_node):
                    try:
                        results.append(analyzer.analyze(item))
                    except Exception:  # pylint: disable=broad-except
                        results.append(self._error_result(item, class_node.name))

        return results

    @staticmethod
    def _is_method(
        node: ast.FunctionDef,
        tree: ast.AST,
    ) -> bool:
        """
        Return True if *node* is a direct child of a ``ClassDef``.

        We need this to avoid double-counting methods (once as top-level
        function, once inside class processing).
        """
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in ast.iter_child_nodes(parent):
                    if child is node:
                        return True
        return False

    @staticmethod
    def _direct_child_of(
        func: ast.FunctionDef,
        class_node: ast.ClassDef,
    ) -> bool:
        """Return True when *func* is a direct child of *class_node*."""
        return any(
            child is func for child in ast.iter_child_nodes(class_node)
        )

    @staticmethod
    def _error_result(
        node: ast.FunctionDef,
        class_name: Optional[str] = None,
    ) -> FunctionResult:
        """
        Fallback result when analysis throws an unexpected exception.
        """
        from bigopy.models import Complexity, Evidence

        name = node.name
        if class_name:
            name = f"{class_name}.{name}"

        tb = traceback.format_exc()
        return FunctionResult(
            name=name,
            complexity=Complexity.UNKNOWN,
            confidence=0.0,
            evidence=[Evidence(
                description=f"Analysis failed: {tb.splitlines()[-1]}",
                complexity=Complexity.UNKNOWN,
            )],
            start_line=getattr(node, "lineno", None),
        )
