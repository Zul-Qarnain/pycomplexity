"""
pycomplexity.reporters.json_reporter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Serialises ``ModuleResult`` to a JSON-compatible dictionary and to a
JSON string.  Used by the CLI ``--format json`` option and by tooling
that embeds pycomplexity as a library.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from pycomplexity.models import FunctionResult, ModuleResult


def _function_to_dict(result: FunctionResult) -> Dict[str, Any]:
    return {
        "name":       result.name,
        "complexity": result.complexity.label,
        "confidence": result.confidence,
        "start_line": result.start_line,
        "end_line":   result.end_line,
        "reasons": [
            {
                "description": ev.description,
                "complexity":  ev.complexity.label,
                "line":        ev.line,
            }
            for ev in result.evidence
        ],
        "loops": [
            {
                "kind":               l.kind,
                "depth":              l.depth,
                "line":               l.line,
                "is_input_dependent": l.is_input_dependent,
                "is_logarithmic":     l.is_logarithmic,
            }
            for l in result.loops
        ],
        "recursion": [
            {
                "function_name": r.function_name,
                "call_sites":    r.call_sites,
                "has_halving":   r.has_halving,
                "line":          r.line,
            }
            for r in result.recursions
        ],
    }


def module_to_dict(result: ModuleResult) -> Dict[str, Any]:
    return {
        "filepath":            result.filepath,
        "dominant_complexity": result.dominant_complexity.label,
        "errors":              result.errors,
        "functions": [_function_to_dict(f) for f in result.functions],
    }


def module_to_json(result: ModuleResult, indent: int = 2) -> str:
    return json.dumps(module_to_dict(result), indent=indent)
