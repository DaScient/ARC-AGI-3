"""Environment module: ARC-AGI-3 API interface and state management.

This module manages all interaction between the agent system and the ARC-AGI-3
benchmark. It provides API client management, frame parsing, action validation,
episode lifecycle management, and a local simulation mode for offline development.

For a complete prose description of every capability in this module, see
docs/FUNCTIONAL_CAPABILITIES.md under "Environment Module Capabilities."
"""

from arc_agi_3.environment.base import BaseEnvironment

__all__ = ["BaseEnvironment"]
