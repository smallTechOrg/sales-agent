"use client";

import type { Lead } from "@/lib/api";

interface ResearchPanelProps {
  lead: Lead;
}

export function ResearchPanel({ lead }: ResearchPanelProps) {
  const hasResearch = lead.research_summary || (lead.signals && lead.signals.length > 0);

  return (
    <section className="bg-slate-800 rounded-xl border border-slate-700 p-5">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-4">
        Research
      </h3>

      {!hasResearch && (
        <p className="text-sm text-slate-500">No research data yet.</p>
      )}

      {lead.signals && lead.signals.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-slate-400 mb-2 uppercase tracking-wide">Buying signals</p>
          <div className="flex flex-wrap gap-2">
            {lead.signals.map((signal, i) => (
              <span
                key={i}
                className="inline-flex items-center rounded-full bg-indigo-900/60 border border-indigo-700 px-2.5 py-0.5 text-xs text-indigo-300"
              >
                {signal}
              </span>
            ))}
          </div>
        </div>
      )}

      {lead.research_summary && (
        <div>
          <p className="text-xs text-slate-400 mb-2 uppercase tracking-wide">Summary</p>
          <div className="space-y-3">
            {lead.research_summary.split("\n\n---\n").map((section, i) => (
              <p key={i} className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                {section.trim()}
              </p>
            ))}
          </div>
        </div>
      )}

      {lead.per_criterion_scores && lead.per_criterion_scores.length > 0 && (
        <div className="mt-4">
          <p className="text-xs text-slate-400 mb-2 uppercase tracking-wide">Per-criterion scores</p>
          <div className="space-y-2">
            {lead.per_criterion_scores.map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-slate-400 w-40 truncate shrink-0">{item.criterion}</span>
                <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full"
                    style={{ width: `${Math.round(item.score)}%` }}
                  />
                </div>
                <span className="text-xs font-mono text-slate-400 w-8 text-right shrink-0">
                  {item.score.toFixed(0)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
