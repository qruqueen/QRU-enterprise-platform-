import React from "react";
import { ChevronRight, Landmark } from "lucide-react";

/* ============================================================
   QRU Component Library™ (MO-004)
   Reusable enterprise components so every page inherits the
   QRU Master Design Language. Deep Navy foundation · QRU Gold
   excellence · Royal Purple signature accent · White clarity.
   ============================================================ */

/* -------- Brand marks (SVG code, never image files) -------- */

export function QRUShield({ className = "w-8 h-8", title = "QRU" }) {
  return (
    <svg viewBox="0 0 100 120" className={className} role="img" aria-label={title} fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M50 4 L90 20 V56 C90 86 72 106 50 116 C28 106 10 86 10 56 V20 Z"
        fill="hsl(var(--navy))"
        stroke="hsl(var(--gold))"
        strokeWidth="3"
      />
      <path d="M32 54 L45 68 L70 40" stroke="hsl(var(--gold))" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  );
}

export function TreasureSeal({ className = "w-16 h-16" }) {
  return (
    <svg viewBox="0 0 100 100" className={className} fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Treasure Standard Verified">
      <circle cx="50" cy="50" r="46" fill="hsl(var(--gold))" />
      <circle cx="50" cy="50" r="39" stroke="hsl(var(--navy))" strokeWidth="1.5" strokeDasharray="3 3" />
      <path d="M32 34 L50 22 L68 34" stroke="hsl(var(--navy))" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <text x="50" y="55" fontFamily="Playfair Display, serif" fontSize="18" fontWeight="800" fill="hsl(var(--navy))" textAnchor="middle">QRU</text>
      <text x="50" y="72" fontFamily="Manrope, sans-serif" fontSize="7.5" fontWeight="700" fill="hsl(var(--navy))" textAnchor="middle" letterSpacing="1.2">VERIFIED</text>
    </svg>
  );
}

/* -------- Provenance badge (Treasure Standard™ honesty) -------- */

const PROV = {
  LIVE: "bg-emerald-50 text-emerald-700 border-emerald-200",
  TEST: "bg-amber-50 text-amber-700 border-amber-200",
  SIMULATED: "bg-violet-50 text-violet-700 border-violet-200",
  NOT_TRACKED: "bg-slate-100 text-slate-500 border-slate-200",
};
const PROV_LABEL = { LIVE: "LIVE", TEST: "TEST", SIMULATED: "SIMULATED", NOT_TRACKED: "NOT TRACKED YET" };

export function ProvenanceBadge({ provenance, testid }) {
  if (!provenance) return null;
  return (
    <span data-testid={testid} className={`text-[9px] font-extrabold tracking-wide px-1.5 py-0.5 rounded border ${PROV[provenance] || PROV.NOT_TRACKED}`}>
      {PROV_LABEL[provenance] || provenance}
    </span>
  );
}

/* -------- Universal status chip -------- */

const STATUS_MAP = {
  // success family
  Verified: "emerald", Approved: "emerald", Published: "emerald", Active: "emerald",
  Connected: "emerald", "Ready to Publish": "emerald", Ready: "emerald", Cleared: "emerald",
  "Test Passed": "emerald", Complete: "emerald", passed: "emerald", pass: "emerald",
  // warning family
  Pending: "amber", "In Review": "amber", "Under Review": "amber", "Quality Review": "amber",
  "Needs Review": "amber", "Needs Authorization": "amber", "Reconnect Required": "amber",
  "Connection Expired": "amber", Paused: "amber", warn: "amber", Medium: "amber",
  // navy / structural family
  Draft: "navy", Queued: "navy", Research: "navy", Architecture: "navy",
  "Developer Setup Required": "blue", "Developer Setup Complete": "blue",
  // accent / active
  Manufacturing: "royal", Generating: "royal", Publishing: "royal",
  // destructive
  "Needs Regeneration": "red", Failed: "red", "Connection Error": "red", High: "red", fail: "red",
  // neutral
  "Not Connected": "slate", Superseded: "slate", Archived: "slate", Low: "slate",
};

const CHIP = {
  emerald: "bg-emerald-50 text-emerald-700 border-emerald-200",
  amber: "bg-amber-50 text-amber-700 border-amber-200",
  red: "bg-red-50 text-red-700 border-red-200",
  blue: "bg-blue-50 text-blue-700 border-blue-200",
  slate: "bg-slate-100 text-slate-500 border-slate-200",
  navy: "bg-navy/8 text-navy border-navy/20",
  royal: "bg-royal/10 text-royal border-royal/25",
  gold: "bg-gold/15 text-navy border-gold/40",
};

export function StatusChip({ status, tone, testid }) {
  const family = tone || STATUS_MAP[status] || "slate";
  return (
    <span data-testid={testid} className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-bold tracking-wide ${CHIP[family]}`}>
      {status}
    </span>
  );
}

/* -------- Enterprise metric card -------- */

export function MetricCard({ icon: Icon, label, value, sub, provenance, accent = "navy", onClick, testid }) {
  const iconColor = accent === "gold" ? "text-gold" : accent === "royal" ? "text-royal" : "text-navy";
  const line = accent === "gold" ? "qru-goldline" : accent === "royal" ? "qru-royalline" : "qru-navyline";
  return (
    <button
      onClick={onClick}
      disabled={!onClick}
      data-testid={testid}
      className={`text-left qru-card ${line} p-5 ${onClick ? "qru-interactive cursor-pointer group" : ""}`}
    >
      <div className="flex items-center justify-between mb-3">
        {Icon && <Icon className={`w-4 h-4 ${iconColor}`} strokeWidth={2} />}
        <div className="flex items-center gap-1.5">
          <ProvenanceBadge provenance={provenance} />
          {onClick && <ChevronRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-navy transition-colors" />}
        </div>
      </div>
      <p className="font-heading text-3xl font-bold text-navy leading-none">{value}</p>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mt-2">{label}</p>
      {sub && <p className="text-[11px] text-muted-foreground/80 mt-0.5">{sub}</p>}
    </button>
  );
}

/* -------- Section panel with title bar -------- */

export function Panel({ title, icon: Icon, right, accent, children, testid, className = "" }) {
  const line = accent === "gold" ? "qru-goldline" : accent === "royal" ? "qru-royalline" : "";
  return (
    <div data-testid={testid} className={`qru-card ${line} overflow-hidden ${className}`}>
      {(title || right) && (
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-border bg-muted/30">
          <p className="font-heading font-bold text-navy flex items-center gap-2 text-[15px]">
            {Icon && <Icon className="w-4 h-4 text-royal" />} {title}
          </p>
          {right}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}

/* -------- Score bar with threshold semantics -------- */

export function ScoreBar({ score = 0, threshold, showLabel = true }) {
  const color = score >= 90 ? "bg-emerald-500" : score >= 70 ? "bg-amber-500" : "bg-red-500";
  const txt = score >= 90 ? "text-emerald-600" : score >= 70 ? "text-amber-600" : "text-red-600";
  return (
    <div>
      {showLabel && (
        <div className="flex justify-end mb-1">
          <span className={`text-xs font-bold ${txt}`}>{score}{threshold != null ? `/${threshold}` : ""}</span>
        </div>
      )}
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full ${color} transition-[width] duration-500 ease-out`} style={{ width: `${Math.min(100, score)}%` }} />
      </div>
    </div>
  );
}

/* -------- Manufacturing lifecycle timeline -------- */

export function StageTimeline({ steps = [], current = 0, testid }) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap" data-testid={testid}>
      {steps.map((s, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <span key={s} className="flex items-center gap-1.5">
            <span
              className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border transition-colors ${
                active ? "bg-navy text-white border-navy"
                  : done ? "bg-gold/15 text-navy border-gold/40"
                  : "bg-muted/40 text-muted-foreground border-border"
              }`}
            >
              {i + 1}. {s}
            </span>
            {i < steps.length - 1 && <ChevronRight className="w-3 h-3 text-muted-foreground/60" />}
          </span>
        );
      })}
    </div>
  );
}

/* -------- Verified / Treasure Standard inline badge -------- */

export function VerifiedBadge({ label = "Treasure Standard™", testid }) {
  return (
    <span data-testid={testid} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-gold/50 bg-gold/12 text-[11px] font-bold text-navy">
      <QRUShield className="w-3.5 h-3.5" /> {label}
    </span>
  );
}

/* -------- Governed-by traceability strip (Governance Binding Layer™) -------- */

export function GovernedBy({ standards = [], className = "", testid }) {
  const list = standards.filter(Boolean);
  if (!list.length) return null;
  return (
    <div data-testid={testid} className={`flex items-center gap-1.5 flex-wrap ${className}`}>
      <span className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground flex items-center gap-1">
        <Landmark className="w-3 h-3" /> Governed by
      </span>
      {list.map((s, i) => (
        <a key={i} href="/qiks"
          className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border transition-colors ${
            s.adopted !== false ? "border-navy/25 bg-navy/[0.06] text-navy hover:border-navy" : "border-amber-300 bg-amber-50 text-amber-700"}`}>
          {s.standard_id ? `${s.standard_id} · ` : ""}{s.name}{s.adopted === false ? " (pending)" : ""}
        </a>
      ))}
    </div>
  );
}
