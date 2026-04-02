# Development Guide

**Development Environment and Workflow Guide for DaScient's ARC-AGI-3 Agent**

---

## Preface

This document provides a practical, step-by-step guide for setting up a local development environment, working with the codebase, running the build protocols, and following the project's conventions for branching, code review, and documentation. It is written in full prose so that every step is accompanied by its rationale, and no procedural detail is left implicit.

---

## System Requirements

The following software must be installed on your development machine before you begin:

**Python 3.11 or later.** The project uses language features and standard library modules introduced in Python 3.11, including `tomllib` for configuration parsing and enhanced error messages for debugging. Python 3.12 and 3.13 are also supported.

**Git 2.30 or later.** The project uses conventional commit messages and branch-based workflows that rely on modern Git features. Any recent Git installation will suffice.

**Make.** The project provides a Makefile for build automation. GNU Make is available by default on macOS and Linux. On Windows, developers should use Windows Subsystem for Linux (WSL) or an equivalent Make-compatible environment.

**A text editor or IDE with Python support.** We recommend Visual Studio Code with the Python and Ruff extensions, or PyCharm with the Ruff plugin. Both provide inline linting, type checking, and autocompletion that are consistent with the project's toolchain.

---

## Initial Setup

### Step 1: Clone the Repository

Clone the repository to your local machine using Git:

```bash
git clone https://github.com/DaScient/ARC-AGI-3.git
cd ARC-AGI-3
```

This places you in the project root directory, which contains the Makefile, the configuration files, and the source and test directories.

### Step 2: Create a Virtual Environment

Create an isolated Python virtual environment to avoid conflicts with system-wide packages:

```bash
python -m venv .venv
```

Activate the virtual environment. On macOS and Linux:

```bash
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

You should see your shell prompt change to indicate the active virtual environment. All subsequent commands assume the virtual environment is active.

### Step 3: Install Dependencies

Install the project in editable mode with all development dependencies:

```bash
make install
```

This command runs `pip install -e ".[dev]"`, which installs the `arc_agi_3` package so that your local source changes take effect immediately (without reinstallation), and installs all development tools including Pytest, Ruff, Mypy, and coverage utilities.

### Step 4: Configure Environment Variables

Copy the environment variable template:

```bash
cp .env.example .env
```

Open the `.env` file in your editor and provide the required values:

- `ARC_API_KEY` — Your ARC-AGI-3 API key, obtained from the ARC Prize developer portal. This is required for remote environment interaction but not for local development with the simulator.
- `ARC_LOG_LEVEL` — Set to `DEBUG` for verbose output during development, or `INFO` for standard output.

The `.env` file is listed in `.gitignore` and will never be committed to version control.

### Step 5: Verify the Installation

Run the full verification suite to confirm that everything is installed correctly:

```bash
make verify
```

This runs linting, type checking, and the test suite. If all three pass, your development environment is correctly configured.

---

## Daily Development Workflow

### Running Individual Build Protocols

During development, you will typically run individual build protocols rather than the full verification suite:

- **Lint your code** after making changes: `make lint`
- **Check types** after modifying function signatures or adding new modules: `make typecheck`
- **Run tests** after implementing new features or fixing bugs: `make test`
- **Run everything** before pushing: `make verify`

### Running the Agent Locally

To test the agent against the bundled sample environment:

```bash
make run-sample
```

This starts a complete episode using the local simulator backend and produces an evaluation report in the configured output directory.

### Adding a New Module or Component

When adding a new component to the system:

1. Create the implementation file in the appropriate subdirectory under `src/arc_agi_3/`.
2. Add type annotations to all public functions and classes.
3. Create a corresponding test file in `tests/`.
4. Add any new configuration parameters to the appropriate YAML file in `config/` and document them in `docs/CONFIGURATION.md`.
5. Run `make verify` to ensure the new component integrates cleanly.
6. Update `docs/FUNCTIONAL_CAPABILITIES.md` if the component introduces a new capability.

### Modifying Configuration

When changing a configuration parameter:

1. Update the YAML file in `config/`.
2. If the parameter is new, add it to the configuration schema in the utilities module.
3. Document the parameter in `docs/CONFIGURATION.md` with its type, default, range, and description.
4. Run `make test` to ensure no tests depend on the old default.

---

## Branching and Version Control Conventions

### Branch Naming

All development work takes place on feature branches. Branch names follow this convention:

- `feature/<short-description>` for new capabilities (e.g., `feature/goal-inference-module`)
- `fix/<short-description>` for bug fixes (e.g., `fix/observation-parsing-edge-case`)
- `docs/<short-description>` for documentation changes (e.g., `docs/update-configuration-reference`)
- `refactor/<short-description>` for structural improvements (e.g., `refactor/agent-state-management`)

### Commit Messages

Commit messages follow the conventional commit format:

```
type(scope): short description

Longer explanation if needed, wrapped at 72 characters. Explain what
changed and why, not how (the diff shows how).
```

Types include `feat`, `fix`, `docs`, `refactor`, `test`, and `chore`. The scope is the module or area affected (e.g., `agent`, `environment`, `models`, `evaluation`, `config`, `ci`).

### Pull Request Process

1. Push your feature branch to the remote repository.
2. Open a pull request against the main branch.
3. Ensure that the continuous integration pipeline passes.
4. Request a review from at least one other contributor.
5. Address review feedback with additional commits on the same branch.
6. Once approved, merge using a squash merge to maintain a clean history on main.

---

## Code Style and Conventions

### Formatting

All code is formatted by Ruff according to the rules specified in `pyproject.toml`. Run `ruff format src/ tests/` to auto-format your code before committing. The CI pipeline rejects unformatted code.

### Type Annotations

All public functions and methods must have complete type annotations. Mypy is run in strict mode, which means that implicit `Any` types and missing return type annotations are treated as errors.

### Docstrings

All public modules, classes, and functions must have docstrings written in Google style. Docstrings should describe what the component does, not how it does it internally (that is what the source code is for). Parameter descriptions should include types and any constraints.

### Import Ordering

Imports are organized in three groups, separated by blank lines: standard library imports, third-party imports, and local imports. Within each group, imports are sorted alphabetically. Ruff enforces this ordering automatically.

---

## Troubleshooting

### "Module not found" errors

Ensure your virtual environment is activated and that you have run `make install`. If you recently added a new module, confirm that its parent directory contains an `__init__.py` file.

### Type checking errors on valid code

Ensure you are using Python 3.11 or later. Some type features used in this project require 3.11's enhanced type system. If the error persists, check whether the module's stubs need updating.

### Tests fail with "fixture not found"

Ensure that `tests/conftest.py` is present and that your test file is in the `tests/` directory. Pytest discovers fixtures from `conftest.py` files in the test directory hierarchy.

### API connection failures

Verify that your `.env` file contains a valid `ARC_API_KEY` and that your network allows outbound HTTPS connections to `api.arcprize.org`. For offline development, set `environment.local.use_local` to `true` in `config/environment.yaml`.

---

## Summary

This guide covers every aspect of working with the ARC-AGI-3 codebase: initial setup, daily workflow, branching conventions, code style standards, and troubleshooting. By following these practices, every contributor operates with the same tools, the same conventions, and the same expectations — which is the foundation of a transparent and effective development process.
