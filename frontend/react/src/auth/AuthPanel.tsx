import {
  ArrowLeft,
  ArrowRight,
  Key,
  LockKey,
  UserPlus,
} from "@phosphor-icons/react";
import { type FormEvent, useState } from "react";

import { ApiClientError } from "../api/client";
import { useAuth } from "./AuthProvider";

type Mode = "forgot" | "login" | "register";

function getFormValue(data: FormData, name: string): string {
  const value = data.get(name);
  return typeof value === "string" ? value : "";
}

export function AuthPanel() {
  const { login, register, requestPasswordReset } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setNotice(null);
    const data = new FormData(event.currentTarget);
    try {
      if (mode === "forgot") {
        await requestPasswordReset(getFormValue(data, "email"));
        setNotice("If that account exists, a reset link has been sent.");
      } else if (mode === "login") {
        await login({
          email: getFormValue(data, "email"),
          password: getFormValue(data, "password"),
        });
      } else {
        await register({
          displayName: getFormValue(data, "displayName"),
          email: getFormValue(data, "email"),
          password: getFormValue(data, "password"),
        });
      }
    } catch (caught) {
      setError(
        caught instanceof ApiClientError
          ? caught.message
          : "Could not complete the request.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="bc-auth-panel" aria-labelledby="auth-title">
      <div className="bc-segmented" aria-label="Authentication mode">
        <button
          type="button"
          aria-pressed={mode === "login"}
          onClick={() => setMode("login")}
        >
          Sign in
        </button>
        <button
          type="button"
          aria-pressed={mode === "register"}
          onClick={() => setMode("register")}
        >
          Register
        </button>
      </div>

      <div className="bc-auth-heading">
        {mode === "forgot" ? (
          <Key aria-hidden size={24} />
        ) : mode === "login" ? (
          <LockKey aria-hidden size={24} />
        ) : (
          <UserPlus aria-hidden size={24} />
        )}
        <div>
          <h1 id="auth-title">
            {mode === "forgot"
              ? "Reset your password"
              : mode === "login"
                ? "Welcome back"
                : "Start with a real account"}
          </h1>
          <p>
            {mode === "forgot"
              ? "We’ll send recovery instructions without revealing whether the account exists."
              : mode === "login"
                ? "Use the credentials you registered with."
                : "The demo persists users and rotates refresh sessions."}
          </p>
        </div>
      </div>

      <form className="bc-form" onSubmit={(event) => void handleSubmit(event)}>
        {mode === "register" && (
          <label>
            Display name
            <input
              name="displayName"
              autoComplete="name"
              minLength={2}
              maxLength={80}
              required
            />
          </label>
        )}
        <label>
          Email
          <input name="email" type="email" autoComplete="email" required />
        </label>
        {mode !== "forgot" && (
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
              minLength={mode === "register" ? 12 : 1}
              maxLength={128}
              required
            />
            {mode === "register" && (
              <span className="bc-field-help">Use at least 12 characters.</span>
            )}
          </label>
        )}
        {mode === "login" && (
          <button
            className="bc-link-button"
            type="button"
            onClick={() => setMode("forgot")}
          >
            Forgot password?
          </button>
        )}
        {error && (
          <div className="bc-form-error" role="alert">
            {error}
          </div>
        )}
        {notice && (
          <div className="bc-form-notice" role="status">
            {notice}
          </div>
        )}
        <button
          className="bc-button bc-button-primary"
          disabled={submitting}
          type="submit"
        >
          <span>
            {submitting
              ? "Working..."
              : mode === "forgot"
                ? "Send reset link"
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
          </span>
          {!submitting && <ArrowRight aria-hidden size={18} />}
        </button>
        {mode === "forgot" && (
          <button
            className="bc-link-button bc-link-button-centered"
            type="button"
            onClick={() => setMode("login")}
          >
            <ArrowLeft aria-hidden size={16} />
            Back to sign in
          </button>
        )}
      </form>
    </section>
  );
}
