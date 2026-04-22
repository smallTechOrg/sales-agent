"use client";

import { use, useState } from "react";
import { useCustomers } from "@/hooks/useCustomers";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import Link from "next/link";
import type { CustomerData } from "@/lib/api";

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

function CustomerDetailDrawer({ 
  customer, 
  onClose 
}: { 
  customer: CustomerData; 
  onClose: () => void;
}) {
  const freshness = getFreshnessBadge(customer.last_enriched_at);
  
  return (
    <div className="fixed inset-0 z-40 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-slate-900 rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto border border-slate-800">
        <div className="sticky top-0 bg-slate-900 border-b border-slate-800 p-4 flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-white">{customer.company_name || "Unknown Company"}</h2>
            <p className="text-sm text-slate-400 font-mono">{customer.domain}</p>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl"
          >
            ✕
          </button>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Profile Section */}
          <div className="space-y-3">
            <h3 className="font-semibold text-white">Profile</h3>
            <div className="grid grid-cols-2 gap-4 text-sm bg-slate-800/30 p-4 rounded">
              <div>
                <span className="text-slate-500">Industry</span>
                <p className="text-white">{customer.industry || "—"}</p>
              </div>
              <div>
                <span className="text-slate-500">Business Type</span>
                <p className="text-white">{customer.business_type || "—"}</p>
              </div>
              <div>
                <span className="text-slate-500">Headcount</span>
                <p className="text-white">{customer.headcount_range || "—"}</p>
              </div>
              <div>
                <span className="text-slate-500">First Seen</span>
                <p className="text-white"><RelativeTime timestamp={customer.first_seen_at} /></p>
              </div>
              <div className="col-span-2">
                <span className="text-slate-500">Enrichment Status</span>
                <p className="text-white">
                  <span className="mr-2">{freshness.icon}</span>
                  {freshness.label}
                  {customer.last_enriched_at && (
                    <span className="text-slate-500 ml-2">(<RelativeTime timestamp={customer.last_enriched_at} />)</span>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Research Summary */}
          {customer.research_summary && (
            <div className="space-y-3">
              <h3 className="font-semibold text-white">Research Summary</h3>
              <div className="bg-slate-800/30 p-4 rounded text-slate-300 text-sm whitespace-pre-wrap">
                {customer.research_summary}
              </div>
            </div>
          )}

          {/* Signals */}
          {customer.signals && customer.signals.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-semibold text-white">Buying Intent Signals ({customer.signals.length})</h3>
              <ul className="space-y-2">
                {customer.signals.map((signal, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-indigo-400 mt-1">•</span>
                    <span>{signal}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Notes */}
          {customer.notes && (
            <div className="space-y-3">
              <h3 className="font-semibold text-white">Operator Notes</h3>
              <div className="bg-slate-800/30 p-4 rounded text-slate-300 text-sm">
                {customer.notes}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CustomersPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const { customers, loading, error } = useCustomers(tenantId);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerData | null>(null);

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Customers</h1>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : customers.length === 0 ? (
        <p className="text-slate-500 text-sm py-8 text-center">
          No customers yet. They appear here once a lead is qualified and linked to a company domain.
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
              {customers.map((c) => {
                const freshness = getFreshnessBadge(c.last_enriched_at);
                const notesPreview = c.notes ? c.notes.substring(0, 50) + (c.notes.length > 50 ? "..." : "") : null;
                return (
                  <tr 
                    key={c.id} 
                    className="hover:bg-slate-800/40 transition-colors cursor-pointer"
                    onClick={() => setSelectedCustomer(c)}
                  >
                    <td className="px-4 py-3 font-medium text-white">{c.company_name ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-xs">{c.domain}</td>
                    <td className="px-4 py-3 text-slate-400">{c.industry ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs capitalize">{c.business_type ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-400">{c.headcount_range ?? "—"}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs">
                      {c.signals ? `${c.signals.length} signal${c.signals.length !== 1 ? "s" : ""}` : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span title={freshness.title} className="text-lg">{freshness.icon} {freshness.label}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      <RelativeTime timestamp={c.first_seen_at} />
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      <RelativeTime timestamp={c.last_enriched_at} />
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs max-w-xs truncate" title={c.notes || "No notes"}>
                      {notesPreview ? `"${notesPreview}"` : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {selectedCustomer && (
        <CustomerDetailDrawer 
          customer={selectedCustomer}
          onClose={() => setSelectedCustomer(null)}
        />
      )}
    </div>
  );
}
