"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import type { TenantData } from "@/lib/api";

interface TenantCardProps {
  tenant: TenantData;
}

export function TenantCard({ tenant }: TenantCardProps) {
  return (
    <div className="flex items-center gap-4 rounded-lg bg-slate-900 border border-slate-800 px-4 py-3 hover:border-slate-700 transition-colors">
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
