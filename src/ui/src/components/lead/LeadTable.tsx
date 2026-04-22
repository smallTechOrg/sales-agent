"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import type { LeadData } from "@/lib/api";

// Must match LeadStage enum values in backend domain/lead.py
const LEAD_STAGES: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "prospect", label: "Prospect" },
  { value: "research", label: "Researching" },
  { value: "qualification", label: "Qualifying" },
  { value: "contacts", label: "Contacts" },
  { value: "approval", label: "Approval" },
  { value: "outreach", label: "Outreach" },
  { value: "first_contact", label: "Contacted" },
  { value: "no_contact", label: "No Contact" },
  { value: "rejected", label: "Rejected" },
  { value: "blocked", label: "Blocked" },
];

interface LeadFilterBarProps {
  stage: string;
  onStageChange: (stage: string) => void;
  stageCounts?: Record<string, number>;
}

export function LeadFilterBar({ stage, onStageChange, stageCounts }: LeadFilterBarProps) {
  return (
    <div className="flex flex-wrap gap-1.5 mb-4">
      {LEAD_STAGES.map((s) => {
        const isActive = s.value === stage || (s.value === "" && !stage);
        const count = s.value && stageCounts ? (stageCounts[s.value] ?? 0) : null;
        return (
          <button
            key={s.value}
            onClick={() => onStageChange(s.value)}
            className={`rounded-full px-3 py-0.5 text-xs font-medium transition-colors flex items-center gap-1 ${
              isActive
                ? "bg-indigo-700 text-white"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }`}
          >
            {s.label}
            {count !== null && count > 0 && (
              <span className={`rounded-full px-1.5 py-px text-[10px] font-bold ${isActive ? "bg-indigo-500" : "bg-slate-700 text-slate-300"}`}>
                {count}
              </span>
            )}
          </button>
        );
      })}
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
        No leads in this stage yet.
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
              {lead.company_name ?? lead.domain ?? lead.id}
            </div>
            <div className="text-xs text-slate-500 truncate">
              {lead.domain ?? "—"}
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
