// @ts-nocheck -- generated from the approved design under its JS runtime contract; not hand-written TypeScript.

import React from "react";

import { Icons } from "@/lib/icons";
import { brand } from "@/lib/brand";
import { useNavigate } from "@/lib/navigate";

const CUTOFF = "2024-03-01";

const SOURCE_META = {
  record: { label: "Record" },
  claim: { label: "Insurance claim" },
  told: { label: "You told us" },
};

const FILTERS = [
  { key: "all", label: "All", wf: "i-2-0-0" },
  { key: "record", label: "Record", wf: "i-2-0-1" },
  { key: "claim", label: "Insurance claim", wf: "i-2-0-2" },
  { key: "told", label: "You told us", wf: "i-2-0-3" },
];

const ITEMS = [
  {
    id: "e1",
    wf: "i-3-0-0",
    kind: "event",
    date: "2024-02-10",
    title: "Night back pain reported",
    sources: ["told"],
    provider: "Your symptom check",
    specialty: "—",
    code: "Intake answer · night pain",
    value: "Woke from sleep with back pain most nights; eased by getting up",
    refs: [{ src: "told", ref: "intake-q-night-pain" }],
    encounterRef: "None — reported by you",
    eventId: "evt-9140021",
  },
  {
    id: "e2",
    kind: "event",
    date: "2024-01-18",
    title: "Naproxen prescription filled",
    sources: ["claim"],
    provider: "Harbor Street Pharmacy",
    specialty: "Pharmacy",
    code: "ATC M01AE02 · naproxen",
    value: "30-day supply",
    refs: [{ src: "claim", ref: "clm-rx-55871-03" }],
    encounterRef: "None — pharmacy claim",
    eventId: "evt-8812204",
  },
  {
    id: "e3",
    wf: "i-3-0-1",
    kind: "event",
    date: "2023-11-02",
    title: "CRP test, normal",
    sources: ["record"],
    provider: "Lakeside Family Medicine",
    specialty: "Laboratory",
    code: "LOINC 1988-5 · C-reactive protein",
    value: "2.1 mg/L (reference under 5.0)",
    refs: [{ src: "record", ref: "ehr-lab-48213" }],
    encounterRef: "enc-20231102-a",
    eventId: "evt-8420077",
  },
  {
    id: "e4",
    wf: "i-3-0-2",
    kind: "event",
    date: "2023-09-14",
    title: "Primary care visit, back pain",
    sources: ["record", "claim"],
    merged: true,
    provider: "Lakeside Family Medicine",
    specialty: "Family medicine",
    code: "ICD-10-CM M54.59 · Other low back pain",
    value: "Visit counted once",
    refs: [
      { src: "record", ref: "ehr-enc-30918" },
      { src: "claim", ref: "clm-55021-01" },
    ],
    encounterRef: "enc-20230914-a",
    eventId: "evt-8301155",
  },
  {
    id: "e5",
    kind: "event",
    date: "2023-06-22",
    title: "Eye clinic visit, red painful eye",
    sources: ["record"],
    provider: "Northgate Eye Associates",
    specialty: "Ophthalmology",
    code: "CPT 92004 · Comprehensive eye exam",
    value: "—",
    refs: [{ src: "record", ref: "ehr-enc-27704" }],
    encounterRef: "enc-20230622-b",
    eventId: "evt-8190342",
  },
  {
    id: "gap",
    wf: "i-3-0-3",
    kind: "gap",
    date: "Before 2023-06",
    title: "Gap — before coverage started (before 2023-06)",
    sources: [],
    reason: "Before coverage started",
    coverage: "cov-0007 · first coverage period begins 2023-06-01",
  },
  {
    id: "e7",
    wf: "i-3-0-4",
    kind: "event",
    date: "2023-03-20",
    title: "Chiropractic care, self-paid",
    sources: ["told"],
    unconfirmed: true,
    provider: "Not named in your answers",
    specialty: "Chiropractic",
    code: "Intake answer · self-paid visits",
    value: "Paid out of pocket; no insurance involved",
    refs: [{ src: "told", ref: "intake-q-selfpaid-02" }],
    encounterRef: "None — not in any record or claim",
    eventId: "evt-9140034",
  },
];

export default function Screen() {
  const navigate = useNavigate();
  const [filter, setFilter] = React.useState("all");
  const [selectedId, setSelectedId] = React.useState("e4");
  const detailRef = React.useRef(null);

  const P = brand.primaryColor;
  const A = brand.accentColor;
  const B = brand.backgroundColor;
  const surface = `color-mix(in srgb, ${B} 55%, white)`;
  const softText = `color-mix(in srgb, ${P} 80%, ${B})`;
  const hairline = `color-mix(in srgb, ${P} 18%, transparent)`;
  const tint = `color-mix(in srgb, ${A} 30%, ${B})`;
  const hatch = `repeating-linear-gradient(135deg, color-mix(in srgb, ${A} 55%, transparent) 0 1px, transparent 1px 7px)`;
  const mono = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace';
  const heading = {
    fontFamily: brand.fontHeading,
    textTransform: "uppercase",
    letterSpacing: "0.16em",
  };
  const frame = {
    border: `1px solid ${A}`,
    outline: `1px solid ${P}`,
    outlineOffset: 4,
    background: surface,
    borderRadius: 0,
  };

  const matches = (it) => it.kind === "gap" || filter === "all" || it.sources.includes(filter);
  const visible = ITEMS.filter(matches);
  const eventCount = (key) =>
    ITEMS.filter((i) => i.kind === "event" && (key === "all" || i.sources.includes(key))).length;
  const visibleEvents = visible.filter((i) => i.kind === "event");
  const selected = ITEMS.find((i) => i.id === selectedId) || ITEMS[3];

  const chooseFilter = (key) => {
    setFilter(key);
    const next = ITEMS.filter(
      (it) => it.kind === "gap" || key === "all" || it.sources.includes(key),
    );
    if (!next.some((i) => i.id === selectedId)) setSelectedId(next[0].id);
  };

  const chooseItem = (id) => {
    setSelectedId(id);
    if (
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(max-width: 767px)").matches &&
      detailRef.current
    ) {
      const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      detailRef.current.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    }
  };

  const ornament = () => (
    <div aria-hidden="true" className="flex items-center gap-3" style={{ width: "100%" }}>
      <span style={{ flex: 1, height: 1, background: A }} />
      <span
        style={{ width: 9, height: 9, transform: "rotate(45deg)", background: P, display: "block" }}
      />
      <span style={{ flex: 1, height: 1, background: A }} />
    </div>
  );

  const doubleRule = () => (
    <div aria-hidden="true">
      <div style={{ height: 1, background: A }} />
      <div style={{ height: 1, background: P, marginTop: 3 }} />
    </div>
  );

  const glyph = (src) => {
    const common = { width: 10, height: 10, "aria-hidden": true, focusable: "false" };
    if (src === "record")
      return (
        <svg {...common} viewBox="0 0 10 10">
          <rect x="1" y="1" width="8" height="8" fill="currentColor" />
        </svg>
      );
    if (src === "claim")
      return (
        <svg {...common} viewBox="0 0 10 10">
          <path d="M5 .8 9.2 5 5 9.2.8 5Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </svg>
      );
    return (
      <svg {...common} viewBox="0 0 10 10">
        <circle cx="5" cy="5" r="4" fill="currentColor" />
      </svg>
    );
  };

  const tag = (src) => {
    const styles = {
      record: { background: P, color: B, border: `1px solid ${P}` },
      claim: { background: "transparent", color: P, border: `1px solid ${P}` },
      told: { background: A, color: P, border: `1px solid ${A}` },
    }[src];
    return (
      <span
        key={src}
        className="inline-flex items-center gap-2 px-2 py-1"
        style={{
          ...styles,
          fontSize: 12,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          fontWeight: 600,
          lineHeight: 1.2,
        }}
      >
        {glyph(src)}
        {SOURCE_META[src].label}
      </span>
    );
  };

  const sourcesLine = (it) => it.sources.map((s) => SOURCE_META[s].label).join(" and ");

  const detailRows = () => {
    if (selected.kind === "gap") {
      return [
        ["Period", "Before 2023-06"],
        ["Reason", selected.reason],
        ["Coverage record", selected.coverage, true],
        [
          "What this means",
          "Records and claims from this period are not reachable. Care may have happened here; we only show what our sources contain.",
        ],
      ];
    }
    const rows = [
      ["Provider", selected.provider],
      [
        "Sources",
        selected.merged
          ? `${sourcesLine(selected)} (merged into one visit)`
          : sourcesLine(selected),
      ],
      ["Source ref", selected.refs.map((r) => r.ref).join(" · "), true],
      ["Encounter ref", selected.encounterRef, true],
      ["Code", selected.code],
      ["Detail", selected.value],
      ["Event id", selected.eventId, true],
    ];
    return rows;
  };

  return (
    <div style={{ background: B, color: P, fontFamily: brand.fontBody, minHeight: "100%" }}>
      <style>{`
        .gt-focus:focus-visible { outline: 2px solid ${P}; outline-offset: 3px; }
        .gt-row { transition: background-color .18s ease, border-color .18s ease; }
        .gt-row:hover { background: ${tint}; }
        .gt-filter { transition: background-color .18s ease, color .18s ease; }
        .gt-filter:hover { background: ${tint}; }
        .gt-filter[aria-pressed="true"]:hover { background: ${P}; }
        .gt-back { transition: background-color .18s ease, color .18s ease; }
        .gt-back:hover { background: ${P}; color: ${A}; }
        @keyframes gt-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
        .gt-in { animation: gt-in .3s ease both; }
        @media (prefers-reduced-motion: reduce) {
          .gt-in { animation: none; }
          .gt-row, .gt-filter, .gt-back { transition: none; }
        }
      `}</style>

      <div className="mx-auto px-4 sm:px-6 py-8" style={{ maxWidth: 1120 }}>
        {/* Row 1 */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          <div data-wf="b-0-0" className="md:col-span-8 text-center">
            <h1
              style={{
                ...heading,
                fontSize: "clamp(28px, 5vw, 38px)",
                fontWeight: 700,
                lineHeight: 1.15,
                margin: 0,
              }}
            >
              Health timeline
            </h1>
            <p
              style={{
                marginTop: 8,
                marginBottom: 16,
                fontSize: 14,
                color: softText,
                lineHeight: 1.5,
              }}
            >
              Records, insurance claims and your own answers, in date order, as of{" "}
              <span style={{ fontVariantNumeric: "tabular-nums", fontFamily: mono }}>{CUTOFF}</span>
              .
            </p>
            <div className="mx-auto" style={{ maxWidth: 360 }}>
              {ornament()}
            </div>
          </div>
          <div className="md:col-span-4 flex justify-center md:justify-end">
            <button
              data-wf="b-0-1"
              type="button"
              onClick={() => navigate("case-summary")}
              className="gt-back gt-focus inline-flex items-center gap-2 px-4"
              style={{
                minHeight: 44,
                border: `1px solid ${P}`,
                background: "transparent",
                color: P,
                borderRadius: 0,
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
              }}
            >
              <Icons.ArrowLeft className="w-4 h-4" aria-hidden="true" />
              Back to case
            </button>
          </div>
        </div>

        {/* Row 2 */}
        <section
          data-wf="b-1-0"
          aria-label="Reachable history"
          className="mt-8"
          style={{ ...frame, padding: 24 }}
        >
          <div className="flex items-start sm:items-center justify-center gap-3 text-left sm:text-center">
            <Icons.AlertCircle className="w-5 h-5 shrink-0" aria-hidden="true" />
            <p style={{ margin: 0, fontSize: 16, lineHeight: 1.5, fontWeight: 500 }}>
              Reachable history goes back to{" "}
              <span style={{ fontVariantNumeric: "tabular-nums" }}>2023-06</span>. Symptoms began
              earlier — add what is missing.
            </p>
          </div>
          <div className="mt-4 grid" style={{ gridTemplateColumns: "35fr 65fr", gap: 4 }}>
            <div>
              <div
                aria-hidden="true"
                style={{ height: 12, border: `1px solid ${A}`, background: hatch }}
              />
              <div style={{ fontSize: 12, marginTop: 4, color: softText }}>Not reachable</div>
            </div>
            <div>
              <div aria-hidden="true" style={{ height: 12, background: P }} />
              <div
                style={{
                  fontSize: 12,
                  marginTop: 4,
                  color: softText,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                Reachable · 2023-06 to {CUTOFF}
              </div>
            </div>
          </div>
        </section>

        {/* Row 3 */}
        <div data-wf="b-2-0" className="mt-8">
          {doubleRule()}
          <div className="flex flex-wrap items-center justify-between gap-3 py-3">
            <div role="group" aria-label="Source" className="flex flex-wrap items-center gap-2">
              <span
                className="inline-flex items-center gap-2 pr-2"
                style={{ ...heading, fontSize: 13, fontWeight: 700 }}
              >
                <Icons.Filter className="w-4 h-4" aria-hidden="true" />
                Source
              </span>
              {FILTERS.map((f) => {
                const on = filter === f.key;
                return (
                  <button
                    key={f.key}
                    data-wf={f.wf}
                    type="button"
                    aria-pressed={on}
                    onClick={() => chooseFilter(f.key)}
                    className="gt-filter gt-focus inline-flex items-center gap-2 px-3"
                    style={{
                      minHeight: 44,
                      borderRadius: 0,
                      cursor: "pointer",
                      fontSize: 14,
                      fontWeight: 600,
                      border: `1px solid ${P}`,
                      background: on ? P : "transparent",
                      color: on ? A : P,
                    }}
                  >
                    {on && <Icons.Check className="w-4 h-4" aria-hidden="true" />}
                    {f.label}
                    <span
                      style={{
                        fontVariantNumeric: "tabular-nums",
                        fontFamily: mono,
                        fontSize: 12,
                        opacity: 0.85,
                      }}
                    >
                      {eventCount(f.key)}
                    </span>
                  </button>
                );
              })}
            </div>
            <p
              aria-live="polite"
              style={{
                margin: 0,
                fontSize: 13,
                color: softText,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              Showing {visibleEvents.length} of {eventCount("all")} events · gaps always shown
            </p>
          </div>
          {doubleRule()}
        </div>

        {/* Row 4 */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
          <section
            data-wf="b-3-0"
            aria-labelledby="events-h"
            className="md:col-span-8"
            style={{ ...frame, padding: 24 }}
          >
            <div className="text-center">
              <h2 id="events-h" style={{ ...heading, fontSize: 22, fontWeight: 700, margin: 0 }}>
                Events
              </h2>
              <p style={{ margin: "4px 0 12px", fontSize: 13, color: softText }}>
                Newest first · only items dated before{" "}
                <span style={{ fontVariantNumeric: "tabular-nums" }}>{CUTOFF}</span>
              </p>
              {ornament()}
            </div>

            {visibleEvents.length === 0 && (
              <div
                className="gt-in mt-6 p-4 text-center"
                style={{ border: `1px dashed ${P}`, fontSize: 14, lineHeight: 1.5 }}
              >
                Nothing from this source before the cutoff date. Try another source, or add what you
                remember from your symptom check.
              </div>
            )}

            <ol
              key={filter}
              className="mt-6"
              style={{ listStyle: "none", margin: 0, padding: 0, position: "relative" }}
            >
              {visible.map((it, idx) => {
                const on = it.id === selectedId;
                const isGap = it.kind === "gap";
                return (
                  <li
                    key={it.id}
                    className="gt-in relative"
                    style={{
                      paddingLeft: 32,
                      paddingBottom: idx === visible.length - 1 ? 0 : 12,
                      animationDelay: `${idx * 40}ms`,
                    }}
                  >
                    {idx < visible.length - 1 && (
                      <span
                        aria-hidden="true"
                        style={{
                          position: "absolute",
                          left: 8,
                          top: 26,
                          bottom: -12,
                          width: 1,
                          background: A,
                        }}
                      />
                    )}
                    <span
                      aria-hidden="true"
                      style={{
                        position: "absolute",
                        left: 3,
                        top: 20,
                        width: 11,
                        height: 11,
                        transform: "rotate(45deg)",
                        border: `1px solid ${P}`,
                        background: on ? P : B,
                      }}
                    />
                    <button
                      data-wf={it.wf}
                      type="button"
                      aria-pressed={on}
                      onClick={() => chooseItem(it.id)}
                      className="gt-row gt-focus w-full text-left p-4"
                      style={{
                        borderRadius: 0,
                        cursor: "pointer",
                        color: P,
                        display: "block",
                        border: `1px ${it.unconfirmed ? "dashed" : "solid"} ${on ? P : hairline}`,
                        background: on ? tint : isGap ? hatch : "transparent",
                        backgroundColor: on ? tint : isGap ? surface : undefined,
                        borderLeftWidth: on ? 3 : 1,
                      }}
                    >
                      {isGap ? (
                        <div className="flex items-center gap-3">
                          <Icons.Clock className="w-5 h-5 shrink-0" aria-hidden="true" />
                          <span style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.4 }}>
                            {it.title}
                          </span>
                        </div>
                      ) : (
                        <>
                          <div
                            style={{
                              fontFamily: mono,
                              fontSize: 13,
                              fontVariantNumeric: "tabular-nums",
                              letterSpacing: "0.06em",
                              color: softText,
                            }}
                          >
                            {it.date}
                          </div>
                          <div
                            style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.4, marginTop: 2 }}
                          >
                            {it.title}
                          </div>
                          <div className="flex flex-wrap items-center gap-2 mt-2">
                            {it.sources.map((s) => tag(s))}
                            {it.merged && (
                              <span style={{ fontSize: 13, color: softText }}>
                                merged into one visit
                              </span>
                            )}
                          </div>
                          {it.unconfirmed && (
                            <div
                              className="flex items-center gap-2 mt-2"
                              style={{ fontSize: 13, fontWeight: 600 }}
                            >
                              <Icons.AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
                              Not confirmed by any record or claim
                            </div>
                          )}
                        </>
                      )}
                    </button>
                  </li>
                );
              })}
            </ol>
          </section>

          <aside
            data-wf="b-3-1"
            ref={detailRef}
            aria-labelledby="detail-h"
            className="md:col-span-4 md:sticky md:top-6"
            style={{ ...frame, padding: 24, scrollMarginTop: 16 }}
          >
            <div className="text-center">
              <h2 id="detail-h" style={{ ...heading, fontSize: 18, fontWeight: 700, margin: 0 }}>
                Item detail
              </h2>
              <div className="mt-3">{ornament()}</div>
            </div>
            <div key={selected.id} className="gt-in mt-4" aria-live="polite">
              <h3 style={{ fontSize: 18, fontWeight: 600, lineHeight: 1.35, margin: 0 }}>
                {selected.kind === "gap" ? "Gap in reachable history" : selected.title}
                {selected.kind === "event" && (
                  <span style={{ fontVariantNumeric: "tabular-nums" }}>, {selected.date}</span>
                )}
              </h3>
              {selected.kind === "event" && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {selected.sources.map((s) => tag(s))}
                </div>
              )}
              {selected.unconfirmed && (
                <p
                  className="flex items-start gap-2"
                  style={{ margin: "12px 0 0", fontSize: 14, lineHeight: 1.5, fontWeight: 600 }}
                >
                  <Icons.AlertCircle className="w-4 h-4 shrink-0 mt-1" aria-hidden="true" />
                  Not confirmed by any record or claim. You reported this in your symptom check.
                </p>
              )}
              {selected.merged && (
                <div style={{ marginTop: 16 }}>
                  <div
                    style={{ ...heading, fontSize: 12, fontWeight: 700, letterSpacing: "0.14em" }}
                  >
                    Contributing rows
                  </div>
                  <ul style={{ listStyle: "none", margin: "8px 0 0", padding: 0 }}>
                    {selected.refs.map((r) => (
                      <li
                        key={r.ref}
                        className="flex flex-wrap items-center justify-between gap-2 py-2"
                        style={{ borderTop: `1px solid ${hairline}` }}
                      >
                        {tag(r.src)}
                        <span
                          style={{
                            fontFamily: mono,
                            fontSize: 13,
                            fontVariantNumeric: "tabular-nums",
                          }}
                        >
                          {r.ref}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <dl style={{ margin: "16px 0 0" }}>
                {detailRows().map(([k, v, isMono]) => (
                  <div key={k} className="py-3" style={{ borderTop: `1px solid ${hairline}` }}>
                    <dt
                      style={{
                        ...heading,
                        fontSize: 12,
                        letterSpacing: "0.14em",
                        fontWeight: 700,
                        color: softText,
                      }}
                    >
                      {k}
                    </dt>
                    <dd
                      style={{
                        margin: "4px 0 0",
                        fontSize: 14,
                        lineHeight: 1.5,
                        overflowWrap: "anywhere",
                        fontFamily: isMono ? mono : undefined,
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {v}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
