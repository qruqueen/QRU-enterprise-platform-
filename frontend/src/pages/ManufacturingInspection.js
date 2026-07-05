import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { MetricCard, Panel, ScoreBar, StatusChip } from "@/components/qru";
import {
  Loader2, X, ShieldCheck, CheckCircle2, XCircle, AlertTriangle, PauseCircle, Gauge, Lock,
} from "lucide-react";

const scoreColor = (s) => (s >= 90 ? "text-emerald-600" : s >= 70 ? "text-amber-600" : "text-red-600");

function GateDetail({ productId, onClose }) {
  const [d, setD] = useState(null);
  useEffect(() => {
    setD(null);
    api.get(`/inspection/product/${productId}`).then((r) => setD(r.data)).catch(() => setD(false));
  }, [productId]);
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="inspection-detail">
      <div className="bg-card rounded-lg max-w-2xl w-full max-h-[88vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-royal" />
            <p className="font-heading font-bold text-navy">Manufacturing Inspection</p>
            {d && <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${d.manufacturing_allowed ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"}`}>{d.status}</span>}
          </div>
          <button onClick={onClose} data-testid="inspection-detail-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>
        <div className="p-4 overflow-auto">
          {!d ? <div className="flex items-center gap-2 text-sm text-muted-foreground py-8"><Loader2 className="w-4 h-4 animate-spin" /> Inspecting…</div>
            : d === false ? <p className="text-sm text-muted-foreground">Could not load inspection.</p>
            : (
              <>
                <div className="flex items-baseline gap-2 mb-4">
                  <span className={`text-3xl font-heading font-bold ${scoreColor(d.overall_score)}`}>{d.overall_score}</span>
                  <span className="text-xs text-muted-foreground">overall inspection score · {d.subject?.code} — {d.subject?.title}</span>
                </div>

                {!d.manufacturing_allowed && (
                  <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3" data-testid="inspection-director-report">
                    <p className="text-xs font-semibold text-red-800 flex items-center gap-1.5"><PauseCircle className="w-3.5 h-3.5" /> Manufacturing Director Report — {d.director_report.verdict}</p>
                    <ul className="mt-1.5 space-y-1">
                      {d.director_report.missing_information.map((m, i) => <li key={i} className="text-[11px] text-red-800 flex gap-1.5"><span>•</span>{m}</li>)}
                    </ul>
                  </div>
                )}

                <div className="space-y-2.5" data-testid="inspection-gates">
                  {d.gates.map((g) => {
                    const Icon = g.passed ? CheckCircle2 : XCircle;
                    return (
                      <div key={g.key} className="border rounded-lg p-3" data-testid={`gate-${g.key}`}>
                        <div className="flex items-center justify-between mb-1.5">
                          <p className="text-sm font-semibold text-navy flex items-center gap-1.5">
                            <Icon className={`w-4 h-4 ${g.passed ? "text-emerald-600" : "text-red-600"}`} /> {g.label}
                            {g.blocking && <Lock className="w-3 h-3 text-muted-foreground" title="Blocking gate" />}
                          </p>
                        </div>
                        <ScoreBar score={g.score} threshold={g.threshold} />
                        {g.findings?.length > 0 && (
                          <ul className="mt-1.5 space-y-0.5">{g.findings.map((f, i) => <li key={i} className="text-[11px] text-muted-foreground flex gap-1.5"><span>•</span>{f}</li>)}</ul>
                        )}
                      </div>
                    );
                  })}
                </div>
              </>
            )}
        </div>
      </div>
    </div>
  );
}

export default function ManufacturingInspection() {
  const [data, setData] = useState(null);
  const [active, setActive] = useState(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => { api.get("/inspection/summary").then((r) => setData(r.data)).catch(() => {}); }, []);

  if (!data) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  const rows = data.products.filter((p) => filter === "all" || (filter === "paused" ? p.gate_status === "Paused" : p.gate_status === "Cleared"));

  return (
    <div>
      <PageHeader
        overline="QRU Manufacturing Inspection System™ · Treasure Standard™"
        title="Manufacturing Quality Gates"
        description="Every product is inspected against objective quality gates before it can manufacture or publish. If a Treasure Standard™ requirement isn't met, manufacturing pauses and the Director report explains exactly what's missing."
      />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <MetricCard testid="insp-stat-inspected" icon={Gauge} label="Products Inspected" value={data.total} />
        <MetricCard testid="insp-stat-cleared" icon={CheckCircle2} accent="gold" label="Cleared to Manufacture" value={data.cleared} />
        <MetricCard testid="insp-stat-paused" icon={PauseCircle} label="Paused (gates failed)" value={data.paused} />
        <MetricCard testid="insp-stat-connectors" icon={ShieldCheck} label="Operational Connectors" value={data.operational_connectors} />
      </div>

      <div className="flex gap-2 mb-3" data-testid="inspection-filters">
        {["all", "paused", "cleared"].map((f) => (
          <button key={f} onClick={() => setFilter(f)} data-testid={`filter-${f}`}
            className={`text-xs px-3.5 py-1.5 rounded-full border capitalize font-semibold transition-colors ${filter === f ? "bg-navy text-white border-navy" : "text-navy border-navy/25 hover:border-navy"}`}>{f}</button>
        ))}
      </div>

      <Panel testid="inspection-table" className="overflow-hidden">
        <div className="overflow-x-auto -m-5">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr>
                {["Product", "Code", "Status", "Score", "Gate", "Blocking failures"].map((h) => (
                  <th key={h} className="text-left font-bold text-navy px-5 py-2.5 whitespace-nowrap text-[11px] uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id} className="border-t border-border hover:bg-muted/30 cursor-pointer transition-colors" onClick={() => setActive(p.id)} data-testid={`inspection-row-${p.product_code}`}>
                  <td className="px-5 py-2.5 text-navy font-medium max-w-[240px] truncate">{p.title}</td>
                  <td className="px-5 py-2.5 text-muted-foreground text-xs">{p.product_code}</td>
                  <td className="px-5 py-2.5 text-xs text-muted-foreground">{p.status}</td>
                  <td className={`px-5 py-2.5 font-bold text-xs ${scoreColor(p.overall_score)}`}>{p.overall_score}</td>
                  <td className="px-5 py-2.5"><StatusChip status={p.gate_status} /></td>
                  <td className="px-5 py-2.5 text-[11px] text-muted-foreground max-w-[280px] truncate">{p.blocking_failures.join(", ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {active && <GateDetail productId={active} onClose={() => setActive(null)} />}
    </div>
  );
}
