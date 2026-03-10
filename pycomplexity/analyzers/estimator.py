"""
pycomplexity.analyzers.estimator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Core estimation engine.
Now uses range_power to correctly detect:
    range(i)   in nested loop → O(n²)
    range(i*i) in nested loop → O(n³)
"""

from __future__ import annotations
from typing import List, Tuple, Optional
from pycomplexity.models import (
    Complexity, Evidence, FunctionResult, LoopInfo, RecursionInfo,
)


def _max_loop_depth(loops):
    return max((l.depth for l in loops), default=0)

def _has_logarithmic_loop(loops):
    return any(l.is_logarithmic for l in loops)


def _effective_depth(loops: List[LoopInfo]) -> int:
    """
    Calculate the TRUE complexity depth by considering range powers.

    Normal nested loops:
        for i in range(n):        depth=1, range_power=1
            for j in range(i):    depth=2, range_power=1
        → effective_depth = 1 + 1 = 2  → O(n²)  ✓

    Quadratic inner range:
        for i in range(n):        depth=1, range_power=1
            for j in range(i*i):  depth=2, range_power=2
        → effective_depth = 1 + 2 = 3  → O(n³)  ✓
    """
    if not loops:
        return 0

    # Group loops by depth level
    by_depth = {}
    for loop in loops:
        d = loop.depth
        if d not in by_depth:
            by_depth[d] = []
        by_depth[d].append(loop)

    if not by_depth:
        return 0

    # Sum up powers across all depth levels
    total_power = 0
    for depth_level in sorted(by_depth.keys()):
        level_loops = by_depth[depth_level]
        # Take the max range_power at each level
        max_power = max(
            getattr(loop, 'range_power', 1)
            for loop in level_loops
        )
        total_power += max_power

    return total_power


# ── Rules ────────────────────────────────────────────────────

def _rule_graph_traversal(graph_info):
    return (
        Complexity.O_N, 0.90,
        [Evidence(
            description=graph_info.description,
            complexity=Complexity.O_N,
            line=graph_info.line,
            weight=1.0,
        )],
        graph_info.complexity_label,
    )

def _rule_branching_recursion(rec):
    return (Complexity.O_2N, 0.80, [Evidence(
        description=f"branching recursion: {rec.call_sites} recursive calls",
        complexity=Complexity.O_2N, line=rec.line, weight=1.0,
    )], None)

def _rule_divide_and_conquer(rec, has_outer_loop):
    if rec.call_sites >= 2 or has_outer_loop:
        c, conf = Complexity.O_N_LOG_N, 0.85
        desc = "divide-and-conquer recursion (argument halved, multiple branches)"
    else:
        c, conf = Complexity.O_LOG_N, 0.80
        desc = "binary-search-style recursion (argument halved, single branch)"
    return (c, conf, [Evidence(
        description=desc, complexity=c, line=rec.line, weight=1.0,
    )], None)

def _rule_linear_recursion(rec):
    return (Complexity.O_N, 0.70, [Evidence(
        description="linear recursion: single recursive call",
        complexity=Complexity.O_N, line=rec.line, weight=0.8,
    )], None)

def _rule_nested_loops(eff_depth, raw_depth, loops):
    """
    Use effective depth (accounts for range_power) to determine
    true complexity class.
    """
    if eff_depth >= 3:
        c, conf = Complexity.O_N3, 0.85
        if eff_depth > 3:
            desc = f"nested loops with polynomial range (effective depth={eff_depth})"
        else:
            desc = f"triple-nested loops (depth={raw_depth})"
    else:
        c, conf = Complexity.O_N2, 0.85
        desc = f"doubly-nested loops (depth={raw_depth})"

    # Check if a quadratic range was found — add explanation
    quad_loops = [l for l in loops if getattr(l, 'range_power', 1) >= 2]
    if quad_loops:
        ql = quad_loops[0]
        desc = (
            f"nested loop with range(i*i) or range(i²) at line {ql.line} "
            f"→ inner bound is quadratic, total = O(n³)"
        )
        c, conf = Complexity.O_N3, 0.85

    evidence = [Evidence(description=desc, complexity=c, weight=1.0)]
    for loop in loops:
        if loop.depth > 1:
            rp = getattr(loop, 'range_power', 1)
            rp_note = f" [range_power={rp}]" if rp > 1 else ""
            evidence.append(Evidence(
                description=f"inner {loop.kind}-loop{rp_note}",
                complexity=c, line=loop.line, weight=0.5,
            ))
    return (c, conf, evidence, None)

def _rule_logarithmic_loop(loops):
    log_loops = [l for l in loops if l.is_logarithmic]
    non_log   = [l for l in loops if not l.is_logarithmic and l.is_input_dependent]
    if non_log:
        c, conf = Complexity.O_N_LOG_N, 0.80
        desc = "outer linear loop wrapping a logarithmic (halving/doubling) while-loop"
    else:
        c, conf = Complexity.O_LOG_N, 0.85
        desc = "logarithmic loop: variable halved or doubled each iteration"
    return (c, conf, [Evidence(
        description=desc, complexity=c, line=log_loops[0].line, weight=1.0,
    )], None)

def _rule_single_loop(loops):
    loop = loops[0]
    conf = 0.90 if loop.is_input_dependent else 0.60
    return (Complexity.O_N, conf, [Evidence(
        description=(
            f"single input-dependent {loop.kind}-loop"
            if loop.is_input_dependent
            else f"single {loop.kind}-loop (may not depend on input size)"
        ),
        complexity=Complexity.O_N, line=loop.line,
        weight=1.0 if loop.is_input_dependent else 0.6,
    )], None)

def _rule_no_loops_no_recursion():
    return (Complexity.O_1, 0.95, [Evidence(
        description="no loops or recursion detected",
        complexity=Complexity.O_1, weight=1.0,
    )], None)


class ComplexityEstimator:

    def estimate(self, name, loops, recursion=None,
                 builtin_calls=None, graph_traversal=None,
                 start_line=None, end_line=None) -> FunctionResult:

        builtin_calls = builtin_calls or []
        complexity, confidence, evidence, override_label = self._decide(
            loops, recursion, builtin_calls, graph_traversal
        )
        for bc_c, bc_desc, bc_line in builtin_calls:
            evidence.append(Evidence(
                description=f"call to {bc_desc}",
                complexity=bc_c, line=bc_line, weight=0.4,
            ))
            if bc_c == complexity:
                confidence = min(1.0, confidence + 0.03)

        confidence = round(confidence, 2)
        result = FunctionResult(
            name=name, complexity=complexity, confidence=confidence,
            evidence=evidence, start_line=start_line, end_line=end_line,
            loops=loops, recursions=[recursion] if recursion else [],
        )
        object.__setattr__(result, '_complexity_override', override_label)
        return result

    def _decide(self, loops, recursion, builtin_calls, graph_traversal):

        # 1. Graph traversal
        if graph_traversal is not None:
            return _rule_graph_traversal(graph_traversal)

        has_loops  = bool(loops)
        has_log    = _has_logarithmic_loop(loops)
        raw_depth  = _max_loop_depth(loops)
        eff_depth  = _effective_depth(loops)   # ← uses range_power

        # 2. Recursion
        if recursion is not None:
            if recursion.has_halving:
                return _rule_divide_and_conquer(recursion, has_loops)
            if recursion.call_sites >= 2:
                return _rule_branching_recursion(recursion)
            return _rule_linear_recursion(recursion)

        # 3. Loops
        if has_loops:
            if has_log:
                return _rule_logarithmic_loop(loops)
            if eff_depth >= 2:                  # ← uses effective depth
                return _rule_nested_loops(eff_depth, raw_depth, loops)
            return _rule_single_loop(loops)

        # 4. Builtins
        if builtin_calls:
            dominant = max(builtin_calls, key=lambda t: t[0])
            bc_c, bc_desc, bc_line = dominant
            if bc_c > Complexity.O_1:
                return (bc_c, 0.75, [Evidence(
                    description=f"dominant builtin: {bc_desc}",
                    complexity=bc_c, line=bc_line, weight=0.9,
                )], None)

        # 5. Base case
        return _rule_no_loops_no_recursion()
