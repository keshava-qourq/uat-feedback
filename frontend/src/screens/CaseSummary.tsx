// @ts-nocheck -- generated from the approved design under its JS runtime contract; not hand-written TypeScript.
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from "react";
import { useSearchParams } from "react-router-dom";

import { ApiError, apiFetch } from "@/lib/api";
import * as UI from "@/lib/ui";
import { Icons } from "@/lib/icons";
import { brand } from "@/lib/brand";
import { useNavigate } from "@/lib/navigate";

const { Textarea, Label } = UI;

const { Check, X, ChevronRight, Clock, Download, ArrowRight, AlertCircle, CheckCircle } = Icons;

const CASE = {
  name: "Maria Alvarez",
  cutoff: "2024-03-01",
  clinician: "Dr. Priya Raman",
};

const TIERS = ["High", "Moderate", "Low", "Insufficient history"];

const EVIDENCE_FOR = [
  {
    id: "i-2-0-0",
    label: "Uveitis visit",
    date: "2022-05-12",
    tag: "Record",
    note: "Ophthalmology visit",
    go: true,
  },
  {
    id: "i-2-0-1",
    label: "Night pain reported",
    date: "2024-02-10",
    tag: "You told us",
    note: "Symptom intake answer",
    go: true,
  },
  {
    id: "i-2-0-2",
    label: "Back pain visits ×3",
    date: null,
    tag: "Insurance claim",
    note: "Three visits in claims, dates on the timeline",
    go: true,
  },
];

const EVIDENCE_AGAINST = [
  {
    id: "i-2-1-0",
    label: "Normal CRP",
    date: "2023-11-02",
    tag: "Record",
    note: "Lab result",
    go: true,
  },
  {
    id: "i-2-1-1",
    label: "Poor NSAID response not reported",
    date: null,
    tag: "You told us",
    note: "No answer in the intake, so nothing to cite on the timeline",
    go: false,
  },
];

const CONFLICTING = [
  {
    id: "i-3-1-0",
    label: "Fibromyalgia",
    date: "2021",
    tag: "Record",
    note: "May not explain inflammatory features",
  },
];

const WORKUP = [
  {
    id: "i-5-0-0",
    label: "Sacroiliac MRI",
    done: false,
    why: "Why: imaging missing, back pain over 3 months",
  },
  { id: "i-5-0-1", label: "CRP", done: true, why: "Already done 2023-11-02, normal" },
];

const DECISIONS = [
  { key: "agree", label: "Agree" },
  { key: "disagree", label: "Disagree" },
  { key: "more", label: "Need more info" },
];

const RESULTS = [
  { key: "hla", label: "HLA-B27 negative" },
  { key: "crp", label: "CRP normal" },
  { key: "mri", label: "Sacroiliac MRI negative" },
];

const Ico = ({ name, size = 16 }) => {
  const C = Icons && Icons[name];
  return C ? (
    <C
      aria-hidden="true"
      width={size}
      height={size}
      className="shrink-0"
      style={{ width: size, height: size }}
    />
  ) : null;
};

const surface = () => `color-mix(in srgb, ${brand.backgroundColor} 55%, white)`;
const soft = () => `color-mix(in srgb, ${brand.primaryColor} 74%, ${brand.backgroundColor})`;
const hair = () => `color-mix(in srgb, ${brand.primaryColor} 16%, transparent)`;
const tint = () => `color-mix(in srgb, ${brand.primaryColor} 7%, transparent)`;

const Frame = ({ wf, children, className = "", style = {}, ...rest }) => (
  <section
    data-wf={wf}
    {...rest}
    className={"cs-enter " + className}
    style={{
      border: `1px solid ${brand.accentColor}`,
      outline: `1px solid ${brand.primaryColor}`,
      outlineOffset: 4,
      background: surface(),
      padding: 24,
      borderRadius: 0,
      ...style,
    }}
  >
    {children}
  </section>
);

const Ornament = () => (
  <div aria-hidden="true" className="flex items-center gap-3" style={{ margin: "12px 0 16px" }}>
    <span style={{ flex: 1, height: 1, background: brand.accentColor }} />
    <span
      style={{
        width: 8,
        height: 8,
        transform: "rotate(45deg)",
        background: brand.primaryColor,
        border: `1px solid ${brand.accentColor}`,
      }}
    />
    <span style={{ flex: 1, height: 1, background: brand.accentColor }} />
  </div>
);

const H2 = ({ children, sub, id }) => (
  <h2
    id={id}
    style={{
      fontFamily: brand.fontHeading,
      color: brand.primaryColor,
      fontSize: 16,
      lineHeight: 1.4,
      letterSpacing: "0.16em",
      textTransform: "uppercase",
      fontWeight: 700,
      margin: 0,
    }}
  >
    {children}
    {sub ? (
      <span
        style={{
          display: "block",
          fontFamily: brand.fontBody,
          fontSize: 13,
          letterSpacing: "normal",
          textTransform: "none",
          fontWeight: 400,
          color: soft(),
          marginTop: 4,
        }}
      >
        {sub}
      </span>
    ) : null}
  </h2>
);

const SourceTag = ({ tag }) => {
  const base = {
    fontSize: 12,
    lineHeight: "16px",
    padding: "2px 8px",
    letterSpacing: "0.04em",
    whiteSpace: "nowrap",
    borderRadius: 0,
    fontWeight: 600,
  };
  const styles = {
    Record: {
      background: brand.primaryColor,
      color: brand.accentColor,
      border: `1px solid ${brand.primaryColor}`,
    },
    "Insurance claim": {
      background: "transparent",
      color: brand.primaryColor,
      border: `1px solid ${brand.primaryColor}`,
    },
    "You told us": {
      background: "transparent",
      color: brand.primaryColor,
      border: `1px dashed ${brand.primaryColor}`,
      fontStyle: "italic",
    },
  };
  return <span style={{ ...base, ...(styles[tag] || styles["Record"]) }}>{tag}</span>;
};

const EvidenceRow = ({ item }) => {
  const inner = (
    <>
      <span className="min-w-0 flex-1">
        <span style={{ display: "block", fontWeight: 600, color: brand.primaryColor }}>
          {item.label}
        </span>
        <span style={{ display: "block", fontSize: 13, color: soft(), marginTop: 4 }}>
          {item.date ? (
            <span style={{ fontVariantNumeric: "tabular-nums" }}>{item.date}</span>
          ) : null}
          {item.date ? " · " : ""}
          {item.note}
        </span>
      </span>
      <SourceTag tag={item.tag} />
      {item.go ? (
        <span style={{ color: brand.primaryColor }}>
          <Ico name="ChevronRight" />
        </span>
      ) : (
        <span style={{ width: 16 }} aria-hidden="true" />
      )}
    </>
  );
  return (
    <li style={{ borderTop: `1px solid ${hair()}` }}>
      {item.go ? (
        <button
          type="button"
          data-wf={item.id}
          className="cs-row flex w-full items-center gap-3 text-left"
          style={{
            padding: "12px 8px",
            minHeight: 44,
            background: "transparent",
            border: 0,
            cursor: "pointer",
            fontSize: 14,
            borderRadius: 0,
          }}
          onClick={() => navigate("timeline")}
          aria-label={`${item.label}${item.date ? ", " + item.date : ""}, ${item.tag}. Open on the timeline`}
        >
          {inner}
        </button>
      ) : (
        <div
          data-wf={item.id}
          className="flex w-full items-center gap-3"
          style={{ padding: "12px 8px", fontSize: 14 }}
        >
          {inner}
        </div>
      )}
    </li>
  );
};

const EmptyNote = ({ children }) => (
  <li
    style={{ borderTop: `1px solid ${hair()}`, padding: "16px 8px", fontSize: 14, color: soft() }}
  >
    {children}
  </li>
);

const ListBlock = ({ wf, title, children, span }) => (
  <Frame wf={wf} className={span}>
    <H2>{title}</H2>
    <Ornament />
    <ul style={{ listStyle: "none", margin: 0, padding: 0, borderBottom: `1px solid ${hair()}` }}>
      {children}
    </ul>
  </Frame>
);

const StatusMark = ({ status }) => {
  const map = {
    met: ["CheckCircle", "Met"],
    unknown: ["AlertCircle", "Unknown"],
    not_met: ["X", "Not met"],
  };
  const [icon, word] = map[status] || map.unknown;
  return (
    <span
      className="inline-flex items-center gap-1"
      style={{
        fontWeight: 700,
        fontSize: 12,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: brand.primaryColor,
      }}
    >
      <Ico name={icon} size={16} />
      {word}
    </span>
  );
};

// US-010: one criterion or SPARTAN point item, straight from
// GET /api/cases/{patient_id}. Its detail opens on demand and shows the named
// evidence (met) or the 'needed' text (unknown / not met).
const CriterionRow = ({ item, group }) => {
  const [open, setOpen] = React.useState(false);
  const panelId = `criterion-${group}-${item.key}`;
  const evidence = item.evidence ?? null;
  return (
    <li
      data-testid={`criterion-${item.key}`}
      style={{ borderTop: `1px solid ${hair()}`, fontSize: 14 }}
    >
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
        className="cs-row flex w-full items-start justify-between gap-3 text-left"
        style={{
          padding: "12px 8px",
          minHeight: 44,
          background: "transparent",
          border: 0,
          cursor: "pointer",
          fontSize: 14,
          borderRadius: 0,
        }}
      >
        <span style={{ fontWeight: 600, color: brand.primaryColor }}>
          {item.label}
          {typeof item.points === "number" ? (
            <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 400 }}>
              {" "}
              · {item.points} {item.points === 1 ? "point" : "points"}
            </span>
          ) : null}
        </span>
        <StatusMark status={item.status} />
      </button>
      {open ? (
        <div id={panelId} style={{ padding: "0 8px 12px", fontSize: 13, color: soft() }}>
          {evidence ? (
            <span className="inline-flex flex-wrap items-center gap-2">
              <span style={{ fontWeight: 600, color: brand.primaryColor }}>{evidence.display}</span>
              <span style={{ fontVariantNumeric: "tabular-nums" }}>{evidence.date}</span>
              <SourceTag tag={evidence.source_tag} />
            </span>
          ) : (
            <span>{item.needed || "No detail recorded for this item."}</span>
          )}
        </div>
      ) : null}
    </li>
  );
};

export default function Screen() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const patientId = params.get("patient_id") ?? "";
  // US-010: the criteria panel is the only part of this screen served by the API.
  const [caseData, setCaseData] = React.useState(null);
  const [caseLoading, setCaseLoading] = React.useState(true);
  const [caseError, setCaseError] = React.useState("");

  React.useEffect(() => {
    let live = true;
    setCaseLoading(true);
    apiFetch(`/api/cases/${patientId}`)
      .then((data) => {
        if (!live) return;
        setCaseData(data);
        setCaseError("");
      })
      .catch((err) => {
        if (!live) return;
        setCaseData(null);
        setCaseError(err instanceof ApiError ? err.message : "Could not load this case.");
      })
      .finally(() => {
        if (live) setCaseLoading(false);
      });
    return () => {
      live = false;
    };
  }, [patientId]);

  // US-012: the headline tier, its reason and the counter-evidence are the API's.
  const tier = caseData?.tier ?? "";
  const cutoff = caseData?.cutoff_date ?? CASE.cutoff;
  const counterEvidence = Array.isArray(caseData?.counter_evidence)
    ? caseData.counter_evidence
    : [];
  const alternative = caseData?.alternative_explanation ?? null;

  const asas = caseData?.criteria?.asas_referral ?? [];
  const spartan = caseData?.criteria?.spartan ?? null;
  const spartanItems = spartan?.items ?? [];

  const [decision, setDecision] = React.useState("");
  const [reason, setReason] = React.useState("");
  const [results, setResults] = React.useState({ hla: false, crp: false, mri: false });
  const [error, setError] = React.useState("");
  const [saved, setSaved] = React.useState(null);
  const [exportState, setExportState] = React.useState("idle");

  React.useEffect(() => {
    if (exportState !== "preparing") return undefined;
    const t = setTimeout(() => setExportState("ready"), 900);
    return () => clearTimeout(t);
  }, [exportState]);

  const onSave = (e) => {
    e.preventDefault();
    if (!decision) {
      setError("Choose Agree, Disagree or Need more info before saving. Your reason is kept.");
      return;
    }
    if (decision !== "agree" && !reason.trim()) {
      setError(
        "Add a short reason so the next reviewer can see why you " +
          (decision === "disagree" ? "disagree." : "need more information."),
      );
      return;
    }
    setError("");
    const label = DECISIONS.find((d) => d.key === decision).label;
    setSaved({
      label,
      reason: reason.trim(),
      results: RESULTS.filter((r) => results[r.key]).map((r) => r.label),
      at: new Date().toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" }),
    });
  };

  const buttonBase = {
    minHeight: 44,
    padding: "8px 24px",
    fontFamily: brand.fontHeading,
    fontSize: 13,
    letterSpacing: "0.16em",
    textTransform: "uppercase",
    fontWeight: 700,
    borderRadius: 0,
    cursor: "pointer",
    width: "100%",
  };
  const secondary = {
    ...buttonBase,
    background: "transparent",
    color: brand.primaryColor,
    border: `1px solid ${brand.primaryColor}`,
  };
  const primary = {
    ...buttonBase,
    background: brand.primaryColor,
    color: brand.accentColor,
    border: `1px solid ${brand.primaryColor}`,
  };

  const labelStyle = {
    fontSize: 13,
    fontWeight: 600,
    color: brand.primaryColor,
    display: "block",
    marginBottom: 8,
  };

  return (
    <div
      style={{
        fontFamily: brand.fontBody,
        color: brand.primaryColor,
        fontVariantNumeric: "tabular-nums",
        fontSize: 14,
        lineHeight: 1.5,
      }}
    >
      <style>{`
        .cs-row:hover { background: ${tint()} !important; }
        .cs-btn { transition: background-color .15s ease, color .15s ease, transform .1s ease; }
        .cs-btn:hover:not(:disabled) { background: ${tint()}; }
        .cs-btn-primary:hover:not(:disabled) { background: color-mix(in srgb, ${brand.primaryColor} 88%, ${brand.accentColor}) !important; }
        .cs-btn:active:not(:disabled) { transform: translateY(1px); }
        .cs-btn:disabled { opacity: .6; cursor: progress; }
        .cs-page button:focus-visible, .cs-page input:focus-visible, .cs-page textarea:focus-visible {
          outline: 2px solid ${brand.primaryColor}; outline-offset: 2px;
        }
        .cs-opt:focus-within { outline: 2px solid ${brand.primaryColor}; outline-offset: 2px; }
        @keyframes cs-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
        .cs-enter { animation: cs-in .35s ease both; }
        @media (prefers-reduced-motion: reduce) {
          .cs-enter { animation: none; }
          .cs-btn { transition: none; }
        }
      `}</style>

      <div
        className="cs-page mx-auto grid grid-cols-1 gap-8 md:grid-cols-12"
        style={{ maxWidth: 1120, padding: "8px 8px 48px" }}
      >
        {/* Row 1 */}
        <div data-wf="b-0-0" className="md:col-span-8">
          <p
            style={{
              margin: 0,
              fontSize: 12,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color: soft(),
            }}
          >
            Clinician view · Synthetic worklist patient
          </p>
          <h1
            style={{
              fontFamily: brand.fontHeading,
              fontSize: 32,
              lineHeight: 1.2,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              fontWeight: 700,
              margin: "8px 0 0",
            }}
          >
            Case summary — {CASE.name}, 34 F
          </h1>
          <Ornament />
        </div>
        <div className="md:col-span-4 md:self-start">
          <button
            type="button"
            data-wf="b-0-1"
            className="cs-btn inline-flex items-center justify-center gap-2"
            style={secondary}
            disabled={exportState === "preparing"}
            onClick={() => setExportState("preparing")}
          >
            <Ico name="Download" />
            {exportState === "preparing" ? "Preparing packet…" : "Export referral packet"}
          </button>
          <div
            role="status"
            aria-live="polite"
            style={{ fontSize: 13, color: soft(), marginTop: 8, minHeight: 20 }}
          >
            {exportState === "ready"
              ? `Packet ready: status, evidence, criteria and workup, using only records dated before ${cutoff}.`
              : ""}
          </div>
        </div>

        {/* Row 2 */}
        <Frame wf="b-1-0" className="md:col-span-12" style={{ textAlign: "center", padding: 32 }}>
          <p
            style={{
              margin: 0,
              fontSize: 12,
              letterSpacing: "0.24em",
              textTransform: "uppercase",
              color: soft(),
            }}
          >
            Status
          </p>
          <h2
            data-testid="case-tier"
            style={{
              fontFamily: brand.fontHeading,
              fontSize: 32,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              fontWeight: 700,
              margin: "8px 0 0",
            }}
          >
            <span className="sr-only">Status: </span>
            {caseLoading ? "Loading…" : tier || "No status from the API"}
          </h2>
          <Ornament />
          <p
            data-testid="case-tier-reason"
            style={{ margin: "0 auto", maxWidth: 640, fontSize: 16, lineHeight: 1.5 }}
          >
            {caseData?.tier_reason ?? ""}
          </p>
          <p style={{ margin: "12px 0 0", fontSize: 13, color: soft() }}>
            Scored as of cutoff{" "}
            <span
              style={{
                fontVariantNumeric: "tabular-nums",
                fontWeight: 600,
                color: brand.primaryColor,
              }}
            >
              {cutoff}
            </span>
            . Only records dated before this day are used.
          </p>
          <ol
            aria-label="Status scale"
            className="flex flex-wrap justify-center gap-2"
            style={{ listStyle: "none", margin: "24px 0 0", padding: 0 }}
          >
            {TIERS.map((t) => {
              const current = t === tier;
              const insufficient = t === "Insufficient history";
              return (
                <li
                  key={t}
                  aria-current={current ? "true" : undefined}
                  style={{
                    padding: "4px 16px",
                    fontSize: 12,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    fontWeight: 700,
                    background: current ? brand.primaryColor : "transparent",
                    color: current ? brand.accentColor : soft(),
                    border: `1px ${insufficient ? "dashed" : "solid"} ${current ? brand.primaryColor : soft()}`,
                  }}
                >
                  {current ? "◆ " : ""}
                  {t}
                  {current ? <span className="sr-only"> (current status)</span> : null}
                </li>
              );
            })}
          </ol>
        </Frame>

        {/* Row 3 */}
        <ListBlock wf="b-2-0" title="Top evidence for" span="md:col-span-6">
          {EVIDENCE_FOR.length ? (
            EVIDENCE_FOR.map((i) => <EvidenceRow key={i.id} item={i} />)
          ) : (
            <EmptyNote>No supporting evidence found before the cutoff.</EmptyNote>
          )}
        </ListBlock>
        <ListBlock wf="b-2-1" title="Evidence against" span="md:col-span-6">
          {EVIDENCE_AGAINST.length ? (
            EVIDENCE_AGAINST.map((i) => <EvidenceRow key={i.id} item={i} />)
          ) : (
            <EmptyNote>No evidence against found before the cutoff.</EmptyNote>
          )}
        </ListBlock>

        {/* Row 4 */}
        {counterEvidence.length ? (
          <Frame wf="b-3-0" className="md:col-span-6" data-testid="counter-evidence-panel">
            <H2>Counter-evidence</H2>
            <Ornament />
            <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {counterEvidence.map((item) => (
                <li
                  key={item.key}
                  data-testid={`counter-evidence-${item.key}`}
                  style={{ borderTop: `1px solid ${hair()}`, padding: "12px 0" }}
                >
                  <p style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>{item.label}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 15 }}>{item.plain_language}</p>
                  <p style={{ margin: "4px 0 0", fontSize: 13, color: soft() }}>
                    Caps the status at {item.capped_to}.
                  </p>
                  <ul style={{ listStyle: "none", margin: "8px 0 0", padding: 0 }}>
                    {(item.evidence ?? []).map((e, i) => (
                      <li
                        key={`${item.key}-${i}`}
                        className="flex flex-wrap items-center gap-2"
                        style={{ fontSize: 13, color: soft(), padding: "4px 0" }}
                      >
                        {e.source_ref ? (
                          <a
                            href={`/timeline?source_ref=${encodeURIComponent(e.source_ref)}`}
                            style={{ fontWeight: 600, color: brand.primaryColor }}
                          >
                            {e.display}
                          </a>
                        ) : (
                          <span style={{ fontWeight: 600, color: brand.primaryColor }}>
                            {e.display}
                          </span>
                        )}
                        {e.date ? (
                          <span style={{ fontVariantNumeric: "tabular-nums" }}>{e.date}</span>
                        ) : null}
                        <SourceTag tag={e.source_tag} />
                      </li>
                    ))}
                  </ul>
                  {item.awaiting_sign_off ? (
                    <p
                      className="inline-flex items-center gap-2"
                      data-testid={`awaiting-sign-off-${item.key}`}
                      style={{
                        margin: "8px 0 0",
                        padding: "4px 12px",
                        fontSize: 12,
                        fontWeight: 700,
                        letterSpacing: "0.08em",
                        textTransform: "uppercase",
                        border: `1px dashed ${brand.primaryColor}`,
                      }}
                    >
                      <Ico name="Clock" />
                      Awaiting clinical review
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
            {alternative ? (
              <p data-testid="alternative-explanation" style={{ margin: "12px 0 0", fontSize: 15 }}>
                <strong>Alternative:</strong> {alternative.label}
              </p>
            ) : null}
          </Frame>
        ) : null}
        <ListBlock wf="b-3-1" title="Conflicting labels in the record" span="md:col-span-6">
          {CONFLICTING.length ? (
            CONFLICTING.map((i) => (
              <li
                key={i.id}
                data-wf={i.id}
                style={{ borderTop: `1px solid ${hair()}`, padding: "12px 8px", fontSize: 14 }}
              >
                <div className="flex items-start justify-between gap-3">
                  <span style={{ fontWeight: 600 }}>
                    {i.label} — <span style={{ fontVariantNumeric: "tabular-nums" }}>{i.date}</span>
                  </span>
                  <SourceTag tag={i.tag} />
                </div>
                <div style={{ fontSize: 13, color: soft(), marginTop: 4 }}>{i.note}</div>
              </li>
            ))
          ) : (
            <EmptyNote>No conflicting labels in this patient's record.</EmptyNote>
          )}
        </ListBlock>

        {/* Row 5 — referral criteria, from GET /api/cases/{patient_id} */}
        <ListBlock wf="b-4-0" title="Referral criteria" span="md:col-span-6">
          {caseLoading ? (
            <EmptyNote>Loading the criteria…</EmptyNote>
          ) : caseError ? (
            <li
              role="alert"
              style={{
                borderTop: `1px solid ${hair()}`,
                padding: "16px 8px",
                fontSize: 14,
              }}
            >
              {caseError}
            </li>
          ) : asas.length ? (
            asas.map((i) => <CriterionRow key={i.key} item={i} group="asas" />)
          ) : (
            <EmptyNote>No referral criteria for this patient.</EmptyNote>
          )}
        </ListBlock>
        <Frame wf="b-4-1" className="md:col-span-6">
          <H2>Point items</H2>
          <Ornament />
          <ul
            style={{
              listStyle: "none",
              margin: 0,
              padding: 0,
              borderBottom: `1px solid ${hair()}`,
            }}
          >
            {caseLoading ? (
              <EmptyNote>Loading the point items…</EmptyNote>
            ) : spartanItems.length ? (
              spartanItems.map((i) => <CriterionRow key={i.key} item={i} group="spartan" />)
            ) : (
              <EmptyNote>No point items for this patient.</EmptyNote>
            )}
          </ul>
          {spartan ? (
            <p
              data-testid="spartan-total"
              style={{
                margin: "12px 0 0",
                fontSize: 14,
                fontWeight: 700,
                fontVariantNumeric: "tabular-nums",
              }}
            >
              Total {spartan.total} of threshold {spartan.threshold}
              {spartan.total >= spartan.threshold ? " — threshold reached" : " — below threshold"}
            </p>
          ) : null}
          <p style={{ margin: "12px 0 0", fontSize: 13, color: soft() }}>
            Unknown is never counted as not met in the total.
          </p>
        </Frame>

        {/* Row 6 */}
        <Frame wf="b-5-0" className="md:col-span-8">
          <H2 sub="— information to consider, not an order; no diagnosis issued">
            Suggested workup
          </H2>
          <Ornament />
          <ul
            style={{
              listStyle: "none",
              margin: 0,
              padding: 0,
              borderBottom: `1px solid ${hair()}`,
            }}
          >
            {WORKUP.map((w) => (
              <li
                key={w.id}
                data-wf={w.id}
                className="flex items-start justify-between gap-3"
                style={{ borderTop: `1px solid ${hair()}`, padding: "12px 8px", fontSize: 14 }}
              >
                <span>
                  <span style={{ display: "block", fontWeight: 600 }}>{w.label}</span>
                  <span
                    style={{
                      display: "block",
                      fontSize: 13,
                      color: soft(),
                      marginTop: 4,
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {w.why}
                  </span>
                </span>
                <span
                  className="inline-flex items-center gap-1"
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    padding: "2px 8px",
                    whiteSpace: "nowrap",
                    background: w.done ? brand.primaryColor : "transparent",
                    color: w.done ? brand.accentColor : brand.primaryColor,
                    border: `1px ${w.done ? "solid" : "dashed"} ${brand.primaryColor}`,
                  }}
                >
                  {w.done ? <Ico name="Check" size={12} /> : null}
                  {w.done ? "Done" : "To consider"}
                </span>
              </li>
            ))}
          </ul>
        </Frame>

        <Frame wf="b-5-1" className="md:col-span-4">
          <H2>Your decision</H2>
          <Ornament />
          <form id="decision-form" onSubmit={onSave} noValidate>
            <fieldset data-wf="i-5-1-0" style={{ border: 0, padding: 0, margin: 0 }}>
              <legend style={labelStyle}>Agree / Disagree / Need more info</legend>
              <div className="flex flex-col gap-2">
                {DECISIONS.map((d) => (
                  <label
                    key={d.key}
                    className="cs-opt flex items-center gap-2"
                    style={{
                      minHeight: 44,
                      padding: "4px 12px",
                      cursor: "pointer",
                      border: `1px solid ${brand.primaryColor}`,
                      background: decision === d.key ? tint() : "transparent",
                      fontWeight: decision === d.key ? 700 : 400,
                    }}
                  >
                    <input
                      type="radio"
                      name="decision"
                      value={d.key}
                      checked={decision === d.key}
                      onChange={() => setDecision(d.key)}
                      style={{ accentColor: brand.primaryColor, width: 16, height: 16 }}
                    />
                    {d.label}
                  </label>
                ))}
              </div>
            </fieldset>

            <div style={{ marginTop: 16 }}>
              <Label htmlFor="decision-reason" style={labelStyle}>
                Reason
              </Label>
              <Textarea
                id="decision-reason"
                data-wf="i-5-1-1"
                rows={4}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                aria-describedby={error ? "decision-error" : undefined}
                aria-invalid={error ? true : undefined}
                style={{
                  width: "100%",
                  borderRadius: 0,
                  border: `1px solid ${brand.primaryColor}`,
                  background: "transparent",
                  padding: 8,
                  fontSize: 14,
                }}
              />
            </div>

            <fieldset data-wf="i-5-1-2" style={{ border: 0, padding: 0, margin: "16px 0 0" }}>
              <legend style={labelStyle}>Record workup results</legend>
              <div className="flex flex-col gap-1">
                {RESULTS.map((r) => (
                  <label
                    key={r.key}
                    className="cs-opt flex items-center gap-2"
                    style={{ minHeight: 44, padding: "4px 4px", cursor: "pointer" }}
                  >
                    <input
                      type="checkbox"
                      checked={results[r.key]}
                      onChange={(e) => setResults({ ...results, [r.key]: e.target.checked })}
                      style={{ accentColor: brand.primaryColor, width: 16, height: 16 }}
                    />
                    {r.label}
                  </label>
                ))}
              </div>
            </fieldset>

            {error ? (
              <p
                id="decision-error"
                role="alert"
                className="cs-enter flex items-start gap-2"
                style={{
                  margin: "16px 0 0",
                  padding: 12,
                  fontSize: 13,
                  border: `1px solid ${brand.primaryColor}`,
                  borderLeftWidth: 4,
                  background: tint(),
                }}
              >
                <Ico name="AlertCircle" />
                <span>{error}</span>
              </p>
            ) : null}
            {saved ? (
              <div
                role="status"
                className="cs-enter"
                style={{
                  margin: "16px 0 0",
                  padding: 12,
                  fontSize: 13,
                  border: `1px solid ${brand.primaryColor}`,
                  background: tint(),
                }}
              >
                <p className="flex items-center gap-2" style={{ margin: 0, fontWeight: 700 }}>
                  <Ico name="CheckCircle" />
                  Decision saved: {saved.label}
                </p>
                <p style={{ margin: "4px 0 0", color: soft() }}>
                  {CASE.clinician} · {saved.at} · tier shown: {tier || "none"}
                </p>
                {saved.reason ? <p style={{ margin: "4px 0 0" }}>“{saved.reason}”</p> : null}
                {saved.results.length ? (
                  <p style={{ margin: "4px 0 0" }}>Results noted: {saved.results.join(", ")}.</p>
                ) : null}
                <p style={{ margin: "4px 0 0", color: soft() }}>
                  The tier is unchanged; decisions are stored as data.
                </p>
              </div>
            ) : null}
          </form>
        </Frame>

        {/* Row 7 */}
        <div className="md:col-span-4 md:col-start-3">
          <button
            type="button"
            data-wf="b-6-0"
            className="cs-btn inline-flex items-center justify-center gap-2"
            style={secondary}
            onClick={() => navigate("timeline")}
          >
            Open full timeline
            <Ico name="ArrowRight" />
          </button>
        </div>
        <div className="md:col-span-4">
          <button
            type="submit"
            form="decision-form"
            data-wf="b-6-1"
            className="cs-btn cs-btn-primary inline-flex items-center justify-center gap-2"
            style={primary}
          >
            Save decision
          </button>
        </div>
      </div>
    </div>
  );
}
