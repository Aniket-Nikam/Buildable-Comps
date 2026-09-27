import type { ReactNode } from "react";

import { useAuthorization } from "./AuthorizationProvider";

interface CanProps {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export function Can({ permission, children, fallback = null }: CanProps) {
  const { status, hasPermission } = useAuthorization();
  if (status !== "ready" || !hasPermission(permission)) return fallback;
  return children;
}

export const PermissionGuard = Can;
