"use client";

import { use } from "react";
import { useCustomers } from "@/hooks/useCustomers";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import Link from "next/link";

export default function CustomersPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const { customers, loading, error } = useCustomers(tenantId);

  return (
    <div className="max-w-4xl mx-auto">
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
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3">Last Enriched</th>
                <th className="px-4 py-3">Contacts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {customers.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 font-medium text-white">{c.company_name ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400 font-mono text-xs">{c.domain}</td>
                  <td className="px-4 py-3 text-slate-400">{c.industry ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">{c.headcount_range ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-500 text-xs">
                    {c.last_enriched_at
                      ? new Date(c.last_enriched_at).toLocaleDateString()
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/${tenantId}/contacts?customer_id=${c.id}`}
                      className="text-indigo-400 hover:underline text-xs"
                    >
                      View contacts
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
