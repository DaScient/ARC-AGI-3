"""
ARC Solver — Main Orchestrator
================================

High-level API for loading ARC tasks, running the Pentarchy inference
loop, and producing predictions.

Task format (JSON)::

    {
        "train": [
            {"input": [[...]], "output": [[...]]},
            ...
        ],
        "test": [
            {"input": [[...]]},
            ...
        ]
    }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .controller import ActiveInferenceController
from .dsl import DSLRegistry, Grid
from .synthesizer import Program

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task loading
# ---------------------------------------------------------------------------

def load_task(path: str | Path) -> Dict[str, Any]:
    """Load an ARC task from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def extract_pairs(task: Dict[str, Any]) -> List[Tuple[Grid, Grid]]:
    """Extract (input, output) training pairs from a task dict."""
    return [(ex["input"], ex["output"]) for ex in task.get("train", [])]


def extract_test_inputs(task: Dict[str, Any]) -> List[Grid]:
    """Extract test inputs from a task dict."""
    return [ex["input"] for ex in task.get("test", [])]


# ---------------------------------------------------------------------------
# Main solver
# ---------------------------------------------------------------------------

class ARCSolver:
    """
    End-to-end ARC solver integrating the five subsystems.

    Usage::

        solver = ARCSolver()
        predictions = solver.solve_task_file("path/to/task.json")
    """

    def __init__(
        self,
        registry: Optional[DSLRegistry] = None,
        max_iterations: int = 5,
        beam_width: int = 64,
        max_depth: int = 3,
        complexity_weight: float = 0.05,
    ) -> None:
        self.registry = registry if registry is not None else DSLRegistry()
        self.controller = ActiveInferenceController(
            registry=self.registry,
            max_iterations=max_iterations,
            beam_width=beam_width,
            max_depth=max_depth,
            complexity_weight=complexity_weight,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve_task(
        self,
        task: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Solve a single ARC task dict.

        Parameters
        ----------
        task : dict with "train" and "test" keys (standard ARC format)

        Returns
        -------
        dict with keys:
            - "program": list[str] — the discovered program
            - "predictions": list[Grid] — one prediction per test input
            - "train_score": float — mean pixel accuracy on training pairs
            - "solved": bool — True if perfectly solved on training pairs
        """
        train_pairs = extract_pairs(task)
        test_inputs = extract_test_inputs(task)

        if not train_pairs:
            logger.warning("Task has no training pairs — returning empty predictions.")
            return {
                "program": [],
                "predictions": [[[0]] for _ in test_inputs],
                "train_score": 0.0,
                "solved": False,
            }

        # Run the active inference loop
        program, state = self.controller.solve(train_pairs)

        train_score = state.best_result.score if state.best_result else 0.0
        solved = state.best_result.is_perfect if state.best_result else False

        # Predict test outputs
        predictions: List[Grid] = []
        for test_inp in test_inputs:
            if program:
                pred = self.controller.predict(program, test_inp)
                predictions.append(pred if pred is not None else test_inp)
            else:
                # Fallback: return the input unchanged
                predictions.append(test_inp)

        return {
            "program": program or [],
            "predictions": predictions,
            "train_score": train_score,
            "solved": solved,
        }

    def solve_task_file(
        self,
        path: str | Path,
    ) -> Dict[str, Any]:
        """
        Convenience wrapper: load a JSON task file and solve it.

        Parameters
        ----------
        path : path to the .json task file

        Returns
        -------
        Same dict as solve_task().
        """
        task = load_task(path)
        return self.solve_task(task)

    def solve_directory(
        self,
        directory: str | Path,
        pattern: str = "*.json",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Solve all task files matching *pattern* inside *directory*.

        Parameters
        ----------
        directory : path to a folder containing ARC task JSON files
        pattern : glob pattern (default "*.json")

        Returns
        -------
        dict mapping task filename → result dict
        """
        directory = Path(directory)
        results: Dict[str, Dict[str, Any]] = {}
        for task_path in sorted(directory.glob(pattern)):
            logger.info("Solving %s …", task_path.name)
            try:
                results[task_path.name] = self.solve_task_file(task_path)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to solve %s: %s", task_path.name, exc)
                results[task_path.name] = {
                    "program": [],
                    "predictions": [],
                    "train_score": 0.0,
                    "solved": False,
                    "error": str(exc),
                }
        return results
