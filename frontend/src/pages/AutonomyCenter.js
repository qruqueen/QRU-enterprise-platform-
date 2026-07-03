import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import {
  Brain, Activity, Stethoscope, Wrench, Lightbulb, DollarSign, Gauge, Search,
  Users, Database, Loader2, CheckCircle2, AlertTriangle,
} from "lucide-react";

const SEV = { high: "text-red-600", medium: "text-amber-600", low: "text-slate-500", ok: "text-emerald-600" };

function Section({ icon: Icon, title, children, testid }) {
  return (
    <div className="bg-card border rounded-sm p-5" data-testid={testid}>
      <h2 className="font-heading font-semibold text-navy flex items-center gap-2 mb-3">
        <Icon className="w-5 h-5 text-gold" /> {title}
      </h2>
      {children}
    </div>
  );
}

export default function AutonomyCenter() {
  const [d, setD] = useState(null);
  const [health, setHealth] = useState(null);
  const [brief, setBrief] = useState(null);
  const [council, setCouncil] = useState(null);
  const [score, setScore] = useState(null);
  const [cap, setCap] = useState(null);
  const [gaps, setGaps] = useState(null);
  const [mem, setMem] = useState(null);
  const [repairing, setRepairing] = useState(false);

  const load = async () => {
    try {
      const [diag, h, b, c, s, cp, g, m] = await Promise.all([
        api.get("/autonomy/diagnostics"), api.get("/autonomy/health"),
        api.get("/autonomy/executive-brief"), api.get("/autonomy/factory-council"),
        api.get("/autonomy/ai-scorecard"), api.get("/autonomy/capacity"),
        api.get("/autonomy/knowledge-gaps"), api.get("/autonomy/enterprise-memory"),
      ]);
      setD(diag.data); setHealth(h.data); setBrief(b.data); setCouncil(c.data);
      setScore(s.data); setCap(cp.data); setGaps(g.data); setMem(m.data);
    } catch (_) {}
  };
  useEffect(() => { load(); }, []);

  const repair = async () => {
    setRepairing(true);
    try {
      const { data } = await api.post("/autonomy/diagnostics/repair");
      toast.success(`Auto-repaired ${data.repaired} item(s).`);
      load();
    } catch (e) { toast.error("Repair failed."); } finally { setRepairing(false); }
  };

  if (!d || !health || !brief) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading Autonomy Center™…</div>;

  return (
    <div className="space-y-6" data-testid="autonomy-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <Brain className="w-7 h-7 text-gold" /> QRU Autonomous Enterprise™
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          The factory that continuously improves, diagnoses, and repairs itself — Level 5 Autonomy.
        </p>
      </div>

      {/* Executive Brief */}
      <Section icon={Lightbulb} title="Executive Advisor™ — What to focus on today" testid="exec-brief">
        <div className="grid sm:grid-cols-4 gap-3 mb-3">
          <div><p className="text-xs text-muted-foreground">Manufactured (24h)</p><p className="font-heading text-xl font-bold text-navy">{brief.yesterday.products_manufactured}</p></div>
          <div><p className="text-xs text-muted-foreground">Published (24h)</p><p className="font-heading text-xl font-bold text-navy">{brief.yesterday.products_published}</p></div>
          <div><p className="text-xs text-muted-foreground">Revenue</p><p className="font-heading text-xl font-bold text-navy">${brief.revenue.total_usd}</p></div>
          <div><p className="text-xs text-muted-foreground">Open Risks</p><p className="font-heading text-xl font-bold text-navy">{brief.risks.open_escalations + brief.risks.issues_found}</p></div>
        </div>
        <ul className="space-y-1">
          {brief.focus_today.map((f, i) => (
            <li key={i} className="text-sm text-navy flex items-start gap-2"><span className="text-gold">→</span>{f}</li>
          ))}
        </ul>
      </Section>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Factory Health */}
        <Section icon={Activity} title="Factory Health™" testid="factory-health-metrics">
          <div className="flex items-center gap-3 mb-3">
            <span className="font-heading text-3xl font-bold text-navy">{health.overall_score}%</span>
            <span className={`text-sm font-semibold ${health.factory_health === "healthy" ? "text-emerald-600" : "text-amber-600"}`}>{health.factory_health.toUpperCase()}</span>
          </div>
          <div className="space-y-1.5">
            {Object.entries(health.metrics).map(([k, v]) => (
              <div key={k} className="flex items-center gap-2 text-xs">
                <span className="w-52 text-muted-foreground shrink-0">{k}</span>
                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden"><div className="h-full bg-gold" style={{ width: `${v}%` }} /></div>
                <span className="w-9 text-right text-navy font-medium">{v}%</span>
              </div>
            ))}
          </div>
        </Section>

        {/* Self-Diagnostics */}
        <Section icon={Stethoscope} title="Self-Diagnostics™" testid="self-diagnostics">
          <div className="flex items-center justify-between mb-3">
            <span className={`text-sm font-semibold ${d.status === "healthy" ? "text-emerald-600" : "text-amber-600"}`}>
              {d.issues_found} issue(s) · {d.status}
            </span>
            {d.auto_repairable > 0 && (
              <button data-testid="repair-btn" onClick={repair} disabled={repairing}
                className="flex items-center gap-1.5 bg-navy text-white px-3 py-1.5 rounded-sm text-xs font-semibold disabled:opacity-60">
                {repairing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Wrench className="w-3.5 h-3.5" />} Auto-Repair ({d.auto_repairable})
              </button>
            )}
          </div>
          <div className="space-y-1.5">
            {d.checks.map((c, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                {c.count === 0 ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" /> : <AlertTriangle className={`w-3.5 h-3.5 shrink-0 ${SEV[c.severity]}`} />}
                <span className="text-navy">{c.area}</span>
                <span className="text-muted-foreground flex-1 truncate">— {c.issue}</span>
                <span className={`font-medium ${SEV[c.severity]}`}>{c.count}</span>
              </div>
            ))}
          </div>
        </Section>

        {/* AI Scorecard / Cost */}
        {score && (
          <Section icon={DollarSign} title="Cost Optimization™ & AI Scorecard" testid="ai-scorecard">
            <p className="text-sm mb-2">Total est. spend: <b className="text-navy">${score.total_estimated_cost_usd}</b> <span className="text-xs text-muted-foreground">(Estimated)</span></p>
            <div className="space-y-1 mb-2">
              {score.by_capability.slice(0, 6).map((c) => (
                <div key={c.name} className="flex items-center justify-between text-xs">
                  <span className="text-navy">{c.name}</span>
                  <span className="text-muted-foreground">{c.jobs} jobs · {c.success_rate}% · ${c.est_cost_usd}</span>
                </div>
              ))}
            </div>
            <ul className="text-xs text-muted-foreground space-y-0.5">
              {score.recommendations.map((r, i) => <li key={i}>• {r}</li>)}
            </ul>
          </Section>
        )}

        {/* Capacity */}
        {cap && (
          <Section icon={Gauge} title="Capacity Planning™" testid="capacity">
            <div className="grid grid-cols-3 gap-2 text-center mb-2">
              <div><p className="text-xs text-muted-foreground">Running</p><p className="font-heading text-lg font-bold text-navy">{cap.jobs_running}</p></div>
              <div><p className="text-xs text-muted-foreground">Queued</p><p className="font-heading text-lg font-bold text-navy">{cap.jobs_queued}</p></div>
              <div><p className="text-xs text-muted-foreground">Batch pending</p><p className="font-heading text-lg font-bold text-navy">{cap.batch_items_pending}</p></div>
            </div>
            <p className="text-xs text-muted-foreground">{cap.recommendation}</p>
          </Section>
        )}

        {/* Knowledge Gaps */}
        {gaps && (
          <Section icon={Search} title="Knowledge Gap Detector™" testid="knowledge-gaps">
            <p className="text-sm mb-2"><b className="text-navy">{gaps.pending_count}</b> topics pending manufacture</p>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {gaps.pending_topics.slice(0, 10).map((t, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-navy truncate">{t.topic}</span>
                  <span className="text-muted-foreground shrink-0">{t.college}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">{gaps.recommendation}</p>
          </Section>
        )}

        {/* Factory Council */}
        {council && (
          <Section icon={Users} title="Factory Council™ — Continuous Improvement" testid="factory-council">
            <div className="space-y-2 mb-2">
              {council.division_reports.map((r, i) => (
                <div key={i} className="text-xs border-l-2 border-gold/60 pl-2">
                  <p className="font-medium text-navy">{r.division}</p>
                  <p className="text-muted-foreground">✓ {r.successes} · {r.recommendation}</p>
                </div>
              ))}
            </div>
            <p className="text-xs font-semibold text-navy">Top improvements</p>
            <ul className="text-xs text-muted-foreground space-y-0.5">
              {council.top_improvements.map((t, i) => <li key={i}>• {t}</li>)}
            </ul>
          </Section>
        )}

        {/* Enterprise Memory */}
        {mem && (
          <Section icon={Database} title="Enterprise Memory™" testid="enterprise-memory">
            <p className="text-xs font-semibold text-navy mb-1">Most reliable workflows</p>
            <div className="space-y-1 mb-3">
              {mem.successful_templates.slice(0, 5).map((t) => (
                <div key={t.template} className="flex items-center justify-between text-xs">
                  <span className="text-navy truncate">{t.template}</span>
                  <span className="text-muted-foreground">{t.reliability}% · {t.runs} runs</span>
                </div>
              ))}
              {mem.successful_templates.length === 0 && <p className="text-xs text-muted-foreground">No completed workflows yet.</p>}
            </div>
            <p className="text-xs font-semibold text-navy mb-1">Best Treasure Standard™ recipes</p>
            <div className="flex flex-wrap gap-1">
              {mem.best_recipes.map((r) => (
                <span key={r.recipe} className="text-[11px] px-1.5 py-0.5 rounded bg-gold/15 text-navy">{r.recipe} ({r.treasure_certified})</span>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}
