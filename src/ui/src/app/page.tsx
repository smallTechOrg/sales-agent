"use client";

import { useState } from "react";
import Link from "next/link";
import { useTenant } from "@/lib/tenant-context";
import { useTenants } from "@/hooks/useTenants";
import { TenantCard, TenantCardLoading } from "@/components/tenant/TenantCard";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

export default function DashboardPage() {
  const { knownTenantIds, addKnownTenant, removeKnownTenant } = useTenant();
  const { tenants, loading, error } = useTenants();
  const [addInput, setAddInput] = useState("");
  const [addError, setAddError] = useState("");

  const handleAdd = () => {
    const id = addInput.trim();
    if (!id) return;
    const uuidRe =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRe.test(id)) {
      setAddError("Must be a valid UUID (e.g. from the DB).");
      return;
    }
    addKnownTenant(id);
    setAddInput("");
    setAddError("");
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Tenants</h1>
        <Link
          href="/tenants/new"
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          + New Tenant
        </Link>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="flex flex-col gap-2 mb-6">
        {knownTenantIds.length === 0 && !loading && (
          <div className="text-slate-500 text-sm py-8 text-center">
            No tenants yet.{" "}
            <Link href="/tenants/new" className="text-indigo-400 hover:text-indigo-300 underline">
              Create your first tenant
            </Link>{" "}
            to get started.
          </div>
        )}
        {knownTenantIds.map((id, i) => {
          const tenant = tenants[i];
          if (loading || tenant === undefined)
            return <TenantCardLoading key={id} id={id} />;
          if (tenant === null)
            return (
              <div
                key={id}
                className="flex items-center gap-3 rounded-lg bg-slate-900 border border-red-900 px-4 py-3 text-sm text-red-400"
              >
                <span className="font-mono text-xs text-slate-500 flex-1">{id}</span>
                <span>Not found in DB</span>
                <button
                  onClick={() => removeKnownTenant(id)}
                  className="text-slate-600 hover:text-red-400 text-xs"
                >
                  ✕
                </button>
              </div>
            );
          return (
            <TenantCard
              key={id}
              tenant={tenant}
              onRemove={removeKnownTenant}
            />
          );
        })}
      </div>

      {/* Add existing tenant by UUID (secondary / advanced) */}
      <details className="rounded-lg bg-slate-900 border border-slate-800">
        <summary className="cursor-pointer px-4 py-3 text-sm text-slate-500 hover:text-slate-300 select-none">
          Add an existing tenant by UUID&hellip;
        </summary>
        <div className="px-4 pb-4 pt-2">
          <p className="text-xs text-slate-500 mb-2">
            Only needed if a tenant was created outside the UI (e.g. via the CLI).
          </p>
          <div className="flex gap-2">
          <input
            type="text"
            className="flex-1 rounded bg-slate-800 border border-slate-700 px-3 py-1.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            value={addInput}
            onChange={(e) => {
              setAddInput(e.target.value);
              setAddError("");
            }}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <button
            onClick={handleAdd}
            className="rounded bg-slate-700 px-3 py-1.5 text-sm text-white hover:bg-slate-600"
          >
            Add
          </button>
        </div>
        {addError && (
          <p className="text-xs text-red-400 mt-1">{addError}</p>
        )}
        </div>
      </details>
    </div>
  );
}
