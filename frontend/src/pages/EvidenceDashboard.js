import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, X, ShieldCheck, CheckCircle2, AlertTriangle, Info, ChevronRight,
  Database, ShoppingCart, Factory, UploadCloud, ExternalLink,
} from "lucide-react";

const PROV = {
  LIVE: { label: "LIVE", cls: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  TEST: { label: "TEST", cls: "bg-amber-50 text-amber-700 border-amber-200" },
  SIMULATED: { label: "SIMULATED", cls: "bg-purple-50 text-purple-700 border-purple-200" },
  NOT_TRACKED: { label: "NOT TRACKED YET", cls: "bg-slate-100 text-slate-500 border-slate-200" },
};

const GROUP_ICON = { Commerce: ShoppingCart, Manufacturing: Factory, Publishing: UploadCloud };
const STATUS_ICON = { ok: CheckCircle2, warn: AlertTriangle, info: Info };
const STATUS_COLOR = { ok: "text-emerald-600", warn: "text-amber-600", info: "text-royal" };

function ProvBadge({ p }) {
  const s = PROV[p] || PROV.NOT_TRACKED;
  return <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${s.cls}`} data-testid={`prov-${p}`}>{s.label}</span>;
}

function BetaStatusPanel() {
  const [d, setD] = useState(null);
  const [open, setOpen] = useState(true);
  useEffect(() => { api.get(`/metrics/beta-status?host=${encodeURIComponent(window.location.host)}`).then((r) => setD(r.data)).catch(() => {}); }, []);
  if (!d) return null;
  const shareCls = d.shareable === "YES" ? "text-emerald-600" : d.shareable === "NO" ? "text-red-600" : "text-amber-600";
  return (
    <div className="rounded-2xl border border-gold/40 mb-8 overflow-hidden" style={{ background: "hsl(var(--gold) / 0.05)" }} data-testid="beta-status-panel">
      <div className="flex items-center justify-between p-4 border-b border-gold/30">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-royal" />
          <h3 className="font-heading font-bold text-navy">Founder Beta Status™</h3>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-navy text-white">{d.deployment_state}</span>
        </div>
        <button onClick={() => setOpen(!open)} data-testid="beta-status-toggle" className="text-xs text-royal font-medium">{open ? "Hide" : "Show"}</button>
      </div>
      {open && (
        <div className="p-4">
          <div className="grid sm:grid-cols-3 gap-3 mb-4">
            <div className="bg-card border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Shareable</p>
              <p className={`font-heading font-bold text-lg ${shareCls}`} data-testid="beta-shareable">{d.shareable}</p>
              <p className="text-[11px] text-muted-foreground mt-1">{d.shareable_detail}</p>
            </div>
            <div className="bg-card border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Payments</p>
              <p className="font-heading font-bold text-lg text-amber-600">{d.stripe_test ? "SANDBOX (TEST)" : "LIVE"}</p>
              <p className="text-[11px] text-muted-foreground mt-1">{d.stripe_test ? "Stripe test mode — no real money moves." : "Live payments active."}</p>
            </div>
            <div className="bg-card border rounded-lg p-3">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Operational Connectors</p>
              <p className="font-heading font-bold text-lg text-emerald-600">{d.operational_connectors.length}</p>
              <p className="text-[11px] text-muted-foreground mt-1">{d.operational_connectors.join(", ") || "None"}</p>
            </div>
          </div>

          {d.blocks_promotion?.length > 0 && (
            <div className="mb-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-xs font-semibold text-amber-800 flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> What blocks Production promotion</p>
              <ul className="mt-1.5 space-y-1">
                {d.blocks_promotion.map((b, i) => <li key={i} className="text-[11px] text-amber-800 flex gap-1.5"><span>•</span>{b}</li>)}
              </ul>
            </div>
          )}

          <div className="grid sm:grid-cols-2 gap-x-6 gap-y-2" data-testid="beta-questions">
            {d.questions.map((q, i) => {
              const Icon = STATUS_ICON[q.status] || Info;
              return (
                <div key={i} className="flex gap-2 text-xs py-1 border-b border-border/50">
                  <Icon className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${STATUS_COLOR[q.status]}`} />
                  <div>
                    <p className="font-medium text-navy">{q.q}</p>
                    <p className="text-muted-foreground">{q.a}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function DrilldownModal({ metric, onClose }) {
  const [d, setD] = useState(null);
  useEffect(() => {
    setD(null);
    api.get(`/metrics/${metric.id}/evidence`).then((r) => setD(r.data)).catch(() => setD({ records: [], columns: [], empty_message: "Could not load evidence." }));
  }, [metric.id]);
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="drilldown-modal">
      <div className="bg-card rounded-lg max-w-6xl w-full max-h-[88vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-royal" />
            <p className="font-heading font-bold text-navy">{metric.label} — Evidence</p>
            {d && <ProvBadge p={d.provenance || metric.provenance} />}
          </div>
          <button onClick={onClose} data-testid="drilldown-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>
        <div className="p-4 overflow-auto">
          <p className="text-xs text-muted-foreground mb-3">{metric.note}</p>
          {!d ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-8"><Loader2 className="w-4 h-4 animate-spin" /> Loading evidence…</div>
          ) : d.records.length === 0 ? (
            <div className="text-sm text-muted-foreground py-8 text-center" data-testid="drilldown-empty">
              <Info className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              {d.empty_message || "No records to show."}
            </div>
          ) : (
            <div className="overflow-x-auto border rounded-lg">
              <table className="w-full text-xs" data-testid="drilldown-table">
                <thead className="bg-muted/50">
                  <tr>{d.columns.map((c) => <th key={c.key} className="text-left font-semibold text-navy px-3 py-2 whitespace-nowrap">{c.label}</th>)}</tr>
                </thead>
                <tbody>
                  {d.records.map((r, i) => (
                    <tr key={i} className="border-t hover:bg-muted/30" data-testid={`drilldown-row-${i}`}>
                      {d.columns.map((c) => (
                        <td key={c.key} className="px-3 py-2 whitespace-nowrap text-muted-foreground">
                          {c.key === "mode" ? <ProvBadge p={r[c.key]} />
                            : String(r[c.key] ?? "—")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {d && d.records.length > 0 && <p className="text-[11px] text-muted-foreground mt-2">{d.records.length} record{d.records.length !== 1 ? "s" : ""} · every value above is a real stored record.</p>}
        </div>
      </div>
    </div>
  );
}

export default function EvidenceDashboard() {
  const [data, setData] = useState(null);
  const [active, setActive] = useState(null);

  useEffect(() => { api.get("/metrics/summary").then((r) => setData(r.data)).catch(() => {}); }, []);

  if (!data) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  const groups = data.groups.map((g) => ({ name: g, items: data.metrics.filter((m) => m.group === g) }));

  return (
    <div>
      <PageHeader
        overline="Evidence Metrics Engine™ · Treasure Standard™"
        title="Evidence Dashboard"
        description="Every number traces to real records. Click any metric to see the exact evidence behind it. TEST and LIVE activity are never combined."
      />

      <BetaStatusPanel />

      {groups.map((g) => {
        const GIcon = GROUP_ICON[g.name] || Database;
        return (
          <div key={g.name} className="mb-8">
            <p className="overline text-primary mb-3 flex items-center gap-1.5"><GIcon className="w-3.5 h-3.5" /> {g.name}</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3" data-testid={`metric-group-${g.name}`}>
              {g.items.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setActive(m)}
                  data-testid={`metric-card-${m.id}`}
                  className="text-left bg-card border border-border rounded-xl p-4 hover:border-primary hover:shadow-sm transition-colors group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <ProvBadge p={m.provenance} />
                    <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                  <p className="font-heading text-2xl font-bold text-navy">{m.display}</p>
                  <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">{m.label}</p>
                </button>
              ))}
            </div>
          </div>
        );
      })}

      {active && <DrilldownModal metric={active} onClose={() => setActive(null)} />}
    </div>
  );
}
