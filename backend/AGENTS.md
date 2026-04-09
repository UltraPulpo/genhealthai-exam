# AGENTS.md — Backend Code Quality Guide

## Quick Reference

All commands assume you are in the `backend/` directory with the venv activated:

```bash
cd backend
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/macOS
```

| Action | Command |
|--------|---------|
| Run tests | `pytest` |
| Run tests with coverage | `pytest --cov=app --cov-branch --cov-report=term-missing` |
| Run linter | `ruff check app/ tests/` |
| Auto-fix lint issues | `ruff check --fix app/ tests/` |
| Auto-format | `ruff format app/ tests/` |
| Check formatting | `ruff format --check app/ tests/` |
| Run static analysis | `mypy app/` |
| Run dependency audit | `pip-audit` |
| Run all checks | See "Full Check Suite" below |
| Install pre-commit hooks | `pre-commit install` |
| Run pre-commit manually | `pre-commit run --all-files` |

## Coverage Requirements

- **Line coverage:** 70% (will ratchet up as the project matures)
- **Branch coverage:** enforced via `--cov-branch`
- Coverage is enforced by pytest (`--cov-fail-under=70`). Tests that reduce coverage below the threshold will fail the test suite.

## Tool Configuration

All tool configs live in `pyproject.toml`:

- **`[tool.ruff]`** — Linter and formatter. Line length 99, Python 3.11+ target.
- **`[tool.ruff.lint]`** — Enabled rule sets: E, W, F, I, N, UP, B, A, S, T20, SIM, RUF, C4, DTZ, PIE, RET, PTH, TCH, TID, PERF.
- **`[tool.mypy]`** — Strict mode. Missing imports ignored for: flask_smorest, flask_limiter, flask_talisman, pdfplumber, anthropic.
- **`[tool.pytest.ini_options]`** — Runs with `--strict-markers --tb=short --cov=app --cov-branch --cov-fail-under=70`.
- **`[tool.coverage.report]`** — Shows missing lines, excludes `TYPE_CHECKING` blocks and `__main__` guards.

## Pre-Commit Hooks

Hooks run automatically on `git commit`:

1. **ruff format** — Auto-formats staged Python files
2. **ruff check** — Lints and auto-fixes; fails if unfixable issues remain
3. **mypy** — Strict type checking on `app/`
4. **trailing-whitespace** — Removes trailing whitespace
5. **end-of-file-fixer** — Ensures files end with a newline
6. **check-yaml** — Validates YAML syntax
7. **check-added-large-files** — Prevents accidental large file commits

To install hooks (required once per clone):
```bash
pre-commit install
```

To bypass hooks (emergency only):
```bash
git commit --no-verify
```

## Full Check Suite

Run this before requesting review or committing:

```bash
ruff format app/ tests/
ruff check app/ tests/
mypy app/
pytest
pip-audit
```

## Project Structure

```
backend/
├── app/           # Application source code
├── tests/         # Test files
├── migrations/    # Alembic database migrations
├── uploads/       # File uploads directory
├── pyproject.toml # Project config + all tool configs
├── requirements.txt
├── .pre-commit-config.yaml
└── .env.example
```
