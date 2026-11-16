import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import Worklist from "./Worklist";

const ID = {
  none: "11111111-1111-1111-1111-111111111111",
  not_yet_opened: "22222222-2222-2222-2222-222222222222",
  opened: "33333333-3333-3333-3333-333333333333",
  intake_completed: "44444444-4444-4444-4444-444444444444",
};

const WORKLIST = {
  items: [
    { patient_id: ID.none, display_name: "Ada Nwosu", invite_status: "none" },
    { patient_id: ID.not_yet_opened, display_name: "Bo Larsen", invite_status: "not_yet_opened" },
    { patient_id: ID.opened, display_name: "Cleo Marsh", invite_status: "opened" },
    {
      patient_id: ID.intake_completed,
      display_name: "Dev Patel",
      invite_status: "intake_completed",
    },
  ],
};

const INVITE = {
  invite_id: "55555555-5555-5555-5555-555555555555",
  patient_id: ID.none,
  token: crypto.randomUUID(),
  invite_url: "https://copilot.example/invite/abc123",
  status: "issued",
  expires_at: "2026-11-23T10:00:00+00:00",
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
  vi.restoreAllMocks();
});

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ok(WORKLIST)),
  );
});

describe("Worklist invite status", () => {
  it("[AC-085] each row shows its invite status and 'none' shows no invite badge", async () => {
    renderScreen();

    await waitFor(() => expect(screen.getByText("Bo Larsen")).toBeInTheDocument());
    expect(screen.getByTestId(`invite-status-${ID.not_yet_opened}`)).toHaveTextContent(
      "Not yet opened",
    );
    expect(screen.getByTestId(`invite-status-${ID.opened}`)).toHaveTextContent("Opened");
    expect(screen.getByTestId(`invite-status-${ID.intake_completed}`)).toHaveTextContent(
      "Intake completed",
    );
    expect(screen.queryByTestId(`invite-status-${ID.none}`)).not.toBeInTheDocument();
  });

  it("[AC-084] inviting a patient posts to /api/invites and shows the link, expiry and copy control", async () => {
    const writeText = vi.fn(async () => undefined);
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
    const fetchMock = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) =>
      init?.method === "POST" ? ok(INVITE) : ok(WORKLIST),
    );
    vi.stubGlobal("fetch", fetchMock);
    renderScreen();

    await waitFor(() => expect(screen.getByText("Ada Nwosu")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: "Invite patient Ada Nwosu" }));

    const dialog = await screen.findByRole("dialog", { name: /invite link for Ada Nwosu/i });
    expect(within(dialog).getByTestId("invite-url")).toHaveTextContent(INVITE.invite_url);
    expect(within(dialog).getByTestId("invite-expires")).toHaveTextContent("2026-11-23");
    expect(dialog).toHaveTextContent(/shown once/i);

    const post = fetchMock.mock.calls.find((c) => (c[1] as RequestInit | undefined)?.method);
    expect(String(post?.[0])).toMatch(/\/api\/invites$/);
    expect(JSON.parse(String((post?.[1] as RequestInit).body))).toEqual({
      patient_id: ID.none,
      email: null,
    });

    await userEvent.click(within(dialog).getByRole("button", { name: /copy link/i }));
    expect(writeText).toHaveBeenCalledWith(INVITE.invite_url);

    // AC-085: the row refreshes after an invite is issued.
    expect(
      fetchMock.mock.calls.filter((c) => !(c[1] as RequestInit | undefined)?.method),
    ).toHaveLength(2);
  });

  it("[AC-084] closing the dialog removes the link and it is not re-fetchable from the UI", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: RequestInfo | URL, init?: RequestInit) =>
        init?.method === "POST" ? ok(INVITE) : ok(WORKLIST),
      ),
    );
    renderScreen();

    await waitFor(() => expect(screen.getByText("Ada Nwosu")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: "Invite patient Ada Nwosu" }));
    const dialog = await screen.findByRole("dialog", { name: /invite link for Ada Nwosu/i });
    await userEvent.click(within(dialog).getByRole("button", { name: /close/i }));

    expect(screen.queryByTestId("invite-url")).not.toBeInTheDocument();
    expect(screen.queryByText(INVITE.invite_url)).not.toBeInTheDocument();
  });

  it("[AC-084] a 403 detail is shown inline without crashing the screen", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: RequestInfo | URL, init?: RequestInit) =>
        init?.method === "POST" ? fail(403, "Not allowed") : ok(WORKLIST),
      ),
    );
    renderScreen();

    await waitFor(() => expect(screen.getByText("Ada Nwosu")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: "Invite patient Ada Nwosu" }));

    expect(await screen.findByText("Not allowed")).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText("Bo Larsen")).toBeInTheDocument();
  });

  it("[AC-084] a 404 on an unknown patient shows its detail inline", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: RequestInfo | URL, init?: RequestInit) =>
        init?.method === "POST" ? fail(404, "Unknown patient") : ok(WORKLIST),
      ),
    );
    renderScreen();

    await waitFor(() => expect(screen.getByText("Ada Nwosu")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: "Invite patient Ada Nwosu" }));

    expect(await screen.findByText("Unknown patient")).toBeInTheDocument();
  });

  it("[AC-085] a failing worklist read surfaces its detail instead of crashing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => fail(403, "Patient tokens may not read the worklist")),
    );
    renderScreen();

    expect(await screen.findByText("Patient tokens may not read the worklist")).toBeInTheDocument();
  });
});
