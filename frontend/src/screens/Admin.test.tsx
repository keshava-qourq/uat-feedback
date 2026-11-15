import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Admin from "./Admin";

const RUN_ID = "11111111-2222-3333-4444-555555555555";

const started = {
  run_id: RUN_ID,
  status: "queued",
  dataset_version: "v0.1",
  seed: 42,
  started_at: "2026-11-15T09:12:00+00:00",
};

const report = (status: string, files: unknown[]) => ({
  run_id: RUN_ID,
  status,
  dataset_version: "v0.1",
  seed: 42,
  patient_count: 5006,
  started_at: "2026-11-15T09:12:00+00:00",
  finished_at: "2026-11-15T09:14:00+00:00",
  files,
});

const PASSED_FILES = [
  { file: "patients.csv", status: "passed", rows_loaded: 5006, rows_rejected: 0, error: null },
  { file: "events.csv", status: "passed", rows_loaded: 572418, rows_rejected: 37, error: null },
];

const FAILED_FILES = [
  { file: "patients.csv", status: "passed", rows_loaded: 5006, rows_rejected: 0, error: null },
  {
    file: "events.csv",
    status: "failed",
    rows_loaded: 0,
    rows_rejected: 0,
    error: "events.csv is missing the required column source_ref",
  },
];

const CONNECTED_SETTINGS = {
  database: { status: "connected" },
  llm: { status: "connected" },
  dataset_version: "v0.1",
};

const UNCONFIGURED_SETTINGS = {
  database: { status: "not-configured" },
  llm: { status: "not-configured" },
  dataset_version: null,
};

function mockApi(
  final: ReturnType<typeof report>,
  settings: Record<string, unknown> = CONNECTED_SETTINGS,
) {
  return vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const u = String(url);
    const body =
      init?.method === "POST"
        ? started
        : u.endsWith("/api/admin/settings")
          ? settings
          : u.endsWith(`/api/admin/ingest-runs/${RUN_ID}`)
            ? final
            : null;
    if (!body) throw new Error("unexpected call " + u);
    return { ok: true, status: 200, json: async () => body } as Response;
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", mockApi(report("passed", PASSED_FILES)));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Admin ingest report", () => {
  it("[AC-001/AC-002/AC-003] a successful run renders passed files with their counts", async () => {
    render(<Admin />);
    await userEvent.click(screen.getByRole("button", { name: /run ingest/i }));

    await waitFor(() => expect(screen.getByText("572,418")).toBeInTheDocument());
    expect(screen.getByText(/Dataset v0\.1/)).toBeInTheDocument();
    expect(screen.getByText(/Seed 42/)).toBeInTheDocument();
    expect(screen.getByText(/5,006 patients/)).toBeInTheDocument();
    expect(screen.getByText("passed")).toBeInTheDocument();
    expect(screen.getByText("patients.csv")).toBeInTheDocument();
    expect(screen.getByText("events.csv")).toBeInTheDocument();
    expect(screen.getByText("2 of 2")).toBeInTheDocument();

    const post = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === "POST",
    )!;
    expect(String(post[0])).toMatch(/\/api\/admin\/ingest-runs$/);
  });

  it("[AC-003] a failed file's row shows its named reason", async () => {
    vi.stubGlobal("fetch", mockApi(report("failed", FAILED_FILES)));
    render(<Admin />);
    await userEvent.click(screen.getByRole("button", { name: /run ingest/i }));

    await waitFor(() =>
      expect(
        screen.getByText("events.csv is missing the required column source_ref"),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("failed")).toBeInTheDocument();
    expect(screen.getAllByText(/Failed/).length).toBeGreaterThan(0);
  });
});

describe("Admin connections and settings", () => {
  it("[AC-144/AC-145] a configured deployment shows Connected for both and the dataset version", async () => {
    render(<Admin />);

    await waitFor(() => expect(screen.getAllByText("Connected")).toHaveLength(2));
    expect(screen.getByText("Active dataset version")).toBeInTheDocument();
    expect(screen.getByText("v0.1")).toBeInTheDocument();

    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls.find((c) =>
      String(c[0]).endsWith("/api/admin/settings"),
    );
    expect(call).toBeDefined();
  });

  it("[AC-145] an unconfigured deployment shows Not configured and never a credential value", async () => {
    vi.stubGlobal(
      "fetch",
      mockApi(report("passed", PASSED_FILES), {
        ...UNCONFIGURED_SETTINGS,
      }),
    );
    const { container } = render(<Admin />);

    await waitFor(() => expect(screen.getAllByText("Not configured")).toHaveLength(2));
    expect(screen.getByText("None loaded")).toBeInTheDocument();
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/postgres|sk-|password|api[_-]?key/i);
  });
});
