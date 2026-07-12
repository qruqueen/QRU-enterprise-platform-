import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, Send, Sparkles, MessageSquareText, ArrowRight, BookOpenCheck, RotateCcw,
  CheckCircle2, ShieldAlert, Bot, Compass, Wand2,
} from "lucide-react";

const MATURITY_TONE = {
  "Gold Master Ready": "gold", "Fully Automated": "emerald", "Guided Workflow": "blue",
  "Draft Generation": "amber", "Script + Narration": "violet", "Experimental": "slate", "Coming Soon": "slate",
};

export default function FactoryConcierge() {
  const nav = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [useAi, setUseAi] = useState(false);
  const [state, setState] = useState({ stage: "need_outcome", slots: {}, outcome: null, plan: null, canLaunch: false, suggestions: [] });
  const [launching, setLaunching] = useState(false);
  const endRef = useRef(null);
  const greeted = useRef(false);

  const send = async (text, sid = sessionId) => {
    if (sending) return;
    setSending(true);
    if (text) setMessages((m) => [...m, { role: "user", text }]);
    try {
      const { data } = await api.post("/factory-os/concierge/message", { message: text, session_id: sid, use_ai: useAi });
      setSessionId(data.session_id);
      setMessages((m) => [...m, { role: "concierge", text: data.reply, stage: data.stage, ai_used: data.ai_used }]);
      setState({ stage: data.stage, slots: data.slots, outcome: data.outcome, plan: data.plan, canLaunch: data.can_launch, suggestions: data.suggestions || [] });
    } catch (e) {
      toast.error(e.response?.data?.detail || "The Concierge is unavailable. Please try again.");
    } finally { setSending(false); }
  };

  useEffect(() => { if (greeted.current) return; greeted.current = true; send(""); /* greeting, once */ }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const onSubmit = (e) => { e.preventDefault(); const t = input.trim(); if (!t) return; setInput(""); send(t); };

  const reset = () => { setMessages([]); setSessionId(null); setState({ stage: "need_outcome", slots: {}, outcome: null, plan: null, canLaunch: false, suggestions: [] }); send("", null); };

  const launch = async () => {
    const { slots, plan } = state;
    const route = plan?.launch?.route;
    setLaunching(true);
    try {
      const { data: proj } = await api.post("/factory-os/projects", { outcome_id: slots.outcome_id, topic: slots.topic, audience: slots.audience, goal: slots.goal });
      toast.success(`Project started — tracked in My Projects. Launching ${plan?.launch?.workflow}…`);
      nav(proj?.id ? `${route}?project=${proj.id}` : route);
    } catch {
      toast.message("Launching workflow…");
      if (route) nav(route);
    } finally { setLaunching(false); }
  };

  const beginKnowledge = () => nav(state.plan?.knowledge_gap?.offer?.route || "/promotion-pipeline");

  const { stage, slots, outcome, plan, canLaunch, suggestions } = state;

  return (
    <div data-testid="concierge-page">
      <PageHeader
        overline="QRU Factory Concierge™ · Governed by QRU-CON-0001 §7/§8"
        title="Concierge"
        description="Just tell the Factory what you want in plain words. The Concierge finds the right governed workflow, checks knowledge first, and never invents facts — you stay in charge of the outcome."
        actions={<VerifiedBadge label="Deterministic · Knowledge-First · $0 by default" testid="concierge-badge" />}
      />

      <div className="grid lg:grid-cols-3 gap-5">
        {/* Conversation */}
        <div className="lg:col-span-2">
          <Panel title="Conversation" icon={MessageSquareText} accent="royal" testid="concierge-chat">
            <div className="flex items-center justify-between mb-3">
              <label className="flex items-center gap-2 text-[11px] text-navy cursor-pointer select-none" data-testid="concierge-ai-toggle" onClick={() => setUseAi((v) => !v)}>
                <span className={`w-9 h-5 rounded-full transition-colors relative ${useAi ? "bg-royal" : "bg-navy/20"}`}>
                  <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${useAi ? "left-4.5" : "left-0.5"}`} style={{ left: useAi ? 18 : 2 }} />
                </span>
                <span className="inline-flex items-center gap-1"><Wand2 className="w-3.5 h-3.5 text-royal" /> Use light-AI understanding <span className="text-muted-foreground">(optional)</span></span>
              </label>
              <button onClick={reset} data-testid="concierge-reset" className="text-[11px] text-royal inline-flex items-center gap-1 hover:underline"><RotateCcw className="w-3 h-3" /> Start over</button>
            </div>

            <div className="space-y-3 max-h-[46vh] overflow-y-auto pr-1" data-testid="concierge-messages">
              {messages.map((m, i) => (
                <div key={i} data-testid={`concierge-message-${i}`} className={`flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  {m.role === "concierge" && <span className="w-7 h-7 rounded-full bg-royal/10 text-royal grid place-items-center shrink-0 mt-0.5"><Bot className="w-4 h-4" /></span>}
                  <div className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-[12.5px] leading-relaxed ${m.role === "user" ? "bg-navy text-white rounded-br-sm" : "bg-navy/[0.05] text-navy rounded-bl-sm"}`}>
                    {m.text}
                    {m.role === "concierge" && m.ai_used && <span className="block mt-1 text-[9px] text-royal/70 inline-flex items-center gap-1"><Wand2 className="w-2.5 h-2.5" /> parsed with light-AI</span>}
                  </div>
                </div>
              ))}
              {sending && <div className="flex items-center gap-2 text-[11px] text-muted-foreground"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Concierge is thinking…</div>}
              <div ref={endRef} />
            </div>

            {/* Suggestion chips (outcome selection) */}
            {stage === "need_outcome" && suggestions.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3" data-testid="concierge-suggestions">
                {suggestions.map((s) => (
                  <button key={s.outcome_id} data-testid={`concierge-suggestion-${s.outcome_id}`} onClick={() => send(s.value)}
                    className="text-[11px] px-2.5 py-1 rounded-full border border-royal/25 text-royal hover:bg-royal hover:text-white transition-colors">{s.label}</button>
                ))}
              </div>
            )}

            {/* Composer */}
            <form onSubmit={onSubmit} className="flex items-center gap-2 mt-4">
              <input data-testid="concierge-input" value={input} onChange={(e) => setInput(e.target.value)} disabled={sending}
                placeholder="e.g. Create a video about financial literacy for beginners"
                className="flex-1 border rounded-full px-4 py-2.5 text-sm focus:outline-none focus:border-royal" />
              <button type="submit" data-testid="concierge-send" disabled={sending || !input.trim()}
                className="inline-flex items-center justify-center w-11 h-11 rounded-full bg-navy text-white disabled:opacity-50 hover:bg-navy/90 transition-colors shrink-0">
                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </form>
          </Panel>
        </div>

        {/* Live plan / action rail */}
        <div className="space-y-5">
          <Panel title="Your request" icon={Compass} accent="gold" testid="concierge-request">
            <dl className="space-y-2 text-[12px]">
              {[["Creating", outcome?.name], ["About", slots.topic], ["For", slots.audience], ["Goal", slots.goal]].map(([k, v]) => (
                <div key={k} className="flex items-start justify-between gap-3">
                  <dt className="text-[10px] uppercase tracking-wide text-muted-foreground pt-0.5">{k}</dt>
                  <dd className="text-navy font-medium text-right">{v || <span className="text-navy/30">—</span>}</dd>
                </div>
              ))}
            </dl>
            {outcome && <div className="mt-3 flex items-center gap-2"><StatusChip status={outcome.maturity_label} tone={MATURITY_TONE[outcome.maturity_label] || "slate"} /><span className="text-[10px] text-muted-foreground">via {outcome.workflow}</span></div>}
          </Panel>

          {/* Knowledge-First + launch */}
          {plan && (
            <Panel title="Knowledge-First" icon={BookOpenCheck} accent="royal" testid="concierge-kr">
              {canLaunch ? (
                <>
                  <div className="flex items-start gap-2" data-testid="concierge-kr-found">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                    <p className="text-[12px] text-navy">{plan.knowledge_gap.message} Your product will be manufactured from it — never invented.</p>
                  </div>
                  <ol className="mt-3 space-y-1 text-[11px]">
                    {plan.steps.slice(0, 6).map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-navy/80"><span className="w-4 h-4 rounded-full bg-navy/[0.08] text-navy grid place-items-center text-[9px] font-bold mt-0.5 shrink-0">{i + 1}</span>{s}</li>
                    ))}
                  </ol>
                  <button onClick={launch} disabled={launching} data-testid="concierge-launch"
                    className="mt-4 w-full inline-flex items-center justify-center gap-2 bg-navy text-white px-4 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
                    {launching ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Launch {plan.launch.workflow} <ArrowRight className="w-4 h-4" /></>}
                  </button>
                </>
              ) : (
                <div data-testid="concierge-kr-gap">
                  <div className="flex items-start gap-2">
                    <ShieldAlert className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                    <p className="text-[12px] text-navy">{plan.knowledge_gap.message}</p>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1.5">{plan.knowledge_gap.offer?.note}</p>
                  <button onClick={beginKnowledge} data-testid="concierge-begin-knowledge"
                    className="mt-3 w-full inline-flex items-center justify-center gap-2 bg-gold text-navy px-4 py-2.5 rounded-sm font-bold hover:bg-gold/90 transition-colors">
                    <BookOpenCheck className="w-4 h-4" /> {plan.knowledge_gap.offer?.label}
                  </button>
                </div>
              )}
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
