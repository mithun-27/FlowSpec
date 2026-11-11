# FlowSpec

### A Type System and Compiler for AI Agent Tool Workflows

<p align="center">
  <strong>Make AI agent workflows compile before they execute.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-v0.1.0%20Implemented-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Language-Python-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Domain-AI%20Infrastructure-purple?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-Apache%202.0-green?style=for-the-badge" />
</p>

---

## Current Status

**✅ v0.1.0 compiler foundation is complete.** All core functionality
is implemented: parsing, AST construction, name resolution, semantic
analysis, type inference and checking, dependency graphs, cycle detection,
topological scheduling, constraint analysis, versioned IR generation,
and a full CLI and Python API.

- What works today: the compiler core, CLI (`flowspec version`, `init`,
  `inspect`, `parse`, `compile`, `explain`, `export`), deterministic JSON
  IR export, and the test/lint toolchain.
- What remains: dataflow and effect analysis (v0.2.0), integrations
  (v0.3.0+), graph rendering (v0.4.0), and the execution runtime.
- See [PROGRESS.md](docs/PROGRESS.md) for the live implementation checklist.

---

## What is FlowSpec?

AI agents can plan complex sequences of tool calls, but can those sequences actually execute successfully?

Consider an AI agent performing an invoicing operation:

```text
User Request
     |
     v
Find Customer
     |
     v
Create Invoice
     |
     v
Send Invoice
     |
     v
Update Payment Status
```

The workflow looks correct.

But what happens if:

- `Create Invoice` never receives a `customer_id`?
- `Send Invoice` receives a `CustomerID` instead of an `InvoiceID`?
- `Update Payment Status` requires a `payment_id` that was never produced?
- A tool executes before its dependencies are available?
- Two tools introduce a circular dependency?

Most agent systems discover these problems during execution.

**FlowSpec aims to catch them before execution begins.**

FlowSpec is an open-source compiler infrastructure that statically analyzes AI agent tool workflows, validates their data dependencies, checks types, detects structural errors, and generates validated execution plans.

Think of it as a compiler for AI agent workflows.

---

## The Problem

Modern AI agents interact with external tools, APIs, databases, MCP servers, and other agents.

However, an agent-generated workflow is not necessarily a valid executable program.

Traditional tool validation typically focuses on individual tool arguments. It does not necessarily establish whether an entire multi-tool workflow has valid dataflow.

For example:

```yaml
tools:
  create_invoice:
    inputs:
      customer_id: CustomerID
      amount: float
    outputs:
      invoice_id: InvoiceID

  send_invoice:
    inputs:
      invoice_id: InvoiceID
```

An agent might generate:

```yaml
steps:
  - id: create
    tool: create_invoice

  - id: send
    tool: send_invoice
```

The workflow is syntactically valid YAML, but it does not provide the required inputs.

FlowSpec analyzes the complete workflow and identifies these problems before any external tool is invoked.

---

## How FlowSpec Works

```text
       AI Agent / Developer
                 |
                 v
          Workflow Plan
            YAML / JSON
                 |
                 v
          Workflow Parser
                 |
                 v
       Abstract Syntax Tree (AST)
                 |
                 v
          Semantic Analysis
                 |
                 v
        Type Inference Engine
                 |
                 v
        Dependency Analyzer
                 |
                 v
          Static Analysis
                 |
                 v
        Constraint Validation
                 |
                 v
         Compilation Result
                 |
           +-----+-----+
           |           |
           v           v
        VALID        INVALID
           |           |
           v           v
       Compiled IR   Diagnostics
           |
           v
    Execution Scheduler
           |
           v
      Agent Tool Runtime
```

### Compilation Pipeline

| Stage | Responsibility |
|-------|----------------|
| Parsing | Read and validate workflow definitions |
| AST Construction | Convert workflows into structured representations |
| Semantic Analysis | Validate tools, references, and declarations |
| Type Inference | Infer types of tool outputs |
| Type Unification | Match producer outputs with consumer inputs |
| Dependency Analysis | Identify data dependencies |
| Static Analysis | Detect workflow errors before execution |
| Constraint Validation | Check required conditions and constraints |
| IR Generation | Generate normalized intermediate representation |
| Scheduling | Determine a valid execution order |

---

## Core Features

### 1. Type Safety

Validate that the output of one tool is compatible with the input expected by another.

```text
Expected: InvoiceID
Received: CustomerID

TYPE ERROR E201

CustomerID cannot be assigned to InvoiceID.
```

FlowSpec supports primitive types and custom semantic types.

### 2. Missing Dependency Detection

Identify required parameters that have no valid source.

```text
FLOW ERROR E101

Tool: send_invoice

Missing dependency:
    invoice_id: InvoiceID

Expected producer:
    create_invoice.invoice_id

Status:
    BLOCKED
```

### 3. Missing Dependency Detection

Identify required parameters that have no valid source.

### 4. Dependency Graph Analysis

Represent workflows as directed graphs and identify relationships between tool calls.

### 5. Circular Dependency Detection

Detect cycles that make valid execution ordering impossible.

### 6. Execution Order Generation

Use topological sorting to determine a valid order of operations.

### 7. Static Workflow Analysis

Identify:

- Missing required inputs
- Invalid output references
- Unknown tools
- Incompatible types
- Unresolved variables
- Circular dependencies
- Unreachable steps
- Invalid execution constraints

### 8. Structured Compiler Diagnostics

Provide meaningful error messages with:

- Error codes
- Workflow locations
- Expected types
- Actual types
- Missing dependencies
- Suggested corrections

### 9. Permission and Side-Effect Analysis

Understand the declared effects of tools, including:

- Read operations
- Write operations
- External operations
- Destructive operations
- Financial operations

### 10. MCP Integration

Import tool definitions from Model Context Protocol servers and normalize their schemas into FlowSpec's internal type system.

### 11. OpenAPI Integration

Import API specifications and convert their operations into typed tool definitions.

---

## Fundamental Computer Science Concepts

FlowSpec brings programming language theory and compiler engineering into AI agent development.

| Concept | Application |
|---------|-------------|
| Abstract Syntax Trees | Workflow representation |
| Type Systems | Input/output validation |
| Type Inference | Inferring tool output types |
| Type Unification | Checking type compatibility |
| Symbol Tables | Resolving workflow references |
| Dependency Graphs | Mapping execution relationships |
| Topological Sorting | Generating execution order |
| Cycle Detection | Identifying circular dependencies |
| Dataflow Analysis | Tracking parameter origins |
| Constraint Solving | Validating execution requirements |
| Static Analysis | Detecting errors before execution |
| Intermediate Representation | Normalizing compiled workflows |
| Effect Systems | Tracking tool side effects |

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Core compiler implementation |
| Typer | CLI development |
| Pydantic | Schema and data validation |
| PyYAML | YAML parsing |
| JSON Schema | Schema validation |
| NetworkX | Initial graph processing |
| Graphviz | Workflow visualization |
| Rich | Terminal diagnostics |
| Pytest | Automated testing |
| Hypothesis | Property-based testing |
| MCP Python SDK | MCP integration |
| HTTPX | API integration |
| MkDocs | Documentation |
| GitHub Actions | CI/CD |

---

## Development Roadmap

### Phase 1 — Compiler Foundation
- [x] YAML and JSON parsing
- [x] Abstract Syntax Tree construction
- [x] Tool registry
- [x] Primitive type system
- [x] Custom nominal types
- [x] Basic compiler diagnostics

### Phase 2 — Static Analysis
- [x] Type inference
- [x] Type unification
- [x] Missing dependency detection
- [x] Dependency graph construction
- [x] Circular dependency detection
- [x] Topological sorting
- [ ] Dataflow analysis

### Phase 3 — Advanced Compiler
- [x] Intermediate representation
- [x] Constraint validation
- [ ] Unreachable step detection
- [ ] Effect system
- [ ] Permission analysis
- [ ] Workflow optimization
- [ ] Automatic correction suggestions

### Phase 4 — Ecosystem Integrations
- [ ] MCP tool discovery
- [ ] MCP schema importer
- [ ] OpenAPI importer
- [ ] Python tool importer
- [ ] LangGraph adapter
- [ ] LangChain adapter

### Phase 5 — Developer Experience
- [ ] Interactive CLI
- [ ] Workflow visualization
- [x] JSON diagnostics
- [x] IR export
- [x] CI/CD integration
- [x] Documentation and examples

### Phase 6 — Open Source Release
- [ ] PyPI publication
- [ ] Hugging Face Playground
- [x] GitHub Actions
- [x] Contribution guidelines
- [ ] Community examples
- [x] Technical documentation

---

## CLI Vision

FlowSpec is designed to provide a developer-friendly command-line interface.

```bash
# Initialize a FlowSpec project
flowspec init

# Inspect available tool definitions
flowspec inspect tools.yaml

# Parse a workflow
flowspec parse workflow.yaml

# Compile and validate a workflow
flowspec compile workflow.yaml

# Explain workflow dependencies
flowspec explain workflow.yaml

# Generate workflow visualization
flowspec graph workflow.yaml

# Run static workflow tests
flowspec test workflow.yaml

# Optimize execution order
flowspec optimize workflow.yaml

# Export compiled intermediate representation
flowspec export workflow.yaml
```

Compiling the example prints:

```text
$ flowspec compile examples/invoice_processing/workflow.yaml
invoice_processing: compiled successfully
steps: 4
execution order: customer -> invoice -> payment -> send
execution stages: customer, invoice, payment/send
```

Invalid workflows fail with structured, located diagnostics and exit
code 1; invalid CLI usage exits with code 5. `flowspec graph`, `test`,
`validate-mcp`, and `validate-openapi` are planned (v0.3.0 / v0.4.0)
and exit with code 4 today.

---

## Contribute

FlowSpec is open source. Help make AI agent workflows more reliable. See
[CONTRIBUTING.md](CONTRIBUTING.md) for contributing guidelines.

---

## License

This project is intended to be released under the Apache License 2.0.

See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>FlowSpec</strong>
  <br/>
  Your agent plans it. FlowSpec proves it.
</p>
