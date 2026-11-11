# Type System

> **Implemented for the v0.1.0 compiler foundation.** This document
> describes the FlowSpec type system as it is implemented today. See
> [PROGRESS.md](PROGRESS.md) for the live status.

The type system is owned by FlowSpec — Pydantic and JSON Schema may
validate external structures, but semantic type checking is FlowSpec's
own. Checking is deterministic; an LLM never participates.

## Primitive types

```text
string   integer   float   boolean   null   any
```

The `any` type is controlled by compiler configuration: strict mode
rejects unresolved or unrestricted types unless explicitly permitted.

## Nominal types

User-defined identifiers such as `CustomerID`, `InvoiceID`, and
`PaymentID` remain **distinct types** even when they share an underlying
representation:

```text
CustomerID != InvoiceID
```

Assigning a `CustomerID` where an `InvoiceID` is required is an error
(E202), not a silent pass.

## Generic types

```text
List[string]        List[InvoiceID]
Optional[CustomerID]
Dict[string, integer]
Union[CustomerID, InvoiceID]
Object
```

Structural object types declare nested properties with their own types
and required flags.

## Compatibility rules

| Source | Target | Result |
| ------ | ------ | ------ |
| string | string | Valid |
| integer | integer | Valid |
| integer | float | Valid with widening |
| float | integer | Invalid by default |
| CustomerID | CustomerID | Valid |
| CustomerID | InvoiceID | Invalid |
| List[string] | List[string] | Valid |
| Optional[T] | T | Invalid without null check |
| T | Optional[T] | Valid |
| null | Optional[T] | Valid |
| string | CustomerID | Invalid without explicit conversion |
| Any | T | Strict-mode error unless explicitly permitted |

All rules live in a **single central compatibility engine** — comparison
logic is never spread across compiler modules.

## Inference and unification

- **Inference** derives expression types from workflow input declarations,
  tool contracts, literals, and previously resolved expressions.
- **Unification** determines whether two types can satisfy the same
  constraint: exact equality, nominal checks, primitive widening, generic
  unification, optional handling, unions, and object compatibility.
