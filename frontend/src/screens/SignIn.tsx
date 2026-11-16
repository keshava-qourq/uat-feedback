import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError, apiFetch, setSessionToken, takeSessionExpired } from "@/lib/api";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@/lib/ui";

type LoginResponse = {
  token: string;
  user: {
    id: string;
    email: string;
    role: "clinician" | "patient" | "admin";
    must_set_password: boolean;
  };
};

export default function SignIn() {
  const navigate = useNavigate();
  // Read once, on mount: the message shows after an expiry redirect and not again.
  const [expired] = useState(takeSessionExpired);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await apiFetch<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      // AC-104: a first-login account must set its own password before it has a session
      // worth keeping, but the token is what later calls need, so store it either way.
      setSessionToken(data.token);
      navigate(data.user.must_set_password ? "/set-password" : "/worklist", { replace: true });
    } catch (err) {
      // The API's own {"detail"} verbatim: it never says whether the password or the
      // account state was wrong, and neither do we.
      setError(err instanceof ApiError ? err.message : "Could not sign in. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-full items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
        </CardHeader>
        <CardContent>
          {expired ? (
            <p role="status" className="mb-4 text-sm text-amber-700">
              Your session expired, please sign in again.
            </p>
          ) : null}
          <form onSubmit={onSubmit} className="flex flex-col gap-3" noValidate>
            <div className="flex flex-col gap-1">
              <Label htmlFor="signin-email">Email</Label>
              <Input
                id="signin-email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="signin-password">Password</Label>
              <Input
                id="signin-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            {error ? (
              <p role="alert" className="text-sm text-red-700">
                {error}
              </p>
            ) : null}
            <Button type="submit" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
