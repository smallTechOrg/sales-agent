"use client";

import { useEffect, useRef, useState } from "react";
import { api, type LeadData } from "@/lib/api";

interface UseLeadsParams {
  tenantId: string | null;
  campaignId?: string;
  stage?: string;
}

export function useLeads({ tenantId, campaignId, stage }: UseLeadsParams) {
  const [leads, setLeads] = useState<LeadData[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetch = () => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listLeads(tenantId, { campaign_id: campaignId, stage, limit: 200 })
      .then((page) => { setLeads(page.items); setHasMore(page.next_cursor !== null); })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetch();
    // Poll every 10 seconds for live run feedback
    intervalRef.current = setInterval(fetch, 10_000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, campaignId, stage]);

  return { leads, hasMore, loading, error, refresh: fetch };
}
