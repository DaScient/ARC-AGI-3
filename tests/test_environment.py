"""Tests for the environment module.

These tests verify the environment's data structures, interface contracts,
and the enforcement of abstract method requirements. Because the
BaseEnvironment is abstract, tests focus on the EpisodeResult dataclass
and on verifying subclass contracts.
"""

from __future__ import annotations

import pytest

from arc_agi_3.agent.base import Action, Observation
from arc_agi_3.environment.base import BaseEnvironment, EpisodeResult


class _MockEnvironment(BaseEnvironment):
    """A minimal concrete environment for testing the BaseEnvironment interface."""

    def __init__(self) -> None:
        self._connected = False
        self._episode_active = False
        self._turn_count = 0

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def start_episode(self, environment_id: str) -> Observation:
        self._episode_active = True
        self._turn_count = 0
        return Observation(
            grid=[[0, 1], [2, 3]],
            legal_actions=["MOVE_UP", "MOVE_DOWN"],
            level=1,
            action_count=0,
            metadata={"environment_id": environment_id},
        )

    def step(self, action: Action) -> tuple[Observation, bool]:
        self._turn_count += 1
        terminated = self._turn_count >= 5
        return (
            Observation(
                grid=[[1, 2], [3, 4]],
                legal_actions=["MOVE_UP", "MOVE_DOWN"],
                level=1,
                action_count=self._turn_count,
            ),
            terminated,
        )

    def end_episode(self) -> EpisodeResult:
        self._episode_active = False
        return EpisodeResult(
            environment_id="test_env",
            levels_completed=1,
            total_actions=self._turn_count,
            success=True,
        )


class TestEpisodeResult:
    """Tests for the EpisodeResult dataclass."""

    def test_episode_result_creation(self):
        result = EpisodeResult(
            environment_id="env_001",
            levels_completed=3,
            total_actions=42,
            success=True,
        )
        assert result.environment_id == "env_001"
        assert result.levels_completed == 3
        assert result.total_actions == 42
        assert result.success is True
        assert result.metadata == {}

    def test_episode_result_with_metadata(self):
        result = EpisodeResult(
            environment_id="env_002",
            levels_completed=0,
            total_actions=100,
            success=False,
            metadata={"reason": "action_budget_exceeded"},
        )
        assert result.metadata["reason"] == "action_budget_exceeded"


class TestBaseEnvironment:
    """Tests for the BaseEnvironment abstract interface and mock implementation."""

    def test_connect_disconnect(self):
        env = _MockEnvironment()
        assert not env._connected
        env.connect()
        assert env._connected
        env.disconnect()
        assert not env._connected

    def test_episode_lifecycle(self):
        env = _MockEnvironment()
        env.connect()

        obs = env.start_episode("test_env_001")
        assert obs.metadata["environment_id"] == "test_env_001"
        assert obs.action_count == 0

        action = Action(action_id="MOVE_UP")
        next_obs, terminated = env.step(action)
        assert next_obs.action_count == 1
        assert not terminated

        result = env.end_episode()
        assert result.total_actions == 1
        assert result.success is True

        env.disconnect()

    def test_episode_termination(self):
        env = _MockEnvironment()
        env.connect()
        env.start_episode("test_env")

        action = Action(action_id="MOVE_UP")
        for _ in range(4):
            _, terminated = env.step(action)
            assert not terminated

        _, terminated = env.step(action)
        assert terminated

    def test_abstract_methods_enforced(self):
        with pytest.raises(TypeError):
            BaseEnvironment()  # type: ignore[abstract]
