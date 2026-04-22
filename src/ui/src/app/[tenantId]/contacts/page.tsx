"use client";

import { use, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useContacts } from "@/hooks/useContacts";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

function ContactsInner({ tenantId }: { tenantId: string }) {
  const searchParams = useSearchParams();
  const customerId = searchParams.get("customer_id") ?? undefined;
  const { contacts, loading, error } = useContacts(tenantId, { customer_id: customerId });

  return (
    <>
      {customerId && (
        <p className="text-sm text-slate-500 mb-4">
          Filtered by customer <span className="font-mono text-xs">{customerId}</span>
        </p>
      )}
      {error && <ErrorBanner message={error} />}
      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : contacts.length === 0 ? (
        <p className="text-slate-500 text-sm py-8 text-center">
          No contacts found. Contacts are discovered during the contact-discovery stage of a campaign run.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-slate-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Phone</th>
                <th className="px-4 py-3">LinkedIn</th>
                <th className="px-4 py-3">Outreach</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {contacts.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 font-medium text-white">
                    {(c.full_name ?? `${c.first_name ?? ""} ${c.last_name ?? ""}`.trim()) || "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{c.role ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {c.email ? (
                      <a href={`mailto:${c.email}`} className="text-indigo-400 hover:underline">
                        {c.email}
                      </a>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{c.phone ?? "—"}</td>
                  <td className="px-4 py-3">
                    {c.linkedin_url ? (
                      <a
                        href={c.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-400 hover:underline text-xs"
                      >
                        LinkedIn
                      </a>
                    ) : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    {c.outreach_stopped ? (
                      <span className="text-red-400 text-xs">Stopped</span>
                    ) : c.approved_for_outreach ? (
                      <span className="text-green-400 text-xs">Approved</span>
                    ) : (
                      <span className="text-slate-500 text-xs">Pending</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

export default function ContactsPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Contacts</h1>
      <Suspense fallback={<div className="flex justify-center py-8"><Spinner /></div>}>
        <ContactsInner tenantId={tenantId} />
      </Suspense>
    </div>
  );
}
