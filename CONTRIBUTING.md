# Contributing to ARC-AGI-3

**Guidelines for Contributing to DaScient's ARC-AGI-3 Agent**

---

## Welcome

We welcome contributions from researchers, engineers, students, and anyone motivated by the challenge of building systems that can learn, reason, and adapt in novel environments. This document describes the standards, processes, and expectations that govern contributions to this project.

---

## How to Contribute

### Reporting Issues

If you discover a bug, a documentation gap, a test failure, or a performance anomaly, please open a GitHub issue with the following information:

- A clear, descriptive title.
- A detailed description of the issue, including what you expected to happen and what actually happened.
- Steps to reproduce the issue, if applicable.
- The output of `make verify`, if the issue is related to a build or test failure.
- Your Python version, operating system, and any relevant configuration overrides.

### Proposing Changes

Before starting work on a significant change, please open an issue or a discussion to describe your proposal. This allows the maintainers and other contributors to provide feedback on the approach before code is written, which saves time and avoids duplicated effort.

For small changes — such as fixing a typo, correcting a documentation error, or resolving a simple bug — you may open a pull request directly.

### Submitting Pull Requests

1. Fork the repository and create a feature branch from `main` following the branching conventions described in [Development](docs/DEVELOPMENT.md).
2. Make your changes, ensuring that all new code includes type annotations and docstrings.
3. Add or update tests to cover your changes.
4. Run `make verify` to confirm that linting, type checking, and all tests pass.
5. Commit your changes with a conventional commit message.
6. Push your branch and open a pull request against `main`.
7. In the pull request description, explain what the change does and why it is needed. Reference any related issues.
8. Respond to review feedback promptly and push additional commits to the same branch.

---

## Standards

### Code Quality

All contributed code must pass the project's linting, type checking, and testing protocols without exceptions. Code that introduces linting violations, type errors, or test failures will not be merged.

### Testing

Every new capability or bug fix must be accompanied by tests that verify the change. Tests should be placed in the `tests/` directory, follow the `test_*.py` naming convention, and use the fixtures defined in `conftest.py` where appropriate.

### Documentation

All public functions, classes, and modules must have docstrings. If a change introduces a new configuration parameter, it must be documented in `docs/CONFIGURATION.md`. If a change introduces a new functional capability, it must be documented in `docs/FUNCTIONAL_CAPABILITIES.md`. If a change affects the build process, it must be documented in `docs/BUILD_PROTOCOLS.md`.

### Commit Messages

Follow the conventional commit format: `type(scope): description`. See [Development](docs/DEVELOPMENT.md) for details.

---

## Code of Conduct

All contributors are expected to treat one another with respect, to engage constructively in discussions and code reviews, and to prioritize the quality and integrity of the project above personal preferences. We are building something that aspires to advance the frontier of artificial intelligence — the standard for our collaboration should reflect that ambition.

---

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License, consistent with the project's existing license.

---

## Questions

If you have questions about contributing that are not answered by this document or by the [Development Guide](docs/DEVELOPMENT.md), please open a GitHub discussion or contact the maintainers.
