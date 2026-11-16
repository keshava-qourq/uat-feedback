/// <reference types="vite/client" />
// Without the reference above, `import.meta.env` is not typed and `tsc --noEmit` fails --
// which `vite build` does not catch, because it tree-shakes this module out when no screen
// imports it yet.
//
// Where the deployed API lives: baked in at build time, falling back to the local backend
// so a bare `npm run dev` still points somewhere real.
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// The shared bearer the deployed API expects (its SECRET_KEY). The platform bakes the
// same value into both sides at deploy time, so authenticated calls work out of the box.
export const API_SECRET_KEY: string = import.meta.env.VITE_API_SECRET_KEY ?? "";

// The frontend and the API are on different origins once deployed, so sign-in cannot rely
// on a cookie: SignIn stores the login response's token here and apiFetch sends it as the
// bearer on every later call, ahead of the shared secret.
const SESSION_TOKEN_KEY = "session_token";

export function getSessionToken(): string | null {
  try {
    return localStorage.getItem(SESSION_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setSessionToken(token: string): void {
  try {
    localStorage.setItem(SESSION_TOKEN_KEY, token);
  } catch {
    // Storage unavailable (private mode, quota): the session just won't persist.
  }
}

export function clearSessionToken(): void {
  try {
    localStorage.removeItem(SESSION_TOKEN_KEY);
  } catch {
    // Nothing to clear if storage was never reachable.
  }
}

/** Thrown by apiFetch for any non-2xx response, carrying the API's {"detail"}. */
export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
  }
}

// AC-102/AC-103: a 401 on an authenticated call ends the session everywhere in the SPA.
// api.ts cannot route (it is not a component), so it clears the token, remembers why,
// and announces it; App listens and redirects to /sign-in.
export const SESSION_EXPIRED_EVENT = "session-expired";

// The two unauthenticated endpoints: a 401 from login is "invalid credentials", not an
// expiry, and must not bounce the user or clear anything.
const UNAUTHENTICATED_PATHS = ["/api/auth/login", "/api/auth/set-password"];

let sessionExpired = false;

/** Reads and clears the "your session expired" flag, so the message shows once. */
export function takeSessionExpired(): boolean {
  const was = sessionExpired;
  sessionExpired = false;
  return was;
}

async function detailOf(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      const first = body.detail[0] as { msg?: string } | undefined;
      if (first?.msg) return first.msg;
    }
  } catch {
    // Not JSON: fall through to the generic message.
  }
  return fallback;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const bearer = getSessionToken() ?? API_SECRET_KEY;
  // Join with exactly one slash: API_BASE_URL is baked with a trailing slash (the API
  // sits behind a /apps/<slug>/ path prefix) and paths start with "/", so a naive
  // concat yields "...//auth/me", which a path-prefix proxy need not route.
  const response = await fetch(`${API_BASE_URL.replace(/\/+$/, "")}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await detailOf(
      response,
      `${init?.method ?? "GET"} ${path} failed: ${response.status}`,
    );
    if (response.status === 401 && !UNAUTHENTICATED_PATHS.includes(path)) {
      clearSessionToken();
      sessionExpired = true;
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
    }
    throw new ApiError(response.status, detail);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}
