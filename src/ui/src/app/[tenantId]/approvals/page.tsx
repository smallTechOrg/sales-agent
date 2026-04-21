"use client";

import { use } from "react";
import { useApprovals } from "@/hooks/useApprovals";
import { ApprovalQueueTable } from "@/components/approval/ApprovalQueueTable";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

export default function ApprovalsPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const { approvals, loading, error, refresh } = useApprovals(tenantId);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Approval Queue</h1>
          {!loading && (
            <p className="text-sm text-slate-500 mt-1">
              {approvals.length} pending
            </p>
          )}
        </div>
        <button
          onClick={refresh}
          className="text-sm px-3 py-1.5 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 border border-slate-600"
        >
          Refresh
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <ApprovalQueueTable
          approvals={approvals}
          tenantId={tenantId}
          onRefresh={refresh}
        />
      )}
    </div>
  );
}
