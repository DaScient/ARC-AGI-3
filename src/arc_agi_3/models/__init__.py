"""Models module: World models, representation learning, and inference.

This module provides the agent's representational and inferential capabilities,
including world model maintenance, state encoding, goal inference, future state
simulation, and prediction uncertainty estimation.

For a complete prose description of every capability in this module, see
docs/FUNCTIONAL_CAPABILITIES.md under "Models Module Capabilities."
"""

from arc_agi_3.models.base import BaseWorldModel

__all__ = ["BaseWorldModel"]
