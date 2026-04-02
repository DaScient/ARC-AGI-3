"""Tests for the utilities module.

These tests verify configuration loading, logging, and reproducibility
utilities.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from arc_agi_3.utils.config import load_config
from arc_agi_3.utils.logging import get_logger
from arc_agi_3.utils.reproducibility import load_checkpoint, save_checkpoint, seed_all


class TestConfigLoading:
    """Tests for configuration loading and merging."""

    def test_load_from_yaml_files(self, tmp_path):
        config_file = tmp_path / "test.yaml"
        config_file.write_text("agent:\n  exploration:\n    curiosity_weight: 0.7\n")

        config = load_config(config_paths=[str(config_file)])
        assert config["agent"]["exploration"]["curiosity_weight"] == 0.7

    def test_merge_multiple_files(self, tmp_path):
        file1 = tmp_path / "base.yaml"
        file1.write_text("agent:\n  policy:\n    policy_type: reactive\n")

        file2 = tmp_path / "override.yaml"
        file2.write_text("agent:\n  policy:\n    policy_type: planning\n")

        config = load_config(config_paths=[str(file1), str(file2)])
        assert config["agent"]["policy"]["policy_type"] == "planning"

    def test_override_with_dict(self, tmp_path):
        config_file = tmp_path / "test.yaml"
        config_file.write_text("agent:\n  learning:\n    learning_rate: 0.001\n")

        config = load_config(
            config_paths=[str(config_file)],
            overrides={"agent.learning.learning_rate": 0.01},
        )
        assert config["agent"]["learning"]["learning_rate"] == 0.01

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_config(config_paths=["/nonexistent/config.yaml"])

    def test_empty_config_paths(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config = load_config(config_paths=[])
        assert config == {}


class TestLogging:
    """Tests for the structured logging facility."""

    def test_get_logger_returns_logger(self):
        logger = get_logger("test_module")
        assert logger.name == "test_module"

    def test_logger_has_handler(self):
        logger = get_logger("test_handler_check")
        assert len(logger.handlers) > 0

    def test_logger_level_setting(self):
        logger = get_logger("test_level", level="DEBUG")
        import logging

        assert logger.level == logging.DEBUG


class TestReproducibility:
    """Tests for seeding, checkpointing, and restoration."""

    def test_seed_all_deterministic(self):
        seed_all(42)
        val1 = random.random()
        np_val1 = np.random.random()  # noqa: NPY002

        seed_all(42)
        val2 = random.random()
        np_val2 = np.random.random()  # noqa: NPY002

        assert val1 == val2
        assert np_val1 == np_val2

    def test_negative_seed_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            seed_all(-1)

    def test_checkpoint_save_and_load(self, tmp_path):
        state: dict[str, Any] = {
            "turn": 10,
            "score": 0.85,
            "config": {"learning_rate": 0.001},
        }
        path = str(tmp_path / "checkpoint.json")
        save_checkpoint(state, path)

        loaded = load_checkpoint(path)
        assert loaded["turn"] == 10
        assert loaded["score"] == 0.85
        assert loaded["config"]["learning_rate"] == 0.001

    def test_load_missing_checkpoint_raises(self):
        with pytest.raises(FileNotFoundError):
            load_checkpoint("/nonexistent/checkpoint.json")

    def test_checkpoint_creates_directories(self, tmp_path):
        nested_path = str(tmp_path / "a" / "b" / "c" / "checkpoint.json")
        save_checkpoint({"data": "test"}, nested_path)
        assert Path(nested_path).exists()
