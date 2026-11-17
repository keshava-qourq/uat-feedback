import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { clearSessionToken, setSessionToken } from "@/lib/api";

beforeEach(() => {
  // No screen may reach the network from a component test.
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) }) as Response),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  clearSessionToken();
});

describe("App", () => {
  it("[AC-101] renders a screen inside the app shell and shows its menu when signed in", () => {
    // AC-101: a clinician page is only drawn for a live session, so the test holds one.
    setSessionToken(crypto.randomUUID());
    render(
      <MemoryRouter initialEntries={["/worklist"]}>
        <App />
      </MemoryRouter>,
    );
    // getAllByText, not getByText: the page may repeat its menu item's text.
    expect(screen.getAllByText("Worklist").length).toBeGreaterThan(0);
  });

  it("[AC-101][AC-102] sends a clinician route to sign-in when no session is held", () => {
    render(
      <MemoryRouter initialEntries={["/worklist"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.queryByRole("navigation", { name: "App menu" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });
});
