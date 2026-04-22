"use client";

import { useMessages } from "@/hooks/useMessages";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

export function LeadMessagesSection({
  tenantId,
  leadId,
}: {
  tenantId: string;
  leadId: string;
}) {
  const { messages, loading, error } = useMessages({ tenantId, leadId });

  return (
    <section className="bg-slate-800 rounded-xl border border-slate-700 p-5">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-4">
        Messages
      </h3>

      {error && <ErrorBanner message={error} />}
      {loading && (
        <div className="flex justify-center py-4">
          <Spinner size="sm" />
        </div>
      )}

      {!loading && messages.length === 0 && (
        <p className="text-sm text-slate-500">No messages yet.</p>
      )}

      <ul className="space-y-3">
        {messages.map((msg) => (
          <li
            key={msg.id}
            className="rounded-lg bg-slate-900 border border-slate-700 p-4 text-sm"
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                <Badge label={msg.status} />
                <span className="text-slate-400 text-xs">seq #{msg.sequence_number}</span>
              </div>
              <span className="text-xs text-slate-500 font-mono">
                {msg.sent_at
                  ? new Date(msg.sent_at).toLocaleString()
                  : new Date(msg.created_at).toLocaleString()}
              </span>
            </div>
            <p className="text-slate-200 whitespace-pre-wrap">{msg.body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
