// API base URL and local storage keys

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const KNOWN_TENANTS_KEY = "zer0:knownTenants";
export const ACTIVE_TENANT_KEY = "zer0:activeTenant";
