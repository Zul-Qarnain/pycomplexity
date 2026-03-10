"""
pycomplexity
~~~~~~~~~~~~
Automatic Big-O complexity estimation for Python code via AST analysis.

Quick start::

    from pycomplexity import analyze_file, analyze_source

    # Analyze a file
    result = analyze_file("my_module.py")
    for func in result.functions:
        print(func.name, func.complexity.label, func.confidence)

    # Analyze a source string
    source = '''
    def bubble_sort(arr):
        n = len(arr)
        for i in range(n):
            for j in range(n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
    '''
    result = analyze_source(source)

:copyright: (c) 2024 – present, pycomplexity contributors.
:license: MIT
"""

from pycomplexity.analyzers.module_analyzer import ModuleAnalyzer
from pycomplexity.models import (
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
    Parse *filepath* and return a ``ModuleResult`` with complexity estimates
    for every function / method found.

    Parameters
    ----------
    filepath:
        Path to a ``.py`` file.

    Returns
    -------
    ModuleResult
    """
    return ModuleAnalyzer().analyze_file(filepath)


def analyze_source(source: str, filepath: str = "<string>") -> ModuleResult:
    """
    Parse *source* (a Python source string) and return a ``ModuleResult``.

    Parameters
    ----------
    source:
        Raw Python source code.
    filepath:
        Optional label shown in reports.

    Returns
    -------
    ModuleResult
    """
    return ModuleAnalyzer().analyze_source(source, filepath=filepath)
