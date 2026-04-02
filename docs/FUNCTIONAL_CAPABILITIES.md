# Functional Capabilities

**Complete Inventory of Functional Capabilities for DaScient's ARC-AGI-3 Agent**

---

## Preface

This document provides an exhaustive, prose-format inventory of every functional capability in the ARC-AGI-3 agent system. A "functional capability" is defined as a discrete, identifiable unit of behavior that the system provides — something the system can do, expressed as a verb phrase. Each capability is described with its purpose, the module that implements it, its interface boundaries, its inputs and outputs, and its relationship to other capabilities. This inventory is organized by module and, within each module, by functional area.

---

## Agent Module Capabilities

The agent module is the decision-making core of the system. It transforms observations into actions. The following capabilities constitute the agent's complete behavioral repertoire.

### Capability: Receive and Process Observations

The agent receives structured observation objects from the environment module at every turn. Upon receipt, the agent transforms the raw observation into an internal representation suitable for downstream processing. This transformation may include encoding the grid state as a tensor, appending the observation to a sliding window of recent history, computing difference masks that highlight what changed between this observation and the previous one, and calculating novelty scores that quantify how different this observation is from anything the agent has previously encountered. This capability is the entry point for all agent computation within a turn and is invoked exactly once per turn.

**Interface.** The agent exposes a `process_observation` method that accepts an `Observation` object and returns nothing. The processed observation is stored in the agent's internal state and is available to all subsequent capabilities within the same turn.

### Capability: Select Actions

The agent selects an action from the set of legal actions provided in the current observation. The selection mechanism depends on the configured policy type. Under the planning policy, the agent uses the world model to simulate multiple action sequences forward in time, evaluates the expected outcome of each sequence, and selects the first action of the highest-scoring sequence. Under the reactive policy, the agent scores each legal action based on immediate features of the current observation — such as proximity to unexplored regions, alignment with inferred goals, or expected information gain — and selects the highest-scoring action. Under the hybrid policy, the agent uses reactive selection in the early turns of an episode and transitions to planning once the world model reaches sufficient confidence.

**Interface.** The agent exposes a `select_action` method that accepts the set of legal actions and returns a single `Action` object. This method must be called after `process_observation` within the same turn.

### Capability: Manage Internal State

The agent maintains a persistent internal state that evolves across turns within an episode. This state includes the history of observations and actions, the current world model parameters, the current curiosity weight (which decays over time), accumulated goal hypotheses, and any planning context carried over from the previous turn. The internal state is fully serializable, allowing it to be checkpointed to disk at any point and restored later for replay or analysis. At the start of each new episode, the internal state is reset to a clean initial condition.

**Interface.** The agent exposes `get_state` and `set_state` methods for serialization and deserialization, and a `reset` method that restores the initial state. These methods are used by the checkpointing and replay utilities.

### Capability: Balance Exploration and Exploitation

The agent dynamically adjusts its behavior between exploration and exploitation over the course of an episode. In early turns, when the agent knows little about the environment, it favors exploratory actions — actions that are expected to reveal new information about the environment's dynamics, objectives, or structure. As the episode progresses and the agent's world model improves, it progressively shifts toward exploitative actions — actions that it believes will advance it toward the inferred goal as efficiently as possible. The balance is controlled by the curiosity weight parameter and its decay schedule, both of which are configurable.

**Interface.** This capability is embedded in the `select_action` method and is not exposed as a separate interface. Its behavior is controlled through the `agent.exploration` configuration section.

### Capability: Adapt Policy During Episode

The agent is capable of modifying its action-selection behavior during an episode based on accumulated experience. If the agent encounters a pattern of observations that contradicts its current world model, it triggers an accelerated model update and may increase its exploration weight temporarily. If the agent detects that it has been repeating a cycle of actions without making progress, it applies a diversification strategy that biases action selection away from recently taken actions. These adaptive behaviors ensure that the agent does not become trapped in unproductive loops.

**Interface.** Adaptation logic is internal to the agent module and operates automatically. It does not require external invocation.

---

## Environment Module Capabilities

The environment module manages all interaction between the agent system and the ARC-AGI-3 benchmark. It is the system's sole point of contact with the external world during an episode.

### Capability: Establish and Manage API Connections

The environment module establishes authenticated connections to the ARC-AGI-3 API at the start of a session. It manages the connection lifecycle, including authentication token refresh, connection keepalive, and graceful disconnection at the end of a session. All connection parameters — endpoint URL, API key, timeout, and retry policy — are sourced from the environment configuration. The module implements retry logic with exponential backoff for transient failures, ensuring that brief network interruptions do not terminate an evaluation run.

**Interface.** The module exposes `connect` and `disconnect` methods for session lifecycle management. Connection state is managed internally and is not directly accessible to other modules.

### Capability: Parse Frames into Observations

Each turn, the ARC-AGI-3 API delivers a frame — a structured data object containing the current grid state as an array of integers, the list of legal action identifiers, and metadata including the current level number, the cumulative action count, and the episode status. The environment module parses this raw frame into a typed `Observation` object with named fields, validated data types, and semantic annotations. This parsing insulates the rest of the system from changes to the API's wire format.

**Interface.** The module exposes a `get_observation` method that returns the current `Observation`. This method is called by the orchestration loop at the start of each turn.

### Capability: Validate and Submit Actions

Before any action is sent to the API, the environment module validates it against the current set of legal actions. If the action is not in the legal set, the module raises an error immediately rather than wasting a turn on an illegal submission. If the action is valid, the module serializes it into the API's expected format and submits it. The module then waits for the API's response, which includes the next frame and any episode-termination signals.

**Interface.** The module exposes a `submit_action` method that accepts an `Action` object and returns the resulting `Observation`. If the episode has terminated, the return value includes a termination flag and a final status.

### Capability: Manage Episode Lifecycle

The environment module manages the complete lifecycle of an episode: initialization, turn-by-turn interaction, and termination. At initialization, it requests a new episode from the API and receives the initial frame. During the episode, it alternates between providing observations and accepting actions. At termination — whether due to successful completion, action budget exhaustion, or an error — it records the final state, emits lifecycle events, and cleanly closes the episode.

**Interface.** The module exposes `start_episode`, `step`, and `end_episode` methods that compose into a standard episode loop. The `step` method combines `get_observation` and `submit_action` into a single turn.

### Capability: Operate in Local Simulation Mode

For development and testing, the environment module can operate against a local environment simulator instead of the remote API. The local simulator reads environment definitions from JSON files on disk and emulates the observation-action loop with deterministic behavior. This capability allows developers to iterate on agent logic without network connectivity and without consuming API quota.

**Interface.** Local simulation mode is activated by setting `environment.local.use_local` to `true` in the configuration. The rest of the system interacts with the environment module through the same interface regardless of the backend.

---

## Models Module Capabilities

The models module provides the agent's capacity to understand, predict, and reason about the environments it encounters.

### Capability: Maintain and Update World Model

The world model is a learned function that predicts the next environment state given the current state and a proposed action. The models module trains this function from the agent's stream of observations and actions, updating it incrementally after each turn using gradient-based learning on a mini-batch sampled from the agent's episodic memory. The world model is the foundation of the agent's planning capability: accurate predictions enable the agent to evaluate action sequences without physically executing them.

**Interface.** The module exposes an `update` method that accepts a batch of transitions and updates the model parameters, and a `predict` method that accepts a state and an action and returns a predicted next state.

### Capability: Encode State Representations

Raw grid observations are high-dimensional (64×64 cells, each taking one of 16 values). The models module compresses these into compact latent representations that capture the essential structure of the environment — object identities and positions, spatial relationships, symmetry patterns, and dynamic elements. These compressed representations are what the agent's policy and planning algorithms operate on, ensuring that computation scales with the complexity of the environment's structure rather than with the raw grid size.

**Interface.** The module exposes an `encode` method that accepts a raw grid observation and returns a latent representation vector.

### Capability: Infer Goals

ARC-AGI-3 environments do not provide explicit goals. The agent must infer what it is supposed to accomplish from indirect evidence: changes in the environment state, patterns in level transitions, and the implicit reward signal of advancing to higher levels. The models module maintains a distribution over candidate goal hypotheses, updates this distribution based on new evidence, and provides the agent with a ranked list of plausible goals. Goal hypotheses may include spatial targets (reach a specific location), state targets (achieve a specific grid configuration), or behavioral targets (trigger a specific sequence of environmental responses).

**Interface.** The module exposes an `infer_goals` method that returns a ranked list of `GoalHypothesis` objects, each with a confidence score and a description of the hypothesized objective.

### Capability: Simulate Future States

Using the world model, the models module can simulate the consequences of an action sequence starting from the current state. This simulation capability is the engine behind the agent's planning policy: the agent proposes candidate action sequences, the models module simulates each one, and the agent evaluates the simulated outcomes to select the best plan. Simulation is performed in the compressed latent space for efficiency and decoded back to grid space only when needed for visualization or debugging.

**Interface.** The module exposes a `simulate` method that accepts a starting state and a sequence of actions and returns a sequence of predicted future states.

### Capability: Estimate Prediction Uncertainty

Not all predictions are equally reliable. The models module provides uncertainty estimates alongside its predictions, quantifying how confident the world model is about each predicted state. These uncertainty estimates serve two purposes: they inform the agent's exploration strategy (states with high uncertainty are prime targets for exploration), and they regulate the transition from reactive to planning-based action selection in the hybrid policy (the agent switches to planning only when the world model's uncertainty falls below a threshold).

**Interface.** The module's `predict` and `simulate` methods return uncertainty estimates alongside their primary outputs.

---

## Evaluation Module Capabilities

The evaluation module measures the agent's performance and produces actionable reports.

### Capability: Compute Efficiency Scores

The evaluation module computes the primary performance metric — Relative Human Action Efficiency (RHAE) — for every episode. RHAE is calculated as the square of the ratio of the human baseline action count to the agent's actual action count, capped at 1.0. An agent that matches the human baseline exactly receives a perfect score of 1.0. An agent that uses twice the human baseline receives 0.25. An agent that uses more than five times the baseline receives 0.0. The module also computes per-level scores for multi-level environments and aggregates them according to the official weighting scheme.

**Interface.** The module exposes a `compute_score` method that accepts episode metadata (action counts, levels completed, human baselines) and returns a detailed score breakdown.

### Capability: Track and Aggregate Metrics

Beyond the primary score, the evaluation module tracks a comprehensive set of secondary metrics across episodes and evaluation runs. These include total actions taken, actions per level, levels completed, exploration-to-exploitation ratio (derived from the agent's curiosity weight trajectory), goal-inference accuracy (when ground truth is available in development environments), wall-clock time per episode, and model update frequency. All metrics are stored in a structured format and can be queried programmatically or exported for external analysis.

**Interface.** The module exposes a `record_metric` method for individual data points and a `get_metrics` method for querying accumulated results.

### Capability: Generate Reports

The evaluation module produces detailed reports in JSON, CSV, and human-readable text formats. Reports include per-environment performance breakdowns, aggregate summaries, trend analyses comparing the current run to historical baselines, and configuration snapshots that record the exact parameters used for the run. Reports are written to the configured output directory and timestamped for archival.

**Interface.** The module exposes a `generate_report` method that accepts a format specifier and writes the report to disk. It returns the file path of the generated report.

### Capability: Detect Performance Regressions

When regression detection is enabled, the evaluation module compares current results against stored historical baselines. If the primary metric has decreased by more than the configured threshold relative to the most recent baseline, the module emits a regression alert with details about which environments degraded, by how much, and what configuration changes (if any) were recorded between the baseline and the current run. This capability is essential for maintaining forward progress during iterative development.

**Interface.** The module exposes a `check_regressions` method that accepts current results and returns a list of `RegressionAlert` objects, each describing a detected regression.

---

## Utilities Module Capabilities

The utilities module provides shared infrastructure that all other modules depend on.

### Capability: Structured Logging

The logging facility provides hierarchical, structured log output to the console and to log files. Every log entry includes a timestamp, the emitting module's name, the severity level, and a structured payload. Log entries can be filtered by module, by severity, or by custom tags. The logging facility is configured through the evaluation configuration and is initialized once at system startup.

**Interface.** The module exposes a `get_logger` factory function that returns a configured logger instance for the requesting module.

### Capability: Load and Validate Configuration

The configuration loader reads YAML files from the `config/` directory, merges them with environment variable overrides and command-line overrides, validates the result against a schema that specifies types, ranges, and required fields, and returns a typed configuration object. If validation fails, the loader raises a descriptive error that identifies the invalid parameter, its provided value, and the constraint that was violated.

**Interface.** The module exposes a `load_config` function that accepts optional override paths and returns a `Config` object.

### Capability: Seed Random Number Generators

At the start of every run, the reproducibility infrastructure seeds all random number generators — Python's built-in `random`, NumPy's generator, and any framework-specific generators — with a deterministic seed derived from the run configuration. This ensures that any run can be exactly reproduced given the same code and configuration.

**Interface.** The module exposes a `seed_all` function that accepts an integer seed and configures all generators.

### Capability: Checkpoint and Restore System State

The checkpointing service serializes the complete system state — agent internal state, world model parameters, episode metadata, and configuration — to disk at configurable intervals. A checkpointed state can be restored to resume a run from the exact point where the checkpoint was taken, or to replay the agent's behavior for debugging or analysis.

**Interface.** The module exposes `save_checkpoint` and `load_checkpoint` functions that write to and read from the configured checkpoint directory.

### Capability: Transform Data Between Representations

Common data transformations are centralized in the utilities module to avoid duplication. These include grid encoding (converting a two-dimensional integer array into a tensor), grid decoding (the reverse), action-space enumeration (constructing the set of possible actions from a specification), observation normalization (scaling observation values to a standard range), and batch construction (assembling individual transitions into batched tensors for model training).

**Interface.** The module exposes individual transformation functions (`encode_grid`, `decode_grid`, `enumerate_actions`, `normalize_observation`, `build_batch`) that other modules call as needed.

---

## Cross-Cutting Capabilities

Several capabilities span multiple modules and represent emergent system-level behaviors.

### Capability: Execute a Complete Episode

The system orchestrates a complete episode by coordinating the environment, agent, models, and evaluation modules in a turn-by-turn loop. The orchestration logic — implemented as a top-level run function — initializes the episode, enters the observation-action loop, records metrics at each turn, handles termination conditions, and produces a final evaluation report. This capability is the primary entry point for both development runs and competition submissions.

### Capability: Reproduce Any Run

By combining deterministic seeding, configuration logging, checkpointing, and structured action logs, the system can reproduce any previously executed run. Given a configuration file and a seed, the system will produce the same sequence of actions, the same model updates, and the same evaluation results as the original run. This capability is critical for debugging, for comparing agent versions, and for satisfying the open-source transparency requirements of the ARC Prize competition.

### Capability: Extend the System with Custom Components

Every module boundary in the system is defined by an interface that custom implementations can satisfy. A researcher can introduce a new policy, a new world model architecture, a new evaluation metric, or a new environment adapter by implementing the corresponding interface and registering it through the configuration system. This extensibility is documented at each interface point in the source code and summarized in this document.

---

## Summary

This inventory covers every functional capability of the ARC-AGI-3 agent system: thirty distinct capabilities spanning five modules and three cross-cutting concerns. Each capability has a clearly defined purpose, a well-specified interface, and a documented relationship to the rest of the system. This completeness is intentional — for a system that aspires to transparent, reproducible, and competitive performance on the most challenging AI benchmark in existence, nothing less is acceptable.
