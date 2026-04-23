"use client";

import { useState, use, useEffect } from "react";
import { api, type LinkData } from "@/lib/api";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

const STATUS_BADGE: Record<string, string> = {
  scraped: "bg-green-500/20 text-green-400 border-green-500/30",
  failed: "bg-red-500/20 text-red-400 border-red-500/30",
  blocked: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  pending: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

const SOURCE_LABEL: Record<string, string> = {
  web: "🌐 Web",
  linkedin: "💼 LinkedIn",
  directory: "📚 Directory",
};

const PAGE_TYPE_LABEL: Record<string, string> = {
  company_website: "Company",
  directory_listing: "Directory",
  news_article: "News",
  social_profile: "Social",
  job_board: "Jobs",
  blog_post: "Blog",
  other: "Other",
};

function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_BADGE[status] ?? STATUS_BADGE.pending;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

function LinkDrawer({ link, onClose }: { link: LinkData; onClose: () => void }) {
  const [showFull, setShowFull] = useState(false);

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/40" onClick={onClose} />
      <div className="w-[480px] bg-slate-900 border-l border-slate-700 flex flex-col overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white truncate">Link Detail</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl">×</button>
        </div>
        <div className="p-6 flex flex-col gap-5">
          <div>
            <div className="text-xs text-slate-500 mb-1">URL</div>
            <a href={link.url} target="_blank" rel="noreferrer"
              className="text-indigo-400 hover:underline text-sm break-all">
              {link.url}
            </a>
          </div>

          <div className="flex gap-3 flex-wrap">
            <div>
              <div className="text-xs text-slate-500 mb-1">Source</div>
              <span className="text-sm text-slate-300">{SOURCE_LABEL[link.source] ?? link.source}</span>
            </div>
            <div>
              <div className="text-xs text-slate-500 mb-1">Status</div>
              <StatusBadge status={link.scrape_status} />
            </div>
            {link.page_type && (
              <div>
                <div className="text-xs text-slate-500 mb-1">Type</div>
                <span className="text-sm text-slate-300">{PAGE_TYPE_LABEL[link.page_type] ?? link.page_type}</span>
              </div>
            )}
          </div>

          {link.page_summary && (
            <div>
              <div className="text-xs text-slate-500 mb-1">Summary</div>
              <p className="text-sm text-slate-300">{link.page_summary}</p>
            </div>
          )}

          {link.page_detail && (
            <div>
              <div className="text-xs text-slate-500 mb-1">Detail</div>
              <p className="text-sm text-slate-300 leading-relaxed">{link.page_detail}</p>
            </div>
          )}

          {link.page_excerpt && (
            <div>
              <div className="text-xs text-slate-500 mb-1">Page Excerpt</div>
              <p className="text-sm text-slate-400 font-mono leading-relaxed whitespace-pre-wrap">
                {showFull ? link.page_excerpt : link.page_excerpt.slice(0, 200)}
                {link.page_excerpt.length > 200 && (
                  <button
                    onClick={() => setShowFull(!showFull)}
                    className="ml-2 text-indigo-400 hover:underline text-xs"
                  >
                    {showFull ? "Show less" : "Show more"}
                  </button>
                )}
              </p>
            </div>
          )}

          {link.scraped_at && (
            <div>
              <div className="text-xs text-slate-500 mb-1">Scraped</div>
              <span className="text-sm text-slate-400">{new Date(link.scraped_at).toLocaleString()}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function LinksPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = use(params);
  const [links, setLinks] = useState<LinkData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<LinkData | null>(null);

  useEffect(() => {
    setLoading(true);
    api.listLinks(tenantId)
      .then((page) => setLinks(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId]);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Discovered Links</h1>
        <span className="text-sm text-slate-400">{links.length} links</span>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <div className="flex justify-center py-8"><Spinner /></div>
      ) : (
        <div className="rounded-xl border border-slate-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-800">
              <tr>
                {["Source", "URL", "Type", "Summary", "Status", "Scraped"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {links.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-500">No links discovered yet.</td>
                </tr>
              ) : (
                links.map((lnk) => (
                  <tr
                    key={lnk.id}
                    className="bg-slate-800/50 hover:bg-slate-800 cursor-pointer"
                    onClick={() => setSelected(lnk)}
                  >
                    <td className="px-4 py-3 text-xs text-slate-300">
                      {SOURCE_LABEL[lnk.source] ?? lnk.source}
                    </td>
                    <td className="px-4 py-3 max-w-xs">
                      <a
                        href={lnk.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-400 hover:underline text-xs truncate block max-w-[200px]"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {lnk.url}
                      </a>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {lnk.page_type ? (PAGE_TYPE_LABEL[lnk.page_type] ?? lnk.page_type) : "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400 max-w-xs truncate">
                      {lnk.page_summary ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={lnk.scrape_status} />
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {lnk.scraped_at ? new Date(lnk.scraped_at).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {selected && <LinkDrawer link={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
