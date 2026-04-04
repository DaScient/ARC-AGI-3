"""Tests for the Active Inference Controller (The Will)."""
import pytest

from arc_solver.controller import (
    ActiveInferenceController,
    ControllerState,
    variational_free_energy,
)


# ---------------------------------------------------------------------------
# variational_free_energy
# ---------------------------------------------------------------------------

class TestFreeEnergy:
    def test_perfect_accuracy_zero_complexity(self):
        fe = variational_free_energy(accuracy=1.0, program_length=0)
        assert fe == pytest.approx(0.0)

    def test_zero_accuracy(self):
        fe = variational_free_energy(accuracy=0.0, program_length=0)
        assert fe == pytest.approx(1.0)

    def test_complexity_penalty(self):
        fe_short = variational_free_energy(accuracy=1.0, program_length=1)
        fe_long  = variational_free_energy(accuracy=1.0, program_length=5)
        assert fe_long > fe_short

    def test_custom_weight(self):
        fe = variational_free_energy(accuracy=1.0, program_length=10, complexity_weight=0.1)
        assert fe == pytest.approx(1.0)  # 0 + 0.1*10


# ---------------------------------------------------------------------------
# ActiveInferenceController
# ---------------------------------------------------------------------------

class TestController:
    def test_solve_identity_task(self):
        controller = ActiveInferenceController(max_iterations=2, max_depth=1)
        grid = [[1, 2], [3, 4]]
        train = [(grid, grid)]
        program, state = controller.solve(train)
        assert isinstance(state, ControllerState)
        # Should find identity (or equivalent)
        assert program is not None

    def test_solve_returns_state_with_history(self):
        controller = ActiveInferenceController(max_iterations=2, max_depth=1)
        grid = [[1]]
        train = [(grid, grid)]
        _, state = controller.solve(train)
        assert isinstance(state.history, list)

    def test_solve_empty_train(self):
        controller = ActiveInferenceController(max_iterations=1)
        program, state = controller.solve([])
        # With no training pairs the system should not crash
        assert state is not None

    def test_predict_with_program(self):
        controller = ActiveInferenceController(max_iterations=1, max_depth=1)
        grid = [[1, 2], [3, 4]]
        program = ["identity"]
        result = controller.predict(program, grid)
        assert result == grid

    def test_predict_empty_program(self):
        controller = ActiveInferenceController(max_iterations=1, max_depth=1)
        grid = [[5, 6]]
        result = controller.predict([], grid)
        assert result == grid

    def test_predict_invalid_program_returns_none(self):
        controller = ActiveInferenceController(max_iterations=1, max_depth=1)
        grid = [[1]]
        result = controller.predict(["bad_op"], grid)
        assert result is None

    def test_controller_state_initial(self):
        state = ControllerState()
        assert state.iteration == 0
        assert state.best_result is None
        assert state.free_energy == float("inf")
        assert state.feedback is None
        assert state.history == []

    def test_solve_rotation_task(self):
        from arc_solver.dsl import rotate_90
        controller = ActiveInferenceController(max_iterations=3, max_depth=2)
        inp = [[0, 1, 0], [0, 1, 0], [0, 1, 0]]
        out = rotate_90(inp)
        train = [(inp, out)]
        program, state = controller.solve(train)
        assert program is not None
        # Verify the found program actually works
        if state.best_result:
            assert state.best_result.score > 0.0
