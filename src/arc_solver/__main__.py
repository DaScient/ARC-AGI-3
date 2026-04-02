"""
Command-line interface for the ARC-AGI-3 solver.

Usage
-----
Single task::

    python -m arc_solver solve path/to/task.json

Directory of tasks::

    python -m arc_solver solve-dir path/to/tasks/ --output results.json

Options
-------
  --beam-width INT      Beam width for program search (default 64)
  --max-depth INT       Maximum program length to explore (default 3)
  --max-iters INT       Active inference iterations (default 5)
  --verbose             Enable DEBUG logging
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .solver import ARCSolver


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arc_solver",
        description="ARC-AGI-3 Pentarchy Solver",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    sub = parser.add_subparsers(dest="command", required=True)

    # ----- solve -----
    p_solve = sub.add_parser("solve", help="Solve a single task JSON file")
    p_solve.add_argument("task", type=Path, help="Path to task .json")
    p_solve.add_argument("--output", "-o", type=Path, default=None, help="Write result JSON here")
    _add_solver_args(p_solve)

    # ----- solve-dir -----
    p_dir = sub.add_parser("solve-dir", help="Solve all tasks in a directory")
    p_dir.add_argument("directory", type=Path, help="Directory containing task .json files")
    p_dir.add_argument("--output", "-o", type=Path, default=None, help="Write results JSON here")
    p_dir.add_argument("--pattern", default="*.json", help="Glob pattern (default *.json)")
    _add_solver_args(p_dir)

    return parser


def _add_solver_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--beam-width", type=int, default=64, metavar="N")
    p.add_argument("--max-depth", type=int, default=3, metavar="N")
    p.add_argument("--max-iters", type=int, default=5, metavar="N")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    solver = ARCSolver(
        beam_width=args.beam_width,
        max_depth=args.max_depth,
        max_iterations=args.max_iters,
    )

    if args.command == "solve":
        result = solver.solve_task_file(args.task)
        _print_and_save(result, args.output)

    elif args.command == "solve-dir":
        results = solver.solve_directory(args.directory, pattern=args.pattern)
        solved = sum(1 for r in results.values() if r.get("solved"))
        print(f"Solved {solved}/{len(results)} tasks")
        _print_and_save(results, args.output)

    return 0


def _print_and_save(data: object, output: Path | None) -> None:
    text = json.dumps(data, indent=2)
    print(text)
    if output is not None:
        output.write_text(text, encoding="utf-8")
        print(f"\nResult written to {output}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
