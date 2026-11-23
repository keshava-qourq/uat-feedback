import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import Admin from "./Admin";

const JOB_ID = "job-ext-1111-2222";

const CONNECTED_SETTINGS = {
  database: { status: "connected" },
  llm: { status: "connected" },
  dataset_version: "v0.1",
};

const REPORT = {
  dataset_version: "v0.1",
  notes_processed: 40000,
  findings_by_clue_type: [
    { clue_type: "night_pain", count: 1284 },
    { clue_type: "morning_stiffness", count: 931 },
  ],
  caveat:
    "Notes are templated text, so counts reflect the templates rather than free clinical prose.",
  notice: "100% synthetic data — not for clinical use.",
};

const job = (status: string, extra: Record<string, unknown> = {}) => ({
  job_id: JOB_ID,
  kind: "clue_extraction",
  status,
  progress: 0,
  result: null,
  ...extra,
});

function mockApi(options: {
  report?: unknown;
  reportError?: { status: number; detail: string };
  jobState?: Record<string, unknown>;
}) {
  return vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const u = String(url);
    if (u.endsWith("/api/admin/jobs") && init?.method === "POST") {
      return {
        ok: true,
        status: 202,
        json: async () => ({ job_id: JOB_ID, kind: "clue_extraction", status: "queued" }),
      } as Response;
    }
    if (u.endsWith(`/api/admin/jobs/${JOB_ID}`)) {
      return {
        ok: true,
        status: 200,
        json: async () => options.jobState ?? job("finished"),
      } as Response;
    }
    if (u.endsWith("/api/admin/extraction-report")) {
      if (options.reportError) {
        return {
          ok: false,
          status: options.reportError.status,
          json: async () => ({ detail: options.reportError!.detail }),
        } as Response;
      }
      return { ok: true, status: 200, json: async () => options.report ?? REPORT } as Response;
    }
    if (u.endsWith("/api/admin/settings")) {
      return { ok: true, status: 200, json: async () => CONNECTED_SETTINGS } as Response;
    }
    throw new Error("unexpected call " + u);
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Admin clue-extraction report", () => {
  it("[AC-052] shows notes processed, findings per clue type and the templated-text caveat", async () => {
    vi.stubGlobal("fetch", mockApi({}));
    render(<Admin />);

    await waitFor(() => expect(screen.getByText("40,000")).toBeInTheDocument());
    expect(screen.getByText("Notes processed")).toBeInTheDocument();
    expect(screen.getByText("night_pain")).toBeInTheDocument();
    expect(screen.getByText("1,284")).toBeInTheDocument();
    expect(screen.getByText("morning_stiffness")).toBeInTheDocument();
    expect(screen.getByText("931")).toBeInTheDocument();
    expect(screen.getByText(REPORT.caveat)).toBeInTheDocument();

    const calls = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls;
    expect(calls.some((c) => String(c[0]).endsWith("/api/admin/extraction-report"))).toBe(true);
  });

  it("[NFR-006] starting the job posts kind clue_extraction and shows polled progress", async () => {
    vi.stubGlobal("fetch", mockApi({ jobState: job("started", { progress: 0.4 }) }));
    render(<Admin />);

    await userEvent.click(screen.getByRole("button", { name: /run clue extraction/i }));

    await waitFor(() =>
      expect(screen.getByText(/Clue extraction running/)).toHaveTextContent("40%"),
    );
    // The rest of the screen keeps rendering while the job runs.
    expect(screen.getByText("Notes processed")).toBeInTheDocument();

    const calls = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls;
    const post = calls.find(
      (c) =>
        (c[1] as RequestInit | undefined)?.method === "POST" &&
        String(c[0]).endsWith("/api/admin/jobs"),
    )!;
    expect(JSON.parse(String((post[1] as RequestInit).body))).toEqual({ kind: "clue_extraction" });
    expect(calls.some((c) => String(c[0]).endsWith(`/api/admin/jobs/${JOB_ID}`))).toBe(true);
  });

  it("[NFR-006] a failed extraction job says so and offers the retry", async () => {
    vi.stubGlobal("fetch", mockApi({ jobState: job("failed") }));
    render(<Admin />);

    await userEvent.click(screen.getByRole("button", { name: /run clue extraction/i }));

    await waitFor(() =>
      expect(screen.getByText(/The clue extraction failed\. Start it again to retry\./)).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: /run clue extraction/i })).toBeEnabled();
  });

  it("[AC-052] a 403 on the report shows the API's detail, not a blank panel", async () => {
    vi.stubGlobal(
      "fetch",
      mockApi({ reportError: { status: 403, detail: "Admin access required" } }),
    );
    const { container } = render(<Admin />);

    await waitFor(() =>
      expect(screen.getByText(/Could not read the extraction report/)).toHaveTextContent(
        "Admin access required",
      ),
    );
    expect(screen.getByText("Clue extraction report")).toBeInTheDocument();
    expect(container.textContent ?? "").not.toMatch(/sk-|password|api[_-]?key|Bearer /i);
  });
});
