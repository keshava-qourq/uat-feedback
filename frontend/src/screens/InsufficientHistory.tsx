// @ts-nocheck -- generated from the approved design under its JS runtime contract; not hand-written TypeScript.

import React from "react";

import { Icons } from "@/lib/icons";
import { brand } from "@/lib/brand";
import { useNavigate } from "@/lib/navigate";

const NEEDS = [
  {
    key: "wf-0",
    wf: "i-3-0-0",
    title: "Patient symptom intake",
    note: "resolves night pain, stiffness and NSAID response",
  },
  {
    key: "wf-1",
    wf: "i-3-0-1",
    title: "Records before 2023-06",
    note: "resolves earlier back-pain visits and uveitis",
  },
  {
    key: "wf-2",
    wf: "i-3-0-2",
    title: "Sacroiliac imaging",
    note: "not performed in reachable history; resolves imaging criteria",
  },
  {
    key: "wf-3",
    wf: "i-3-0-3",
    title: "HLA-B27 result",
    note: "none on file; resolves genetic criterion",
  },
];
const NUMERALS = ["I", "II", "III", "IV"];

export default function Screen() {
  const navigate = useNavigate();
  const [requested, setRequested] = React.useState({});
  const [invite, setInvite] = React.useState("idle"); // idle | sending | issued
  const P = brand.primaryColor;
  const A = brand.accentColor;
  const BG = brand.backgroundColor;
  const heading = {
    fontFamily: brand.fontHeading,
    letterSpacing: "0.16em",
    textTransform: "uppercase",
  };
  const num = { fontVariantNumeric: "tabular-nums" };
  const frame = {
    border: "1px solid " + A,
    outline: "1px solid " + P,
    outlineOffset: "4px",
    borderRadius: 0,
  };

  React.useEffect(() => {
    if (invite !== "sending") return undefined;
    const t = setTimeout(() => setInvite("issued"), 800);
    return () => clearTimeout(t);
  }, [invite]);

  const doneCount = NEEDS.filter((n) => requested[n.key]).length;
  const toggle = (k) => setRequested((r) => ({ ...r, [k]: !r[k] }));

  const Ornament = ({ light }) => (
    <div
      aria-hidden="true"
      className="flex items-center justify-center gap-3 my-4"
      style={{ color: light ? A : P }}
    >
      <span style={{ height: 1, width: 72, backgroundColor: A }} />
      <span
        style={{
          width: 8,
          height: 8,
          transform: "rotate(45deg)",
          backgroundColor: A,
          border: "1px solid " + (light ? A : P),
        }}
      />
      <span style={{ height: 1, width: 72, backgroundColor: A }} />
    </div>
  );

  return (
    <div
      style={{ backgroundColor: BG, color: P, fontFamily: brand.fontBody }}
      className="min-h-full w-full px-4 py-8 md:px-8"
    >
      <style>{`
        .ih-btn { transition: background-color .2s, color .2s, transform .2s; }
        .ih-btn:focus-visible, .ih-link:focus-visible, .ih-check:focus-visible { outline: 2px solid ${P}; outline-offset: 3px; box-shadow: 0 0 0 5px ${A}; }
        .ih-primary:hover:not(:disabled) { background-color: ${A}; color: ${P}; }
        .ih-secondary:hover { background-color: ${P}; color: ${BG}; }
        .ih-link:hover { text-decoration: underline; }
        .ih-row { transition: background-color .2s; }
        .ih-row:hover { background-color: rgba(159,181,127,0.18); }
        .ih-enter { animation: ihIn .35s ease-out both; }
        @keyframes ihIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
        @keyframes ihPulse { 0%,100% { opacity: .35; } 50% { opacity: 1; } }
        .ih-pulse { animation: ihPulse 1s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) { .ih-enter, .ih-pulse { animation: none; } .ih-btn, .ih-row { transition: none; } }
      `}</style>

      <div className="mx-auto" style={{ maxWidth: 1040 }}>
        {/* Row 1 */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          <div className="md:col-span-2">
            <button
              type="button"
              data-wf="b-0-0"
              onClick={() => navigate("worklist")}
              className="ih-link inline-flex items-center gap-2 text-sm font-medium"
              style={{
                minHeight: 44,
                color: P,
                background: "none",
                border: "none",
                cursor: "pointer",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              <Icons.ArrowLeft aria-hidden="true" width={16} height={16} />
              Worklist
            </button>
          </div>
          <div className="md:col-span-10 text-center md:pr-24" data-wf="b-0-1">
            <h1 className="text-2xl md:text-3xl font-bold" style={{ ...heading, lineHeight: 1.3 }}>
              Insufficient history — Daniel Okafor, 52 M
            </h1>
            <p
              className="text-xs mt-2"
              style={{ letterSpacing: "0.12em", textTransform: "uppercase" }}
            >
              Synthetic patient · 100% synthetic data, not for clinical use
            </p>
          </div>
        </div>

        <Ornament />

        {/* Row 2 */}
        <section
          data-wf="b-1-0"
          aria-labelledby="status-h"
          className="mt-6 text-center px-6 py-8 ih-enter"
          style={{ ...frame, backgroundColor: P, color: BG }}
        >
          <h2
            id="status-h"
            className="text-xs font-semibold"
            style={{ ...heading, color: A, letterSpacing: "0.24em" }}
          >
            Status
          </h2>
          <p
            className="mt-3 inline-flex items-center gap-3 text-xl md:text-2xl font-bold"
            style={{ ...heading, color: A }}
          >
            <Icons.Clock aria-hidden="true" width={24} height={24} />
            Insufficient history
          </p>
          <div aria-hidden="true" className="flex items-center justify-center gap-3 my-4">
            <span style={{ height: 1, width: 64, backgroundColor: A }} />
            <span style={{ width: 8, height: 8, transform: "rotate(45deg)", backgroundColor: A }} />
            <span style={{ height: 1, width: 64, backgroundColor: A }} />
          </div>
          <p className="text-base mx-auto" style={{ maxWidth: 620, lineHeight: 1.6 }}>
            Reachable history covers about{" "}
            <span style={{ ...num, color: A, fontWeight: 700 }}>10 months</span> (since{" "}
            <span style={num}>2023-06</span>), not enough to assess this case.
          </p>
          <p
            className="text-sm mt-2 mx-auto"
            style={{ maxWidth: 620, lineHeight: 1.6, opacity: 0.85 }}
          >
            The tool could not see enough to form a view either way. It gives no tier for this
            patient.
          </p>
        </section>

        {/* Row 3 */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 mt-12">
          <section
            data-wf="b-2-0"
            aria-labelledby="why-h"
            className="md:col-span-6 p-6"
            style={frame}
          >
            <h2
              id="why-h"
              className="text-base font-bold text-center"
              style={{ ...heading, letterSpacing: "0.2em" }}
            >
              Why history is limited
            </h2>
            <Ornament />
            <p className="text-base" style={{ lineHeight: 1.6 }}>
              Coverage started <span style={num}>2023-06</span> after an employer and insurer
              change; earlier records are not reachable.
            </p>
            <dl className="mt-4 text-sm" style={{ borderTop: "1px solid rgba(18,32,28,0.2)" }}>
              {[
                ["Coverage starts", "2023-06"],
                ["Cause", "Employer and insurer change"],
                ["Earlier records", "Not reachable"],
                ["Reachable span", "About 10 months"],
              ].map(([k, v]) => (
                <div
                  key={k}
                  className="flex justify-between gap-4 py-2"
                  style={{ borderBottom: "1px solid rgba(18,32,28,0.2)" }}
                >
                  <dt style={{ letterSpacing: "0.06em", textTransform: "uppercase", fontSize: 12 }}>
                    {k}
                  </dt>
                  <dd className="font-medium text-right" style={num}>
                    {v}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section
            data-wf="b-2-1"
            aria-labelledby="span-h"
            className="md:col-span-6 p-6"
            style={frame}
          >
            <h2
              id="span-h"
              className="text-base font-bold text-center"
              style={{ ...heading, letterSpacing: "0.2em" }}
            >
              Reachable history span
            </h2>
            <Ornament />
            <svg
              viewBox="0 0 400 130"
              width="100%"
              role="img"
              aria-label="Timeline from January 2019 to the April 2024 cutoff. Records before June 2023 are not reachable. About 10 months, from June 2023 to April 2024, are reachable, with four visits."
              style={{ display: "block" }}
            >
              <defs>
                <pattern
                  id="ih-hatch"
                  width="6"
                  height="6"
                  patternUnits="userSpaceOnUse"
                  patternTransform="rotate(45)"
                >
                  <line x1="0" y1="0" x2="0" y2="6" stroke={brand.neutralColor} strokeWidth="1" />
                </pattern>
              </defs>
              <rect
                x="20"
                y="40"
                width="298"
                height="30"
                fill="url(#ih-hatch)"
                stroke={brand.neutralColor}
                strokeWidth="1"
              />
              <rect x="318" y="40" width="59" height="30" fill={A} stroke={P} strokeWidth="1" />
              {[329, 346, 357.5, 369].map((x) => (
                <rect
                  key={x}
                  x={x - 3}
                  y={52}
                  width="6"
                  height="6"
                  fill={P}
                  transform={"rotate(45 " + x + " 55)"}
                />
              ))}
              <line x1="318" y1="30" x2="318" y2="80" stroke={P} strokeWidth="1" />
              <text
                x="318"
                y="24"
                fontSize="10"
                textAnchor="middle"
                fill={P}
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                2023-06
              </text>
              <text
                x="377"
                y="102"
                fontSize="10"
                textAnchor="end"
                fill={P}
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                Cutoff 2024-04
              </text>
              {[
                ["2019", 20],
                ["2020", 87.5],
                ["2021", 155],
                ["2022", 222.5],
                ["2023", 290],
              ].map(([y, x]) => (
                <g key={y}>
                  <line x1={x} y1="70" x2={x} y2="76" stroke={P} strokeWidth="1" />
                  <text
                    x={x}
                    y="90"
                    fontSize="10"
                    textAnchor="middle"
                    fill={P}
                    style={{ fontVariantNumeric: "tabular-nums" }}
                  >
                    {y}
                  </text>
                </g>
              ))}
            </svg>
            <ul className="mt-4 text-sm grid gap-2" style={{ listStyle: "none", padding: 0 }}>
              <li className="flex items-center gap-3">
                <span
                  aria-hidden="true"
                  style={{
                    width: 20,
                    height: 12,
                    border: "1px solid " + brand.neutralColor,
                    background:
                      "repeating-linear-gradient(45deg, " +
                      brand.neutralColor +
                      " 0 1px, transparent 1px 5px)",
                  }}
                />
                Not reachable: before <span style={num}>2023-06</span>
              </li>
              <li className="flex items-center gap-3">
                <span
                  aria-hidden="true"
                  style={{ width: 20, height: 12, backgroundColor: A, border: "1px solid " + P }}
                />
                Reachable: <span style={num}>10 months</span>, <span style={num}>4</span> visits
                seen
              </li>
            </ul>
          </section>
        </div>

        {/* Row 4 */}
        <section
          data-wf="b-3-0"
          aria-labelledby="need-h"
          className="mt-12 p-6 md:p-8"
          style={frame}
        >
          <h2
            id="need-h"
            className="text-lg font-bold text-center"
            style={{ ...heading, letterSpacing: "0.22em" }}
          >
            What we still need
          </h2>
          <Ornament />
          <p className="text-sm text-center" style={num} aria-live="polite">
            {doneCount} of {NEEDS.length} marked as requested
          </p>
          <ul
            className="mt-4"
            style={{ listStyle: "none", padding: 0, borderTop: "1px solid rgba(18,32,28,0.2)" }}
          >
            {NEEDS.map((n, i) => {
              const on = !!requested[n.key];
              const id = "need-" + n.key;
              return (
                <li
                  key={n.key}
                  className="ih-row grid grid-cols-[40px_1fr] md:grid-cols-[48px_1fr_auto] gap-x-4 gap-y-2 items-center px-2 py-4"
                  style={{ borderBottom: "1px solid rgba(18,32,28,0.2)" }}
                >
                  <span
                    aria-hidden="true"
                    className="text-lg font-bold text-center"
                    style={{
                      fontFamily: brand.fontHeading,
                      border: "1px solid " + A,
                      outline: "1px solid " + P,
                      outlineOffset: 2,
                      width: 36,
                      height: 36,
                      lineHeight: "34px",
                    }}
                  >
                    {NUMERALS[i]}
                  </span>
                  <div>
                    <p className="text-base font-bold" style={{ lineHeight: 1.4 }}>
                      {n.title}
                    </p>
                    <p className="text-sm" style={{ lineHeight: 1.5 }}>
                      {n.note.charAt(0).toUpperCase() + n.note.slice(1)}
                    </p>
                  </div>
                  <div
                    className="col-start-2 md:col-start-3 flex items-center gap-3"
                    style={{ minHeight: 44 }}
                  >
                    <input
                      id={id}
                      data-wf={n.wf}
                      className="ih-check"
                      type="checkbox"
                      checked={on}
                      onChange={() => toggle(n.key)}
                      style={{ width: 20, height: 20, accentColor: P, cursor: "pointer" }}
                    />
                    <label
                      htmlFor={id}
                      className="text-sm font-medium inline-flex items-center gap-2"
                      style={{ cursor: "pointer", minWidth: 112 }}
                    >
                      {on ? (
                        <>
                          <Icons.Check aria-hidden="true" width={14} height={14} />
                          Requested
                        </>
                      ) : (
                        "Mark as requested"
                      )}
                    </label>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>

        {/* Row 5 */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 mt-12">
          <div className="md:col-span-4 md:col-start-3">
            <button
              type="button"
              data-wf="b-4-0"
              className="ih-btn ih-primary w-full inline-flex items-center justify-center gap-2 px-4 text-sm font-bold"
              disabled={invite !== "idle"}
              onClick={() => setInvite("sending")}
              style={{
                minHeight: 52,
                backgroundColor: P,
                color: A,
                border: "1px solid " + P,
                borderRadius: 0,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                cursor: invite === "idle" ? "pointer" : "default",
                opacity: invite === "idle" ? 1 : 0.9,
              }}
            >
              {invite === "issued" ? (
                <Icons.Check aria-hidden="true" width={16} height={16} />
              ) : (
                <Icons.ArrowRight aria-hidden="true" width={16} height={16} />
              )}
              {invite === "idle"
                ? "Invite patient to complete intake"
                : invite === "sending"
                  ? "Issuing invite link"
                  : "Invite issued"}
            </button>
          </div>
          <div className="md:col-span-4">
            <button
              type="button"
              data-wf="b-4-1"
              onClick={() => navigate("timeline")}
              className="ih-btn ih-secondary w-full inline-flex items-center justify-center gap-2 px-4 text-sm font-bold"
              style={{
                minHeight: 52,
                backgroundColor: "transparent",
                color: P,
                border: "1px solid " + P,
                borderRadius: 0,
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                cursor: "pointer",
              }}
            >
              View timeline
            </button>
          </div>
        </div>

        <div aria-live="polite" className="mt-8">
          {invite === "sending" && (
            <p className="text-sm text-center ih-pulse">
              Generating a single-use invite link for Daniel Okafor…
            </p>
          )}
          {invite === "issued" && (
            <div
              className="ih-enter mx-auto p-6 text-center"
              role="status"
              style={{ ...frame, maxWidth: 640 }}
            >
              <h2 className="text-sm font-bold" style={{ ...heading, letterSpacing: "0.2em" }}>
                Invite ready to send
              </h2>
              <p
                className="mt-3 text-sm break-all px-3 py-2"
                style={{
                  border: "1px solid rgba(18,32,28,0.3)",
                  fontFamily: "ui-monospace, Menlo, Consolas, monospace",
                }}
              >
                https://copilot.invite/i/&lt;single-use-token&gt;
              </p>
              <dl className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                <div>
                  <dt className="text-xs uppercase" style={{ letterSpacing: "0.1em" }}>
                    Status
                  </dt>
                  <dd className="font-medium">Not yet opened</dd>
                </div>
                <div>
                  <dt className="text-xs uppercase" style={{ letterSpacing: "0.1em" }}>
                    Expires
                  </dt>
                  <dd className="font-medium" style={num}>
                    2026-11-21
                  </dd>
                </div>
                <div>
                  <dt className="text-xs uppercase" style={{ letterSpacing: "0.1em" }}>
                    Access
                  </dt>
                  <dd className="font-medium">This patient only</dd>
                </div>
              </dl>
              <p className="text-sm mt-4" style={{ lineHeight: 1.5 }}>
                Send this link to the patient. It opens their intake — night pain, stiffness and
                NSAID response — and works once.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
