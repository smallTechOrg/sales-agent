"use client";

import { useState, use, useEffect } from "react";
import { useLeads } from "@/hooks/useLeads";
import { useLinks } from "@/hooks/useLinks";
import { useRuns, useRun } from "@/hooks/useRuns";
import { useEvents } from "@/hooks/useEvents";
import { useCampaignStats } from "@/hooks/useCampaignStats";
import { LeadFilterBar, LeadTable } from "@/components/lead/LeadTable";
import { LinksTable } from "@/components/campaign/LinksTable";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import { api, type RunData, type EventData } from "@/lib/api";

type Tab = "pipeline" | "activity" | "runs";

// ── Agent node pipeline (ordered) ──────────────────────────────────────────
const NODES = [
  { key: "resolve_config", label: "Config" },
  { key: "discover", label: "Discover" },
  { key: "scrape_links", label: "Scrape" },
  { key: "identify_leads", label: "Identify" },
  { key: "research", label: "Research" },
  { key: "qualify", label: "Qualify" },
  { key: "get_contacts", label: "Contacts" },
  { key: "approval_gate", label: "Approval" },
  { key: "outreach", label: "Outreach" },
  { key: "check_replies", label: "Replies" },
];

type NodeStatus = "completed" | "active" | "failed" | "pending";

function getNodeStatus(nodeKey: string, run: RunData): NodeStatus {
  const idx = NODES.findIndex((n) => n.key === nodeKey);
  const curIdx = run.current_node
    ? NODES.findIndex((n) => n.key === run.current_node)
    : -1;

  if (run.status === "completed") return "completed";
  if (run.status === "failed" || run.status === "interrupted") {
    if (idx < curIdx) return "completed";
    if (idx === curIdx) return "failed";
    return "pending";
  }
  if (run.status === "running" || run.status === "pending") {
    if (idx < curIdx) return "completed";
    if (idx === curIdx) return "active";
    return "pending";
  }
  return "pending";
}

function NodePipeline({ run }: { run: RunData }) {
  return (
    <div className="flex items-center gap-1 flex-wrap py-3">
      {NODES.map((node, i) => {
        const st = getNodeStatus(node.key, run);
        const dot =
          st === "completed" ? "bg-green-500" :
          st === "active" ? "bg-blue-500 animate-pulse" :
          st === "failed" ? "bg-red-500" :
          "bg-slate-700";
        const text =
          st === "completed" ? "text-green-400" :
          st === "active" ? "text-blue-300" :
          st === "failed" ? "text-red-400" :
          "text-slate-600";
        return (
          <div key={node.key} className="flex items-center gap-1">
            <div className="flex flex-col items-center gap-1">
              <div className={`w-2.5 h-2.5 rounded-full ${dot}`} />
              <span className={`text-[10px] font-medium ${text}`}>{node.label}</span>
            </div>
            {i < NODES.length - 1 && (
              <div className={`w-4 h-px mb-3 ${st === "completed" ? "bg-green-700" : "bg-slate-700"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Status badge ───────────────────────────────────────────────────────────
const STATUS_COLORS: Record<string, string> = {
  pending: "text-yellow-400 bg-yellow-400/10",
  running: "text-blue-400 bg-blue-400/10",
  completed: "text-green-400 bg-green-400/10",
  failed: "text-red-400 bg-red-400/10",
  interrupted: "text-orange-400 bg-orange-400/10",
};

function RunStatusBadge({ status }: { status: string }) {
  const cls = STATUS_COLORS[status] ?? "text-slate-400 bg-slate-400/10";
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${cls}`}>
      {status}
    </span>
  );
}

function fmtDuration(start: string | null, end: string | null): string {
  if (!start) return "—";
  const s = new Date(start).getTime();
  const e = end ? new Date(end).getTime() : Date.now();
  const secs = Math.round((e - s) / 1000);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  return `${mins}m ${secs % 60}s`;
}

// ── Event descriptions ─────────────────────────────────────────────────────
function eventLabel(ev: EventData): string {
  const labels: Record<string, string> = {
    "link.discovered": "🔗 Link discovered",
    "lead.identified": "👤 Lead identified",
    "lead.researched": "🔍 Lead researched",
    "lead.qualified": "✅ Lead qualified",
    "lead.rejected": "❌ Lead rejected",
    "lead.contacts_found": "📇 Contacts found",
    "contact.discovered": "📇 Contact discovered",
    "approval.granted": "✅ Approval granted",
    "approval.pending": "⏳ Approval pending",
    "message.drafted": "✏️ Message drafted",
    "message.sent": "📨 Message sent",
    "message.pending_approval": "⏳ Message awaiting approval",
    "handoff.triggered": "🤝 Handoff triggered",
    "outreach.exhausted": "🚫 Outreach exhausted",
    "run.error": "💥 Run error",
  };
  return labels[ev.event_type] ?? ev.event_type;
}

// ── Stats bar ──────────────────────────────────────────────────────────────
function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col items-center rounded-lg bg-slate-900 border border-slate-800 px-5 py-3 min-w-[80px]">
      <span className="text-xl font-bold text-white">{value}</span>
      <span className="text-xs text-slate-500 mt-0.5">{label}</span>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function CampaignLeadPipelinePage({
  params,
}: {
  params: Promise<{ tenantId: string; campaignId: string }>;
}) {
  const { tenantId, campaignId } = use(params);
  const [stage, setStage] = useState("");
  const [tab, setTab] = useState<Tab>("pipeline");
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  const isRunning = !!activeRunId;

  const { leads, hasMore: leadsHasMore, loading: leadsLoading, error: leadsError } = useLeads({ tenantId, campaignId, stage });
  const { links, loading: linksLoading, error: linksError } = useLinks({ tenantId, campaignId });
  const { runs, loading: runsLoading, error: runsError, refresh: refreshRuns } = useRuns(tenantId, campaignId);
  const activeRun = useRun(tenantId, campaignId, activeRunId);
  const { stats, refresh: refreshStats } = useCampaignStats(tenantId, campaignId, isRunning);
  const { events, hasMore: eventsHasMore, loading: eventsLoading } = useEvents({ tenantId, campaignId, poll: isRunning });

  // Index leads and links for activity enrichment
  const leadMap = Object.fromEntries(leads.map((l) => [l.id, l]));
  const linkMap = Object.fromEntries(links.map((l) => [l.id, l]));

  const handleRunNow = async () => {
    setTriggering(true);
    setTriggerError(null);
    try {
      const result = await api.triggerCampaign(tenantId, campaignId);
      setActiveRunId(result.run_id);
      setTab("runs");
      refreshRuns();
      refreshStats();
    } catch (e) {
      setTriggerError(String(e));
    } finally {
      setTriggering(false);
    }
  };

  // Clear active run once it finishes and refresh data.
  useEffect(() => {
    if (
      activeRun &&
      (activeRun.status === "completed" ||
        activeRun.status === "failed" ||
        activeRun.status === "interrupted")
    ) {
      setActiveRunId(null);
      refreshRuns();
      refreshStats();
    }
  }, [activeRun?.status]);

  // Chronological events for activity feed (API returns newest-first → reverse)
  const chronoEvents = [...events].reverse();

  return (
    <div className="max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-2xl font-bold text-white">Campaign</h1>
        <button
          onClick={handleRunNow}
          disabled={triggering || isRunning}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {triggering ? "Queuing…" : isRunning ? "Running…" : "▶ Run Now"}
        </button>
      </div>
      <p className="text-sm text-slate-500 mb-4 font-mono">{campaignId}</p>

      {triggerError && <ErrorBanner message={triggerError} />}

      {/* Stats bar */}
      {stats && (
        <div className="flex gap-3 mb-4 flex-wrap">
          <StatCard label="URLs found" value={stats.total_links} />
          <StatCard label="Leads" value={stats.total_leads} />
          <StatCard label="Sent" value={stats.messages_sent} />
          <StatCard label="Replies" value={stats.replies_received} />
        </div>
      )}

      {/* Active run progress */}
      {activeRun && (activeRun.status === "pending" || activeRun.status === "running") && (
        <div className="mb-4 rounded-md border border-blue-500/30 bg-blue-500/10 px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-blue-300 mb-2">
            <Spinner />
            <span>
              Run <span className="font-mono text-xs">{activeRun.id.slice(0, 8)}</span>
              {" — "}<RunStatusBadge status={activeRun.status} />
            </span>
          </div>
          <NodePipeline run={activeRun} />
        </div>
      )}

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 border-b border-slate-800">
        {(["pipeline", "activity", "runs"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
              tab === t
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-300"
            }`}
          >
            {t === "pipeline"
              ? `Pipeline (${stats?.total_leads ?? leads.length}${leadsHasMore ? "+" : ""})`
              : t === "activity"
              ? `Activity (${events.length}${eventsHasMore ? "+" : ""})`
              : `Runs (${runs.length})`}
          </button>
        ))}
      </div>

      {/* ── Pipeline tab ── */}
      {tab === "pipeline" && (
        <>
          {leadsError && <ErrorBanner message={leadsError} />}
          <LeadFilterBar
            stage={stage}
            onStageChange={setStage}
            stageCounts={stats?.by_stage}
          />
          {leadsLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : (
            <LeadTable leads={leads} tenantId={tenantId} />
          )}
          {/* Discovered URLs section below pipeline */}
          <div className="mt-8">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Discovered URLs ({links.length})
              </h3>
            </div>
            <p className="text-xs text-slate-600 mb-3">
              These are the web pages the agent found and scraped. Each URL is evaluated to identify whether a lead exists at that company.
            </p>
            {linksError && <ErrorBanner message={linksError} />}
            {linksLoading ? (
              <div className="flex justify-center py-4"><Spinner /></div>
            ) : (
              <LinksTable links={links} />
            )}
          </div>
        </>
      )}

      {/* ── Activity tab ── */}
      {tab === "activity" && (
        <>
          {isRunning && (
            <p className="text-xs text-blue-400 mb-3 flex items-center gap-1">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              Live — updating every 10 s
            </p>
          )}
          {eventsHasMore && (
            <p className="text-xs text-yellow-500 mb-3">
              Showing first 200 events. Use the API for full history.
            </p>
          )}
          {eventsLoading && events.length === 0 ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : chronoEvents.length === 0 ? (
            <p className="text-slate-500 text-sm py-8 text-center">
              No activity yet. Trigger a run to see the agent at work.
            </p>
          ) : (
            <div className="relative border-l border-slate-800 ml-3 pl-6 flex flex-col gap-4">
              {chronoEvents.map((ev) => {
                const p = ev.payload ?? {};
                const lead = ev.lead_id ? leadMap[ev.lead_id] : null;
                const companyName = (p.company_name as string) ?? lead?.company_name ?? null;
                const domain = (p.domain as string) ?? lead?.domain ?? null;
                const url = (p.url as string) ?? null;
                const score = p.score != null ? Number(p.score) : lead?.score ?? null;

                // Dot colour by event type
                const dotColor =
                  ev.event_type === "lead.rejected" ? "bg-red-500 border-red-600" :
                  ev.event_type === "lead.qualified" ? "bg-green-500 border-green-600" :
                  ev.event_type === "lead.identified" ? "bg-indigo-500 border-indigo-600" :
                  ev.event_type === "lead.contacts_found" ? "bg-purple-500 border-purple-600" :
                  ev.event_type === "link.discovered" ? "bg-cyan-500 border-cyan-600" :
                  ev.event_type.startsWith("message.") ? "bg-yellow-500 border-yellow-600" :
                  "bg-slate-700 border-slate-600";

                return (
                  <div key={ev.id} className="relative">
                    <span className={`absolute -left-[1.625rem] top-1 w-2.5 h-2.5 rounded-full border ${dotColor}`} />
                    <div className="text-sm text-white font-medium">{eventLabel(ev)}</div>

                    {/* Entity line: company + domain */}
                    {(companyName || domain) && (
                      <div className="text-xs text-slate-300 mt-0.5">
                        {companyName && <span className="font-medium">{companyName}</span>}
                        {companyName && domain && <span className="text-slate-500"> · </span>}
                        {domain && <span className="font-mono text-slate-400">{domain}</span>}
                      </div>
                    )}

                    {/* Source URL for link events */}
                    {url && (
                      <div className="text-xs text-slate-500 mt-0.5 truncate max-w-sm">
                        <a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-indigo-400">{url}</a>
                      </div>
                    )}

                    {/* Rejection reason */}
                    {ev.event_type === "lead.rejected" && (lead?.rejection_reason || lead?.rationale) && (
                      <div className="mt-1 text-xs text-red-300 bg-red-900/20 rounded px-2 py-1">
                        {lead.rejection_reason ?? lead.rationale}
                      </div>
                    )}

                    {/* Score for qualified / rejected */}
                    {(ev.event_type === "lead.qualified" || ev.event_type === "lead.rejected") && score != null && (
                      <div className="text-xs text-slate-500 mt-0.5">Score: <span className="text-slate-300">{score}</span></div>
                    )}

                    {/* Contacts count */}
                    {ev.event_type === "lead.contacts_found" && p.count != null && (
                      <div className="text-xs text-slate-400 mt-0.5">{p.count as number} contact{(p.count as number) !== 1 ? "s" : ""} found</div>
                    )}

                    {/* Source URL the lead was extracted from (lead.identified has link_id) */}
                    {ev.event_type === "lead.identified" && p.link_id && linkMap[p.link_id as string] && (
                      <div className="text-xs text-slate-500 mt-0.5 truncate max-w-sm">
                        From: <a href={linkMap[p.link_id as string].url} target="_blank" rel="noopener noreferrer" className="font-mono hover:text-indigo-400">{linkMap[p.link_id as string].url}</a>
                      </div>
                    )}

                    <div className="text-xs text-slate-600 mt-0.5">
                      {new Date(ev.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* ── Runs tab ── */}
      {tab === "runs" && (
        <>
          {runsError && <ErrorBanner message={runsError} />}
          {runsLoading ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : runs.length === 0 ? (
            <p className="text-slate-500 text-sm py-8 text-center">
              No runs yet. Click <strong className="text-white">▶ Run Now</strong> to trigger a run.
            </p>
          ) : (
            <div className="flex flex-col gap-4">
              {runs.map((r) => (
                <div key={r.id} className="rounded-md border border-slate-800 bg-slate-900 p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="font-mono text-xs text-slate-500">{r.id.slice(0, 8)}</span>
                    <RunStatusBadge status={r.status} />
                    <span className="text-xs text-slate-500 ml-auto">{fmtDuration(r.started_at, r.finished_at)}</span>
                    <span className="text-xs text-slate-600">
                      {r.started_at ? new Date(r.started_at).toLocaleString() : "—"}
                    </span>
                  </div>
                  <NodePipeline run={r} />
                  {r.error && (
                    <p className="mt-2 text-xs text-red-400 bg-red-900/20 rounded px-3 py-2">{r.error}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
