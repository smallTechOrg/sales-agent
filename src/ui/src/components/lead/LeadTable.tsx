"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import type { LeadData } from "@/lib/api";

const STAGES = [
  "all",
  "discovered",
  "enriched",
  "qualified",
  "approved",
  "rejected",
  "outreach_active",
  "responded",
  "blocked",
];

interface LeadFilterBarProps {
  stage: string;
  onStageChange: (stage: string) => void;
}

export function LeadFilterBar({ stage, onStageChange }: LeadFilterBarProps) {
  return (
    <div className="flex flex-wrap gap-1 mb-4">
      {STAGES.map((s) => (
        <button
          key={s}
          onClick={() => onStageChange(s === "all" ? "" : s)}
          className={`rounded-full px-3 py-0.5 text-xs font-medium transition-colors ${
            (s === "all" && !stage) || s === stage
              ? "bg-indigo-700 text-white"
              : "bg-slate-800 text-slate-400 hover:bg-slate-700"
          }`}
        >
          {s}
        </button>
      ))}
    </div>
  );
}

interface LeadTableProps {
  leads: LeadData[];
  tenantId: string;
}

export function LeadTable({ leads, tenantId }: LeadTableProps) {
  if (leads.length === 0) {
    return (
      <div className="text-slate-500 text-sm py-8 text-center">
        No leads in this stage.
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {leads.map((lead) => (
        <Link
          key={lead.id}
          href={`/${tenantId}/leads/${lead.id}`}
          className="flex items-center gap-4 rounded-lg bg-slate-900 border border-slate-800 px-4 py-3 hover:border-slate-700 transition-colors"
        >
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-white truncate">
              {lead.name ?? lead.company ?? lead.url}
            </div>
            <div className="text-xs text-slate-500 truncate">
              {lead.company ?? lead.url}
            </div>
          </div>
          <Badge label={lead.stage} />
          {lead.score != null && (
            <span className="text-sm font-mono text-slate-400">
              {lead.score}
            </span>
          )}
          <span className="text-xs text-slate-600">
            {new Date(lead.updated_at).toLocaleDateString()}
          </span>
        </Link>
      ))}
    </div>
  );
}
