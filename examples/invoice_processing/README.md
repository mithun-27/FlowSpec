# Invoice Processing — Example Project

A complete FlowSpec example: invoice automation, straight from the
FlowSpec specification.

```text
Get Customer → Create Invoice → Send Invoice → Update Payment Status
```

> **Status: reference material only.** The FlowSpec compiler is not
> implemented yet, so nothing here can be compiled today. These files
> define the contracts the compiler will validate in v0.1.0. See
> [docs/PROGRESS.md](../../docs/PROGRESS.md).

## Files

| File | Contents |
| ---- | -------- |
| `tools.yaml` | Tool registry: `get_customer`, `create_invoice`, `send_invoice`, `update_payment_status` with input/output contracts, effects, and permissions |
| `workflow.yaml` | **Valid** workflow — expected to compile cleanly |
| `workflow_invalid.yaml` | **Deliberately invalid** workflow — must fail compilation |

## Expected behavior once v0.1.0 is implemented

`workflow.yaml` compiles successfully:

```text
✓ Workflow parsed
✓ Type checking passed
✓ Dependencies validated
✓ No circular dependencies
✓ Execution plan generated

Stage 1: get_customer
Stage 2: create_invoice
Stage 3: send_invoice
Stage 4: update_payment_status
```

`workflow_invalid.yaml` must fail with structured diagnostics including:

| Bug in the file | Expected diagnostic |
| --------------- | ------------------- |
| `$customer.customer_id` (a `CustomerID`) passed to `send_invoice.invoice_id` (expects `InvoiceID`) | E202 nominal type mismatch |
| Duplicate step `id: payment` declared twice | E304 duplicate step ID |
| Unknown tool `delete_customer` | E401 unknown tool |
| `$send.updated` (a `boolean`) passed where `CustomerID` is required | E201 type mismatch |

The invalid file must **never** produce executable IR.
