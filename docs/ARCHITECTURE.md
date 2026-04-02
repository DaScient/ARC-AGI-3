# Architecture

**System Architecture and Design Principles for DaScient's ARC-AGI-3 Agent**

---

## Preface

This document describes the architectural design of the ARC-AGI-3 agent system in its entirety. It is written in full prose to ensure that every design decision, module boundary, data flow, and interaction pattern is transparent and accessible to any reader — whether they are a contributing developer, a competition reviewer, or a researcher studying the approach. No architectural detail is left implicit; every choice is stated, explained, and justified.

---

## Guiding Design Principles

The architecture of this system rests on five foundational principles. Each principle is not merely aspirational — it directly shapes module boundaries, interface contracts, and implementation constraints.

### Separation of Concerns

Every module in the system has a single, clearly defined responsibility. The agent module is responsible for decision-making and nothing else. The environment module is responsible for interfacing with the ARC-AGI-3 benchmark and nothing else. The models module is responsible for representation learning and inference and nothing else. The evaluation module is responsible for measurement and reporting and nothing else. The utilities module provides shared infrastructure that is agnostic to any specific domain concern. This strict separation ensures that changes to one module do not propagate unintended effects to others, that each module can be tested in isolation, and that the system can evolve without accumulating entangled dependencies.

### Transparency by Default

Every component of this system is designed to be fully inspectable. All configurations are stored in human-readable YAML files with annotations. All logging is structured and hierarchical, allowing any user to trace the exact sequence of observations, decisions, and actions that the agent took during any episode. All model states are serializable and checkpointable, so that any point in a training or evaluation run can be reproduced or audited. This principle exists because the ARC Prize competition values open-source rigor and because opaque systems are fundamentally more difficult to debug, improve, and trust.

### Modularity and Extensibility

The system is structured so that any module can be replaced, extended, or composed with alternative implementations without requiring changes to the rest of the system. This is achieved through well-defined interfaces at each module boundary. The agent module exposes a standard action-selection interface. The environment module exposes a standard observation-and-action interface. The models module exposes a standard prediction-and-update interface. Any new strategy, model architecture, or evaluation metric can be introduced by implementing the corresponding interface and registering it with the configuration system. This modularity is essential because research on ARC-AGI-3 is inherently experimental — the optimal approach is not known in advance, and the system must accommodate rapid iteration.

### Efficiency Consciousness

The ARC-AGI-3 benchmark scores agents on their action efficiency relative to a human baseline. An agent that solves an environment but uses three times as many actions as a human receives less than twelve percent of the maximum score. An agent that uses more than five times the human baseline receives zero. This scoring regime means that every architectural decision must account for computational and action efficiency. The agent's planning and decision-making pipelines are designed to minimize unnecessary exploration, the world model is designed to generalize from minimal observations, and the evaluation system is designed to surface efficiency regressions immediately.

### Reproducibility

Every run of this system — whether for development, evaluation, or competition submission — must be fully reproducible. This means that all sources of randomness are explicitly seeded, all configurations are versioned and logged alongside results, all model checkpoints are stored with their training context, and all environment interactions are recorded in a replay-compatible format. Reproducibility is not a convenience feature; it is a prerequisite for credible research and fair competition.

---

## System Overview

The system is organized as a layered architecture with five principal modules arranged in three tiers. The bottom tier contains the environment interface. The middle tier contains the world models and the agent's decision-making logic. The top tier contains the evaluation and reporting subsystem. Shared utilities cut across all tiers as a vertical service layer.

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Evaluation and Reporting                       │
│         (Scoring, Metrics, Performance Analysis, Reporting)          │
├──────────────────────────────────────────────────────────────────────┤
│              Agent Decision-Making          │    World Models        │
│   (Policy, Planning, Action Selection)      │ (State Repr, Predict) │
├──────────────────────────────────────────────────────────────────────┤
│                     Environment Interface                            │
│       (API Client, Frame Parsing, Action Validation, Lifecycle)      │
├──────────────────────────────────────────────────────────────────────┤
│                     Shared Utilities                                 │
│     (Logging, Config, Seeding, Checkpointing, Data Transforms)       │
└──────────────────────────────────────────────────────────────────────┘
```

Data flows upward from the environment through the agent and models to the evaluation layer. Control flows downward from the evaluation layer (which orchestrates episodes and runs) through the agent (which selects actions) to the environment (which executes them). The utilities layer provides services horizontally to all other layers.

---

## Module Descriptions

### Environment Module (`src/arc_agi_3/environment/`)

The environment module serves as the exclusive gateway between the agent system and the ARC-AGI-3 benchmark. Its responsibilities are:

**API Client Management.** The module establishes, maintains, and gracefully terminates connections to the ARC-AGI-3 API. It handles authentication using the API key provided through the environment configuration, manages session tokens, and implements retry logic with exponential backoff for transient network failures. All connection parameters — including endpoint URLs, timeout durations, and retry limits — are configurable through `config/environment.yaml`.

**Frame Parsing and Observation Construction.** Each turn of an ARC-AGI-3 environment produces a frame — a structured data object containing the current grid state, the list of legal actions, and metadata such as the current level number and cumulative action count. The environment module parses these raw frames into typed observation objects that the rest of the system can consume without knowing anything about the API's wire format. This parsing layer serves as an insulation boundary: if the API format changes, only this module needs to be updated.

**Action Validation.** Before submitting any action to the API, the environment module validates it against the current set of legal actions. This prevents the agent from wasting a turn on an illegal action and provides an early diagnostic signal if the agent's internal state has become inconsistent with the environment's actual state.

**Episode Lifecycle Management.** The module manages the complete lifecycle of an episode, from initialization through turn-by-turn interaction to termination. It tracks episode-level metadata — the environment identifier, the number of levels completed, the total action count — and emits structured lifecycle events that the evaluation module consumes.

### Agent Module (`src/arc_agi_3/agent/`)

The agent module contains the system's core decision-making logic. It is the component that receives observations and produces actions. Its responsibilities are:

**Observation Processing.** When the agent receives an observation from the environment, it first processes the raw observation into a form suitable for its internal computations. This may involve encoding the grid state into a latent representation, updating a history buffer of recent observations, or computing derived features such as novelty scores or change masks.

**Policy Execution.** The agent maintains a policy — a function from observations (and internal state) to actions. The policy may be a learned neural network, a planning algorithm, a heuristic rule system, or any combination thereof. The agent module does not prescribe the form of the policy; it provides the interface through which any policy implementation can be plugged in. At each turn, the agent invokes its current policy with the processed observation and selects an action from the legal action space.

**Exploration and Exploitation Balancing.** Because ARC-AGI-3 environments provide no instructions or goals, the agent must balance exploration — taking actions to discover how the environment works — with exploitation — taking actions that it believes will advance toward a goal it has inferred. The agent module encapsulates the strategies for managing this balance, including curiosity-driven exploration bonuses, uncertainty-based action selection, and progressive strategy refinement as the agent's world model improves.

**Internal State Management.** The agent maintains an internal state that persists across turns within an episode. This state may include a history of observations and actions, accumulated beliefs about the environment's dynamics, inferred goals, and planning context. The state is fully serializable for checkpointing and replay purposes.

### Models Module (`src/arc_agi_3/models/`)

The models module provides the agent's representational and inferential capabilities. It is where the agent's understanding of the environment is built, maintained, and queried. Its responsibilities are:

**World Model Maintenance.** The world model is a learned internal representation of the environment's dynamics — a model that, given the current state and an action, predicts the next state. The models module is responsible for training this model from the agent's stream of observations and actions, updating it incrementally as new data arrives, and managing its capacity to avoid overfitting to early observations. The world model is the foundation of the agent's ability to plan ahead without physically executing actions.

**State Representation.** Raw grid observations are high-dimensional and redundant. The models module compresses them into compact, structured representations that capture the essential features of the environment state — object positions, spatial relationships, dynamic patterns, and invariant structures. These representations are what the agent's policy and planning algorithms operate on.

**Goal Inference.** Because ARC-AGI-3 environments do not provide explicit goals, the agent must infer what it is supposed to achieve. The models module supports goal inference by identifying regularities in the environment's reward signals (or the absence thereof), detecting progress indicators in the environment state, and maintaining a distribution over candidate goals that is updated as evidence accumulates.

**Planning and Prediction.** Using the world model, the agent can simulate the consequences of action sequences without executing them. The models module provides planning primitives — forward simulation, rollout evaluation, and tree-search support — that the agent module uses to select actions that are not merely locally optimal but globally efficient.

### Evaluation Module (`src/arc_agi_3/evaluation/`)

The evaluation module measures, records, and reports on the agent's performance. Its responsibilities are:

**Efficiency Scoring.** The primary metric for ARC-AGI-3 is Relative Human Action Efficiency, computed as the square of the ratio of the human baseline action count to the agent's action count, capped at one. The evaluation module computes this score for every episode, tracks it across environments and levels, and aggregates it into summary statistics.

**Per-Environment and Aggregate Metrics.** Beyond the primary score, the evaluation module tracks a comprehensive set of secondary metrics: levels completed per environment, action counts per level, exploration-to-exploitation ratios, goal-inference accuracy (when ground truth is available during development), and wall-clock time per episode. These metrics are essential for diagnosing bottlenecks and guiding development.

**Reporting and Visualization.** The evaluation module generates human-readable reports in both text and structured formats. Reports include per-environment breakdowns, trend analyses across runs, and comparisons between different agent configurations. All reports are written to disk and logged for archival purposes.

**Regression Detection.** As the agent evolves, it is critical to detect regressions — cases where a change that improves performance on some environments degrades it on others. The evaluation module maintains historical baselines and flags statistically significant regressions when they occur.

### Utilities Module (`src/arc_agi_3/utils/`)

The utilities module provides shared infrastructure that is used across all other modules. Its responsibilities are:

**Structured Logging.** All system components log their operations through a centralized, structured logging facility. Log entries include timestamps, module identifiers, severity levels, and structured payloads. Logging verbosity is configurable at both the global and per-module level, and logs can be directed to the console, to files, or to both.

**Configuration Loading.** The utilities module provides the configuration-loading pipeline: it reads YAML files from the `config/` directory, applies environment-variable overrides, validates the resulting configuration against a schema, and exposes the final configuration as typed objects that other modules can query without parsing logic.

**Reproducibility Infrastructure.** Seeding, checkpointing, and replay are managed by the utilities module. At the start of every run, the module seeds all random number generators with a deterministic seed derived from the run configuration. During a run, it provides checkpointing services that serialize the entire system state to disk at configurable intervals. After a run, it provides replay services that can reconstruct the agent's behavior from its logged observations and actions.

**Data Transformation Helpers.** Common data transformations — grid encoding and decoding, action-space enumeration, observation normalization, and batch construction — are collected in the utilities module to avoid duplication across the codebase.

---

## Data Flow

A single turn of agent-environment interaction proceeds through the following stages:

1. **Environment produces a frame.** The ARC-AGI-3 API delivers a frame containing the current grid state, the set of legal actions, and episode metadata.

2. **Environment module parses the frame.** The raw frame is parsed into a structured observation object and passed to the agent.

3. **Agent processes the observation.** The agent encodes the observation into its internal representation format and updates its state history.

4. **Agent queries the world model.** The agent passes the processed observation to the models module, which updates the world model and returns predictions, goal-inference results, or planning outputs as needed.

5. **Agent selects an action.** Using its policy, the agent selects an action from the legal action space. This selection may involve forward planning using the world model's simulation capabilities.

6. **Environment module validates and submits the action.** The selected action is validated against the legal action set and submitted to the ARC-AGI-3 API.

7. **Evaluation module records the turn.** The evaluation module logs the observation, the selected action, and any associated metrics for later scoring and reporting.

8. **The loop repeats** until the episode terminates (either by the agent completing all levels, exceeding the action budget, or encountering a terminal condition).

---

## Concurrency and Performance

The current architecture is single-threaded within an episode, reflecting the sequential nature of turn-based environment interaction. However, multiple episodes can be evaluated concurrently across different environments, and the evaluation module supports parallel scoring and report generation. If future performance requirements demand it, the architecture's modular design allows the models module to offload computation to GPU-accelerated backends without affecting the rest of the system.

---

## Extension Points

The architecture provides explicit extension points at every module boundary:

- **Custom agent policies** can be registered by implementing the base policy interface and specifying the policy class in `config/agent.yaml`.
- **Custom world model architectures** can be introduced by implementing the base model interface and registering them in `config/agent.yaml`.
- **Custom evaluation metrics** can be added by implementing the base metric interface and listing them in `config/evaluation.yaml`.
- **Custom environment adapters** can support alternative environment backends (such as local simulators or third-party benchmarks) by implementing the base environment interface and configuring the adapter in `config/environment.yaml`.

All extension points are documented with their interface contracts in the source code and summarized in [Functional Capabilities](FUNCTIONAL_CAPABILITIES.md).

---

## Security and Isolation

During competition evaluation, the agent runs in a sandboxed environment with no internet access. The architecture respects this constraint: no component depends on external network services during inference. The API client in the environment module is the only component that opens network connections, and it is configured to operate exclusively against the ARC-AGI-3 evaluation endpoint. All model weights, configurations, and inference logic are bundled locally.

---

## Summary

This architecture is designed to be transparent, modular, efficient, and reproducible. Every module has a single responsibility, every interface is well-defined, and every design decision is documented. The system can accommodate the rapid experimental iteration that ARC-AGI-3 research demands while maintaining the rigor and auditability that open-source competition requires.
