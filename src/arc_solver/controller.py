"""
Subsystem IV: Active Inference Controller (The Will)
=====================================================

Minimises variational free energy by orchestrating recursive loops
between The Seer, The Poet, and The Critic.

The controller operates as a meta-loop:

  1. Perceive the task (Seer).
  2. Synthesise candidate programs (Poet) informed by perception hints.
  3. Verify candidates (Critic).
  4. If imperfect: generate delta-error feedback → refine hypothesis.
  5. Repeat until a perfect solution is found or the iteration budget
     is exhausted (Occam's Razor: prefer simpler programs).

Free energy is approximated here as::

    F = (1 - accuracy) + λ · program_complexity

where *λ* is a regularisation weight that penalises long programs,
implementing an Occam's Razor prior.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .dsl import DSLRegistry, Grid
from .perception import GridPerception, SceneDescription
from .synthesizer import Program, ProgramSynthesizer, ScoredCandidate, apply_program
from .verifier import SymbolicVerifier, VerificationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Free energy
# ---------------------------------------------------------------------------

def variational_free_energy(
    accuracy: float,
    program_length: int,
    complexity_weight: float = 0.05,
) -> float:
    """
    Approximate variational free energy.

    Lower is better (more confident, simpler explanation).

    Parameters
    ----------
    accuracy : float
        Pixel accuracy on training pairs (0–1).
    program_length : int
        Number of DSL steps in the program.
    complexity_weight : float
        λ — regularisation strength penalising long programs.
    """
    reconstruction_error = 1.0 - accuracy
    complexity_cost = complexity_weight * program_length
    return reconstruction_error + complexity_cost


# ---------------------------------------------------------------------------
# Controller state
# ---------------------------------------------------------------------------

@dataclass
class ControllerState:
    """Mutable state maintained across inference iterations."""

    iteration: int = 0
    best_result: Optional[VerificationResult] = None
    free_energy: float = float("inf")
    feedback: Optional[Dict[str, Any]] = None
    perception: Optional[SceneDescription] = None
    history: List[Dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Active Inference Controller
# ---------------------------------------------------------------------------

class ActiveInferenceController:
    """
    Subsystem IV — The Will.

    Orchestrates the Perception → Synthesis → Verification loop to
    minimise variational free energy.
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
        self.max_iterations = max_iterations
        self.complexity_weight = complexity_weight

        self.perceiver = GridPerception()
        self.synthesizer = ProgramSynthesizer(
            registry=self.registry,
            beam_width=beam_width,
            max_depth=max_depth,
        )
        self.verifier = SymbolicVerifier(registry=self.registry)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def solve(
        self,
        train_pairs: List[Tuple[Grid, Grid]],
        test_input: Optional[Grid] = None,
    ) -> Tuple[Optional[Program], ControllerState]:
        """
        Run the active inference loop to find a program that solves the task.

        Parameters
        ----------
        train_pairs : list of (input_grid, output_grid)
        test_input : optional test grid (not used for training)

        Returns
        -------
        (best_program, state)
            best_program is None if no candidate was found.
        """
        state = ControllerState()

        # Perceive all training inputs
        if train_pairs:
            state.perception = self.perceiver.perceive(train_pairs[0][0])
            logger.info(
                "Perceived %d objects, %d unique colors",
                state.perception.object_count,
                len(state.perception.unique_colors),
            )

        for iteration in range(self.max_iterations):
            state.iteration = iteration
            logger.info("Inference iteration %d / %d", iteration + 1, self.max_iterations)

            # 1. Synthesise candidates (The Poet)
            candidates = self.synthesizer.synthesize(
                train_pairs, feedback=state.feedback
            )

            if not candidates:
                logger.warning("No candidates generated at iteration %d", iteration)
                break

            # 2. Verify (The Critic)
            result = self.verifier.select_best(candidates, train_pairs)
            if result is None:
                break

            # 3. Compute free energy
            fe = variational_free_energy(
                accuracy=result.score,
                program_length=len(result.program),
                complexity_weight=self.complexity_weight,
            )
            logger.info(
                "Best program: %s | score=%.4f | F=%.4f",
                result.program,
                result.score,
                fe,
            )

            # 4. Update state
            if state.best_result is None or fe < state.free_energy:
                state.best_result = result
                state.free_energy = fe

            state.history.append(
                {
                    "iteration": iteration,
                    "program": result.program,
                    "score": result.score,
                    "free_energy": fe,
                }
            )

            # 5. Perfect solution → stop
            if result.is_perfect:
                logger.info("Perfect solution found: %s", result.program)
                return result.program, state

            # 6. Generate feedback for next iteration (The Critic → The Poet)
            state.feedback = self.verifier.generate_feedback(result)

        # Return best partial solution
        if state.best_result is not None:
            return state.best_result.program, state
        return None, state

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(
        self,
        program: Program,
        test_input: Grid,
    ) -> Optional[Grid]:
        """
        Apply a solved program to a test input.

        Returns the predicted output grid, or None on failure.
        """
        return apply_program(program, test_input, self.registry)
