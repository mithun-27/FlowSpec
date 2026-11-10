# Changelog

All notable changes to FlowSpec are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffolding: `src/` package layout, packaging via Hatchling, and Ruff,
  pytest, mypy, and coverage configuration.
- Honest placeholder skeleton for every module defined in the architecture. Each
  module documents its responsibility and raises `NotImplementedError` instead of
  simulating behavior — see `docs/PROGRESS.md` for the implementation roadmap.
- `flowspec` command-line interface with a working `version` command. All other
  commands report that they are not implemented yet and exit with code 4.
- Design documentation for the planned compiler pipeline, type system, workflow
  language, diagnostics, integrations, and public API, plus the implementation
  checklist (`docs/PROGRESS.md`).
- Example project `examples/invoice_processing` with valid and deliberately
  invalid workflow definitions taken from the specification.
- CI workflow running Ruff and pytest on Linux and Windows for Python
  3.11–3.13, and a tag-triggered build workflow that produces distributions.
- Community files: Apache-2.0 `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`,
  issue templates, and a pull request template.
