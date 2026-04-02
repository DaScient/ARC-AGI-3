"""
Subsystem II: DSL Hyper-Generator / Program Synthesizer (The Poet)
===================================================================

Generates candidate programs (ordered sequences of DSL primitives) and
searches the program space using Beam Search guided by a delta-error
signal from the Symbolic Verifier.

A "program" is represented as a list of DSL primitive names, e.g.::

    ["rotate_90", "flip_vertical"]

The synthesiser iterates through increasing program lengths and applies
Beam Search to keep only the most promising partial programs alive.
"""

from __future__ import annotations

import itertools
import logging
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .dsl import DSLRegistry, Grid

logger = logging.getLogger(__name__)

# A program is just an ordered list of DSL primitive names.
Program = List[str]

# A scored candidate is (score, program).
ScoredCandidate = Tuple[float, Program]


# ---------------------------------------------------------------------------
# Helper: apply a program to a grid
# ---------------------------------------------------------------------------

def apply_program(
    program: Program,
    grid: Grid,
    registry: DSLRegistry,
) -> Optional[Grid]:
    """
    Execute *program* on *grid*, returning the transformed grid or
    ``None`` if any step raises an exception.
    """
    result = [row[:] for row in grid]  # shallow copy
    for primitive in program:
        try:
            fn, kwargs = registry.get(primitive)
            result = fn(result, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Program step '%s' failed: %s", primitive, exc)
            return None
    return result


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def pixel_accuracy(predicted: Grid, expected: Grid) -> float:
    """
    Fraction of pixels that match between *predicted* and *expected*.

    Returns 0.0 if the grids have different shapes.
    """
    if len(predicted) != len(expected):
        return 0.0
    if any(len(r1) != len(r2) for r1, r2 in zip(predicted, expected)):
        return 0.0
    total = sum(len(row) for row in expected)
    if total == 0:
        return 1.0
    correct = sum(
        1
        for row_p, row_e in zip(predicted, expected)
        for vp, ve in zip(row_p, row_e)
        if vp == ve
    )
    return correct / total


def score_program(
    program: Program,
    train_pairs: List[Tuple[Grid, Grid]],
    registry: DSLRegistry,
) -> float:
    """
    Average pixel accuracy across all training pairs.

    Returns -1.0 if the program fails on any example.
    """
    if not train_pairs:
        return 0.0
    total = 0.0
    for inp, expected in train_pairs:
        predicted = apply_program(program, inp, registry)
        if predicted is None:
            return -1.0
        total += pixel_accuracy(predicted, expected)
    return total / len(train_pairs)


# ---------------------------------------------------------------------------
# Beam Search
# ---------------------------------------------------------------------------

class BeamSearch:
    """
    Iterative-deepening Beam Search over programs of increasing length.

    Parameters
    ----------
    registry : DSLRegistry
        Source of available DSL primitives.
    beam_width : int
        Number of partial programs retained at each depth.
    max_depth : int
        Maximum program length to explore.
    primitives : list[str] | None
        Subset of registry to search over (defaults to all).
    """

    def __init__(
        self,
        registry: DSLRegistry,
        beam_width: int = 64,
        max_depth: int = 3,
        primitives: Optional[List[str]] = None,
    ) -> None:
        self.registry = registry
        self.beam_width = beam_width
        self.max_depth = max_depth
        self.primitives = primitives if primitives is not None else registry.names()

    def search(
        self,
        train_pairs: List[Tuple[Grid, Grid]],
    ) -> Iterator[ScoredCandidate]:
        """
        Yield (score, program) candidates in descending order of score.

        Stops early once a perfect program (score == 1.0) is found.
        """
        # Depth 0 — identity
        beam: List[ScoredCandidate] = [(0.0, [])]

        for depth in range(1, self.max_depth + 1):
            candidates: List[ScoredCandidate] = []
            for _, partial in beam:
                for prim in self.primitives:
                    program = partial + [prim]
                    sc = score_program(program, train_pairs, self.registry)
                    if sc < 0:
                        continue
                    candidates.append((sc, program))

            if not candidates:
                break

            # Sort descending by score
            candidates.sort(key=lambda x: -x[0])

            # Yield the best at this depth
            for scored in candidates[: self.beam_width]:
                yield scored
                if scored[0] >= 1.0:
                    return

            # Prune beam
            beam = candidates[: self.beam_width]


# ---------------------------------------------------------------------------
# Delta-error decomposition (feedback to The Poet from The Critic)
# ---------------------------------------------------------------------------

def compute_delta(
    predicted: Grid,
    expected: Grid,
) -> Dict[str, Any]:
    """
    Return a structured description of the difference between *predicted*
    and *expected* for use as feedback.
    """
    delta: Dict[str, Any] = {}

    shape_matches = (
        len(predicted) == len(expected)
        and all(
            len(r1) == len(r2) for r1, r2 in zip(predicted, expected)
        )
    )
    delta["shape_matches"] = shape_matches

    if not shape_matches:
        delta["predicted_shape"] = (len(predicted), len(predicted[0]) if predicted else 0)
        delta["expected_shape"] = (len(expected), len(expected[0]) if expected else 0)
        return delta

    wrong_pixels: List[Tuple[int, int, int, int]] = []  # (r, c, got, want)
    for r, (row_p, row_e) in enumerate(zip(predicted, expected)):
        for c, (vp, ve) in enumerate(zip(row_p, row_e)):
            if vp != ve:
                wrong_pixels.append((r, c, vp, ve))

    delta["wrong_pixel_count"] = len(wrong_pixels)
    delta["wrong_pixels"] = wrong_pixels[:20]  # first 20 for brevity
    total = sum(len(row) for row in expected)
    delta["accuracy"] = 1.0 - len(wrong_pixels) / total if total > 0 else 1.0
    return delta


# ---------------------------------------------------------------------------
# Main synthesiser
# ---------------------------------------------------------------------------

class ProgramSynthesizer:
    """
    Subsystem II — The Poet.

    Combines Beam Search with delta-error feedback to produce programs
    that transform inputs to expected outputs.
    """

    def __init__(
        self,
        registry: Optional[DSLRegistry] = None,
        beam_width: int = 64,
        max_depth: int = 3,
    ) -> None:
        self.registry = registry if registry is not None else DSLRegistry()
        self.beam_width = beam_width
        self.max_depth = max_depth
        self._beam_search = BeamSearch(
            self.registry,
            beam_width=beam_width,
            max_depth=max_depth,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def synthesize(
        self,
        train_pairs: List[Tuple[Grid, Grid]],
        feedback: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredCandidate]:
        """
        Search for programs that solve the task defined by *train_pairs*.

        Parameters
        ----------
        train_pairs : list of (input_grid, output_grid)
        feedback : optional delta-error dict from the verifier

        Returns
        -------
        list of (score, program) sorted by descending score
        """
        primitives = self._prioritize_primitives(feedback)
        searcher = BeamSearch(
            self.registry,
            beam_width=self.beam_width,
            max_depth=self.max_depth,
            primitives=primitives,
        )

        results: List[ScoredCandidate] = []
        seen: set = set()
        for score, program in searcher.search(train_pairs):
            key = tuple(program)
            if key not in seen:
                seen.add(key)
                results.append((score, program))

        results.sort(key=lambda x: -x[0])
        return results

    def best_program(
        self,
        train_pairs: List[Tuple[Grid, Grid]],
        feedback: Optional[Dict[str, Any]] = None,
    ) -> Optional[Program]:
        """Return only the best-scoring program, or None if none found."""
        candidates = self.synthesize(train_pairs, feedback)
        if candidates:
            return candidates[0][1]
        return None

    # ------------------------------------------------------------------
    # Feedback-driven prioritisation
    # ------------------------------------------------------------------

    def _prioritize_primitives(
        self,
        feedback: Optional[Dict[str, Any]],
    ) -> List[str]:
        """
        Reorder primitives based on delta-error feedback so that the most
        likely helpful operations are tried first.
        """
        all_prims = self.registry.names()
        if feedback is None:
            return all_prims

        priority: List[str] = []
        rest: List[str] = []

        # If shapes don't match, prefer scaling/tiling operations
        if not feedback.get("shape_matches", True):
            scale_prims = {"upscale_2x", "upscale_3x", "tile_2x2", "crop_to_content"}
            priority = [p for p in all_prims if p in scale_prims]
            rest = [p for p in all_prims if p not in scale_prims]
        else:
            priority = all_prims
            rest = []

        return priority + rest
