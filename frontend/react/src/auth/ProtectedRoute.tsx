import type { ReactNode } from "react";

import { useAuth } from "./AuthProvider";

interface ProtectedRouteProps {
  children: ReactNode;
  fallback: ReactNode;
  loadingFallback?: ReactNode;
}

export function ProtectedRoute({
  children,
  fallback,
  loadingFallback,
}: ProtectedRouteProps) {
  const { status } = useAuth();
  if (status === "loading") return loadingFallback ?? <AuthSkeleton />;
  if (status === "anonymous") return fallback;
  return children;
}

export function AuthSkeleton() {
  return (
    <div className="bc-skeleton" aria-label="Loading session" role="status">
      <span />
      <span />
      <span />
    </div>
  );
}
