"use client";

import Link from "next/link";
import { useTenants } from "@/hooks/useTenants";
import { TenantCard, TenantCardLoading } from "@/components/tenant/TenantCard";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

export default function DashboardPage() {
  const { tenants, loading, error } = useTenants();

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Tenants</h1>
        <Link
          href="/tenants/new"
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          + New Tenant
        </Link>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="flex flex-col gap-2">
        {loading && ["a", "b", "c"].map((k) => <TenantCardLoading key={k} />)}
        {!loading && tenants.length === 0 && (
          <div className="text-slate-500 text-sm py-8 text-center">
            No tenants yet.{" "}
            <Link href="/tenants/new" className="text-indigo-400 hover:text-indigo-300 underline">
              Create your first tenant
            </Link>{" "}
            to get started.
          </div>
        )}
        {tenants.map((tenant) => (
          <TenantCard key={tenant.id} tenant={tenant} />
        ))}
      </div>
    </div>
  );
}
