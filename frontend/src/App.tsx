import { useEffect, type ReactNode } from "react";
import { NavLink, Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";

import SyntheticDataNotice from "@/components/SyntheticDataNotice";
import { SESSION_EXPIRED_EVENT, apiFetch, clearSessionToken, getSessionToken } from "@/lib/api";
import { Icons } from "@/lib/icons";
import SignIn from "@/screens/SignIn";
import SetPassword from "@/screens/SetPassword";
import Start from "@/screens/Start";
import Worklist from "@/screens/Worklist";
import CaseSummary from "@/screens/CaseSummary";
import InsufficientHistory from "@/screens/InsufficientHistory";
import MyHealth from "@/screens/MyHealth";
import Timeline from "@/screens/Timeline";
import Admin from "@/screens/Admin";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    "flex items-center gap-2 rounded-[var(--brand-radius)] px-3 py-2 text-sm font-medium transition-colors",
    isActive ? "bg-[var(--brand-hover)] text-[var(--brand-fg)]" : "text-[var(--brand-fg-muted)]",
  ].join(" ");

/**
 * Every route the app registers, in one table so the guardrail test (AC-121) can
 * iterate it and assert the synthetic-data notice renders on each one. Add a new
 * screen here and it inherits the notice from the root layout automatically.
 */
export const ROUTES: ReadonlyArray<{ path: string; element: ReactNode }> = [
  { path: "/sign-in", element: <SignIn /> },
  { path: "/set-password", element: <SetPassword /> },
  { path: "/start", element: <Start /> },
  { path: "/worklist", element: <Worklist /> },
  { path: "/case-summary", element: <CaseSummary /> },
  { path: "/insufficient-history", element: <InsufficientHistory /> },
  { path: "/my-health", element: <MyHealth /> },
  { path: "/timeline", element: <Timeline /> },
  { path: "/admin", element: <Admin /> },
];

// /start is the demo entry point and the auth screens stand alone: all three are drawn
// without the app menu around them.
const OUTSIDE_SHELL = ["/start", "/sign-in", "/set-password"];
const inShell = (path: string) => !OUTSIDE_SHELL.includes(path);

// Clinician and admin areas: without a stored token they bounce to sign-in.
const GUARDED = ["/worklist", "/case-summary", "/timeline", "/admin"];

function RequireSession({ children }: { children: ReactNode }) {
  if (!getSessionToken()) return <Navigate to="/sign-in" replace />;
  return <>{children}</>;
}

// NFR-017: mounted once, around every route, so no screen file hand-adds the notice.
function RootLayout() {
  const navigate = useNavigate();
  // AC-102/AC-103: apiFetch clears the token and announces any 401 from an authenticated
  // call; the redirect lives here because api.ts cannot route.
  useEffect(() => {
    const onExpired = () => navigate("/sign-in", { replace: true });
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, [navigate]);

  return (
    <div className="flex min-h-screen flex-col">
      <SyntheticDataNotice />
      <div className="flex-1">
        <Outlet />
      </div>
    </div>
  );
}

// The app's menu, drawn around every screen except the ones routed outside it below.
function AppShellLayout() {
  const navigate = useNavigate();
  const signOut = async () => {
    try {
      await apiFetch("/api/auth/logout", { method: "POST" });
    } catch {
      // A revoked or expired token is already signed out; clear locally regardless.
    }
    clearSessionToken();
    navigate("/sign-in", { replace: true });
  };

  return (
    <div className="flex min-h-full">
      <aside
        className="w-56 shrink-0 border-r p-4"
        style={{
          backgroundColor: "var(--brand-surface)",
          borderColor: "var(--brand-border)",
        }}
      >
        <p
          className="mb-4 px-3 text-sm font-semibold"
          style={{ fontFamily: "var(--brand-font-heading)" }}
        >
          {"Diagnostic Odyssey Copilot"}
        </p>
        <nav aria-label="App menu" className="flex flex-col gap-1">
          <NavLink to="/worklist" className={navLinkClass}>
            <Icons.Home size={16} />
            {"Worklist"}
          </NavLink>
          <NavLink to="/timeline" className={navLinkClass}>
            <Icons.Menu size={16} />
            {"Timeline"}
          </NavLink>
          <NavLink to="/my-health" className={navLinkClass}>
            <Icons.User size={16} />
            {"My health"}
          </NavLink>
          <NavLink to="/admin" className={navLinkClass}>
            <Icons.Settings size={16} />
            {"Admin"}
          </NavLink>
          <NavLink to="/start" className={navLinkClass}>
            <Icons.User size={16} />
            {"Demo personas"}
          </NavLink>
        </nav>
        <button
          type="button"
          onClick={signOut}
          className="mt-4 flex w-full items-center gap-2 rounded-[var(--brand-radius)] px-3 py-2 text-sm font-medium text-[var(--brand-fg-muted)] hover:bg-[var(--brand-hover)]"
        >
          <Icons.ArrowLeft size={16} />
          {"Sign out"}
        </button>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route element={<AppShellLayout />}>
          {ROUTES.filter((route) => inShell(route.path)).map((route) => (
            <Route
              key={route.path}
              path={route.path}
              element={
                GUARDED.includes(route.path) ? (
                  <RequireSession>{route.element}</RequireSession>
                ) : (
                  route.element
                )
              }
            />
          ))}
        </Route>
        {ROUTES.filter((route) => !inShell(route.path)).map((route) => (
          <Route key={route.path} path={route.path} element={route.element} />
        ))}
        <Route path="*" element={<Navigate to="/start" replace />} />
      </Route>
    </Routes>
  );
}
