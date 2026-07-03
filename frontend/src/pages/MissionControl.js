import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Loader2, Users, Heart, BookOpen, ShieldCheck, Sparkles, Package, CheckCircle2,
  Award, Gem, Gauge, Smile, Brain, TrendingUp, AlertTriangle, ChevronRight, Activity, ChevronDown,
} from "lucide-react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { FactoryResilience } from "@/components/FactoryResilience";

const ICONS = { users: Users, heart: Heart, book: BookOpen, shield: ShieldCheck, sparkles: Sparkles,
  package: Package, check: CheckCircle2, award: Award, gem: Gem, gauge: Gauge, smile: Smile, brain: Brain };

const URGENCY = { High: "hsl(var(--destructive))", Medium: "hsl(var(--warning))", Low: "hsl(var(--success))" };

function Ring({ value, size = 68 }) {
  const r = (size - 8) / 2, c = 2 * Math.PI * r;
  const color = value >= 80 ? "hsl(var(--success))" : value >= 55 ? "hsl(var(--warning))" : "hsl(var(--destructive))";
  return (
    <svg width={size} height={size} className="shrink-0">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth="6" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="6" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={c - (value / 100) * c} transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 0.6s ease" }} />
      <text x="50%" y="50%" dy="0.35em" textAnchor="middle" className="font-heading font-bold" fontSize="16" fill="hsl(var(--foreground))">{value}</text>
    </svg>
  );
}

export default function MissionControl() {
  const navigate = useNavigate();
  const [d, setD] = useState(null);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get("/command-center/briefing"),
      api.get("/command-center/mission-impact"),
      api.get("/command-center/health-detailed"),
      api.get("/command-center/departments"),
      api.get("/command-center/alerts"),
      api.get("/org-activity"),
    ]).then(([b, m, h, dep, a, act]) => setD({
      briefing: b.data, impact: m.data, health: h.data, departments: dep.data.departments,
      alerts: a.data.alerts, activity: act.data.slice(0, 8),
    }));
  }, []);

  if (!d) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div>
      <PageHeader
        overline="QRU Mission Control · Enterprise Mode"
        title="Executive Command Center"
        description="Verified knowledge enters. Understanding grows. Lives improve."
        actions={<button data-testid="open-mission-console" onClick={() => navigate("/command")} className="px-4 py-2 rounded-md text-white text-sm font-medium" style={{ background: "hsl(var(--royal))" }}>Open Mission Control</button>}
      />

      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold mb-6" style={{ background: "hsl(var(--navy))", color: "white" }} data-testid="enterprise-mode-badge">
        <ShieldCheck className="w-3.5 h-3.5" style={{ color: "hsl(var(--gold))" }} /> ENTERPRISE MODE · INTERNAL
      </span>

      {/* Daily briefing */}
      <div className="rounded-2xl p-6 mb-8 text-white relative overflow-hidden" style={{ background: "linear-gradient(135deg, hsl(var(--royal)), hsl(var(--navy)))" }} data-testid="daily-briefing">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="font-heading text-2xl font-bold">{d.briefing.greeting}</h2>
            <p className="text-white/70 text-sm mt-1">Today's Enterprise Health: <span className="font-semibold text-gold" style={{ color: "hsl(var(--gold))" }}>{d.briefing.enterprise_health}%</span></p>
          </div>
          <Ring value={d.briefing.enterprise_health} size={76} />
        </div>
        <div className="grid sm:grid-cols-2 gap-x-8 gap-y-2 mt-5">
          {d.briefing.lines.map((l, i) => (
            <div key={i} className="flex gap-2 text-sm">
              <span className="text-gold font-semibold shrink-0" style={{ color: "hsl(var(--gold))" }}>{l.area}:</span>
              <span className="text-white/85">{l.text}</span>
            </div>
          ))}
        </div>
        <div className="mt-5 pt-4 border-t border-white/15 flex items-start gap-2">
          <Sparkles className="w-4 h-4 shrink-0 mt-0.5" style={{ color: "hsl(var(--gold))" }} />
          <p className="text-sm"><span className="font-semibold" style={{ color: "hsl(var(--gold))" }}>Recommendation:</span> {d.briefing.recommendation}</p>
        </div>
      </div>

      <FactoryResilience />

      {/* Mission + Money */}
      <div className="mb-8">
        <p className="overline text-primary mb-4">Understanding Impact™</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3" data-testid="impact-grid">
          {d.impact.impact.map((m) => {
            const Icon = ICONS[m.icon] || TrendingUp;
            return (
              <div key={m.label} className="bg-card border border-border rounded-xl p-4">
                <Icon className="w-4 h-4 text-primary mb-2" />
                <p className="font-heading text-xl font-bold">{m.prefix || ""}{typeof m.value === "number" ? m.value.toLocaleString() : m.value}{m.suffix || ""}</p>
                <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">{m.label}</p>
              </div>
            );
          })}
        </div>
        <div className="grid grid-cols-3 gap-3 mt-3">
          {d.impact.business.map((m) => (
            <div key={m.label} className="rounded-xl p-4 border border-gold" style={{ background: "hsl(var(--gold) / 0.06)" }}>
              <p className="font-heading text-xl font-bold">{m.prefix || ""}{typeof m.value === "number" ? m.value.toLocaleString() : m.value}{m.suffix || ""}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">{m.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Enterprise Health transparency */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <p className="overline text-primary">Enterprise Health · {d.health.overall}%</p>
          <button onClick={() => navigate("/enterprise-health")} className="text-xs text-primary font-medium flex items-center gap-1">Full dashboard <ChevronRight className="w-3.5 h-3.5" /></button>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="health-systems">
          {Object.entries(d.health.systems).map(([name, s]) => (
            <div key={name} className="bg-card border border-border rounded-xl overflow-hidden">
              <button onClick={() => setExpanded(expanded === name ? null : name)} className="w-full p-4 flex items-center justify-between text-left" data-testid={`health-${name}`}>
                <div>
                  <p className="text-sm font-semibold">{name}</p>
                  <p className="text-[11px] text-muted-foreground">{s.owner}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-heading font-bold text-lg">{s.score}</span>
                  <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${expanded === name ? "rotate-180" : ""}`} />
                </div>
              </button>
              <div className="h-1.5 bg-muted mx-4"><div className="h-full rounded-full" style={{ width: `${s.score}%`, background: s.score >= 80 ? "hsl(var(--success))" : s.score >= 55 ? "hsl(var(--warning))" : "hsl(var(--destructive))" }} /></div>
              {expanded === name && (
                <div className="p-4 pt-3 text-xs space-y-1.5 border-t border-border mt-3">
                  <p><span className="text-muted-foreground">Why:</span> {s.why}</p>
                  <p><span className="text-muted-foreground">Recommendation:</span> {s.recommendation}</p>
                  <p><span className="text-muted-foreground">Urgency:</span> <span style={{ color: URGENCY[s.urgency] }}>{s.urgency}</span></p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Department cards */}
        <div className="lg:col-span-2">
          <p className="overline text-primary mb-4">Department Status</p>
          <div className="grid sm:grid-cols-2 gap-3" data-testid="department-cards">
            {d.departments.map((dep) => (
              <div key={dep.name} className="bg-card border border-border rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-semibold">{dep.name}</p>
                  <span className="font-heading font-bold text-sm" style={{ color: dep.health >= 80 ? "hsl(var(--success))" : dep.health >= 55 ? "hsl(var(--warning))" : "hsl(var(--destructive))" }}>{dep.health}</span>
                </div>
                <p className="text-[11px] text-muted-foreground">{dep.lead}</p>
                <p className="text-xs mt-2"><span className="text-muted-foreground">Now:</span> {dep.task}</p>
                <p className="text-xs mt-1"><span className="text-muted-foreground">Win:</span> {dep.achievement}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts + activity */}
        <div className="space-y-6">
          <div>
            <p className="overline text-primary mb-4">Alerts & Recommendations</p>
            <div className="space-y-2" data-testid="alerts-panel">
              {d.alerts.map((a, i) => (
                <div key={i} className="bg-card border border-border rounded-xl p-3">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{ color: URGENCY[a.priority] }} />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold">{a.issue}</p>
                      <p className="text-[11px] text-muted-foreground mt-0.5">{a.why}</p>
                      <p className="text-[11px] mt-1"><span className="text-primary font-medium">{a.action}</span> · {a.department}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="overline text-primary mb-4 flex items-center gap-1.5"><Activity className="w-3.5 h-3.5" /> Live Organization</p>
            <div className="space-y-2" data-testid="live-activity">
              {d.activity.map((a) => (
                <div key={a.id} className="text-xs flex gap-2">
                  <span className="text-primary font-medium shrink-0">{a.agent}</span>
                  <span className="text-muted-foreground">{a.action} {a.entity}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
