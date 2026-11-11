# Invoice Processing — Example Project

A complete FlowSpec example: invoice automation, straight from the
FlowSpec specification.

```text
Get Customer → Create Invoice → Send Invoice → Update Payment Status
```

> **Status: fully working.** The v0.1.0 compiler foundation is
> implemented, so every file below compiles (or fails) for real. Run the
> commands from this directory. See [docs/PROGRESS.md](../../docs/PROGRESS.md).

## Files

| File | Contents |
| ---- | -------- |
| `tools.yaml` | Tool registry: `get_customer`, `create_invoice`, `send_invoice`, `update_payment_status` with input/output contracts, effects, and permissions |
| `workflow.yaml` | **Valid** workflow — compiles cleanly |
| `workflow_invalid.yaml` | **Deliberately invalid** workflow — fails compilation with structured diagnostics |

## Compiling the valid workflow

```bash
flowspec compile workflow.yaml
```

```text
invoice_processing: compiled successfully
steps: 4
execution order: customer -> invoice -> payment -> send
execution stages: customer, invoice, payment/send
```

The `payment` and `send` steps have no data dependency between them, so
the execution plan runs them in parallel in stage 3.

Use `flowspec explain workflow.yaml` to see every step's dependencies,
parameter origins, and types, or `flowspec export workflow.yaml` to dump
the compiled intermediate representation as deterministic JSON.

## The invalid workflow must fail

`workflow_invalid.yaml` contains five deliberate bugs; compiling it
fails (exit code 1) with six structured diagnostics:

```text
invoice_processing_invalid: 6 errors
E102 workflow_invalid.yaml:85:9 (invoice_processing_invalid.ghost) step 'ghost' argument 'customer_id' references unknown output 'updated' of step 'send' (tool 'send_invoice' declares no such output) (expected one of: status, received $send.updated)
E201 workflow_invalid.yaml:59:9 (invoice_processing_invalid.payment) step 'payment' argument 'status': float is not compatible with string (expected string, received float)
E201 workflow_invalid.yaml:73:9 (invoice_processing_invalid.payment) step 'payment' argument 'status': float is not compatible with string (expected string, received float)
E202 workflow_invalid.yaml:52:9 (invoice_processing_invalid.send) step 'send' argument 'invoice_id': CustomerID and InvoiceID are distinct nominal types (expected InvoiceID, received CustomerID)
E304 workflow_invalid.yaml:69:7 (invoice_processing_invalid.payment) duplicate step id 'payment'
  suggestion: step ids must be unique within a workflow
E401 workflow_invalid.yaml:81:7 (invoice_processing_invalid.ghost) step 'ghost' uses unregistered tool 'delete_customer' (expected a tool registered in the tool schema, received delete_customer)
  suggestion: register 'delete_customer' in the tool schema
  suggestion: check the tool name for typos
```

| Bug in the file | Diagnostic |
| --------------- | ---------- |
| `$customer.customer_id` (a `CustomerID`) passed to `send_invoice.invoice_id` (expects `InvoiceID`) | E202 nominal type mismatch |
| Duplicate step `id: payment` declared twice | E304 duplicate step ID |
| Unknown tool `delete_customer` | E401 unknown tool |
| `$send.updated` is not an output of `send_invoice` (it declares only `status`) | E102 unknown output reference |
| `$input.amount` (a `float`) passed to `update_payment_status.status` (expects `string`), in both `payment` steps | E201 type mismatch ×2 |

The invalid file never produces executable IR: `flowspec export
workflow_invalid.yaml` refuses and exits with code 1.
