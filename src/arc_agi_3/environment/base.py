"""Base environment interface and lifecycle management.

This module defines the abstract interface that all environment backends must
satisfy. The interface covers the complete episode lifecycle: connection
management, episode initialization, turn-by-turn interaction, and termination.

The BaseEnvironment class is the extension point for custom environment backends.
The default implementation connects to the ARC-AGI-3 API; alternative backends
(such as the local simulator) implement the same interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from arc_agi_3.agent.base import Action, Observation


@dataclass
class EpisodeResult:
    """The outcome of a completed episode.

    Attributes:
        environment_id: The unique identifier of the environment.
        levels_completed: The number of levels the agent completed.
        total_actions: The total number of actions the agent took.
        success: Whether the agent completed all levels successfully.
        metadata: Additional result metadata.
    """

    environment_id: str
    levels_completed: int
    total_actions: int
    success: bool
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseEnvironment(ABC):
    """Abstract base class for all ARC-AGI-3 environment backends.

    This class defines the interface contract that the orchestration loop
    depends on. Every environment backend — whether it connects to the remote
    API or runs a local simulator — must implement these methods.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection to the environment backend.

        For the remote API, this performs authentication and session setup.
        For the local simulator, this loads environment data from disk.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Gracefully close the connection to the environment backend."""

    @abstractmethod
    def start_episode(self, environment_id: str) -> Observation:
        """Initialize a new episode and return the first observation.

        Args:
            environment_id: The unique identifier of the environment to start.

        Returns:
            The initial observation for the episode.
        """

    @abstractmethod
    def step(self, action: Action) -> tuple[Observation, bool]:
        """Submit an action and receive the next observation.

        Args:
            action: The action to submit to the environment.

        Returns:
            A tuple of (next_observation, is_terminated). The boolean indicates
            whether the episode has ended.
        """

    @abstractmethod
    def end_episode(self) -> EpisodeResult:
        """Finalize the current episode and return its result.

        Returns:
            The complete result of the episode, including levels completed,
            total actions, and success status.
        """
