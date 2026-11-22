import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import Admin from "./Admin";

const JOB_ID = "job-aaaa-bbbb-cccc";

const CONNECTED_SETTINGS = {
  database: { status: "connected" },
  llm: { status: "connected" },
  dataset_version: "v0.1",
};

const DEDUP_RESULT = {
  true_encounters: 14820,
  matched_to_one_entry: 9641,
  split_into_more_than_one: 437,
  merged_in_error: 96,
  invisible_care: 4742,
  dataset_version: "v0.1",
};

const job = (status: string, extra: Record<string, unknown> = {}) => ({
  job_id: JOB_ID,
  kind: "dedup_check",
  status,
  progress_pct: null,
  result: null,
  ...extra,
});

function mockApi(
  states: Array<Record<string, unknown>>,
  jobError?: { status: number; detail: string },
) {
  let i = 0;
  return vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const u = String(url);
    if (u.endsWith("/api/admin/jobs") && init?.method === "POST") {
      return {
        ok: true,
        status: 202,
        json: async () => ({ job_id: JOB_ID, kind: "dedup_check", status: "queued" }),
      } as Response;
    }
    if (u.endsWith(`/api/admin/jobs/${JOB_ID}`)) {
      if (jobError) {
        return {
          ok: false,
          status: jobError.status,
          json: async () => ({ detail: jobError.detail }),
        } as Response;
      }
      const body = states[Math.min(i++, states.length - 1)];
      return { ok: true, status: 200, json: async () => body } as Response;
    }
    if (u.endsWith("/api/admin/settings")) {
      return { ok: true, status: 200, json: async () => CONNECTED_SETTINGS } as Response;
    }
    throw new Error("unexpected call " + u);
  });
}

const RUN_ID = "run-1111-2222-3333";

const INGEST_REPORT = {
  run_id: RUN_ID,
  status: "passed",
  dataset_version: "v0.1",
  seed: 42,
  patient_count: 5006,
  started_at: "2026-11-20T10:00:00+00:00",
  finished_at: "2026-11-20T10:04:00+00:00",
  files: [
    { file: "patients.csv", status: "passed", rows_loaded: 5006, rows_rejected: 0, error: null },
    { file: "events.csv", status: "failed", rows_loaded: 0, rows_rejected: 120, error: "bad rows" },
  ],
};

const ingestApi = () =>
  vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const u = String(url);
    if (u.endsWith("/api/admin/ingest-runs") && init?.method === "POST") {
      return { ok: true, status: 202, json: async () => ({ run_id: RUN_ID }) } as Response;
    }
    if (u.endsWith(`/api/admin/ingest-runs/${RUN_ID}`)) {
      return { ok: true, status: 200, json: async () => INGEST_REPORT } as Response;
    }
    if (u.endsWith("/api/admin/settings")) {
      return { ok: true, status: 200, json: async () => CONNECTED_SETTINGS } as Response;
    }
    throw new Error("unexpected call " + u);
  });

const startCheck = () =>
  userEvent.click(screen.getByRole("button", { name: /run de-duplication check/i }));

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Admin de-duplication panel", () => {
  it("[AC-004-3] starts the job with kind dedup_check and shows progress while it runs", async () => {
    vi.stubGlobal("fetch", mockApi([job("started", { progress_pct: 40 })]));
    render(<Admin />);
    await startCheck();

    await waitFor(() =>
      expect(screen.getByText(/De-duplication check running/)).toHaveTextContent("40%"),
    );
    expect(screen.queryByText("9,641")).not.toBeInTheDocument();

    const calls = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls;
    const post = calls.find(
      (c) =>
        (c[1] as RequestInit | undefined)?.method === "POST" &&
        String(c[0]).endsWith("/api/admin/jobs"),
    )!;
    expect(JSON.parse(String((post[1] as RequestInit).body))).toEqual({ kind: "dedup_check" });
    expect(calls.some((c) => String(c[0]).endsWith(`/api/admin/jobs/${JOB_ID}`))).toBe(true);
  });

  it("[AC-004-3][AC-013] a finished job renders the four counts with thousands separators", async () => {
    vi.stubGlobal("fetch", mockApi([job("finished", { result: DEDUP_RESULT })]));
    render(<Admin />);
    await startCheck();

    await waitFor(() => expect(screen.getByText("9,641")).toBeInTheDocument());
    expect(screen.getByText("437")).toBeInTheDocument();
    expect(screen.getByText("96")).toBeInTheDocument();
    expect(screen.getByText("4,742")).toBeInTheDocument();
    expect(screen.getByText(/14,820 true encounters checked/)).toBeInTheDocument();
    // AC-013: invisible care is counted but never drawn as a timeline entry.
    expect(screen.getByText(/Counted, but never drawn as a timeline entry/)).toBeInTheDocument();
  });

  it("[AC-004-3] a failed job shows a readable message, not a blank panel", async () => {
    vi.stubGlobal("fetch", mockApi([job("failed")]));
    render(<Admin />);
    await startCheck();

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/de-duplication check failed/i),
    );
    expect(screen.getByText("Matched to one entry")).toBeInTheDocument();
  });

  it("[AC-004-3] a 403 on the job read shows the API's detail and no credential value", async () => {
    vi.stubGlobal("fetch", mockApi([], { status: 403, detail: "Admin access required" }));
    const { container } = render(<Admin />);
    await startCheck();

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("Admin access required"),
    );
    expect(container.textContent ?? "").not.toMatch(/sk-|password|api[_-]?key|Bearer /i);
  });

  it("[AC-004-3] a 404 on the job read shows the API's detail", async () => {
    vi.stubGlobal("fetch", mockApi([], { status: 404, detail: "Unknown job" }));
    render(<Admin />);
    await startCheck();

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Unknown job"));
  });
});

describe("Admin ingest summary totals", () => {
  it("[AC-002] a finished run reports loaded, rejected and passed totals once, consistently", async () => {
    vi.stubGlobal("fetch", ingestApi());
    render(<Admin />);
    await userEvent.click(screen.getByRole("button", { name: /run ingest/i }));

    await waitFor(() => expect(screen.getAllByText("5,006").length).toBeGreaterThan(0));
    expect(screen.getAllByText("120").length).toBeGreaterThan(0);
    expect(screen.getByText("1 of 2")).toBeInTheDocument();
    expect(
      screen.getByText(/Ingest passed\. 1 of 2 files passed, 120 rows rejected/),
    ).toBeInTheDocument();
  });
});
