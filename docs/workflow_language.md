# Workflow Language

> **Implemented for the v0.1.0 compiler foundation.** This document
> describes the YAML/JSON workflow schemas of FlowSpec as they are
> implemented today. See [PROGRESS.md](PROGRESS.md) for the live status.

FlowSpec's first release deliberately avoids inventing a programming
language. Workflows are **data** — YAML or JSON documents with a stable,
versioned schema that can evolve into a dedicated language later.

## Project structure

```text
invoice-agent/
├── flowspec.yaml        # Project + compiler configuration
├── tools.yaml           # Tool registry
├── workflow.yaml        # (or workflows/ directory)
├── workflows/
├── schemas/
├── tests/
└── .flowspec/           # Compiler output (cache, reports, build)
```

## Tool schema

Tools declare explicit input and output contracts:

```yaml
version: "1.0"

tools:
  get_customer:
    description: Find a customer using email.
    inputs:
      email:
        type: string
        required: true
    outputs:
      customer_id:
        type: CustomerID
        nullable: false
      email:
        type: string
    effects:
      - read
    permissions:
      - customers.read
```

- `inputs` / `outputs` map parameter names to `type`, `required`, and
  `nullable` declarations.
- `effects` declare side effects: `read`, `write`, `external_write`,
  `destructive`, `financial`, `network`, `unknown`.
- `permissions` declare what the tool requires (metadata — never proof of
  authorization).
- Destructive tools may declare `requires_confirmation: true`.

## Workflow schema

```yaml
version: "1.0"

workflow:
  name: invoice_processing
  description: Complete invoice processing workflow.

  inputs:
    email:
      type: string
      required: true
    amount:
      type: float
      required: true

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

  outputs:
    invoice_id: $invoice.invoice_id
```

## Workflow rules

1. Every step has a unique ID.
2. Every tool reference exists in the registry.
3. Every required tool input is supplied.
4. Every reference points to a workflow input or valid tool output.
5. Every reference resolves to a known type.
6. Every type assignment is compatible.
7. Every dependency appears in the dependency graph.
8. Circular dependencies are rejected.
9. Optional values never silently become required values.
10. Invalid workflows are never marked executable.

## Expression categories (v0.1.0)

| Expression | Meaning |
| ---------- | ------- |
| `$input.email` | Workflow input reference |
| `$customer.customer_id` | Step output reference |
| `"literal text"` | String literal |
| `25000` | Numeric literal |
| `true` / `false` | Boolean literal |
| `null` | Explicit null |

Complex expressions, transformations, conditional expressions, and function
calls arrive in later releases.

## Project configuration (`flowspec.yaml`)

```yaml
version: "1.0"

project:
  name: invoice-agent
  description: Invoice automation agent

compiler:
  strict_types: true
  allow_unknown_types: false
  detect_cycles: true
  validate_permissions: true
  generate_ir: true

paths:
  tools: ./tools.yaml
  workflows: ./workflows
  output: ./.flowspec/build

target:
  format: flowspec-ir
```
