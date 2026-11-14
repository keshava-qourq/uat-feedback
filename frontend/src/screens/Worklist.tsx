// @ts-nocheck -- generated from the approved design under its JS runtime contract; not hand-written TypeScript.
/* eslint-disable @typescript-eslint/no-unused-vars */
import React from "react";

import * as UI from "@/lib/ui";
import { Icons } from "@/lib/icons";
import { brand } from "@/lib/brand";
import { useNavigate } from "@/lib/navigate";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const { Table, THead, TBody, TR, TH, TD, Empty } = UI;
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const { Filter } = Icons;

const TIER_ORDER = { 'High': 0, 'Moderate': 1, 'Insufficient history': 2, 'Low': 3 };
const FILTERS = ['All', 'High', 'Moderate', 'Insufficient history', 'Low'];

const INVITE_LABEL = {
  none: 'Not invited',
  sent: 'Not yet opened',
  opened: 'Opened',
  done: 'Intake completed',
};
const INVITE_GLYPH = { none: '–', sent: '○', opened: '◐', done: '●' };

const PATIENTS = [
  { id: 'p-0412', name: 'Delphine Archambault', meta: '1991 · F', tier: 'High', reason: 'Night pain, alternating buttock pain and prior uveitis; HLA-B27 positive; MRI wording of sacroiliitis.', span: '7 yr 3 mo', decision: { kind: 'Agree', by: 'Dr. Imani Rao', on: '12 Nov' }, invite: 'done' },
  { id: 'p-0388', name: 'Tomasz Wieczorek', meta: '1987 · M', tier: 'High', reason: 'Four years of back-pain visits, CRP raised twice, parent with spondylitis.', span: '5 yr 8 mo', decision: null, invite: 'opened' },
  { id: 'p-0451', name: 'Marisol Quintero', meta: '1993 · F', tier: 'High', reason: 'Uveitis history, plus cash-paid chiropractic care reported at intake.', span: '5 yr 0 mo', decision: null, invite: 'done' },
  { id: 'p-0307', name: 'Rosalind Achterberg', meta: '1994 · F', tier: 'Moderate', reason: 'Chronic back pain under a fibromyalgia label; HLA-B27 negative and CRP normal, which do not rule it out.', span: '4 yr 1 mo', decision: { kind: 'Need more info', by: 'Dr. Imani Rao', on: '10 Nov' }, invite: 'done' },
  { id: 'p-0366', name: 'Odalys Brennan', meta: '1996 · F', tier: 'Moderate', reason: 'Capped below High: postpartum onset and iliac-side sclerosis fit osteitis condensans ilii.', span: '6 yr 2 mo', decision: { kind: 'Agree', by: 'Dr. Samuel Whitlock', on: '13 Nov' }, invite: 'opened' },
  { id: 'p-0429', name: 'Callum Ferreira', meta: '1999 · M', tier: 'Moderate', reason: 'Heel pain and one uveitis episode; back-pain pattern not yet documented.', span: '3 yr 6 mo', decision: null, invite: 'sent' },
  { id: 'p-0274', name: 'Bertrand Nkemelu', meta: '1983 · M', tier: 'Insufficient history', reason: 'Only 10 months of records reachable after an insurer change; no symptom intake yet.', span: '10 mo', decision: null, invite: 'none' },
  { id: 'p-0340', name: 'Henrik Solvang', meta: '1978 · M', tier: 'Insufficient history', reason: 'Back care was paid in cash; only 11 months of claims are reachable.', span: '11 mo', decision: null, invite: 'sent' },
  { id: 'p-0495', name: 'Priya Venkataraghavan', meta: '2001 · F', tier: 'Insufficient history', reason: 'Coverage began 9 months ago; nothing earlier is connected.', span: '9 mo', decision: null, invite: 'opened' },
  { id: 'p-0219', name: 'Lucien Marchetti', meta: '1997 · M', tier: 'Low', reason: 'Rower with load-related sacroiliac edema; pain worse with activity.', span: '4 yr 11 mo', decision: { kind: 'Agree', by: 'Dr. Samuel Whitlock', on: '9 Nov' }, invite: 'done' },
  { id: 'p-0258', name: 'Gideon Aldous', meta: '1990 · M', tier: 'Low', reason: 'Back pain after lifting; normal CRP, good NSAID response, no inflammatory features.', span: '8 yr 4 mo', decision: null, invite: 'none' },
  { id: 'p-0231', name: 'Imelda Oyelaran', meta: '1969 · F', tier: 'Low', reason: 'Widespread pain, normal CRP and poor NSAID response; counter-evidence applied.', span: '6 yr 9 mo', decision: { kind: 'Disagree', by: 'Dr. Imani Rao', on: '11 Nov' }, invite: 'none' },
  { id: 'p-0203', name: 'Wren Takahashi', meta: '1985 · F', tier: 'Low', reason: 'A single back-pain visit in 2024; no family history, eye or joint signs on record.', span: '6 yr 9 mo', decision: null, invite: 'none' },
].sort((a, b) => TIER_ORDER[a.tier] - TIER_ORDER[b.tier]);

export default function Screen() {
  const navigate = useNavigate();
  const P = brand.primaryColor;
  const A = brand.accentColor;
  const BG = brand.backgroundColor;
  const N = brand.neutralColor;
  const hair = `color-mix(in srgb, ${P} 16%, transparent)`;
  const soft = `color-mix(in srgb, ${P} 78%, transparent)`;
  const surface = `color-mix(in srgb, ${BG} 45%, white)`;
  const spacing = 16;

  const [patients, setPatients] = React.useState(PATIENTS);
  const [filter, setFilter] = React.useState('All');
  const [issued, setIssued] = React.useState(null);

  const counts = React.useMemo(() => {
    const c = { All: patients.length };
    patients.forEach((p) => { c[p.tier] = (c[p.tier] || 0) + 1; });
    return c;
  }, [patients]);

  const rows = filter === 'All' ? patients : patients.filter((p) => p.tier === filter);
  const nextToInvite = patients.find((p) => p.invite === 'none');

  const openCase = (p) => navigate(p.tier === 'Insufficient history' ? 'insufficient-history' : 'case-summary');

  const sendInvite = () => {
    if (!nextToInvite) return;
    setPatients((list) => list.map((p) => (p.id === nextToInvite.id ? { ...p, invite: 'sent' } : p)));
    setIssued({ id: nextToInvite.id, name: nextToInvite.name });
  };

  const fontHead = { fontFamily: brand.fontHeading, textTransform: 'uppercase', letterSpacing: '0.16em' };
  const th = { fontFamily: brand.fontBody, textTransform: 'uppercase', letterSpacing: '0.14em', fontSize: 12, fontWeight: 600, color: P, textAlign: 'left', padding: '12px 16px', borderBottom: `1px solid ${P}`, backgroundColor: 'transparent', whiteSpace: 'nowrap' };
  const td = { padding: '16px', verticalAlign: 'top', borderBottom: `1px solid ${hair}`, fontSize: 14, lineHeight: 1.5, color: P };

  const Ornament = ({ className }) => (
    <div className={'flex items-center gap-3 ' + (className || '')} aria-hidden="true">
      <span className="flex-1" style={{ height: 1, backgroundColor: A }} />
      <span style={{ width: 9, height: 9, transform: 'rotate(45deg)', border: `1px solid ${P}`, backgroundColor: A }} />
      <span className="flex-1" style={{ height: 1, backgroundColor: A }} />
    </div>
  );

  const TierBadge = ({ tier }) => {
    const base = { display: 'inline-flex', alignItems: 'center', gap: 8, padding: '4px 12px', fontSize: 12, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', whiteSpace: 'nowrap', fontFamily: brand.fontBody };
    if (tier === 'High') return (
      <span style={{ ...base, backgroundColor: P, color: A, border: `1px solid ${P}` }}><span aria-hidden="true" style={{ letterSpacing: 2 }}>◆◆◆</span>High</span>
    );
    if (tier === 'Moderate') return (
      <span style={{ ...base, backgroundColor: A, color: P, border: `1px solid ${P}` }}><span aria-hidden="true" style={{ letterSpacing: 2 }}>◆◆◇</span>Moderate</span>
    );
    if (tier === 'Insufficient history') return (
      <span style={{ ...base, color: P, border: `1px dashed ${P}`, backgroundImage: `repeating-linear-gradient(135deg, transparent 0 5px, color-mix(in srgb, ${P} 14%, transparent) 5px 6px)` }}>
        <Icons.Clock className="w-4 h-4" aria-hidden="true" />Insufficient history
      </span>
    );
    return (
      <span style={{ ...base, color: P, border: `1px solid ${N}`, backgroundColor: 'transparent' }}><span aria-hidden="true" style={{ letterSpacing: 2 }}>◆◇◇</span>Low</span>
    );
  };

  return (
    <div style={{ backgroundColor: BG, color: P, fontFamily: brand.fontBody, minHeight: '100%' }} className="px-4 py-6 md:px-8 md:py-8">
      <style>{`
        .wl-focus:focus-visible { outline: 2px solid ${P}; outline-offset: 3px; }
        .wl-row { transition: background-color 160ms ease; }
        .wl-row:hover { background-color: color-mix(in srgb, ${A} 22%, transparent); }
        .wl-chip { transition: background-color 160ms ease, color 160ms ease; }
        .wl-chip:hover { background-color: color-mix(in srgb, ${A} 35%, transparent); }
        .wl-chip[aria-pressed="true"]:hover { background-color: ${P}; }
        .wl-btn { transition: transform 160ms ease, background-color 160ms ease; }
        .wl-btn:hover:not(:disabled) { background-color: color-mix(in srgb, ${P} 88%, ${A}); }
        .wl-btn:active:not(:disabled) { transform: translateY(1px); }
        .wl-btn:disabled { opacity: 0.55; cursor: not-allowed; }
        .wl-link:hover { text-decoration: underline; text-underline-offset: 4px; }
        @keyframes wl-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
        @keyframes wl-flash { from { background-color: color-mix(in srgb, ${A} 60%, transparent); } to { background-color: transparent; } }
        .wl-enter { animation: wl-in 220ms ease both; }
        .wl-flash { animation: wl-flash 1600ms ease both; }
        @media (prefers-reduced-motion: reduce) { .wl-enter, .wl-flash { animation: none; } .wl-row, .wl-chip, .wl-btn { transition: none; } }
      `}</style>

      <div className="mx-auto" style={{ maxWidth: 1152 }}>
        {/* Row 1 */}
        <div className="grid grid-cols-12 gap-6 items-end">
          <div data-wf="b-0-0" className="col-span-12 md:col-span-8">
            <p style={{ fontSize: 12, letterSpacing: '0.2em', textTransform: 'uppercase', color: soft, margin: 0 }}>Clinician · Dr. Imani Rao</p>
            <h1 style={{ ...fontHead, fontSize: 40, lineHeight: 1.1, fontWeight: 700, margin: '8px 0 12px' }}>Worklist</h1>
            <p style={{ fontSize: 15, lineHeight: 1.5, color: soft, margin: 0, maxWidth: 560 }}>
              Synthetic patients, most urgent first. Each is scored as of their own cutoff date, and the history we could reach is shown beside every status.
            </p>
          </div>
          <div className="col-span-12 md:col-span-4 flex flex-col md:items-end gap-2">
            <button
              type="button"
              data-wf="b-0-1"
              onClick={sendInvite}
              disabled={!nextToInvite}
              className="wl-btn wl-focus inline-flex items-center justify-center gap-3"
              style={{ backgroundColor: P, color: A, border: `1px solid ${A}`, outline: `1px solid ${P}`, outlineOffset: 3, minHeight: 48, padding: '0 24px', fontSize: 13, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase', borderRadius: 0, margin: 4 }}
            >
              <Icons.ArrowRight className="w-4 h-4" aria-hidden="true" />
              Invite patient
            </button>
            <p style={{ fontSize: 12, color: soft, margin: 0 }} className="md:text-right">
              {nextToInvite ? <>Next without an invite: <strong style={{ color: P }}>{nextToInvite.name}</strong></> : 'Every patient on this list already has an invite.'}
            </p>
          </div>
        </div>

        <Ornament className="mt-6" />

        <p className="mt-3 text-center" style={{ fontSize: 12, letterSpacing: '0.14em', textTransform: 'uppercase', color: soft }}>
          100% synthetic data · Not for clinical use
        </p>

        {issued && (
          <div
            role="status"
            className="wl-enter mt-6"
            onKeyDown={(e) => { if (e.key === 'Escape') setIssued(null); }}
            style={{ border: `1px solid ${A}`, outline: `1px solid ${P}`, outlineOffset: 4, margin: '24px 4px 0', padding: 16, backgroundColor: surface }}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 style={{ ...fontHead, fontSize: 16, margin: 0, fontWeight: 700 }}>Invite ready for {issued.name}</h2>
                <p style={{ fontSize: 14, lineHeight: 1.5, margin: '8px 0 8px' }}>
                  Send this link yourself. It works once, expires on 21 Nov 2026, and opens only {issued.name.split(' ')[0]}’s own story.
                </p>
                <code style={{ fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 13, padding: '8px 12px', border: `1px solid ${hair}`, display: 'inline-block', wordBreak: 'break-all', backgroundColor: BG }}>
                  https://odyssey-copilot.example/invite/&lt;single-use-token&gt;
                </code>
              </div>
            </div>
          </div>
        )}

        {/* Row 2 */}
        <div data-wf="b-1-0" className="mt-8">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-3" role="group" aria-label="Filter by status">
            <span className="inline-flex items-center gap-2" style={{ fontSize: 12, fontWeight: 700, letterSpacing: '0.16em', textTransform: 'uppercase' }}>
              <Icons.Filter className="w-4 h-4" aria-hidden="true" />Filter by status
            </span>
            {FILTERS.map((f, i) => {
              const on = filter === f;
              return (
                <button
                  key={f}
                  type="button"
                  data-wf={`i-1-0-${i}`}
                  aria-pressed={on}
                  onClick={() => setFilter(f)}
                  className="wl-chip wl-focus inline-flex items-center gap-2"
                  style={{ minHeight: 44, padding: '0 16px', fontSize: 13, fontWeight: 600, letterSpacing: '0.06em', border: `1px solid ${P}`, backgroundColor: on ? P : 'transparent', color: on ? A : P }}
                >
                  {f}
                  <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 400, opacity: 0.9 }}>({counts[f] || 0})</span>
                </button>
              );
            })}
          </div>
          <p aria-live="polite" style={{ fontSize: 13, color: soft, margin: '12px 0 0', fontVariantNumeric: 'tabular-nums' }}>
            Showing {rows.length} of {patients.length} patients{filter !== 'All' ? ` with status ${filter}` : ''}.
          </p>
        </div>

        {/* Row 3 */}
        <section data-wf="b-2-0" aria-labelledby="wl-patients" className="mt-6" style={{ margin: '24px 4px 0' }}>
          <div style={{ border: `1px solid ${A}`, outline: `1px solid ${P}`, outlineOffset: 4, backgroundColor: surface }}>
            <div className="px-4 pt-6">
              <h2 id="wl-patients" style={{ ...fontHead, fontSize: 22, fontWeight: 700, textAlign: 'center', margin: 0 }}>Patients</h2>
              <Ornament className="mt-3" />
            </div>
            {rows.length === 0 ? (
              <div className="p-8">
                <Empty
                  title="No patients at this status"
                  description="Nobody on your list is currently at this status. Choose All to see every patient assigned to you."
                  action={<button type="button" onClick={() => setFilter('All')} className="wl-focus" style={{ minHeight: 44, padding: '0 16px', border: `1px solid ${P}`, backgroundColor: P, color: A, fontWeight: 700, fontSize: 13, letterSpacing: '0.1em', textTransform: 'uppercase' }}>Show all patients</button>}
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table className="w-full" style={{ borderCollapse: 'collapse', minWidth: 980, fontVariantNumeric: 'tabular-nums' }}>
                  <THead>
                    <TR>
                      <TH data-wf="i-2-0-0" scope="col" style={th}>Patient</TH>
                      <TH data-wf="i-2-0-1" scope="col" style={th}>Status</TH>
                      <TH data-wf="i-2-0-2" scope="col" style={th}>Reason</TH>
                      <TH data-wf="i-2-0-3" scope="col" style={th}>Reachable history</TH>
                      <TH data-wf="i-2-0-4" scope="col" style={th}>Decision</TH>
                      <TH data-wf="i-2-0-5" scope="col" style={th}>Invite status</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {rows.map((p) => {
                      const insuff = p.tier === 'Insufficient history';
                      return (
                        <TR
                          key={p.id}
                          className={'wl-row wl-enter' + (issued && issued.id === p.id ? ' wl-flash' : '')}
                          onClick={() => openCase(p)}
                          style={{ cursor: 'pointer', boxShadow: insuff ? `inset 3px 0 0 0 ${N}` : 'none' }}
                        >
                          <TD style={td}>
                            <button
                              type="button"
                              onClick={(e) => { e.stopPropagation(); openCase(p); }}
                              className="wl-focus wl-link text-left"
                              style={{ background: 'none', border: 0, padding: 0, minHeight: 24, color: P, fontWeight: 700, fontSize: 15, cursor: 'pointer' }}
                            >
                              {p.name}
                              <span className="sr-only">{insuff ? ' — open what we still need' : ' — open case summary'}</span>
                            </button>
                            <div style={{ fontSize: 12, color: soft, marginTop: 4 }}>{p.meta} · {p.id.toUpperCase()}</div>
                          </TD>
                          <TD style={td}><TierBadge tier={p.tier} /></TD>
                          <TD style={{ ...td, maxWidth: 360 }}>{p.reason}</TD>
                          <TD style={{ ...td, whiteSpace: 'nowrap' }}>
                            <span style={{ fontWeight: 600 }}>{p.span}</span>
                            {insuff && <div style={{ fontSize: 12, color: soft, marginTop: 4 }}>Below the threshold</div>}
                          </TD>
                          <TD style={td}>
                            {p.decision ? (
                              <>
                                <div style={{ fontWeight: 600 }}>{p.decision.kind}</div>
                                <div style={{ fontSize: 12, color: soft, marginTop: 4 }}>{p.decision.by} · {p.decision.on}</div>
                              </>
                            ) : (
                              <span style={{ color: soft }}>No decision yet</span>
                            )}
                          </TD>
                          <TD style={{ ...td, whiteSpace: 'nowrap' }}>
                            <span aria-hidden="true" style={{ display: 'inline-block', width: 16 }}>{INVITE_GLYPH[p.invite]}</span>
                            <span style={{ color: p.invite === 'none' ? soft : P }}>{INVITE_LABEL[p.invite]}</span>
                          </TD>
                        </TR>
                      );
                    })}
                  </TBody>
                </Table>
              </div>
            )}
            <p style={{ fontSize: 12, color: soft, margin: 0, padding: '12px 16px 16px' }}>
              Order: High, Moderate, Insufficient history, then Low. Insufficient history means we could not see enough to say, and is never the same as Low.
            </p>
          </div>
        </section>

        {/* Row 4 */}
        <div data-wf="b-3-0" className="mt-8 flex justify-center">
          <button
            type="button"
            onClick={() => navigate('insufficient-history')}
            className="wl-focus wl-link inline-flex items-center gap-2"
            style={{ background: 'none', border: 0, minHeight: 44, color: P, fontSize: 14, fontWeight: 600, cursor: 'pointer', textAlign: 'center' }}
          >
            <span aria-hidden="true" style={{ width: 8, height: 8, transform: 'rotate(45deg)', backgroundColor: A, border: `1px solid ${P}`, display: 'inline-block' }} />
            Insufficient history rows open the what-we-still-need screen
            <Icons.ChevronRight className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}
