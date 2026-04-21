// API base URL and local storage keys
// Port 8001 is the default because macOS CoreSimulator (Xcode) occupies 8000.
// Override with NEXT_PUBLIC_API_URL in src/ui/.env.local if needed.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export const KNOWN_TENANTS_KEY = "zer0:knownTenants";
export const ACTIVE_TENANT_KEY = "zer0:activeTenant";
