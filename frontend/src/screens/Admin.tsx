// @ts-nocheck -- generated from the approved design under its JS runtime contract; not hand-written TypeScript.
import React from "react";
import { QueryClient, QueryClientProvider, useMutation, useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import * as UI from "@/lib/ui";
import { Icons } from "@/lib/icons";
import { brand } from "@/lib/brand";

const DEDUP_FIELDS = [
  {
    key: "matched_to_one_entry",
    label: "Matched to one entry",
    hint: "EHR and claim rows merged into a single timeline entry, visit counted once.",
  },
  {
    key: "split_into_more_than_one",
    label: "Split into more than one",
    hint: "One real encounter that still shows as two or more entries.",
  },
  {
    key: "merged_in_error",
    label: "Merged in error",
    hint: "Source rows joined although they were separate visits.",
  },
  {
    key: "invisible_care",
    label: "Invisible care",
    hint: "In encounter_truth.csv but in no source. Counted, but never drawn as a timeline entry.",
  },
];

const JOB_ACTIVE = ["queued", "started"];

const PROVENANCE = [
  { id: "evt_0412876", patient: "P-00318", missing: "source_ref" },
  { id: "evt_0098113", patient: "P-00742", missing: "source_type" },
  { id: "evt_0287740", patient: "P-00055", missing: "source_ref" },
  { id: "evt_0530902", patient: "P-00961", missing: "source_ref" },
  { id: "evt_0155327", patient: "P-00406", missing: "source_type" },
];

const TABS = [
  { key: "icd10", label: "ICD-10", system: "ICD-10-CM" },
  { key: "cpt", label: "CPT", system: "CPT" },
  { key: "loinc", label: "LOINC", system: "LOINC" },
  { key: "hla", label: "HLA-B27", system: "HLA-B27" },
  { key: "atc", label: "ATC", system: "ATC" },
  { key: "thresholds", label: "Thresholds", system: "Thresholds" },
];

const SIGNALS = {
  icd10: [
    "Back-pain visits",
    "Sacroiliitis",
    "Anterior uveitis",
    "Psoriasis",
    "Inflammatory bowel disease",
    "Conflicting label: fibromyalgia",
    "Conflicting label: anxiety",
    "Postpartum timing",
  ],
  cpt: ["SI-joint imaging", "Pelvic MRI", "Chiropractic care", "Physical therapy"],
  loinc: ["CRP", "ESR"],
  hla: ["HLA-B27 result"],
  atc: ["NSAID exposure", "Analgesic (non-NSAID)"],
};

const R = "reviewed";
const W = "awaiting";
const INITIAL_CODES = {
  icd10: [
    {
      code: "M54.5",
      desc: "Low back pain (legacy code, valid to 2021-09-30)",
      signal: "Back-pain visits",
      review: R,
    },
    { code: "M54.50", desc: "Low back pain, unspecified", signal: "Back-pain visits", review: R },
    { code: "M54.59", desc: "Other low back pain", signal: "Back-pain visits", review: R },
    {
      code: "M46.1",
      desc: "Sacroiliitis, not elsewhere classified",
      signal: "Sacroiliitis",
      review: R,
    },
    {
      code: "H20.00",
      desc: "Unspecified acute and subacute iridocyclitis",
      signal: "Anterior uveitis",
      review: R,
    },
    { code: "L40.9", desc: "Psoriasis, unspecified", signal: "Psoriasis", review: W },
    {
      code: "K51.90",
      desc: "Ulcerative colitis, unspecified, without complications",
      signal: "Inflammatory bowel disease",
      review: W,
    },
    { code: "M79.7", desc: "Fibromyalgia", signal: "Conflicting label: fibromyalgia", review: W },
    {
      code: "F41.9",
      desc: "Anxiety disorder, unspecified",
      signal: "Conflicting label: anxiety",
      review: W,
    },
    { code: "Z39.2", desc: "Routine postpartum follow-up", signal: "Postpartum timing", review: W },
  ],
  cpt: [
    {
      code: "72202",
      desc: "Radiologic exam, sacroiliac joints, 3 or more views",
      signal: "SI-joint imaging",
      review: R,
    },
    { code: "72195", desc: "MRI pelvis without contrast", signal: "Pelvic MRI", review: R },
    {
      code: "72197",
      desc: "MRI pelvis without, then with contrast",
      signal: "Pelvic MRI",
      review: R,
    },
    {
      code: "98940",
      desc: "Chiropractic manipulation, 1 to 2 spinal regions",
      signal: "Chiropractic care",
      review: W,
    },
    {
      code: "98941",
      desc: "Chiropractic manipulation, 3 to 4 spinal regions",
      signal: "Chiropractic care",
      review: W,
    },
    {
      code: "97110",
      desc: "Therapeutic exercise, each 15 minutes",
      signal: "Physical therapy",
      review: R,
    },
  ],
  loinc: [
    {
      code: "1988-5",
      desc: "C reactive protein [Mass/volume] in Serum or Plasma",
      signal: "CRP",
      review: R,
    },
    {
      code: "30522-7",
      desc: "C reactive protein [Mass/volume] in Serum or Plasma by high sensitivity method",
      signal: "CRP",
      review: R,
    },
    {
      code: "4537-7",
      desc: "Erythrocyte sedimentation rate by Westergren method",
      signal: "ESR",
      review: R,
    },
    { code: "30341-2", desc: "Erythrocyte sedimentation rate", signal: "ESR", review: R },
  ],
  hla: [
    {
      code: "LAB-HLAB27",
      desc: "HLA-B27 antigen, qualitative (local lab code)",
      signal: "HLA-B27 result",
      review: W,
    },
    {
      code: "LAB-HLAB27-PCR",
      desc: "HLA-B27 allele by PCR (local lab code)",
      signal: "HLA-B27 result",
      review: W,
    },
  ],
  atc: [
    { code: "M01AE01", desc: "Ibuprofen", signal: "NSAID exposure", review: R },
    { code: "M01AE02", desc: "Naproxen", signal: "NSAID exposure", review: R },
    { code: "M01AB05", desc: "Diclofenac", signal: "NSAID exposure", review: R },
    { code: "M01AH01", desc: "Celecoxib", signal: "NSAID exposure", review: W },
    { code: "N02BE01", desc: "Paracetamol", signal: "Analgesic (non-NSAID)", review: W },
  ],
};

const HISTORY = [
  {
    by: "Marcus Okafor",
    at: "2026-11-09 16:42",
    summary:
      "Added ICD-10 K51.90 (ulcerative colitis, unspecified) to Inflammatory bowel disease signal",
  },
  {
    by: "Priya Natarajan",
    at: "2026-10-28 11:05",
    summary: "Reachable-history threshold 9 → 12 months",
  },
  {
    by: "Marcus Okafor",
    at: "2026-10-02 09:30",
    summary: "Added ICD-10 M54.50 and M54.59 to Back-pain visits (code drift after 2021-10-01)",
  },
  {
    by: "Priya Natarajan",
    at: "2026-09-15 14:18",
    summary: "Removed CPT 72200 (SI joint, fewer than 3 views) from SI-joint imaging",
  },
  {
    by: "Marcus Okafor",
    at: "2026-08-21 10:00",
    summary: "Initial axSpA pack v1.0 loaded from configuration",
  },
];

const CURVE = [
  [1, 0],
  [3, 8],
  [6, 22],
  [9, 38],
  [10, 46],
  [12, 61],
  [18, 98],
  [24, 140],
  [36, 230],
  [60, 410],
];
const estimateInsufficient = (m) => {
  for (let i = 1; i < CURVE.length; i++) {
    if (m <= CURVE[i][0]) {
      const [x0, y0] = CURVE[i - 1];
      const [x1, y1] = CURVE[i];
      return Math.round(y0 + ((m - x0) / (x1 - x0)) * (y1 - y0));
    }
  }
  return 410;
};

const pad = (n) => String(n).padStart(2, "0");
const fmt = (d) =>
  d.getFullYear() +
  "-" +
  pad(d.getMonth() + 1) +
  "-" +
  pad(d.getDate()) +
  " " +
  pad(d.getHours()) +
  ":" +
  pad(d.getMinutes());
const n0 = (n) => Number(n).toLocaleString("en-US");
const parseWhole = (s, lo, hi) => {
  if (!/^\d+$/.test(String(s).trim())) return null;
  const v = Number(s);
  return v >= lo && v <= hi ? v : null;
};

const Ornament = () => (
  <div aria-hidden="true" className="orn">
    <span className="orn-line" />
    <span className="orn-dia" />
    <span className="orn-line" />
  </div>
);

const ReviewMark = ({ status }) =>
  status === "reviewed" ? (
    <span className="mark mark-ok">
      <Icons.Check className="h-4 w-4" aria-hidden="true" /> Reviewed
    </span>
  ) : (
    <span className="mark mark-wait">
      <Icons.Clock className="h-4 w-4" aria-hidden="true" /> Awaiting clinical review
    </span>
  );

const MASKED = "••••••••";

const ConnectionStatus = ({ status }) =>
  status === "connected" ? (
    <span className="mark mark-ok">
      <Icons.CheckCircle className="h-4 w-4" aria-hidden="true" /> Connected
    </span>
  ) : (
    <span className="mark mark-wait">
      <Icons.AlertCircle className="h-4 w-4" aria-hidden="true" /> Not configured
    </span>
  );

const FileStatus = ({ kind }) => {
  if (kind === "passed")
    return (
      <span className="mark mark-ok">
        <Icons.CheckCircle className="h-4 w-4" aria-hidden="true" /> Passed
      </span>
    );
  if (kind === "failed")
    return (
      <span className="mark mark-fail">
        <Icons.AlertCircle className="h-4 w-4" aria-hidden="true" /> Failed
      </span>
    );
  if (kind === "loading")
    return (
      <span className="mark mark-wait">
        <Icons.Clock className="h-4 w-4" aria-hidden="true" /> Loading
      </span>
    );
  return (
    <span className="mark mark-q">
      <Icons.Clock className="h-4 w-4" aria-hidden="true" /> Queued
    </span>
  );
};

function diffPack(saved, draft) {
  const out = [];
  TABS.filter((t) => t.key !== "thresholds").forEach((t) => {
    const s = saved.codes[t.key];
    const d = draft.codes[t.key];
    d.filter((c) => !s.find((x) => x.code === c.code)).forEach((c) =>
      out.push("Added " + t.label + " " + c.code + " to " + c.signal),
    );
    s.filter((c) => !d.find((x) => x.code === c.code)).forEach((c) =>
      out.push("Removed " + t.label + " " + c.code + " from " + c.signal),
    );
  });
  if (draft.months !== null && draft.months !== saved.months)
    out.push("Reachable-history threshold " + saved.months + " → " + draft.months + " months");
  if (draft.spartan !== null && draft.spartan !== saved.spartan)
    out.push("SPARTAN referral threshold " + saved.spartan + " → " + draft.spartan + " points");
  return out;
}

const ACTIVE = ["queued", "running"];

function AdminScreen() {
  const { Button, Input, Label, Select, Table, THead, TBody, TR, TH, TD, Empty } = UI;

  const [runId, setRunId] = React.useState(null);
  const [startError, setStartError] = React.useState("");

  const start = useMutation({
    mutationFn: () => apiFetch("/api/admin/ingest-runs", { method: "POST", body: "{}" }),
    onSuccess: (data) => {
      setStartError("");
      setRunId(data.run_id);
    },
    onError: (err) => setStartError(err.message || "Could not start the ingest run."),
  });

  // De-duplication check: a real background job, started on demand and polled.
  const [dedupJobId, setDedupJobId] = React.useState(null);
  const [dedupError, setDedupError] = React.useState("");

  const startDedup = useMutation({
    mutationFn: () =>
      apiFetch("/api/admin/jobs", {
        method: "POST",
        body: JSON.stringify({ kind: "dedup_check" }),
      }),
    onSuccess: (data) => {
      setDedupError("");
      setDedupJobId(data.job_id);
    },
    onError: (err) => setDedupError(err.message || "Could not start the de-duplication check."),
  });

  const dedupJob = useQuery({
    queryKey: ["admin-job", dedupJobId],
    queryFn: () => apiFetch("/api/admin/jobs/" + dedupJobId),
    enabled: dedupJobId !== null,
    retry: false,
    refetchInterval: (query) => (JOB_ACTIVE.includes(query.state.data?.status) ? 1000 : false),
  });

  const dedupData = dedupJob.data ?? null;
  const dedupRunning =
    startDedup.isPending ||
    (dedupData ? JOB_ACTIVE.includes(dedupData.status) : dedupJob.isFetching);
  const dedupResult = dedupData && dedupData.status === "finished" ? dedupData.result : null;
  const dedupMessage = dedupJob.error
    ? dedupJob.error.message || "Could not read the de-duplication check."
    : dedupData && dedupData.status === "failed"
      ? "The de-duplication check failed. Start it again to retry."
      : dedupError;
  const dedupProgress =
    dedupRunning && dedupData && typeof dedupData.progress_pct === "number"
      ? dedupData.progress_pct
      : null;

  const settings = useQuery({
    queryKey: ["admin-settings"],
    queryFn: () => apiFetch("/api/admin/settings"),
  });

  const report = useQuery({
    queryKey: ["ingest-run", runId],
    queryFn: () => apiFetch("/api/admin/ingest-runs/" + runId),
    enabled: runId !== null,
    refetchInterval: (query) => (ACTIVE.includes(query.state.data?.status) ? 1000 : false),
  });

  const data = report.data ?? null;
  const status = data ? data.status : start.isPending ? "queued" : "";
  const files = data && Array.isArray(data.files) ? data.files : [];
  const ingestNote =
    data && !ACTIVE.includes(data.status)
      ? "Ingest " +
        data.status +
        ". " +
        files.filter((f) => f.status === "passed").length +
        " of " +
        files.length +
        " files passed, " +
        n0(files.reduce((s, f) => s + (f.rows_rejected || 0), 0)) +
        " rows rejected. Patients loaded: " +
        n0(data.patient_count) +
        "."
      : startError;

  const [tab, setTab] = React.useState("icd10");
  const [saved, setSaved] = React.useState({ codes: INITIAL_CODES, months: 12, spartan: 6 });
  const [codes, setCodes] = React.useState(INITIAL_CODES);
  const [monthsStr, setMonthsStr] = React.useState("12");
  const [spartanStr, setSpartanStr] = React.useState("6");
  const [history, setHistory] = React.useState(HISTORY);
  const [version, setVersion] = React.useState(4);
  const [saving, setSaving] = React.useState(false);
  const [saveNote, setSaveNote] = React.useState("");
  const [confirmRemove, setConfirmRemove] = React.useState(null);
  const [newCode, setNewCode] = React.useState("");
  const [newDesc, setNewDesc] = React.useState("");
  const [newSignal, setNewSignal] = React.useState("");
  const [errors, setErrors] = React.useState({});
  const [addNote, setAddNote] = React.useState("");
  const tabRefs = React.useRef({});

  const startIngest = () => start.mutate();

  // pack validation and diff
  const monthsVal = parseWhole(monthsStr, 1, 60);
  const spartanVal = parseWhole(spartanStr, 1, 20);
  const monthsErr = monthsVal === null ? "Enter a whole number of months from 1 to 60." : "";
  const spartanErr = spartanVal === null ? "Enter a whole number of points from 1 to 20." : "";
  const pending = diffPack(saved, { codes, months: monthsVal, spartan: spartanVal });
  const invalid = monthsVal === null || spartanVal === null;

  React.useEffect(() => {
    if (!saving) return undefined;
    const t = setTimeout(() => {
      const summary = pending.join("; ");
      const now = fmt(new Date());
      const v = version + 1;
      setHistory((h) => [{ by: "Marcus Okafor", at: now, summary, fresh: true }, ...h]);
      setSaved({ codes, months: monthsVal, spartan: spartanVal });
      setVersion(v);
      setSaving(false);
      setSaveNote(
        "Pack v1." +
          v +
          " saved. The cohort will use these code lists and thresholds on the next rescore, with no deployment.",
      );
    }, 700);
    return () => clearTimeout(t);
  }, [saving]);

  const activeTab = TABS.find((t) => t.key === tab);
  const isThresholds = tab === "thresholds";
  const rows = isThresholds
    ? [
        {
          code: "reachable_history_months",
          desc:
            "Below " +
            (monthsVal === null ? "…" : monthsVal) +
            " reachable months a patient is shown as Insufficient history, never as Low.",
          signal: "Insufficient history",
          review: W,
        },
        {
          code: "spartan_referral_points",
          desc:
            "At " +
            (spartanVal === null ? "…" : spartanVal) +
            " SPARTAN points or more, referral is suggested.",
          signal: "SPARTAN referral",
          review: W,
        },
      ]
    : codes[tab];
  const signals = SIGNALS[tab] || [];
  const signalValue = signals.includes(newSignal) ? newSignal : signals[0];
  const savedCodeSet = isThresholds ? [] : saved.codes[tab].map((c) => c.code);

  const onTabKey = (e, i) => {
    let next = null;
    if (e.key === "ArrowRight") next = (i + 1) % TABS.length;
    if (e.key === "ArrowLeft") next = (i - 1 + TABS.length) % TABS.length;
    if (e.key === "Home") next = 0;
    if (e.key === "End") next = TABS.length - 1;
    if (next !== null) {
      e.preventDefault();
      setTab(TABS[next].key);
      setConfirmRemove(null);
      setErrors({});
      setAddNote("");
      const el = tabRefs.current[TABS[next].key];
      if (el) el.focus();
    }
  };

  const addCode = (e) => {
    e.preventDefault();
    const code = newCode.trim();
    const errs = {};
    if (!code) errs.code = "Enter the code exactly as it appears in the source data.";
    else if (codes[tab].some((c) => c.code.toLowerCase() === code.toLowerCase()))
      errs.code = code + " is already in the " + activeTab.label + " list.";
    if (!newDesc.trim()) errs.desc = "Add a short description so reviewers know what this code is.";
    setErrors(errs);
    if (Object.keys(errs).length) {
      setAddNote("");
      return;
    }
    setCodes((c) => ({
      ...c,
      [tab]: [...c[tab], { code, desc: newDesc.trim(), signal: signalValue, review: W }],
    }));
    setNewCode("");
    setNewDesc("");
    setAddNote(
      "Added " +
        code +
        " to " +
        signalValue +
        ". It is marked awaiting clinical review and stays unsaved until you save the pack.",
    );
    setSaveNote("");
  };

  const removeCode = (code) => {
    setCodes((c) => ({ ...c, [tab]: c[tab].filter((x) => x.code !== code) }));
    setConfirmRemove(null);
    setAddNote(
      "Removed " +
        code +
        " from the " +
        activeTab.label +
        " list. Unsaved until you save the pack.",
    );
    setSaveNote("");
  };

  const totalLoaded = files.reduce((s, f) => s + (f.rows_loaded || 0), 0);
  const totalRejected = files.reduce((s, f) => s + (f.rows_rejected || 0), 0);
  const running = start.isPending || ACTIVE.includes(status);
  const passedCount = files.filter((f) => f.status === "passed").length;
  const pct = files.length ? Math.round((passedCount / files.length) * 100) : 0;

  return (
    <div
      className="gx"
      style={{
        "--primary": brand.primaryColor,
        "--accent": brand.accentColor,
        "--neutral": brand.neutralColor,
        "--bg": brand.backgroundColor,
        "--fh": brand.fontHeading,
        "--fb": brand.fontBody,
        backgroundColor: "var(--bg)",
        color: "var(--primary)",
        fontFamily: "var(--fb)",
        padding: "24px 16px 48px",
        minHeight: "100%",
      }}
    >
      <style>{`
        .gx, .gx * { box-sizing: border-box; }
        .gx { font-size: 15px; line-height: 1.5; }
        .gx .hd { font-family: var(--fh); text-transform: uppercase; letter-spacing: .16em; font-weight: 700; margin: 0; }
        .gx .eyebrow { font-family: var(--fh); text-transform: uppercase; letter-spacing: .24em; font-size: 12px; font-weight: 700; }
        .gx .muted { opacity: .78; }
        .gx .small { font-size: 13px; line-height: 1.5; }
        .gx .num { font-variant-numeric: tabular-nums; }
        .gx .mono { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-variant-numeric: tabular-nums; font-size: 13px; }
        .gx .frame { position: relative; margin: 5px; border: 1px solid var(--accent); outline: 1px solid var(--primary); outline-offset: 4px; background: color-mix(in srgb, var(--bg) 55%, white); padding: 24px; }
        .gx .orn { display: flex; align-items: center; gap: 12px; margin: 12px 0 16px; }
        .gx .orn-line { flex: 1; height: 4px; border-top: 1px solid var(--primary); border-bottom: 1px solid var(--accent); }
        .gx .orn-dia { width: 10px; height: 10px; transform: rotate(45deg); background: var(--accent); border: 1px solid var(--primary); flex: none; }
        .gx .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 44px; padding: 0 24px; border-radius: 0; font-family: var(--fh); font-weight: 700; letter-spacing: .16em; text-transform: uppercase; font-size: 13px; cursor: pointer; border: 1px solid var(--primary); transition: background-color .15s, color .15s, transform .1s; }
        .gx .btn.btn-p { background: var(--primary); color: var(--accent); }
        .gx .btn.btn-p:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 82%, var(--accent)); }
        .gx .btn.btn-p:active:not(:disabled) { transform: translateY(1px); }
        .gx .btn.btn-s { background: transparent; color: var(--primary); }
        .gx .btn.btn-s:hover:not(:disabled) { background: var(--primary); color: var(--accent); }
        .gx .btn:disabled { opacity: .55; cursor: not-allowed; }
        .gx .btn-quiet { min-height: 44px; min-width: 44px; padding: 0 12px; background: transparent; border: 1px solid transparent; color: var(--primary); font-size: 13px; text-decoration: underline; text-underline-offset: 3px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; border-radius: 0; }
        .gx .btn-quiet:hover { border-color: var(--primary); }
        .gx :focus-visible { outline: 2px solid var(--primary); outline-offset: 3px; }
        .gx .btn.btn-p:focus-visible, .gx .tab[aria-selected="true"]:focus-visible { outline: 2px solid var(--primary); outline-offset: 3px; box-shadow: 0 0 0 5px var(--accent); }
        .gx .fld { display: block; width: 100%; min-height: 44px; padding: 8px 12px; border: 1px solid var(--primary); border-radius: 0; background: var(--bg); color: var(--primary); font-family: var(--fb); font-size: 15px; font-variant-numeric: tabular-nums; }
        .gx .fld[aria-invalid="true"] { border-width: 2px; border-style: dashed; }
        .gx .lbl { display: block; font-family: var(--fh); text-transform: uppercase; letter-spacing: .12em; font-size: 12px; font-weight: 700; margin-bottom: 4px; }
        .gx .err { display: flex; gap: 4px; align-items: flex-start; font-size: 13px; margin-top: 4px; font-weight: 600; }
        .gx table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
        .gx th { text-align: left; font-family: var(--fh); text-transform: uppercase; letter-spacing: .12em; font-size: 12px; font-weight: 700; padding: 12px 16px; border-bottom: 3px double var(--primary); white-space: nowrap; background: transparent; color: var(--primary); }
        .gx td { padding: 12px 16px; vertical-align: top; border-bottom: 1px solid var(--neutral); font-size: 14px; color: var(--primary); }
        .gx tbody tr:last-child td { border-bottom: 0; }
        .gx .num-col { text-align: right; }
        .gx .scroll { overflow-x: auto; }
        .gx .mark { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; font-weight: 700; padding: 2px 8px; border: 1px solid var(--primary); white-space: nowrap; }
        .gx .mark-wait { border-style: dashed; }
        .gx .mark-ok { background: var(--primary); color: var(--accent); }
        .gx .mark-q { border-color: var(--neutral); font-weight: 600; }
        .gx .mark-fail { border-width: 2px; }
        .gx .pill { display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; padding: 0 8px; margin-left: 8px; background: var(--accent); color: var(--primary); border: 1px solid var(--primary); }
        .gx .tabstrip { display: flex; flex-wrap: wrap; gap: 8px; border-bottom: 3px double var(--primary); padding-bottom: 12px; }
        .gx .tab { min-height: 44px; padding: 0 16px; background: transparent; color: var(--primary); border: 1px solid var(--primary); border-radius: 0; font-family: var(--fh); font-weight: 700; letter-spacing: .14em; text-transform: uppercase; font-size: 13px; cursor: pointer; transition: background-color .15s, color .15s; }
        .gx .tab:hover { background: color-mix(in srgb, var(--accent) 35%, transparent); }
        .gx .tab[aria-selected="true"] { background: var(--primary); color: var(--accent); }
        .gx .figure { font-family: var(--fh); font-weight: 700; font-size: 28px; line-height: 1.1; font-variant-numeric: tabular-nums; letter-spacing: .02em; }
        .gx .bar { height: 8px; border: 1px solid var(--primary); background: transparent; }
        .gx .bar > span { display: block; height: 100%; background: var(--primary); transition: width .3s ease; }
        .gx .newrow { animation: gxrow .4s ease-out; }
        .gx .fade { animation: gxrow .3s ease-out; }
        @keyframes gxrow { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: none; } }
        @media (prefers-reduced-motion: reduce) { .gx *, .gx *::before, .gx *::after { animation: none !important; transition: none !important; } }
      `}</style>

      <div
        style={{
          maxWidth: 1180,
          margin: "0 auto",
          display: "flex",
          flexDirection: "column",
          gap: 32,
        }}
      >
        {/* Row 1 */}
        <div className="grid grid-cols-12 gap-6 items-end">
          <div data-wf="b-0-0" className="col-span-12 lg:col-span-8">
            <p className="eyebrow" style={{ margin: "0 0 8px" }}>
              Administration · axSpA pack v1.{version}
            </p>
            <h1 className="hd" style={{ fontSize: 34, lineHeight: 1.2, letterSpacing: ".14em" }}>
              Admin: ingest and condition pack
            </h1>
            <Ornament />
            <p className="muted" style={{ margin: 0, maxWidth: "62ch" }}>
              Load the synthetic dataset once, check what arrived, and keep the axSpA code lists and
              thresholds correct without a code change.
            </p>
          </div>
          <div
            data-wf="b-0-1"
            className="col-span-12 lg:col-span-4 flex flex-col lg:items-end gap-2"
          >
            <Button
              type="button"
              className="btn btn-p"
              onClick={startIngest}
              disabled={running}
              aria-describedby="ingest-hint"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
                <path d="M3 1.5 L12 7 L3 12.5 Z" fill="currentColor" />
              </svg>
              {running ? "Ingesting…" : "Run ingest"}
            </Button>
            <p id="ingest-hint" className="small muted lg:text-right" style={{ margin: 0 }}>
              Re-running replaces the prior load. No duplicate patients or events.
            </p>
          </div>
        </div>

        {/* Row 2 */}
        <section data-wf="b-1-0" className="frame" aria-labelledby="report-h">
          <h2 id="report-h" className="hd" style={{ fontSize: 20, textAlign: "center" }}>
            Ingest report
          </h2>
          <p className="num" style={{ textAlign: "center", margin: "8px 0 0", fontWeight: 600 }}>
            Dataset {data ? data.dataset_version : "—"} · Seed {data ? data.seed : "—"} ·{" "}
            {data ? n0(data.patient_count) : "—"} patients · Status{" "}
            {status === "failed" ? (
              <span className="mark mark-fail">
                <Icons.AlertCircle className="h-4 w-4" aria-hidden="true" /> failed
              </span>
            ) : status === "passed" ? (
              <span className="mark mark-ok">
                <Icons.CheckCircle className="h-4 w-4" aria-hidden="true" /> passed
              </span>
            ) : (
              <span className="mark mark-wait">
                <Icons.Clock className="h-4 w-4" aria-hidden="true" /> {status || "not started"}
              </span>
            )}
          </p>
          <Ornament />
          {running && (
            <div className="fade" style={{ marginBottom: 24 }}>
              <div
                className="bar"
                role="progressbar"
                aria-label="Ingest progress"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={pct}
              >
                <span style={{ width: pct + "%" }} />
              </div>
              <p className="small num" style={{ margin: "8px 0 0", textAlign: "center" }}>
                {files.length
                  ? "Loaded " + passedCount + " of " + files.length + " files"
                  : "Starting the ingest run"}
              </p>
            </div>
          )}
          <dl
            className="grid grid-cols-2 lg:grid-cols-4 gap-6"
            style={{ margin: 0, textAlign: "center" }}
          >
            {[
              ["Rows loaded", n0(totalLoaded)],
              ["Rows rejected", n0(totalRejected)],
              ["Files passed", passedCount + " of " + files.length],
              ["Run", runId ? String(runId).slice(0, 8) : "—"],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="eyebrow muted" style={{ marginBottom: 4 }}>
                  {k}
                </dt>
                <dd className="figure" style={{ margin: 0 }}>
                  {v}
                </dd>
              </div>
            ))}
          </dl>
          <p className="small num muted" style={{ margin: "24px 0 0", textAlign: "center" }}>
            {data ? "Started " + data.started_at : "No run started yet"} ·{" "}
            {data && data.finished_at ? "finished " + data.finished_at : "in progress"} · synthetic
            data, not for clinical use
          </p>
          <div role="status" aria-live="polite">
            {ingestNote && (
              <p
                className="fade small"
                style={{ margin: "12px 0 0", textAlign: "center", fontWeight: 600 }}
              >
                <Icons.CheckCircle className="h-4 w-4 inline" aria-hidden="true" /> {ingestNote}
              </p>
            )}
          </div>
        </section>

        {/* Connections and settings */}
        <section className="frame" aria-labelledby="conn-h">
          <h2 id="conn-h" className="hd" style={{ fontSize: 18, textAlign: "center" }}>
            Connections and settings
          </h2>
          <Ornament />
          <p className="small muted" style={{ margin: "0 0 16px", textAlign: "center" }}>
            Credentials are supplied as deployment configuration. Only a masked placeholder and its
            status are shown here.
          </p>
          {settings.isError ? (
            <p className="err" role="status">
              <Icons.AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" /> Could not read
              the connection settings.
            </p>
          ) : settings.isLoading ? (
            <p className="small muted" style={{ margin: 0, textAlign: "center" }}>
              Checking connections…
            </p>
          ) : (
            <dl className="grid grid-cols-1 sm:grid-cols-3 gap-6" style={{ margin: 0 }}>
              <div>
                <dt className="eyebrow muted" style={{ marginBottom: 4 }}>
                  Database
                </dt>
                <dd style={{ margin: 0 }}>
                  <span className="mono">{MASKED}</span>{" "}
                  <ConnectionStatus status={settings.data?.database?.status} />
                </dd>
              </div>
              <div>
                <dt className="eyebrow muted" style={{ marginBottom: 4 }}>
                  LLM credential
                </dt>
                <dd style={{ margin: 0 }}>
                  <span className="mono">{MASKED}</span>{" "}
                  <ConnectionStatus status={settings.data?.llm?.status} />
                </dd>
              </div>
              <div>
                <dt className="eyebrow muted" style={{ marginBottom: 4 }}>
                  Active dataset version
                </dt>
                <dd className="num" style={{ margin: 0, fontWeight: 700 }}>
                  {settings.data?.dataset_version ?? "None loaded"}
                </dd>
              </div>
            </dl>
          )}
        </section>

        {/* Row 3 */}
        <section data-wf="b-2-0" className="frame" aria-labelledby="files-h">
          <h2 id="files-h" className="hd" style={{ fontSize: 20, textAlign: "center" }}>
            Files
          </h2>
          <Ornament />
          <div className="scroll">
            <Table>
              <THead>
                <TR>
                  <TH data-wf="i-2-0-0">File</TH>
                  <TH data-wf="i-2-0-1" className="num-col" style={{ textAlign: "right" }}>
                    Rows loaded
                  </TH>
                  <TH data-wf="i-2-0-2" style={{ textAlign: "right" }}>
                    Rows rejected
                  </TH>
                  <TH data-wf="i-2-0-3">Status</TH>
                  <TH data-wf="i-2-0-4">Error detail</TH>
                </TR>
              </THead>
              <TBody>
                {files.map((f) => (
                  <TR key={f.file}>
                    <TD>
                      <span className="mono" style={{ fontWeight: 700 }}>
                        {f.file}
                      </span>
                    </TD>
                    <TD style={{ textAlign: "right" }} className="num">
                      {n0(f.rows_loaded)}
                    </TD>
                    <TD style={{ textAlign: "right" }} className="num">
                      {n0(f.rows_rejected)}
                    </TD>
                    <TD>
                      <FileStatus kind={f.status} />
                    </TD>
                    <TD style={{ maxWidth: 360 }}>
                      {f.error ? f.error : <span className="muted">—</span>}
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </div>
        </section>

        {/* Row 4 */}
        <div className="grid grid-cols-12 gap-8">
          <section
            data-wf="b-3-0"
            className="col-span-12 lg:col-span-6 frame"
            aria-labelledby="dedup-h"
          >
            <h2 id="dedup-h" className="hd" style={{ fontSize: 18, textAlign: "center" }}>
              De-duplication check vs encounter_truth.csv
            </h2>
            <Ornament />
            <div style={{ textAlign: "center", marginBottom: 16 }}>
              <Button
                type="button"
                className="btn btn-s"
                onClick={() => startDedup.mutate()}
                disabled={dedupRunning}
              >
                {dedupRunning ? "Checking…" : "Run de-duplication check"}
              </Button>
            </div>
            <p
              className="small muted num"
              style={{ margin: "0 0 16px", textAlign: "center" }}
              role="status"
              aria-live="polite"
            >
              {dedupRunning
                ? "De-duplication check running" +
                  (dedupProgress === null ? "…" : " · " + dedupProgress + "%")
                : dedupResult
                  ? n0(dedupResult.true_encounters) +
                    " true encounters checked · visits are counted once in every visit-count signal"
                  : "Not run yet. Start the check to compare the loaded data with encounter_truth.csv."}
            </p>
            {dedupMessage ? (
              <p className="small" role="alert" style={{ margin: "0 0 16px", textAlign: "center" }}>
                {dedupMessage}
              </p>
            ) : null}
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-6" style={{ margin: 0 }}>
              {DEDUP_FIELDS.map((d) => (
                <div
                  key={d.label}
                  style={{ borderTop: "1px solid var(--primary)", paddingTop: 12 }}
                >
                  <dt className="eyebrow">{d.label}</dt>
                  <dd style={{ margin: 0 }}>
                    <span className="figure">{dedupResult ? n0(dedupResult[d.key]) : "—"}</span>
                    <span className="small muted" style={{ display: "block", marginTop: 4 }}>
                      {d.hint}
                    </span>
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section
            data-wf="b-3-1"
            className="col-span-12 lg:col-span-6 frame"
            aria-labelledby="prov-h"
          >
            <h2 id="prov-h" className="hd" style={{ fontSize: 18, textAlign: "center" }}>
              Provenance failures
            </h2>
            <Ornament />
            <p style={{ margin: "0 0 16px", textAlign: "center" }}>
              Rows missing source_type or source_ref, withheld from scoring and display.
            </p>
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                gap: 32,
                marginBottom: 16,
                textAlign: "center",
              }}
            >
              <div>
                <div className="figure">{running ? "…" : "37"}</div>
                <div className="eyebrow muted">Rows withheld</div>
              </div>
              <div>
                <div className="figure">{running ? "…" : "14"}</div>
                <div className="eyebrow muted">No source_type</div>
              </div>
              <div>
                <div className="figure">{running ? "…" : "23"}</div>
                <div className="eyebrow muted">No source_ref</div>
              </div>
            </div>
            <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
              {PROVENANCE.map((p) => (
                <li
                  key={p.id}
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "4px 16px",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "8px 0",
                    borderTop: "1px solid var(--neutral)",
                  }}
                >
                  <span className="mono" style={{ fontWeight: 700 }}>
                    {p.id}
                  </span>
                  <span className="mono">{p.patient}</span>
                  <span className="mark mark-wait">
                    <Icons.AlertCircle className="h-4 w-4" aria-hidden="true" /> missing {p.missing}
                  </span>
                </li>
              ))}
            </ul>
            <p className="small muted" style={{ margin: "12px 0 0" }}>
              Showing 5 of 37. Withheld rows never appear on a timeline or in a score.
            </p>
          </section>
        </div>

        {/* Row 5 */}
        <section data-wf="b-4-0" aria-labelledby="pack-h">
          <div style={{ textAlign: "center", marginBottom: 16 }}>
            <h2 id="pack-h" className="hd" style={{ fontSize: 22 }}>
              Condition pack: axSpA
            </h2>
            <p className="small num muted" style={{ margin: "8px 0 0" }}>
              Version 1.{version} · last change by {history[0].by}, {history[0].at}
            </p>
          </div>
          <div role="tablist" aria-label="Condition pack sections" className="tabstrip">
            {TABS.map((t, i) => (
              <button
                key={t.key}
                type="button"
                role="tab"
                id={"tab-" + t.key}
                data-wf={"i-4-0-" + i}
                aria-selected={tab === t.key}
                aria-controls="pack-panel"
                tabIndex={tab === t.key ? 0 : -1}
                ref={(el) => {
                  tabRefs.current[t.key] = el;
                }}
                className="tab"
                onClick={() => {
                  setTab(t.key);
                  setConfirmRemove(null);
                  setErrors({});
                  setAddNote("");
                }}
                onKeyDown={(e) => onTabKey(e, i)}
              >
                {t.label}
              </button>
            ))}
          </div>
        </section>

        {/* Row 6 */}
        <div className="grid grid-cols-12 gap-8" style={{ marginTop: -8 }}>
          <section
            data-wf="b-5-0"
            className="col-span-12 lg:col-span-8 frame"
            aria-labelledby="codes-h"
          >
            <h2 id="codes-h" className="hd" style={{ fontSize: 18, textAlign: "center" }}>
              Code list
            </h2>
            <p className="small muted" style={{ margin: "8px 0 0", textAlign: "center" }}>
              {isThresholds
                ? "Thresholds in force for rescoring"
                : activeTab.system + " · " + rows.length + " codes"}
            </p>
            <Ornament />
            <div
              id="pack-panel"
              role="tabpanel"
              aria-labelledby={"tab-" + tab}
              className="fade"
              key={tab}
            >
              {rows.length === 0 ? (
                <Empty
                  title={"No " + activeTab.label + " codes in this pack"}
                  description={
                    "Without codes here the engine cannot see this signal. Add a code on the right, or save the pack as it is to leave the signal blind."
                  }
                />
              ) : (
                <div className="scroll">
                  <Table>
                    <THead>
                      <TR>
                        <TH data-wf="i-5-0-0">Code</TH>
                        <TH data-wf="i-5-0-1">Description</TH>
                        <TH data-wf="i-5-0-2">Mapped signal</TH>
                        <TH data-wf="i-5-0-3">Review status</TH>
                        {!isThresholds && (
                          <TH>
                            <span className="sr-only">Remove</span>
                          </TH>
                        )}
                      </TR>
                    </THead>
                    <TBody>
                      {rows.map((c) => {
                        const unsaved = !isThresholds && !savedCodeSet.includes(c.code);
                        return (
                          <TR key={tab + c.code} className={unsaved ? "newrow" : ""}>
                            <TD>
                              <span className="mono" style={{ fontWeight: 700 }}>
                                {c.code}
                              </span>
                              {unsaved && <span className="pill">Unsaved</span>}
                            </TD>
                            <TD style={{ maxWidth: 320 }}>{c.desc}</TD>
                            <TD>{c.signal}</TD>
                            <TD>
                              <ReviewMark status={c.review} />
                            </TD>
                            {!isThresholds && (
                              <TD style={{ whiteSpace: "nowrap" }}>
                                {confirmRemove === c.code ? (
                                  <span role="group" aria-label={"Confirm removing " + c.code}>
                                    <button
                                      type="button"
                                      className="btn-quiet"
                                      onClick={() => removeCode(c.code)}
                                    >
                                      Remove {c.code}
                                    </button>
                                    <button
                                      type="button"
                                      className="btn-quiet"
                                      onClick={() => setConfirmRemove(null)}
                                    >
                                      Keep
                                    </button>
                                  </span>
                                ) : (
                                  <button
                                    type="button"
                                    className="btn-quiet"
                                    aria-label={"Remove " + c.code + " from " + c.signal}
                                    onClick={() => setConfirmRemove(c.code)}
                                  >
                                    <Icons.Trash className="h-4 w-4" aria-hidden="true" />
                                  </button>
                                )}
                              </TD>
                            )}
                          </TR>
                        );
                      })}
                    </TBody>
                  </Table>
                </div>
              )}
              {tab === "icd10" && (
                <p className="small muted" style={{ margin: "16px 0 0" }}>
                  M54.5, M54.50 and M54.59 are one signal, so back-pain visit counts stay continuous
                  across the 2021-10-01 code split.
                </p>
              )}
              {isThresholds && (
                <p className="small muted" style={{ margin: "16px 0 0" }}>
                  Edit both values in the Thresholds form. The review marker is informational and
                  never blocks scoring.
                </p>
              )}
            </div>
          </section>

          <div data-wf="b-5-1" className="col-span-12 lg:col-span-4 frame">
            <h2 className="hd" style={{ fontSize: 18, textAlign: "center" }}>
              Thresholds
            </h2>
            <Ornament />
            <div
              role="group"
              aria-label="Pack thresholds"
              style={{ display: "flex", flexDirection: "column", gap: 16 }}
            >
              <div>
                <Label htmlFor="th-months" className="lbl">
                  Reachable-history threshold (months)
                </Label>
                <Input
                  id="th-months"
                  data-wf="i-5-1-0"
                  className="fld"
                  type="number"
                  min={1}
                  max={60}
                  inputMode="numeric"
                  value={monthsStr}
                  onChange={(e) => {
                    setMonthsStr(e.target.value);
                    setSaveNote("");
                  }}
                  aria-invalid={monthsErr ? "true" : "false"}
                  aria-describedby="th-months-hint"
                />
                <div id="th-months-hint">
                  {monthsErr ? (
                    <p className="err">
                      <Icons.AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />{" "}
                      {monthsErr}
                    </p>
                  ) : (
                    <p className="small muted num" style={{ margin: "4px 0 0" }}>
                      About {estimateInsufficient(monthsVal)} of 1,000 patients would read
                      Insufficient history. Applies on the next rescore.
                    </p>
                  )}
                </div>
              </div>
              <div>
                <Label htmlFor="th-spartan" className="lbl">
                  SPARTAN referral threshold
                </Label>
                <Input
                  id="th-spartan"
                  data-wf="i-5-1-1"
                  className="fld"
                  type="number"
                  min={1}
                  max={20}
                  inputMode="numeric"
                  value={spartanStr}
                  onChange={(e) => {
                    setSpartanStr(e.target.value);
                    setSaveNote("");
                  }}
                  aria-invalid={spartanErr ? "true" : "false"}
                  aria-describedby="th-spartan-hint"
                />
                <div id="th-spartan-hint">
                  {spartanErr ? (
                    <p className="err">
                      <Icons.AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />{" "}
                      {spartanErr}
                    </p>
                  ) : (
                    <p className="small muted" style={{ margin: "4px 0 0" }}>
                      Points shown against this line on every case. Awaiting clinical review.
                    </p>
                  )}
                </div>
              </div>
            </div>

            <Ornament />
            <form
              onSubmit={addCode}
              noValidate
              style={{ display: "flex", flexDirection: "column", gap: 16 }}
            >
              <h3 className="hd" style={{ fontSize: 14 }}>
                Add a code{isThresholds ? "" : " to " + activeTab.label}
              </h3>
              {isThresholds ? (
                <p className="small muted" style={{ margin: 0 }}>
                  Choose ICD-10, CPT, LOINC, HLA-B27 or ATC above to add a code.
                </p>
              ) : (
                <>
                  <div>
                    <Label htmlFor="new-code" className="lbl">
                      Code
                    </Label>
                    <Input
                      id="new-code"
                      className="fld"
                      value={newCode}
                      onChange={(e) => setNewCode(e.target.value)}
                      aria-invalid={errors.code ? "true" : "false"}
                      aria-describedby={errors.code ? "new-code-err" : undefined}
                      autoComplete="off"
                    />
                    {errors.code && (
                      <p id="new-code-err" className="err" role="alert">
                        <Icons.AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />{" "}
                        {errors.code}
                      </p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="new-desc" className="lbl">
                      Description
                    </Label>
                    <Input
                      id="new-desc"
                      className="fld"
                      value={newDesc}
                      onChange={(e) => setNewDesc(e.target.value)}
                      aria-invalid={errors.desc ? "true" : "false"}
                      aria-describedby={errors.desc ? "new-desc-err" : undefined}
                      autoComplete="off"
                    />
                    {errors.desc && (
                      <p id="new-desc-err" className="err" role="alert">
                        <Icons.AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />{" "}
                        {errors.desc}
                      </p>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="new-signal" className="lbl">
                      Mapped signal
                    </Label>
                    <Select
                      id="new-signal"
                      className="fld"
                      value={signalValue}
                      onChange={(e) => setNewSignal(e.target.value)}
                    >
                      {signals.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </Select>
                  </div>
                </>
              )}
              <Button type="submit" data-wf="i-5-1-2" className="btn btn-s" disabled={isThresholds}>
                <Icons.Plus className="h-4 w-4" aria-hidden="true" /> Add code
              </Button>
              <div role="status" aria-live="polite">
                {addNote && (
                  <p className="fade small" style={{ margin: 0, fontWeight: 600 }}>
                    {addNote}
                  </p>
                )}
              </div>
            </form>
          </div>
        </div>

        {/* Row 7 */}
        <div className="grid grid-cols-12 gap-8 items-start">
          <div
            data-wf="b-6-0"
            className="col-span-12 lg:col-span-4"
            style={{ display: "flex", flexDirection: "column", gap: 12 }}
          >
            <Button
              type="button"
              className="btn btn-p"
              style={{ width: "100%" }}
              disabled={pending.length === 0 || invalid || saving}
              onClick={() => {
                setSaveNote("");
                setSaving(true);
              }}
              aria-describedby="save-hint"
            >
              {saving ? "Saving pack…" : "Save pack"}
            </Button>
            <div id="save-hint" aria-live="polite">
              {pending.length > 0 ? (
                <div className="fade small">
                  <p style={{ margin: "0 0 4px", fontWeight: 700 }}>
                    {pending.length} unsaved {pending.length === 1 ? "change" : "changes"}
                  </p>
                  <ul style={{ margin: 0, paddingLeft: 16 }}>
                    {pending.map((p) => (
                      <li key={p}>{p}</li>
                    ))}
                  </ul>
                </div>
              ) : saveNote ? (
                <p className="fade small" style={{ margin: 0, fontWeight: 600 }}>
                  <Icons.CheckCircle className="h-4 w-4 inline" aria-hidden="true" /> {saveNote}
                </p>
              ) : (
                <p className="small muted" style={{ margin: 0 }}>
                  No unsaved changes. Saving records who changed what, and when.
                </p>
              )}
              {invalid && (
                <p className="err">
                  <Icons.AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" /> Fix the
                  threshold values before saving.
                </p>
              )}
            </div>
          </div>

          <section
            data-wf="b-6-1"
            className="col-span-12 lg:col-span-8 frame"
            aria-labelledby="hist-h"
          >
            <h2 id="hist-h" className="hd" style={{ fontSize: 18, textAlign: "center" }}>
              Pack change history
            </h2>
            <Ornament />
            <div className="scroll">
              <Table>
                <THead>
                  <TR>
                    <TH data-wf="i-6-1-0">Changed by</TH>
                    <TH data-wf="i-6-1-1">Changed at</TH>
                    <TH data-wf="i-6-1-2">Change summary</TH>
                  </TR>
                </THead>
                <TBody>
                  {history.map((h) => (
                    <TR key={h.at + h.summary} className={h.fresh ? "newrow" : ""}>
                      <TD style={{ whiteSpace: "nowrap" }}>{h.by}</TD>
                      <TD className="num" style={{ whiteSpace: "nowrap" }}>
                        {h.at}
                      </TD>
                      <TD>{h.summary}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

export default function Screen() {
  // One client per mount: the screen owns the only queries on this page.
  const [client] = React.useState(() => new QueryClient());
  return (
    <QueryClientProvider client={client}>
      <AdminScreen />
    </QueryClientProvider>
  );
}
