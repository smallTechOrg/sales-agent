"use client";

import { useState, use } from "react";
import { useLeads } from "@/hooks/useLeads";
import { useLinks } from "@/hooks/useLinks";
import { LeadFilterBar, LeadTable } from "@/components/lead/LeadTable";
import { LinksTable } from "@/components/campaign/LinksTable";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

type Tab = "pipeline" | "links";

export default function CampaignLeadPipelinePage({
  params,
}: {
  params: Promise<{ tenantId: string; campaignId: string }>;
}) {
  const { tenantId, campaignId } = use(params);
  const [stage, setStage] = useState("");
  const [tab, setTab] = useState<Tab>("pipeline");

  const { leads, loading: leadsLoading, error: leadsError } = useLeads({ tenantId, campaignId, stage });
  const { links, loading: linksLoading, error: linksError } = useLinks({ tenantId, campaignId });

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-2">Campaign</h1>
      <p className="text-sm text-slate-500 mb-6 font-mono">{campaignId}</p>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 border-b border-slate-800">
        {(["pipeline", "links"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
              tab === t
                ? "border-indigo-500 text-white"
                : "border-transparent text-slate-400 hover:text-slate-300"
            }`}
          >
            {t === "pipeline" ? "Lead Pipeline" : `Links (${links.length})`}
          </button>
        ))}
      </div>

      {tab === "pipeline" && (
        <>
          {leadsError && <ErrorBanner message={leadsError} />}
          <LeadFilterBar stage={stage} onStageChange={setStage} />
          {leadsLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : (
            <LeadTable leads={leads} tenantId={tenantId} />
          )}
        </>
      )}

      {tab === "links" && (
        <>
          {linksError && <ErrorBanner message={linksError} />}
          {linksLoading ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : (
            <LinksTable links={links} />
          )}
        </>
      )}
    </div>
  );
}
