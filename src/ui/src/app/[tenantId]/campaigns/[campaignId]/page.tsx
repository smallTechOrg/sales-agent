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
import { api, type RunData, type RunEventSummary, type EventData, type LeadData, type LinkData } from "@/lib/api";

type Tab = "pipeline" | "activity" | "runs";

// ── Agent progress stages shown to operators ───────────────────────────────
const PROGRESS_NODES = [
  { key: "discover", label: "Discover" },
  { key: "scrape_links", label: "Scrape" },
  { key: "identify_leads", label: "Identify" },
  { key: "research", label: "Research" },
  { key: "qualify", label: "Qualify" },
 ] as const;

const QUALIFY_STAGE_INDEX = PROGRESS_NODES.findIndex((node) => node.key === "qualify");

function getProgressNodeIndex(currentNode: string | null): number {
  if (!currentNode || currentNode === "resolve_config") {
    return -1;
  }

  const visibleIndex = PROGRESS_NODES.findIndex((node) => node.key === currentNode);
  if (visibleIndex >= 0) {
    return visibleIndex;
  }

  return QUALIFY_STAGE_INDEX;
}

type NodeStatus = "completed" | "active" | "failed" | "pending";

function getNodeStatus(nodeKey: string, run: RunData): NodeStatus {
  const idx = PROGRESS_NODES.findIndex((node) => node.key === nodeKey);
  const curIdx = getProgressNodeIndex(run.current_node);

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
      {PROGRESS_NODES.map((node, i) => {
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
            {i < PROGRESS_NODES.length - 1 && (
              <div className={`w-4 h-px mb-3 ${st === "completed" ? "bg-green-700" : "bg-slate-700"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Per-stage counts pulled from run event summary ─────────────────────────

const STAGE_GROUPS: { label: string; events: string[]; icon: string }[] = [
  { label: "Links found",    events: ["link.discovered"],              icon: "🔗" },
  { label: "Leads ID'd",     events: ["lead.identified"],              icon: "🏢" },
  { label: "Researched",     events: ["lead.researched"],              icon: "🔬" },
  { label: "Qualified",      events: ["lead.qualified"],               icon: "✅" },
  { label: "Rejected",       events: ["lead.rejected"],                icon: "❌" },
  { label: "People found",   events: ["person.discovered"],            icon: "👤" },
  { label: "Pending review", events: ["approval.pending"],             icon: "⏳" },
  { label: "Approved",       events: ["approval.granted"],             icon: "👍" },
  { label: "Msgs sent",      events: ["message.sent"],                 icon: "📧" },
  { label: "Msgs queued",    events: ["message.pending_approval"],     icon: "📋" },
];

function sumCounts(counts: Record<string, number>, events: string[]): number {
  return events.reduce((acc, e) => acc + (counts[e] ?? 0), 0);
}

function RunStageCounts({
  tenantId,
  campaignId,
  run,
}: {
  tenantId: string;
  campaignId: string;
  run: RunData;
}) {
  const [summary, setSummary] = useState<RunEventSummary | null>(null);

  useEffect(() => {
    api
      .getRunEventSummary(tenantId, campaignId, run.id)
      .then(setSummary)
      .catch(() => {/* silently ignore — no events yet */});
  }, [tenantId, campaignId, run.id]);

  if (!summary) return null;

  const active = STAGE_GROUPS.filter(
    (g) => sumCounts(summary.counts, g.events) > 0
  );
  if (active.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
      {active.map((g) => {
        const n = sumCounts(summary.counts, g.events);
        return (
          <span key={g.label} className="flex items-center gap-1 text-xs text-slate-400">
            <span>{g.icon}</span>
            <span className="font-mono text-white">{n}</span>
            <span>{g.label}</span>
          </span>
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
    "lead.people_found": "📇 People found",
    "person.discovered": "📇 Person discovered",
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

function ActivityEventItem({
  event,
  leadMap,
  linkMap,
}: {
  event: EventData;
  leadMap: Record<string, LeadData>;
  linkMap: Record<string, LinkData>;
}) {
  const payload = event.payload ?? {};
  const lead = event.lead_id ? leadMap[event.lead_id] : null;
  const companyName =
    (typeof payload.company_name === "string" ? payload.company_name : null) ??
    lead?.company_name ??
    null;
  const domain =
    (typeof payload.domain === "string" ? payload.domain : null) ??
    lead?.domain ??
    null;
  const url = typeof payload.url === "string" ? payload.url : null;
  const score =
    payload.score != null ? Number(payload.score) : lead?.score ?? null;
  const rejectionText = lead?.rejection_reason ?? lead?.rationale ?? "";
  const showRejectionReason =
    event.event_type === "lead.rejected" && rejectionText.length > 0;
  const contactCount = typeof payload.count === "number" ? payload.count : null;
  const identifiedLinkId = typeof payload.link_id === "string" ? payload.link_id : null;

  const dotColor =
    event.event_type === "lead.rejected" ? "bg-red-500 border-red-600" :
    event.event_type === "lead.qualified" ? "bg-green-500 border-green-600" :
    event.event_type === "lead.identified" ? "bg-indigo-500 border-indigo-600" :
    event.event_type === "lead.people_found" ? "bg-purple-500 border-purple-600" :
    event.event_type === "link.discovered" ? "bg-cyan-500 border-cyan-600" :
    event.event_type.startsWith("message.") ? "bg-yellow-500 border-yellow-600" :
    "bg-slate-700 border-slate-600";

  return (
    <div className="relative">
      <span className={`absolute -left-[1.625rem] top-1 w-2.5 h-2.5 rounded-full border ${dotColor}`} />
      <div className="text-sm text-white font-medium">{eventLabel(event)}</div>

      {(companyName || domain) && (
        <div className="text-xs text-slate-300 mt-0.5">
          {companyName && <span className="font-medium">{companyName}</span>}
          {companyName && domain && <span className="text-slate-500"> · </span>}
          {domain && <span className="font-mono text-slate-400">{domain}</span>}
        </div>
      )}

      {url && (
        <div className="text-xs text-slate-500 mt-0.5 truncate max-w-sm">
          <a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-indigo-400">{url}</a>
        </div>
      )}

      {showRejectionReason && (
        <div className="mt-1 text-xs text-red-300 bg-red-900/20 rounded px-2 py-1">
          {rejectionText}
        </div>
      )}

      {(event.event_type === "lead.qualified" || event.event_type === "lead.rejected") && score != null && (
        <div className="text-xs text-slate-500 mt-0.5">Score: <span className="text-slate-300">{score}</span></div>
      )}

      {event.event_type === "lead.people_found" && contactCount != null && (
        <div className="text-xs text-slate-400 mt-0.5">{contactCount} people found</div>
      )}

      {event.event_type === "lead.identified" && identifiedLinkId && linkMap[identifiedLinkId] && (
        <div className="text-xs text-slate-500 mt-0.5 truncate max-w-sm">
          From: <a href={linkMap[identifiedLinkId].url} target="_blank" rel="noopener noreferrer" className="font-mono hover:text-indigo-400">{linkMap[identifiedLinkId].url}</a>
        </div>
      )}

      <div className="text-xs text-slate-600 mt-0.5">
        {new Date(event.created_at).toLocaleTimeString()}
      </div>
    </div>
  );
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
  const {
    events,
    hasMore: eventsHasMore,
    loading: eventsLoading,
    loadingMore: eventsLoadingMore,
    loadMore: loadMoreEvents,
  } = useEvents({ tenantId, campaignId, poll: isRunning });

  // Index leads and links for activity enrichment
  const leadMap: Record<string, LeadData> = Object.fromEntries(
    leads.map((lead) => [lead.id, lead])
  );
  const linkMap: Record<string, LinkData> = Object.fromEntries(
    links.map((link) => [link.id, link])
  );

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
          <p className="text-xs text-blue-200/80 mb-2">
            Progress stops at qualification. Approved leads move into operator review after this point.
          </p>
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
              Showing the latest {events.length} events. Load older events below.
            </p>
          )}
          {eventsLoading && events.length === 0 ? (
            <div className="flex justify-center py-8"><Spinner /></div>
          ) : events.length === 0 ? (
            <p className="text-slate-500 text-sm py-8 text-center">
              No activity yet. Trigger a run to see the agent at work.
            </p>
          ) : (
            <>
              <div className="relative border-l border-slate-800 ml-3 pl-6 flex flex-col gap-4">
                {events.map((event) => (
                  <ActivityEventItem
                    key={event.id}
                    event={event}
                    leadMap={leadMap}
                    linkMap={linkMap}
                  />
                ))}
              </div>
              {eventsHasMore && (
                <div className="mt-4 flex justify-center">
                  <button
                    onClick={loadMoreEvents}
                    disabled={eventsLoadingMore}
                    className="rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {eventsLoadingMore ? "Loading older events…" : "Load older events"}
                  </button>
                </div>
              )}
            </>
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
                  <RunStageCounts tenantId={tenantId} campaignId={campaignId} run={r} />
                  {(r.total_tokens > 0 || r.llm_call_count > 0) && (
                    <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
                      <span>{r.llm_call_count} LLM calls</span>
                      <span>{r.total_tokens.toLocaleString()} tokens ({r.input_tokens.toLocaleString()} in / {r.output_tokens.toLocaleString()} out)</span>
                      <span className="text-emerald-400">${r.estimated_cost_usd.toFixed(6)}</span>
                    </div>
                  )}
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
