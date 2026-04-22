"use client";

import { useState, use } from "react";
import Link from "next/link";
import { useMessages } from "@/hooks/useMessages";
import { Badge } from "@/components/ui/Badge";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import { Pagination } from "@/components/ui/Pagination";
import { type Message } from "@/lib/api";

const PAGE_SIZE = 20;

function MessageRow({ msg, tenantId }: { msg: Message; tenantId: string }) {
  return (
    <tr className="bg-slate-800/50 hover:bg-slate-800">
      <td className="px-4 py-3 font-mono text-xs text-slate-300">
        <Link
          href={`/${tenantId}/leads/${msg.lead_id}`}
          className="text-indigo-400 hover:underline"
        >
          {msg.lead_id.slice(0, 8)}…
        </Link>
      </td>
      <td className="px-4 py-3">
        <Badge label={msg.status} />
      </td>
      <td className="px-4 py-3 text-xs text-slate-400">{msg.sequence_number}</td>
      <td className="px-4 py-3 text-xs text-slate-300 max-w-xs truncate">
        {msg.body}
      </td>
      <td className="px-4 py-3 text-xs text-slate-400 font-mono">
        {msg.sent_at
          ? new Date(msg.sent_at).toLocaleString()
          : new Date(msg.created_at).toLocaleString()}
      </td>
    </tr>
  );
}

export default function MessagesPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const [page, setPage] = useState(1);
  const { messages, loading, error } = useMessages({ tenantId });

  const paged = messages.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(messages.length / PAGE_SIZE));

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Messages</h1>

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
                  {["Lead", "Status", "Seq #", "Body", "Date"].map((h) => (
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
                      colSpan={5}
                      className="text-center py-8 text-slate-500"
                    >
                      No messages yet.
                    </td>
                  </tr>
                ) : (
                  paged.map((msg) => (
                    <MessageRow key={msg.id} msg={msg} tenantId={tenantId} />
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
