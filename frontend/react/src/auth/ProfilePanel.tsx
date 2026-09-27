import { CheckCircle, SignOut, UserCircle } from "@phosphor-icons/react";
import { type FormEvent, useEffect, useState } from "react";

import { ApiClientError } from "../api/client";
import { useAuth } from "./AuthProvider";

export function ProfilePanel() {
  const { user, updateProfile, logout, requestEmailVerification } = useAuth();
  const [displayName, setDisplayName] = useState(user?.displayName ?? "");
  const [state, setState] = useState<"idle" | "saving" | "saved">("idle");
  const [error, setError] = useState<string | null>(null);
  const [verificationState, setVerificationState] = useState<
    "idle" | "sending" | "sent"
  >("idle");

  useEffect(() => setDisplayName(user?.displayName ?? ""), [user?.displayName]);
  if (!user) return null;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("saving");
    setError(null);
    try {
      await updateProfile({ displayName });
      setState("saved");
    } catch (caught) {
      setState("idle");
      setError(
        caught instanceof ApiClientError
          ? caught.message
          : "Could not save your profile.",
      );
    }
  }

  return (
    <section className="bc-profile" aria-labelledby="profile-title">
      <header className="bc-profile-header">
        <div className="bc-avatar" aria-hidden>
          {user.displayName.slice(0, 1).toUpperCase()}
        </div>
        <div>
          <p>Authenticated session</p>
          <h1 id="profile-title">{user.displayName}</h1>
          <span>{user.email}</span>
        </div>
        {user.emailVerified && (
          <CheckCircle
            className="bc-verified"
            weight="fill"
            aria-label="Email verified"
            size={24}
          />
        )}
      </header>

      <div className="bc-profile-grid">
        <form
          className="bc-form"
          onSubmit={(event) => void handleSubmit(event)}
        >
          <div className="bc-section-heading">
            <UserCircle aria-hidden size={22} />
            <div>
              <h2>Basic profile</h2>
              <p>This route requires a valid access token.</p>
            </div>
          </div>
          <label>
            Display name
            <input
              value={displayName}
              onChange={(event) => {
                setDisplayName(event.target.value);
                setState("idle");
              }}
              minLength={2}
              maxLength={80}
              required
            />
          </label>
          {error && (
            <div className="bc-form-error" role="alert">
              {error}
            </div>
          )}
          <button
            className="bc-button bc-button-primary"
            disabled={state === "saving"}
            type="submit"
          >
            {state === "saving"
              ? "Saving..."
              : state === "saved"
                ? "Saved"
                : "Save profile"}
          </button>
        </form>

        <aside className="bc-session-facts">
          <h2>Session behavior</h2>
          <dl>
            <div>
              <dt>Email</dt>
              <dd>
                {user.emailVerified ? "Verified" : "Verification pending"}
              </dd>
            </div>
            <div>
              <dt>Access</dt>
              <dd>Short-lived bearer token</dd>
            </div>
            <div>
              <dt>Refresh</dt>
              <dd>Rotating HttpOnly cookie</dd>
            </div>
            <div>
              <dt>Storage</dt>
              <dd>Server stores only a token digest</dd>
            </div>
          </dl>
          {!user.emailVerified && (
            <button
              className="bc-button bc-button-secondary"
              disabled={verificationState !== "idle"}
              type="button"
              onClick={() => {
                setVerificationState("sending");
                void requestEmailVerification()
                  .then(() => setVerificationState("sent"))
                  .catch(() => setVerificationState("idle"));
              }}
            >
              {verificationState === "sending"
                ? "Sending..."
                : verificationState === "sent"
                  ? "Verification sent"
                  : "Send verification email"}
            </button>
          )}
          <button
            className="bc-button bc-button-secondary"
            type="button"
            onClick={() => void logout()}
          >
            <SignOut aria-hidden size={18} />
            Sign out
          </button>
        </aside>
      </div>
    </section>
  );
}
