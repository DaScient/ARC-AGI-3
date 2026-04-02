"""Base agent interface and default implementation.

This module defines the abstract interface that all agent implementations must
satisfy, and provides a reference implementation that demonstrates the standard
observation-action loop, exploration-exploitation balancing, and internal state
management patterns.

The BaseAgent class is the extension point for custom agent policies. To introduce
a new policy, subclass BaseAgent and override the select_action method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    """A structured representation of a single environment frame.

    Attributes:
        grid: The current environment grid as a list of lists of integers.
            Each integer represents a cell value (color/state) in the range
            [0, color_depth).
        legal_actions: The set of action identifiers that are valid in the
            current state.
        level: The current level number within the episode.
        action_count: The cumulative number of actions taken so far in the episode.
        metadata: Additional frame metadata provided by the API.
    """

    grid: list[list[int]]
    legal_actions: list[str]
    level: int = 0
    action_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """A discrete action to be submitted to the environment.

    Attributes:
        action_id: The identifier of the action, corresponding to one of the
            legal action identifiers in the current observation.
    """

    action_id: str


class BaseAgent(ABC):
    """Abstract base class for all ARC-AGI-3 agent implementations.

    This class defines the interface contract that the orchestration loop
    depends on. Every agent — regardless of its internal policy, model
    architecture, or exploration strategy — must implement these methods.

    The interface is deliberately minimal: process an observation, select an
    action, manage state, and reset. All complexity lives in the implementations,
    not in the interface.
    """

    @abstractmethod
    def process_observation(self, observation: Observation) -> None:
        """Process a new observation from the environment.

        This method is called exactly once per turn, before select_action.
        Implementations should update internal state, encode the observation,
        compute novelty scores, and perform any other per-turn preprocessing.

        Args:
            observation: The current environment observation.
        """

    @abstractmethod
    def select_action(self, legal_actions: list[str]) -> Action:
        """Select an action from the set of legal actions.

        This method is called exactly once per turn, after process_observation.
        Implementations should apply their policy — whether reactive, planning,
        or hybrid — to choose the best action given the current internal state.

        Args:
            legal_actions: The identifiers of all actions that are valid in the
                current environment state.

        Returns:
            The selected action.
        """

    @abstractmethod
    def get_state(self) -> dict[str, Any]:
        """Serialize the agent's internal state for checkpointing.

        Returns:
            A dictionary containing all internal state needed to restore the
            agent to its current condition.
        """

    @abstractmethod
    def set_state(self, state: dict[str, Any]) -> None:
        """Restore the agent's internal state from a checkpoint.

        Args:
            state: A dictionary previously returned by get_state.
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset the agent to its initial state for a new episode.

        This method is called at the start of each episode. Implementations
        should clear all episode-specific state while preserving any
        configuration or learned parameters that persist across episodes.
        """
