# FlowSpec

### A Type System and Compiler for AI Agent Tool Workflows

<p align="center">
  <strong>Make AI agent workflows compile before they execute.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Under%20Development-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Language-Python-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Domain-AI%20Infrastructure-purple?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-Apache%202.0-green?style=for-the-badge" />
</p>

---

## Current Status

**⚠️ Under active development — the compiler is not implemented yet.**

The repository currently contains the complete project structure, packaging
and CI configuration, design documentation, and an honest placeholder
skeleton for every planned module. What works today:

- Installing the package from source (`pip install -e .`)
- `flowspec version`
- The development toolchain (pytest, Ruff, mypy) and CI

What does not work yet: every compiler feature — workflow parsing, type
checking, dependency analysis, diagnostics, and IR generation. All planned
commands other than `version` report that they are not implemented and exit
with code 4.

See the live implementation checklist in
[`docs/PROGRESS.md`](docs/PROGRESS.md) for exactly what is real versus
planned, and [`examples/invoice_processing`](examples/invoice_processing/)
for the example project the first release will compile.

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
|---|---|
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

### 3. Dependency Graph Analysis

Represent workflows as directed graphs and identify relationships between tool calls.

### 4. Circular Dependency Detection

Detect cycles that make valid execution ordering impossible.

```text
FLOW ERROR E301

Circular dependency detected:

A → B → C → A

Compilation failed.
```

### 5. Execution Order Generation

Use topological sorting to determine a valid order of operations.

### 6. Static Workflow Analysis

Identify:

- Missing required inputs
- Invalid output references
- Unknown tools
- Incompatible types
- Unresolved variables
- Circular dependencies
- Unreachable steps
- Invalid execution constraints

### 7. Structured Compiler Diagnostics

Provide meaningful error messages with:

- Error codes
- Workflow locations
- Expected types
- Actual types
- Missing dependencies
- Suggested corrections

### 8. Permission and Side-Effect Analysis

Understand the declared effects of tools, including:

- Read operations
- Write operations
- External operations
- Destructive operations
- Financial operations

Identify workflows that require additional authorization or approval.

### 9. MCP Integration

Import tool definitions from Model Context Protocol servers and normalize their schemas into FlowSpec's internal type system.

### 10. OpenAPI Integration

Import API specifications and convert their operations into typed tool definitions.

---

## Fundamental Computer Science Concepts

FlowSpec brings programming language theory and compiler engineering into AI agent development.

| Concept | Application |
|---|---|
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

## Example Tool Definitions

Define tools and their contracts using YAML.

```yaml
version: "1.0"

tools:

  get_customer:
    description: Retrieve customer details.

    inputs:
      email:
        type: string
        required: true

    outputs:
      customer_id:
        type: CustomerID

      email:
        type: string

    effects:
      - read


  create_invoice:
    description: Create a new invoice.

    inputs:
      customer_id:
        type: CustomerID
        required: true

      amount:
        type: float
        required: true

    outputs:
      invoice_id:
        type: InvoiceID

      payment_id:
        type: PaymentID

    effects:
      - write


  send_invoice:
    description: Send an invoice.

    inputs:
      invoice_id:
        type: InvoiceID
        required: true

    outputs:
      status:
        type: string

    effects:
      - external_write
```

## Example Workflow

```yaml
version: "1.0"

workflow:

  name: invoice_processing

  inputs:
    email:
      type: string

    amount:
      type: float

  steps:

    - id: customer
      tool: get_customer
      inputs:
        email: $input.email

    - id: invoice
      tool: create_invoice
      inputs:
        customer_id: $customer.customer_id
        amount: $input.amount

    - id: send
      tool: send_invoice
      inputs:
        invoice_id: $invoice.invoice_id

  outputs:
    invoice_id: $invoice.invoice_id
```

Every input has an explicit source, allowing the compiler to analyze the complete dataflow.

---

## Type System

FlowSpec aims to support the following types:

| Type | Description |
|---|---|
| `string` | Text values |
| `integer` | Whole numbers |
| `float` | Decimal numbers |
| `boolean` | True/false values |
| `UUID` | Unique identifiers |
| `CustomerID` | Customer identifier |
| `InvoiceID` | Invoice identifier |
| `PaymentID` | Payment identifier |
| `List[T]` | Collection of values |
| `Optional[T]` | Nullable values |
| `Dict[K,V]` | Key-value structures |
| `Object` | Structured objects |
| `Union[A,B]` | Multiple possible types |

Custom identifiers use nominal type checking.

For example:

```python
CustomerID != InvoiceID
```

Even if both identifiers are represented as strings at runtime, FlowSpec treats them as semantically different types.

---

## Compiler Error Reference

| Error Code | Category | Description |
|---|---|---|
| E001 | Syntax | Invalid workflow syntax |
| E101 | Dependency | Missing required dependency |
| E102 | Dependency | Unknown output reference |
| E103 | Dependency | Unresolved variable |
| E201 | Type | Type mismatch |
| E202 | Type | Incompatible custom types |
| E203 | Type | Unable to infer type |
| E204 | Type | Invalid nullable value |
| E301 | Graph | Circular dependency |
| E302 | Graph | Invalid execution order |
| E303 | Graph | Unreachable step |
| E304 | Graph | Duplicate step ID |
| E401 | Tool | Unknown tool |
| E402 | Tool | Invalid tool argument |
| E501 | Security | Missing permission |
| E502 | Security | Unsafe side-effect configuration |
| E601 | Constraint | Failed execution condition |

---

## Architecture

```text
flowspec/
│
├── src/
│   └── flowspec/
│       │
│       ├── parser/
│       │   ├── yaml_parser.py
│       │   ├── json_parser.py
│       │   ├── validator.py
│       │   └── ast_builder.py
│       │
│       ├── ast/
│       │   ├── nodes.py
│       │   ├── workflow.py
│       │   └── expressions.py
│       │
│       ├── typesystem/
│       │   ├── types.py
│       │   ├── type_checker.py
│       │   ├── inference.py
│       │   ├── unification.py
│       │   └── symbols.py
│       │
│       ├── registry/
│       │   ├── tool_registry.py
│       │   └── schema_loader.py
│       │
│       ├── graph/
│       │   ├── dependency.py
│       │   ├── cycle_detection.py
│       │   ├── topological_sort.py
│       │   └── scheduler.py
│       │
│       ├── analysis/
│       │   ├── semantic.py
│       │   ├── dataflow.py
│       │   ├── static.py
│       │   ├── effects.py
│       │   └── constraints.py
│       │
│       ├── compiler/
│       │   ├── pipeline.py
│       │   ├── compiler.py
│       │   ├── ir.py
│       │   └── diagnostics.py
│       │
│       ├── integrations/
│       │   ├── mcp/
│       │   ├── openapi/
│       │   ├── langgraph/
│       │   └── langchain/
│       │
│       ├── visualization/
│       │   └── graph_renderer.py
│       │
│       ├── cli.py
│       └── __init__.py
│
├── tests/
├── examples/
├── docs/
│
├── pyproject.toml
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

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

---

## Technology Stack

| Technology | Purpose |
|---|---|
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

## Integrations

FlowSpec aims to be framework-independent.

Planned integrations include:

- Model Context Protocol (MCP)
- OpenAPI / Swagger
- LangGraph
- LangChain
- Custom Python tools
- REST APIs
- Multi-agent systems

The goal is to validate workflows regardless of which framework generated them.

---

## Development Roadmap

### Phase 1 — Compiler Foundation
- [ ] YAML and JSON parsing
- [ ] Abstract Syntax Tree construction
- [ ] Tool registry
- [ ] Primitive type system
- [ ] Custom nominal types
- [ ] Basic compiler diagnostics

### Phase 2 — Static Analysis
- [ ] Type inference
- [ ] Type unification
- [ ] Missing dependency detection
- [ ] Dependency graph construction
- [ ] Circular dependency detection
- [ ] Topological sorting
- [ ] Dataflow analysis

### Phase 3 — Advanced Compiler
- [ ] Intermediate representation
- [ ] Constraint validation
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
- [ ] JSON diagnostics
- [ ] IR export
- [ ] CI/CD integration
- [ ] Documentation and examples

### Phase 6 — Open Source Release
- [ ] PyPI publication
- [ ] Hugging Face Playground
- [ ] GitHub Actions
- [ ] Contribution guidelines
- [ ] Community examples
- [ ] Technical documentation

---

## Who Is FlowSpec For?

- AI agent developers
- MCP tool developers
- AI infrastructure engineers
- Agent framework maintainers
- API developers
- Multi-agent system builders
- Researchers exploring reliable agent execution

---

## Design Philosophy

FlowSpec is built around three principles:

**1. Validate Before Execution**

Catch structural problems before an agent interacts with external systems.

**2. Make Dataflow Explicit**

Every tool input should have a traceable source, and every connection should respect its type contract.

**3. Keep Compilation Deterministic**

The compiler should produce predictable results. AI can assist with explanations and suggestions, but must not override the compiler's validation rules.

---

## Vision

AI agents are evolving from simple chat interfaces into systems capable of performing complex, multi-step operations.

As these systems become more autonomous, the reliability of their tool execution becomes increasingly important.

FlowSpec explores a different approach: treating agent-generated workflows as programs that deserve the same rigor as traditional software.

We believe that agent workflows should not merely look executable. Their structure, dependencies, and contracts should be validated before execution.

**Compile the plan. Validate the dataflow. Then execute.**

---

## Contributing

FlowSpec is being developed as an open-source project.

Contributions are welcome in:

- Compiler construction
- Programming language theory
- Type systems
- Graph algorithms
- Static analysis
- MCP integrations
- API schema processing
- Testing and benchmarking
- Documentation

If you're interested in making AI agent execution more reliable, you're welcome to contribute.

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
