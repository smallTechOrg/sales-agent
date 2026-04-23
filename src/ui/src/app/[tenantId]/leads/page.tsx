"use client";

import { use, useState } from "react";
import { useLeads } from "@/hooks/useLeads";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import Link from "next/link";
import type { LeadData } from "@/lib/api";

function getFreshnessBadge(lastResearchedAt: string | null) {
  if (!lastResearchedAt) return { icon: "🔴", label: "Needs refresh" };
  const days = Math.floor(
    (Date.now() - new Date(lastResearchedAt).getTime()) / (1000 * 60 * 60 * 24)
  );
  if (days < 7) return { icon: "🟢", label: "Fresh" };
  if (days < 30) return { icon: "🟡", label: "Stale" };
  return { icon: "🔴", label: "Needs refresh" };
}

function getSourceBadge(source?: string | null) {
  switch (source) {
    case "linkedin":
      return { icon: "💼", label: "LinkedIn" };
    case "web":
      return { icon: "🌐", label: "Web" };
    case "directory":
      return { icon: "📚", label: "Directory" };
    default:
      return { icon: "—", label: "Unknown" };
  }
}

function formatStage(stage: string) {
  return stage
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function RelativeTime({ timestamp }: { timestamp: string | null }) {
  if (!timestamp) return <span className="text-slate-500">—</span>;
  const date = new Date(timestamp);
  const now = new Date();
  const days = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  let label = "";
  if (days === 0) label = "Today";
  else if (days === 1) label = "Yesterday";
  else if (days < 7) label = `${days}d ago`;
  else if (days < 30) label = `${Math.floor(days / 7)}w ago`;
  else if (days < 365) label = `${Math.floor(days / 30)}mo ago`;
  else label = `${Math.floor(days / 365)}y ago`;
  
  return (
    <span title={date.toLocaleString()} className="text-slate-400">
      {label}
    </span>
  );
}

const stageColors: Record<string, string> = {
  prospect: "bg-slate-700 text-slate-100",
  research: "bg-blue-700 text-blue-100",
  qualification: "bg-purple-700 text-purple-100",
  people: "bg-indigo-700 text-indigo-100",
  approval: "bg-amber-700 text-amber-100",
  outreach: "bg-green-700 text-green-100",
  first_contact: "bg-emerald-700 text-emerald-100",
  no_contact: "bg-orange-700 text-orange-100",
  rejected: "bg-red-700 text-red-100",
  blocked: "bg-gray-700 text-gray-100",
};

export default function LeadsPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const { leads, loading, error } = useLeads({ tenantId });
  const [filterStage, setFilterStage] = useState<string>("");
  const [filterSource, setFilterSource] = useState<string>("");

  const filtered = leads.filter((lead) => {
    if (filterStage && lead.stage !== filterStage) return false;
    if (filterSource && lead.source !== filterSource) return false;
    return true;
  });

  const stages = Array.from(new Set(leads.map((l) => l.stage))).sort();
  const sources = Array.from(
    new Set(leads.map((lead) => lead.source).filter((source): source is string => Boolean(source)))
  ).sort();

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">All Leads</h1>

      {error && <ErrorBanner message={error} />}

      {/* Filter Bar */}
      <div className="mb-6 flex gap-4">
        <div>
          <label className="block text-xs font-semibold uppercase text-slate-500 mb-2">
            Stage
          </label>
          <select
            value={filterStage}
            onChange={(e) => setFilterStage(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded text-slate-300 text-sm"
          >
            <option value="">All stages</option>
            {stages.map((stage) => (
              <option key={stage} value={stage}>
                {formatStage(stage)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-semibold uppercase text-slate-500 mb-2">
            Source
          </label>
          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded text-slate-300 text-sm"
          >
            <option value="">All sources</option>
            {sources.map((source) => {
              const badge = getSourceBadge(source);
              return (
                <option key={source} value={source}>
                  {badge.label}
                </option>
              );
            })}
          </select>
        </div>
        <div className="text-sm text-slate-400 flex items-end">
          {filtered.length} of {leads.length} leads
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-slate-500 text-sm py-8 text-center">
          {leads.length === 0
            ? "No leads yet. They appear here once discovery discovers and identifies companies."
            : "No leads match the current filters."}
        </p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-slate-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                <th className="px-4 py-3">Company</th>
                <th className="px-4 py-3">Domain</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Stage</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Industry</th>
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3">Language</th>
                <th className="px-4 py-3">Freshness</th>
                <th className="px-4 py-3">Last Activity</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.map((lead) => {
                const freshness = getFreshnessBadge(lead.last_researched_at);
                const sourceBadge = getSourceBadge(lead.source);
                const stageColor = stageColors[lead.stage] || "bg-slate-700 text-slate-100";
                
                return (
                  <tr key={lead.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3 font-medium text-white">
                      {lead.company_name || "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-xs">
                      {lead.domain || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span title={sourceBadge.label} className="text-lg">
                        {sourceBadge.icon}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${stageColor}`}>
                        {formatStage(lead.stage)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white font-mono">
                      {lead.score !== null ? `${lead.score.toFixed(1)}/100` : "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-400">
                      {lead.industry || "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {lead.headcount_range || "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs uppercase">
                      {lead.detected_language || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span title={freshness.label} className="text-lg">
                        {freshness.icon}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      <RelativeTime timestamp={lead.last_researched_at} />
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/${tenantId}/leads/${lead.id}`}
                        className="text-indigo-400 hover:underline text-xs"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
