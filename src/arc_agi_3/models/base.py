"""Base world model interface.

This module defines the abstract interface that all world model implementations
must satisfy. The interface covers state encoding, prediction, simulation,
goal inference, and uncertainty estimation.

The BaseWorldModel class is the extension point for custom model architectures.
Any new model — whether neural, symbolic, or hybrid — can be introduced by
implementing this interface and registering it through the configuration system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass
class GoalHypothesis:
    """A hypothesized goal for the current environment.

    Attributes:
        description: A human-readable description of the hypothesized goal.
        confidence: The model's confidence in this hypothesis, in [0, 1].
        evidence: Supporting evidence from observations.
    """

    description: str
    confidence: float
    evidence: list[str] = field(default_factory=list)


@dataclass
class Prediction:
    """A predicted future state with uncertainty.

    Attributes:
        state: The predicted state as a latent representation vector.
        uncertainty: The model's uncertainty about this prediction, in [0, 1].
    """

    state: NDArray[np.float64]
    uncertainty: float


class BaseWorldModel(ABC):
    """Abstract base class for all world model implementations.

    The world model is the agent's internal representation of environment
    dynamics. Given a state and an action, it predicts the next state. It
    also provides state encoding, goal inference, simulation, and uncertainty
    estimation capabilities.
    """

    @abstractmethod
    def encode(self, grid: list[list[int]]) -> NDArray[np.float64]:
        """Encode a raw grid observation into a latent representation.

        Args:
            grid: The environment grid as a list of lists of integers.

        Returns:
            A compact latent representation vector.
        """

    @abstractmethod
    def predict(
        self, state: NDArray[np.float64], action: str
    ) -> Prediction:
        """Predict the next state given a current state and action.

        Args:
            state: The current state as a latent representation.
            action: The action identifier to simulate.

        Returns:
            A prediction containing the predicted next state and uncertainty.
        """

    @abstractmethod
    def update(self, transitions: list[dict[str, Any]]) -> float:
        """Update the model from a batch of observed transitions.

        Args:
            transitions: A list of transition dictionaries, each containing
                'state', 'action', 'next_state', and optionally 'reward'.

        Returns:
            The training loss for this update step.
        """

    @abstractmethod
    def simulate(
        self, state: NDArray[np.float64], actions: list[str]
    ) -> list[Prediction]:
        """Simulate a sequence of actions from a starting state.

        Args:
            state: The starting state as a latent representation.
            actions: An ordered list of action identifiers to simulate.

        Returns:
            A list of predictions, one for each step of the simulation.
        """

    @abstractmethod
    def infer_goals(
        self, observation_history: list[dict[str, Any]]
    ) -> list[GoalHypothesis]:
        """Infer plausible goals from the agent's observation history.

        Args:
            observation_history: A chronological list of observation records.

        Returns:
            A ranked list of goal hypotheses with confidence scores.
        """
