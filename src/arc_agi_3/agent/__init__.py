"""Agent module: Decision-making and action-selection logic.

This module contains the agent's core decision-making components, including
observation processing, policy execution, exploration-exploitation balancing,
internal state management, and adaptive behavior. The agent receives observations
from the environment module, maintains and updates its internal state, and produces
actions according to its configured policy.

For a complete prose description of every capability in this module, see
docs/FUNCTIONAL_CAPABILITIES.md under "Agent Module Capabilities."
"""

from arc_agi_3.agent.base import BaseAgent

__all__ = ["BaseAgent"]
