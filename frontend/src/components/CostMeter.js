import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { Gauge, AlertTriangle, DollarSign, Settings2, ShieldAlert } from "lucide-react";

function Bar({ pct }) {
  const color = pct >= 100 ? "bg-red-500" : pct >= 90 ? "bg-orange-500" : pct >= 75 ? "bg-amber-500" : pct >= 50 ? "bg-yellow-400" : "bg-emerald-500";
  return (
    <div className="w-full h-2.5 rounded-full bg-muted overflow-hidden">
      <div className={`h-full ${color} transition-all`} style={{ width: `${Math.min(100, pct)}%` }} />
    </div>
  );
}

export function CostMeter() {
  const [d, setD] = useState(null);
  const [budget, setBudget] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => api.get("/cost-meter/overview").then(({ data }) => { setD(data); setBudget(String(data.budget.daily_budget_usd)); }).catch(() => {});
  useEffect(() => { load(); }, []);

  const saveBudget = async () => {
    setSaving(true);
    try { await api.post("/cost-meter/budget", { daily_budget_usd: parseFloat(budget) }); toast.success("Daily AI budget updated"); load(); }
    finally { setSaving(false); }
  };
  const toggleOverride = async () => {
    const next = !d.budget.override_100;
    await api.post("/cost-meter/budget", { override_100: next });
    toast[next ? "warning" : "success"](next ? "Founder override ACTIVE — AI manufacturing continues past 100%" : "Override removed");
    load();
  };

  if (!d) return null;
  const b = d.budget;

  return (
    <div className="bg-card border rounded-md p-5" data-testid="cost-meter">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Gauge className="w-5 h-5 text-gold" />
          <h3 className="font-heading font-semibold">AI Usage & Cost Meter™</h3>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-navy/5 text-navy">Estimated</span>
        </div>
        <span className="text-xs text-muted-foreground">Protects cash flow during First Dollar Mode™</span>
      </div>

      {/* Daily budget gauge */}
      <div className="mt-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-muted-foreground">Today: <span className="font-semibold text-navy">${b.spent_today}</span> of ${b.daily_budget_usd}</span>
          <span className={`font-semibold ${b.percent_used >= 90 ? "text-red-600" : "text-navy"}`}>{b.percent_used}%</span>
        </div>
        <Bar pct={b.percent_used} />
        <p className="text-xs text-muted-foreground mt-1">Remaining today (est.): ${b.remaining_today}</p>
      </div>

      {/* Warning */}
      {d.warnings.active_level > 0 && (
        <div data-testid="cost-warning" className={`mt-3 rounded-sm p-3 text-sm flex items-start gap-2 ${d.warnings.active_level >= 100 ? "bg-red-50 text-red-700 border border-red-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`}>
          {d.warnings.active_level >= 100 ? <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" /> : <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />}
          <span>{d.warnings.message}</span>
        </div>
      )}

      {/* Usage windows */}
      <div className="grid grid-cols-3 gap-3 mt-4">
        <div className="rounded-sm bg-muted/40 p-3"><p className="text-lg font-heading font-bold text-navy">${d.daily.total}</p><p className="text-[11px] text-muted-foreground">Today (est.)</p></div>
        <div className="rounded-sm bg-muted/40 p-3"><p className="text-lg font-heading font-bold text-navy">${d.weekly_total}</p><p className="text-[11px] text-muted-foreground">Last 7 days (est.)</p></div>
        <div className="rounded-sm bg-muted/40 p-3"><p className="text-lg font-heading font-bold text-navy">${d.monthly_total}</p><p className="text-[11px] text-muted-foreground">Last 30 days (est.)</p></div>
      </div>

      {/* By service */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3">
        {Object.entries(d.daily.by_service).map(([k, v]) => (
          <div key={k} className="rounded-sm border border-border p-2 text-center">
            <p className="text-sm font-semibold text-navy">${v.est_cost}</p>
            <p className="text-[10px] text-muted-foreground">{k}</p>
            <p className="text-[10px] text-muted-foreground">{v.calls} calls</p>
          </div>
        ))}
      </div>

      {/* Provider limits */}
      <div className="mt-4 rounded-sm bg-navy/5 p-3 text-xs text-foreground/75">
        <p><span className="font-semibold text-navy">Provider:</span> {d.provider_limits.provider}</p>
        <p><span className="font-semibold text-navy">OpenAI daily cap:</span> {d.provider_limits.openai_daily_cap}</p>
        <p><span className="font-semibold text-navy">Universal Key balance:</span> {d.provider_limits.universal_key_balance}</p>
      </div>

      {/* Per product */}
      {d.per_product?.length > 0 && (
        <div className="mt-4">
          <p className="overline text-primary mb-2 flex items-center gap-1"><DollarSign className="w-3.5 h-3.5" /> Estimated cost per product</p>
          <div className="space-y-1">
            {d.per_product.slice(0, 5).map((p) => (
              <div key={p.product_id} className="flex justify-between text-xs border-b border-border/60 py-1">
                <span className="font-mono text-muted-foreground truncate max-w-[70%]">{p.product_id}</span>
                <span className="font-semibold text-navy">${p.est_cost}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="mt-4 pt-4 border-t flex flex-wrap items-end gap-3">
        <div>
          <label className="text-xs text-muted-foreground flex items-center gap-1"><Settings2 className="w-3 h-3" /> Daily soft budget (USD)</label>
          <input data-testid="budget-input" type="number" value={budget} onChange={(e) => setBudget(e.target.value)}
            className="mt-1 w-32 px-2 py-1.5 rounded-sm border text-sm outline-none focus:border-primary" />
        </div>
        <button data-testid="budget-save" onClick={saveBudget} disabled={saving}
          className="text-sm px-3 py-1.5 rounded-sm bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-60">Save budget</button>
        <button data-testid="override-toggle" onClick={toggleOverride}
          className={`text-sm px-3 py-1.5 rounded-sm border ${b.override_100 ? "bg-red-50 text-red-700 border-red-200" : "border-border hover:border-navy"}`}>
          {b.override_100 ? "Override ON (past 100%)" : "Founder override at 100%"}
        </button>
      </div>
      <p className="text-[10px] text-muted-foreground mt-2">{d.note} Deterministic fallback workflows are never blocked.</p>
    </div>
  );
}
