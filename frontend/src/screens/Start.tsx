// @ts-nocheck -- generated from the approved design under its JS runtime contract; not hand-written TypeScript.
import React from "react";

import { brand } from "@/lib/brand";
import { useNavigate } from "@/lib/navigate";

const SCREEN = "Demo persona picker";

export default function Screen() {
  const navigate = useNavigate();
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
      className="flex min-h-screen items-center justify-center px-6 py-10"
      style={{ color: brand.primaryColor, fontFamily: brand.fontBody }}
    >
      <main className="w-full max-w-md p-8 text-center sm:p-10" style={frame}>
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
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <button
            data-wf="b-3-1"
            type="button"
            onClick={() => navigate("case-summary")}
            className="min-h-14 w-full px-3 py-3 text-[11px]"
            style={demoBtn}
          >
            Open clinician case
          </button>
          <button
            data-wf="b-3-2"
            type="button"
            onClick={() => navigate("timeline")}
            className="min-h-14 w-full px-3 py-3 text-[11px]"
            style={demoBtn}
          >
            Open patient view
          </button>
        </div>
        <p
          className="mt-8 text-[10px] uppercase tracking-[0.25em]"
          style={{ color: brand.neutralColor }}
        >
          Demo entry only — by invitation
        </p>
      </main>
    </div>
  );
}
