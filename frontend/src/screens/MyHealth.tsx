// @ts-nocheck -- generated from the approved design under its JS runtime contract; not hand-written TypeScript.
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from "react";

import { Icons } from "@/lib/icons";
import { useNavigate } from "@/lib/navigate";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const { Check, ChevronRight, Calendar, Download, ArrowRight, AlertCircle, CheckCircle } = Icons;

const PRIMARY = "#111111";
const ACCENT = "#0e766e";
const RADIUS = "2px";

const SECTIONS = [
  { key: "symptom", label: "Symptom check", wf: "i-2-0-0" },
  { key: "prep", label: "Visit prep", wf: "i-2-0-1" },
  { key: "updates", label: "Updates", wf: "i-2-0-2" },
];

const OPTIONS = [
  { value: "yes", label: "Yes", wf: "i-4-0-0" },
  { value: "no", label: "No", wf: "i-4-0-1" },
  { value: "unsure", label: "Not sure", wf: "i-4-0-2" },
];

const QUESTIONS = [
  {
    id: "q1",
    topic: "Duration",
    text: "Has your back or buttock pain lasted longer than three months?",
    why: "Why we ask: long-running back pain is treated differently from a short strain, so the length matters to your clinician.",
  },
  {
    id: "q2",
    topic: "Onset age",
    text: "Did your back symptoms first start before you turned 45?",
    why: "Why we ask: the age pain first began helps your clinician narrow down what to look for.",
  },
  {
    id: "q3",
    topic: "Activity",
    text: "Does your pain improve when you move or exercise, rather than with rest?",
    why: "Why we ask: pain that eases with movement follows a different pattern from pain that eases with rest.",
  },
  {
    id: "q4",
    topic: "Morning stiffness",
    text: "Does your back feel stiff in the morning for more than 30 minutes?",
    why: "Why we ask: morning stiffness that eases with movement is a pattern worth noting for your clinician.",
  },
  {
    id: "q5",
    topic: "Night pain",
    text: "Do you ever wake in the second half of the night because of back pain?",
    why: "Why we ask: pain that wakes you in the early hours is easy to forget in a short appointment, so it helps to record it now.",
  },
  {
    id: "q6",
    topic: "Alternating pain",
    text: "Does the pain ever move from one side of your buttocks to the other?",
    why: "Why we ask: pain that alternates between sides is a specific detail your clinician will want to know.",
  },
  {
    id: "q7",
    topic: "Medication response",
    text: "Have anti-inflammatory painkillers such as ibuprofen or naproxen clearly eased your pain?",
    why: "Why we ask: how well these particular painkillers work tells your clinician something your records may not have captured.",
  },
  {
    id: "q8",
    topic: "Family history",
    text: "Has anyone in your immediate family been diagnosed with a long-term spine or joint condition?",
    why: "Why we ask: some back conditions run in families, so a relative's history can add useful context.",
  },
  {
    id: "q9",
    topic: "Eyes",
    text: "Have you ever had a painful, red eye that a doctor treated as inflammation?",
    why: "Why we ask: eye inflammation and back pain can be linked, and an eye visit may sit in records your clinician hasn't seen.",
  },
  {
    id: "q10",
    topic: "Skin & gut",
    text: "Have you been treated for psoriasis, or for gut inflammation such as Crohn's or colitis?",
    why: "Why we ask: these conditions sometimes travel alongside back symptoms, so they are worth mentioning together.",
  },
  {
    id: "q11",
    topic: "Self-paid care",
    text: "Have you paid out of pocket for care — a chiropractor or physiotherapist — that may not be in your records?",
    why: "Why we ask: care you paid for yourself often never reaches your medical record, so telling us keeps your history complete.",
  },
  {
    id: "q12",
    topic: "Body map",
    text: "Is your pain mainly in your lower back and buttocks, rather than spread all over your body?",
    why: "Why we ask: where the pain sits helps your clinician tell apart conditions that can feel similar.",
  },
];

const PREFILLED = { q1: "yes", q2: "yes", q3: "yes" };

const PATTERNS = [
  {
    text: "Morning stiffness lasting over 30 minutes that eases as you move",
    meta: "You told us · 14 Nov 2026",
  },
  {
    text: "Back pain that wakes you in the second half of the night",
    meta: "You told us · 14 Nov 2026",
  },
  {
    text: "A painful, red eye treated for inflammation",
    meta: "Record · Meadowbrook Eye Clinic · 09 Mar 2023",
  },
  {
    text: "Back pain that eased noticeably with ibuprofen",
    meta: "You told us · 14 Nov 2026",
  },
  {
    text: "Chiropractor visits you paid for yourself",
    meta: "You told us · not confirmed by any record or claim",
  },
];

const QUESTIONS_TO_ASK = [
  "Could my back pain and the red-eye episode in 2023 be connected?",
  "Is it worth tracking down my records from before my insurer changed in Feb 2024?",
  "Should the chiropractor visits I paid for myself be added to my history?",
];

const UPDATE_RESULTS = [
  { name: "HLA-B27", result: "Negative", date: "05 Nov 2026" },
  { name: "C-reactive protein (CRP)", result: "Normal", date: "05 Nov 2026" },
  { name: "Sacroiliac joint MRI", result: "No signs found", date: "10 Nov 2026" },
];

const SHARE_URL = "https://diagnostic-odyssey.app/shared/<share-token>";

function qrMatrix(seed, size) {
  let a = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    a ^= seed.charCodeAt(i);
    a = Math.imul(a, 16777619) >>> 0;
  }
  const rand = () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const m = [];
  for (let r = 0; r < size; r++) {
    const row = [];
    for (let c = 0; c < size; c++) row.push(rand() > 0.52);
    m.push(row);
  }
  const finder = (or, oc) => {
    for (let r = -1; r <= 7; r++) {
      for (let c = -1; c <= 7; c++) {
        const rr = or + r;
        const cc = oc + c;
        if (rr < 0 || cc < 0 || rr >= size || cc >= size) continue;
        const inBox = r >= 0 && r <= 6 && c >= 0 && c <= 6;
        const edge =
          inBox && (r === 0 || r === 6 || c === 0 || c === 6);
        const core = r >= 2 && r <= 4 && c >= 2 && c <= 4;
        m[rr][cc] = inBox ? edge || core : false;
      }
    }
  };
  finder(0, 0);
  finder(0, size - 7);
  finder(size - 7, 0);
  return m;
}

export default function Screen() {
  const navigate = useNavigate();
  const [active, setActive] = React.useState("symptom");
  const [idx, setIdx] = React.useState(3);
  const [answers, setAnswers] = React.useState(PREFILLED);
  const [completed, setCompleted] = React.useState(false);
  const [showError, setShowError] = React.useState(false);
  const [share, setShare] = React.useState("idle");
  const [pdf, setPdf] = React.useState("idle");

  const q = QUESTIONS[idx];
  const answeredCount = QUESTIONS.filter((x) => answers[x.id]).length;
  const progress = completed
    ? 100
    : Math.round(((idx + 1) / QUESTIONS.length) * 100);

  const choose = (val) => {
    setAnswers((prev) => ({ ...prev, [q.id]: val }));
    setShowError(false);
  };

  const next = () => {
    if (!answers[q.id]) {
      setShowError(true);
      return;
    }
    if (idx >= QUESTIONS.length - 1) {
      setCompleted(true);
      return;
    }
    setIdx((i) => i + 1);
    setShowError(false);
  };

  const qr = React.useMemo(() => qrMatrix("odyssey-visitprep-share", 25), []);
  const qrSize = 25;

  const sq = { borderRadius: RADIUS };
  const labelCls =
    "text-[11px] font-bold uppercase tracking-[0.14em]";

  const primaryBtn =
    "inline-flex items-center justify-center gap-2 h-11 px-5 text-sm font-bold border-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2";
  const ghostBtn =
    "inline-flex items-center justify-center gap-2 h-11 px-5 text-sm font-bold border-2 bg-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2";

  return (
    <div
      className="min-h-full w-full bg-white"
      style={{ color: PRIMARY, fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif' }}
    >
      <style>{`
        @keyframes wfIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
        .wf-in { animation: wfIn .22s ease-out both; }
        @media (prefers-reduced-motion: reduce) { .wf-in { animation: none; } }
      `}</style>

      <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
        {/* Row 1 — page title */}
        <h1
          data-wf="b-0-0"
          className="text-3xl font-bold tracking-[-0.02em] sm:text-4xl"
        >
          My health
        </h1>

        {/* Row 2 — synthetic data notice */}
        <div
          data-wf="b-1-0"
          className="mt-4 flex items-start gap-2 border-l-2 border-2 px-3 py-2"
          style={{ borderColor: ACCENT, color: ACCENT, ...sq }}
          role="note"
        >
          <AlertCircle className="mt-[1px] h-4 w-4 shrink-0" aria-hidden="true" />
          <p className="text-xs font-semibold tracking-tight">
            100% synthetic data — not for clinical use.
          </p>
        </div>

        {/* Row 3 — section tabs */}
        <div
          data-wf="b-2-0"
          role="tablist"
          aria-label="Section"
          className="mt-6 flex border-b-2"
          style={{ borderColor: PRIMARY }}
        >
          {SECTIONS.map((s) => {
            const on = active === s.key;
            return (
              <button
                key={s.key}
                data-wf={s.wf}
                role="tab"
                id={`tab-${s.key}`}
                aria-selected={on}
                aria-controls={`panel-${s.key}`}
                tabIndex={on ? 0 : -1}
                onClick={() => setActive(s.key)}
                className={`-mb-[2px] border-b-2 px-4 py-2.5 text-sm font-bold tracking-tight transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2`}
                style={{
                  borderColor: on ? PRIMARY : "transparent",
                  color: on ? PRIMARY : "#6b6b6b",
                }}
              >
                {s.label}
              </button>
            );
          })}
        </div>

        {/* ===== SYMPTOM CHECK ===== */}
        {active === "symptom" && (
          <section
            id="panel-symptom"
            role="tabpanel"
            aria-labelledby="tab-symptom"
            className="mt-6"
          >
            {!completed ? (
              <>
                {/* Row 4 — progress card */}
                <div
                  data-wf="b-3-0"
                  className="border-2 p-4"
                  style={{ borderColor: PRIMARY, ...sq }}
                >
                  <div className="flex items-baseline justify-between">
                    <p className={labelCls} style={{ color: PRIMARY }}>
                      Question{" "}
                      <span style={{ fontVariantNumeric: "tabular-nums" }}>
                        {idx + 1}
                      </span>{" "}
                      of{" "}
                      <span style={{ fontVariantNumeric: "tabular-nums" }}>
                        {QUESTIONS.length}
                      </span>
                    </p>
                    <p
                      className="text-[11px] font-semibold"
                      style={{ color: "#6b6b6b", fontVariantNumeric: "tabular-nums" }}
                    >
                      {answeredCount} answered
                    </p>
                  </div>
                  <div
                    className="mt-3 h-[6px] w-full"
                    style={{ backgroundColor: "#ececec" }}
                    role="progressbar"
                    aria-valuenow={progress}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label="Intake progress"
                  >
                    <div
                      className="h-full transition-all duration-300"
                      style={{ width: `${progress}%`, backgroundColor: PRIMARY }}
                    />
                  </div>
                </div>

                {/* Row 5 — question form */}
                <form
                  data-wf="b-4-0"
                  key={q.id}
                  className="wf-in mt-4 border-2 p-4 sm:p-5"
                  style={{ borderColor: PRIMARY, ...sq }}
                  onSubmit={(e) => {
                    e.preventDefault();
                    next();
                  }}
                >
                  <fieldset>
                    <legend className="block">
                      <span className={labelCls} style={{ color: ACCENT }}>
                        {q.topic}
                      </span>
                      <span className="mt-2 block text-lg font-bold leading-snug tracking-tight sm:text-xl">
                        {q.text}
                      </span>
                    </legend>

                    <div className="mt-4 grid gap-2">
                      {OPTIONS.map((opt) => {
                        const on = answers[q.id] === opt.value;
                        return (
                          <label
                            key={opt.value}
                            className="flex min-h-[48px] cursor-pointer items-center gap-3 border-2 px-4 py-2 text-sm font-semibold transition-colors"
                            style={{
                              borderColor: PRIMARY,
                              backgroundColor: on ? PRIMARY : "#ffffff",
                              color: on ? "#ffffff" : PRIMARY,
                              ...sq,
                            }}
                          >
                            <input
                              data-wf={opt.wf}
                              type="radio"
                              name={q.id}
                              value={opt.value}
                              checked={on}
                              onChange={() => choose(opt.value)}
                              className="h-4 w-4 accent-black focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
                              style={{ accentColor: on ? "#ffffff" : PRIMARY }}
                            />
                            <span>{opt.label}</span>
                            {on && (
                              <Check className="ml-auto h-4 w-4" aria-hidden="true" />
                            )}
                          </label>
                        );
                      })}
                    </div>

                    {showError && (
                      <p
                        className="mt-3 flex items-center gap-1.5 text-xs font-semibold"
                        style={{ color: ACCENT }}
                        role="alert"
                      >
                        <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
                        Please choose an answer to continue — your other answers are
                        kept.
                      </p>
                    )}
                  </fieldset>
                </form>

                {/* Row 6 — why we ask + Next */}
                <div className="mt-4 grid grid-cols-12 gap-3">
                  <p
                    data-wf="b-5-0"
                    className="col-span-12 self-center text-sm leading-relaxed sm:col-span-8"
                    style={{ color: "#444444" }}
                  >
                    {q.why}
                  </p>
                  <div className="col-span-12 sm:col-span-4">
                    <button
                      data-wf="b-5-1"
                      type="button"
                      onClick={next}
                      className={primaryBtn + " w-full"}
                      style={{
                        backgroundColor: PRIMARY,
                        borderColor: PRIMARY,
                        color: "#ffffff",
                        ...sq,
                      }}
                    >
                      {idx >= QUESTIONS.length - 1 ? "Finish" : "Next"}
                      <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                {/* completed state keeps the same blocks */}
                <div
                  data-wf="b-3-0"
                  className="border-2 p-4"
                  style={{ borderColor: PRIMARY, ...sq }}
                >
                  <p className={labelCls} style={{ color: ACCENT }}>
                    Symptom check complete
                  </p>
                  <div
                    className="mt-3 h-[6px] w-full"
                    style={{ backgroundColor: ACCENT }}
                    role="progressbar"
                    aria-valuenow={100}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label="Intake progress"
                  />
                </div>

                <div
                  data-wf="b-4-0"
                  className="wf-in mt-4 flex items-start gap-3 border-2 p-5"
                  style={{ borderColor: PRIMARY, ...sq }}
                >
                  <CheckCircle
                    className="mt-0.5 h-6 w-6 shrink-0"
                    style={{ color: ACCENT }}
                    aria-hidden="true"
                  />
                  <div>
                    <h2 className="text-lg font-bold tracking-tight">
                      All 12 questions answered
                    </h2>
                    <p className="mt-1 text-sm leading-relaxed" style={{ color: "#444444" }}>
                      Your answers are saved and added to your health story, tagged
                      “You told us”. You can head to visit prep to see your history
                      laid out in plain language.
                    </p>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-12 gap-3">
                  <p
                    data-wf="b-5-0"
                    className="col-span-12 self-center text-sm leading-relaxed sm:col-span-8"
                    style={{ color: "#444444" }}
                  >
                    Why we ask: every answer fills a gap your records may have missed,
                    so your clinician starts from the full picture.
                  </p>
                  <div className="col-span-12 sm:col-span-4">
                    <button
                      data-wf="b-5-1"
                      type="button"
                      onClick={() => setActive("prep")}
                      className={primaryBtn + " w-full"}
                      style={{
                        backgroundColor: PRIMARY,
                        borderColor: PRIMARY,
                        color: "#ffffff",
                        ...sq,
                      }}
                    >
                      Go to visit prep
                      <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </>
            )}
          </section>
        )}

        {/* ===== VISIT PREP ===== */}
        {active === "prep" && (
          <section
            id="panel-prep"
            role="tabpanel"
            aria-labelledby="tab-prep"
            className="mt-6"
          >
            {/* Row 7 — visit prep card */}
            <div
              data-wf="b-6-0"
              className="wf-in border-2 p-5"
              style={{ borderColor: PRIMARY, ...sq }}
            >
              <span className={labelCls} style={{ color: ACCENT }}>
                Visit prep
              </span>
              <h2 className="mt-2 text-xl font-bold tracking-tight">
                Your history in plain language
              </h2>
              <p className="mt-1 text-xs" style={{ color: "#6b6b6b" }}>
                Patterns worth raising, with dates and sources — and questions to ask.
                No diagnosis, no score.
              </p>

              <p className="mt-4 text-sm leading-relaxed" style={{ color: "#333333" }}>
                You've had lower-back and buttock pain on and off since early 2023.
                Your records show four primary-care visits and two courses of
                physiotherapy, plus a chiropractor you paid for yourself in 2024 that
                never made it into your records.
              </p>

              <div className="my-5 h-0 border-t-2" style={{ borderColor: "#e4e4e4" }} />

              <h3 className={labelCls} style={{ color: PRIMARY }}>
                Patterns worth raising
              </h3>
              <ul className="mt-3 space-y-0">
                {PATTERNS.map((p, i) => (
                  <li
                    key={i}
                    className="flex gap-3 border-b py-3 last:border-b-0"
                    style={{ borderColor: "#e4e4e4" }}
                  >
                    <span
                      className="mt-1 h-2 w-2 shrink-0"
                      style={{ backgroundColor: PRIMARY }}
                      aria-hidden="true"
                    />
                    <div>
                      <p className="text-sm font-semibold leading-snug">{p.text}</p>
                      <p
                        className="mt-0.5 text-xs"
                        style={{ color: "#6b6b6b", fontVariantNumeric: "tabular-nums" }}
                      >
                        {p.meta}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>

              <div className="my-5 h-0 border-t-2" style={{ borderColor: "#e4e4e4" }} />

              <h3 className={labelCls} style={{ color: PRIMARY }}>
                Questions to ask your clinician
              </h3>
              <ol className="mt-3 space-y-2">
                {QUESTIONS_TO_ASK.map((qa, i) => (
                  <li key={i} className="flex gap-3 text-sm leading-snug">
                    <span
                      className="font-bold"
                      style={{ color: ACCENT, fontVariantNumeric: "tabular-nums" }}
                    >
                      {i + 1}.
                    </span>
                    <span style={{ color: "#333333" }}>{qa}</span>
                  </li>
                ))}
              </ol>
            </div>

            {/* Row 8 — QR, share link, save PDF */}
            <div className="mt-4 grid grid-cols-12 gap-3">
              {/* QR */}
              <div
                data-wf="b-7-0"
                className="col-span-12 flex flex-col items-center justify-center border-2 p-4 sm:col-span-4"
                style={{ borderColor: PRIMARY, ...sq }}
              >
                <svg
                  role="img"
                  aria-label="QR code that opens your visit-prep sheet"
                  viewBox={`0 0 ${qrSize} ${qrSize}`}
                  className="h-28 w-28"
                >
                  <rect width={qrSize} height={qrSize} fill="#ffffff" />
                  {qr.map((row, r) =>
                    row.map((on, c) =>
                      on ? (
                        <rect
                          key={`${r}-${c}`}
                          x={c}
                          y={r}
                          width={1}
                          height={1}
                          fill={PRIMARY}
                        />
                      ) : null
                    )
                  )}
                </svg>
                <p className={labelCls + " mt-2"} style={{ color: "#6b6b6b" }}>
                  Scan to share
                </p>
              </div>

              {/* Share link */}
              <div className="col-span-12 sm:col-span-4">
                <button
                  data-wf="b-7-1"
                  type="button"
                  onClick={() => setShare(share === "active" ? "idle" : "active")}
                  aria-expanded={share === "active"}
                  className={primaryBtn + " h-full w-full min-h-[48px]"}
                  style={{
                    backgroundColor: PRIMARY,
                    borderColor: PRIMARY,
                    color: "#ffffff",
                    ...sq,
                  }}
                >
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                  Share link
                </button>
              </div>

              {/* Save PDF */}
              <div className="col-span-12 sm:col-span-4">
                <button
                  data-wf="b-7-2"
                  type="button"
                  onClick={() => setPdf("done")}
                  className={ghostBtn + " h-full w-full min-h-[48px]"}
                  style={{ borderColor: PRIMARY, color: PRIMARY, ...sq }}
                >
                  <Download className="h-4 w-4" aria-hidden="true" />
                  Save as PDF
                </button>
              </div>
            </div>

            {/* Share reveal (completes the share interaction) */}
            {share === "active" && (
              <div
                className="wf-in mt-3 border-2 p-4"
                style={{ borderColor: ACCENT, ...sq }}
                role="status"
              >
                <p className={labelCls} style={{ color: ACCENT }}>
                  Share link active
                </p>
                <p
                  className="mt-2 break-all border-2 px-3 py-2 text-sm"
                  style={{ borderColor: "#e4e4e4", fontVariantNumeric: "tabular-nums", color: "#333333", ...sq }}
                >
                  {SHARE_URL}
                </p>
                <p className="mt-2 text-xs" style={{ color: "#6b6b6b" }}>
                  Only a clinician who signs in can open it. You can revoke it at any
                  time and the link stops working.
                </p>
              </div>
            )}

            {pdf === "done" && (
              <p
                className="wf-in mt-3 flex items-center gap-1.5 text-xs font-semibold"
                style={{ color: ACCENT }}
                role="status"
              >
                <CheckCircle className="h-3.5 w-3.5" aria-hidden="true" />
                Saved. The PDF carries the synthetic-data notice on every page.
              </p>
            )}
          </section>
        )}

        {/* ===== UPDATES ===== */}
        {active === "updates" && (
          <section
            id="panel-updates"
            role="tabpanel"
            aria-labelledby="tab-updates"
            className="mt-6"
          >
            <div className="grid grid-cols-12 gap-3">
              {/* Row 9 — update card */}
              <div
                data-wf="b-8-0"
                className="wf-in col-span-12 border-2 p-5 sm:col-span-8"
                style={{ borderColor: PRIMARY, ...sq }}
              >
                <span className={labelCls} style={{ color: ACCENT }}>
                  Update · 12 Nov 2026
                </span>
                <h2 className="mt-2 text-xl font-bold tracking-tight">
                  Your recent tests came back
                </h2>
                <p className="mt-2 text-sm leading-relaxed" style={{ color: "#333333" }}>
                  Your clinician checked three things — your HLA-B27, your CRP and an
                  MRI of your sacroiliac joints. All three were done and came back
                  negative. Your clinician has suggested next steps below. These
                  results are now on your timeline, tagged “Record”.
                </p>

                <ul className="mt-4">
                  {UPDATE_RESULTS.map((r, i) => (
                    <li
                      key={i}
                      className="flex items-center justify-between border-b py-2.5 last:border-b-0"
                      style={{ borderColor: "#e4e4e4" }}
                    >
                      <span className="text-sm font-semibold">{r.name}</span>
                      <span className="flex items-center gap-3">
                        <span className="text-sm" style={{ color: ACCENT }}>
                          {r.result}
                        </span>
                        <span
                          className="text-xs"
                          style={{ color: "#6b6b6b", fontVariantNumeric: "tabular-nums" }}
                        >
                          {r.date}
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>

                <div className="my-4 h-0 border-t-2" style={{ borderColor: "#e4e4e4" }} />

                <h3 className={labelCls} style={{ color: PRIMARY }}>
                  What your clinician suggested next
                </h3>
                <p className="mt-2 text-sm leading-relaxed" style={{ color: "#333333" }}>
                  Keep noting your morning stiffness and night pain, and book a
                  follow-up if the stiffness continues for another few weeks. Nothing
                  here needs action today.
                </p>
              </div>

              {/* Row 9 — view full timeline */}
              <div className="col-span-12 sm:col-span-4">
                <button
                  data-wf="b-8-1"
                  type="button"
                  onClick={() => navigate("timeline")}
                  className="flex h-full w-full flex-col justify-between border-2 p-4 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
                  style={{ borderColor: PRIMARY, ...sq }}
                >
                  <Calendar className="h-5 w-5" aria-hidden="true" />
                  <span className="mt-6 flex items-center justify-between text-sm font-bold">
                    View full timeline
                    <ChevronRight className="h-4 w-4" aria-hidden="true" />
                  </span>
                </button>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
