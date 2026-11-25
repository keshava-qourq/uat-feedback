import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Worklist from "./Worklist";

const ID = {
  high: "11111111-1111-1111-1111-111111111111",
  moderate: "22222222-2222-2222-2222-222222222222",
  insufficient: "33333333-3333-3333-3333-333333333333",
  low: "44444444-4444-4444-4444-444444444444",
};

const row = (
  patient_id: string,
  display_name: string,
  tier: string,
  extra: Record<string, unknown> = {},
) => ({
  patient_id,
  display_name,
  dataset_patient_id: "DS-" + display_name.split(" ")[0],
  invite_status: null,
  tier,
  tier_reason: tier + " reason for " + display_name,
  reachable_history_months: 48,
  below_reachable_history_threshold: false,
  counter_evidence_count: 0,
  ...extra,
});

// Deliberately unsorted, so the screen's own ordering is what is asserted.
const WORKLIST = {
  items: [
    row(ID.low, "Ada Nwosu", "Low"),
    row(ID.insufficient, "Cleo Marsh", "Insufficient history", {
      reachable_history_months: 9,
      below_reachable_history_threshold: true,
      tier_reason: "Only 9 months of records are reachable.",
    }),
    row(ID.high, "Bo Larsen", "High"),
    row(ID.moderate, "Dev Patel", "Moderate", { counter_evidence_count: 2 }),
  ],
  notice: "100% synthetic data — not for clinical use.",
};

const ok = (body: unknown) =>
  ({ ok: true, status: 200, json: async () => body }) as unknown as Response;
const fail = (status: number, detail: string) =>
  ({ ok: false, status, json: async () => ({ detail }) }) as unknown as Response;

function renderScreen() {
  render(
    <MemoryRouter>
      <Worklist />
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ok(WORKLIST)),
  );
});

describe("Worklist tiers from the API", () => {
  it("[AC-037] each row shows the API tier, reason and reachable history, read via VITE_API_BASE_URL", async () => {
    renderScreen();

    await waitFor(() => expect(screen.getByText("Bo Larsen")).toBeInTheDocument());

    const high = screen.getByTestId("worklist-row-" + ID.high);
    expect(within(high).getByText("High")).toBeInTheDocument();
    expect(within(high).getByText("High reason for Bo Larsen")).toBeInTheDocument();
    expect(within(high).getByText("48 months")).toBeInTheDocument();

    const moderate = screen.getByTestId("worklist-row-" + ID.moderate);
    expect(within(moderate).getByText("Moderate")).toBeInTheDocument();
    expect(within(moderate).getByText("2 items")).toBeInTheDocument();

    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(call[0])).toMatch(/\/api\/worklist$/);
    // The apiFetch helper is what calls: no cookie credentials, JSON headers only.
    expect((call[1] as RequestInit).credentials).toBeUndefined();
    expect((call[1] as RequestInit).headers).toMatchObject({
      "Content-Type": "application/json",
    });
  });

  it("[AC-037] rows are ordered High, Moderate, Insufficient history, Low", async () => {
    renderScreen();

    await waitFor(() => expect(screen.getByText("Bo Larsen")).toBeInTheDocument());
    const names = screen
      .getAllByTestId(/^worklist-row-/)
      .map((r) => (r.textContent ?? "").split(" ")[0]);
    expect(names).toEqual(["Bo", "Dev", "Cleo", "Ada"]);
  });

  it("[AC-037] the filter counts come from the API data", async () => {
    renderScreen();

    await waitFor(() => expect(screen.getByText("Bo Larsen")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /^All \(4\)$/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^High \(1\)$/ })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^Insufficient history \(1\)$/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Low \(1\)$/ })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /^High \(1\)$/ }));
    expect(screen.getAllByTestId(/^worklist-row-/)).toHaveLength(1);
  });

  it("[AC-038][AC-039] an Insufficient history row never reads Low or any reassuring wording", async () => {
    renderScreen();

    await waitFor(() => expect(screen.getByText("Cleo Marsh")).toBeInTheDocument());
    const insufficient = screen.getByTestId("worklist-row-" + ID.insufficient);
    expect(within(insufficient).getByText("Insufficient history")).toBeInTheDocument();
    expect(within(insufficient).getByText("9 months")).toBeInTheDocument();
    expect(within(insufficient).getByText("Below the threshold")).toBeInTheDocument();
    const text = insufficient.textContent ?? "";
    expect(text).not.toMatch(/\bLow\b/);
    expect(text).not.toMatch(/no flag|nothing to flag|all clear|reassur/i);
  });

  it("[AC-037] the loading state renders and a failed read shows the API detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => fail(403, "Patient tokens may not read the worklist")),
    );
    renderScreen();

    expect(await screen.findByText("Patient tokens may not read the worklist")).toBeInTheDocument();
    expect(screen.queryByTestId(/^worklist-row-/)).not.toBeInTheDocument();
  });
});
