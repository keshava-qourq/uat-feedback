import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import CaseSummary from "./CaseSummary";

const PATIENT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";

// Exactly the US-010 contract shape; the backend route is not live yet.
const CASE_BODY = {
  patient_id: PATIENT_ID,
  cutoff_date: "2024-03-01",
  criteria: {
    asas_referral: [
      {
        key: "inflammatory_back_pain",
        label: "Inflammatory back pain",
        status: "met",
        evidence: {
          event_id: "evt-1",
          display: "Night pain reported",
          date: "2024-02-10",
          source_tag: "You told us",
        },
        needed: null,
      },
      {
        key: "hla_b27",
        label: "Genetic marker result",
        status: "not_met",
        evidence: null,
        needed: null,
      },
      {
        key: "imaging",
        label: "Sacroiliac imaging",
        status: "unknown",
        evidence: null,
        needed: "Needs an MRI or X-ray of the sacroiliac joints",
      },
    ],
    spartan: {
      items: [
        {
          key: "uveitis",
          label: "Uveitis episode",
          status: "met",
          points: 3,
          evidence: {
            event_id: "evt-2",
            display: "Uveitis visit",
            date: "2022-05-12",
            source_tag: "Record",
          },
          needed: null,
        },
        {
          key: "family_history",
          label: "Family history",
          status: "unknown",
          points: 2,
          evidence: null,
          needed: "Ask the patient about a relative with a spine condition",
        },
      ],
      total: 3,
      threshold: 6,
    },
  },
  notice: "100% synthetic data — not for clinical use.",
};

const ok = (body: unknown) =>
  ({ ok: true, status: 200, json: async () => body }) as unknown as Response;

function renderScreen() {
  render(
    <MemoryRouter initialEntries={[`/case-summary?patient_id=${PATIENT_ID}`]}>
      <CaseSummary />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ok(CASE_BODY)),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CaseSummary criteria panel", () => {
  it("[AC-030] lists each criterion and point item with its met / not_met / unknown status", async () => {
    renderScreen();

    await waitFor(() => expect(screen.getByTestId("criterion-hla_b27")).toBeInTheDocument());
    expect(
      within(screen.getByTestId("criterion-inflammatory_back_pain")).getByText("Met"),
    ).toBeInTheDocument();
    expect(
      within(screen.getByTestId("criterion-hla_b27")).getByText("Not met"),
    ).toBeInTheDocument();
    expect(
      within(screen.getByTestId("criterion-imaging")).getByText("Unknown"),
    ).toBeInTheDocument();
    expect(within(screen.getByTestId("criterion-uveitis")).getByText("Met")).toBeInTheDocument();
    expect(
      within(screen.getByTestId("criterion-family_history")).getByText("Unknown"),
    ).toBeInTheDocument();

    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(call[0])).toMatch(new RegExp(`/api/cases/${PATIENT_ID}$`));
  });

  it("[AC-030] shows the SPARTAN total against the threshold", async () => {
    renderScreen();

    await waitFor(() =>
      expect(screen.getByTestId("spartan-total")).toHaveTextContent("Total 3 of threshold 6"),
    );
    expect(screen.getByTestId("spartan-total")).toHaveTextContent(/below threshold/i);
  });

  it("[AC-031] opening a met item reveals the named evidence with its date and source tag", async () => {
    renderScreen();

    await waitFor(() => expect(screen.getByTestId("criterion-uveitis")).toBeInTheDocument());
    const row = screen.getByTestId("criterion-uveitis");
    expect(within(row).queryByText("Uveitis visit")).not.toBeInTheDocument();

    await userEvent.click(within(row).getByRole("button"));

    expect(within(row).getByText("Uveitis visit")).toBeInTheDocument();
    expect(within(row).getByText("2022-05-12")).toBeInTheDocument();
    expect(within(row).getByText("Record")).toBeInTheDocument();
  });

  it("[AC-032] opening an unknown item reveals the 'needed' text", async () => {
    renderScreen();

    await waitFor(() => expect(screen.getByTestId("criterion-imaging")).toBeInTheDocument());
    const row = screen.getByTestId("criterion-imaging");

    await userEvent.click(within(row).getByRole("button"));

    expect(
      within(row).getByText("Needs an MRI or X-ray of the sacroiliac joints"),
    ).toBeInTheDocument();
  });

  it("[AC-030] a failed read shows the API's detail instead of an empty panel", async () => {
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
  });
});
