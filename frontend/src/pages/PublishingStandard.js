import { useEffect, useMemo, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import {
  Loader2, BookOpenCheck, Type, Palette, Quote, ListTree, ShieldCheck, Image as ImageIcon,
  Search, CheckCircle2, XCircle, AlertTriangle, MinusCircle, Layers,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";

const STATUS_ICON = {
  BLOCKING_FAILURE: { icon: XCircle, cls: "text-red-600" },
  WARNING: { icon: AlertTriangle, cls: "text-amber-600" },
  ADVISORY: { icon: AlertTriangle, cls: "text-sky-600" },
  PASSED: { icon: CheckCircle2, cls: "text-emerald-600" },
  NOT_APPLICABLE: { icon: MinusCircle, cls: "text-navy/30" },
};

export default function PublishingStandard() {
  const [std, setStd] = useState(null);
  const [pilot, setPilot] = useState(null);
  const [refs, setRefs] = useState([]);
  const [q, setQ] = useState("");

  useEffect(() => {
    api.get("/publishing/standard").then((r) => setStd(r.data)).catch(() => setStd(false));
    api.get("/publishing/pilot").then((r) => setPilot(r.data)).catch(() => {});
    api.get("/publishing/reference-covers").then((r) => setRefs(r.data.covers)).catch(() => {});
    // Inject the governed CSS so in-app previews use the SAME tokens as PDF/HTML.
    const id = "qru-publishing-tokens";
    if (!document.getElementById(id)) {
      fetch(`${BACKEND}/api/publishing/tokens.css`).then((r) => r.text()).then((css) => {
        const s = document.createElement("style"); s.id = id; s.textContent = css; document.head.appendChild(s);
      });
    }
  }, []);

  const match = (t) => !q || (t || "").toLowerCase().includes(q.toLowerCase());
  const filteredPhil = useMemo(() => (std ? std.philosophy.filter(match) : []), [std, q]); // eslint-disable-line

  if (std === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (std === false) return <p className="text-sm text-muted-foreground p-8">Could not load the Publishing Standard.</p>;

  return (
    <div data-testid="publishing-page">
      <PageHeader
        overline={`${std.doc_id} · v${std.version} · ${std.status} · Foundational`}
        title="Publishing Standard™"
        description="The single governed source of truth for how every QRU product looks and reads. Typography, color, layout, the QRU Callout System™, the professional Table of Contents, the Cover & Visual Identity Standard™, and the Treasure Standard™ Pre-Ship Gate — inherited automatically by every current and future product."
        actions={<VerifiedBadge label="Manufactured Understanding · Luxury Simplicity" testid="publishing-badge" />}
      />
      <GovernedBy standards={[std.doc_id, "QRU-CON-0001"]} className="mb-4" testid="publishing-governed-by" />

      <div className="relative mb-5 max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-2.5 text-navy/40" />
        <input data-testid="publishing-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search the standard…"
          className="w-full border rounded-full pl-9 pr-4 py-2 text-sm focus:outline-none focus:border-royal" />
      </div>

      {/* Philosophy */}
      <Panel title="Design Philosophy" icon={BookOpenCheck} accent="royal" testid="publishing-philosophy" className="mb-6">
        <div className="flex flex-wrap gap-2">
          {filteredPhil.map((p) => <span key={p} className="text-[11px] px-2.5 py-1 rounded-full bg-royal/[0.06] text-navy border border-royal/15">{p}</span>)}
        </div>
      </Panel>

      {/* Typography */}
      {match("typography title heading body") && (
        <Panel title="Typography Hierarchy (13 levels)" icon={Type} accent="gold" testid="publishing-typography" className="mb-6">
          <div className="space-y-2">
            {std.typography.filter((t) => match(t.role)).map((t) => (
              <div key={t.token} className="flex items-baseline justify-between border-b border-navy/5 pb-2" data-testid={`publishing-type-${t.token}`}>
                <span style={{ fontFamily: t.font === "Playfair Display" ? "'Playfair Display',serif" : "'Manrope',sans-serif", fontSize: Math.min(t.size_pt, 30), fontWeight: t.weight, color: "#0B1B3F" }}>{t.role}</span>
                <span className="text-[10px] text-muted-foreground font-mono">{t.font} · {t.size_pt}pt · {t.weight} · lh {t.line}</span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* Colors */}
      {match("color navy gold royal") && (
        <Panel title="Color Tokens" icon={Palette} accent="royal" testid="publishing-colors" className="mb-6">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {std.colors.filter((c) => match(c.purpose + c.token)).map((c) => (
              <div key={c.token} className="border rounded-md p-3 border-navy/10" data-testid={`publishing-color-${c.token}`}>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="w-8 h-8 rounded-md border" style={{ background: c.value }} />
                  <div><p className="text-[11px] font-bold text-navy font-mono">{c.value}</p><p className="text-[10px] text-muted-foreground">{c.token}</p></div>
                </div>
                <p className="text-[10px] text-navy/80">{c.purpose}</p>
                <p className="text-[9px] text-emerald-700 mt-1">✓ {c.allowed_use}</p>
                <p className="text-[9px] text-red-600">✕ {c.prohibited_use}</p>
                <p className="text-[9px] text-muted-foreground mt-0.5">a11y: {c.accessibility}</p>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* Callout system */}
      {match("callout key insight evidence warning treasure") && (
        <Panel title="QRU Callout System™ (10 types)" icon={Quote} accent="gold" testid="publishing-callouts" className="mb-6">
          <div className="grid sm:grid-cols-2 gap-3">
            {std.callouts.filter((c) => match(c.name)).map((c) => (
              <div key={c.id} data-testid={`publishing-callout-${c.id}`} style={{ background: c.ground, borderLeft: `4px solid ${c.border}` }} className="rounded-md p-3">
                <p className="text-[11px] font-bold" style={{ color: c.accent }}>{c.name}</p>
                <p className="text-[10px] text-navy/70 mt-0.5">Consistent color, icon ({c.icon}), border and typography across every product.</p>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* TOC before/after */}
      {pilot && match("table of contents toc dot leaders") && (
        <Panel title="Professional Table of Contents Standard" icon={ListTree} accent="royal" testid="publishing-toc" className="mb-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wide text-red-600 mb-1">Before — raw source</p>
              <pre className="text-[10px] bg-red-50 border border-red-200 rounded-md p-3 whitespace-pre-wrap text-red-900" data-testid="publishing-toc-before">{pilot.pilot.toc_before_raw}</pre>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-700 mb-1">After — governed typeset</p>
              <pre className="text-[11px] bg-white border border-emerald-200 rounded-md p-3 whitespace-pre text-navy overflow-x-auto" style={{ fontFamily: "'Manrope',monospace" }} data-testid="publishing-toc-after">{pilot.pilot.toc_after_lines.join("\n")}</pre>
            </div>
          </div>
        </Panel>
      )}

      {/* Pre-ship gate — pilot before/after */}
      {pilot && (
        <Panel title="Treasure Standard™ Pre-Ship Validation Gate" icon={ShieldCheck} accent="gold" testid="publishing-gate" className="mb-6">
          <div className="grid md:grid-cols-2 gap-4">
            {[["Before (current book)", pilot.preflight_before, "publishing-gate-before"], ["After (governed rebuild)", pilot.preflight_after, "publishing-gate-after"]].map(([label, rep, tid]) => (
              <div key={label} className={`border rounded-md p-3 ${rep.blocked ? "border-red-200 bg-red-50/40" : "border-emerald-200 bg-emerald-50/30"}`} data-testid={tid}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[11px] font-bold text-navy">{label}</p>
                  <StatusChip status={rep.verdict.replace(/_/g, " ")} tone={rep.blocked ? "rose" : "emerald"} />
                </div>
                <p className="text-[10px] text-muted-foreground mb-2">Blocking {rep.counts.BLOCKING_FAILURE} · Warnings {rep.counts.WARNING} · Passed {rep.counts.PASSED} · N/A {rep.counts.NOT_APPLICABLE}</p>
                <div className="space-y-1 max-h-56 overflow-y-auto">
                  {rep.results.filter((r) => r.status !== "PASSED" && r.status !== "NOT_APPLICABLE").map((r) => {
                    const S = STATUS_ICON[r.status] || STATUS_ICON.PASSED; const Ic = S.icon;
                    return (
                      <div key={r.rule_id} className="flex items-start gap-1.5 text-[10px]">
                        <Ic className={`w-3 h-3 mt-0.5 shrink-0 ${S.cls}`} />
                        <span className="text-navy/80"><b>{r.name}</b> — {r.why} <span className="text-royal">({r.responsible_module})</span></span>
                      </div>
                    );
                  })}
                  {rep.results.filter((r) => r.status !== "PASSED" && r.status !== "NOT_APPLICABLE").length === 0 && <p className="text-[10px] text-emerald-700">All measurable checks passed. Ready to ship.</p>}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* Cover standard + reference gallery */}
      <Panel title="Cover & Visual Identity Standard™" icon={ImageIcon} accent="royal" testid="publishing-cover-standard" className="mb-6">
        <p className="text-[12px] text-navy/80 mb-3">{std.cover_standard.philosophy}</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4" data-testid="publishing-reference-covers">
          {refs.map((c) => (
            <div key={c.id} className="border rounded-md overflow-hidden border-navy/10" data-testid={`publishing-ref-${c.id}`}>
              <img src={c.url} alt={c.name} className="w-full h-40 object-cover" />
              <div className="p-2">
                <p className="text-[10px] font-bold text-navy leading-tight">{c.name}</p>
                <StatusChip status={c.classification} tone={c.classification === "Approved Reference" ? "emerald" : c.classification === "Template Candidate" ? "gold" : "blue"} />
                <p className="text-[9px] text-emerald-700 mt-1">Retain: {c.retain.slice(0, 2).join(", ")}</p>
                <p className="text-[9px] text-red-600">Avoid: {c.avoid[0]}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="flex items-start gap-2 text-[10px] text-amber-700 bg-amber-50 border border-amber-200 rounded-md p-2">
          <Layers className="w-3.5 h-3.5 shrink-0 mt-0.5" /> Reference assets are evidence of visual DIRECTION — not permission to reproduce a composition. New covers are original compositions in the same governed family.
        </div>
      </Panel>
    </div>
  );
}
