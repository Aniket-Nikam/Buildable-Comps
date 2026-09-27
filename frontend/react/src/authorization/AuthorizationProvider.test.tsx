import { render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import { AuthProvider } from "../auth/AuthProvider";
import {
  AuthorizationProvider,
  useAuthorization,
} from "./AuthorizationProvider";
import { Can } from "./Can";

const user = {
  id: "user-1",
  email: "admin@example.com",
  displayName: "Admin",
  status: "active" as const,
  emailVerified: true,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url =
        input instanceof Request
          ? input.url
          : input instanceof URL
            ? input.href
            : input;
      if (url.endsWith("/auth/refresh")) {
        return Promise.resolve(
          Response.json({
            success: true,
            data: {
              accessToken: "access-token",
              tokenType: "bearer",
              expiresIn: 900,
              user,
            },
            meta: {},
          }),
        );
      }
      if (url.endsWith("/authorization/me")) {
        return Promise.resolve(
          Response.json({
            success: true,
            data: {
              roles: [
                {
                  id: "role-1",
                  name: "platform-admin",
                  description: "Administrator",
                  isSystem: true,
                  createdAt: "2026-01-01T00:00:00Z",
                  updatedAt: "2026-01-01T00:00:00Z",
                },
              ],
              permissions: [
                {
                  id: "permission-1",
                  name: "authorization.roles.read",
                  description: "Read roles",
                  createdAt: "2026-01-01T00:00:00Z",
                },
              ],
            },
            meta: {},
          }),
        );
      }
      throw new Error(`Unhandled request: ${url}`);
    }),
  );
});

test("renders content only when the permission is granted", async () => {
  render(
    <AuthProvider apiUrl="http://api.test/api/v1">
      <AuthorizationProvider>
        <Can permission="authorization.roles.read">
          <span>Role manager</span>
        </Can>
        <Can
          permission="authorization.roles.write"
          fallback={<span>Read only</span>}
        >
          <span>Create role</span>
        </Can>
      </AuthorizationProvider>
    </AuthProvider>,
  );

  expect(await screen.findByText("Role manager")).toBeInTheDocument();
  expect(screen.getByText("Read only")).toBeInTheDocument();
  expect(screen.queryByText("Create role")).not.toBeInTheDocument();
});

test("exposes assigned role and permission data", async () => {
  function Summary() {
    const authorization = useAuthorization();
    if (authorization.status !== "ready") return <span>Loading</span>;
    return (
      <span>
        {authorization.roles[0]?.name}:{authorization.permissions[0]?.name}
      </span>
    );
  }

  render(
    <AuthProvider apiUrl="http://api.test/api/v1">
      <AuthorizationProvider>
        <Summary />
      </AuthorizationProvider>
    </AuthProvider>,
  );

  expect(
    await screen.findByText("platform-admin:authorization.roles.read"),
  ).toBeInTheDocument();
});
