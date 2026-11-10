# Contributing Guide

> Full contribution guidelines live in
> [`CONTRIBUTING.md`](../CONTRIBUTING.md) at the repository root.

## Quick summary

- Development setup, common tasks, and Windows/PowerShell command
  equivalents: see the root `CONTRIBUTING.md`.
- **Honesty rule:** never claim a feature is implemented when it is not —
  update [PROGRESS.md](PROGRESS.md) in the same pull request that adds
  the feature.
- Every compiler change ships with tests, including negative cases.
- CI must pass: Ruff lint, Ruff format check, pytest, mypy.
- Security invariants are binding: compilation never executes tools, and
  workflow files are untrusted input. See
  [`SECURITY.md`](../SECURITY.md).
