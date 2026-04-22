"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { ACTIVE_TENANT_KEY, KNOWN_TENANTS_KEY } from "./constants";

interface TenantContextValue {
  activeTenantId: string | null;
  setActiveTenant: (id: string | null) => void;
  knownTenantIds: string[];
  addKnownTenant: (id: string) => void;
  removeKnownTenant: (id: string) => void;
}

const TenantContext = createContext<TenantContextValue>({
  activeTenantId: null,
  setActiveTenant: () => {},
  knownTenantIds: [],
  addKnownTenant: () => {},
  removeKnownTenant: () => {},
});

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);
  const [knownTenantIds, setKnownTenantIds] = useState<string[]>([]);

  useEffect(() => {
    const active = localStorage.getItem(ACTIVE_TENANT_KEY);
    if (active) setActiveTenantId(active);

    const raw = localStorage.getItem(KNOWN_TENANTS_KEY);
    if (raw) {
      try {
        setKnownTenantIds(JSON.parse(raw) as string[]);
      } catch {
        // stale / corrupted value — ignore
      }
    }
  }, []);

  const setActiveTenant = useCallback((id: string | null) => {
    setActiveTenantId(id);
    if (id) {
      localStorage.setItem(ACTIVE_TENANT_KEY, id);
    } else {
      localStorage.removeItem(ACTIVE_TENANT_KEY);
    }
  }, []);

  const addKnownTenant = useCallback((id: string) => {
    setKnownTenantIds((prev) => {
      if (prev.includes(id)) return prev;
      const next = [...prev, id];
      localStorage.setItem(KNOWN_TENANTS_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const removeKnownTenant = useCallback((id: string) => {
    setKnownTenantIds((prev) => {
      const next = prev.filter((t) => t !== id);
      localStorage.setItem(KNOWN_TENANTS_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return (
    <TenantContext.Provider
      value={{
        activeTenantId,
        setActiveTenant,
        knownTenantIds,
        addKnownTenant,
        removeKnownTenant,
      }}
    >
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
