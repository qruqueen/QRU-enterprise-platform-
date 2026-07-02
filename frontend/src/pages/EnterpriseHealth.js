import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, ShieldCheck, ChevronDown, AlertTriangle, GitMerge, Sparkles, ArrowRightLeft } from "lucide-react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";

const URGENCY = { High: "hsl(var(--destructive))", Medium: "hsl(var(--warning))", Low: "hsl(var(--success))" };

function BigRing({ value }) {
  const size = 120, r = 52, c = 2 * Math.PI * r;
  const color = value >= 80 ? "hsl(var(--success))" : value >= 55 ? "hsl(var(--warning))" : "hsl(var(--destructive))";
  return (
    <svg width={size} height={size}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth="10" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={c} strokeDashoffset={c - (value / 100) * c} transform={`rotate(-90 ${size / 2} ${size / 2})`} style={{ transition: "stroke-dashoffset 0.6s" }} />
      <text x="50%" y="46%" dy="0.1em" textAnchor="middle" className="font-heading font-bold" fontSize="30" fill="hsl(var(--foreground))">{value}</text>
      <text x="50%" y="64%" textAnchor="middle" fontSize="10" fill="hsl(var(--muted-foreground))">OVERALL</text>
    </svg>
  );
}

export default function EnterpriseHealth() {
  const navigate = useNavigate();
  const [d, setD] = useState(null);
  const [legacy, setLegacy] = useState(null);
  const [open, setOpen] = useState(null);
  const [refactor, setRefactor] = useState(null);
  const [objective, setObjective] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [review, setReview] = useState(null);

  useEffect(() => {
    Promise.all([api.get("/command-center/health-detailed"), api.get("/enterprise-health"), api.get("/evolution/refactoring")])
      .then(([h, l, rf]) => { setD(h.data); setLegacy(l.data); setRefactor(rf.data); });
  }, []);

  const runReview = async () => {
    if (!objective.trim()) { toast.error("Describe the capability you're considering."); return; }
    setReviewing(true); setReview(null);
    try {
      const { data } = await api.post("/evolution/review", { objective, save: true });
      setReview(data);
    } catch { toast.error("Review failed. Try again."); }
    setReviewing(false);
  };

  if (!d) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div>
      <PageHeader overline="Organizational Health Director™ · Enterprise Mode" title="Enterprise Health"
        description="Continuous self-monitoring across every QRU system, with transparent, expandable detail." />

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-card border rounded-2xl p-6 flex flex-col items-center justify-center text-center">
          <BigRing value={d.overall} />
          <p className="text-sm text-muted-foreground mt-3">Enterprise Health</p>
        </div>
        <div className="lg:col-span-2 bg-card border rounded-2xl p-6">
          <p className="overline text-primary mb-4 flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" /> Detected Bottlenecks</p>
          {legacy?.bottlenecks?.length ? (
            <div className="space-y-2">
              {legacy.bottlenecks.map((b, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <span className="shrink-0 w-2 h-2 rounded-full mt-1.5" style={{ background: b.severity === "critical" ? "hsl(var(--destructive))" : b.severity === "warning" ? "hsl(var(--warning))" : "hsl(var(--primary))" }} />
                  <span><b>{b.area}:</b> <span className="text-muted-foreground">{b.detail}</span></span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-muted-foreground">No bottlenecks detected. All systems healthy.</p>}
          <p className="overline text-primary mt-6 mb-3">Recommendations</p>
          <ul className="space-y-1.5 text-sm">
            {legacy?.recommendations?.map((r, i) => <li key={i} className="flex gap-2"><span className="text-gold">→</span>{r}</li>)}
          </ul>
        </div>
      </div>

      <p className="overline text-primary mb-4">System Breakdown</p>
      <div className="grid sm:grid-cols-2 gap-3" data-testid="health-breakdown">
        {Object.entries(d.systems).map(([name, s]) => (
          <div key={name} className="bg-card border border-border rounded-xl overflow-hidden">
            <button onClick={() => setOpen(open === name ? null : name)} className="w-full p-4 flex items-center justify-between text-left" data-testid={`eh-${name}`}>
              <div>
                <p className="text-sm font-semibold">{name}</p>
                <p className="text-[11px] text-muted-foreground">Owned by {s.owner}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-heading font-bold text-lg" style={{ color: s.score >= 80 ? "hsl(var(--success))" : s.score >= 55 ? "hsl(var(--warning))" : "hsl(var(--destructive))" }}>{s.score}</span>
                <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${open === name ? "rotate-180" : ""}`} />
              </div>
            </button>
            <div className="h-1.5 bg-muted mx-4"><div className="h-full rounded-full" style={{ width: `${s.score}%`, background: s.score >= 80 ? "hsl(var(--success))" : s.score >= 55 ? "hsl(var(--warning))" : "hsl(var(--destructive))" }} /></div>
            {open === name && (
              <div className="p-4 pt-3 text-xs space-y-1.5 border-t border-border mt-3">
                <p><span className="text-muted-foreground">Why this score:</span> {s.why}</p>
                <p><span className="text-muted-foreground">Recommended improvement:</span> {s.recommendation}</p>
                <p><span className="text-muted-foreground">Urgency:</span> <span style={{ color: URGENCY[s.urgency] }} className="font-medium">{s.urgency}</span></p>
                {s.next_action !== "None" && <button onClick={() => navigate("/")} className="text-primary font-medium mt-1">Next: {s.next_action} →</button>}
              </div>
            )}
          </div>
        ))}
      </div>

      {(legacy?.idle_specialists?.length > 0 || legacy?.overloaded_specialists?.length > 0) && (
        <div className="grid sm:grid-cols-2 gap-4 mt-8">
          <div className="bg-card border rounded-xl p-4">
            <p className="overline text-muted-foreground mb-2">Idle Specialists</p>
            <p className="text-sm">{legacy.idle_specialists.length ? legacy.idle_specialists.join(", ") : "None"}</p>
          </div>
          <div className="bg-card border rounded-xl p-4">
            <p className="overline text-muted-foreground mb-2">Overloaded Specialists</p>
            <p className="text-sm">{legacy.overloaded_specialists.length ? legacy.overloaded_specialists.join(", ") : "None"}</p>
          </div>
        </div>
      )}

      {/* Extend Before Expand™ — Enterprise Evolution Governance */}
      <div className="mt-10 border-t border-border pt-8" data-testid="evolution-governance">
        <div className="flex items-center gap-2 mb-1">
          <ArrowRightLeft className="w-4 h-4 text-primary" />
          <h2 className="font-heading text-lg font-bold">Enterprise Evolution Review™</h2>
          <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold" style={{ background: "hsl(var(--gold) / 0.15)", color: "hsl(var(--navy))" }}>Extend Before Expand™</span>
        </div>
        <p className="text-sm text-muted-foreground mb-4">QRU becomes more powerful by becoming more intelligent, not more complicated. Before building anything new, check whether an existing capability can be extended.</p>

        <div className="grid lg:grid-cols-2 gap-6">
          <div className="bg-card border rounded-2xl p-5">
            <label className="text-xs text-muted-foreground mb-1 block">Proposed capability or objective</label>
            <textarea data-testid="evo-objective" value={objective} onChange={(e) => setObjective(e.target.value)} rows={3}
              placeholder="e.g. We want a system to deliver finished products to customers after certification."
              className="w-full px-3 py-2 text-sm bg-muted rounded-md border border-border outline-none focus:border-primary resize-none" />
            <button data-testid="evo-review-btn" onClick={runReview} disabled={reviewing}
              className="mt-3 px-5 py-2 rounded-md text-white text-sm font-medium flex items-center gap-2 disabled:opacity-60" style={{ background: "hsl(var(--royal))" }}>
              {reviewing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Run Evolution Review
            </button>
            {review && (
              <div className="mt-4 space-y-3" data-testid="evo-result">
                <div className="rounded-xl p-3 text-white" style={{ background: review.recommendation === "EXTEND EXISTING SYSTEM" ? "hsl(var(--success))" : "hsl(var(--navy))" }}>
                  <p className="text-[11px] opacity-80">Recommendation</p>
                  <p className="font-heading font-bold">{review.recommendation}</p>
                  <p className="text-xs opacity-90 mt-0.5">Target: {review.target_capability}</p>
                </div>
                <p className="text-sm">{review.rationale}</p>
                {review.questions?.length > 0 && (
                  <div className="space-y-1.5">
                    {review.questions.map((q, i) => (
                      <div key={i} className="text-xs border rounded-lg p-2"><p className="font-medium">{q.q}</p><p className="text-muted-foreground mt-0.5">{q.a}</p></div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="bg-card border rounded-2xl p-5">
            <p className="overline text-primary mb-3 flex items-center gap-1.5"><GitMerge className="w-3.5 h-3.5" /> Continuous Refactoring</p>
            <div className="space-y-2" data-testid="refactoring-insights">
              {refactor?.insights?.map((ins, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <span className="shrink-0 w-2 h-2 rounded-full mt-1.5" style={{ background: ins.severity === "warning" ? "hsl(var(--warning))" : ins.severity === "success" ? "hsl(var(--success))" : "hsl(var(--primary))" }} />
                  <div>
                    <p><b>{ins.area}:</b> <span className="text-muted-foreground">{ins.finding}</span></p>
                    <p className="text-xs text-primary mt-0.5">{ins.recommendation}</p>
                  </div>
                </div>
              ))}
            </div>
            {refactor?.decisions_recorded > 0 && <p className="text-xs text-muted-foreground mt-4">{refactor.decisions_recorded} architectural decision(s) recorded in Enterprise Memory.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
