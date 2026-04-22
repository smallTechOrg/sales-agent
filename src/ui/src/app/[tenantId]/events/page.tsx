"use client";

import { useState, use } from "react";
import { useEvents } from "@/hooks/useEvents";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import { Pagination } from "@/components/ui/Pagination";
import { type LeadEvent } from "@/lib/api";
import Link from "next/link";

const PAGE_SIZE = 25;

function EventRow({ ev, tenantId }: { ev: LeadEvent; tenantId: string }) {
  return (
    <tr className="bg-slate-800/50 hover:bg-slate-800">
      <td className="px-4 py-3 text-xs text-slate-400 font-mono">
        {ev.created_at ? new Date(ev.created_at).toLocaleString() : "—"}
      </td>
      <td className="px-4 py-3 text-sm font-medium text-white">{ev.event_type}</td>
      <td className="px-4 py-3 font-mono text-xs text-slate-300">
        {ev.lead_id ? (
          <Link
            href={`/${tenantId}/leads/${ev.lead_id}`}
            className="text-indigo-400 hover:underline"
          >
            {ev.lead_id.slice(0, 8)}…
          </Link>
        ) : (
          <span className="text-slate-500">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-xs text-slate-400 max-w-xs truncate">
        {ev.payload && Object.keys(ev.payload).length > 0
          ? JSON.stringify(ev.payload)
          : "—"}
      </td>
    </tr>
  );
}

export default function EventsPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const [page, setPage] = useState(1);
  const { events, loading, error } = useEvents({ tenantId });

  const paged = events.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(events.length / PAGE_SIZE));

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Event Log</h1>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <>
          <div className="rounded-xl border border-slate-700 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-800">
                <tr>
                  {["Timestamp", "Event", "Lead", "Payload"].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {paged.length === 0 ? (
                  <tr>
                    <td
                      colSpan={4}
                      className="text-center py-8 text-slate-500"
                    >
                      No events yet.
                    </td>
                  </tr>
                ) : (
                  paged.map((ev) => (
                    <EventRow key={ev.id} ev={ev} tenantId={tenantId} />
                  ))
                )}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
