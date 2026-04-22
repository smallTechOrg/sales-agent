"use client";

import { useEffect, useRef, useState } from "react";
import { api, type RunData } from "@/lib/api";

const ACTIVE_STATUSES = new Set(["pending", "running"]);
const POLL_INTERVAL_MS = 3000;

export function useRuns(tenantId: string, campaignId: string) {
  const [runs, setRuns] = useState<RunData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    if (!tenantId || !campaignId) return;
    api
      .listRuns(tenantId, campaignId)
      .then((page) => setRuns(page.items))
      .catch((e) => setError(String(e)));
  };

  useEffect(() => {
    if (!tenantId || !campaignId) return;
    setLoading(true);
    api
      .listRuns(tenantId, campaignId)
      .then((page) => setRuns(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId, campaignId]);

  // Poll while any run is active.
  const runsRef = useRef(runs);
  runsRef.current = runs;

  useEffect(() => {
    if (!tenantId || !campaignId) return;
    const hasActive = runsRef.current.some((r) => ACTIVE_STATUSES.has(r.status));
    if (!hasActive) return;

    const id = setInterval(() => {
      api
        .listRuns(tenantId, campaignId)
        .then((page) => setRuns(page.items))
        .catch(() => {});
    }, POLL_INTERVAL_MS);

    return () => clearInterval(id);
  });

  return { runs, loading, error, refresh };
}

export function useRun(
  tenantId: string,
  campaignId: string,
  runId: string | null
) {
  const [run, setRun] = useState<RunData | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    if (!runId) return;

    const poll = () => {
      api
        .getRun(tenantId, campaignId, runId)
        .then((r) => {
          setRun(r);
          if (!ACTIVE_STATUSES.has(r.status)) stop();
        })
        .catch(() => {});
    };

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
    return stop;
  }, [tenantId, campaignId, runId]);

  return run;
}
