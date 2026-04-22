"use client";

import Link from "next/link";
import { useTenant } from "@/lib/tenant-context";
import { useTenants } from "@/hooks/useTenants";

export function TopBar() {
  const { activeTenantId, setActiveTenant } = useTenant();
  const { tenants } = useTenants();

  return (
    <header className="fixed top-0 left-56 right-0 h-14 bg-slate-900 border-b border-slate-800 flex items-center px-6 gap-4 z-20">
      <h1 className="text-sm font-semibold text-slate-300 flex-1">
        {activeTenantId ? (
          <Link
            href={`/${activeTenantId}`}
            className="text-white hover:text-indigo-300"
          >
            {tenants.find((t) => t.id === activeTenantId)?.name ?? activeTenantId}
          </Link>
        ) : (
          <span className="text-slate-500">No tenant selected</span>
        )}
      </h1>

      {tenants.length > 1 && (
        <select
          className="text-xs bg-slate-800 border border-slate-700 text-slate-300 rounded px-2 py-1"
          value={activeTenantId ?? ""}
          onChange={(e) => setActiveTenant(e.target.value || null)}
        >
          <option value="">— select tenant —</option>
          {tenants.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
      )}
    </header>
  );
}
