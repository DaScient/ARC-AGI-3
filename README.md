# ARC-AGI-3

**DaScient's Autonomous Agent for the Abstraction and Reasoning Corpus — Third Generation**

---

## Project Overview

This repository houses DaScient's purpose-built autonomous agent system designed to compete in the ARC Prize 2026 competition, which centers on the ARC-AGI-3 benchmark — the first fully interactive, agentic intelligence benchmark in the history of artificial intelligence research. Unlike its predecessors, ARC-AGI-3 replaces static grid-based pattern matching with dynamic, turn-based environments where an agent must explore, infer goals, build world models, and act with human-level efficiency — all without receiving any instructions, rules, or objectives in advance.

The ARC-AGI-3 benchmark measures what François Chollet has termed "skill-acquisition efficiency": the capacity to learn, adapt, and generalize in completely novel situations. As of early 2026, human participants solve one hundred percent of ARC-AGI-3 environments, while the most advanced frontier AI systems score below one percent. This project exists to close that gap through principled, open-source research and development.

Every element of this project — from its build protocols and configurations to its modular source architecture — has been designed with full transparency in mind. All protocols are documented in plain prose, all configurations are annotated and explained, and all functional capabilities are described with both their rationale and their implementation context.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Getting Started](#getting-started)
3. [Project Structure](#project-structure)
4. [Documentation](#documentation)
5. [Build and Development Workflow](#build-and-development-workflow)
6. [Configuration](#configuration)
7. [Functional Capabilities](#functional-capabilities)
8. [Testing](#testing)
9. [Contributing](#contributing)
10. [License](#license)

---

## Getting Started

### Prerequisites

This project requires Python 3.11 or later. All dependencies are managed through the Python packaging ecosystem using `pyproject.toml`. You will also need an ARC Prize API key to interact with the official ARC-AGI-3 environments.

### Installation

Clone this repository and install the project with all development dependencies:

```bash
git clone https://github.com/DaScient/ARC-AGI-3.git
cd ARC-AGI-3
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Copy the environment variable template and supply your credentials:

```bash
cp .env.example .env
# Edit .env with your ARC API key and preferred configuration overrides
```

### Quick Start

To verify your installation and run the agent against a sample environment:

```bash
make verify       # Runs linting, type checks, and unit tests
make run-sample   # Executes the agent against a bundled sample environment
```

---

## Project Structure

The repository is organized to separate concerns cleanly. Source code lives under `src/arc_agi_3/`, configuration templates reside in `config/`, documentation is collected in `docs/`, and all test suites are housed under `tests/`.

```
ARC-AGI-3/
├── .github/
│   └── workflows/           # Continuous integration and deployment pipelines
├── config/
│   ├── agent.yaml           # Agent behavior and hyperparameter configuration
│   ├── environment.yaml     # Environment interaction and connection settings
│   └── evaluation.yaml      # Scoring, metrics, and evaluation parameters
├── docs/
│   ├── ARCHITECTURE.md      # System architecture and design principles
│   ├── BUILD_PROTOCOLS.md   # Transparent build-out protocols
│   ├── CONFIGURATION.md     # Configuration reference and tuning guide
│   ├── DEVELOPMENT.md       # Development environment and workflow guide
│   └── FUNCTIONAL_CAPABILITIES.md  # Complete functional capability inventory
├── src/
│   └── arc_agi_3/
│       ├── __init__.py      # Package initialization and version declaration
│       ├── agent/           # Agent decision-making and action-selection logic
│       ├── environment/     # Environment wrappers and state management
│       ├── models/          # World models, representation learning, inference
│       ├── evaluation/      # Scoring, metrics, and performance analysis
│       └── utils/           # Shared utilities, logging, and helper functions
├── tests/
│   ├── conftest.py          # Shared test fixtures and configuration
│   ├── test_agent.py        # Agent module test suite
│   ├── test_environment.py  # Environment module test suite
│   ├── test_models.py       # Models module test suite
│   └── test_evaluation.py   # Evaluation module test suite
├── .env.example             # Environment variable reference template
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # MIT License
├── Makefile                 # Build automation and developer convenience targets
├── pyproject.toml           # Python project metadata and dependency specification
└── README.md                # This document
```

---

## Documentation

Comprehensive prose documentation is maintained in the `docs/` directory. Each document covers a distinct facet of the project and is written to be self-contained yet cross-referenced:

- **[Architecture](docs/ARCHITECTURE.md)** — Describes the system's layered architecture, the rationale behind each module boundary, and the data flow from environment observation through agent decision-making to action execution.

- **[Build Protocols](docs/BUILD_PROTOCOLS.md)** — A fully transparent account of every build, test, and deployment protocol used in this project. This document explains not just what happens at each stage, but why each step exists and how it contributes to the integrity of the final system.

- **[Configuration](docs/CONFIGURATION.md)** — A complete reference for every configurable parameter in the system, organized by module. Each parameter is documented with its purpose, its default value, its valid range, and the effect of changing it.

- **[Development](docs/DEVELOPMENT.md)** — A practical guide for setting up a local development environment, running the test suite, using the Makefile targets, and following the project's branching and code review conventions.

- **[Functional Capabilities](docs/FUNCTIONAL_CAPABILITIES.md)** — An exhaustive inventory of every functional capability the system provides, from low-level environment parsing to high-level strategic planning. Each capability is described in prose with its design intent, its interface boundaries, and its relationship to the broader system.

---

## Build and Development Workflow

All build and development tasks are automated through the project Makefile and the continuous integration pipeline. The core workflow proceeds as follows:

1. **Install** — `make install` installs the project in editable mode with all development dependencies.
2. **Lint** — `make lint` runs Ruff for code style enforcement and static analysis.
3. **Type Check** — `make typecheck` runs Mypy for static type verification across the entire codebase.
4. **Test** — `make test` executes the full Pytest test suite with coverage reporting.
5. **Verify** — `make verify` runs linting, type checking, and testing in sequence as a single validation gate.
6. **Run** — `make run-sample` executes the agent against a bundled sample environment for rapid iteration.

The continuous integration pipeline mirrors these steps exactly, ensuring that every pull request is validated against the same criteria that developers use locally. See [Build Protocols](docs/BUILD_PROTOCOLS.md) for a thorough discussion of each stage.

---

## Configuration

The project uses YAML-based configuration files stored in the `config/` directory. Each file governs a specific subsystem:

- **`agent.yaml`** — Controls the agent's exploration strategy, action-selection policy, learning rate schedules, and world-model hyperparameters.
- **`environment.yaml`** — Specifies connection parameters for the ARC-AGI-3 API, local environment settings, frame processing options, and timeout thresholds.
- **`evaluation.yaml`** — Defines scoring metrics, efficiency baselines, logging verbosity, and output formats for evaluation runs.

All configuration parameters can be overridden at runtime through environment variables or command-line arguments. The [Configuration Reference](docs/CONFIGURATION.md) provides a complete annotated guide.

---

## Functional Capabilities

The system is composed of five principal modules, each encapsulating a distinct set of functional capabilities:

1. **Agent** — The decision-making core. It receives observations from the environment, updates its internal state, selects actions according to its current policy, and adapts its strategy as it accumulates experience within an episode.

2. **Environment** — The interface layer between the agent and the ARC-AGI-3 benchmark. It manages API connections, translates raw frame data into structured observations, validates actions against the current legal action space, and handles episode lifecycle events.

3. **Models** — The representational and inferential engine. It maintains the agent's world model — a learned, internal representation of environment dynamics — and supports goal inference, state prediction, and planning computations.

4. **Evaluation** — The measurement and analysis subsystem. It computes Relative Human Action Efficiency scores, tracks per-environment and aggregate performance metrics, and generates detailed reports for human review.

5. **Utilities** — Shared infrastructure including structured logging, configuration loading, reproducibility utilities such as seeding and checkpointing, and common data-transformation helpers.

A detailed description of every capability within each module is provided in [Functional Capabilities](docs/FUNCTIONAL_CAPABILITIES.md).

---

## Testing

The test suite is built on Pytest and is designed to validate every module at the unit, integration, and system levels. Tests are located in the `tests/` directory and follow a consistent naming convention that mirrors the source package structure.

To run the full test suite:

```bash
make test
```

To run tests with verbose output and coverage reporting:

```bash
pytest tests/ -v --cov=src/arc_agi_3 --cov-report=term-missing
```

Test fixtures, mock environments, and shared utilities are defined in `tests/conftest.py`. The continuous integration pipeline runs the full test suite on every push and pull request, and coverage metrics are tracked over time.

---

## Contributing

We welcome contributions from researchers, engineers, and anyone interested in advancing agentic intelligence. Please read our [Contributing Guidelines](CONTRIBUTING.md) for information on how to propose changes, the code review process, branching conventions, and standards for documentation and testing.

---

## License

This project is released under the [MIT License](LICENSE).

Copyright (c) 2026 DaScient