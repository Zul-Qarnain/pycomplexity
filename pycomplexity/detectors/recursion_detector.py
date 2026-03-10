"""
pycomplexity.detectors.recursion_detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Detects recursive function calls within a function body and classifies
the recursion pattern:

  * **simple**          – one recursive call, no argument halving
  * **tail**            – last statement is the recursive call (still O(n))
  * **divide-and-conquer** – argument is halved  → O(n log n) or O(log n)
  * **branching**       – two or more recursive calls in the body → O(2^n)

Detection strategy
------------------
1. Collect all ``Call`` nodes inside the function body.
2. Check whether the callee name matches the enclosing function name.
3. Inspect the arguments of each recursive call:
   - If an argument is ``n // 2``, ``n / 2``, ``n >> 1``, ``mid``,
     ``lo + (hi - lo) // 2`` etc. → mark as halving.
4. Count call-sites to distinguish branching (≥2) from linear (1).
"""

from __future__ import annotations

import ast
from typing import List, Optional, Set

from pycomplexity.models import RecursionInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_name(node: ast.AST) -> Optional[str]:
    """Return simple function name from a Call's func node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _arg_is_halved(arg: ast.expr) -> bool:
    """
    Return True when *arg* is an expression that represents half of some value.

    Patterns matched:
    - ``n // 2``   BinOp(Name, FloorDiv, 2)
    - ``n / 2``    BinOp(Name, Div, 2)
    - ``n >> 1``   BinOp(Name, RShift, 1)
    - ``mid``      bare name (common in binary search / merge sort)
    - ``(lo + hi) // 2``   BinOp(BinOp, FloorDiv, 2)
    - ``arr[:mid]``  Subscript with a Slice using a mid-point variable
    - ``arr[mid:]``  same
    - ``arr[1:]``    removing one element per call (also logarithmic in depth)
    """
    if isinstance(arg, ast.Name) and arg.id in {"mid", "middle", "pivot"}:
        return True

    # arr[:mid], arr[mid:], arr[1:] – slice patterns indicating halving/shrinking
    if isinstance(arg, ast.Subscript):
        sl = arg.slice
        if isinstance(sl, ast.Slice):
            # arr[:mid] or arr[mid:]
            upper = sl.upper
            lower = sl.lower
            for bound in (upper, lower):
                if bound is not None:
                    if isinstance(bound, ast.Name) and bound.id in {
                        "mid", "middle", "pivot", "half"
                    }:
                        return True
                    if isinstance(bound, ast.BinOp) and isinstance(
                        bound.op, ast.FloorDiv
                    ):
                        return True
            # arr[1:] – drop-one-element recursion (still shrinks)
            if lower is None and isinstance(upper, ast.Constant):
                pass  # arr[:k] with constant k – not halving
            if (
                lower is not None
                and isinstance(lower, ast.Constant)
                and lower.value == 1
                and upper is None
            ):
                # arr[1:] – each call shrinks by 1 only → linear, not halving
                pass
            # Any non-trivial slice on a name variable: treat as potential halving
            if lower is None and isinstance(upper, ast.Name):
                return True
            if upper is None and isinstance(lower, ast.Name):
                return True

    if isinstance(arg, ast.BinOp):
        op = arg.op
        right = arg.right

        # n // 2  or  n >> 1
        if isinstance(op, (ast.FloorDiv, ast.RShift)):
            if isinstance(right, ast.Constant) and right.value in (1, 2):
                return True

        # n / 2
        if isinstance(op, ast.Div):
            if isinstance(right, ast.Constant) and right.value == 2:
                return True

        # (lo + hi) // 2  – any floor division on a non-trivial expr is halving
        if isinstance(op, ast.FloorDiv):
            return True

    return False


def _body_contains_midpoint_assignment(body: list) -> bool:
    """
    Return True when the function body contains an assignment like:
        mid = len(arr) // 2
        mid = (lo + hi) // 2
        half = n // 2
    This indicates divide-and-conquer even when slice notation hides it.
    """
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(node, ast.Assign):
            # Check target names
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {
                    "mid", "middle", "half", "pivot", "median"
                }:
                    if isinstance(node.value, ast.BinOp) and isinstance(
                        node.value.op, (ast.FloorDiv, ast.Div)
                    ):
                        return True
    return False


def _has_halving_arg(call: ast.Call) -> bool:
    """Return True if any argument of *call* represents a halved value."""
    return any(_arg_is_halved(arg) for arg in call.args)


def _detect_result_doubling(func_node: ast.FunctionDef) -> int:
    """
    Detect patterns where the recursive result is doubled/expanded, e.g.:
        rest = func(arr[1:])
        return rest + [[arr[0]] + s for s in rest]   ← rest iterated twice
    
    This is the characteristic pattern of subset-enumeration functions,
    which are O(2^n) even with a single recursive call site.
    
    Returns 1 if such a doubling pattern is found, 0 otherwise.
    """
    # Find names that hold recursive call results
    recursive_result_names: Set[str] = set()
    
    class _RecCallFinder(ast.NodeVisitor):
        def visit_Assign(self_, node: ast.Assign) -> None:  # noqa: N805
            if isinstance(node.value, ast.Call):
                name = _extract_name(node.value.func)
                if name == func_node.name:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            recursive_result_names.add(target.id)
            self_.generic_visit(node)
    
    _RecCallFinder().visit(func_node)
    
    if not recursive_result_names:
        return 0
    
    # Check if any of these names are iterated inside a comprehension
    # in a return statement (doubling pattern)
    class _DoublingChecker(ast.NodeVisitor):
        found = False
        
        def visit_Return(self_, node: ast.Return) -> None:  # noqa: N805
            if node.value is not None:
                self_._check_expr(node.value)
        
        def _check_expr(self_, node: ast.expr) -> None:  # noqa: N805
            # Look for: result + [... for x in result]
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                self_._find_comprehension_over_result(node)
            # Look for list comprehension at the return level
            if isinstance(node, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
                for gen in node.generators:
                    if (
                        isinstance(gen.iter, ast.Name)
                        and gen.iter.id in recursive_result_names
                    ):
                        self_.found = True
        
        def _find_comprehension_over_result(self_, node: ast.AST) -> None:  # noqa: N805
            for child in ast.walk(node):
                if isinstance(child, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
                    for gen in child.generators:
                        if (
                            isinstance(gen.iter, ast.Name)
                            and gen.iter.id in recursive_result_names
                        ):
                            self_.found = True
    
    checker = _DoublingChecker()
    checker.visit(func_node)
    return 1 if checker.found else 0


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

class RecursionDetector(ast.NodeVisitor):
    """
    Detects recursive calls in a function body.

    Usage::

        detector = RecursionDetector()
        result = detector.analyze(func_node)
        if result:
            print(result)
    """

    def __init__(self) -> None:
        self._func_name: str = ""
        self._call_sites: List[ast.Call] = []
        self._halving_sites: int = 0

    def analyze(self, func_node: ast.FunctionDef) -> Optional[RecursionInfo]:
        """
        Walk *func_node* and return a ``RecursionInfo`` if recursion is found,
        or ``None`` otherwise.
        """
        self._func_name = func_node.name
        self._call_sites = []
        self._halving_sites = 0
        self.visit(func_node)

        # Effective call sites: also count list-comprehension doublings where
        # the recursive result is iterated (e.g. all_subsets-style)
        doubling = _detect_result_doubling(func_node)
        effective_call_sites = len(self._call_sites) + doubling

        if effective_call_sites == 0:
            return None

        # Also check for midpoint assignments as a halving signal
        has_mid_assign = _body_contains_midpoint_assignment(func_node.body)
        has_halving = self._halving_sites > 0 or has_mid_assign

        return RecursionInfo(
            function_name=self._func_name,
            call_sites=effective_call_sites,
            has_halving=has_halving,
            line=func_node.lineno,
        )

    # ------------------------------------------------------------------
    # Visitor methods
    # ------------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        name = _extract_name(node.func)
        if name == self._func_name:
            self._call_sites.append(node)
            if _has_halving_arg(node):
                self._halving_sites += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Skip nested function definitions – they are separate analysis units."""
        if node.name == self._func_name:
            # Top-level function itself: descend into it.
            self.generic_visit(node)
        # Nested function: skip.

    visit_AsyncFunctionDef = visit_FunctionDef


# ---------------------------------------------------------------------------
# Convenience: detect mutual recursion (best-effort)
# ---------------------------------------------------------------------------

def detect_all_recursion(
    func_nodes: List[ast.FunctionDef],
) -> List[RecursionInfo]:
    """
    Run ``RecursionDetector`` on a list of function nodes and return
    a ``RecursionInfo`` for each recursive function found.
    """
    results: List[RecursionInfo] = []
    func_names: Set[str] = {fn.name for fn in func_nodes}

    for func in func_nodes:
        detector = RecursionDetector()
        result = detector.analyze(func)
        if result:
            results.append(result)
        else:
            # Check for mutual recursion: does this function call any other
            # function in the same module?
            mutual = _check_mutual_recursion(func, func_names)
            if mutual:
                results.append(mutual)

    return results


def _check_mutual_recursion(
    func_node: ast.FunctionDef,
    all_names: Set[str],
) -> Optional[RecursionInfo]:
    """
    Detect mutual recursion: function A calls function B which (presumably)
    calls A back.  We can only detect one side here – we flag A as mutually
    recursive if it calls any *other* function in the same module.
    """
    called: Set[str] = set()

    class _CallCollector(ast.NodeVisitor):
        def visit_Call(self_, node: ast.Call) -> None:  # noqa: N805
            name = _extract_name(node.func)
            if name and name != func_node.name:
                called.add(name)
            self_.generic_visit(node)

    _CallCollector().visit(func_node)
    mutual_targets = called & all_names

    if mutual_targets:
        return RecursionInfo(
            function_name=func_node.name,
            call_sites=len(mutual_targets),
            has_halving=False,
            line=func_node.lineno,
        )
    return None
