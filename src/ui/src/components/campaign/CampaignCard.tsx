"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { api, type CampaignData } from "@/lib/api";

interface CampaignCardProps {
  campaign: CampaignData;
  tenantId: string;
  onDelete: (id: string) => void;
}

export function CampaignCard({ campaign, tenantId, onDelete }: CampaignCardProps) {
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

  const handleTrigger = async () => {
    setTriggering(true);
    setTriggerError("");
    try {
      await api.triggerCampaign(tenantId, campaign.id);
    } catch (e) {
      setTriggerError(e instanceof Error ? e.message : String(e));
    } finally {
      setTriggering(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    try {
      await api.deleteCampaign(tenantId, campaign.id);
      onDelete(campaign.id);
    } catch (e) {
      setTriggerError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="rounded-lg bg-slate-900 border border-slate-800 px-4 py-3 hover:border-slate-700 transition-colors">
      <div className="flex items-center gap-4">
        <Link
          href={`/${tenantId}/campaigns/${campaign.id}`}
          className="flex-1 min-w-0"
        >
          <div className="font-semibold text-white truncate">{campaign.name}</div>
          <div className="text-xs text-slate-500 font-mono mt-0.5 truncate">{campaign.id}</div>
        </Link>
        <Badge label={campaign.approval_mode ?? "auto"} />
        <Badge label={campaign.status} />

        <div className="flex items-center gap-2">
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="rounded bg-indigo-700 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-600 disabled:opacity-50 flex items-center gap-1"
          >
            {triggering ? <Spinner size="sm" /> : null}
            Run now
          </button>

          <Link
            href={`/${tenantId}/campaigns/${campaign.id}/edit`}
            className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-600"
          >
            Edit
          </Link>

          <button
            onClick={handleDelete}
            className={`rounded px-2 py-1 text-xs ${
              confirmDelete
                ? "bg-red-700 text-white hover:bg-red-600"
                : "bg-slate-700 text-slate-400 hover:text-red-400"
            }`}
          >
            {confirmDelete ? "Confirm delete" : "Delete"}
          </button>
        </div>
      </div>
      {triggerError && (
        <p className="mt-2 text-xs text-red-400">{triggerError}</p>
      )}
    </div>
  );
}
