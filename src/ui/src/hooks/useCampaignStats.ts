"use client";

import { useEffect, useRef, useState } from "react";
import { api, type CampaignStats } from "@/lib/api";

const POLL_MS = 8000;

export function useCampaignStats(
  tenantId: string,
  campaignId: string,
  poll = false
) {
  const [stats, setStats] = useState<CampaignStats | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = () => {
    if (!tenantId || !campaignId) return;
    api
      .getCampaignStats(tenantId, campaignId)
      .then(setStats)
      .catch(() => {});
  };

  useEffect(() => {
    refresh();
    if (poll) {
      intervalRef.current = setInterval(refresh, POLL_MS);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, campaignId, poll]);

  return { stats, refresh };
}
