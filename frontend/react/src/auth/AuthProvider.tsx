import type {
  LoginInput,
  RegisterInput,
  UpdateProfileInput,
  User,
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

import { ApiClient } from "../api/client";

export type AuthStatus = "loading" | "anonymous" | "authenticated";

interface AuthContextValue {
  client: ApiClient;
  status: AuthStatus;
  user: User | null;
  login: (input: LoginInput) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
  confirmEmailVerification: (token: string) => Promise<void>;
  requestEmailVerification: () => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  updateProfile: (input: UpdateProfileInput) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  apiUrl: string;
  children: ReactNode;
}

export function AuthProvider({ apiUrl, children }: AuthProviderProps) {
  const client = useMemo(() => new ApiClient(apiUrl), [apiUrl]);
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    let active = true;
    void client
      .refresh()
      .then((data) => {
        if (!active) return;
        setUser(data.user);
        setStatus("authenticated");
      })
      .catch(() => {
        if (!active) return;
        setUser(null);
        setStatus("anonymous");
      });
    return () => {
      active = false;
    };
  }, [client]);

  const login = useCallback(
    async (input: LoginInput) => {
      const data = await client.login(input);
      client.setAccessToken(data.accessToken);
      setUser(data.user);
      setStatus("authenticated");
    },
    [client],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      const data = await client.register(input);
      client.setAccessToken(data.accessToken);
      setUser(data.user);
      setStatus("authenticated");
    },
    [client],
  );

  const logout = useCallback(async () => {
    await client.logout();
    setUser(null);
    setStatus("anonymous");
  }, [client]);

  const requestEmailVerification = useCallback(async () => {
    if (!user) throw new Error("Authentication is required.");
    await client.requestEmailVerification({ email: user.email });
  }, [client, user]);

  const confirmEmailVerification = useCallback(
    async (token: string) => {
      const verifiedUser = await client.confirmEmailVerification({ token });
      if (user?.id === verifiedUser.id) setUser(verifiedUser);
    },
    [client, user?.id],
  );

  const requestPasswordReset = useCallback(
    async (email: string) => {
      await client.requestPasswordReset({ email });
    },
    [client],
  );

  const resetPassword = useCallback(
    async (token: string, newPassword: string) => {
      await client.resetPassword({ token, newPassword });
      try {
        await client.logout();
      } catch {
        client.setAccessToken(null);
      }
      setUser(null);
      setStatus("anonymous");
    },
    [client],
  );

  const updateProfile = useCallback(
    async (input: UpdateProfileInput) => {
      setUser(await client.updateProfile(input));
    },
    [client],
  );

  const value = useMemo(
    () => ({
      client,
      status,
      user,
      login,
      register,
      logout,
      confirmEmailVerification,
      requestEmailVerification,
      requestPasswordReset,
      resetPassword,
      updateProfile,
    }),
    [
      client,
      status,
      user,
      login,
      register,
      logout,
      confirmEmailVerification,
      requestEmailVerification,
      requestPasswordReset,
      resetPassword,
      updateProfile,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within AuthProvider");
  return value;
}

export function useApiClient(): ApiClient {
  return useAuth().client;
}
