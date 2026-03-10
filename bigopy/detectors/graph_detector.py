"""
bigopy.detectors.graph_detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Detects graph traversal patterns and classifies them:

  DFS recursive  → O(V+E)
  DFS iterative  → O(V+E)
  BFS            → O(V+E)
  Dijkstra       → O((V+E) log V)   ← heapq + graph traversal
  Prim           → O((V+E) log V)   ← same pattern as Dijkstra
"""

import ast
from typing import Optional

_GRAPH_PARAM_NAMES = {
    "graph", "g", "adj", "adjacency", "edges",
    "neighbors", "tree", "grid"
}

_VISITED_NAMES = {
    "visited", "seen", "explored", "marked",
    "discovered", "processed"
}

_QUEUE_NAMES = {
    "queue", "stack", "deque", "frontier",
    "to_visit", "to_process", "worklist"
}

_HEAP_NAMES = {
    "pq", "heap", "priority_queue", "min_heap",
    "max_heap", "hq", "open_set"
}

_HEAPQ_FUNCS = {
    "heappush", "heappop", "heappushpop",
    "heapreplace", "nlargest", "nsmallest"
}


def _get_param_names(func_node):
    return {arg.arg for arg in func_node.args.args}


def _has_neighbor_iteration(func_node):
    """Detects: for neighbor in graph[node]"""
    for node in ast.walk(func_node):
        if isinstance(node, ast.For):
            if isinstance(node.iter, ast.Subscript):
                return True
            if isinstance(node.iter, ast.Call):
                if isinstance(node.iter.func, ast.Attribute):
                    if node.iter.func.attr in {"get", "neighbors", "adj"}:
                        return True
    return False


def _has_visited_set(func_node):
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in _VISITED_NAMES:
                    return True
        if isinstance(node, ast.Name) and node.id in _VISITED_NAMES:
            return True
        if isinstance(node, ast.FunctionDef):
            for arg in node.args.args:
                if arg.arg in _VISITED_NAMES:
                    return True
    return False


def _has_queue(func_node):
    for node in ast.walk(func_node):
        if isinstance(node, ast.Name) and node.id in _QUEUE_NAMES:
            return True
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in _QUEUE_NAMES:
                    return True
    return False


def _has_heapq_calls(func_node):
    """
    Detects heapq.heappush / heapq.heappop calls inside the function.
    This is the key signal that upgrades O(V+E) to O((V+E) log V).
    """
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            func = node.func
            # heapq.heappush(...)  or  heapq.heappop(...)
            if isinstance(func, ast.Attribute):
                if func.attr in _HEAPQ_FUNCS:
                    return True
            # direct import: heappush(...) heappop(...)
            if isinstance(func, ast.Name):
                if func.id in _HEAPQ_FUNCS:
                    return True
    return False


def _has_heap_variable(func_node):
    """Detects priority queue variable names like pq, heap."""
    for node in ast.walk(func_node):
        if isinstance(node, ast.Name) and node.id in _HEAP_NAMES:
            return True
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in _HEAP_NAMES:
                    return True
    return False


def _has_distance_array(func_node):
    """Detects distance/dist/cost dict — Dijkstra signal."""
    distance_names = {"distance", "dist", "cost", "d", "distances"}
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in distance_names:
                    return True
    return False


def _is_recursive(func_node):
    func_name = func_node.name
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == func_name:
                return True
    return False


class GraphTraversalInfo:
    def __init__(self, traversal_type, line, complexity_label, description):
        self.traversal_type = traversal_type
        self.line           = line
        self.complexity_label = complexity_label
        self.description    = description


def detect_graph_traversal(func_node) -> Optional[GraphTraversalInfo]:
    """
    Returns GraphTraversalInfo if a graph traversal is detected.

    Priority:
    1. heapq + neighbor iteration + distance array → Dijkstra O((V+E) log V)
    2. queue + neighbor iteration + visited        → BFS      O(V+E)
    3. recursive + neighbor iteration + visited    → DFS      O(V+E)
    4. iterative + neighbor iteration + visited    → DFS      O(V+E)
    """
    has_neighbors = _has_neighbor_iteration(func_node)
    if not has_neighbors:
        return None

    has_heapq    = _has_heapq_calls(func_node)
    has_heap_var = _has_heap_variable(func_node)
    has_visited  = _has_visited_set(func_node)
    has_queue    = _has_queue(func_node)
    has_distance = _has_distance_array(func_node)
    is_recursive = _is_recursive(func_node)

    # ── Dijkstra / Prim pattern ──────────────────────────────────────────
    # Signal: heapq calls + neighbor iteration + distance tracking
    if has_heapq or (has_heap_var and has_distance):
        return GraphTraversalInfo(
            traversal_type  = "dijkstra",
            line            = func_node.lineno,
            complexity_label = "O((V+E) log V)",
            description     = (
                "Dijkstra/Prim detected: heapq operations cost O(log V) "
                "per edge relaxation, total = O((V+E) log V)"
            ),
        )

    # ── BFS pattern ──────────────────────────────────────────────────────
    if has_queue and has_visited:
        return GraphTraversalInfo(
            traversal_type  = "bfs",
            line            = func_node.lineno,
            complexity_label = "O(V+E)",
            description     = (
                "BFS detected: visits every vertex (V) once "
                "and every edge (E) once"
            ),
        )

    # ── DFS pattern ──────────────────────────────────────────────────────
    if has_visited:
        t = "dfs_recursive" if is_recursive else "dfs_iterative"
        label = "DFS recursive" if is_recursive else "DFS iterative"
        return GraphTraversalInfo(
            traversal_type  = t,
            line            = func_node.lineno,
            complexity_label = "O(V+E)",
            description     = (
                f"{label} detected: visits every vertex (V) once "
                f"and every edge (E) once"
            ),
        )

    return None
