"use client";

import { useEffect, use } from "react";
import { useTenant } from "@/lib/tenant-context";

export default function TenantLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const { setActiveTenant } = useTenant();

  useEffect(() => {
    setActiveTenant(tenantId);
  }, [tenantId, setActiveTenant]);

  return <>{children}</>;
}
