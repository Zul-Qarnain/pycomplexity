"""
pycomplexity.detectors.builtin_detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Maps calls to well-known Python builtins and standard-library functions
to their documented time complexities.

This avoids false O(1) estimates when a function calls, for instance,
``sorted()`` (O(n log n)) or ``list.sort()`` (O(n log n)).

Only calls at the *top level* of the function (not inside loops – the loop
detector already accounts for that) matter for direct lookup.  When a known
O(n log n) call is inside a loop the loop detector's nesting logic handles
the combination.
"""

from __future__ import annotations

import ast
from typing import Dict, List, Optional, Tuple

from pycomplexity.models import Complexity


# ---------------------------------------------------------------------------
# Known complexity table
# ---------------------------------------------------------------------------
# key  : (module_or_none, function_name)
# value: (complexity, note)
#
# None as module means a builtin or method accessed as bare name or
# attribute on an arbitrary object.

_KNOWN: Dict[Tuple[Optional[str], str], Tuple[Complexity, str]] = {
    # --- Sorting -----------------------------------------------------------
    (None, "sorted"):        (Complexity.O_N_LOG_N, "built-in sorted()"),
    (None, "sort"):          (Complexity.O_N_LOG_N, "list.sort()"),
    ("heapq", "heappush"):   (Complexity.O_LOG_N,   "heapq.heappush()"),
    ("heapq", "heappop"):    (Complexity.O_LOG_N,   "heapq.heappop()"),
    ("heapq", "heapify"):    (Complexity.O_N,       "heapq.heapify()"),
    ("heapq", "nlargest"):   (Complexity.O_N_LOG_N, "heapq.nlargest()"),
    ("heapq", "nsmallest"):  (Complexity.O_N_LOG_N, "heapq.nsmallest()"),
    ("bisect", "bisect"):    (Complexity.O_LOG_N,   "bisect.bisect()"),
    ("bisect", "insort"):    (Complexity.O_N,       "bisect.insort() (shift cost)"),

    # --- String / sequence ------------------------------------------------
    (None, "join"):          (Complexity.O_N,       "str.join()"),
    (None, "split"):         (Complexity.O_N,       "str.split()"),
    (None, "replace"):       (Complexity.O_N,       "str.replace()"),
    (None, "find"):          (Complexity.O_N,       "str.find()"),
    (None, "count"):         (Complexity.O_N,       "str/list.count()"),
    (None, "index"):         (Complexity.O_N,       "list.index()"),
    (None, "reverse"):       (Complexity.O_N,       "list.reverse()"),
    (None, "copy"):          (Complexity.O_N,       "list/dict.copy()"),

    # --- Set / dict operations are O(1) average – but construction is O(n)
    (None, "set"):           (Complexity.O_N,       "set() construction"),
    (None, "dict"):          (Complexity.O_N,       "dict() construction"),
    (None, "list"):          (Complexity.O_N,       "list() construction"),
    (None, "tuple"):         (Complexity.O_N,       "tuple() construction"),

    # --- Searching ---------------------------------------------------------
    (None, "max"):           (Complexity.O_N,       "built-in max()"),
    (None, "min"):           (Complexity.O_N,       "built-in min()"),
    (None, "sum"):           (Complexity.O_N,       "built-in sum()"),
    (None, "any"):           (Complexity.O_N,       "built-in any()"),
    (None, "all"):           (Complexity.O_N,       "built-in all()"),
    (None, "filter"):        (Complexity.O_N,       "built-in filter()"),
    (None, "map"):           (Complexity.O_N,       "built-in map()"),

    # --- Math --------------------------------------------------------------
    ("math", "log"):         (Complexity.O_1,       "math.log()"),
    ("math", "sqrt"):        (Complexity.O_1,       "math.sqrt()"),
    ("math", "factorial"):   (Complexity.O_N,       "math.factorial()"),
}


def _extract_call_key(
    node: ast.Call,
) -> Optional[Tuple[Optional[str], str]]:
    """
    Extract a lookup key from a ``Call`` node.

    Returns:
      - ``(None, 'sorted')``    for ``sorted(x)``
      - ``(None, 'sort')``      for ``x.sort()``
      - ``('heapq', 'heappush')`` for ``heapq.heappush(...)``
    """
    func = node.func

    if isinstance(func, ast.Name):
        return (None, func.id)

    if isinstance(func, ast.Attribute):
        attr_name = func.attr
        # Check if the object is a module alias (simple Name)
        if isinstance(func.value, ast.Name):
            obj_name = func.value.id
            # Could be module access like heapq.heappush
            key_with_module = (obj_name, attr_name)
            if key_with_module in _KNOWN:
                return key_with_module
        return (None, attr_name)

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_known_calls(
    func_node: ast.FunctionDef,
) -> List[Tuple[Complexity, str, int]]:
    """
    Walk *func_node* and return ``(complexity, description, line)`` tuples
    for every call that matches a known complexity entry.

    Only calls that are *more complex than O(1)* are returned – we don't
    need to annotate plain builtins.
    """
    results: List[Tuple[Complexity, str, int]] = []
    _visited_funcs: set = set()

    class _Visitor(ast.NodeVisitor):
        def visit_Call(self_, node: ast.Call) -> None:  # noqa: N805
            key = _extract_call_key(node)
            if key and key in _KNOWN:
                complexity, note = _KNOWN[key]
                if complexity > Complexity.O_1:
                    results.append((complexity, note, node.lineno))
            self_.generic_visit(node)

        def visit_FunctionDef(self_, node: ast.FunctionDef) -> None:  # noqa: N805
            # Skip nested functions
            if node.name not in _visited_funcs:
                _visited_funcs.add(node.name)
                if node.name == func_node.name:
                    self_.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

    _Visitor().visit(func_node)
    return results
