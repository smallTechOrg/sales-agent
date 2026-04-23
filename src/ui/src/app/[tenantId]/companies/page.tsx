"use client";

import { use, useState, useEffect } from "react";
import { useCompanies } from "@/hooks/useCompanies";
import { api, ApiError } from "@/lib/api";
import type { SourceLinkData, CompanyData } from "@/lib/api";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

function getFreshnessBadge(lastEnrichedAt: string | null) {
  if (!lastEnrichedAt) return { icon: "🔴", label: "Needs refresh", title: "No enrichment data yet" };
  const days = Math.floor(
    (Date.now() - new Date(lastEnrichedAt).getTime()) / (1000 * 60 * 60 * 24)
  );
  if (days < 7) return { icon: "🟢", label: "Fresh", title: `${days} days ago` };
  if (days < 30) return { icon: "🟡", label: "Stale", title: `${days} days ago` };
  return { icon: "🔴", label: "Needs refresh", title: `${days} days ago` };
}

function RelativeTime({ timestamp }: { timestamp: string | null }) {
  if (!timestamp) return <span className="text-slate-500">—</span>;
  const date = new Date(timestamp);
  const now = new Date();
  const days = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  let label = "";
  if (days === 0) label = "Today";
  else if (days === 1) label = "Yesterday";
  else if (days < 7) label = `${days} days ago`;
  else if (days < 30) label = `${Math.floor(days / 7)} weeks ago`;
  else if (days < 365) label = `${Math.floor(days / 30)} months ago`;
  else label = `${Math.floor(days / 365)} years ago`;

  return (
    <span title={date.toLocaleString()} className="text-slate-400">
      {label}
    </span>
  );
}

function CompanyDetailDrawer({
  tenantId,
  companyId,
  onClose,
}: {
  tenantId: string;
  companyId: string;
  onClose: () => void;
}) {
  const [company, setCompany] = useState<CompanyData | null>(null);

  useEffect(() => {
    api
      .getCompany(tenantId, companyId)
      .then(setCompany)
      .catch((e: unknown) => {
        if (!(e instanceof ApiError)) console.error(e);
      });
  }, [tenantId, companyId]);

  if (!company) {
    return (
      <div className="fixed inset-0 z-40 bg-black/50 flex items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const freshness = getFreshnessBadge(company.last_enriched_at);

  return (
    <div className="fixed inset-0 z-40 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-slate-900 rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto border border-slate-800">
        <div className="sticky top-0 bg-slate-900 border-b border-slate-800 p-4 flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-white">{company.company_name || "Unknown Company"}</h2>
            <p className="text-sm text-slate-400 font-mono">{company.domain}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="space-y-3">
            <h3 className="font-semibold text-white">Profile</h3>
            <div className="grid grid-cols-2 gap-4 text-sm bg-slate-800/30 p-4 rounded">
              <div>
                <span className="text-slate-500">Industry</span>
                <p className="text-white">{company.industry || "—"}</p>
              </div>
              <div>
                <span className="text-slate-500">Business Type</span>
                <p className="text-white">{company.business_type || "—"}</p>
              </div>
              <div>
                <span className="text-slate-500">Headcount</span>
                <p className="text-white">{company.headcount_range || "—"}</p>
              </div>
              <div>
                <span className="text-slate-500">First Seen</span>
                <p className="text-white"><RelativeTime timestamp={company.first_seen_at} /></p>
              </div>
              <div className="col-span-2">
                <span className="text-slate-500">Enrichment Status</span>
                <p className="text-white">
                  <span className="mr-2">{freshness.icon}</span>
                  {freshness.label}
                  {company.last_enriched_at && (
                    <span className="text-slate-500 ml-2">(<RelativeTime timestamp={company.last_enriched_at} />)</span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {company.research_summary && (
            <div className="space-y-3">
              <h3 className="font-semibold text-white">Research Summary</h3>
              <div className="bg-slate-800/30 p-4 rounded text-slate-300 text-sm whitespace-pre-wrap">
                {company.research_summary}
              </div>
            </div>
          )}

          {company.signals && company.signals.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-white">Buying Intent Signals ({company.signals.length})</h3>
              <ul className="space-y-2">
                {company.signals.map((signal, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-indigo-400 mt-1">•</span>
                    <span>{signal}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {company.notes && (
            <div className="space-y-3">
              <h3 className="font-semibold text-white">Operator Notes</h3>
              <div className="bg-slate-800/30 p-4 rounded text-slate-300 text-sm">
                {company.notes}
              </div>
            </div>
          )}

          {company.source_links && company.source_links.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-white">Source Links ({company.source_links.length})</h3>
              <div className="space-y-2">
                {company.source_links.map((link: SourceLinkData) => (
                  <SourceLinkRow key={link.id} link={link} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SourceLinkRow({ link }: { link: SourceLinkData }) {
  const [open, setOpen] = useState(false);
  const icon = link.source === "linkedin" ? "💼" : link.source === "web" ? "🌐" : link.source === "directory" ? "📚" : "🔗";
  return (
    <div className="bg-slate-800/30 rounded p-3 text-sm">
      <div className="flex items-start gap-2">
        <span title={link.source}>{icon}</span>
        <div className="flex-1 min-w-0">
          <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline break-all text-xs">
            {link.url}
          </a>
          {link.scraped_at && (
            <p className="text-xs text-slate-500 mt-0.5">Scraped {new Date(link.scraped_at).toLocaleString()}</p>
          )}
          {link.page_excerpt && (
            <div className="mt-1">
              <button onClick={() => setOpen((v) => !v)} className="text-xs text-slate-400 hover:text-white">
                {open ? "▲ Hide excerpt" : "▼ Show excerpt"}
              </button>
              {open && (
                <pre className="mt-1 text-xs text-slate-400 bg-slate-900 rounded p-2 whitespace-pre-wrap break-all max-h-36 overflow-y-auto">
                  {link.page_excerpt}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CompaniesPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const { companies, loading, error } = useCompanies(tenantId);
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null);

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Companies</h1>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : companies.length === 0 ? (
        <p className="text-slate-500 text-sm py-8 text-center">
          No companies yet. They appear here once a lead is qualified and linked to a company domain.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-slate-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                <th className="px-4 py-3">Company</th>
                <th className="px-4 py-3">Domain</th>
                <th className="px-4 py-3">Industry</th>
                <th className="px-4 py-3">Business Type</th>
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3">Signals</th>
                <th className="px-4 py-3">Freshness</th>
                <th className="px-4 py-3">First Seen</th>
                <th className="px-4 py-3">Last Enriched</th>
                <th className="px-4 py-3">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {companies.map((company) => {
                const freshness = getFreshnessBadge(company.last_enriched_at);
                const notesPreview = company.notes
                  ? company.notes.substring(0, 50) + (company.notes.length > 50 ? "..." : "")
                  : null;
                return (
                  <tr
                    key={company.id}
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer"
                    onClick={() => setSelectedCompanyId(company.id)}
                  >
                    <td className="px-4 py-3 font-medium text-white">{company.company_name ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-xs">{company.domain}</td>
                    <td className="px-4 py-3 text-slate-400">{company.industry ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs capitalize">{company.business_type ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-400">{company.headcount_range ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {company.signals ? `${company.signals.length} signal${company.signals.length !== 1 ? "s" : ""}` : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span title={freshness.title} className="text-lg">{freshness.icon} {freshness.label}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      <RelativeTime timestamp={company.first_seen_at} />
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      <RelativeTime timestamp={company.last_enriched_at} />
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs max-w-xs truncate" title={company.notes || "No notes"}>
                      {notesPreview ? `"${notesPreview}"` : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selectedCompanyId && (
        <CompanyDetailDrawer
          tenantId={tenantId}
          companyId={selectedCompanyId}
          onClose={() => setSelectedCompanyId(null)}
        />
      )}
    </div>
  );
}