"""Tests for the models module.

These tests verify the models' data structures, interface contracts, and
the enforcement of abstract method requirements. Because the BaseWorldModel
is abstract, tests focus on the GoalHypothesis and Prediction dataclasses.
"""

from __future__ import annotations

import numpy as np
import pytest

from arc_agi_3.models.base import BaseWorldModel, GoalHypothesis, Prediction


class TestGoalHypothesis:
    """Tests for the GoalHypothesis dataclass."""

    def test_goal_hypothesis_creation(self):
        goal = GoalHypothesis(
            description="Reach the top-right corner",
            confidence=0.85,
            evidence=["Agent moved closer to corner", "Score increased"],
        )
        assert goal.description == "Reach the top-right corner"
        assert goal.confidence == 0.85
        assert len(goal.evidence) == 2

    def test_goal_hypothesis_defaults(self):
        goal = GoalHypothesis(description="Unknown", confidence=0.0)
        assert goal.evidence == []


class TestPrediction:
    """Tests for the Prediction dataclass."""

    def test_prediction_creation(self):
        state = np.array([1.0, 2.0, 3.0])
        pred = Prediction(state=state, uncertainty=0.3)
        np.testing.assert_array_equal(pred.state, state)
        assert pred.uncertainty == 0.3


class TestBaseWorldModel:
    """Tests for the BaseWorldModel abstract interface."""

    def test_abstract_methods_enforced(self):
        with pytest.raises(TypeError):
            BaseWorldModel()  # type: ignore[abstract]
