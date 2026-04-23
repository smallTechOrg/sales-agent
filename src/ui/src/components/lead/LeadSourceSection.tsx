"use client";

import { useEffect, useState } from "react";
import { api, type LinkData, ApiError } from "@/lib/api";

function sourceIcon(source: string) {
  switch (source) {
    case "linkedin": return "💼";
    case "web": return "🌐";
    case "directory": return "📚";
    default: return "🔗";
  }
}

export function LeadSourceSection({
  tenantId,
  linkId,
}: {
  tenantId: string;
  linkId: string;
}) {
  const [link, setLink] = useState<LinkData | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    api
      .getLink(tenantId, linkId)
      .then(setLink)
      .catch((e: unknown) => {
        if (!(e instanceof ApiError && e.status === 404)) console.error(e);
      });
  }, [tenantId, linkId]);

  if (!link) return null;

  return (
    <section className="bg-slate-800 rounded-xl border border-slate-700 p-5 space-y-3">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Source</h3>
      <div className="flex items-start gap-3 text-sm">
        <span className="text-lg" title={link.source}>{sourceIcon(link.source)}</span>
        <div className="flex-1 min-w-0">
          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-400 hover:underline break-all"
          >
            {link.url}
          </a>
          {link.scraped_at && (
            <p className="text-xs text-slate-500 mt-1">
              Scraped {new Date(link.scraped_at).toLocaleString()}
            </p>
          )}
          {link.page_excerpt && (
            <div className="mt-2">
              <button
                onClick={() => setOpen((v) => !v)}
                className="text-xs text-slate-400 hover:text-white"
              >
                {open ? "▲ Hide excerpt" : "▼ Show page excerpt"}
              </button>
              {open && (
                <pre className="mt-2 text-xs text-slate-400 bg-slate-900 rounded p-3 whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
                  {link.page_excerpt}
                </pre>
              )}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
