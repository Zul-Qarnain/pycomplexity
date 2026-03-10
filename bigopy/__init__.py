"""
bigopy
~~~~~~
Static AST-based Big-O complexity estimation for Python code.
No code execution needed — just point it at your source file.

Quick start:
    from bigopy import analyze_file, analyze_source

    result = analyze_file("my_module.py")
    for func in result.functions:
        print(func.name, func.complexity.label, func.confidence)
"""

from bigopy.analyzers.module_analyzer import ModuleAnalyzer
from bigopy.models import (
    Complexity,
    Evidence,
    FunctionResult,
    ModuleResult,
)

__version__ = "0.1.0"
__all__ = [
    "analyze_file",
    "analyze_source",
    "Complexity",
    "Evidence",
    "FunctionResult",
    "ModuleResult",
    "ModuleAnalyzer",
]


def analyze_file(filepath: str) -> ModuleResult:
    """
    Parse a .py file and return complexity estimates
    for every function and method found.
    """
    return ModuleAnalyzer().analyze_file(filepath)


def analyze_source(source: str, filepath: str = "<string>") -> ModuleResult:
    """
    Parse a Python source string and return complexity estimates.
    """
    return ModuleAnalyzer().analyze_source(source, filepath=filepath)
