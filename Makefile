# =============================================================================
# ARC-AGI-3 Makefile
# =============================================================================
# This Makefile provides build automation targets for the ARC-AGI-3 project.
# Every target corresponds to a documented build protocol. Run `make help`
# to see all available targets with descriptions.
#
# Usage:
#   make install       Install the project with development dependencies
#   make lint          Run code linting and format checking
#   make typecheck     Run static type checking
#   make test          Run the test suite with coverage
#   make verify        Run lint, typecheck, and test in sequence
#   make run-sample    Run the agent against a sample environment
#   make clean         Remove build artifacts and caches
#   make help          Show this help message
# =============================================================================

.PHONY: install lint typecheck test verify run-sample clean help

# Default Python interpreter — can be overridden with `make PYTHON=python3.12`
PYTHON ?= python

# ---------------------------------------------------------------------------
# Protocol 1: Dependency Installation
# ---------------------------------------------------------------------------
install:
	$(PYTHON) -m pip install -e ".[dev]"

# ---------------------------------------------------------------------------
# Protocol 2: Code Linting
# ---------------------------------------------------------------------------
lint:
	$(PYTHON) -m ruff check src/ tests/
	$(PYTHON) -m ruff format --check src/ tests/

# Auto-fix linting issues and reformat code
lint-fix:
	$(PYTHON) -m ruff check --fix src/ tests/
	$(PYTHON) -m ruff format src/ tests/

# ---------------------------------------------------------------------------
# Protocol 3: Static Type Checking
# ---------------------------------------------------------------------------
typecheck:
	$(PYTHON) -m mypy src/arc_agi_3/

# ---------------------------------------------------------------------------
# Protocol 4: Unit and Integration Testing
# ---------------------------------------------------------------------------
test:
	$(PYTHON) -m pytest tests/ -v --cov=src/arc_agi_3 --cov-report=term-missing

# ---------------------------------------------------------------------------
# Protocol 5: Full Verification
# ---------------------------------------------------------------------------
verify: lint typecheck test

# ---------------------------------------------------------------------------
# Protocol 6: Sample Execution
# ---------------------------------------------------------------------------
run-sample:
	$(PYTHON) -m arc_agi_3 --config config/agent.yaml --config config/environment.yaml --config config/evaluation.yaml

# ---------------------------------------------------------------------------
# Protocol 7: Clean Build
# ---------------------------------------------------------------------------
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	rm -rf outputs/ dist/ build/ *.egg-info src/*.egg-info

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
help:
	@echo "ARC-AGI-3 Build Targets"
	@echo "======================="
	@echo ""
	@echo "  install      Install project with development dependencies"
	@echo "  lint         Run Ruff linting and format checking"
	@echo "  lint-fix     Auto-fix linting issues and reformat code"
	@echo "  typecheck    Run Mypy static type checking"
	@echo "  test         Run Pytest test suite with coverage"
	@echo "  verify       Run lint + typecheck + test (full validation)"
	@echo "  run-sample   Run agent against a sample environment"
	@echo "  clean        Remove build artifacts and caches"
	@echo "  help         Show this help message"
