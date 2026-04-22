"use client";

const variantClass: Record<string, string> = {
  ok: "bg-emerald-900 text-emerald-300",
  degraded: "bg-red-900 text-red-300",
  disabled: "bg-slate-700 text-slate-400",
  active: "bg-indigo-900 text-indigo-300",
  pending: "bg-amber-900 text-amber-300",
  discovered: "bg-slate-700 text-slate-300",
  enriched: "bg-blue-900 text-blue-300",
  qualified: "bg-indigo-900 text-indigo-300",
  approved: "bg-emerald-900 text-emerald-300",
  rejected: "bg-red-900 text-red-300",
  outreach_active: "bg-cyan-900 text-cyan-300",
  responded: "bg-green-900 text-green-300",
  blocked: "bg-rose-900 text-rose-300",
  sent: "bg-emerald-900 text-emerald-300",
  pending_approval: "bg-amber-900 text-amber-300",
  draft: "bg-slate-700 text-slate-300",
  email: "bg-blue-900 text-blue-300",
  whatsapp: "bg-green-900 text-green-300",
};

export function Badge({ label }: { label: string }) {
  const cls = variantClass[label.toLowerCase()] ?? "bg-slate-700 text-slate-300";
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${cls}`}>
      {label}
    </span>
  );
}
