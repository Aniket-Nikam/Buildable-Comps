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
