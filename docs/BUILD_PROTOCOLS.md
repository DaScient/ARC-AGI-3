# Build Protocols

**Fully Transparent Build-Out Protocols for DaScient's ARC-AGI-3 Agent**

---

## Preface

This document describes every build, test, validation, and deployment protocol used in this project. The word "transparent" is taken literally: for each protocol, this document states what the protocol does, why it exists, what tools it uses, what inputs it expects, what outputs it produces, what conditions cause it to succeed or fail, and how its results are used by subsequent protocols. Nothing is hidden, nothing is abbreviated, and nothing is left to convention alone.

---

## Build Philosophy

The build system for this project is designed around three commitments:

**Determinism.** Given the same source code, the same configuration, and the same environment, the build system must produce the same result every time. This is achieved by pinning all dependencies to exact versions, seeding all stochastic processes, and using locked dependency resolution.

**Locality.** A developer must be able to run every build protocol on their local machine with no special infrastructure. The Makefile provides identical targets to those used in continuous integration. There is no "it works in CI" escape hatch — if it works anywhere, it must work everywhere.

**Incrementality.** Build steps that have not been affected by a source change are not re-executed. The dependency graph is explicit, and the build system leverages caching at every opportunity — Python bytecode caching, pip's download cache, and Pytest's result caching.

---

## Protocol Inventory

The following sections describe each build protocol in the order it appears in the standard development and continuous integration workflow.

---

### Protocol 1: Dependency Installation

**Purpose.** To install the project and all of its dependencies into a Python virtual environment, producing a fully functional development setup.

**When this runs.** This protocol runs when a developer first clones the repository, when the dependency specification changes, or when the continuous integration pipeline starts a fresh run.

**What it does.** The protocol creates (or reuses) a Python virtual environment, then invokes pip to install the project in editable mode with the `dev` extras group. The `dev` group includes Pytest for testing, Ruff for linting, Mypy for type checking, and all other development-time tools. Pip resolves dependencies from `pyproject.toml`, downloads them from the Python Package Index, and installs them into the virtual environment. Because `pyproject.toml` specifies exact version constraints for all direct dependencies, the resolution is deterministic.

**Command.**

```bash
make install
```

This is equivalent to:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Success condition.** The command exits with code zero and all imports from the `arc_agi_3` package succeed.

**Failure modes.** Dependency conflicts, network failures during download, or Python version incompatibilities will cause this protocol to fail with a descriptive error message from pip.

---

### Protocol 2: Code Linting

**Purpose.** To enforce a consistent code style across the entire codebase and to catch common programming errors through static analysis, before any tests are run.

**When this runs.** This protocol runs on every local `make lint` invocation, on every push to any branch, and as the first validation step in the continuous integration pipeline.

**What it does.** The protocol invokes Ruff, a fast Python linter and formatter, against the entire `src/` and `tests/` directories. Ruff checks for style violations (import ordering, line length, naming conventions), common bugs (unused variables, unreachable code, mutable default arguments), and security antipatterns (use of `eval`, insecure hash functions, overly broad exception handling). The specific rules enforced are configured in `pyproject.toml` under the `[tool.ruff]` section.

**Command.**

```bash
make lint
```

This is equivalent to:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

**Success condition.** Ruff reports zero violations and zero formatting differences.

**Failure modes.** Any style violation, formatting inconsistency, or static analysis finding causes this protocol to fail. The output includes the file path, line number, rule identifier, and a human-readable description of each finding. Developers can auto-fix most issues with `ruff check --fix` and `ruff format`.

---

### Protocol 3: Static Type Checking

**Purpose.** To verify that all type annotations in the codebase are internally consistent and that no type errors exist at the boundaries between modules.

**When this runs.** This protocol runs on every local `make typecheck` invocation and as the second validation step in the continuous integration pipeline.

**What it does.** The protocol invokes Mypy in strict mode against the `src/arc_agi_3/` package. Mypy reads the type annotations on all function signatures, variable declarations, and class definitions, and it verifies that every call site, assignment, and return value is type-consistent. Strict mode requires that all public functions have complete type annotations and that no `Any` types are used without explicit justification.

**Command.**

```bash
make typecheck
```

This is equivalent to:

```bash
mypy src/arc_agi_3/
```

**Success condition.** Mypy reports zero errors.

**Failure modes.** Type mismatches, missing annotations, incompatible return types, or incorrect generic parameterizations cause this protocol to fail. The output includes the file path, line number, and a detailed description of each type error.

---

### Protocol 4: Unit and Integration Testing

**Purpose.** To verify that every module's behavior matches its specification, that modules interact correctly at their boundaries, and that no regressions have been introduced.

**When this runs.** This protocol runs on every local `make test` invocation and as the third validation step in the continuous integration pipeline.

**What it does.** The protocol invokes Pytest against the `tests/` directory. Pytest discovers all test files matching the `test_*.py` naming pattern, collects all test functions matching the `test_*` naming convention, and executes them. Tests are organized by module: `test_agent.py` tests the agent module, `test_environment.py` tests the environment module, `test_models.py` tests the models module, and `test_evaluation.py` tests the evaluation module. Shared fixtures — such as mock environment instances, sample observations, and pre-configured agents — are defined in `conftest.py`.

Coverage measurement is enabled by default. After all tests complete, Pytest generates a coverage report showing which lines and branches of the source code were exercised by the test suite. The coverage threshold is configured in `pyproject.toml`.

**Command.**

```bash
make test
```

This is equivalent to:

```bash
pytest tests/ -v --cov=src/arc_agi_3 --cov-report=term-missing
```

**Success condition.** All tests pass and the coverage percentage meets or exceeds the configured threshold.

**Failure modes.** Any test assertion failure, unhandled exception, or coverage shortfall causes this protocol to fail. The output includes the test name, the assertion that failed, and a traceback showing the exact point of failure.

---

### Protocol 5: Full Verification

**Purpose.** To execute all validation protocols in sequence as a single, gated validation pass that mirrors the continuous integration pipeline.

**When this runs.** This protocol runs on every local `make verify` invocation and as the full validation sequence in the continuous integration pipeline.

**What it does.** The protocol runs Protocol 2 (linting), Protocol 3 (type checking), and Protocol 4 (testing) in strict sequence. If any protocol fails, the entire verification fails immediately and subsequent protocols are not executed. This fail-fast behavior ensures that developers receive feedback on the earliest possible failure point.

**Command.**

```bash
make verify
```

This is equivalent to:

```bash
make lint && make typecheck && make test
```

**Success condition.** All three constituent protocols succeed.

**Failure modes.** Any failure in linting, type checking, or testing causes this protocol to fail.

---

### Protocol 6: Sample Execution

**Purpose.** To run the agent against a bundled sample environment for rapid manual validation during development.

**When this runs.** This protocol runs on demand via `make run-sample` and is not part of the automated pipeline.

**What it does.** The protocol invokes the agent entry point with a pre-configured sample environment. The sample environment is a lightweight, deterministic simulation of an ARC-AGI-3 game that ships with the repository for development purposes. The agent interacts with the sample environment for a complete episode, and the evaluation module produces a summary report showing the agent's score, action count, and level progression.

**Command.**

```bash
make run-sample
```

**Success condition.** The agent completes the episode without errors and produces a valid evaluation report.

**Failure modes.** Configuration errors, missing dependencies, or agent crashes cause this protocol to fail.

---

### Protocol 7: Clean Build

**Purpose.** To remove all build artifacts, cached files, and generated outputs, restoring the repository to a pristine state.

**When this runs.** This protocol runs on demand via `make clean` when a developer wants to start from a fresh state.

**What it does.** The protocol removes compiled Python bytecode files, Pytest caches, Mypy caches, Ruff caches, coverage reports, and any generated evaluation outputs. It does not remove the virtual environment or installed dependencies.

**Command.**

```bash
make clean
```

**Success condition.** All specified artifacts are removed.

---

## Continuous Integration Pipeline

The continuous integration pipeline is defined in `.github/workflows/ci.yml` and runs on every push to any branch and on every pull request targeting the main branch. The pipeline consists of a single job that executes the following steps in order:

1. **Checkout.** The pipeline checks out the repository at the triggering commit.
2. **Python Setup.** The pipeline configures the specified Python version (3.11) using the GitHub Actions `setup-python` action.
3. **Dependency Caching.** The pipeline restores the pip download cache from previous runs to accelerate dependency installation.
4. **Installation.** The pipeline runs Protocol 1 (dependency installation).
5. **Linting.** The pipeline runs Protocol 2 (code linting).
6. **Type Checking.** The pipeline runs Protocol 3 (static type checking).
7. **Testing.** The pipeline runs Protocol 4 (unit and integration testing).

If any step fails, the pipeline halts immediately, the pull request is marked as failing, and a detailed log is available for inspection. The pipeline's configuration is version-controlled alongside the source code, ensuring that the build process itself is subject to code review.

---

## Dependency Management

All dependencies are declared in `pyproject.toml` under the `[project.dependencies]` and `[project.optional-dependencies]` sections. Direct dependencies specify minimum version constraints to ensure compatibility, and the `dev` extras group includes all tools needed for development. When adding or updating a dependency, the developer modifies `pyproject.toml`, runs `make install` to verify resolution, and commits the change.

The project does not use a separate lock file for production dependencies at this time, because the ARC-AGI-3 competition submission process packages the agent with its dependencies in a sandboxed evaluation environment. If reproducibility requirements tighten, a `pip freeze`-based lock file or a migration to a tool like `uv` or `pdm` with native lock file support can be introduced with minimal disruption.

---

## Summary

Every build protocol in this project is documented, deterministic, and reproducible. The local development workflow and the continuous integration pipeline execute the same steps in the same order. All configuration is version-controlled, all outputs are logged, and all failure conditions produce actionable diagnostics. This transparency is not an afterthought — it is a design requirement.
