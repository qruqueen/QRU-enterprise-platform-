import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { toast } from "sonner";
import { Wand2, Loader2, Sparkles, CheckCircle2, XCircle, Circle, ShieldCheck, AlertTriangle, ArrowRight, BookOpen, Lightbulb, Brain } from "lucide-react";

const SECTIONS = [
  ["simple_answer", "1 · Simple Answer"],
  ["why_it_matters", "2 · Why It Matters"],
  ["everyday_example", "3 · Everyday Example"],
  ["visual_analogy", "4 · Visual Analogy"],
  ["qru_translation", "5 · QRU Translation™"],
  ["memory_sentence", "6 · Memory Sentence™"],
  ["deep_roots", "8 · Deep Roots™ (Cause → Mechanism → Outcome)"],
];

function StageRow({ s }) {
  const Icon = s.status === "done" ? CheckCircle2 : s.status === "failed" ? XCircle : Circle;
  const color = s.status === "done" ? "text-emerald-600" : s.status === "failed" ? "text-red-600" : "text-amber-500";
  return (
    <div className="flex items-start gap-2.5 py-1.5" data-testid={`stage-${s.stage}`}>
      <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${color}`} />
      <div>
        <p className="text-sm font-medium text-navy">{s.stage}</p>
        {s.detail && <p className="text-xs text-muted-foreground">{s.detail}</p>}
      </div>
    </div>
  );
}

export default function TranslationEngine() {
  const [question, setQuestion] = useState("");
  const [audience, setAudience] = useState("");
  const [audiences, setAudiences] = useState([]);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/translation-engine/stages").then(({ data }) => setAudiences(data.audiences || [])).catch(() => {});
  }, []);

  const run = async (resumeCtx) => {
    if (!question.trim()) return toast.error("Describe what you're curious about");
    setLoading(true);
    setData(null);
    try {
      const { data } = await api.post("/translation-engine/manufacture", {
        question, audience: audience || null,
        resume_from: resumeCtx?.error?.retry_from, context: resumeCtx?.context,
      });
      setData(data);
      if (data.ok) toast.success(data.verified ? "Treasure Standard™ understanding manufactured" : "Draft understanding manufactured");
      else toast.message(`Paused at: ${data.error?.failed_stage}`);
    } catch { toast.error("The Translation Engine is temporarily unavailable — please retry"); }
    finally { setLoading(false); }
  };

  const r = data?.result;

  return (
    <div>
      <PageHeader
        overline="QRU Translation Engine™ · Flagship"
        title="Manufacture Understanding"
        description="You don't need technical expertise. You only need curiosity. QRU manufactures understanding — through a complete, verified workflow, not a single guess."
      />

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input */}
        <div className="bg-card border rounded-md p-6 h-fit lg:sticky lg:top-24">
          <label className="text-sm font-medium">What would you like to understand today?</label>
          <p className="text-xs text-muted-foreground mt-0.5 mb-2">You don't need technical language. Describe what you're curious about, and QRU will transform it into clear understanding.</p>
          <textarea data-testid="te-question" rows={4} value={question} onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How does sleep help my memory?"
            className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm resize-none" />
          <label className="text-sm font-medium mt-4 block">Audience</label>
          <select data-testid="te-audience" value={audience} onChange={(e) => setAudience(e.target.value)}
            className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm bg-white">
            <option value="">Auto-detect</option>
            {audiences.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <button data-testid="te-run" onClick={() => run()} disabled={loading}
            className="mt-4 w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground py-2.5 rounded-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Manufacturing…</> : <><Wand2 className="w-4 h-4" /> Manufacture Understanding</>}
          </button>

          {data?.stages && (
            <div className="mt-5 pt-4 border-t" data-testid="te-pipeline">
              <p className="overline text-primary mb-1">Manufacturing Pipeline</p>
              {data.stages.map((s, i) => <StageRow key={i} s={s} />)}
            </div>
          )}
        </div>

        {/* Output */}
        <div>
          {loading && (
            <div className="bg-card border rounded-md p-12 flex flex-col items-center text-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
              <p className="font-heading font-semibold">Manufacturing understanding…</p>
            </div>
          )}

          {!loading && !data && (
            <div className="bg-card border border-dashed rounded-md p-12 flex flex-col items-center text-center">
              <Sparkles className="w-10 h-10 text-muted-foreground mb-4" strokeWidth={1.5} />
              <p className="font-heading font-semibold">Your understanding appears here</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">A complete QRU educational explanation, manufactured through a verified 7-stage workflow.</p>
            </div>
          )}

          {/* Error / clarifying */}
          {!loading && data && !data.ok && (
            <div className="bg-amber-50 border border-amber-300 rounded-md p-6" data-testid="te-error">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0" />
                <div className="flex-1">
                  <p className="font-heading font-semibold text-navy">Paused at: {data.error?.failed_stage}</p>
                  <p className="text-sm text-foreground/70 mt-1">{data.clarifying_question || data.error?.reason}</p>
                  <p className="text-xs text-muted-foreground mt-2">Your input is preserved. You can retry from this stage without starting over.</p>
                  <button data-testid="te-retry" onClick={() => run(data)}
                    className="mt-3 inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm bg-navy text-white hover:bg-navy/90">
                    <ArrowRight className="w-3.5 h-3.5" /> Retry from {data.error?.retry_from}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Result */}
          {!loading && r && (
            <div className="animate-fade-up space-y-4" data-testid="te-result">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full border ${r.source === "verified" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"}`}>
                  <ShieldCheck className="w-3.5 h-3.5" /> {r.source_label}
                </span>
                {r.treasure_standard && <span className="text-xs px-2 py-1 rounded-full bg-gold/15 text-navy border border-gold">Treasure Standard™</span>}
                <span className="text-xs px-2 py-1 rounded-full bg-navy/5 text-navy">{r.audience}</span>
              </div>

              {SECTIONS.map(([key, label]) => r[key] ? (
                <div key={key} className="bg-card border rounded-md p-4">
                  <p className="overline text-primary mb-1">{label}</p>
                  <p className="text-sm text-foreground/85 leading-relaxed">{r[key]}</p>
                </div>
              ) : null)}

              {r.key_vocabulary?.length > 0 && (
                <div className="bg-card border rounded-md p-4">
                  <p className="overline text-primary mb-2 flex items-center gap-1"><BookOpen className="w-3.5 h-3.5" /> 7 · Key Vocabulary</p>
                  <div className="space-y-1.5">
                    {r.key_vocabulary.map((v, i) => (
                      <p key={i} className="text-sm"><span className="font-semibold text-navy">{v.term}:</span> <span className="text-foreground/75">{v.definition}</span></p>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-card border rounded-md p-4">
                <p className="overline text-primary mb-1 flex items-center gap-1"><Brain className="w-3.5 h-3.5" /> 9 · Verification Status</p>
                <p className="text-sm text-foreground/85">{r.verification_status}</p>
                {r.verification_checks && (
                  <div className="grid sm:grid-cols-2 gap-1 mt-2">
                    {Object.entries(r.verification_checks).map(([k, val]) => (
                      <p key={k} className="text-xs text-muted-foreground"><span className="capitalize">{k.replace(/_/g, " ")}</span>: {val}</p>
                    ))}
                  </div>
                )}
              </div>

              {r.suggested_next_question && (
                <button data-testid="te-next" onClick={() => { setQuestion(r.suggested_next_question); }}
                  className="w-full text-left bg-navy/5 border border-navy/10 rounded-md p-4 hover:border-gold transition-colors">
                  <p className="overline text-primary mb-1 flex items-center gap-1"><Lightbulb className="w-3.5 h-3.5" /> 10 · Suggested Next Question</p>
                  <p className="text-sm text-navy font-medium">{r.suggested_next_question}</p>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
