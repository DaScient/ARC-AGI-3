"""Reproducibility infrastructure for the ARC-AGI-3 agent system.

This module provides utilities for deterministic execution, including
random number generator seeding, state checkpointing, and run
configuration logging. These utilities ensure that any run can be
exactly reproduced given the same code, configuration, and seed.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import numpy as np


def seed_all(seed: int) -> None:
    """Seed all random number generators for reproducibility.

    This function seeds Python's built-in random module and NumPy's
    random number generator with the provided seed. If additional
    framework-specific generators (e.g., PyTorch, TensorFlow) are in
    use, they should be seeded separately or this function should be
    extended.

    Args:
        seed: The integer seed to use. Must be non-negative.

    Raises:
        ValueError: If seed is negative.
    """
    if seed < 0:
        msg = f"Seed must be non-negative, got {seed}"
        raise ValueError(msg)

    random.seed(seed)
    np.random.seed(seed)


def save_checkpoint(state: dict[str, Any], path: str) -> Path:
    """Save a system state checkpoint to disk as JSON.

    The checkpoint file contains the complete system state at a point in
    time, enabling exact restoration for replay or debugging.

    Args:
        state: The system state dictionary to checkpoint.
        path: The filesystem path where the checkpoint will be written.

    Returns:
        The Path object of the written checkpoint file.
    """
    checkpoint_path = Path(path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    with checkpoint_path.open("w") as f:
        json.dump(state, f, indent=2, default=str)

    return checkpoint_path


def load_checkpoint(path: str) -> dict[str, Any]:
    """Load a system state checkpoint from disk.

    Args:
        path: The filesystem path of the checkpoint file to load.

    Returns:
        The system state dictionary from the checkpoint.

    Raises:
        FileNotFoundError: If the checkpoint file does not exist.
    """
    checkpoint_path = Path(path)
    if not checkpoint_path.exists():
        msg = f"Checkpoint file not found: {path}"
        raise FileNotFoundError(msg)

    with checkpoint_path.open("r") as f:
        state: dict[str, Any] = json.load(f)

    return state
