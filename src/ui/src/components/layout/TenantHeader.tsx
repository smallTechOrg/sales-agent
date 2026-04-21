"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import type { TenantData } from "@/lib/api";

interface TenantHeaderProps {
  tenant: TenantData;
}

export function TenantHeader({ tenant }: TenantHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h2 className="text-xl font-bold text-white">{tenant.name}</h2>
        <p className="text-xs text-slate-500 font-mono mt-0.5">{tenant.id}</p>
      </div>
      <div className="flex items-center gap-3">
        <Badge label={tenant.default_approval_mode} />
        <Link
          href={`/${tenant.id}/campaigns/new`}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
        >
          + New Campaign
        </Link>
      </div>
    </div>
  );
}
