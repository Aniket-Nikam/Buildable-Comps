import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthPanel } from "./AuthPanel";
import { AuthProvider, useAuth } from "./AuthProvider";
import { RecoveryPanel } from "./RecoveryPanel";

const apiUser = {
  id: "9f8494b9-1111-4444-8888-d8cce8a30123",
  email: "rhea@example.com",
  displayName: "Rhea Menon",
  status: "active",
  emailVerified: false,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
};

function StateProbe() {
  const { status, user } = useAuth();
  return <div>{status === "authenticated" ? user?.displayName : status}</div>;
}

describe("AuthProvider", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("falls back to the anonymous state when no refresh session exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: () =>
          Promise.resolve({
            success: false,
            error: {
              code: "invalid_session",
              message: "Session expired",
              details: [],
            },
            meta: {},
          }),
      }),
    );
    render(
      <AuthProvider apiUrl="http://api.test/api/v1">
        <StateProbe />
      </AuthProvider>,
    );
    expect(await screen.findByText("anonymous")).toBeInTheDocument();
  });

  it("registers a user and exposes the authenticated profile", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () =>
          Promise.resolve({
            success: false,
            error: {
              code: "invalid_session",
              message: "Session expired",
              details: [],
            },
            meta: {},
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () =>
          Promise.resolve({
            success: true,
            data: {
              accessToken: "access",
              tokenType: "bearer",
              expiresIn: 900,
              user: apiUser,
            },
            meta: {},
          }),
      });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(
      <AuthProvider apiUrl="http://api.test/api/v1">
        <AuthPanel />
        <StateProbe />
      </AuthProvider>,
    );
    await screen.findByText("anonymous");
    await user.click(screen.getByRole("button", { name: "Register" }));
    await user.type(screen.getByLabelText("Display name"), "Rhea Menon");
    await user.type(screen.getByLabelText("Email"), "rhea@example.com");
    fireEvent.change(screen.getByLabelText(/^Password/), {
      target: { value: "a-long-password" },
    });
    await user.click(screen.getByRole("button", { name: "Create account" }));
    await waitFor(() =>
      expect(screen.getByText("Rhea Menon")).toBeInTheDocument(),
    );
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://api.test/api/v1/auth/register",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });

  it("confirms an email through the single-use recovery panel", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () =>
          Promise.resolve({
            success: false,
            error: {
              code: "invalid_session",
              message: "Session expired",
              details: [],
            },
            meta: {},
          }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({
            success: true,
            data: { ...apiUser, emailVerified: true },
            meta: {},
          }),
      });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(
      <AuthProvider apiUrl="http://api.test/api/v1">
        <RecoveryPanel mode="email-verification" token="opaque-token" />
        <StateProbe />
      </AuthProvider>,
    );

    await screen.findByText("anonymous");
    await user.click(screen.getByRole("button", { name: "Verify email" }));
    expect(
      await screen.findByRole("heading", { name: "Email verified" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://api.test/api/v1/auth/email-verification/confirm",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ token: "opaque-token" }),
      }),
    );
  });
});
