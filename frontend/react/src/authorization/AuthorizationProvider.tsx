import type {
  AuthorizationSnapshot,
  Permission,
  Role,
} from "@buildable/contracts";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { useApiClient, useAuth } from "../auth/AuthProvider";

export type AuthorizationStatus = "idle" | "loading" | "ready" | "error";

interface AuthorizationContextValue {
  status: AuthorizationStatus;
  roles: Role[];
  permissions: Permission[];
  hasPermission: (permission: string) => boolean;
  refresh: () => Promise<void>;
}

const AuthorizationContext = createContext<AuthorizationContextValue | null>(
  null,
);

interface AuthorizationProviderProps {
  children: ReactNode;
}

const EMPTY_SNAPSHOT: AuthorizationSnapshot = { roles: [], permissions: [] };

export function AuthorizationProvider({
  children,
}: AuthorizationProviderProps) {
  const { status: authStatus, user } = useAuth();
  const client = useApiClient();
  const [status, setStatus] = useState<AuthorizationStatus>("idle");
  const [snapshot, setSnapshot] =
    useState<AuthorizationSnapshot>(EMPTY_SNAPSHOT);

  const refresh = useCallback(async () => {
    if (authStatus !== "authenticated") {
      setSnapshot(EMPTY_SNAPSHOT);
      setStatus("idle");
      return;
    }
    setStatus("loading");
    try {
      setSnapshot(await client.authorization());
      setStatus("ready");
    } catch {
      setSnapshot(EMPTY_SNAPSHOT);
      setStatus("error");
    }
  }, [authStatus, client]);

  useEffect(() => {
    void refresh();
  }, [refresh, user?.id]);

  const granted = useMemo(
    () => new Set(snapshot.permissions.map((permission) => permission.name)),
    [snapshot.permissions],
  );
  const hasPermission = useCallback(
    (permission: string) => granted.has(permission),
    [granted],
  );
  const value = useMemo(
    () => ({
      status,
      roles: snapshot.roles,
      permissions: snapshot.permissions,
      hasPermission,
      refresh,
    }),
    [hasPermission, refresh, snapshot.permissions, snapshot.roles, status],
  );

  return (
    <AuthorizationContext.Provider value={value}>
      {children}
    </AuthorizationContext.Provider>
  );
}

export function useAuthorization(): AuthorizationContextValue {
  const value = useContext(AuthorizationContext);
  if (!value)
    throw new Error(
      "useAuthorization must be used within AuthorizationProvider",
    );
  return value;
}
