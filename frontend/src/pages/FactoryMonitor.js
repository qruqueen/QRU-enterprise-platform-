import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import {
  Activity, Cpu, DollarSign, Gauge, PackageCheck, Radio, ShieldCheck, TrendingUp,
  Truck, Users, AlertTriangle, Loader2,
} from "lucide-react";

const HEALTH_COLOR = { healthy: "text-emerald-600", attention: "text-amber-600" };

function Stat({ icon: Icon, label, value, sub, testid }) {
  return (
    <div data-testid={testid} className="bg-card border rounded-sm p-4">
      <div className="flex items-center gap-2 text-muted-foreground mb-1">
        <Icon className="w-4 h-4 text-gold" />
        <span className="text-xs uppercase tracking-wide">{label}</span>
      </div>
      <p className="font-heading text-2xl font-bold text-navy">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  );
}

const STATUS_BADGE = {
  running: "bg-blue-100 text-blue-700", queued: "bg-slate-100 text-slate-600",
  completed: "bg-emerald-100 text-emerald-700", completed_with_errors: "bg-amber-100 text-amber-700",
  escalated: "bg-purple-100 text-purple-700", failed: "bg-red-100 text-red-700",
};

export default function FactoryMonitor() {
  const [m, setM] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get("/workflow/monitor");
        setM(data);
      } catch (_) {}
    };
    load();
    const iv = setInterval(load, 6000);
    return () => clearInterval(iv);
  }, []);

  if (!m)
    return (
      <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading Executive Factory Monitor™…
      </div>
    );

  return (
    <div className="space-y-6" data-testid="factory-monitor-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
            <Radio className="w-7 h-7 text-gold" /> Executive Factory Monitor™
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            The control room of the QRU Knowledge Manufacturing System™ — live.
          </p>
        </div>
        <div className={`flex items-center gap-2 text-sm font-semibold ${HEALTH_COLOR[m.health.factory_health] || ""}`} data-testid="factory-health-badge">
          <Activity className="w-4 h-4" /> Factory Health: {m.health.factory_health.toUpperCase()}
        </div>
      </div>

      {/* Job queue */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat icon={Loader2} label="Jobs Running" value={m.jobs.running} testid="stat-jobs-running" />
        <Stat icon={Gauge} label="Jobs Waiting" value={m.jobs.waiting} testid="stat-jobs-waiting" />
        <Stat icon={PackageCheck} label="Jobs Completed" value={m.jobs.completed} testid="stat-jobs-completed" />
        <Stat icon={AlertTriangle} label="Escalated" value={m.jobs.escalated} testid="stat-jobs-escalated" />
      </div>

      {/* Enterprise metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat icon={DollarSign} label="Est. Production Cost" value={`$${m.estimated_production_cost_usd}`} sub={m.cost_label} testid="stat-cost" />
        <Stat icon={TrendingUp} label="Revenue" value={`$${m.revenue.revenue_usd}`} sub={`${m.revenue.paid_orders} paid · AOV $${m.revenue.aov_usd}`} testid="stat-revenue" />
        <Stat icon={Cpu} label="AI Service Jobs" value={m.ai_usage.jobs} sub={`${m.ai_usage.real} real · ${m.ai_usage.failed} failed`} testid="stat-ai" />
        <Stat icon={Truck} label="Distributions" value={m.distribution.total} sub={`${m.distribution.platforms_connected} platforms connected`} testid="stat-dist" />
      </div>

      {/* Health metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat icon={ShieldCheck} label="Treasure Compliance" value={`${m.health.treasure_compliance_pct}%`} testid="stat-treasure" />
        <Stat icon={Gauge} label="Automation Success" value={`${m.health.automation_success_pct}%`} testid="stat-automation" />
        <Stat icon={Users} label="Founder Intervention" value={`${m.health.founder_intervention_pct}%`} testid="stat-intervention" />
        <Stat icon={Activity} label="Knowledge Health" value={`${m.health.knowledge_health}%`} testid="stat-knowledge-health" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Job cards */}
        <div className="lg:col-span-2 bg-card border rounded-sm p-5" data-testid="recent-jobs-panel">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-heading font-semibold text-navy">Manufacturing Jobs</h2>
            <Link to="/workflows" className="text-xs text-primary hover:underline" data-testid="monitor-to-workflows">Open Workflow Engine →</Link>
          </div>
          {m.recent_jobs.length === 0 && <p className="text-sm text-muted-foreground">No jobs yet. Start one in the Workflow Engine™.</p>}
          <div className="space-y-2">
            {m.recent_jobs.map((j) => (
              <div key={j.id} data-testid={`job-row-${j.job_number}`} className="border rounded-sm p-3">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-navy truncate">
                      {j.job_number} · {j.template} {j.is_fat && <span className="text-gold">· FAT</span>}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">{j.topic}</p>
                  </div>
                  <span className={`text-[11px] px-2 py-0.5 rounded-full ${STATUS_BADGE[j.status] || "bg-slate-100"}`}>{j.status}</span>
                </div>
                <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-gold transition-all" style={{ width: `${j.progress}%` }} />
                </div>
                <div className="flex items-center justify-between mt-1.5 text-[11px] text-muted-foreground">
                  <span>{j.stage} · {j.current_task}</span>
                  <span>{j.manufactured}/{j.planned} · ${j.est_cost_usd}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Division activity */}
        <div className="bg-card border rounded-sm p-5" data-testid="division-activity-panel">
          <h2 className="font-heading font-semibold text-navy mb-3">Division Activity</h2>
          <div className="space-y-2 max-h-[420px] overflow-y-auto">
            {m.division_activity.map((a, i) => (
              <div key={i} className="text-xs border-l-2 border-gold/60 pl-2">
                <p className="text-navy font-medium">{a.actor}</p>
                <p className="text-muted-foreground">{a.action}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
