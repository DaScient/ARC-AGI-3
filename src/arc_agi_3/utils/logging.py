"""Structured logging facility for the ARC-AGI-3 agent system.

This module provides a centralized logging factory that returns pre-configured
logger instances. All log output is structured, hierarchical, and configurable
at both the global and per-module level.

Usage:
    from arc_agi_3.utils import get_logger

    logger = get_logger(__name__)
    logger.info("Agent selected action", extra={"action": "MOVE_UP", "turn": 5})
"""

from __future__ import annotations

import logging
import sys


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Create or retrieve a configured logger instance.

    Returns a logger with a standard format that includes timestamps,
    module names, and severity levels. If the logger already has handlers
    (from a previous call), it is returned as-is to avoid duplicate output.

    Args:
        name: The name for the logger, typically __name__ of the calling module.
        level: The minimum severity level for log messages. Valid values are
            "DEBUG", "INFO", "WARNING", "ERROR", and "CRITICAL".

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
