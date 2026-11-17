import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "@/App";
import SetPassword from "./SetPassword";
import { apiFetch, clearSessionToken, getSessionToken, setSessionToken } from "@/lib/api";

const password = () => crypto.randomUUID();

// Typed as fetch itself, so `.mock.calls[i]` keeps fetch's argument tuple.
const mockFetch = (impl: typeof fetch) => vi.fn(impl);

const okJson = (body: unknown) => ({ ok: true, status: 200, json: async () => body }) as Response;
const errJson = (status: number, detail: string) =>
  ({ ok: false, status, json: async () => ({ detail }) }) as Response;

const loginBody = (must_set_password = false) => ({
  token: crypto.randomUUID(),
  user: {
    id: crypto.randomUUID(),
    email: "clinician@example.test",
    role: "clinician",
    must_set_password,
  },
});

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

async function submitSignIn() {
  await userEvent.type(screen.getByLabelText("Email"), "clinician@example.test");
  await userEvent.type(screen.getByLabelText("Password"), password());
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
}

beforeEach(() => {
  clearSessionToken();
});

afterEach(() => {
  vi.unstubAllGlobals();
  clearSessionToken();
});

describe("sign-in", () => {
  it("[AC-100] a successful sign-in stores the token and lands on the worklist", async () => {
    const body = loginBody();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => okJson(body)),
    );
    renderAt("/sign-in");
    await submitSignIn();

    await waitFor(() => expect(getSessionToken()).toBe(body.token));
    await waitFor(() => expect(screen.getAllByText("Worklist").length).toBeGreaterThan(0));

    const call = (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(String(call[0])).toMatch(/\/api\/auth\/login$/);
    expect((call[1] as RequestInit).method).toBe("POST");
    expect((call[1] as RequestInit).credentials).toBeUndefined();
  });

  it("[AC-100] a failed sign-in shows the API's detail and stores no token", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => errJson(401, "Invalid credentials")),
    );
    renderAt("/sign-in");
    await submitSignIn();

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials");
    expect(getSessionToken()).toBeNull();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });

  it("[AC-104] must_set_password routes to the set-password screen", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => okJson(loginBody(true))),
    );
    renderAt("/sign-in");
    await submitSignIn();

    expect(await screen.findByText("Set your password")).toBeInTheDocument();
  });
});

describe("route guard and session expiry", () => {
  it("[AC-101] a clinician route without a token redirects to sign-in", () => {
    renderAt("/worklist");
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });

  it("[AC-101] sign-out calls logout, clears the token and returns to sign-in", async () => {
    setSessionToken(crypto.randomUUID());
    const fetchMock = mockFetch(async () => okJson({ detail: "signed out" }));
    vi.stubGlobal("fetch", fetchMock);
    renderAt("/worklist");

    await userEvent.click(screen.getByRole("button", { name: "Sign out" }));

    await waitFor(() => expect(getSessionToken()).toBeNull());
    expect(await screen.findByRole("button", { name: "Sign in" })).toBeInTheDocument();
    const logout = fetchMock.mock.calls.find((c) => String(c[0]).endsWith("/api/auth/logout"))!;
    expect((logout[1] as RequestInit).method).toBe("POST");
  });

  it("[AC-102][AC-103] a 401 clears the token and redirects with the expiry message", async () => {
    setSessionToken(crypto.randomUUID());
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => errJson(401, "Not authenticated")),
    );
    renderAt("/worklist");

    await expect(apiFetch("/api/worklist")).rejects.toThrow();

    await waitFor(() => expect(getSessionToken()).toBeNull());
    expect(await screen.findByRole("status")).toHaveTextContent(
      /your session expired, please sign in again/i,
    );
  });
});

describe("set-password", () => {
  it("[AC-104] posts the URL token with the new password and returns to sign-in", async () => {
    const token = crypto.randomUUID();
    const fetchMock = mockFetch(async () => okJson({ detail: "password set" }));
    vi.stubGlobal("fetch", fetchMock);
    renderAt(`/set-password?token=${token}`);

    await userEvent.type(screen.getByLabelText("New password"), password());
    await userEvent.click(screen.getByRole("button", { name: "Set password" }));

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument(),
    );
    const call = fetchMock.mock.calls[0];
    expect(String(call[0])).toMatch(/\/api\/auth\/set-password$/);
    const sent = JSON.parse(String((call[1] as RequestInit).body));
    expect(sent.token).toBe(token);
    expect(typeof sent.new_password).toBe("string");
    expect(getSessionToken()).toBeNull();
  });

  it("[AC-104] a rejected token shows the API's detail and stays on the screen", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => errJson(409, "This link has already been used.")),
    );
    render(
      <MemoryRouter initialEntries={[`/set-password?token=${crypto.randomUUID()}`]}>
        <Routes>
          <Route path="/set-password" element={<SetPassword />} />
        </Routes>
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText("New password"), password());
    await userEvent.click(screen.getByRole("button", { name: "Set password" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("This link has already been used.");
  });
});
