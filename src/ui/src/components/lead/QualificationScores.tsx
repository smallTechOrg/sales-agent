"use client";

import { type Lead } from "@/lib/api";

function ScoreBar({ value }: { value: number | null | undefined }) {
  const pct = value != null ? Math.round(value) : null;
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        {pct != null && (
          <div
            className="h-full bg-indigo-500 rounded-full"
            style={{ width: `${pct}%` }}
          />
        )}
      </div>
      <span className="text-sm text-white w-10 text-right font-mono">
        {value != null ? value.toFixed(1) : "—"}
      </span>
    </div>
  );
}

export function QualificationScores({ lead }: { lead: Lead }) {
  return (
    <section className="bg-slate-800 rounded-xl border border-slate-700 p-5">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-4">
        Qualification Score
      </h3>

      {lead.score == null ? (
        <p className="text-sm text-slate-500">Not yet scored.</p>
      ) : (
        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-1">
            <span>Score</span>
            <span>/ 100</span>
          </div>
          <ScoreBar value={lead.score} />
        </div>
      )}

      {lead.rationale && (
        <p className="mt-4 text-xs text-slate-400 italic">"{lead.rationale}"</p>
      )}

      {lead.rejection_reason && (
        <p className="mt-2 text-xs text-red-400">Rejected: {lead.rejection_reason}</p>
      )}
    </section>
  );
}
