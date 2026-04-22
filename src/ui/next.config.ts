import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Note: output:'export' deferred — dynamic [tenantId]/[campaignId]/[leadId] routes
  // require generateStaticParams with known IDs at build time, which is incompatible
  // with runtime-discovered tenants. Re-enable when "zer0 ui" CLI phase adds
  // a build-time param generator or switches to a different serving strategy.
  trailingSlash: true,
};

export default nextConfig;
