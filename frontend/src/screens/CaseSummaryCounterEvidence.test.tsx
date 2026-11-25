import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import CaseSummary from "./CaseSummary";

const PATIENT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";

const CRITERIA = {
  asas_referral: [],
  spartan: { items: [], total: 0, threshold: 6 },
};

const COUNTER_EVIDENCE = [
  {
    key: "widespread_pain",
    label: "Widespread pain with normal inflammatory markers",
    plain_language: "Pain reported all over the body with normal CRP caps the status at Moderate.",
    effect: "cap",
    capped_to: "Moderate",
    awaiting_sign_off: true,
    evidence: [
      {
        display: "Normal CRP",
        date: "2023-11-02",
        source_tag: "Record",
        source_ref: "note-crp-1",
      },
    ],
  },
  {
    key: "load_related",
    label: "Load-related pattern",
    plain_language: "Pain that worsens with activity caps the status at Low.",
    effect: "cap",
    capped_to: "Low",
    awaiting_sign_off: false,
    evidence: [
      {
        display: "Rowing injury visit",
        date: null,
        source_tag: "Insurance claim",
        source_ref: null,
      },
    ],
  },
];

const body = (extra: Record<string, unknown> = {}) => ({
  patient_id: PATIENT_ID,
  cutoff_date: "2024-03-01",
  criteria: CRITERIA,
  extracted_evidence: [],
  tier: "Moderate",
  tier_reason: "Capped below High by counter-evidence.",
  reachable_history: { months: 48, threshold_months: 12, below_threshold: false },
  counter_evidence: COUNTER_EVIDENCE,
  alternative_explanation: { label: "Pattern consistent with fibromyalgia" },
  notice: "100% synthetic data — not for clinical use.",
  ...extra,
});

const ok = (b: unknown) => ({ ok: true, status: 200, json: async () => b }) as unknown as Response;

function renderScreen() {
  render(
    <MemoryRouter initialEntries={[`/case-summary?patient_id=${PATIENT_ID}`]}>
      <CaseSummary />
    </MemoryRouter>,
  );
}

function stub(b: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ok(b)),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CaseSummary headline status", () => {
  it("[AC-037] the headline reads the API tier and its reason, with no probability or score", async () => {
    stub(body());
    renderScreen();

    await waitFor(() => expect(screen.getByTestId("case-tier")).toHaveTextContent("Moderate"));
    expect(screen.getByTestId("case-tier-reason")).toHaveTextContent(
      "Capped below High by counter-evidence.",
    );
    const headline =
      (screen.getByTestId("case-tier").textContent ?? "") +
      (screen.getByTestId("case-tier-reason").textContent ?? "");
    expect(headline).not.toMatch(/\d/);
    expect(headline).not.toMatch(/probability|risk score|raw score|%/i);
  });

  it("[AC-038][AC-039] an Insufficient history case states that wording and never Low", async () => {
    stub(
      body({
        tier: "Insufficient history",
        tier_reason: "Only 9 months of records are reachable.",
        reachable_history: { months: 9, threshold_months: 12, below_threshold: true },
        counter_evidence: [],
        alternative_explanation: null,
      }),
    );
    renderScreen();

    await waitFor(() =>
      expect(screen.getByTestId("case-tier")).toHaveTextContent("Insufficient history"),
    );
    expect(screen.getByTestId("case-tier")).not.toHaveTextContent(/\bLow\b/);
    expect(screen.getByTestId("case-tier-reason")).toHaveTextContent(
      "Only 9 months of records are reachable.",
    );
  });

  it("[AC-037] a failed read leaves the screen standing with the API detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 404,
        json: async () => ({ detail: "Unknown patient" }),
      })),
    );
    renderScreen();

    expect(await screen.findByRole("alert")).toHaveTextContent("Unknown patient");
    expect(screen.getByTestId("case-tier")).toHaveTextContent("No status from the API");
  });
});

describe("CaseSummary counter-evidence panel", () => {
  it("[AC-036] every item is listed with its sentence, cap and triggering evidence with a source link", async () => {
    stub(body());
    renderScreen();

    await waitFor(() =>
      expect(screen.getByTestId("counter-evidence-widespread_pain")).toBeInTheDocument(),
    );

    const first = screen.getByTestId("counter-evidence-widespread_pain");
    expect(within(first).getByText(COUNTER_EVIDENCE[0].plain_language)).toBeInTheDocument();
    expect(within(first).getByText(/Caps the status at Moderate/)).toBeInTheDocument();
    const link = within(first).getByRole("link", { name: "Normal CRP" });
    expect(link).toHaveAttribute("href", expect.stringContaining("note-crp-1"));
    expect(within(first).getByText("2023-11-02")).toBeInTheDocument();
    expect(within(first).getByText("Record")).toBeInTheDocument();

    const second = screen.getByTestId("counter-evidence-load_related");
    expect(within(second).getByText(/Caps the status at Low/)).toBeInTheDocument();
    expect(within(second).getByText("Rowing injury visit")).toBeInTheDocument();
    expect(within(second).getByText("Insurance claim")).toBeInTheDocument();

    expect(screen.getByTestId("alternative-explanation")).toHaveTextContent(
      "Pattern consistent with fibromyalgia",
    );
  });

  it("[AC-036] awaiting_sign_off true shows the marker and false does not", async () => {
    stub(body());
    renderScreen();

    await waitFor(() =>
      expect(screen.getByTestId("awaiting-sign-off-widespread_pain")).toHaveTextContent(
        /awaiting clinical review/i,
      ),
    );
    expect(screen.queryByTestId("awaiting-sign-off-load_related")).not.toBeInTheDocument();
  });

  it("[AC-036] the panel is omitted when the counter-evidence list is empty", async () => {
    stub(body({ counter_evidence: [], alternative_explanation: null }));
    renderScreen();

    await waitFor(() => expect(screen.getByTestId("case-tier")).toHaveTextContent("Moderate"));
    expect(screen.queryByTestId("counter-evidence-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("alternative-explanation")).not.toBeInTheDocument();
  });
});
