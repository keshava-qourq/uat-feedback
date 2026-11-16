/**
 * NFR-017: a visible notice that the data is wholly synthetic and not for clinical use
 * must appear on every route. It is mounted once, in the app's root layout, so a new
 * route inherits it automatically -- never hand-added to a screen file.
 *
 * AC-120 (out of scope this sprint): no printable or exported document exists yet. When
 * the referral packet (US-024) and the visit-prep PDF (US-028) are built, their Jinja2
 * templates must carry this same notice text on EVERY page of the document.
 */
export const SYNTHETIC_DATA_NOTICE = "100% synthetic data — not for clinical use.";

export default function SyntheticDataNotice() {
  return (
    <div
      data-testid="synthetic-data-notice"
      role="note"
      aria-label="Synthetic data notice"
      className="w-full px-4 py-1.5 text-center text-xs font-semibold"
      style={{
        backgroundColor: "var(--brand-primary)",
        // The neutral, not the accent: the accent is a mid-tone teal that does not
        // carry enough contrast on the near-black primary for a notice that must be
        // legible on every route.
        color: "var(--brand-neutral)",
      }}
    >
      {SYNTHETIC_DATA_NOTICE}
    </div>
  );
}
