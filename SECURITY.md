# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in FlowSpec, please report it
privately using GitHub's **"Report a vulnerability"** option on the
[Security tab](https://github.com/mithun-27/FlowSpec/security) of the
repository.

Please do not open public issues for vulnerabilities. We aim to respond to
reports promptly.

## Trust model

FlowSpec is a compiler that treats **workflow files and external tool schemas
as untrusted input**. The following invariants are part of the project's core
specification and must hold at every stage of development:

1. **Compilation never executes tools.** Compiling a workflow must never
   invoke an external tool, API, MCP server, or shell command. Only an
   explicit runtime invocation may execute tools.
2. **No arbitrary code execution from workflow files.** Workflow definitions
   must never be evaluated as Python expressions or shell commands.
3. **Safe parsing only.** YAML loading must not construct arbitrary Python
   objects, and malformed or deeply nested input must be rejected safely.
4. **No secrets in diagnostics.** Compiler diagnostics must never expose
   credentials or other sensitive values.
5. **External schemas are validated before import.** Tool schemas imported
   from MCP servers or OpenAPI documents are untrusted and must be validated
   before being processed.
6. **Compilation is not authorization.** A successfully compiled workflow
   does not prove that credentials are valid, that a service is reachable, or
   that an operation is permitted. Runtime adapters must independently enforce
   authentication, access policies, and approvals.

## Scope

FlowSpec is currently in its scaffolding stage: the repository contains the
project structure, design documentation, and placeholder modules, but no
compiler logic yet. The invariants above are binding for all future
implementation work; see `docs/PROGRESS.md` for what is currently implemented.
