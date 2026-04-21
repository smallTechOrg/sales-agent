"use client";

const steps = [
  "Identity",
  "Credentials",
  "Offering",
  "Campaign",
  "Review",
];

export function StepIndicator({ current }: { current: number }) {
  return (
    <ol className="flex items-center gap-2 mb-8">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                done
                  ? "bg-indigo-600 text-white"
                  : active
                  ? "bg-indigo-500 text-white"
                  : "bg-slate-800 text-slate-500"
              }`}
            >
              {done ? "✓" : i + 1}
            </span>
            <span
              className={`text-sm ${active ? "text-white font-semibold" : "text-slate-500"}`}
            >
              {label}
            </span>
            {i < steps.length - 1 && (
              <span className="text-slate-700 mx-1">›</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
