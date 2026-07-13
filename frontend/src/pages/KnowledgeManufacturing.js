import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { Button } from "@/components/ui/button";
import { Loader2, Boxes, CheckCircle2, Clock, Rocket, MessageSquareHeart, ArrowRight, Factory, Download, Lock, Sparkles, TrendingUp } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

const API_BASE = process.env.REACT_APP_BACKEND_URL;

const STATE = {
  published: { tone: "gold", icon: Rocket, label: "Published" },
  manufactured: { tone: "emerald", icon: CheckCircle2, label: "Manufactured" },
  available: { tone: "slate", icon: Clock, label: "Available" },
  coming_soon: { tone: "amber", icon: Lock, label: "Coming Soon" },
};

export default function KnowledgeManufacturing() {
  const nav = useNavigate();
  const [krs, setKrs] = useState([]);
  const [sel, setSel] = useState(null);
  const [dash, setDash] = useState(null);
  const [loading, setLoading] = useState(false);
  const [batching, setBatching] = useState(false);
  const [busyKey, setBusyKey] = useState(null);

  useEffect(() => {
    api.get("/media-studio/knowledge-manufacturing").then((r) => {
      setKrs(r.data.knowledge_records || []);
      const v = r.data.knowledge_records?.find((k) => k.verified_external) || r.data.knowledge_records?.[0];
      if (v) selectKr(v.id);
    }).catch((e) => { console.error(e); toast.error("Could not load Knowledge Records."); });
  }, []);

  const selectKr = async (id) => {
    setSel(id); setLoading(true);
    try { const { data } = await api.get(`/media-studio/knowledge-manufacturing/${id}`); setDash(data); }
    catch (e) { console.error(e); toast.error("Could not load the manufacturing dashboard."); }
    finally { setLoading(false); }
  };

  const manufactureAll = async () => {
    if (!sel) return;
    setBatching(true);
    try {
      const { data } = await api.post(`/media-studio/knowledge-manufacturing/${sel}/manufacture-all`);
      const n = data.manufactured_count || 0;
      if (n > 0) toast.success(`Manufactured ${n} product${n === 1 ? "" : "s"} from the verified Knowledge Record.`);
      else toast.info("Everything available is already manufactured for this Knowledge Record.");
      await selectKr(sel);
    } catch (e) { console.error(e); toast.error(e?.response?.data?.detail || "Batch manufacture failed."); }
    finally { setBatching(false); }
  };

  const manufactureRecipe = async (recipe) => {
    if (!sel) return;
    setBusyKey(recipe);
    try {
      await api.post(`/media-studio/knowledge-manufacturing/${sel}/recipe/${recipe}`);
      toast.success("Product manufactured from the verified Knowledge Record.");
      await selectKr(sel);
    } catch (e) { console.error(e); toast.error(e?.response?.data?.detail || "Manufacture failed."); }
    finally { setBusyKey(null); }
  };

  return (
    <div data-testid="knowledge-manufacturing-page">
      <PageHeader
        overline="QRU Knowledge Record Inheritance™ · Single Source of Truth"
        title="Enterprise Manufacturing Dashboard"
        description="Understand Once. Manufacture Forever. Each verified Knowledge Record is a living dashboard — every product inherits its verified content automatically. Select a Record to govern its manufacturing."
        actions={<VerifiedBadge label="Knowledge-first manufacturing" testid="km-badge" />}
      />

      <div className="grid lg:grid-cols-[320px_1fr] gap-5">
        <Panel title="Verified Knowledge Records™" icon={Boxes} accent="royal" testid="km-kr-list">
          <div className="space-y-1.5 max-h-[640px] overflow-y-auto">
            {krs.map((k) => (
              <button key={k.id} onClick={() => selectKr(k.id)} data-testid={`km-kr-${k.id}`}
                className={`w-full text-left border rounded-md p-2.5 transition-colors ${sel === k.id ? "border-royal bg-royal/[0.04]" : "border-navy/10 hover:border-royal/50"}`}>
                <p className="text-[11px] font-bold text-navy truncate">{k.topic}</p>
                <p className="text-[9px] text-muted-foreground">{k.asset_count} product{k.asset_count === 1 ? "" : "s"} manufactured</p>
                <StatusChip status={k.verified_external ? "Verified Knowledge" : "Internal draft"} tone={k.verified_external ? "emerald" : "amber"} />
              </button>
            ))}
          </div>
        </Panel>

        <div className="space-y-4">
          {loading ? (
            <Panel title="Loading…" icon={Loader2} testid="km-loading"><Loader2 className="w-5 h-5 animate-spin text-royal" /></Panel>
          ) : dash ? (
            <>
              <Panel title={`${dash.kr.topic} — Living Manufacturing Dashboard`} icon={Boxes} accent="gold" testid="km-dashboard">
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <StatusChip status={dash.kr.verified_external ? "Single Source of Truth · Verified" : "Not externally verified"} tone={dash.kr.verified_external ? "emerald" : "amber"} />
                  <span className="text-[10px] text-muted-foreground">{dash.summary.product_types_manufactured}/{dash.summary.product_types_total} product types · {dash.summary.total_assets} assets</span>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 mb-4 border border-gold/40 bg-gold/[0.06] rounded-md p-3">
                  <div className="flex items-start gap-2">
                    <Factory className="w-4 h-4 text-gold mt-0.5" />
                    <div>
                      <p className="text-[12px] font-bold text-navy">Manufacture the complete product line</p>
                      <p className="text-[10px] text-muted-foreground">One click builds every available product that inherits this verified Knowledge Record. Unbuilt archetypes stay honestly "Coming Soon".</p>
                    </div>
                  </div>
                  <Button size="sm" onClick={manufactureAll} disabled={batching}
                    data-testid="km-manufacture-all-btn"
                    className="bg-navy hover:bg-navy/90 text-white text-[11px] h-8">
                    {batching ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : <Sparkles className="w-3.5 h-3.5 mr-1.5" />}
                    Manufacture Everything Available
                  </Button>
                </div>

                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                  {dash.matrix.map((m) => {
                    const st = STATE[m.state]; const Ic = st.icon;
                    const isComing = m.state === "coming_soon";
                    const hasFiles = (m.items || []).some((i) => i.download);
                    return (
                      <div key={m.key} data-testid={`km-product-${m.key}`}
                        className={`border rounded-md p-3 ${isComing ? "border-amber-200/60 bg-amber-50/30 opacity-90" : m.count > 0 ? "border-emerald-200 bg-emerald-50/40" : "border-navy/10"}`}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[12px] font-bold text-navy">{m.type}</span>
                          <Ic className={`w-4 h-4 ${m.count > 0 ? "text-emerald-600" : isComing ? "text-amber-500" : "text-muted-foreground/50"}`} />
                        </div>
                        <div className="flex items-center justify-between gap-2">
                          <StatusChip status={m.count > 0 ? `${st.label} · ${m.count}` : st.label} tone={st.tone} />
                          {m.recipe && m.count === 0 && (
                            <button onClick={() => manufactureRecipe(m.recipe)} disabled={busyKey === m.recipe}
                              data-testid={`km-make-${m.key}`}
                              className="text-[10px] text-navy font-semibold inline-flex items-center gap-0.5 hover:text-gold disabled:opacity-50">
                              {busyKey === m.recipe ? <Loader2 className="w-3 h-3 animate-spin" /> : <Factory className="w-3 h-3" />} Manufacture
                            </button>
                          )}
                          {m.route && (
                            <button onClick={() => nav(`${m.route}?kr=${sel}`)} data-testid={`km-go-${m.key}`} className="text-[10px] text-royal inline-flex items-center gap-0.5 hover:underline">
                              {m.count > 0 ? "Open" : "Manufacture"} <ArrowRight className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                        {hasFiles && (
                          <div className="mt-2 pt-2 border-t border-navy/10 space-y-1">
                            {m.items.filter((i) => i.download).map((i) => (
                              <a key={i.id} href={`${API_BASE}${i.download}`} target="_blank" rel="noreferrer"
                                data-testid={`km-download-${i.id}`}
                                className="text-[10px] text-royal inline-flex items-center gap-1 hover:underline">
                                <Download className="w-3 h-3" /> {i.label} PDF
                              </a>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Panel>

              <Panel title="Project Zero™ — Continuous Improvement Loop" icon={MessageSquareHeart} accent="royal" testid="km-project-zero">
                <p className="text-[11px] text-navy/70 mb-2">{dash.project_zero.note}</p>
                {dash.project_zero.feedback_count === 0 ? (
                  <div className="text-[11px] text-muted-foreground border border-dashed border-navy/15 rounded-md p-3 text-center" data-testid="km-pz-empty">
                    No customer feedback yet. After publication, feedback & learning metrics return here and improve this Knowledge Record — and every future product it manufactures.
                  </div>
                ) : (
                  <div className="space-y-3" data-testid="km-pz-data">
                    <div className="grid grid-cols-3 gap-2">
                      <div className="border border-navy/10 rounded-md p-2 text-center">
                        <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Feedback</p>
                        <p className="text-[16px] font-bold text-navy">{dash.project_zero.aggregate.feedback_count}</p>
                      </div>
                      <div className="border border-navy/10 rounded-md p-2 text-center">
                        <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Avg Rating</p>
                        <p className="text-[16px] font-bold text-navy">{dash.project_zero.aggregate.avg_rating ?? "—"}</p>
                      </div>
                      <div className="border border-navy/10 rounded-md p-2 text-center">
                        <p className="text-[9px] text-muted-foreground uppercase tracking-wide">Understanding Gain</p>
                        <p className="text-[16px] font-bold text-emerald-600 inline-flex items-center gap-0.5">
                          {dash.project_zero.aggregate.avg_understanding_gain != null && <TrendingUp className="w-3.5 h-3.5" />}
                          {dash.project_zero.aggregate.avg_understanding_gain ?? "—"}
                        </p>
                      </div>
                    </div>
                    {(dash.project_zero.aggregate.improvement_signals || []).length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {dash.project_zero.aggregate.improvement_signals.map((s, i) => (
                          <span key={i} className="text-[10px] bg-royal/[0.06] text-royal border border-royal/20 rounded-full px-2 py-0.5">
                            {s.signal} · {s.mentions}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="space-y-1.5">
                      {dash.project_zero.feedback.map((f, i) => (
                        <div key={i} className="text-[11px] text-navy border-l-2 border-royal pl-2">{f.summary || f.comment || f.suggested_improvement}</div>
                      ))}
                    </div>
                  </div>
                )}
                <p className="text-[10px] text-gold font-bold mt-3 tracking-wide">UNDERSTAND ONCE. MANUFACTURE FOREVER.</p>
              </Panel>
            </>
          ) : (
            <Panel title="Select a Knowledge Record" icon={Boxes} testid="km-empty">
              <p className="text-[12px] text-navy/80">Choose a verified Knowledge Record to see everything manufactured from it and what remains.</p>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
