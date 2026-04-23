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
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const nextCursorRef = useRef<string | null>(null);

  const fetch = (mode: "replace" | "prepend" = "replace") => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listEvents(tenantId, { campaign_id: campaignId, lead_id: leadId, limit: 200 })
      .then((page) => {
        if (mode !== "prepend") {
          nextCursorRef.current = page.next_cursor;
        }
        setHasMore(page.next_cursor !== null);
        setEvents((current) => {
          if (mode === "replace") {
            return page.items;
          }

          const seen = new Set(page.items.map((event) => event.id));
          const retained = current.filter((event) => !seen.has(event.id));
          return [...page.items, ...retained];
        });
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  const loadMore = () => {
    if (!tenantId || !nextCursorRef.current || loadingMore) return;
    setLoadingMore(true);
    api
      .listEvents(tenantId, {
        campaign_id: campaignId,
        lead_id: leadId,
        cursor: nextCursorRef.current,
        limit: 200,
      })
      .then((page) => {
        nextCursorRef.current = page.next_cursor;
        setHasMore(page.next_cursor !== null);
        setEvents((current) => {
          const seen = new Set(current.map((event) => event.id));
          const older = page.items.filter((event) => !seen.has(event.id));
          return [...current, ...older];
        });
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoadingMore(false));
  };

  useEffect(() => {
    fetch();
    if (poll) {
      intervalRef.current = setInterval(() => fetch("prepend"), 10_000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, campaignId, leadId, poll]);

  return { events, hasMore, loading, loadingMore, error, refresh: fetch, loadMore };
}
