"use client";

import { type Lead } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";

export function LeadProfile({ lead }: { lead: Lead }) {
  const rows: [string, string | number | null | undefined][] = [
    ["Domain", lead.domain],
    ["Industry", lead.industry],
    ["Headcount", lead.headcount_range],
    ["Business type", lead.business_type],
    ["Stage", lead.stage],
    ["Language", lead.detected_language],
    ["Created", lead.created_at ? new Date(lead.created_at).toLocaleString() : "—"],
    ["Updated", lead.updated_at ? new Date(lead.updated_at).toLocaleString() : "—"],
  ];

  return (
    <section className="bg-slate-800 rounded-xl border border-slate-700 p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-lg">
          {(lead.company_name ?? lead.domain ?? "?")[0].toUpperCase()}
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white">
            {lead.company_name ?? lead.domain ?? "Unknown"}
          </h2>
          <p className="text-sm text-slate-400">{lead.domain}</p>
          <Badge label={lead.stage} />
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="text-slate-400">{label}</dt>
            <dd className="text-white font-mono break-all">{value ?? "—"}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
