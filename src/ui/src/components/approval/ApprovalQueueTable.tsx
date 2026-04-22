"use client";

import { useState } from "react";
import Link from "next/link";
import { api, type Approval, type ApprovalItem, ApiError } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

// ── Message-approval modal ───────────────────────────────────────────────────

function MessageApprovalModal({
  item,
  tenantId,
  onClose,
  onDone,
}: {
  item: Extract<ApprovalItem, { type: "message" }>;
  tenantId: string;
  onClose: () => void;
  onDone: () => void;
}) {
  const [body, setBody] = useState(item.body ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(decision: "approve" | "reject") {
    setLoading(true);
    setError("");
    try {
      await api.approveMessage(tenantId, item.id, {
        decision,
        body: decision === "approve" && body !== item.body ? body : undefined,
      });
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-lg p-6 shadow-xl">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-lg font-semibold text-white">Review Message</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">×</button>
        </div>

        <div className="text-xs text-slate-500 font-mono mb-1">
          Lead:{" "}
          <Link href={`/${tenantId}/leads/${item.lead_id}`} className="text-indigo-400 hover:underline">
            {item.lead_id.slice(0, 8)}…
          </Link>
        </div>
        <div className="text-xs text-slate-500 mb-4">Channel: {item.channel} · Seq #{item.sequence_number}</div>

        {item.subject && <p className="text-xs text-slate-400 mb-2">Subject: <span className="text-white">{item.subject}</span></p>}
        {error && <ErrorBanner message={error} className="mb-3" />}

        <label className="block text-sm text-slate-300 mb-1">Body</label>
        <textarea
          className="w-full h-36 rounded-lg bg-slate-900 border border-slate-600 text-slate-100 text-sm p-3 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />

        <div className="flex gap-3 justify-end">
          <button onClick={() => submit("reject")} disabled={loading} className="px-4 py-2 rounded-lg bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30 text-sm disabled:opacity-50">
            Reject
          </button>
          <button onClick={() => submit("approve")} disabled={loading} className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 text-sm disabled:opacity-50 flex items-center gap-2">
            {loading && <Spinner size="sm" />}
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Lead-qualification modal ─────────────────────────────────────────────────

function LeadQualifyModal({
  item,
  tenantId,
  onClose,
  onDone,
}: {
  item: Extract<ApprovalItem, { type: "lead" }>;
  tenantId: string;
  onClose: () => void;
  onDone: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");

  async function submit(decision: "approve" | "reject") {
    setLoading(true);
    setError("");
    try {
      await api.qualifyLead(tenantId, item.id, decision, reason || undefined);
      onDone();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-slate-800 border border-slate-700 rounded-xl w-full max-w-lg p-6 shadow-xl">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-lg font-semibold text-white">Qualify Lead</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">×</button>
        </div>

        <div className="mb-1 text-white font-medium">{item.name ?? item.company ?? item.url}</div>
        <div className="text-xs text-slate-400 mb-1">{item.company} · Score: {item.score ?? "—"}</div>
        {item.rationale && <p className="text-xs text-slate-400 italic mb-4">"{item.rationale}"</p>}

        {error && <ErrorBanner message={error} className="mb-3" />}

        <label className="block text-sm text-slate-300 mb-1">Reason (optional)</label>
        <input
          type="text"
          className="w-full rounded-lg bg-slate-900 border border-slate-600 text-slate-100 text-sm px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          placeholder="Rejection reason or override note"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />

        <div className="flex gap-3 justify-end">
          <button onClick={() => submit("reject")} disabled={loading} className="px-4 py-2 rounded-lg bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30 text-sm disabled:opacity-50">
            Reject
          </button>
          <button onClick={() => submit("approve")} disabled={loading} className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-500 text-sm disabled:opacity-50 flex items-center gap-2">
            {loading && <Spinner size="sm" />}
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Table ────────────────────────────────────────────────────────────────────

export function ApprovalQueueTable({
  approvals,
  tenantId,
  onRefresh,
}: {
  approvals: Approval[];
  tenantId: string;
  onRefresh: () => void;
}) {
  const [selected, setSelected] = useState<ApprovalItem | null>(null);

  if (approvals.length === 0) {
    return <p className="text-center py-12 text-slate-500">No pending approvals — inbox zero!</p>;
  }

  return (
    <>
      {selected?.type === "message" && (
        <MessageApprovalModal
          item={selected}
          tenantId={tenantId}
          onClose={() => setSelected(null)}
          onDone={() => { setSelected(null); onRefresh(); }}
        />
      )}
      {selected?.type === "lead" && (
        <LeadQualifyModal
          item={selected}
          tenantId={tenantId}
          onClose={() => setSelected(null)}
          onDone={() => { setSelected(null); onRefresh(); }}
        />
      )}

      <div className="rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800">
            <tr>
              {["Type", "Subject / Name", "Detail", ""].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {approvals.map((a) => (
              <tr key={a.id} className="bg-slate-800/50 hover:bg-slate-800">
                <td className="px-4 py-3">
                  <Badge label={a.type === "lead" ? "qualified" : "pending_approval"} />
                </td>
                <td className="px-4 py-3 text-slate-200 text-sm">
                  {a.type === "lead"
                    ? (a.name ?? a.company ?? a.url)
                    : (a.subject ?? `seq #${a.sequence_number}`)}
                </td>
                <td className="px-4 py-3 text-xs text-slate-400">
                  {a.type === "lead"
                    ? `Score: ${a.score ?? "—"}`
                    : `${a.channel} · seq #${a.sequence_number}`}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => setSelected(a)}
                    className="text-xs px-3 py-1 rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600/30"
                  >
                    Review
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
