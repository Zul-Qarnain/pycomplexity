"""
pycomplexity.cli
~~~~~~~~~~~~~~~~~
Command-line interface.

Usage examples::

    pycomplexity analyze my_file.py
    pycomplexity analyze my_file.py --verbose
    pycomplexity analyze my_file.py --format json
    pycomplexity analyze src/ --format json --output report.json
    pycomplexity analyze my_file.py --only bubble_sort

Run ``pycomplexity --help`` for full usage.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from pycomplexity.analyzers.module_analyzer import ModuleAnalyzer
from pycomplexity.models import ModuleResult
from pycomplexity.reporters.json_reporter import module_to_json
from pycomplexity.reporters.terminal import TerminalReporter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _collect_python_files(paths: List[str]) -> List[Path]:
    """
    Expand directories into a list of ``*.py`` files.
    Non-directory paths are returned as-is (validated later).
    """
    collected: List[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            collected.extend(sorted(p.rglob("*.py")))
        else:
            collected.append(p)
    return collected


# ---------------------------------------------------------------------------
# Sub-command: analyze
# ---------------------------------------------------------------------------

def cmd_analyze(args: argparse.Namespace) -> int:
    """
    Analyze one or more Python files and print / save results.

    Returns an exit code (0 = success, 1 = errors found).
    """
    files  = _collect_python_files(args.paths)
    format_ = args.format
    verbose = getattr(args, "verbose", False)
    only    = getattr(args, "only", None)
    output  = getattr(args, "output", None)

    if not files:
        print("pycomplexity: no Python files found.", file=sys.stderr)
        return 1

    analyzer = ModuleAnalyzer()
    results: List[ModuleResult] = []
    exit_code = 0

    for filepath in files:
        if not filepath.exists():
            print(f"pycomplexity: file not found: {filepath}", file=sys.stderr)
            exit_code = 1
            continue

        result = analyzer.analyze_file(filepath)
        if result.errors:
            exit_code = 1

        # Filter to specific function names if requested
        if only:
            result.functions = [
                f for f in result.functions
                if f.name in only or f.name.split(".")[-1] in only
            ]

        results.append(result)

    # ── Output ────────────────────────────────────────────────────────────
    if format_ == "json":
        import json
        combined = {
            "files": [
                json.loads(module_to_json(r)) for r in results
            ]
        }
        out_str = json.dumps(combined, indent=2)
        if output:
            Path(output).write_text(out_str, encoding="utf-8")
            print(f"Results written to {output}")
        else:
            print(out_str)

    else:  # terminal (default)
        reporter = TerminalReporter(verbose=verbose)
        for result in results:
            reporter.report_module(result)

    return exit_code


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pycomplexity",
        description="Estimate Big-O complexity of Python code via AST analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pycomplexity analyze my_sort.py
  pycomplexity analyze src/ --format json --output report.json
  pycomplexity analyze my_sort.py --verbose
  pycomplexity analyze my_sort.py --only bubble_sort merge_sort
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- analyze -----------------------------------------------------------
    analyze_cmd = sub.add_parser(
        "analyze",
        help="Analyze one or more Python files / directories",
    )
    analyze_cmd.add_argument(
        "paths",
        nargs="+",
        metavar="PATH",
        help="Python file(s) or directory/ies to analyze",
    )
    analyze_cmd.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print full evidence list for each function",
    )
    analyze_cmd.add_argument(
        "--format", "-f",
        choices=["terminal", "json"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    analyze_cmd.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Write output to FILE instead of stdout (JSON mode only)",
    )
    analyze_cmd.add_argument(
        "--only",
        nargs="+",
        metavar="FUNC",
        help="Only analyze functions with these names",
    )
    analyze_cmd.set_defaults(func=cmd_analyze)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args   = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
