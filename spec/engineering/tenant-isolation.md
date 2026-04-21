# Rule: tenant isolation patterns

**Scope:** all code that touches tenant state, credentials, or external APIs.

> Note: This rule applies when the product is multi-tenant. If the product
> spec defines a single-tenant model, review whether these patterns still apply.
> See [`spec/product/01-vision.md`](../product/01-vision.md).

## Why these are strict

When multiple tenants share a process, one boundary violation — a shared client,
a missing `WHERE` clause, a module-level credential cache — means one tenant's
data or failure leaks into another. These patterns are cheap to maintain if you
never break them and expensive to restore if you do.

## Patterns

### P1. Always scope queries to the tenant

Every SELECT, UPDATE, and DELETE against tenant-scoped tables must include a
tenant scope predicate. No exceptions, including "administrative" reads.

Cross-tenant aggregates are explicitly-named functions in a dedicated reporting
module, with a docstring that says "reads across all tenants."

### P2. Construct API clients per-tenant per-run

Do not cache a client and pass it to a different tenant's code path. Build with
that tenant's credentials at job start, use, close.

### P3. Catch `Exception` at tenant boundary

Every tenant runner wraps its body in `try/except Exception`, logs the error with
`tenant_id`, and returns. A failure in one tenant must never propagate to another.

### P4. Rate-limit state is per-tenant

Never store a backoff timestamp or retry-after in a module-level variable. Scope
it per tenant.

### P5. Pass secrets explicitly through function arguments

Credentials are passed as arguments to the functions that use them, never stashed
in module-level or class-level state where another tenant's code might see them.

### P6. Bind `tenant_id` on every log line in tenant-scoped code

Use `log = logger.bind(tenant_id=tenant.id)` at the top of each tenant-scoped
function or class.

## Test coverage

Any code that touches tenant state needs a test with **two tenants configured**
that verifies state from tenant A is not visible to or affected by tenant B.
Single-tenant happy path is not sufficient coverage in this codebase.
