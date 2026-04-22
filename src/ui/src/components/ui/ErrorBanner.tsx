"use client";

import { useState } from "react";

export function ErrorBanner({ message, className }: { message: string; className?: string }) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;
  return (
    <div className={`flex items-start gap-3 rounded-md bg-red-950 border border-red-800 p-4 text-sm text-red-300 ${className ?? ""}`}>
      <span className="flex-1">{message}</span>
      <button
        onClick={() => setDismissed(true)}
        className="text-red-500 hover:text-red-300 font-bold"
        aria-label="Dismiss"
      >
        ✕
      </button>
    </div>
  );
}
