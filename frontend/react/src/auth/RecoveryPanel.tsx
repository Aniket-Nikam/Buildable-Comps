import { CheckCircle, Key, ShieldCheck } from "@phosphor-icons/react";
import { type FormEvent, useState } from "react";

import { ApiClientError } from "../api/client";
import { useAuth } from "./AuthProvider";

interface RecoveryPanelProps {
  mode: "email-verification" | "password-reset";
  token: string;
  onComplete?: () => void;
}

export function RecoveryPanel({ mode, token, onComplete }: RecoveryPanelProps) {
  const { confirmEmailVerification, resetPassword } = useAuth();
  const [state, setState] = useState<"idle" | "submitting" | "complete">(
    "idle",
  );
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("submitting");
    setError(null);
    try {
      if (mode === "email-verification") {
        await confirmEmailVerification(token);
      } else {
        const data = new FormData(event.currentTarget);
        const newPassword = data.get("newPassword");
        await resetPassword(
          token,
          typeof newPassword === "string" ? newPassword : "",
        );
      }
      setState("complete");
      onComplete?.();
    } catch (caught) {
      setState("idle");
      setError(
        caught instanceof ApiClientError
          ? caught.message
          : "This link could not be completed.",
      );
    }
  }

  const verifying = mode === "email-verification";
  return (
    <section
      className="bc-auth-panel bc-recovery-panel"
      aria-labelledby="recovery-title"
    >
      <div className="bc-auth-heading">
        {state === "complete" ? (
          <CheckCircle aria-hidden size={24} />
        ) : verifying ? (
          <ShieldCheck aria-hidden size={24} />
        ) : (
          <Key aria-hidden size={24} />
        )}
        <div>
          <h1 id="recovery-title">
            {state === "complete"
              ? verifying
                ? "Email verified"
                : "Password updated"
              : verifying
                ? "Verify your email"
                : "Choose a new password"}
          </h1>
          <p>
            {state === "complete"
              ? "This one-time link has been consumed."
              : "The server validates and consumes this link exactly once."}
          </p>
        </div>
      </div>

      {state !== "complete" && (
        <form
          className="bc-form"
          onSubmit={(event) => void handleSubmit(event)}
        >
          {!verifying && (
            <label>
              New password
              <input
                name="newPassword"
                type="password"
                autoComplete="new-password"
                minLength={12}
                maxLength={128}
                required
              />
              <span className="bc-field-help">Use at least 12 characters.</span>
            </label>
          )}
          {error && (
            <div className="bc-form-error" role="alert">
              {error}
            </div>
          )}
          <button
            className="bc-button bc-button-primary"
            disabled={state === "submitting"}
            type="submit"
          >
            {state === "submitting"
              ? "Working..."
              : verifying
                ? "Verify email"
                : "Reset password"}
          </button>
        </form>
      )}
    </section>
  );
}
