import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, MetricCard } from "@/components/qru";
import {
  Loader2, Sparkles, ShieldCheck, ThumbsUp, ThumbsDown, FileText, BookOpen,
  FlaskConical, FolderUp, ArrowRight, Brain, Quote, CheckCircle2, Clock,
} from "lucide-react";

const SOURCE_ICON = { founder_request: Sparkles, verified_research: FlaskConical, library_import: FolderUp };
const STAGE_ICON = { complete: CheckCircle2, pending: Clock, partial: Clock };

export default function KRManufacturing() {
  const nav = useNavigate();
  const [standard, setStandard] = useState(null);
  const [stats, setStats] = useState(null);
  const [pending, setPending] = useState([]);
  const [form, setForm] = useState({ source_type: "founder_request", topic: "", division: "", goal: "", audience: "", source_text: "" });
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [acting, setActing] = useState(null);

  const load = () => {
    api.get("/kr-manufacturing/stats").then((r) => setStats(r.data)).catch(() => {});
    api.get("/kr-manufacturing/pending-review").then((r) => setPending(r.data.records)).catch(() => {});
  };
  useEffect(() => {
    api.get("/kr-manufacturing/standard").then((r) => setStandard(r.data)).catch(() => {});
    load();
  }, []);

  const manufacture = async () => {
    if (!form.topic.trim()) { toast.error("Enter a topic or idea to manufacture."); return; }
    if (form.source_type === "library_import" && !form.source_text.trim()) {
      toast.error("Paste the source document text to manufacture from a library import."); return;
    }
    setBusy(true); setResult(null);
    toast.message("Manufacturing a governed Knowledge Record… researching, verifying, organizing.");
    try {
      const { data } = await api.post("/kr-manufacturing/manufacture", form);
      setResult(data);
      toast.success(`${data.kr_code} drafted — pending your review.`);
      load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const decide = async (krId, action) => {
    setActing(krId + action);
    try {
      if (action === "approve") { await api.post(`/kr-manufacturing/${krId}/approve`); toast.success("Approved — entered Enterprise Memory™. Ready to manufacture products."); }
      else { await api.post(`/kr-manufacturing/${krId}/reject`, { reason: "Rejected on Founder review" }); toast.message("Rejected."); }
      setResult(null); load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setActing(null); }
  };

  if (!standard) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div data-testid="kr-manufacturing-page">
      <PageHeader
        overline="Knowledge Record Manufacturing Engine™ · Inheritance-First™"
        title="Manufacture a Knowledge Record™"
        description="The Factory's first responsibility: manufacture the verified raw material — one governed Knowledge Record™ from which every product inherits. AI drafts and organizes; you approve; only then does it become truth."
        actions={<VerifiedBadge label={standard.standard.id} testid="kr-mfg-badge" />}
      />

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-8" data-testid="kr-mfg-stats">
          <MetricCard icon={FileText} label="Manufactured" value={stats.manufactured} testid="stat-manufactured" />
          <MetricCard icon={Clock} accent="royal" label="Pending Your Review" value={stats.pending_review} testid="stat-pending" onClick={() => document.getElementById("pending-review")?.scrollIntoView({ behavior: "smooth" })} />
          <MetricCard icon={Brain} accent="gold" label="In Enterprise Memory™" value={stats.enterprise_memory} testid="stat-memory" />
          <MetricCard icon={ShieldCheck} label="Confidence Threshold" value={`${stats.confidence_threshold}%`} testid="stat-threshold" />
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Manufacture form */}
        <div className="lg:col-span-2 space-y-6">
          <Panel title="Manufacture from a Source" icon={Sparkles} accent="gold" testid="kr-mfg-form">
            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-navy uppercase tracking-wide">Source</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-1.5">
                  {standard.sources.map((s) => {
                    const Icon = SOURCE_ICON[s.value] || Sparkles;
                    const active = form.source_type === s.value;
                    return (
                      <button key={s.value} data-testid={`source-${s.value}`} onClick={() => setForm((f) => ({ ...f, source_type: s.value }))}
                        className={`text-left p-3 rounded-md border text-xs transition-colors ${active ? "border-gold bg-gold/10 text-navy font-bold" : "border-border text-muted-foreground hover:border-navy"}`}>
                        <Icon className="w-4 h-4 mb-1" /> {s.label}
                      </button>
                    );
                  })}
                </div>
              </div>
              <div>
                <label className="text-xs font-bold text-navy uppercase tracking-wide">Topic / Idea</label>
                <input data-testid="kr-topic-input" value={form.topic} onChange={(e) => setForm((f) => ({ ...f, topic: e.target.value }))}
                  placeholder="e.g. How compound interest builds lasting wealth"
                  className="w-full mt-1.5 px-3 py-2 text-sm border border-border rounded-md bg-card outline-none focus:border-navy" />
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Audience (optional)</label>
                  <input data-testid="kr-audience-input" value={form.audience} onChange={(e) => setForm((f) => ({ ...f, audience: e.target.value }))}
                    placeholder="e.g. Teens, Parents, Beginners"
                    className="w-full mt-1.5 px-3 py-2 text-sm border border-border rounded-md bg-card outline-none focus:border-navy" />
                </div>
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Goal (optional)</label>
                  <input data-testid="kr-goal-input" value={form.goal} onChange={(e) => setForm((f) => ({ ...f, goal: e.target.value }))}
                    placeholder="What should the learner walk away able to do?"
                    className="w-full mt-1.5 px-3 py-2 text-sm border border-border rounded-md bg-card outline-none focus:border-navy" />
                </div>
              </div>
              {form.source_type === "library_import" && (
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Source Document Text</label>
                  <textarea data-testid="kr-source-text" value={form.source_text} onChange={(e) => setForm((f) => ({ ...f, source_text: e.target.value }))}
                    rows={6} placeholder="Paste the verified source text. The Factory structures it — it never invents facts."
                    className="w-full mt-1.5 px-3 py-2 text-sm border border-border rounded-md bg-card outline-none focus:border-navy" />
                </div>
              )}
              <button data-testid="kr-manufacture-btn" onClick={manufacture} disabled={busy}
                className="inline-flex items-center gap-2 bg-navy text-white px-5 py-2.5 rounded-md font-bold text-sm hover:bg-navy/90 disabled:opacity-60">
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                Manufacture Knowledge Record
              </button>
            </div>
          </Panel>

          {/* Result — pipeline stages */}
          {result && (
            <Panel title={`${result.kr_code} — Pipeline`} icon={FileText} accent="royal" testid="kr-result">
              <div className="space-y-2">
                {result.job.stages.map((st, i) => {
                  const Icon = STAGE_ICON[st.status] || Clock;
                  return (
                    <div key={i} data-testid={`stage-${i}`} className="flex items-start gap-2 text-sm">
                      <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${st.status === "complete" ? "text-emerald-600" : st.status === "pending" ? "text-amber-600" : "text-royal"}`} />
                      <div>
                        <span className="font-semibold text-navy">{st.stage}</span>
                        {st.detail && <span className="text-muted-foreground"> — {st.detail}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 flex items-center gap-2">
                <button data-testid={`result-approve-${result.kr_id}`} onClick={() => decide(result.kr_id, "approve")} disabled={acting}
                  className="inline-flex items-center gap-1.5 bg-emerald-600 text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-60"><ThumbsUp className="w-4 h-4" /> Approve → Enterprise Memory™</button>
                <button data-testid={`result-view-${result.kr_id}`} onClick={() => nav(`/kr2`)} className="inline-flex items-center gap-1.5 border border-navy/20 text-navy px-4 py-2 rounded-md text-sm font-medium">Review sections <ArrowRight className="w-4 h-4" /></button>
              </div>
            </Panel>
          )}
        </div>

        {/* The Standard */}
        <Panel title={standard.standard.title} icon={Quote} accent="gold" testid="kr-standard">
          <p className="text-[11px] text-muted-foreground mb-3">Every manufactured Knowledge Record™ is governed by these principles.</p>
          <ol className="space-y-2">
            {standard.standard.principles.map((p, i) => (
              <li key={i} data-testid={`principle-${i}`} className="flex items-start gap-2 text-[13px] text-navy">
                <span className="w-5 h-5 shrink-0 rounded-full bg-gold/20 text-navy text-[10px] font-bold flex items-center justify-center">{i + 1}</span>
                <span>{p}</span>
              </li>
            ))}
          </ol>
        </Panel>
      </div>

      {/* Pending Founder Review */}
      <div id="pending-review" className="mt-8">
        <Panel title="Pending Your Review" icon={ShieldCheck} accent="royal" testid="kr-pending">
          {pending.length === 0 ? (
            <p className="text-sm text-muted-foreground">No Knowledge Records are awaiting review. Manufacture one above.</p>
          ) : (
            <div className="space-y-3" data-testid="pending-list">
              {pending.map((kr) => (
                <div key={kr.id} data-testid={`pending-${kr.id}`} className="border border-border rounded-md p-3">
                  <div className="flex items-start justify-between flex-wrap gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-[10px] text-muted-foreground">{kr.kr_code}</span>
                        <p className="font-bold text-navy text-sm">{kr.title}</p>
                        <StatusChip status={`${kr.confidence_score || 0}% confidence`} tone={(kr.confidence_score || 0) >= 80 ? "emerald" : "amber"} />
                        <StatusChip status={kr.category || "General"} tone="navy" />
                      </div>
                      <p className="text-[12px] text-muted-foreground mt-1 line-clamp-2">{kr.verified_truth}</p>
                      {(kr.references || []).length > 0 && (
                        <p className="text-[10px] text-muted-foreground mt-1"><b>Sources:</b> {(kr.references || []).slice(0, 3).join(" · ")}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button data-testid={`approve-${kr.id}`} onClick={() => decide(kr.id, "approve")} disabled={acting === kr.id + "approve"}
                        className="inline-flex items-center gap-1 bg-emerald-600 text-white px-3 py-1.5 rounded-sm text-[11px] font-bold disabled:opacity-60">
                        {acting === kr.id + "approve" ? <Loader2 className="w-3 h-3 animate-spin" /> : <ThumbsUp className="w-3 h-3" />} Approve
                      </button>
                      <button data-testid={`reject-${kr.id}`} onClick={() => decide(kr.id, "reject")} disabled={acting === kr.id + "reject"}
                        className="inline-flex items-center gap-1 border border-red-300 text-red-600 px-3 py-1.5 rounded-sm text-[11px] font-medium disabled:opacity-60"><ThumbsDown className="w-3 h-3" /> Reject</button>
                      <button data-testid={`open-${kr.id}`} onClick={() => nav(`/knowledge/${kr.id}`)} className="inline-flex items-center gap-1 border border-navy/20 text-navy px-3 py-1.5 rounded-sm text-[11px]"><BookOpen className="w-3 h-3" /> Open</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
