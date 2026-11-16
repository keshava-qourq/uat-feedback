import type { ReactNode } from "react";
import { NavLink, Navigate, Outlet, Route, Routes } from "react-router-dom";

import SyntheticDataNotice from "@/components/SyntheticDataNotice";
import { Icons } from "@/lib/icons";
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
  { path: "/start", element: <Start /> },
  { path: "/worklist", element: <Worklist /> },
  { path: "/case-summary", element: <CaseSummary /> },
  { path: "/insufficient-history", element: <InsufficientHistory /> },
  { path: "/my-health", element: <MyHealth /> },
  { path: "/timeline", element: <Timeline /> },
  { path: "/admin", element: <Admin /> },
];

// /start is the demo entry point and is drawn without the app menu around it.
const inShell = (path: string) => path !== "/start";

// NFR-017: mounted once, around every route, so no screen file hand-adds the notice.
function RootLayout() {
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
            <Route key={route.path} path={route.path} element={route.element} />
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
