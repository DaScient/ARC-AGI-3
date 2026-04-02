"""Evaluation module: Scoring, metrics, and performance analysis.

This module measures, records, and reports on the agent's performance. It
computes efficiency scores, tracks per-environment and aggregate metrics,
generates detailed reports, and detects performance regressions.

For a complete prose description of every capability in this module, see
docs/FUNCTIONAL_CAPABILITIES.md under "Evaluation Module Capabilities."
"""

from arc_agi_3.evaluation.scorer import Scorer

__all__ = ["Scorer"]
