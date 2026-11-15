import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App, { ROUTES } from "@/App";
import SyntheticDataNotice, { SYNTHETIC_DATA_NOTICE } from "./SyntheticDataNotice";

beforeEach(() => {
  // No screen may reach the network while the guardrail walks every route.
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) }) as Response),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SyntheticDataNotice", () => {
  it("[AC-119] states the data is 100% synthetic and not for clinical use", () => {
    render(<SyntheticDataNotice />);
    expect(screen.getByTestId("synthetic-data-notice")).toHaveTextContent(/100% synthetic data/i);
    expect(screen.getByTestId("synthetic-data-notice")).toHaveTextContent(/not for clinical use/i);
    expect(SYNTHETIC_DATA_NOTICE).toMatch(/100% synthetic data/i);
  });

  it("[AC-121] the route table is not empty, so the guardrail below cannot pass vacuously", () => {
    expect(ROUTES.length).toBeGreaterThanOrEqual(7);
  });

  it.each(ROUTES.map((route) => route.path))(
    "[AC-119][AC-121] the notice renders on %s",
    (path) => {
      render(
        <MemoryRouter initialEntries={[path]}>
          <App />
        </MemoryRouter>,
      );
      const notices = screen.getAllByTestId("synthetic-data-notice");
      expect(notices.length).toBe(1);
      expect(notices[0]).toHaveTextContent(/100% synthetic data/i);
      expect(notices[0]).toHaveTextContent(/not for clinical use/i);
    },
  );

  it("[AC-119] an unregistered route still shows the notice after its redirect", () => {
    render(
      <MemoryRouter initialEntries={["/nowhere"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("synthetic-data-notice")).toBeInTheDocument();
  });
});
