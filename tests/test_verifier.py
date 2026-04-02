"""Tests for the Symbolic Verifier (The Critic)."""
import pytest

from arc_solver.dsl import DSLRegistry
from arc_solver.verifier import SymbolicVerifier, VerificationResult


@pytest.fixture
def reg():
    return DSLRegistry()


@pytest.fixture
def verifier(reg):
    return SymbolicVerifier(registry=reg)


# ---------------------------------------------------------------------------
# VerificationResult
# ---------------------------------------------------------------------------

class TestVerificationResult:
    def test_is_perfect_true(self):
        r = VerificationResult(program=["identity"], passed=True, score=1.0)
        assert r.is_perfect is True

    def test_is_perfect_false_wrong_score(self):
        r = VerificationResult(program=["identity"], passed=True, score=0.9)
        assert r.is_perfect is False

    def test_is_perfect_false_not_passed(self):
        r = VerificationResult(program=["identity"], passed=False, score=1.0)
        assert r.is_perfect is False


# ---------------------------------------------------------------------------
# SymbolicVerifier.verify
# ---------------------------------------------------------------------------

class TestVerify:
    def test_verify_perfect(self, verifier):
        grid = [[1, 2], [3, 4]]
        result = verifier.verify(["identity"], [(grid, grid)])
        assert result.passed is True
        assert result.score == 1.0
        assert result.is_perfect is True

    def test_verify_imperfect(self, verifier):
        inp = [[1, 0]]
        out = [[1, 1]]
        result = verifier.verify(["identity"], [(inp, out)])
        assert result.passed is False
        assert result.score < 1.0

    def test_verify_invalid_program(self, verifier):
        grid = [[1]]
        result = verifier.verify(["bad_op"], [(grid, grid)])
        assert result.passed is False
        assert result.score == 0.0

    def test_verify_rotate_task(self, verifier):
        # input → rotate_90 → expected
        inp = [[1, 2], [3, 4]]
        from arc_solver.dsl import rotate_90
        out = rotate_90(inp)
        result = verifier.verify(["rotate_90"], [(inp, out)])
        assert result.passed is True

    def test_verify_multiple_pairs(self, verifier):
        pairs = [
            ([[1, 0]], [[1, 0]]),
            ([[0, 2]], [[0, 2]]),
        ]
        result = verifier.verify(["identity"], pairs)
        assert result.passed is True
        assert result.score == 1.0
        assert len(result.pair_scores) == 2

    def test_verify_partial_failure(self, verifier):
        # First pair passes, second fails
        pairs = [
            ([[1, 0]], [[1, 0]]),      # passes
            ([[0, 2]], [[9, 9]]),      # fails
        ]
        result = verifier.verify(["identity"], pairs)
        assert result.passed is False
        assert 0.0 < result.score < 1.0


# ---------------------------------------------------------------------------
# SymbolicVerifier.select_best
# ---------------------------------------------------------------------------

class TestSelectBest:
    def test_select_best_perfect(self, verifier):
        grid = [[1, 2]]
        candidates = [(1.0, ["identity"]), (0.5, ["rotate_90"])]
        result = verifier.select_best(candidates, [(grid, grid)])
        assert result is not None
        assert result.is_perfect is True
        assert result.program == ["identity"]

    def test_select_best_no_perfect(self, verifier):
        inp = [[1, 0]]
        out = [[0, 1]]
        # Neither of these perfectly transforms inp → out
        candidates = [(0.5, ["identity"]), (0.3, ["rotate_90"])]
        result = verifier.select_best(candidates, [(inp, out)])
        assert result is not None
        # Should return the best partial

    def test_select_best_empty_candidates(self, verifier):
        result = verifier.select_best([], [([[1]], [[1]])])
        assert result is None


# ---------------------------------------------------------------------------
# SymbolicVerifier.generate_feedback
# ---------------------------------------------------------------------------

class TestGenerateFeedback:
    def test_feedback_structure(self, verifier):
        result = VerificationResult(
            program=["rotate_90"],
            passed=False,
            score=0.5,
            deltas=[{"shape_matches": True, "wrong_pixel_count": 2, "accuracy": 0.5}],
        )
        feedback = verifier.generate_feedback(result)
        assert "best_program" in feedback
        assert "score" in feedback
        assert "shape_matches" in feedback
        assert "wrong_pixel_count" in feedback
        assert feedback["wrong_pixel_count"] == 2
        assert feedback["score"] == 0.5

    def test_feedback_shape_mismatch(self, verifier):
        result = VerificationResult(
            program=["crop_to_content"],
            passed=False,
            score=0.0,
            deltas=[{"shape_matches": False, "wrong_pixel_count": 0}],
        )
        feedback = verifier.generate_feedback(result)
        assert feedback["shape_matches"] is False
