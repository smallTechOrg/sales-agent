# Plan: Delete Tenant from Home Page

**Date:** 2026-04-23  
**Scope:** Add a "Delete Tenant" action to the dashboard home page.

---

## Spec gap

`spec/product/09-api.md` documents no `DELETE /tenants/{id}` endpoint. The data model
(`spec/product/07-data-model.md`) does specify a `deleted_at` soft-delete column on
`TenantRow`. This feature is spec-aligned: we add the endpoint to the spec and implement it.

Spec file to update: `spec/product/09-api.md` — add `DELETE /tenants/{id}` under "Tenant settings".

---

## Phases

### Phase 1 — Spec (spec/product/09-api.md)

Add `DELETE /tenants/{id}` endpoint documentation:
- No auth (same as `POST /tenants` — operator-level bootstrap endpoint)
- Soft-delete: sets `deleted_at = now()` on the row
- `204 No Content` on success
- `404 TENANT_NOT_FOUND` if not found

### Phase 2 — Backend (src/zer0/api/tenant.py)

Add handler on `tenants_router`:

```python
@tenants_router.delete("/{tenant_id}", status_code=204)
def delete_tenant(tenant_id: str, session: Session = Depends(get_session)):
    ...
```

Soft-deletes the tenant row. Returns 204.

### Phase 3 — API client (src/ui/src/lib/api.ts)

Add `deleteTenant(tenantId: string)` on the `api` object.

### Phase 4 — UI (src/ui/src/components/tenant/TenantCard.tsx + page.tsx)

- Add a delete (trash) icon button to `TenantCard`.
- On click: show inline confirmation ("Delete <name>? This cannot be undone.") with
  Confirm / Cancel buttons.
- On confirm: call `api.deleteTenant`, then refresh the tenant list via `mutateTenants`.
- Error handling: show an `ErrorBanner` on failure.

---

## Risks

- Soft-delete only — the tenant data is not purged. Acceptable per spec lifecycle.
- No auth enforcement yet (spec phase 2). Consistent with existing create/list endpoints.
