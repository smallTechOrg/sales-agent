"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { ACTIVE_TENANT_KEY } from "./constants";

interface TenantContextValue {
  activeTenantId: string | null;
  setActiveTenant: (id: string | null) => void;
}

const TenantContext = createContext<TenantContextValue>({
  activeTenantId: null,
  setActiveTenant: () => {},
});

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);

  useEffect(() => {
    const active = localStorage.getItem(ACTIVE_TENANT_KEY);
    if (active) setActiveTenantId(active);
  }, []);

  const setActiveTenant = useCallback((id: string | null) => {
    setActiveTenantId(id);
    if (id) {
      localStorage.setItem(ACTIVE_TENANT_KEY, id);
    } else {
      localStorage.removeItem(ACTIVE_TENANT_KEY);
    }
  }, []);

  return (
    <TenantContext.Provider value={{ activeTenantId, setActiveTenant }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
