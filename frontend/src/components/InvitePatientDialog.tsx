import { useState } from "react";

import { ApiError, apiFetch } from "@/lib/api";

/** POST /api/invites response, exactly as the invite contract defines it. */
type InviteResponse = {
  invite_id: string;
  patient_id: string;
  token: string;
  invite_url: string;
  status: "issued";
  expires_at: string;
};

/** The expiry as a plain UTC calendar date: no per-user time zone is stored anywhere. */
function expiryDate(iso: string): string {
  const parsed = new Date(iso);
  return Number.isNaN(parsed.getTime()) ? iso : parsed.toISOString().slice(0, 10);
}

/**
 * AC-084: issues an invite for one patient and shows the returned invite_url once,
 * with a copy control and the expiry. The link lives in component state only; closing
 * the dialog drops it and nothing in the UI can fetch it again (NFR-009: the API never
 * re-displays a live token).
 */
export default function InvitePatientDialog({
  patientId,
  patientName,
  onIssued,
}: {
  patientId: string;
  patientName: string;
  onIssued?: () => void;
}) {
  const [invite, setInvite] = useState<InviteResponse | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  const issue = async () => {
    setBusy(true);
    setError("");
    try {
      const data = await apiFetch<InviteResponse>("/api/invites", {
        method: "POST",
        body: JSON.stringify({ patient_id: patientId, email: null }),
      });
      setInvite(data);
      onIssued?.();
    } catch (err) {
      // 403/404/422 all arrive as {"detail"}: show it inline, keep the screen up.
      setError(err instanceof ApiError ? err.message : "Could not issue an invite.");
    } finally {
      setBusy(false);
    }
  };

  const copy = async () => {
    if (!invite) return;
    try {
      await navigator.clipboard.writeText(invite.invite_url);
      setCopied(true);
    } catch {
      setCopied(false);
      setError("Could not copy the link. Select it and copy it by hand.");
    }
  };

  const close = () => {
    setInvite(null);
    setCopied(false);
  };

  return (
    <div>
      <button
        type="button"
        onClick={issue}
        disabled={busy}
        aria-label={`Invite patient ${patientName}`}
        className="inline-flex min-h-[44px] items-center gap-2 border border-slate-900 px-3 text-xs font-bold uppercase tracking-widest disabled:opacity-60"
      >
        {busy ? "Issuing…" : "Invite patient"}
      </button>

      {error ? (
        <p role="alert" className="mt-2 max-w-xs text-xs font-semibold text-red-700">
          {error}
        </p>
      ) : null}

      {invite ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={`Invite link for ${patientName}`}
          className="mt-2 border border-slate-900 bg-white p-4 text-sm"
          onKeyDown={(event) => {
            if (event.key === "Escape") close();
          }}
        >
          <p className="font-semibold">
            This link is shown once. Copy it now — after you close this dialog it cannot be shown
            again.
          </p>
          <code
            data-testid="invite-url"
            className="mt-2 block break-all border border-slate-300 p-2 text-xs"
          >
            {invite.invite_url}
          </code>
          <p className="mt-2 text-xs">
            Expires <span data-testid="invite-expires">{expiryDate(invite.expires_at)}</span>. It
            opens {patientName}&rsquo;s own intake only.
          </p>
          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={copy}
              className="min-h-[44px] border border-slate-900 bg-slate-900 px-3 text-xs font-bold uppercase tracking-widest text-white"
            >
              Copy link
            </button>
            <button
              type="button"
              onClick={close}
              className="min-h-[44px] border border-slate-900 px-3 text-xs font-bold uppercase tracking-widest"
            >
              Close
            </button>
            <span role="status" className="text-xs">
              {copied ? "Link copied" : ""}
            </span>
          </div>
        </div>
      ) : null}
    </div>
  );
}
