"""
Subsystem III: Symbolic Verifier (The Critic)
==============================================

Executes candidate programs in a sandboxed Python environment, tests
them against all training pairs, and produces structured delta-error
feedback when a program fails.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .dsl import DSLRegistry, Grid
from .synthesizer import (
    Program,
    ScoredCandidate,
    apply_program,
    compute_delta,
    pixel_accuracy,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verification result
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    """Outcome of verifying a program against a set of training pairs."""

    program: Program
    passed: bool
    score: float  # mean pixel accuracy across all pairs (0.0-1.0)
    pair_scores: List[float] = field(default_factory=list)
    deltas: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None

    @property
    def is_perfect(self) -> bool:
        return self.passed and self.score >= 1.0


# ---------------------------------------------------------------------------
# Verifier
# ---------------------------------------------------------------------------

class SymbolicVerifier:
    """
    Subsystem III — The Critic.

    Executes programs against training pairs and delivers delta-error
    feedback to the synthesiser.
    """

    def __init__(self, registry: Optional[DSLRegistry] = None) -> None:
        self.registry = registry if registry is not None else DSLRegistry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify(
        self,
        program: Program,
        train_pairs: List[Tuple[Grid, Grid]],
    ) -> VerificationResult:
        """
        Run *program* on every training input and compare against expected.

        Parameters
        ----------
        program : list[str]
            Ordered list of DSL primitive names.
        train_pairs : list of (input, expected_output)

        Returns
        -------
        VerificationResult
        """
        pair_scores: List[float] = []
        deltas: List[Dict[str, Any]] = []

        for idx, (inp, expected) in enumerate(train_pairs):
            try:
                predicted = apply_program(program, inp, self.registry)
            except Exception as exc:  # noqa: BLE001
                msg = f"Pair {idx}: execution error — {exc}"
                logger.warning(msg)
                return VerificationResult(
                    program=program,
                    passed=False,
                    score=0.0,
                    error_message=msg,
                )

            if predicted is None:
                msg = f"Pair {idx}: program returned None"
                return VerificationResult(
                    program=program,
                    passed=False,
                    score=0.0,
                    error_message=msg,
                )

            sc = pixel_accuracy(predicted, expected)
            pair_scores.append(sc)
            if sc < 1.0:
                deltas.append(compute_delta(predicted, expected))

        mean_score = sum(pair_scores) / len(pair_scores) if pair_scores else 0.0
        passed = all(s >= 1.0 for s in pair_scores)

        return VerificationResult(
            program=program,
            passed=passed,
            score=mean_score,
            pair_scores=pair_scores,
            deltas=deltas,
        )

    def select_best(
        self,
        candidates: List[ScoredCandidate],
        train_pairs: List[Tuple[Grid, Grid]],
    ) -> Optional[VerificationResult]:
        """
        Verify a ranked list of candidates and return the first perfect
        solution, or the best partial solution if none passes completely.

        Parameters
        ----------
        candidates : list of (score, program) sorted descending by score
        train_pairs : list of (input, expected_output)

        Returns
        -------
        VerificationResult or None
        """
        best: Optional[VerificationResult] = None

        for _, program in candidates:
            result = self.verify(program, train_pairs)
            if result.is_perfect:
                return result
            if best is None or result.score > best.score:
                best = result

        return best

    def generate_feedback(
        self,
        result: VerificationResult,
    ) -> Dict[str, Any]:
        """
        Produce structured feedback suitable for the synthesiser.

        Parameters
        ----------
        result : VerificationResult from a failed verification

        Returns
        -------
        dict with keys:
            - "best_program": program that achieved the best score so far
            - "score": best mean pixel accuracy
            - "shape_matches": bool
            - "wrong_pixel_count": total wrong pixels across pairs
        """
        feedback: Dict[str, Any] = {
            "best_program": result.program,
            "score": result.score,
            "shape_matches": True,
            "wrong_pixel_count": 0,
        }

        for delta in result.deltas:
            if not delta.get("shape_matches", True):
                feedback["shape_matches"] = False
            feedback["wrong_pixel_count"] += delta.get("wrong_pixel_count", 0)

        return feedback
