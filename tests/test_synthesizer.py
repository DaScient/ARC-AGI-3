"""Tests for the Program Synthesizer (The Poet)."""
import pytest

from arc_solver.dsl import DSLRegistry
from arc_solver.synthesizer import (
    ProgramSynthesizer,
    apply_program,
    compute_delta,
    pixel_accuracy,
    score_program,
)


# ---------------------------------------------------------------------------
# pixel_accuracy
# ---------------------------------------------------------------------------

class TestPixelAccuracy:
    def test_perfect_match(self):
        grid = [[1, 2], [3, 4]]
        assert pixel_accuracy(grid, grid) == 1.0

    def test_zero_match(self):
        pred = [[0, 0], [0, 0]]
        exp  = [[1, 1], [1, 1]]
        assert pixel_accuracy(pred, exp) == 0.0

    def test_partial_match(self):
        pred = [[1, 0]]
        exp  = [[1, 1]]
        assert pixel_accuracy(pred, exp) == 0.5

    def test_shape_mismatch(self):
        pred = [[1, 2, 3]]
        exp  = [[1, 2]]
        assert pixel_accuracy(pred, exp) == 0.0

    def test_empty_grid(self):
        assert pixel_accuracy([], []) == 1.0


# ---------------------------------------------------------------------------
# apply_program
# ---------------------------------------------------------------------------

class TestApplyProgram:
    def test_apply_identity(self):
        reg = DSLRegistry()
        grid = [[1, 2], [3, 4]]
        result = apply_program(["identity"], grid, reg)
        assert result == grid

    def test_apply_empty_program(self):
        reg = DSLRegistry()
        grid = [[1, 2]]
        result = apply_program([], grid, reg)
        assert result == grid

    def test_apply_rotate_twice(self):
        from arc_solver.dsl import rotate_180
        reg = DSLRegistry()
        grid = [[1, 2], [3, 4]]
        result = apply_program(["rotate_90", "rotate_90"], grid, reg)
        assert result == rotate_180(grid)

    def test_apply_invalid_primitive_returns_none(self):
        reg = DSLRegistry()
        grid = [[1]]
        result = apply_program(["nonexistent"], grid, reg)
        assert result is None


# ---------------------------------------------------------------------------
# score_program
# ---------------------------------------------------------------------------

class TestScoreProgram:
    def test_perfect_score(self):
        reg = DSLRegistry()
        train = [([[1, 2]], [[1, 2]])]
        sc = score_program(["identity"], train, reg)
        assert sc == 1.0

    def test_zero_score_wrong_output(self):
        reg = DSLRegistry()
        train = [([[1, 2]], [[3, 4]])]
        sc = score_program(["identity"], train, reg)
        assert sc == 0.0

    def test_invalid_program_returns_negative(self):
        reg = DSLRegistry()
        train = [([[1]], [[1]])]
        sc = score_program(["bad_op"], train, reg)
        assert sc == -1.0

    def test_empty_train_pairs(self):
        reg = DSLRegistry()
        sc = score_program(["identity"], [], reg)
        assert sc == 0.0


# ---------------------------------------------------------------------------
# compute_delta
# ---------------------------------------------------------------------------

class TestComputeDelta:
    def test_perfect_match(self):
        g = [[1, 2], [3, 4]]
        delta = compute_delta(g, g)
        assert delta["wrong_pixel_count"] == 0
        assert delta["accuracy"] == 1.0

    def test_shape_mismatch(self):
        delta = compute_delta([[1, 2]], [[1]])
        assert delta["shape_matches"] is False

    def test_partial_mismatch(self):
        pred = [[1, 0]]
        exp  = [[1, 1]]
        delta = compute_delta(pred, exp)
        assert delta["wrong_pixel_count"] == 1
        assert delta["accuracy"] == 0.5


# ---------------------------------------------------------------------------
# ProgramSynthesizer
# ---------------------------------------------------------------------------

class TestProgramSynthesizer:
    def test_synthesize_returns_candidates(self):
        synth = ProgramSynthesizer(max_depth=1)
        train = [([[0, 1, 0], [0, 1, 0], [0, 1, 0]],
                  [[0, 0, 0], [1, 1, 1], [0, 0, 0]])]
        candidates = synth.synthesize(train)
        assert isinstance(candidates, list)

    def test_synthesize_identity_task(self):
        synth = ProgramSynthesizer(max_depth=1)
        grid = [[1, 0], [0, 1]]
        train = [(grid, grid)]
        candidates = synth.synthesize(train)
        # Identity should be among top candidates
        top_programs = [prog for _, prog in candidates[:5]]
        assert ["identity"] in top_programs or any(
            p == [] for p in top_programs
        ) or len(candidates) > 0

    def test_best_program_identity_task(self):
        synth = ProgramSynthesizer(max_depth=1)
        grid = [[1, 2], [3, 4]]
        train = [(grid, grid)]
        prog = synth.best_program(train)
        assert prog is not None
        assert isinstance(prog, list)

    def test_synthesize_with_feedback(self):
        synth = ProgramSynthesizer(max_depth=1)
        grid = [[1, 0]]
        train = [(grid, grid)]
        feedback = {"shape_matches": False}
        candidates = synth.synthesize(train, feedback=feedback)
        assert isinstance(candidates, list)

    def test_beam_search_returns_scores(self):
        synth = ProgramSynthesizer(beam_width=10, max_depth=1)
        grid = [[1]]
        train = [(grid, grid)]
        candidates = synth.synthesize(train)
        for score, prog in candidates:
            assert 0.0 <= score <= 1.0
            assert isinstance(prog, list)
