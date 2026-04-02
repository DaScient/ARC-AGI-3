"""Tests for the agent module.

These tests verify the agent's data structures, interface contracts, and
observation/action handling. Because the BaseAgent is abstract, tests
focus on the Observation and Action dataclasses and on verifying that
subclass contracts are enforced.
"""

from __future__ import annotations

from typing import Any

import pytest

from arc_agi_3.agent.base import Action, BaseAgent, Observation


class _MockAgent(BaseAgent):
    """A minimal concrete agent for testing the BaseAgent interface."""

    def __init__(self) -> None:
        self._last_observation: Observation | None = None
        self._state: dict[str, Any] = {}

    def process_observation(self, observation: Observation) -> None:
        self._last_observation = observation

    def select_action(self, legal_actions: list[str]) -> Action:
        return Action(action_id=legal_actions[0])

    def get_state(self) -> dict[str, Any]:
        return dict(self._state)

    def set_state(self, state: dict[str, Any]) -> None:
        self._state = dict(state)

    def reset(self) -> None:
        self._last_observation = None
        self._state = {}


class TestObservation:
    """Tests for the Observation dataclass."""

    def test_observation_creation(self, sample_grid, sample_observation):
        assert sample_observation.grid == sample_grid
        assert len(sample_observation.legal_actions) == 5
        assert sample_observation.level == 1
        assert sample_observation.action_count == 0

    def test_observation_defaults(self):
        obs = Observation(grid=[[0]], legal_actions=["INTERACT"])
        assert obs.level == 0
        assert obs.action_count == 0
        assert obs.metadata == {}

    def test_observation_metadata(self, sample_observation):
        assert sample_observation.metadata["environment_id"] == "test_env_001"


class TestAction:
    """Tests for the Action dataclass."""

    def test_action_creation(self, sample_action):
        assert sample_action.action_id == "MOVE_UP"

    def test_action_equality(self):
        a1 = Action(action_id="INTERACT")
        a2 = Action(action_id="INTERACT")
        assert a1 == a2


class TestBaseAgent:
    """Tests for the BaseAgent abstract interface and mock implementation."""

    def test_process_observation(self, sample_observation):
        agent = _MockAgent()
        agent.process_observation(sample_observation)
        assert agent._last_observation is sample_observation

    def test_select_action(self, sample_legal_actions):
        agent = _MockAgent()
        action = agent.select_action(sample_legal_actions)
        assert action.action_id == sample_legal_actions[0]

    def test_get_and_set_state(self):
        agent = _MockAgent()
        agent.set_state({"turn": 5, "score": 0.8})
        state = agent.get_state()
        assert state["turn"] == 5
        assert state["score"] == 0.8

    def test_reset(self, sample_observation):
        agent = _MockAgent()
        agent.process_observation(sample_observation)
        agent.set_state({"turn": 5})
        agent.reset()
        assert agent._last_observation is None
        assert agent._state == {}

    def test_abstract_methods_enforced(self):
        with pytest.raises(TypeError):
            BaseAgent()  # type: ignore[abstract]
