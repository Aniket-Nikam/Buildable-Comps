export interface User {
  id: string;
  email: string;
  displayName: string;
  status: "active" | "inactive" | "suspended";
  emailVerified: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AuthData {
  accessToken: string;
  tokenType: "bearer";
  expiresIn: number;
  user: User;
}

export interface ApiSuccess<T> {
  success: true;
  data: T;
  meta: Record<string, unknown>;
}

export interface ApiErrorDetail {
  path?: string;
  message: string;
}

export interface ApiFailure {
  success: false;
  error: {
    code: string;
    message: string;
    details: ApiErrorDetail[];
  };
  meta: { requestId?: string };
}

export type ApiEnvelope<T> = ApiSuccess<T> | ApiFailure;

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput extends LoginInput {
  displayName: string;
}

export interface UpdateProfileInput {
  displayName: string;
}

export interface EmailInput {
  email: string;
}

export interface TokenInput {
  token: string;
}

export interface PasswordResetInput extends TokenInput {
  newPassword: string;
}

export interface AcceptedResult {
  accepted: true;
}

export interface PasswordResetResult {
  passwordReset: true;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  isSystem: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  createdAt: string;
}

export interface RoleDetail extends Role {
  permissions: Permission[];
}

export interface AuthorizationSnapshot {
  roles: Role[];
  permissions: Permission[];
}

export interface RoleInput {
  name: string;
  description?: string;
}

export interface PermissionInput {
  name: string;
  description?: string;
}

export interface AuthorizationAuditLog {
  id: string;
  actorUserId: string | null;
  action: string;
  targetType: string;
  targetId: string;
  details: Record<string, unknown>;
  requestId: string | null;
  ipAddress: string | null;
  createdAt: string;
}
