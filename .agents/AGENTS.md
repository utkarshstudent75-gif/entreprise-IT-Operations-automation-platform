# Workspace Customization Rules

## Verification Standards
Whenever modifying code or resolving issues related to Python styling, dependencies, formatting, or testing:
- **Run all code quality checks locally**: Proactively run `black --check .` (or `black .` to auto-format) and `ruff check .` on the codebase to guarantee styling compliance.
- **Verify dependencies**: Ensure dependency audits like `pip-audit` are run and verified.
- **Run test suites**: Run the full test suite (e.g. `pytest`) to verify functionality and ensure the CI pipeline does not encounter any regressions.
