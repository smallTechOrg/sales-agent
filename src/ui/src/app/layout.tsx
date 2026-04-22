import type { Metadata } from "next";
import "./globals.css";
import { TenantProvider } from "@/lib/tenant-context";
import { TopBar } from "@/components/layout/TopBar";
import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "Zer0 — Sales Agent Dashboard",
  description: "Operator dashboard for the Zer0 autonomous sales agent.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 antialiased">
        <TenantProvider>
          <Sidebar />
          <TopBar />
          <main className="ml-56 mt-14 min-h-screen p-6">{children}</main>
        </TenantProvider>
      </body>
    </html>
  );
}
