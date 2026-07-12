import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import {
  Loader2, GitBranch, LayoutDashboard, Boxes, ShieldCheck, ArrowRight, CircleDot, CheckCircle2,
  Ban, Clock, Activity, Building2, Map,
} from "lucide-react";

const HEALTH_TONE = { "On Track": "emerald", "Awaiting Approval": "amber", Blocked: "rose", Complete: "emerald" };
const STATE_TONE = { Blocked: "rose", "Attention needed": "amber", Healthy: "emerald" };

export default function ManufacturingFlow() {
  const [tab, setTab] = useState("dashboard");
  const [lifecycle, setLifecycle] = useState(null);
  const [dash, setDash] = useState(null);
  const [modules, setModules] = useState([]);
  const [registry, setRegistry] = useState([]);

  useEffect(() => {
    api.get("/flow/lifecycle").then((r) => setLifecycle(r.data)).catch(() => {});
    api.get("/flow/dashboard").then((r) => setDash(r.data)).catch(() => {});
    api.get("/flow/modules").then((r) => setModules(r.data.modules)).catch(() => {});
    api.get("/flow/registry").then((r) => setRegistry(r.data.registry)).catch(() => {});
  }, []);

  const TABS = [
    { id: "dashboard", label: "Enterprise Dashboard", icon: LayoutDashboard },
    { id: "lifecycle", label: "Production Lifecycle", icon: GitBranch },
    { id: "modules", label: "Module Registry", icon: Boxes },
    { id: "registry", label: "Constitutional Registry", icon: ShieldCheck },
  ];

  return (
    <div data-testid="flow-page">
      <PageHeader
        overline="STD-MFG-0001 · Knowledge Manufacturing Execution System™"
        title="Manufacturing Flow™"
        description="One continuous, governed, auditable production lifecycle. The Factory always knows where every project came from, where it is, and what happens next — nothing exists outside the flow."
        actions={<VerifiedBadge label="No orphaned products · Human authorizes" testid="flow-badge" />}
      />
      <GovernedBy standards={["STD-MFG-0001", "QRU-CON-0001", "QRU-CON-0002"]} className="mb-4" testid="flow-governed-by" />

      <div className="flex flex-wrap gap-1.5 mb-5" data-testid="flow-tabs">
        {TABS.map((t) => {
          const Ic = t.icon;
          return (
            <button key={t.id} data-testid={`flow-tab-${t.id}`} onClick={() => setTab(t.id)}
              className={`text-[12px] inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-colors ${tab === t.id ? "bg-navy text-white" : "bg-white border border-navy/15 text-navy hover:border-royal"}`}>
              <Ic className="w-3.5 h-3.5" /> {t.label}
            </button>
          );
        })}
      </div>

      {/* ENTERPRISE DASHBOARD */}
      {tab === "dashboard" && (
        !dash ? <Loading /> : (
          <div data-testid="flow-dashboard">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-5">
              {[["Projects", dash.totals.projects], ["Gold Masters", dash.totals.gold_masters], ["Released", dash.totals.released],
                ["Blocked", dash.totals.blocked], ["Awaiting Approval", dash.totals.awaiting_approval], ["Publish Queue", dash.totals.publishing_queue]].map(([k, v]) => (
                <div key={k} className="border rounded-md p-3 border-navy/10 bg-white" data-testid={`flow-stat-${k.replace(/\s/g, "-").toLowerCase()}`}>
                  <p className="text-2xl font-black text-navy tabular-nums">{v}</p>
                  <p className="text-[9px] uppercase tracking-wide text-muted-foreground">{k}</p>
                </div>
              ))}
            </div>
            <Panel title="Factory Health" icon={Activity} accent="gold" testid="flow-health" className="mb-5">
              <div className="flex items-center gap-3">
                <div className="flex-1 h-3 rounded-full bg-navy/10 overflow-hidden">
                  <div className={`h-full rounded-full ${dash.factory_health.score >= 60 ? "bg-emerald-500" : "bg-amber-500"}`} style={{ width: `${dash.factory_health.score}%`, transition: "width 800ms ease-out" }} />
                </div>
                <span className="text-lg font-black text-navy tabular-nums">{dash.factory_health.score}</span>
                <StatusChip status={dash.factory_health.label} tone={STATE_TONE[dash.factory_health.label] || "slate"} />
              </div>
            </Panel>
            <Panel title="Production Cards™" icon={LayoutDashboard} accent="royal" testid="flow-cards">
              <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-3">
                {dash.cards.map((c) => (
                  <div key={c.project_id} className="border rounded-md p-3 border-navy/10" data-testid={`flow-card-${c.project_id}`}>
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <p className="text-[12px] font-bold text-navy leading-tight">{c.name}</p>
                      <StatusChip status={c.production_state} tone={c.production_state === "Released" ? "emerald" : "blue"} />
                    </div>
                    <div className="h-1.5 rounded-full bg-navy/10 overflow-hidden my-2">
                      <div className="h-full bg-royal rounded-full" style={{ width: `${c.progress}%` }} />
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                      <span>{c.current_stage}</span>
                      <span className={c.risk_level === "High" ? "text-red-600" : c.risk_level === "Medium" ? "text-amber-600" : "text-emerald-600"}>Risk: {c.risk_level}</span>
                    </div>
                    <p className="text-[10px] text-navy/70 mt-1.5 flex items-start gap-1"><ArrowRight className="w-3 h-3 mt-0.5 shrink-0 text-royal" />{c.next_action}</p>
                    {c.treasure_status === "Gold Master Certified™" && <p className="text-[10px] text-gold font-bold mt-1">★ {c.treasure_status}</p>}
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        )
      )}

      {/* LIFECYCLE */}
      {tab === "lifecycle" && (
        !lifecycle ? <Loading /> : (
          <Panel title="Universal Production Lifecycle (18 stages)" icon={GitBranch} accent="royal" testid="flow-lifecycle">
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {lifecycle.lifecycle.map((s) => (
                <div key={s.id} className="flex items-center gap-2 border rounded-md p-2.5 border-navy/10" data-testid={`flow-stage-${s.id}`}>
                  <span className="w-6 h-6 rounded-full bg-navy text-white grid place-items-center text-[10px] font-bold shrink-0">{s.n}</span>
                  <div className="min-w-0">
                    <p className="text-[12px] font-bold text-navy truncate">{s.name}</p>
                    <p className="text-[9px] text-muted-foreground">{s.department}{s.gate ? " · Quality Gate" : ""}{s.approval ? " · Human Approval" : ""}{s.conditional ? " · Conditional" : ""}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {lifecycle.production_states.map((st) => <span key={st} className="text-[10px] px-2 py-0.5 rounded-full bg-navy/[0.05] text-navy border border-navy/10">{st}</span>)}
            </div>
          </Panel>
        )
      )}

      {/* MODULES */}
      {tab === "modules" && (
        <Panel title="Module Responsibility Registry" icon={Boxes} accent="gold" testid="flow-modules">
          <div className="space-y-2">
            {modules.map((m) => (
              <div key={m.id} className="border rounded-md p-3 border-navy/10" data-testid={`flow-module-${m.id}`}>
                <p className="text-[12px] font-bold text-navy">{m.name}</p>
                <p className="text-[11px] text-muted-foreground">{m.purpose}</p>
                <div className="grid sm:grid-cols-2 gap-x-4 gap-y-0.5 mt-1.5 text-[10px] text-navy/80">
                  <span><b>Inputs:</b> {m.inputs.join(", ")}</span>
                  <span><b>Outputs:</b> {m.outputs.join(", ")}</span>
                  <span><b>Standards:</b> {m.standards.join(", ")}</span>
                  <span><b>Departments:</b> {m.departments.join(", ")}</span>
                  <span><b>Quality gates:</b> {m.quality_gates.join(", ")}</span>
                  <span><b>Next stage:</b> {m.next_stage}</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* REGISTRY */}
      {tab === "registry" && (
        <Panel title="Constitutional Registry (permanent · never overwritten)" icon={ShieldCheck} accent="royal" testid="flow-registry">
          <div className="space-y-2">
            {registry.map((r) => (
              <div key={r.id} className="flex items-center justify-between border rounded-md p-3 border-navy/10" data-testid={`flow-registry-${r.id}`}>
                <div>
                  <p className="text-[12px] font-bold text-navy">{r.id} <span className="text-muted-foreground font-normal">v{r.version}</span></p>
                  <p className="text-[11px] text-navy/80">{r.name}</p>
                  <p className="text-[10px] text-muted-foreground">{r.category} · Owner {r.owner}</p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <StatusChip status={r.implementation_status} tone="emerald" />
                  <span className="text-[9px] text-emerald-700 inline-flex items-center gap-1"><CheckCircle2 className="w-3 h-3" />{r.verification_status}</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

const Loading = () => <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
