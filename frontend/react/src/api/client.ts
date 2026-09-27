import type {
  ApiEnvelope,
  AcceptedResult,
  AuthorizationAuditLog,
  AuthorizationSnapshot,
  AuthData,
  EmailInput,
  LoginInput,
  PasswordResetInput,
  PasswordResetResult,
  Permission,
  PermissionInput,
  RegisterInput,
  Role,
  RoleDetail,
  RoleInput,
  TokenInput,
  UpdateProfileInput,
  User,
} from "@buildable/contracts";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly status: number,
    public readonly details: ReadonlyArray<{
      path?: string;
      message: string;
    }> = [],
  ) {
    super(message);
  }
}

export class ApiClient {
  private accessToken: string | null = null;
  private refreshPromise: Promise<AuthData> | null = null;

  constructor(private readonly baseUrl: string) {}

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  login(input: LoginInput): Promise<AuthData> {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  register(input: RegisterInput): Promise<AuthData> {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  refresh(): Promise<AuthData> {
    if (!this.refreshPromise) {
      this.refreshPromise = this.request<AuthData>(
        "/auth/refresh",
        { method: "POST" },
        false,
      )
        .then((data) => {
          this.accessToken = data.accessToken;
          return data;
        })
        .finally(() => {
          this.refreshPromise = null;
        });
    }
    return this.refreshPromise;
  }

  async logout(): Promise<void> {
    try {
      await this.request<{ loggedOut: boolean }>(
        "/auth/logout",
        { method: "POST" },
        false,
      );
    } finally {
      this.accessToken = null;
    }
  }

  me(): Promise<User> {
    return this.request("/users/me", {}, true);
  }

  updateProfile(input: UpdateProfileInput): Promise<User> {
    return this.request(
      "/users/me",
      { method: "PATCH", body: JSON.stringify(input) },
      true,
    );
  }

  requestEmailVerification(input: EmailInput): Promise<AcceptedResult> {
    return this.request("/auth/email-verification/request", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  confirmEmailVerification(input: TokenInput): Promise<User> {
    return this.request("/auth/email-verification/confirm", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  requestPasswordReset(input: EmailInput): Promise<AcceptedResult> {
    return this.request("/auth/password/forgot", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  resetPassword(input: PasswordResetInput): Promise<PasswordResetResult> {
    return this.request("/auth/password/reset", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  authorization(): Promise<AuthorizationSnapshot> {
    return this.request("/authorization/me", {}, true);
  }

  listRoles(): Promise<Role[]> {
    return this.request("/authorization/roles", {}, true);
  }

  getRole(roleId: string): Promise<RoleDetail> {
    return this.request(`/authorization/roles/${roleId}`, {}, true);
  }

  createRole(input: RoleInput): Promise<Role> {
    return this.request(
      "/authorization/roles",
      { method: "POST", body: JSON.stringify(input) },
      true,
    );
  }

  listPermissions(): Promise<Permission[]> {
    return this.request("/authorization/permissions", {}, true);
  }

  createPermission(input: PermissionInput): Promise<Permission> {
    return this.request(
      "/authorization/permissions",
      { method: "POST", body: JSON.stringify(input) },
      true,
    );
  }

  async grantPermission(roleId: string, permissionId: string): Promise<void> {
    await this.request(
      `/authorization/roles/${roleId}/permissions/${permissionId}`,
      { method: "PUT" },
      true,
    );
  }

  async revokePermission(roleId: string, permissionId: string): Promise<void> {
    await this.request(
      `/authorization/roles/${roleId}/permissions/${permissionId}`,
      { method: "DELETE" },
      true,
    );
  }

  async assignRole(userId: string, roleId: string): Promise<void> {
    await this.request(
      `/authorization/users/${userId}/roles/${roleId}`,
      { method: "PUT" },
      true,
    );
  }

  getUserAuthorization(userId: string): Promise<AuthorizationSnapshot> {
    return this.request(`/authorization/users/${userId}`, {}, true);
  }

  async revokeRole(userId: string, roleId: string): Promise<void> {
    await this.request(
      `/authorization/users/${userId}/roles/${roleId}`,
      { method: "DELETE" },
      true,
    );
  }

  listAuthorizationAuditLogs(
    limit = 50,
    offset = 0,
  ): Promise<AuthorizationAuditLog[]> {
    return this.request(
      `/authorization/audit-logs?limit=${limit}&offset=${offset}`,
      {},
      true,
    );
  }

  private async request<T>(
    path: string,
    init: RequestInit = {},
    retryAfterRefresh = false,
  ): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("content-type", "application/json");
    if (this.accessToken)
      headers.set("authorization", `Bearer ${this.accessToken}`);

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers,
      credentials: "include",
    });

    if (response.status === 401 && retryAfterRefresh) {
      await this.refresh();
      return this.request<T>(path, init, false);
    }

    const body = (await response.json()) as ApiEnvelope<T>;
    if (!response.ok || !body.success) {
      const failure = body.success
        ? {
            code: "request_failed",
            message: "The request failed.",
            details: [],
          }
        : body.error;
      throw new ApiClientError(
        failure.message,
        failure.code,
        response.status,
        failure.details,
      );
    }
    return body.data;
  }
}
