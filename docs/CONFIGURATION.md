# Configuration Reference

**Complete Annotated Configuration Guide for DaScient's ARC-AGI-3 Agent**

---

## Preface

This document provides a comprehensive reference for every configurable parameter in the ARC-AGI-3 agent system. Each parameter is documented with its purpose, its default value, its valid range or set of acceptable values, and a prose explanation of what happens when it is changed. Configuration files are stored in the `config/` directory in YAML format. Every parameter can be overridden at runtime through environment variables or command-line arguments, with environment variables taking precedence over file-based values and command-line arguments taking precedence over both.

---

## Configuration Architecture

The configuration system is structured as a three-layer hierarchy:

**File-based defaults.** The YAML files in `config/` establish the baseline configuration for the system. These files are version-controlled and represent the project's standard operating parameters.

**Environment variable overrides.** Any configuration parameter can be overridden by setting an environment variable whose name is derived from the parameter's path in the YAML hierarchy. The derivation rule is: convert the YAML path to uppercase, replace dots with double underscores, and prefix with `ARC_`. For example, the parameter `agent.exploration.curiosity_weight` can be overridden by setting the environment variable `ARC__AGENT__EXPLORATION__CURIOSITY_WEIGHT`. This mechanism allows sensitive values (such as API keys) to be supplied without committing them to version control, and it allows ephemeral overrides during experimentation.

**Command-line argument overrides.** When invoking the agent from the command line, any parameter can be overridden using the `--config` flag with dot-notation paths. For example: `--config agent.exploration.curiosity_weight=0.8`. Command-line overrides take the highest precedence and are primarily used for one-off experiments.

At startup, the configuration loader reads the YAML files, applies environment variable overrides, applies command-line overrides, validates the merged result against the configuration schema, and exposes the final configuration as a typed, immutable object. If validation fails — because a value is out of range, of the wrong type, or missing — the system logs a detailed error message and refuses to start.

---

## Agent Configuration (`config/agent.yaml`)

The agent configuration file controls all aspects of the agent's behavior, from exploration strategy to action-selection policy to learning dynamics.

### Section: `agent.exploration`

These parameters govern how the agent balances exploration (discovering how the environment works) with exploitation (acting on what it has already learned).

**`curiosity_weight`**
- **Type:** Float
- **Default:** `0.5`
- **Valid range:** `0.0` to `1.0`
- **Description:** Controls the relative importance of curiosity-driven exploration bonuses in the agent's action-selection process. A value of zero means the agent relies entirely on its current policy without any exploration incentive. A value of one means the agent prioritizes novel actions and unexplored states above all else. In practice, values between 0.3 and 0.7 produce the best balance between discovering environment dynamics early in an episode and converging to efficient goal-directed behavior later. This parameter has a significant impact on the agent's action efficiency: too much exploration wastes actions, while too little exploration causes the agent to miss critical environmental dynamics.

**`exploration_decay`**
- **Type:** Float
- **Default:** `0.95`
- **Valid range:** `0.0` to `1.0`
- **Description:** The multiplicative decay factor applied to the curiosity weight after each turn. This parameter controls how quickly the agent transitions from exploratory behavior to exploitative behavior within an episode. A value of 1.0 means the curiosity weight never decays, maintaining a constant exploration pressure. A value of 0.9 means the curiosity weight halves roughly every seven turns. The default of 0.95 provides a gradual transition that allows the agent to explore thoroughly in the first several dozen turns before focusing on goal-directed action.

**`novelty_threshold`**
- **Type:** Float
- **Default:** `0.1`
- **Valid range:** `0.0` to `1.0`
- **Description:** The minimum novelty score an observation must have to trigger an exploration bonus. Observations with novelty scores below this threshold are considered "familiar" and do not receive additional exploration weight. Raising this threshold makes the agent more selective about what counts as novel, potentially reducing wasted exploration of minor state variations. Lowering it makes the agent more sensitive to small changes, which can be beneficial in environments with subtle dynamics.

### Section: `agent.policy`

These parameters configure the agent's action-selection policy.

**`policy_type`**
- **Type:** String
- **Default:** `"planning"`
- **Valid values:** `"planning"`, `"reactive"`, `"hybrid"`
- **Description:** Selects the type of policy the agent uses to choose actions. The `"planning"` policy uses the world model to simulate action sequences and selects the sequence with the highest expected return. The `"reactive"` policy selects actions based on immediate observations without forward simulation. The `"hybrid"` policy uses reactive action selection for the first few turns of an episode (while the world model has insufficient data) and transitions to planning once the world model reaches a configurable confidence threshold.

**`planning_horizon`**
- **Type:** Integer
- **Default:** `5`
- **Valid range:** `1` to `50`
- **Description:** The number of future turns the planning policy simulates when evaluating action sequences. A longer planning horizon allows the agent to consider more distant consequences but increases computation time per turn. This parameter has no effect when the policy type is set to `"reactive"`.

**`planning_beam_width`**
- **Type:** Integer
- **Default:** `10`
- **Valid range:** `1` to `100`
- **Description:** The number of candidate action sequences maintained during beam-search planning. A wider beam increases the diversity of plans considered but increases computation. In practice, beam widths of 5 to 20 produce good results for most environments.

### Section: `agent.learning`

These parameters control how the agent updates its internal models and policies during an episode.

**`learning_rate`**
- **Type:** Float
- **Default:** `0.001`
- **Valid range:** `0.0` to `1.0`
- **Description:** The step size used when updating the world model's parameters in response to new observations. Higher learning rates cause faster adaptation but risk instability. Lower learning rates produce more stable updates but may cause the agent to adapt too slowly to novel environments.

**`memory_capacity`**
- **Type:** Integer
- **Default:** `1000`
- **Valid range:** `100` to `100000`
- **Description:** The maximum number of observation-action-outcome transitions stored in the agent's episodic memory. When the memory is full, the oldest transitions are discarded. This parameter bounds the agent's memory consumption and influences how much historical context the world model can draw upon.

**`batch_size`**
- **Type:** Integer
- **Default:** `32`
- **Valid range:** `1` to `512`
- **Description:** The number of transitions sampled from episodic memory for each world model update. Larger batches provide more stable gradient estimates but increase computation per update step.

---

## Environment Configuration (`config/environment.yaml`)

The environment configuration file controls all aspects of the system's interaction with the ARC-AGI-3 benchmark API and local environment simulators.

### Section: `environment.api`

These parameters govern the connection to the ARC-AGI-3 API.

**`endpoint_url`**
- **Type:** String
- **Default:** `"https://api.arcprize.org/v3"`
- **Description:** The base URL of the ARC-AGI-3 API endpoint. During development, this can be pointed at a local mock server. During competition evaluation, this is set to the official endpoint by the evaluation harness. This value should not normally be changed in production.

**`api_key`**
- **Type:** String
- **Default:** `""` (empty — must be provided via environment variable)
- **Description:** The authentication key for the ARC-AGI-3 API. This value must never be committed to version control. It should always be provided through the `ARC__ENVIRONMENT__API__API_KEY` environment variable or through the `.env` file. The API key is required for all remote environment interactions.

**`timeout_seconds`**
- **Type:** Integer
- **Default:** `30`
- **Valid range:** `5` to `300`
- **Description:** The maximum time, in seconds, that the system will wait for a response from the API before treating the request as failed. Longer timeouts accommodate slow network conditions but delay failure detection. The default of 30 seconds is suitable for most network environments.

**`max_retries`**
- **Type:** Integer
- **Default:** `3`
- **Valid range:** `0` to `10`
- **Description:** The maximum number of times a failed API request will be retried before the system raises an error. Retries use exponential backoff to avoid overwhelming the API during transient outages. Setting this to zero disables retries entirely.

**`retry_backoff_factor`**
- **Type:** Float
- **Default:** `1.5`
- **Valid range:** `1.0` to `5.0`
- **Description:** The multiplicative factor applied to the wait time between successive retries. With the default factor of 1.5, the wait times between retries are approximately 1.5 seconds, 2.25 seconds, and 3.375 seconds for three retries.

### Section: `environment.local`

These parameters configure local environment simulation for development and testing.

**`use_local`**
- **Type:** Boolean
- **Default:** `false`
- **Description:** When set to true, the system uses a local environment simulator instead of connecting to the remote API. This is useful for offline development and automated testing. The local simulator provides a deterministic, lightweight approximation of the ARC-AGI-3 environment format.

**`local_data_path`**
- **Type:** String
- **Default:** `"data/sample_environments/"`
- **Description:** The filesystem path to the directory containing local environment data files. Each file describes a single environment in JSON format compatible with the ARC-AGI-3 specification.

### Section: `environment.frame`

These parameters control how raw frames from the API are processed into observations.

**`grid_size`**
- **Type:** Integer
- **Default:** `64`
- **Valid range:** `1` to `256`
- **Description:** The expected width and height of the environment grid, in cells. The ARC-AGI-3 specification uses 64x64 grids. Changing this value is only appropriate when working with custom environments that use a different grid resolution.

**`color_depth`**
- **Type:** Integer
- **Default:** `16`
- **Valid range:** `2` to `256`
- **Description:** The number of distinct cell values (colors or states) that the grid can represent. The ARC-AGI-3 specification uses values 0 through 15, giving a color depth of 16.

---

## Evaluation Configuration (`config/evaluation.yaml`)

The evaluation configuration file controls scoring, metrics collection, reporting, and regression detection.

### Section: `evaluation.scoring`

These parameters define how the agent's performance is scored.

**`efficiency_metric`**
- **Type:** String
- **Default:** `"rhae"`
- **Valid values:** `"rhae"`, `"raw_actions"`, `"levels_completed"`
- **Description:** The primary metric used for scoring. The `"rhae"` (Relative Human Action Efficiency) metric computes the squared ratio of the human baseline action count to the agent's action count, capped at 1.0. The `"raw_actions"` metric simply reports the total number of actions taken. The `"levels_completed"` metric counts the number of levels the agent successfully completed. The `"rhae"` metric is the official ARC-AGI-3 competition metric and should be used for all competition-oriented evaluation.

**`human_baseline_multiplier`**
- **Type:** Float
- **Default:** `5.0`
- **Valid range:** `1.0` to `20.0`
- **Description:** The maximum ratio of agent actions to human baseline actions before the episode is terminated with a zero score. With the default of 5.0, an agent that uses more than five times the human baseline number of actions receives zero credit for that episode. This parameter mirrors the official ARC-AGI-3 cutoff rule.

### Section: `evaluation.logging`

These parameters control the verbosity and format of evaluation logging.

**`log_level`**
- **Type:** String
- **Default:** `"INFO"`
- **Valid values:** `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`
- **Description:** The minimum severity level for log messages emitted by the evaluation module. Setting this to `"DEBUG"` produces the most detailed output, including per-turn scoring breakdowns. Setting it to `"ERROR"` suppresses all output except error conditions.

**`output_format`**
- **Type:** String
- **Default:** `"json"`
- **Valid values:** `"json"`, `"csv"`, `"text"`
- **Description:** The format used for evaluation report files. JSON is the default because it preserves the full structure of evaluation results and is easily consumed by downstream analysis tools. CSV is useful for import into spreadsheet applications. Text produces a human-readable summary.

**`output_directory`**
- **Type:** String
- **Default:** `"outputs/evaluation/"`
- **Description:** The filesystem path where evaluation reports are written. This directory is created automatically if it does not exist.

### Section: `evaluation.regression`

These parameters control the regression detection system.

**`enable_regression_detection`**
- **Type:** Boolean
- **Default:** `true`
- **Description:** When enabled, the evaluation module compares current results against historical baselines and flags any statistically significant performance regressions.

**`regression_threshold`**
- **Type:** Float
- **Default:** `0.05`
- **Valid range:** `0.01` to `0.5`
- **Description:** The minimum relative performance decrease (as a fraction) that triggers a regression alert. With the default of 0.05, a five-percent decrease in the primary metric compared to the historical baseline is flagged as a regression.

**`baseline_directory`**
- **Type:** String
- **Default:** `"outputs/baselines/"`
- **Description:** The filesystem path where historical baseline results are stored for regression comparison. Baselines are stored as JSON files, one per evaluation run.

---

## Environment Variable Reference

The following table summarizes the most commonly used environment variables and their corresponding YAML paths:

| Environment Variable | YAML Path | Description |
|---|---|---|
| `ARC__ENVIRONMENT__API__API_KEY` | `environment.api.api_key` | ARC-AGI-3 API authentication key |
| `ARC__ENVIRONMENT__API__ENDPOINT_URL` | `environment.api.endpoint_url` | API endpoint URL |
| `ARC__AGENT__EXPLORATION__CURIOSITY_WEIGHT` | `agent.exploration.curiosity_weight` | Exploration-exploitation balance |
| `ARC__AGENT__POLICY__POLICY_TYPE` | `agent.policy.policy_type` | Action-selection policy type |
| `ARC__EVALUATION__LOGGING__LOG_LEVEL` | `evaluation.logging.log_level` | Evaluation log verbosity |

---

## Summary

Every configurable parameter in the system is documented in this reference. The three-layer configuration hierarchy — file defaults, environment variable overrides, and command-line overrides — provides flexibility without sacrificing traceability. All defaults are chosen to provide reasonable behavior out of the box, and all valid ranges are enforced at startup through schema validation. When in doubt, start with the defaults and adjust incrementally based on evaluation results.
