# Getting Started

> **Status: the compiler is not implemented yet.** This page describes
> how to set up the repository for development today and what you will be
> able to do once v0.1.0 ships. See [PROGRESS.md](PROGRESS.md).

## Installation

FlowSpec is not yet published on PyPI. Install from source (Windows,
Linux, and macOS):

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

## What works today

```bash
flowspec version     # Prints the package version
python -m pytest     # Runs the test suite
python -m ruff check src tests
```

Every other CLI command honestly reports that it is not implemented yet
and exits with code 4.

## What v0.1.0 will provide

```bash
# Initialize a FlowSpec project
flowspec init

# Inspect a tool registry
flowspec inspect tools.yaml

# Compile a workflow (the core deliverable)
flowspec compile workflow.yaml

# Explain dependency relationships
flowspec explain workflow.yaml

# Export the intermediate representation
flowspec compile workflow.yaml --emit-ir compiled.json
```

```python
from flowspec import Compiler

compiler = Compiler(tools="tools.yaml")
result = compiler.compile("workflow.yaml")
```

## Explore the example project

See [`examples/invoice_processing`](../examples/invoice_processing/) for
a complete tool registry and workflow (including a deliberately invalid
variant) that the compiler will validate once implemented.

## Documentation

Continue with [architecture.md](architecture.md) and
[workflow_language.md](workflow_language.md), or read the implementation
checklist in [PROGRESS.md](PROGRESS.md).
