"""Tests for the evaluation module.

These tests verify the Scorer's RHAE computation, edge case handling,
and score breakdown generation.
"""

from __future__ import annotations

import pytest

from arc_agi_3.evaluation.scorer import Scorer


class TestScorer:
    """Tests for the Scorer class and RHAE computation."""

    def test_perfect_score(self, scorer):
        """Agent matches human baseline exactly — should receive 1.0."""
        assert scorer.compute_rhae(agent_actions=10, human_baseline=10) == 1.0

    def test_better_than_human(self, scorer):
        """Agent uses fewer actions than human — should be capped at 1.0."""
        assert scorer.compute_rhae(agent_actions=5, human_baseline=10) == 1.0

    def test_double_human_actions(self, scorer):
        """Agent uses twice the human baseline — should receive 0.25."""
        score = scorer.compute_rhae(agent_actions=20, human_baseline=10)
        assert abs(score - 0.25) < 1e-9

    def test_triple_human_actions(self, scorer):
        """Agent uses three times the baseline — should receive ~0.111."""
        score = scorer.compute_rhae(agent_actions=30, human_baseline=10)
        expected = (10 / 30) ** 2
        assert abs(score - expected) < 1e-9

    def test_exceeds_multiplier_threshold(self, scorer):
        """Agent exceeds 5x the baseline — should receive 0.0."""
        assert scorer.compute_rhae(agent_actions=51, human_baseline=10) == 0.0

    def test_exactly_at_multiplier(self, scorer):
        """Agent uses exactly 5x the baseline — should still score."""
        score = scorer.compute_rhae(agent_actions=50, human_baseline=10)
        expected = (10 / 50) ** 2
        assert abs(score - expected) < 1e-9

    def test_zero_agent_actions(self, scorer):
        """Agent takes no actions — should receive 0.0."""
        assert scorer.compute_rhae(agent_actions=0, human_baseline=10) == 0.0

    def test_negative_agent_actions_raises(self, scorer):
        """Negative agent actions should raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            scorer.compute_rhae(agent_actions=-1, human_baseline=10)

    def test_zero_human_baseline_raises(self, scorer):
        """Zero human baseline should raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            scorer.compute_rhae(agent_actions=10, human_baseline=0)

    def test_negative_human_baseline_raises(self, scorer):
        """Negative human baseline should raise ValueError."""
        with pytest.raises(ValueError, match="positive"):
            scorer.compute_rhae(agent_actions=10, human_baseline=-5)

    def test_invalid_multiplier_raises(self):
        """Multiplier below 1.0 should raise ValueError."""
        with pytest.raises(ValueError, match=r"must be >= 1\.0"):
            Scorer(human_baseline_multiplier=0.5)

    def test_compute_episode_score(self, scorer):
        """Episode score should include correct metadata and RHAE."""
        breakdown = scorer.compute_episode_score(
            environment_id="env_001",
            agent_actions=10,
            human_baseline=10,
            levels_completed=3,
        )
        assert breakdown.environment_id == "env_001"
        assert breakdown.rhae_score == 1.0
        assert breakdown.agent_actions == 10
        assert breakdown.human_baseline == 10
        assert breakdown.levels_completed == 3
        assert breakdown.per_level_scores == []

    def test_custom_multiplier(self):
        """Custom multiplier should change the threshold."""
        scorer = Scorer(human_baseline_multiplier=3.0)
        assert scorer.compute_rhae(agent_actions=31, human_baseline=10) == 0.0
        score = scorer.compute_rhae(agent_actions=30, human_baseline=10)
        assert score > 0.0
