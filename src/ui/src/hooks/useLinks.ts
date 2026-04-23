"use client";

import { useEffect, useRef, useState } from "react";
import { api, type LinkData } from "@/lib/api";

interface UseLinksParams {
  tenantId: string | null;
  campaignId?: string;
}

export function useLinks({ tenantId, campaignId }: UseLinksParams) {
  const [links, setLinks] = useState<LinkData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetch = () => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listLinks(tenantId, campaignId)
      .then((page) => setLinks(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetch();
    intervalRef.current = setInterval(fetch, 10_000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, campaignId]);

  return { links, loading, error, refresh: fetch };
}
