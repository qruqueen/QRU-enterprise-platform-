import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import {
  Factory, Power, PlayCircle, Loader2, AlertTriangle, CheckCircle2, ArrowRight,
  Clock, ShieldCheck, Gauge, TrendingUp, Inbox,
} from "lucide-react";

const HEALTH_STYLE = {
  ready: "bg-emerald-50 text-emerald-700 border-emerald-200",
  needs_metadata: "bg-amber-50 text-amber-700 border-amber-200",
  needs_assets: "bg-orange-50 text-orange-700 border-orange-200",
  needs_knowledge: "bg-blue-50 text-blue-700 border-blue-200",
  blocked: "bg-red-50 text-red-700 border-red-200",
};

function Metric({ label, value, suffix, testid, tone }) {
  return (
    <div className="bg-card border rounded-lg p-3" data-testid={testid}>
      <p className="text-[11px] text-muted-foreground leading-tight">{label}</p>
      <p className={`font-heading text-2xl font-bold ${tone || "text-navy"}`}>{value}{suffix}</p>
    </div>
  );
}

export default function AutonomyEngineDashboard() {
  const [ov, setOv] = useState(null);
  const [busy, setBusy] = useState(false);
  const [advancing, setAdvancing] = useState("");

  const load = () => api.get("/autonomy-engine/overview").then((r) => setOv(r.data)).catch(() => {});
  useEffect(() => { load(); const t = setInterval(load, 20000); return () => clearInterval(t); }, []);

  const toggle = async () => {
    if (!ov) return;
    setBusy(true);
    try {
      const { data } = await api.put("/autonomy-engine/settings", { enabled: !ov.settings.enabled });
      toast.success(`Autonomy ${data.enabled ? "ON — the factory will self-coordinate" : "OFF — manual control"}`);
      load();
    } catch (e) { toast.error("Could not update autonomy switch"); }
    finally { setBusy(false); }
  };

  const runCycle = async () => {
    setBusy(true);
    try {
      await api.post("/autonomy-engine/run-cycle");
      toast.success("Autonomous cycle started — advancing top products in the background.");
      setTimeout(load, 4000);
    } catch (e) { toast.error("Could not start cycle"); }
    finally { setBusy(false); }
  };

  const advance = async (pid) => {
    setAdvancing(pid);
    try {
      const { data } = await api.post(`/autonomy-engine/advance/${pid}`);
      toast.success(data.message);
      load();
    } catch (e) { toast.error("Advance failed"); }
    finally { setAdvancing(""); }
  };

  if (!ov) return (
    <div className="bg-card border rounded-sm p-5 flex items-center gap-2 text-sm text-muted-foreground" data-testid="engine-loading">
      <Loader2 className="w-4 h-4 animate-spin" /> Loading Autonomous Manufacturing Engine™…
    </div>
  );

  const m = ov.metrics;
  const on = ov.settings.enabled;

  return (
    <div className="space-y-4" data-testid="autonomy-engine-dashboard">
      {/* Header + master switch */}
      <div className="rounded-sm p-5 text-white" style={{ background: "hsl(var(--royal))" }}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="font-heading text-xl font-bold flex items-center gap-2">
              <Factory className="w-6 h-6 text-gold" /> Autonomous Manufacturing Engine™
            </h2>
            <p className="text-sm text-white/70 mt-1 max-w-xl">
              The factory continuously determines the next safe action and advances products —
              deterministic ($0 AI), governed, and always leaving publication to you.
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button data-testid="engine-run-cycle" onClick={runCycle} disabled={busy}
              className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 text-white px-3 py-2 rounded-sm text-sm font-medium disabled:opacity-60">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlayCircle className="w-4 h-4" />} Run Cycle Now
            </button>
            <button data-testid="engine-toggle" onClick={toggle} disabled={busy}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-sm text-sm font-semibold transition-colors ${on ? "bg-gold text-navy" : "bg-white/15 text-white hover:bg-white/25"}`}>
              <Power className="w-4 h-4" /> Autonomy {on ? "ON" : "OFF"}
            </button>
          </div>
        </div>
        <div className="mt-4 flex items-start gap-2 bg-white/10 rounded-sm p-3" data-testid="engine-next-action">
          <ArrowRight className="w-4 h-4 text-gold mt-0.5 shrink-0" />
          <div>
            <p className="text-[11px] uppercase tracking-wide text-gold font-semibold">Next Recommended Action™</p>
            <p className="text-sm">{ov.next_recommended_action}</p>
          </div>
        </div>
      </div>

      {/* Executive metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3" data-testid="engine-metrics">
        <Metric testid="metric-queue" label="Currently Manufacturing" value={m.manufacturing_queue} />
        <Metric testid="metric-waiting" label="Waiting for Founder" value={m.founder_decisions_waiting} tone="text-gold" />
        <Metric testid="metric-blocked" label="Blocked (needs you)" value={m.blocked_items} tone={m.blocked_items ? "text-red-600" : "text-navy"} />
        <Metric testid="metric-today" label="Manufactured Today" value={m.products_today} />
        <Metric testid="metric-published" label="Published Today" value={m.published_today} />
        <Metric testid="metric-hours" label="Founder Hours Saved" value={m.founder_hours_saved} suffix="h" tone="text-emerald-600" />
        <Metric testid="metric-automation" label="Automation Rate" value={m.automation_rate} suffix="%" />
        <Metric testid="metric-tspass" label="Treasure Standard™ Pass" value={m.treasure_pass_rate} suffix="%" />
        <Metric testid="metric-confidence" label="Avg Factory Confidence™" value={m.avg_factory_confidence} suffix="%" />
        <Metric testid="metric-published-total" label="Published Catalog" value={m.published} />
        <Metric testid="metric-deliverables" label="Deliverables Ready" value={m.deliverables_ready} />
        <Metric testid="metric-health" label="System Health" value={m.system_health === "healthy" ? "Healthy" : "Attention"}
          tone={m.system_health === "healthy" ? "text-emerald-600" : "text-amber-600"} />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* Manufacturing queue */}
        <div className="bg-card border rounded-sm p-4" data-testid="engine-queue">
          <p className="font-heading font-semibold text-navy flex items-center gap-2 mb-3">
            <Gauge className="w-4 h-4 text-gold" /> Manufacturing Queue™ <span className="text-xs text-muted-foreground">(deterministic, auto-advancing)</span>
          </p>
          {ov.manufacturing_queue.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing to advance — queue is clear.</p>
          ) : (
            <div className="space-y-1.5 max-h-80 overflow-y-auto">
              {ov.manufacturing_queue.map((r) => (
                <div key={r.id} className="flex items-center gap-2 text-xs border rounded-sm px-2 py-1.5" data-testid={`queue-row-${r.product_code}`}>
                  <span className={`px-1.5 py-0.5 rounded-full border text-[10px] ${HEALTH_STYLE[r.data_health]}`}>{r.data_health_label}</span>
                  <span className="text-navy truncate flex-1">{r.title}</span>
                  <span className="text-muted-foreground shrink-0">{r.factory_confidence}%</span>
                  <span className="text-muted-foreground shrink-0 hidden sm:inline">{r.next_action.label}</span>
                  <button data-testid={`queue-advance-${r.product_code}`} onClick={() => advance(r.id)} disabled={advancing === r.id}
                    className="flex items-center gap-1 bg-navy text-white px-2 py-1 rounded-sm shrink-0 disabled:opacity-60">
                    {advancing === r.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <ArrowRight className="w-3 h-3" />} Advance
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Waiting for Founder + Blocked */}
        <div className="space-y-4">
          <div className="bg-card border rounded-sm p-4" data-testid="engine-awaiting">
            <p className="font-heading font-semibold text-navy flex items-center gap-2 mb-3">
              <Inbox className="w-4 h-4 text-gold" /> Waiting for Founder Decision
            </p>
            {ov.awaiting_founder.length === 0 ? (
              <p className="text-sm text-muted-foreground">No products awaiting your decision.</p>
            ) : (
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {ov.awaiting_founder.map((r) => (
                  <div key={r.id} className="flex items-center gap-2 text-xs" data-testid={`awaiting-row-${r.product_code}`}>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span className="text-navy truncate flex-1">{r.title}</span>
                    <span className="text-muted-foreground">{r.factory_confidence}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="bg-card border rounded-sm p-4" data-testid="engine-blocked">
            <p className="font-heading font-semibold text-navy flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-red-500" /> Blocked — Needs Your Input
            </p>
            {ov.blocked.length === 0 ? (
              <p className="text-sm text-muted-foreground">Nothing blocked. The factory is running clear.</p>
            ) : (
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {ov.blocked.map((r) => (
                  <div key={r.id} className="flex items-center gap-2 text-xs" data-testid={`blocked-row-${r.product_code}`}>
                    <span className="text-red-600 truncate flex-1">{r.title}</span>
                    <span className="text-muted-foreground truncate max-w-[50%]">{r.next_action.reason}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Factory Learning™ (MO-039 — the factory improves every day) */}
      {ov.factory_learning && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="engine-learning">
          <Metric testid="learn-recovery" label="Auto-Recovery Rate" value={ov.factory_learning.auto_recovery_rate} suffix="%" tone="text-emerald-600" />
          <Metric testid="learn-interruptions" label="Founder Interruptions Prevented" value={ov.factory_learning.founder_interruptions_prevented} />
          <Metric testid="learn-failures" label="Failures Learned From" value={ov.factory_learning.failures_seen} />
          <Metric testid="learn-recovered" label="Auto-Recovered" value={ov.factory_learning.auto_recovered} tone="text-emerald-600" />
        </div>
      )}

      {/* Recent autonomous actions (Founder Translation Layer™ — plain language) */}
      {ov.recent_actions.length > 0 && (
        <div className="bg-card border rounded-sm p-4" data-testid="engine-recent">
          <p className="font-heading font-semibold text-navy flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-gold" /> Recent Autonomous Work
          </p>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {ov.recent_actions.map((a, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <Clock className="w-3 h-3 text-muted-foreground mt-0.5 shrink-0" />
                <span className="text-muted-foreground">{a.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
