import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import * as Icons from "lucide-react";
import { Loader2, ArrowRight, ArrowLeft, Sparkles, CheckCircle2, ShieldAlert, BookOpenCheck, Compass } from "lucide-react";

const MATURITY_TONE = {
  "Gold Master Ready": "gold", "Fully Automated": "emerald", "Guided Workflow": "blue",
  "Draft Generation": "amber", "Script + Narration": "violet", "Experimental": "slate", "Coming Soon": "slate",
};

export default function CreateExperience() {
  const nav = useNavigate();
  const [data, setData] = useState(null);
  const [step, setStep] = useState(1);
  const [outcome, setOutcome] = useState(null);
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("Beginner adult");
  const [goal, setGoal] = useState("");
  const [plan, setPlan] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get("/factory-os/outcomes").then((r) => setData(r.data)).catch(() => setData(false)); }, []);

  const pick = (o) => { setOutcome(o); setPlan(null); setStep(2); };

  const buildPlan = async () => {
    if (!topic.trim()) return toast.error("Tell the Factory what it's about.");
    setBusy(true); setPlan(null);
    try {
      const { data: p } = await api.post("/factory-os/plan", { outcome_id: outcome.id, topic, audience, goal });
      setPlan(p); setStep(3);
    } catch (e) { toast.error(e.response?.data?.detail || "Could not build the plan."); }
    finally { setBusy(false); }
  };

  const launch = async () => {
    const route = plan?.launch?.route || outcome?.route;
    try {
      const { data: proj } = await api.post("/factory-os/projects", { outcome_id: outcome.id, topic, audience, goal });
      toast.success(`Project started — tracked in My Projects. Launching ${plan?.launch?.workflow}…`);
      // Pass the project so production auto-advances the continuity board with zero manual tracking.
      nav(proj?.id ? `${route}?project=${proj.id}` : route);
    } catch {
      toast.message("Launching workflow…");
      nav(route);
    }
  };

  if (data === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (data === false) return <p className="text-sm text-muted-foreground p-8">Could not load the Create experience.</p>;

  const Icon = (name) => Icons[name] || Icons.Sparkles;

  return (
    <div data-testid="create-page">
      <PageHeader
        overline="QRU Factory Operating System™ · Governed by QRU-CON-0001 §7/§8"
        title="Create"
        description="Tell the Factory what you'd like to create. It handles the specialized intelligences, knowledge, design, quality and governance behind the scenes — you manage the outcome."
        actions={<VerifiedBadge label="You manage outcomes · The Factory manages agents" testid="create-badge" />}
      />

      {/* Stepper */}
      <div className="flex items-center gap-2 mb-6 text-[11px]" data-testid="create-stepper">
        {["Choose an outcome", "Describe it", "Review & launch"].map((label, i) => (
          <div key={i} className="flex items-center gap-2">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-semibold ${step === i + 1 ? "bg-navy text-white" : step > i + 1 ? "bg-emerald-100 text-emerald-700" : "bg-navy/[0.06] text-navy/50"}`}>
              {step > i + 1 ? <CheckCircle2 className="w-3 h-3" /> : <span className="w-4 h-4 rounded-full bg-current/20 grid place-items-center text-[9px]">{i + 1}</span>} {label}
            </span>
            {i < 2 && <ArrowRight className="w-3 h-3 text-navy/30" />}
          </div>
        ))}
      </div>

      {/* Step 1 — outcomes */}
      {step === 1 && (
        <Panel title={data.operating_question} icon={Sparkles} accent="royal" testid="create-outcomes">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.outcomes.map((o) => {
              const OI = Icon(o.icon);
              return (
                <button key={o.id} onClick={() => pick(o)} data-testid={`create-outcome-${o.id}`}
                  className="text-left border rounded-lg p-4 border-navy/15 hover:border-royal hover:shadow-md transition-all group">
                  <div className="flex items-center justify-between mb-2">
                    <span className="w-9 h-9 rounded-md bg-royal/10 text-royal grid place-items-center group-hover:bg-royal group-hover:text-white transition-colors"><OI className="w-4.5 h-4.5" /></span>
                    <StatusChip status={o.maturity_label} tone={MATURITY_TONE[o.maturity_label] || "slate"} />
                  </div>
                  <p className="text-sm font-bold text-navy">{o.name}</p>
                  <p className="text-[11px] text-muted-foreground mt-1 leading-snug">{o.description}</p>
                  <p className="text-[10px] text-royal font-semibold mt-2 inline-flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">Choose <ArrowRight className="w-3 h-3" /></p>
                </button>
              );
            })}
          </div>
          <div className="mt-4 flex flex-wrap gap-2 text-[10px]" data-testid="create-legend">
            <span className="text-muted-foreground mr-1">Manufacturing maturity:</span>
            {Object.values(data.maturity_legend).map((m) => <StatusChip key={m} status={m} tone={MATURITY_TONE[m] || "slate"} />)}
          </div>
        </Panel>
      )}

      {/* Step 2 — describe */}
      {step === 2 && outcome && (
        <Panel title={`Tell the Factory about your ${outcome.name}`} icon={Compass} accent="gold" testid="create-describe">
          <button onClick={() => setStep(1)} data-testid="create-back-1" className="text-[11px] text-royal inline-flex items-center gap-1 mb-3"><ArrowLeft className="w-3 h-3" /> Choose a different outcome</button>
          <div className="grid md:grid-cols-3 gap-3">
            <div className="md:col-span-3">
              <label className="text-xs font-bold text-navy uppercase tracking-wide">What is it about?</label>
              <input data-testid="create-topic" value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. Forex trading basics" className="w-full mt-1 border rounded-sm p-2 text-sm" />
            </div>
            <div>
              <label className="text-xs font-bold text-navy uppercase tracking-wide">Who is it for?</label>
              <select data-testid="create-audience" value={audience} onChange={(e) => setAudience(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
                {["Beginner adult", "Teen learner", "Student", "Entrepreneur", "Professional audience", "General public"].map((a) => <option key={a}>{a}</option>)}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="text-xs font-bold text-navy uppercase tracking-wide">What understanding should they leave with?</label>
              <input data-testid="create-goal" value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="e.g. Understand currency risk before trading" className="w-full mt-1 border rounded-sm p-2 text-sm" />
            </div>
          </div>
          <button onClick={buildPlan} disabled={busy} data-testid="create-build-plan"
            className="mt-4 inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Check knowledge & plan
          </button>
        </Panel>
      )}

      {/* Step 3 — plan */}
      {step === 3 && plan && (
        <div className="space-y-5" data-testid="create-plan">
          <button onClick={() => setStep(2)} data-testid="create-back-2" className="text-[11px] text-royal inline-flex items-center gap-1"><ArrowLeft className="w-3 h-3" /> Edit details</button>

          {/* Knowledge-First gate */}
          <Panel title="Knowledge-First Check" icon={BookOpenCheck} accent="royal" testid="create-kr-gate">
            {plan.knowledge_gap.knowledge_record_found ? (
              <div className="flex items-start gap-2" data-testid="create-kr-found">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-navy font-semibold">{plan.knowledge_gap.message}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">Your {plan.outcome.name} will be manufactured from this verified Knowledge Record — never invented.</p>
                </div>
              </div>
            ) : (
              <div data-testid="create-kr-gap">
                <div className="flex items-start gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm text-navy font-semibold">{plan.knowledge_gap.message}</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">{plan.knowledge_gap.offer?.note}</p>
                  </div>
                </div>
                <button onClick={() => nav(plan.knowledge_gap.offer.route)} data-testid="create-begin-knowledge"
                  className="mt-3 inline-flex items-center gap-2 bg-gold text-navy px-4 py-2 rounded-sm font-bold text-sm"><BookOpenCheck className="w-4 h-4" /> {plan.knowledge_gap.offer?.label}</button>
              </div>
            )}
            {plan.knowledge_gap.alternatives?.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5" data-testid="create-kr-alts">
                <span className="text-[10px] text-muted-foreground mr-1">Related records:</span>
                {plan.knowledge_gap.alternatives.map((a) => <span key={a.kr_code} className="text-[10px] px-1.5 py-0.5 rounded border bg-navy/[0.05] text-navy">{a.kr_code} · {String(a.title).slice(0, 28)}</span>)}
              </div>
            )}
          </Panel>

          {/* Guidance — the Factory always answers (Constitution §7) */}
          <Panel title="Where you are" icon={Compass} accent="gold" testid="create-guidance">
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 text-[12px]">
              {Object.entries({
                "What am I creating?": plan.guidance.what_am_i_creating,
                "What's happening now?": plan.guidance.whats_happening_now,
                "What happens next?": plan.guidance.what_happens_next,
                "What needs my approval?": plan.guidance.what_needs_my_approval,
                "Where is my product?": plan.guidance.where_is_my_product,
                "How do I publish it?": plan.guidance.how_do_i_publish,
              }).map(([q, a]) => (
                <div key={q} className="border rounded-md p-2.5 border-navy/10">
                  <p className="text-[10px] font-bold uppercase tracking-wide text-royal">{q}</p>
                  <p className="text-navy mt-0.5">{a}</p>
                </div>
              ))}
            </div>
          </Panel>

          {/* Plan + launch */}
          <Panel title="Your governed plan" icon={Sparkles} accent="royal" testid="create-plan-steps">
            <div className="flex items-center justify-between flex-wrap gap-3 mb-3">
              <div className="flex items-center gap-2">
                <StatusChip status={plan.outcome.maturity_label} tone={MATURITY_TONE[plan.outcome.maturity_label] || "slate"} />
                <span className="text-[11px] text-muted-foreground">via <b className="text-navy">{plan.launch.workflow}</b></span>
              </div>
              <div className="flex flex-wrap gap-1">{plan.governed_by.map((g) => <span key={g} className="text-[9px] px-1.5 py-0.5 rounded bg-royal/10 text-royal border border-royal/20">{g}</span>)}</div>
            </div>
            <ol className="space-y-1.5 mb-4">
              {plan.steps.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-[12px]"><span className="w-4 h-4 rounded-full bg-navy/[0.08] text-navy grid place-items-center text-[9px] font-bold mt-0.5 shrink-0">{i + 1}</span><span className="text-navy">{s}</span></li>
              ))}
            </ol>
            <button onClick={launch} disabled={!plan.can_launch} data-testid="create-launch"
              className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
              {plan.can_launch ? <>Launch {plan.launch.workflow} <ArrowRight className="w-4 h-4" /></> : "Manufacture the Knowledge Record first"}
            </button>
            {!plan.can_launch && <p className="text-[11px] text-amber-700 mt-2" data-testid="create-launch-blocked">Knowledge always comes before products — begin the Knowledge Manufacturing Pipeline above.</p>}
          </Panel>
        </div>
      )}
    </div>
  );
}
