"""Scoring engine for ARC-AGI-3 evaluation.

This module implements the Relative Human Action Efficiency (RHAE) scoring
metric used by the ARC-AGI-3 competition, along with supporting metrics
for development and analysis.

RHAE is computed as: min(1.0, (human_baseline / agent_actions) ** 2)

An agent that matches the human baseline receives a perfect 1.0.
An agent using twice the baseline receives 0.25.
An agent exceeding the configured multiplier threshold receives 0.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown for a single episode.

    Attributes:
        environment_id: The environment that was evaluated.
        rhae_score: The Relative Human Action Efficiency score in [0, 1].
        agent_actions: The total number of actions the agent took.
        human_baseline: The human baseline action count for this environment.
        levels_completed: The number of levels completed by the agent.
        per_level_scores: Individual RHAE scores for each level, if applicable.
    """

    environment_id: str
    rhae_score: float
    agent_actions: int
    human_baseline: int
    levels_completed: int
    per_level_scores: list[float] = field(default_factory=list)


class Scorer:
    """Computes Relative Human Action Efficiency and related metrics.

    The Scorer is configured with the maximum allowed action multiplier
    (the ratio of agent actions to human baseline beyond which the agent
    receives a zero score). By default, this multiplier is 5.0, matching
    the official ARC-AGI-3 competition rules.
    """

    def __init__(self, human_baseline_multiplier: float = 5.0) -> None:
        """Initialize the scorer.

        Args:
            human_baseline_multiplier: The maximum ratio of agent actions to
                human baseline before the episode receives a zero score.
                Must be >= 1.0.

        Raises:
            ValueError: If human_baseline_multiplier is less than 1.0.
        """
        if human_baseline_multiplier < 1.0:
            msg = f"human_baseline_multiplier must be >= 1.0, got {human_baseline_multiplier}"
            raise ValueError(msg)
        self._multiplier = human_baseline_multiplier

    def compute_rhae(self, agent_actions: int, human_baseline: int) -> float:
        """Compute the Relative Human Action Efficiency score.

        RHAE = min(1.0, (human_baseline / agent_actions) ** 2)

        If the agent uses more than human_baseline * multiplier actions,
        the score is 0.0. If agent_actions is zero (no actions taken), the
        score is 0.0.

        Args:
            agent_actions: The number of actions the agent took.
            human_baseline: The human baseline action count.

        Returns:
            The RHAE score in [0.0, 1.0].

        Raises:
            ValueError: If agent_actions is negative or human_baseline is
                not positive.
        """
        if agent_actions < 0:
            msg = f"agent_actions must be non-negative, got {agent_actions}"
            raise ValueError(msg)
        if human_baseline <= 0:
            msg = f"human_baseline must be positive, got {human_baseline}"
            raise ValueError(msg)

        if agent_actions == 0:
            return 0.0

        if agent_actions > human_baseline * self._multiplier:
            return 0.0

        ratio = human_baseline / agent_actions
        return min(1.0, ratio**2)

    def compute_episode_score(
        self,
        environment_id: str,
        agent_actions: int,
        human_baseline: int,
        levels_completed: int,
    ) -> ScoreBreakdown:
        """Compute a complete score breakdown for an episode.

        Args:
            environment_id: The environment identifier.
            agent_actions: Total actions taken by the agent.
            human_baseline: The human baseline action count.
            levels_completed: Number of levels the agent completed.

        Returns:
            A ScoreBreakdown with the computed RHAE score and metadata.
        """
        rhae = self.compute_rhae(agent_actions, human_baseline)
        return ScoreBreakdown(
            environment_id=environment_id,
            rhae_score=rhae,
            agent_actions=agent_actions,
            human_baseline=human_baseline,
            levels_completed=levels_completed,
        )
