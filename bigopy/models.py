"""
bigopy.models
~~~~~~~~~~~~~~~~~~~
Data models representing complexity classes, analysis results,
and evidence collected during AST traversal.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Complexity taxonomy
# ---------------------------------------------------------------------------

class Complexity(enum.Enum):
    """Canonical Big-O complexity classes, ordered from best to worst."""

    O_1       = "O(1)"
    O_LOG_N   = "O(log n)"
    O_N       = "O(n)"
    O_N_LOG_N = "O(n log n)"
    O_N2      = "O(n²)"
    O_N3      = "O(n³)"
    O_2N      = "O(2^n)"
    O_N_FACT  = "O(n!)"
    UNKNOWN   = "O(?)"

    @property
    def _rank(self) -> int:
        """Numeric rank for comparison (lower = better complexity)."""
        return _COMPLEXITY_RANK.get(self.name, 99)

    def __lt__(self, other: "Complexity") -> bool:
        return self._rank < other._rank

    def __le__(self, other: "Complexity") -> bool:
        return self._rank <= other._rank

    def __gt__(self, other: "Complexity") -> bool:
        return self._rank > other._rank

    def __ge__(self, other: "Complexity") -> bool:
        return self._rank >= other._rank

    @staticmethod
    def dominant(*complexities: "Complexity") -> "Complexity":
        """Return the worst-case (dominant) complexity from a collection."""
        filtered = [c for c in complexities if c is not Complexity.UNKNOWN]
        if not filtered:
            return Complexity.UNKNOWN
        return max(filtered)

    @property
    def label(self) -> str:
        return self.value


# Rank mapping (defined after class body so enum values are available)
_COMPLEXITY_RANK = {
    "O_1":       0,
    "O_LOG_N":   1,
    "O_N":       2,
    "O_N_LOG_N": 3,
    "O_N2":      4,
    "O_N3":      5,
    "O_2N":      6,
    "O_N_FACT":  7,
    "UNKNOWN":   99,
}


# ---------------------------------------------------------------------------
# Evidence & detection results
# ---------------------------------------------------------------------------

@dataclass
class Evidence:
    """A single piece of evidence that influenced the complexity estimate."""

    description: str
    """Human-readable description of what was detected."""

    complexity: Complexity
    """The complexity class this evidence implies."""

    line: Optional[int] = None
    """Source line number where evidence was found (1-based)."""

    weight: float = 1.0
    """Relative contribution to the confidence score (0.0 – 1.0)."""

    def __str__(self) -> str:
        loc = f" (line {self.line})" if self.line else ""
        return f"[{self.complexity.label}]{loc} {self.description}"


@dataclass
class LoopInfo:
    """Metadata about a loop discovered during AST traversal."""

    kind: str          # "for" | "while"
    depth: int         # nesting depth (1 = outermost)
    line: int
    is_input_dependent: bool = False   # iterates over input/n
    is_logarithmic: bool = False       # n = n // 2 style
    inner_call_complexities: List[Complexity] = field(default_factory=list)


@dataclass
class RecursionInfo:
    """Metadata about a recursive function."""

    function_name: str
    call_sites: int          # number of recursive call sites in the body
    has_halving: bool        # argument is halved (divide-and-conquer)
    line: int


# ---------------------------------------------------------------------------
# Per-function analysis result
# ---------------------------------------------------------------------------

@dataclass
class FunctionResult:
    """Complexity analysis result for a single function or method."""

    name: str
    """Qualified name, e.g. ``MyClass.sort`` or ``bubble_sort``."""

    complexity: Complexity
    """Estimated dominant complexity."""

    confidence: float
    """Confidence score in [0.0, 1.0]. Higher = more certain."""

    evidence: List[Evidence] = field(default_factory=list)
    """Ordered list of evidence items that justify the estimate."""

    start_line: Optional[int] = None
    end_line: Optional[int] = None

    # Raw detection metadata (used internally, not displayed by default)
    loops: List[LoopInfo] = field(default_factory=list)
    recursions: List[RecursionInfo] = field(default_factory=list)

    @property
    def reasons(self) -> List[str]:
        """Short, human-readable reason strings."""
        return [str(e) for e in self.evidence]


# ---------------------------------------------------------------------------
# Module-level analysis result
# ---------------------------------------------------------------------------

@dataclass
class ModuleResult:
    """Aggregated analysis result for an entire Python source file."""

    filepath: str
    functions: List[FunctionResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def dominant_complexity(self) -> Complexity:
        if not self.functions:
            return Complexity.UNKNOWN
        return Complexity.dominant(*(f.complexity for f in self.functions))
