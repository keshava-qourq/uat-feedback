import { NavLink, Navigate, Outlet, Route, Routes } from "react-router-dom";

import { Icons } from "@/lib/icons";
import Start from "@/screens/Start";
import Worklist from "@/screens/Worklist";
import CaseSummary from "@/screens/CaseSummary";
import InsufficientHistory from "@/screens/InsufficientHistory";
import Timeline from "@/screens/Timeline";
import Admin from "@/screens/Admin";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    "flex items-center gap-2 rounded-[var(--brand-radius)] px-3 py-2 text-sm font-medium transition-colors",
    isActive ? "bg-[var(--brand-hover)] text-[var(--brand-fg)]" : "text-[var(--brand-fg-muted)]",
  ].join(" ");

// The app's menu, drawn around every screen except the ones routed outside it below.
function AppShellLayout() {
  return (
    <div className="flex min-h-screen">
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
      <Route element={<AppShellLayout />}>
        <Route path="/worklist" element={<Worklist />} />
        <Route path="/case-summary" element={<CaseSummary />} />
        <Route path="/insufficient-history" element={<InsufficientHistory />} />
        <Route path="/timeline" element={<Timeline />} />
        <Route path="/admin" element={<Admin />} />
      </Route>
      <Route path="/start" element={<Start />} />
      <Route path="*" element={<Navigate to="/start" replace />} />
    </Routes>
  );
}
