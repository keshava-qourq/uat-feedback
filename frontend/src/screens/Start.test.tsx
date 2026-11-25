import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "@/App";

const fetchMock = () =>
  vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) }) as Response);

function renderStart() {
  render(
    <MemoryRouter initialEntries={["/start"]}>
      <App />
    </MemoryRouter>,
  );
}

const loginCalls = () =>
  (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls.filter((call) =>
    String(call[0]).includes("/api/auth/login"),
  );

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Start screen", () => {
  it("[AC-147] shows no email field, no password field and no sign-in control", () => {
    renderStart();

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/password/i)).not.toBeInTheDocument();
    expect(document.querySelectorAll('input[type="password"]').length).toBe(0);
    expect(document.querySelectorAll("input").length).toBe(0);
    expect(screen.queryByRole("button", { name: /sign in/i })).not.toBeInTheDocument();
  });

  it("[AC-148] shows both demo entry buttons and the synthetic-data notice", () => {
    renderStart();

    expect(screen.getByRole("button", { name: /open clinician case/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /open patient view/i })).toBeInTheDocument();
    const notice = screen.getByTestId("synthetic-data-notice");
    expect(notice).toHaveTextContent(/100% synthetic data/i);
    expect(notice).toHaveTextContent(/not for clinical use/i);
  });

  it("[AC-149] issues no POST to /api/auth/login on mount or on a button press", async () => {
    renderStart();
    expect(loginCalls()).toHaveLength(0);

    await userEvent.click(screen.getByRole("button", { name: /open clinician case/i }));
    expect(loginCalls()).toHaveLength(0);
  });

  it("[AC-150] the buttons and notice fill the panel with no leftover gap or fixed-width overflow", () => {
    renderStart();

    const clinician = screen.getByRole("button", { name: /open clinician case/i });
    const grid = clinician.parentElement as HTMLElement;
    // One grid holding exactly the two demo buttons: no empty slot where the form was.
    expect(grid.children).toHaveLength(2);
    expect(grid.className).toContain("grid-cols-1");
    expect(grid.className).toContain("sm:grid-cols-2");
    // The panel is fluid up to a max width, so neither viewport scrolls sideways.
    const panel = grid.closest("main") as HTMLElement;
    expect(panel.className).toContain("w-full");
    expect(panel.className).toContain("max-w-md");
  });
});
