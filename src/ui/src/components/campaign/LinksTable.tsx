"use client";

import type { LinkData } from "@/lib/api";

function StatusBadge({ scraped, identified }: { scraped: boolean; identified: boolean }) {
  if (identified) {
    return (
      <span className="inline-flex items-center rounded-full bg-emerald-900/60 border border-emerald-700 px-2 py-0.5 text-xs text-emerald-300">
        identified
      </span>
    );
  }
  if (scraped) {
    return (
      <span className="inline-flex items-center rounded-full bg-indigo-900/60 border border-indigo-700 px-2 py-0.5 text-xs text-indigo-300">
        scraped
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full bg-slate-800 border border-slate-700 px-2 py-0.5 text-xs text-slate-400">
      discovered
    </span>
  );
}

interface LinksTableProps {
  links: LinkData[];
}

export function LinksTable({ links }: LinksTableProps) {
  if (links.length === 0) {
    return (
      <div className="text-slate-500 text-sm py-8 text-center">
        No links discovered yet.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <div className="grid grid-cols-[1fr_auto_auto] gap-4 px-4 py-2 text-xs text-slate-500 uppercase tracking-wide">
        <span>URL</span>
        <span>Source</span>
        <span>Status</span>
      </div>
      {links.map((link) => (
        <div
          key={link.id}
          className="grid grid-cols-[1fr_auto_auto] gap-4 items-center rounded-lg bg-slate-900 border border-slate-800 px-4 py-3"
        >
          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-indigo-400 hover:text-indigo-300 truncate min-w-0"
            title={link.url}
          >
            {link.url}
          </a>
          <span className="text-xs text-slate-500 shrink-0">{link.source}</span>
          <StatusBadge
            scraped={link.scraped_at != null}
            identified={link.identified_at != null}
          />
        </div>
      ))}
    </div>
  );
}
