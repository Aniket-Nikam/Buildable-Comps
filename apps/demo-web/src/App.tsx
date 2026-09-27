import {
  AuthorizationProvider,
  AuthPanel,
  AuthProvider,
  Can,
  ProfilePanel,
  ProtectedRoute,
  useAuthorization,
} from "@buildable/react";
import {
  BracketsCurly,
  Cube,
  GithubLogo,
  ShieldCheck,
} from "@phosphor-icons/react";

const configuredApiUrl: unknown = import.meta.env.VITE_API_URL;
const apiUrl =
  typeof configuredApiUrl === "string"
    ? configuredApiUrl
    : "http://localhost:8000/api/v1";

export function App() {
  return (
    <AuthProvider apiUrl={apiUrl}>
      <AuthorizationProvider>
        <div className="app-shell">
          <header className="site-header">
            <a className="brand" href="/" aria-label="Buildable Comps home">
              <span className="brand-mark" aria-hidden>
                <Cube size={20} weight="fill" />
              </span>
              <span>Buildable Comps</span>
            </a>
            <nav aria-label="Primary navigation">
              <a href="http://localhost:8000/docs">API docs</a>
              <a href="https://github.com/Aniket-Nikam/Buildable-Comps">
                <GithubLogo aria-hidden size={18} />
                Repository
              </a>
            </nav>
          </header>

          <main>
            <ProtectedRoute fallback={<UnauthenticatedView />}>
              <AuthenticatedView />
            </ProtectedRoute>
          </main>

          <footer>
            <span>Built from registered modules, not copied snippets.</span>
            <a href="http://localhost:8000/health">Health endpoint</a>
          </footer>
        </div>
      </AuthorizationProvider>
    </AuthProvider>
  );
}

function UnauthenticatedView() {
  return (
    <div className="auth-layout">
      <section className="intro" aria-labelledby="intro-title">
        <div className="intro-icon" aria-hidden>
          <BracketsCurly size={25} />
        </div>
        <h1 id="intro-title">Reusable parts. One verified path.</h1>
        <p>
          This runnable slice connects React, FastAPI, rotating sessions, and
          relational persistence.
        </p>
        <div className="capability-list" aria-label="Included capabilities">
          <span>Typed contracts</span>
          <span>Argon2 passwords</span>
          <span>Replay-safe sessions</span>
          <span>Email recovery</span>
          <span>Protected profile</span>
        </div>
      </section>
      <AuthPanel />
    </div>
  );
}

function AuthenticatedView() {
  return (
    <div className="authenticated-layout">
      <div className="authenticated-copy">
        <p>End-to-end proof</p>
        <h2>Your reusable identity module is running.</h2>
      </div>
      <ProfilePanel />
      <AccessSummary />
    </div>
  );
}

function AccessSummary() {
  const { status, roles, permissions } = useAuthorization();
  const roleNames = roles.map((role) => role.name).join(", ");

  return (
    <section className="access-summary" aria-labelledby="access-summary-title">
      <div className="access-summary-icon" aria-hidden>
        <ShieldCheck size={24} weight="fill" />
      </div>
      <div>
        <p>Effective access</p>
        <h3 id="access-summary-title">
          {status === "loading"
            ? "Loading authorization…"
            : roleNames || "No roles assigned"}
        </h3>
        <span>
          {permissions.length} effective permission
          {permissions.length === 1 ? "" : "s"}
        </span>
      </div>
      <Can permission="authorization.roles.read">
        <span className="access-summary-badge">
          Role administration enabled
        </span>
      </Can>
    </section>
  );
}
