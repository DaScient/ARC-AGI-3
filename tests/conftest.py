"""Shared test fixtures and configuration for the ARC-AGI-3 test suite.

This module provides reusable fixtures that are automatically discovered by
Pytest and made available to all test files in the tests/ directory. Fixtures
include sample observations, mock environments, pre-configured agents, and
utility helpers for common test patterns.
"""

from __future__ import annotations

from typing import Any

import pytest

from arc_agi_3.agent.base import Action, Observation
from arc_agi_3.evaluation.scorer import Scorer


@pytest.fixture
def sample_grid() -> list[list[int]]:
    """A minimal 4x4 grid for testing observation processing."""
    return [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
        [12, 13, 14, 15],
    ]


@pytest.fixture
def sample_observation(sample_grid: list[list[int]]) -> Observation:
    """A complete sample observation with grid, actions, and metadata."""
    return Observation(
        grid=sample_grid,
        legal_actions=["MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT", "INTERACT"],
        level=1,
        action_count=0,
        metadata={"environment_id": "test_env_001"},
    )


@pytest.fixture
def sample_action() -> Action:
    """A sample action for testing action submission."""
    return Action(action_id="MOVE_UP")


@pytest.fixture
def sample_legal_actions() -> list[str]:
    """A standard set of legal action identifiers."""
    return ["MOVE_UP", "MOVE_DOWN", "MOVE_LEFT", "MOVE_RIGHT", "INTERACT", "RESET"]


@pytest.fixture
def scorer() -> Scorer:
    """A Scorer instance configured with the default multiplier."""
    return Scorer(human_baseline_multiplier=5.0)


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """A minimal configuration dictionary for testing."""
    return {
        "agent": {
            "exploration": {
                "curiosity_weight": 0.5,
                "exploration_decay": 0.95,
                "novelty_threshold": 0.1,
            },
            "policy": {
                "policy_type": "planning",
                "planning_horizon": 5,
                "planning_beam_width": 10,
            },
            "learning": {
                "learning_rate": 0.001,
                "memory_capacity": 1000,
                "batch_size": 32,
            },
        },
        "environment": {
            "api": {
                "endpoint_url": "https://api.arcprize.org/v3",
                "api_key": "",
                "timeout_seconds": 30,
                "max_retries": 3,
            },
            "local": {
                "use_local": True,
            },
        },
    }
