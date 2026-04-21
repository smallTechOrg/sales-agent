"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTenant } from "@/lib/tenant-context";

interface NavItem {
  label: string;
  href: string;
}

export function Sidebar() {
  const pathname = usePathname();
  const { activeTenantId } = useTenant();

  const globalNav: NavItem[] = [{ label: "Home", href: "/" }];

  const tenantNav: NavItem[] = activeTenantId
    ? [
        { label: "Overview", href: `/${activeTenantId}` },
        { label: "Offerings", href: `/${activeTenantId}/offerings` },
        { label: "Approvals", href: `/${activeTenantId}/approvals` },
        { label: "Messages", href: `/${activeTenantId}/messages` },
        { label: "Events", href: `/${activeTenantId}/events` },
        { label: "Settings", href: `/${activeTenantId}/settings` },
      ]
    : [];

  const navLink = ({ label, href }: NavItem) => {
    const active = pathname === href;
    return (
      <Link
        key={href}
        href={href}
        className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
          active
            ? "bg-indigo-700 text-white"
            : "text-slate-400 hover:bg-slate-800 hover:text-white"
        }`}
      >
        {label}
      </Link>
    );
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-slate-900 border-r border-slate-800 flex flex-col p-4 gap-1 z-30">
      <div className="mb-4 px-3 py-2 text-lg font-bold text-white tracking-tight">
        Zer0
      </div>
      <div className="flex flex-col gap-1">
        {globalNav.map(navLink)}
      </div>
      {tenantNav.length > 0 && (
        <>
          <div className="my-3 border-t border-slate-800" />
          <div className="px-3 mb-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Tenant
          </div>
          <div className="flex flex-col gap-1">
            {tenantNav.map(navLink)}
          </div>
        </>
      )}
    </aside>
  );
}
