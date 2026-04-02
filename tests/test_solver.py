"""Integration tests for the ARCSolver end-to-end pipeline."""
import json
import pytest
from pathlib import Path

from arc_solver.solver import ARCSolver, load_task, extract_pairs, extract_test_inputs


SAMPLE_TASKS = Path(__file__).parent.parent / "data" / "sample_tasks"


# ---------------------------------------------------------------------------
# Task loading helpers
# ---------------------------------------------------------------------------

class TestTaskLoading:
    def test_load_task_from_file(self, tmp_path):
        task = {
            "train": [{"input": [[1]], "output": [[1]]}],
            "test":  [{"input": [[2]]}],
        }
        p = tmp_path / "task.json"
        p.write_text(json.dumps(task))
        loaded = load_task(p)
        assert loaded["train"][0]["input"] == [[1]]

    def test_extract_pairs(self):
        task = {
            "train": [
                {"input": [[1, 2]], "output": [[3, 4]]},
                {"input": [[5]], "output": [[6]]},
            ]
        }
        pairs = extract_pairs(task)
        assert len(pairs) == 2
        assert pairs[0] == ([[1, 2]], [[3, 4]])

    def test_extract_test_inputs(self):
        task = {"test": [{"input": [[9, 8]]}, {"input": [[7]]}]}
        inputs = extract_test_inputs(task)
        assert inputs == [[[9, 8]], [[7]]]

    def test_extract_pairs_empty(self):
        assert extract_pairs({}) == []

    def test_extract_test_inputs_empty(self):
        assert extract_test_inputs({}) == []


# ---------------------------------------------------------------------------
# ARCSolver
# ---------------------------------------------------------------------------

class TestARCSolver:
    @pytest.fixture
    def solver(self):
        return ARCSolver(max_iterations=2, beam_width=32, max_depth=1)

    def test_solve_task_identity(self, solver):
        grid = [[1, 2], [3, 4]]
        task = {
            "train": [{"input": grid, "output": grid}],
            "test":  [{"input": grid}],
        }
        result = solver.solve_task(task)
        assert "program" in result
        assert "predictions" in result
        assert "train_score" in result
        assert "solved" in result
        assert len(result["predictions"]) == 1

    def test_solve_task_no_train_pairs(self, solver):
        task = {"train": [], "test": [{"input": [[1]]}]}
        result = solver.solve_task(task)
        assert result["solved"] is False
        assert result["predictions"] == [[[0]]]

    def test_solve_task_no_test(self, solver):
        grid = [[1]]
        task = {"train": [{"input": grid, "output": grid}], "test": []}
        result = solver.solve_task(task)
        assert result["predictions"] == []

    def test_solve_task_file_identity(self, solver, tmp_path):
        task = {
            "train": [{"input": [[1, 0]], "output": [[1, 0]]}],
            "test":  [{"input": [[2, 0]]}],
        }
        p = tmp_path / "task.json"
        p.write_text(json.dumps(task))
        result = solver.solve_task_file(p)
        assert "predictions" in result

    def test_solve_directory(self, solver, tmp_path):
        task = {
            "train": [{"input": [[1]], "output": [[1]]}],
            "test":  [{"input": [[1]]}],
        }
        (tmp_path / "t1.json").write_text(json.dumps(task))
        (tmp_path / "t2.json").write_text(json.dumps(task))
        results = solver.solve_directory(tmp_path)
        assert len(results) == 2
        for r in results.values():
            assert "predictions" in r

    def test_solve_directory_bad_file(self, solver, tmp_path):
        (tmp_path / "bad.json").write_text("not json{{{")
        results = solver.solve_directory(tmp_path)
        assert len(results) == 1
        assert "error" in results["bad.json"]

    def test_solve_sample_identity_task(self, solver):
        """Smoke test using the identity sample task."""
        p = SAMPLE_TASKS / "identity.json"
        if not p.exists():
            pytest.skip("Sample task not found")
        result = solver.solve_task_file(p)
        assert result["train_score"] >= 0.0
