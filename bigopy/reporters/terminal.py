"""
bigopy.reporters.terminal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Color-coded terminal output. Shows O(V+E) when graph traversal detected.
"""
from __future__ import annotations
import sys
from bigopy.models import Complexity, FunctionResult, ModuleResult

_RESET   = "\033[0m"
_BOLD    = "\033[1m"
_GREEN   = "\033[32m"
_CYAN    = "\033[36m"
_YELLOW  = "\033[33m"
_RED     = "\033[31m"
_DIM     = "\033[2m"
_WHITE   = "\033[97m"
_MAGENTA = "\033[35m"

def _supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def _complexity_color(c, override=None):
    if not _supports_color():
        return ""
    if override and "V+E" in str(override):
        return _MAGENTA
    return {
        Complexity.O_1:       _GREEN,
        Complexity.O_LOG_N:   _CYAN,
        Complexity.O_N:       _YELLOW,
        Complexity.O_N_LOG_N: _YELLOW + _BOLD,
        Complexity.O_N2:      _RED,
        Complexity.O_N3:      _RED + _BOLD,
        Complexity.O_2N:      _RED + _BOLD,
        Complexity.UNKNOWN:   _DIM,
    }.get(c, "")

def _colored(text, color):
    if not _supports_color() or not color:
        return text
    return f"{color}{text}{_RESET}"

def _confidence_bar(confidence, width=20):
    filled = int(confidence * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {confidence * 100:.0f}%"


class TerminalReporter:

    def __init__(self, verbose=False, output=None):
        self.verbose = verbose
        self.out = output or sys.stdout

    def report_module(self, result: ModuleResult) -> None:
        self._section_header(f"📂  {result.filepath}")
        if result.errors:
            for err in result.errors:
                self._print(f"  ⚠  {err}", color=_RED)
            return
        if not result.functions:
            self._print("  (no functions found)", color=_DIM)
            return
        for f in result.functions:
            self.report_function(f)
        self._divider()
        dominant = result.dominant_complexity
        self._print(
            f"  Module dominant complexity: "
            + _colored(dominant.label, _complexity_color(dominant))
        )
        self._print("")

    def report_function(self, result: FunctionResult) -> None:
        override      = getattr(result, '_complexity_override', None)
        display_label = override if override else result.complexity.label
        color         = _complexity_color(result.complexity, override)
        c_label       = _colored(display_label, color)
        loc           = _colored(
            f" (line {result.start_line})", _DIM
        ) if result.start_line else ""

        self._print("")
        self._print(
            f"  {'Function:':<14} "
            + _colored(f"{result.name}()", _BOLD + _WHITE) + loc
        )
        self._print(f"  {'Complexity:':<14} {c_label}")
        self._print(f"  {'Confidence:':<14} {_confidence_bar(result.confidence)}")

        if result.evidence:
            self._print(f"  {'Reasons:':<14}")
            items = result.evidence if self.verbose else result.evidence[:1]
            for ev in items:
                line_ref = f" (line {ev.line})" if (self.verbose and ev.line) else ""
                self._print(f"    • {ev.description}{line_ref}")

    def _print(self, msg="", color=""):
        if color and _supports_color():
            print(f"{color}{msg}{_RESET}", file=self.out)
        else:
            print(msg, file=self.out)

    def _section_header(self, title):
        self._print("")
        self._print("=" * 60, color=_DIM)
        self._print(title, color=_BOLD + _WHITE)
        self._print("=" * 60, color=_DIM)

    def _divider(self):
        self._print("  " + "-" * 50, color=_DIM)
