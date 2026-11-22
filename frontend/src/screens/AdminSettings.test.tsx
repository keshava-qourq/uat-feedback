import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Admin from "./Admin";

const CONNECTED = {
  database: { status: "connected" },
  llm: { status: "connected" },
  dataset_version: "v0.1",
  credentials: [
    { name: "database", status: "connected", value: "not-shown" },
    { name: "llm", status: "connected", value: "not-shown" },
  ],
};

const UNCONFIGURED = {
  database: { status: "not-configured" },
  llm: { status: "not-configured" },
  dataset_version: null,
  credentials: [
    { name: "database", status: "not-configured", value: "not-shown" },
    { name: "llm", status: "not-configured", value: "not-shown" },
  ],
};

const settingsApi = (body: unknown) =>
  vi.fn(async (url: RequestInfo | URL) => {
    if (String(url).endsWith("/api/admin/settings")) {
      return { ok: true, status: 200, json: async () => body } as Response;
    }
    throw new Error("unexpected call " + String(url));
  });

const failingApi = (status: number, detail: string) =>
  vi.fn(async (url: RequestInfo | URL) => {
    if (String(url).endsWith("/api/admin/settings")) {
      return { ok: false, status, json: async () => ({ detail }) } as Response;
    }
    throw new Error("unexpected call " + String(url));
  });

afterEach(() => {
  vi.unstubAllGlobals();
});

const CREDENTIAL_SHAPED =
  /postgres(ql)?:\/\/|sk-[A-Za-z0-9]|api[_-]?key\s*[:=]|Bearer\s+\S|password/i;

describe("Admin settings credential panel", () => {
  it("[AC-057] the LLM credential is a masked placeholder labelled as deployment configuration", async () => {
    vi.stubGlobal("fetch", settingsApi(CONNECTED));
    const { container } = render(<Admin />);

    await waitFor(() => expect(screen.getByText("LLM credential")).toBeInTheDocument());
    expect(screen.getAllByText("••••••••").length).toBeGreaterThanOrEqual(2);
    expect(
      screen.getByText(/Credentials are supplied as deployment configuration/i),
    ).toBeInTheDocument();
    // Never an input holding a value.
    container.querySelectorAll("input, textarea").forEach((el) => {
      expect((el as HTMLInputElement).value ?? "").not.toMatch(/•|sk-|postgres/i);
    });
  });

  it("[AC-057] a configured deployment reads Connected for both the LLM and the database", async () => {
    vi.stubGlobal("fetch", settingsApi(CONNECTED));
    const { container } = render(<Admin />);

    await waitFor(() => expect(screen.getAllByText("Connected")).toHaveLength(2));
    expect(screen.getByText("v0.1")).toBeInTheDocument();
    expect(container.textContent ?? "").not.toMatch(CREDENTIAL_SHAPED);
  });

  it("[AC-057] an unconfigured deployment reads Not configured for both and shows no value", async () => {
    vi.stubGlobal("fetch", settingsApi(UNCONFIGURED));
    const { container } = render(<Admin />);

    await waitFor(() => expect(screen.getAllByText("Not configured")).toHaveLength(2));
    expect(screen.getAllByText("••••••••").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("None loaded")).toBeInTheDocument();
    expect(container.textContent ?? "").not.toMatch(CREDENTIAL_SHAPED);
  });

  it("[AC-057] a 403 on the settings call renders a readable message, not a blank panel", async () => {
    vi.stubGlobal("fetch", failingApi(403, "Admin access required"));
    const { container } = render(<Admin />);

    await waitFor(() =>
      expect(screen.getByText(/Could not read the connection settings/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/Admin access required/)).toBeInTheDocument();
    expect(screen.getByText("Connections and settings")).toBeInTheDocument();
    expect(container.textContent ?? "").not.toMatch(CREDENTIAL_SHAPED);
  });
});
