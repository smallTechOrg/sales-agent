"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import type { TenantData } from "@/lib/api";

interface TenantCardProps {
  tenant: TenantData;
  onDelete?: (id: string) => Promise<void>;
}

export function TenantCard({ tenant, onDelete }: TenantCardProps) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function handleConfirmDelete() {
    if (!onDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await onDelete(tenant.id);
    } catch (e) {
      setDeleteError(String(e));
      setDeleting(false);
      setConfirming(false);
    }
  }

  return (
    <div className="rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition-colors">
      <div className="flex items-center gap-4 px-4 py-3">
        <Link
          href={`/${tenant.id}`}
          className="flex-1 flex items-center gap-4 min-w-0"
        >
          <div className="min-w-0">
            <div className="font-semibold text-white truncate">{tenant.name}</div>
            <div className="text-xs text-slate-500 font-mono truncate">{tenant.id}</div>
          </div>
          <Badge label={tenant.default_approval_mode} />
          <div className="text-xs text-slate-500 ml-auto">
            cooldown {tenant.retargeting_cooldown_days}d
          </div>
        </Link>

        {onDelete && !confirming && (
          <button
            onClick={() => setConfirming(true)}
            className="ml-2 p-1.5 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors"
            title="Delete tenant"
            aria-label="Delete tenant"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 0 0 6 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 1 0 .23 1.482l.149-.022.841 10.518A2.75 2.75 0 0 0 7.596 19h4.807a2.75 2.75 0 0 0 2.742-2.53l.841-10.52.149.023a.75.75 0 0 0 .23-1.482A41.03 41.03 0 0 0 14 4.193V3.75A2.75 2.75 0 0 0 11.25 1h-2.5ZM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4ZM8.58 7.72a.75.75 0 0 0-1.5.06l.3 7.5a.75.75 0 1 0 1.5-.06l-.3-7.5Zm4.34.06a.75.75 0 1 0-1.5-.06l-.3 7.5a.75.75 0 1 0 1.5.06l.3-7.5Z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>

      {confirming && (
        <div className="px-4 pb-3 border-t border-slate-800 pt-3">
          <p className="text-sm text-slate-300 mb-3">
            Delete <span className="font-semibold text-white">{tenant.name}</span>? This cannot be undone.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleConfirmDelete}
              disabled={deleting}
              className="flex items-center gap-1.5 rounded bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-500 disabled:opacity-50"
            >
              {deleting && <Spinner size="sm" />}
              {deleting ? "Deleting…" : "Delete"}
            </button>
            <button
              onClick={() => { setConfirming(false); setDeleteError(null); }}
              disabled={deleting}
              className="rounded bg-slate-700 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-600 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
          {deleteError && (
            <p className="mt-2 text-xs text-red-400">{deleteError}</p>
          )}
        </div>
      )}
    </div>
  );
}

export function TenantCardLoading() {
  return (
    <div className="flex items-center gap-4 rounded-lg bg-slate-900 border border-slate-800 px-4 py-3">
      <Spinner size="sm" />
      <span className="text-slate-500 text-xs">Loading…</span>
    </div>
  );
}
