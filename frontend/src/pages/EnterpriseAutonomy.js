import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { Cpu, Loader2, RefreshCw, PlayCircle, Stethoscope, Network, ListChecks, CheckCircle2, AlertTriangle, ClipboardCheck } from "lucide-react";

const TABS = [
  { key: "continuous", label: "Continuous Improvement™", icon: RefreshCw },
  { key: "diagnostics", label: "Enterprise Diagnostics™", icon: Stethoscope },
  { key: "relationships", label: "Relationship Engine™", icon: Network },
  { key: "checklist", label: "Enterprise-First Thinking™", icon: ListChecks },
];

export default function EnterpriseAutonomy() {
  const [tab, setTab] = useState("continuous");
  const [data, setData] = useState(null);
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = () => api.get("/continuous/overview").then(({ data }) => setData(data)).catch(() => {}).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);
  useEffect(() => { if (tab === "relationships" && !graph) api.get("/relationships/graph").then(({ data }) => setGraph(data)).catch(() => {}); }, [tab]);

  const probe = async () => {
    setBusy(true);
    try { const { data } = await api.post("/continuous/probe"); toast[data.available ? "success" : "message"](data.available ? "AI capacity available" : data.reason); load(); }
    finally { setBusy(false); }
  };
  const autoResume = async () => {
    setBusy(true);
    try { const { data } = await api.post("/continuous/auto-resume"); toast.success(`Auto-resume: ${data.resumed?.length || 0} job(s) actioned`); load(); }
    finally { setBusy(false); }
  };

  if (loading) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading Enterprise Autonomy…</div>;

  const cap = data?.capacity || {};

  return (
    <div className="space-y-6" data-testid="enterprise-autonomy-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <Cpu className="w-7 h-7 text-gold" /> QRU Enterprise Autonomy & Continuous Improvement™
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          Every manufacturing order should leave the factory better than before. <span className="font-semibold text-navy">Build the factory once. Improve it forever.</span>
        </p>
      </div>

      {/* Capacity banner */}
      <div data-testid="capacity-banner" className={`rounded-md border p-4 flex flex-wrap items-center gap-3 ${cap.available ? "border-emerald-300 bg-emerald-50" : "border-amber-300 bg-amber-50"}`}>
        {cap.available ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : <AlertTriangle className="w-5 h-5 text-amber-600" />}
        <div className="flex-1 min-w-[200px]">
          <p className="font-semibold text-navy text-sm">AI Capacity: {cap.available ? "Available" : "Unavailable"}</p>
          <p className="text-xs text-foreground/70">{cap.reason} {cap.checked_at ? `· checked ${new Date(cap.checked_at).toLocaleTimeString()}` : "· not yet probed"}</p>
        </div>
        <button data-testid="probe-btn" onClick={probe} disabled={busy} className="text-xs px-3 py-1.5 rounded-sm border border-border hover:border-primary flex items-center gap-1.5 disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${busy ? "animate-spin" : ""}`} /> Probe capacity
        </button>
        <button data-testid="auto-resume-btn" onClick={autoResume} disabled={busy} className="text-xs px-3 py-1.5 rounded-sm bg-navy text-white hover:bg-navy/90 flex items-center gap-1.5 disabled:opacity-50">
          <PlayCircle className="w-3.5 h-3.5" /> Auto-resume safe jobs
        </button>
      </div>

      <div className="flex flex-wrap gap-2 border-b border-border">
        {TABS.map((t) => (
          <button key={t.key} data-testid={`ea-tab-${t.key}`} onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm border-b-2 -mb-px transition-colors ${tab === t.key ? "border-gold text-navy font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"}`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === "continuous" && (
        <div className="grid lg:grid-cols-2 gap-6" data-testid="continuous-tab">
          <div>
            <p className="overline text-primary mb-2 flex items-center gap-2"><PlayCircle className="w-4 h-4" /> Auto-Resume™ Activity</p>
            <p className="text-xs text-muted-foreground mb-3">{data.watcher.policy} (checks every {data.watcher.interval_seconds}s)</p>
            <div className="space-y-2">
              {data.auto_resume_actions?.length ? data.auto_resume_actions.map((a, i) => (
                <div key={i} className="rounded-md border border-border bg-card p-3 text-sm">
                  <span className="font-medium text-navy">{a.kind}</span> — {a.detail}
                  <p className="text-[10px] text-muted-foreground mt-0.5">{new Date(a.at).toLocaleString()}</p>
                </div>
              )) : <p className="text-sm text-muted-foreground">No auto-resume actions yet. When AI capacity returns, paused/failed jobs finish automatically.</p>}
            </div>
          </div>
          <div>
            <p className="overline text-primary mb-2 flex items-center gap-2"><ClipboardCheck className="w-4 h-4" /> After-Action Reviews™</p>
            <div className="space-y-2">
              {data.after_action_reviews?.length ? data.after_action_reviews.map((r) => (
                <div key={r.id} className="rounded-md border border-border bg-card p-3 text-sm">
                  <p className="font-medium text-navy">{r.batch_name} <span className="text-[10px] font-mono text-muted-foreground">{r.id}</span></p>
                  <p className="text-xs text-foreground/70 mt-0.5">{r.done}/{r.total} done · {r.failed} failed · {r.escalated} escalated</p>
                  <p className="text-xs text-foreground/60 mt-1">{r.findings?.reusable_recipe}</p>
                </div>
              )) : <p className="text-sm text-muted-foreground">No completed batches to review yet.</p>}
            </div>
          </div>
        </div>
      )}

      {tab === "diagnostics" && (
        <div data-testid="diagnostics-tab">
          <p className="text-sm text-muted-foreground mb-3">{data.diagnostics_count} failed job(s). Every failure includes a root cause, recovery recommendation, retry status, dependency status, estimated resolution, and confidence.</p>
          {data.diagnostics?.length ? (
            <div className="overflow-x-auto rounded-md border border-border">
              <table className="w-full text-sm">
                <thead><tr className="bg-muted/50 text-left text-xs text-muted-foreground">
                  <th className="px-3 py-2">Job</th><th className="px-3 py-2">Item</th><th className="px-3 py-2">Root Cause</th>
                  <th className="px-3 py-2">Recovery</th><th className="px-3 py-2">Retry</th><th className="px-3 py-2">Dependency</th>
                  <th className="px-3 py-2">ETA</th><th className="px-3 py-2">Conf.</th>
                </tr></thead>
                <tbody>
                  {data.diagnostics.map((d, i) => (
                    <tr key={i} className="border-t border-border" data-testid={`diag-row-${i}`}>
                      <td className="px-3 py-2 font-mono text-xs">{d.job}</td>
                      <td className="px-3 py-2">{d.item}</td>
                      <td className="px-3 py-2 text-foreground/80">{d.root_cause}</td>
                      <td className="px-3 py-2 text-foreground/70">{d.recovery_recommendation}</td>
                      <td className="px-3 py-2"><span className="text-[11px] rounded-full px-1.5 py-0.5 bg-navy/5">{d.retry_status}</span></td>
                      <td className="px-3 py-2 text-xs">{d.dependency_status}</td>
                      <td className="px-3 py-2 text-xs">{d.estimated_resolution}</td>
                      <td className="px-3 py-2">{Math.round(d.confidence * 100)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 flex items-center gap-2"><CheckCircle2 className="w-4 h-4" /> No failed jobs. The factory is healthy.</div>}
        </div>
      )}

      {tab === "relationships" && (
        <div data-testid="relationships-tab">
          {graph ? (
            <>
              <p className="text-sm text-muted-foreground mb-3">{graph.object_types} enterprise object types · {graph.relationship_types} relationship connections. Every object understands what it is connected to.</p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {graph.nodes.map((n) => (
                  <div key={n.type} className="rounded-md border border-border bg-card p-3">
                    <div className="flex items-center justify-between">
                      <p className="font-semibold text-navy text-sm">{n.type}</p>
                      <span className="text-lg font-heading font-bold text-gold">{n.count}</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {n.connects_to.map((c) => <span key={c} className="text-[10px] bg-muted px-1.5 py-0.5 rounded-sm text-foreground/70">{c}</span>)}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading graph…</div>}
        </div>
      )}

      {tab === "checklist" && (
        <div data-testid="checklist-tab">
          <p className="text-sm text-muted-foreground mb-3">Every component asks these questions before completing work. No component operates in isolation.</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {data.enterprise_first_checklist.map((q, i) => (
              <div key={i} className="rounded-md border border-border bg-card p-3 flex items-start gap-2">
                <span className="w-5 h-5 rounded-full bg-gold text-navy text-xs font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                <p className="text-sm text-foreground/80">{q}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
