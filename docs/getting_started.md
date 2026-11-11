# Getting Started

> **Status: the v0.1.0 compiler foundation is implemented.** This page
> shows how to set up the repository and compile your first workflow
> today. See [PROGRESS.md](PROGRESS.md) for what is real versus planned.

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
# Initialize, scaffold, and verify a new FlowSpec project
flowspec init

# Inspect a tool registry
flowspec inspect examples/invoice_processing/tools.yaml

# Compile a workflow (the core deliverable)
flowspec compile examples/invoice_processing/workflow.yaml

# Explain dependency relationships and parameter origins
flowspec explain examples/invoice_processing/workflow.yaml

# Export the intermediate representation as deterministic JSON
flowspec export examples/invoice_processing/workflow.yaml
```

Compiling the example prints:

```text
invoice_processing: compiled successfully
steps: 4
execution order: customer -> invoice -> payment -> send
execution stages: customer, invoice, payment/send
```

An invalid workflow fails with structured diagnostics and exit code 1:

```bash
flowspec compile examples/invoice_processing/workflow_invalid.yaml
```

The Python API works the same way:

```python
from flowspec import Compiler

compiler = Compiler()
result = compiler.compile(
    "examples/invoice_processing/workflow.yaml",
    tools_path="examples/invoice_processing/tools.yaml",
)

print(result.success)          # True
print(result.execution_order)  # ('customer', 'invoice', 'payment', 'send')
```

Commands not implemented yet (`test`, `graph`, `validate-mcp`,
`validate-openapi`) report that honestly and exit with code 4.

## Development

```bash
python -m pytest     # Runs the test suite
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
```

## Explore the example project

See [`examples/invoice_processing`](../examples/invoice_processing/) for
a complete tool registry and workflow (including a deliberately invalid
variant with documented expected diagnostics).

## Documentation

Continue with [architecture.md](architecture.md) and
[workflow_language.md](workflow_language.md), or read the implementation
checklist in [PROGRESS.md](PROGRESS.md).
