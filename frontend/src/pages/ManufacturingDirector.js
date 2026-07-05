import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { MetricCard, Panel, StatusChip, ScoreBar, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, X, Gavel, CheckCircle2, PauseCircle, XCircle, AlertTriangle, BookOpenCheck,
  Sparkles, ChevronRight, Layers, ShieldCheck, ArrowRight,
} from "lucide-react";

const VERDICT_TONE = {
  APPROVE: "emerald",
  APPROVE_WITH_CONDITIONS: "gold",
  HOLD: "amber",
  REJECT: "red",
};
const VERDICT_ICON = {
  APPROVE: CheckCircle2,
  APPROVE_WITH_CONDITIONS: ShieldCheck,
  HOLD: PauseCircle,
  REJECT: XCircle,
};

function ReviewPanel({ orderId, onClose, onApplied }) {
  const [r, setR] = useState(null);
  const [useAi, setUseAi] = useState(false);
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const load = (ai) => {
    setR(null);
    api.get(`/director/review/${orderId}?use_ai=${ai ? "true" : "false"}`).then((res) => setR(res.data)).catch(() => setR(false));
  };
  useEffect(() => { load(false); /* eslint-disable-next-line */ }, [orderId]);

  const apply = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/director/review/${orderId}/decision`);
      toast.success(`Director decision applied — order moved to ${data.new_status}`);
      onApplied();
      onClose();
    } catch (e) { toast.error(e.response?.data?.detail || "Could not apply decision"); }
    finally { setBusy(false); }
  };

  const Icon = r ? (VERDICT_ICON[r.verdict] || Gavel) : Gavel;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="director-review-panel">
      <div className="bg-card rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Gavel className="w-4 h-4 text-royal" />
            <p className="font-heading font-bold text-navy">Director Review</p>
            {r && <StatusChip status={r.verdict.replace(/_/g, " ")} tone={VERDICT_TONE[r.verdict]} testid="director-verdict-chip" />}
          </div>
          <button onClick={onClose} data-testid="director-review-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>

        <div className="p-5 overflow-auto">
          {!r ? <div className="flex items-center gap-2 text-sm text-muted-foreground py-10"><Loader2 className="w-4 h-4 animate-spin" /> Director is reviewing…</div>
            : r === false ? <p className="text-sm text-muted-foreground">Could not load the review.</p>
            : (
              <>
                <div className="flex items-start gap-3 mb-4">
                  <Icon className={`w-8 h-8 shrink-0 ${r.verdict === "APPROVE" ? "text-emerald-600" : r.verdict === "REJECT" ? "text-red-600" : r.verdict === "HOLD" ? "text-amber-600" : "text-navy"}`} />
                  <div>
                    <p className="font-heading text-xl font-bold text-navy leading-tight" data-testid="director-verdict-label">{r.verdict_label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{r.mo_code} · {r.topic}</p>
                  </div>
                  <div className="ml-auto text-right">
                    <p className="font-heading text-3xl font-bold text-navy leading-none">{r.confidence}%</p>
                    <p className="text-[10px] uppercase tracking-wide text-muted-foreground">confidence</p>
                  </div>
                </div>

                {/* Executive brief */}
                <div className="mb-4 rounded-md border border-royal/25 bg-royal/[0.04] p-4 qru-royalline" data-testid="director-brief">
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="overline text-royal flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> Executive Brief</p>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded border bg-muted text-muted-foreground border-border">{r.brief_source === "ai" ? "AI" : "$0 DETERMINISTIC"}</span>
                  </div>
                  <p className="text-sm text-navy leading-relaxed">{r.executive_brief}</p>
                  <button data-testid="director-ai-brief-btn" onClick={() => { setUseAi(true); load(true); }} disabled={r.brief_source === "ai"}
                    className="mt-2 text-[11px] inline-flex items-center gap-1 text-royal font-semibold disabled:opacity-40">
                    <Sparkles className="w-3 h-3" /> {r.brief_source === "ai" ? "AI brief generated" : "Request AI brief"}
                  </button>
                </div>

                {/* Knowledge Record */}
                {r.knowledge_record ? (
                  <button onClick={() => nav("/kr2")} data-testid="director-kr-link"
                    className="w-full text-left flex items-center gap-2 text-sm border rounded-md p-3 mb-4 hover:border-navy transition-colors">
                    <BookOpenCheck className="w-4 h-4 text-royal shrink-0" />
                    <span className="text-navy font-medium">{r.knowledge_record.kr_code} — {r.knowledge_record.title}</span>
                    <StatusChip status={r.knowledge_record.verification_status} />
                    {r.knowledge_record.source === "matched_by_topic" && <span className="text-[10px] text-amber-600">(matched by topic)</span>}
                    <ChevronRight className="w-4 h-4 text-muted-foreground ml-auto" />
                  </button>
                ) : (
                  <div className="text-sm border border-red-200 bg-red-50 rounded-md p-3 mb-4 text-red-800 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" /> No verified Knowledge Record is linked or matched for this topic.
                  </div>
                )}

                {/* Reasons */}
                {r.reasons?.length > 0 && (
                  <div className="mb-4">
                    <p className="overline text-navy mb-2">Director Reasoning</p>
                    <ul className="space-y-1" data-testid="director-reasons">
                      {r.reasons.map((x, i) => <li key={i} className="text-xs text-muted-foreground flex gap-1.5"><span className="text-royal">•</span>{x}</li>)}
                    </ul>
                  </div>
                )}

                {/* Missing knowledge */}
                {r.missing_knowledge?.length > 0 && (
                  <div className="mb-4">
                    <p className="overline text-navy mb-2 flex items-center gap-1.5"><Layers className="w-3.5 h-3.5" /> Missing Knowledge ({r.missing_knowledge.length})</p>
                    <div className="space-y-1.5" data-testid="director-missing-knowledge">
                      {r.missing_knowledge.map((m, i) => (
                        <div key={i} className="flex items-center gap-2 text-xs border rounded-sm p-2">
                          <XCircle className="w-3.5 h-3.5 text-red-500 shrink-0" />
                          <span className="text-navy font-medium">{m.section}</span>
                          <span className="text-muted-foreground">· needed by {m.needed_by.join(", ")}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Readiness by product */}
                {r.readiness_by_product?.length > 0 && (
                  <div className="mb-4">
                    <p className="overline text-navy mb-2">Readiness by Product</p>
                    <div className="space-y-2" data-testid="director-readiness">
                      {r.readiness_by_product.map((p, i) => {
                        const pct = p.required.length ? Math.round(p.ready_sections.length / p.required.length * 100) : 100;
                        return (
                          <div key={i} className="border rounded-sm p-2.5">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-semibold text-navy">{p.product_type}</span>
                              <StatusChip status={p.manufacturing_allowed ? "Ready" : "Paused"} />
                            </div>
                            <ScoreBar score={pct} showLabel={false} />
                            <p className="text-[10px] text-muted-foreground mt-1">{p.ready_sections.length}/{p.required.length} required sections ready</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Recommended actions */}
                {r.recommended_actions?.length > 0 && (
                  <div className="mb-4">
                    <p className="overline text-navy mb-2">Recommended Actions</p>
                    <div className="space-y-1.5" data-testid="director-actions">
                      {r.recommended_actions.map((a, i) => (
                        <button key={i} onClick={() => nav(a.link)} className="w-full text-left flex items-center gap-2 text-xs border rounded-sm p-2 hover:border-navy transition-colors">
                          <ArrowRight className="w-3.5 h-3.5 text-royal shrink-0" />
                          <span className="text-navy">{a.label}</span>
                          <ChevronRight className="w-3.5 h-3.5 text-muted-foreground ml-auto" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
        </div>

        {r && r !== false && (
          <div className="p-4 border-t flex items-center justify-between gap-3">
            <p className="text-xs text-muted-foreground">Applying moves the order to <b className="text-navy">{r.recommended_status}</b>.</p>
            <button onClick={apply} disabled={busy} data-testid="director-apply-decision"
              className="text-sm inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm font-semibold disabled:opacity-60 hover:bg-navy/90 transition-colors">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Gavel className="w-4 h-4" />} Apply Director Decision
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ManufacturingDirector() {
  const [data, setData] = useState(null);
  const [active, setActive] = useState(null);
  const [filter, setFilter] = useState("all");

  const load = () => api.get("/director/queue").then((r) => setData(r.data)).catch(() => setData(false));
  useEffect(() => { load(); }, []);

  if (data === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (data === false) return <p className="text-sm text-muted-foreground p-8">Could not load the Director queue.</p>;

  const rows = data.orders.filter((o) =>
    filter === "all" ? true
      : filter === "cleared" ? (o.verdict === "APPROVE" || o.verdict === "APPROVE_WITH_CONDITIONS")
      : (o.verdict === "HOLD" || o.verdict === "REJECT"));

  return (
    <div>
      <PageHeader
        overline="QRU Manufacturing Director™ · Supervisory Review"
        title="Manufacturing Director"
        description="The Director reviews every manufacturing order before production — verifying the knowledge foundation, identifying exactly what's missing, and approving or holding each order. Every verdict is evidence-based and deterministic; AI only writes the brief, never the decision."
        actions={<VerifiedBadge label="Evidence-Based · $0 AI" testid="director-badge" />}
      />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <MetricCard testid="director-total" icon={Gavel} label="Orders Reviewed" value={data.total} />
        <MetricCard testid="director-cleared" icon={CheckCircle2} accent="gold" label="Cleared to Manufacture" value={data.cleared} sub={`${data.counts.APPROVE} approved · ${data.counts.APPROVE_WITH_CONDITIONS} conditional`} />
        <MetricCard testid="director-held" icon={PauseCircle} label="On Hold" value={data.counts.HOLD} sub="missing knowledge" />
        <MetricCard testid="director-rejected" icon={XCircle} label="Rejected" value={data.counts.REJECT} sub="no verified foundation" />
      </div>

      <div className="flex gap-2 mb-3" data-testid="director-filters">
        {["all", "cleared", "held"].map((f) => (
          <button key={f} onClick={() => setFilter(f)} data-testid={`director-filter-${f}`}
            className={`text-xs px-3.5 py-1.5 rounded-full border capitalize font-semibold transition-colors ${filter === f ? "bg-navy text-white border-navy" : "text-navy border-navy/25 hover:border-navy"}`}>{f}</button>
        ))}
      </div>

      <Panel testid="director-queue" className="overflow-hidden">
        <div className="overflow-x-auto -m-5">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr>{["Order", "Topic", "Products", "Verdict", "Confidence", "Missing", "Status"].map((h) => (
                <th key={h} className="text-left font-bold text-navy px-5 py-2.5 text-[11px] uppercase tracking-wide whitespace-nowrap">{h}</th>
              ))}</tr>
            </thead>
            <tbody>
              {rows.map((o) => (
                <tr key={o.order_id} className="border-t border-border hover:bg-muted/30 cursor-pointer transition-colors" onClick={() => setActive(o.order_id)} data-testid={`director-row-${o.mo_code}`}>
                  <td className="px-5 py-2.5 text-navy font-medium whitespace-nowrap">{o.mo_code}</td>
                  <td className="px-5 py-2.5 text-navy max-w-[280px] truncate">{o.topic}</td>
                  <td className="px-5 py-2.5 text-xs text-muted-foreground max-w-[160px] truncate">{o.product_types.join(", ") || "—"}</td>
                  <td className="px-5 py-2.5"><StatusChip status={o.verdict.replace(/_/g, " ")} tone={VERDICT_TONE[o.verdict]} /></td>
                  <td className="px-5 py-2.5 font-bold text-xs text-navy">{o.confidence}%</td>
                  <td className="px-5 py-2.5 text-xs text-muted-foreground">{o.missing_count || "—"}</td>
                  <td className="px-5 py-2.5 text-xs text-muted-foreground">{o.current_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {active && <ReviewPanel orderId={active} onClose={() => setActive(null)} onApplied={load} />}
    </div>
  );
}
