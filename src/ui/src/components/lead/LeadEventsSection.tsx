"use client";

import { useEvents } from "@/hooks/useEvents";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

export function LeadEventsSection({
  tenantId,
  leadId,
}: {
  tenantId: string;
  leadId: string;
}) {
  const { events, loading, error } = useEvents({ tenantId, leadId });

  return (
    <section className="bg-slate-800 rounded-xl border border-slate-700 p-5">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-4">
        Event Log
      </h3>

      {error && <ErrorBanner message={error} />}
      {loading && (
        <div className="flex justify-center py-4">
          <Spinner size="sm" />
        </div>
      )}

      {!loading && events.length === 0 && (
        <p className="text-sm text-slate-500">No events yet.</p>
      )}

      <ol className="relative border-l border-slate-700 space-y-4 pl-4">
        {events.map((ev) => (
          <li key={ev.id} className="relative">
            <span className="absolute -left-[1.35rem] top-1 w-2.5 h-2.5 rounded-full bg-indigo-500 border-2 border-slate-800" />
            <div className="text-xs text-slate-500 font-mono mb-1">
              {ev.created_at ? new Date(ev.created_at).toLocaleString() : "—"}
            </div>
            <div className="text-sm font-medium text-white">{ev.event_type}</div>
            {ev.payload && Object.keys(ev.payload).length > 0 && (
              <pre className="mt-1 text-xs text-slate-400 overflow-x-auto">
                {JSON.stringify(ev.payload, null, 2)}
              </pre>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
