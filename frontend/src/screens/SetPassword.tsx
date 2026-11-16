import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { ApiError, apiFetch, clearSessionToken } from "@/lib/api";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from "@/lib/ui";

export default function SetPassword() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  // AC-104: the opaque set-password token travels in the emailed link's query string.
  const token = params.get("token") ?? "";
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await apiFetch("/api/auth/set-password", {
        method: "POST",
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      // The password is set; nothing from before is trusted, so sign in afresh.
      clearSessionToken();
      navigate("/sign-in", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not set the password. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-full items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Set your password</CardTitle>
        </CardHeader>
        <CardContent>
          {token ? null : (
            <p role="alert" className="mb-4 text-sm text-red-700">
              This link is missing its set-password token. Open the link from your invitation email.
            </p>
          )}
          <form onSubmit={onSubmit} className="flex flex-col gap-3" noValidate>
            <div className="flex flex-col gap-1">
              <Label htmlFor="new-password">New password</Label>
              <Input
                id="new-password"
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            {error ? (
              <p role="alert" className="text-sm text-red-700">
                {error}
              </p>
            ) : null}
            <Button type="submit" disabled={busy || !token}>
              {busy ? "Saving…" : "Set password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
