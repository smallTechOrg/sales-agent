"use client";

import { useEffect, useRef, useState } from "react";
import { api, type EventData } from "@/lib/api";

interface UseEventsParams {
  tenantId: string | null;
  campaignId?: string;
  leadId?: string;
  poll?: boolean;
}

export function useEvents({
  tenantId,
  campaignId,
  leadId,
  poll = false,
}: UseEventsParams) {
  const [events, setEvents] = useState<EventData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetch = () => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listEvents(tenantId, { campaign_id: campaignId, lead_id: leadId })
      .then((page) => setEvents(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetch();
    if (poll) {
      intervalRef.current = setInterval(fetch, 10_000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, campaignId, leadId, poll]);

  return { events, loading, error, refresh: fetch };
}
