// @ts-nocheck -- generated from the approved design under its JS runtime contract; not hand-written TypeScript.
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from "react";

import { brand } from "@/lib/brand";
import { useNavigate } from "@/lib/navigate";

const PRODUCT = "UAT-Feedback";
const SCREEN = "Sign in and demo persona picker";

export default function Screen() {
  const navigate = useNavigate();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [done, setDone] = React.useState(false);
  const frame = {
    border: `1px solid ${brand.accentColor}`,
    outline: `1px solid ${brand.primaryColor}`,
    outlineOffset: 3,
    borderRadius: brand.radius,
  };
  const caps = {
    fontFamily: brand.fontHeading,
    textTransform: "uppercase",
    letterSpacing: "0.3em",
  };
  const rule = (
    <div aria-hidden className="flex items-center gap-3">
      <span className="h-px flex-1" style={{ backgroundColor: brand.accentColor }} />
      <span className="text-xs" style={{ color: brand.accentColor }}>
        ◆
      </span>
      <span className="h-px flex-1" style={{ backgroundColor: brand.accentColor }} />
    </div>
  );
  const demoBtn = {
    fontFamily: brand.fontHeading,
    textTransform: "uppercase",
    letterSpacing: "0.15em",
    border: `1px solid ${brand.accentColor}`,
    outline: `1px solid ${brand.primaryColor}`,
    outlineOffset: 2,
    borderRadius: brand.radius,
    color: brand.primaryColor,
    backgroundColor: "transparent",
  };

  return (
    <div
      className="flex min-h-screen items-center justify-center px-6"
      style={{ color: brand.primaryColor, fontFamily: brand.fontBody }}
    >
      <main className="w-full max-w-md p-10 text-center" style={frame}>
        <p aria-hidden className="text-sm tracking-[0.5em]" style={{ color: brand.accentColor }}>
          ◆ ◆ ◆
        </p>
        <h1 data-wf="b-0-0" className="mt-4 text-2xl" style={caps}>
          Diagnostic Odyssey Copilot
        </h1>
        <p
          className="mt-2 text-[10px] uppercase tracking-[0.35em]"
          style={{ color: brand.neutralColor }}
        >
          {SCREEN}
        </p>
        <div className="mt-6">{rule}</div>
        {done ? (
          <p role="status" className="mt-8 text-lg" style={caps}>
            Admitted
          </p>
        ) : (
          <form
            className="mt-8 space-y-5 text-left"
            onSubmit={(e) => {
              e.preventDefault();
              setDone(true);
              navigate("worklist");
            }}
          >
            <div className="space-y-2">
              <label
                htmlFor="ga-email"
                className="block text-[10px] uppercase tracking-[0.25em]"
                style={{ color: brand.neutralColor }}
              >
                Email
              </label>
              <input
                id="ga-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 w-full bg-transparent px-3 text-center text-sm outline-none"
                style={{
                  border: `1px solid ${brand.accentColor}`,
                  borderRadius: brand.radius,
                  color: brand.primaryColor,
                }}
              />
            </div>
            <div className="space-y-2">
              <label
                htmlFor="ga-password"
                className="block text-[10px] uppercase tracking-[0.25em]"
                style={{ color: brand.neutralColor }}
              >
                Password
              </label>
              <input
                id="ga-password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 w-full bg-transparent px-3 text-center text-sm outline-none"
                style={{
                  border: `1px solid ${brand.accentColor}`,
                  borderRadius: brand.radius,
                  color: brand.primaryColor,
                }}
              />
            </div>
            <button
              data-wf="b-3-0"
              type="submit"
              className="h-12 w-full text-xs"
              style={{
                ...caps,
                backgroundColor: brand.primaryColor,
                color: brand.accentColor,
                borderRadius: brand.radius,
              }}
            >
              Sign in
            </button>
          </form>
        )}
        <div className="mt-6 grid grid-cols-2 gap-4">
          <button
            data-wf="b-3-1"
            type="button"
            onClick={() => navigate("case-summary")}
            className="min-h-12 px-2 py-2 text-[11px]"
            style={demoBtn}
          >
            Open clinician case
          </button>
          <button
            data-wf="b-3-2"
            type="button"
            onClick={() => navigate("timeline")}
            className="min-h-12 px-2 py-2 text-[11px]"
            style={demoBtn}
          >
            Open patient view
          </button>
        </div>
        <p
          className="mt-7 text-[10px] uppercase tracking-[0.25em]"
          style={{ color: brand.neutralColor }}
        >
          By invitation —{" "}
          <button
            type="button"
            className="underline underline-offset-4"
            style={{ color: brand.accentColor }}
          >
            request yours
          </button>
        </p>
      </main>
    </div>
  );
}
