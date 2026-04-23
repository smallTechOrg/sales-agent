"use client";

import { use, Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { usePeople } from "@/hooks/usePeople";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import type { PersonData } from "@/lib/api";

function sourceIcon(source: string) {
  switch (source) {
    case "linkedin": return "💼";
    case "web": return "🌐";
    case "directory": return "📚";
    default: return "🔗";
  }
}

function PersonDrawer({ person, onClose }: { person: PersonData; onClose: () => void }) {
  const [excerptOpen, setExcerptOpen] = useState(false);
  const name = (person.full_name ?? `${person.first_name ?? ""} ${person.last_name ?? ""}`.trim()) || "Unknown";
  const link = person.source_link;

  return (
    <div className="fixed inset-0 z-40 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-slate-900 rounded-lg max-w-lg w-full max-h-screen overflow-y-auto border border-slate-800">
        <div className="sticky top-0 bg-slate-900 border-b border-slate-800 p-4 flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-white">{name}</h2>
            {person.role && <p className="text-sm text-slate-400">{person.role}</p>}
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl">✕</button>
        </div>
        <div className="p-6 space-y-5">
          <div className="grid grid-cols-2 gap-4 text-sm bg-slate-800/30 p-4 rounded">
            <div><span className="text-slate-500">Email</span>
              <p className="text-white">{person.email ? <a href={`mailto:${person.email}`} className="text-indigo-400 hover:underline">{person.email}</a> : "—"}</p>
            </div>
            <div><span className="text-slate-500">Phone</span>
              <p className="text-white">{person.phone ?? "—"}</p>
            </div>
            <div><span className="text-slate-500">LinkedIn</span>
              <p>{person.linkedin_url ? <a href={person.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline text-xs">View profile</a> : <span className="text-white">—</span>}</p>
            </div>
            <div><span className="text-slate-500">Outreach</span>
              <p className="text-white">{person.outreach_stopped ? <span className="text-red-400">Stopped</span> : person.approved_for_outreach ? <span className="text-green-400">Approved</span> : <span className="text-slate-400">Pending</span>}</p>
            </div>
          </div>

          {link && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Source</h3>
              <div className="bg-slate-800/30 rounded p-3 text-sm">
                <div className="flex items-start gap-2">
                  <span title={link.source}>{sourceIcon(link.source)}</span>
                  <div className="flex-1 min-w-0">
                    <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline break-all text-xs">{link.url}</a>
                    {link.scraped_at && <p className="text-xs text-slate-500 mt-0.5">Scraped {new Date(link.scraped_at).toLocaleString()}</p>}
                    {link.page_excerpt && (
                      <div className="mt-1">
                        <button onClick={() => setExcerptOpen(v => !v)} className="text-xs text-slate-400 hover:text-white">
                          {excerptOpen ? "▲ Hide excerpt" : "▼ Show excerpt"}
                        </button>
                        {excerptOpen && (
                          <pre className="mt-1 text-xs text-slate-400 bg-slate-900 rounded p-2 whitespace-pre-wrap break-all max-h-36 overflow-y-auto">{link.page_excerpt}</pre>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PeopleInner({ tenantId }: { tenantId: string }) {
  const searchParams = useSearchParams();
  const companyId = searchParams.get("company_id") ?? undefined;
  const { people, loading, error } = usePeople(tenantId, { company_id: companyId });
  const [selected, setSelected] = useState<PersonData | null>(null);

  return (
    <>
      {companyId && (
        <p className="text-sm text-slate-500 mb-4">
          Filtered by company <span className="font-mono text-xs">{companyId}</span>
        </p>
      )}
      {error && <ErrorBanner message={error} />}
      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : people.length === 0 ? (
        <p className="text-slate-500 text-sm py-8 text-center">
          No people found. People are discovered during the contact-discovery stage of a campaign run.
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
                <th className="px-4 py-3">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {people.map((person) => (
                <tr key={person.id} className="hover:bg-slate-800/40 transition-colors cursor-pointer" onClick={() => setSelected(person)}>
                  <td className="px-4 py-3 font-medium text-white">
                    {(person.full_name ?? `${person.first_name ?? ""} ${person.last_name ?? ""}`.trim()) || "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{person.role ?? "—"}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {person.email ? (
                      <a href={`mailto:${person.email}`} className="text-indigo-400 hover:underline">
                        {person.email}
                      </a>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-400">{person.phone ?? "—"}</td>
                  <td className="px-4 py-3">
                    {person.linkedin_url ? (
                      <a
                        href={person.linkedin_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-400 hover:underline text-xs"
                      >
                        LinkedIn
                      </a>
                    ) : <span className="text-slate-600">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    {person.outreach_stopped ? (
                      <span className="text-red-400 text-xs">Stopped</span>
                    ) : person.approved_for_outreach ? (
                      <span className="text-green-400 text-xs">Approved</span>
                    ) : (
                      <span className="text-slate-500 text-xs">Pending</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {person.source_link ? (
                      <span title={person.source_link.url}>{sourceIcon(person.source_link.source)} Source</span>
                    ) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {selected && <PersonDrawer person={selected} onClose={() => setSelected(null)} />}
    </>
  );
}

export default function PeoplePage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">People</h1>
      <Suspense fallback={<div className="flex justify-center py-8"><Spinner /></div>}>
        <PeopleInner tenantId={tenantId} />
      </Suspense>
    </div>
  );
}