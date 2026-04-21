"use client";

import { use } from "react";
import Link from "next/link";
import { useOfferings } from "@/hooks/useOfferings";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

function ConfigPill({ label, values }: { label: string; values: string[] }) {
  if (!values.length) return null;
  return (
    <div className="flex gap-1.5 items-center flex-wrap">
      <span className="text-xs text-slate-500 w-24 shrink-0">{label}</span>
      <div className="flex gap-1 flex-wrap">
        {values.slice(0, 4).map((v) => (
          <span key={v} className="rounded bg-slate-700 px-1.5 py-0.5 text-xs text-slate-300">
            {v}
          </span>
        ))}
        {values.length > 4 && (
          <span className="text-xs text-slate-500">+{values.length - 4} more</span>
        )}
      </div>
    </div>
  );
}

export default function OfferingsPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const { offerings, loading, error } = useOfferings(tenantId);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Offerings</h1>
        <Link
          href={`/${tenantId}/offerings/new`}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
        >
          + New Offering
        </Link>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading && (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      )}

      {!loading && offerings.length === 0 && (
        <div className="text-slate-500 text-sm py-8 text-center">
          No offerings yet.{" "}
          <Link href={`/${tenantId}/offerings/new`} className="text-indigo-400 hover:underline">
            Create the first one.
          </Link>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {offerings.map((o) => {
          const disc = o.discovery_config as Record<string, unknown> | null;
          const icp = o.icp as Record<string, unknown> | null;
          const qual = o.qualification_config as Record<string, unknown> | null;
          const out = o.outreach_config as Record<string, unknown> | null;

          const sources = (disc?.sources as string[]) ?? [];
          const roles = (icp?.target_roles as string[]) ?? [];
          const industries = (icp?.target_industries as string[]) ?? [];
          const channels = (out?.channels_enabled as string[]) ?? [];
          const threshold = qual?.score_threshold as number | undefined;
          const queries = (disc?.query_templates as string[]) ?? [];

          const isConfigured = sources.length > 0 && queries.length > 0;

          return (
            <div
              key={o.id}
              className="rounded-lg bg-slate-900 border border-slate-800 p-4 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="font-semibold text-white">{o.name}</h2>
                    {!isConfigured && (
                      <span className="rounded bg-amber-900/60 border border-amber-700 px-1.5 py-0.5 text-xs text-amber-300">
                        Incomplete — edit to configure
                      </span>
                    )}
                  </div>
                  {o.value_proposition && (
                    <p className="text-sm text-slate-400 mb-3 line-clamp-2">{o.value_proposition}</p>
                  )}

                  <div className="flex flex-col gap-1.5">
                    <ConfigPill label="Discovery" values={sources} />
                    <ConfigPill label="Roles" values={roles} />
                    <ConfigPill label="Industries" values={industries} />
                    <ConfigPill label="Channels" values={channels} />
                    {threshold !== undefined && (
                      <div className="flex gap-1.5 items-center">
                        <span className="text-xs text-slate-500 w-24 shrink-0">Score threshold</span>
                        <span className="text-xs text-slate-300">{threshold}</span>
                      </div>
                    )}
                    {queries.length > 0 && (
                      <div className="flex gap-1.5 items-start">
                        <span className="text-xs text-slate-500 w-24 shrink-0 mt-0.5">Queries</span>
                        <div className="flex flex-col gap-0.5">
                          {queries.slice(0, 2).map((q, i) => (
                            <span key={i} className="text-xs text-slate-400 font-mono">{q}</span>
                          ))}
                          {queries.length > 2 && (
                            <span className="text-xs text-slate-500">+{queries.length - 2} more</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex flex-col gap-2 shrink-0">
                  <Link
                    href={`/${tenantId}/offerings/${o.id}/edit`}
                    className="rounded bg-indigo-700 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-600 text-center"
                  >
                    Edit config
                  </Link>
                  <span className="text-xs text-slate-600 font-mono text-center">{o.id.slice(0, 8)}…</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
