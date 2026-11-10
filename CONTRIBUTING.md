# Contributing to FlowSpec

Thank you for your interest in improving FlowSpec. This project is compiler
infrastructure for AI agent workflows, so correctness, determinism, and honest
reporting matter more than feature count.

## Development setup

The commands below work on Windows, Linux, and macOS.

```bash
git clone https://github.com/mithun-27/FlowSpec.git
cd FlowSpec

python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

python -m pip install -e ".[dev]"
```

Verify your environment:

```bash
python -m pytest
python -m ruff check src tests
flowspec version
```

## Common tasks

A `Makefile` is provided for Unix-like systems. On Windows, run the underlying
Python commands directly — every target maps to one:

| Make target   | Direct command                                    |
| ------------- | ------------------------------------------------- |
| `make dev`    | `python -m pip install -e ".[dev]"`               |
| `make lint`   | `python -m ruff check src tests` and `python -m ruff format --check src tests` |
| `make format` | `python -m ruff format src tests`                |
| `make typecheck` | `python -m mypy src`                           |
| `make test`   | `python -m pytest`                                |
| `make build`  | `python -m build`                                 |

## Code style

- Formatting and linting are enforced by Ruff (line length 100, target
  Python 3.11). Run `python -m ruff format src tests` before committing.
- Use type hints throughout; `mypy` is configured in `pyproject.toml`.
- Keep compiler logic free of dependencies on terminal formatting libraries —
  Rich is only used by the CLI.
- Use `pathlib` and cross-platform Python; the development environment may be
  Windows.
- Every module starts with a docstring stating its responsibility and status.

## Testing policy

A compiler that only works on the happy path is not acceptable (specification
§25). Every compiler pass must ship with:

- Unit tests for the pass itself.
- Valid workflow tests.
- Invalid workflow tests proving the expected diagnostic is produced.
- Edge-case tests where relevant.

Property-based tests use Hypothesis, and benchmarks live under
`tests/benchmarks/`.

## Honest progress reporting

The single most important contribution rule: **never claim a feature is
implemented when it is not.**

- Placeholders raise `NotImplementedError` — they never return fake success.
- When you implement or change a feature, update `docs/PROGRESS.md` in the
  same pull request.
- Documentation must match implementation; delete or mark outdated docs rather
  than leaving stale instructions.

## Pull requests

- Keep pull requests focused; one logical change per request.
- Use [Conventional Commits](https://www.conventionalcommits.org/) style for
  commit messages (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, ...).
- Fill in the pull request template, including the checklist.
- CI must pass: Ruff lint, Ruff format check, and pytest on Linux and Windows.

## Reporting bugs and security issues

- Bugs: open an issue using the bug report template.
- Security vulnerabilities: see `SECURITY.md` — do not open public issues for
  vulnerabilities.
