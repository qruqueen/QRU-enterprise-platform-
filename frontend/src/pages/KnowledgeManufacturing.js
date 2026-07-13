import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { Loader2, Boxes, CheckCircle2, Clock, Rocket, MessageSquareHeart, ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

const STATE = {
  published: { tone: "gold", icon: Rocket, label: "Published" },
  manufactured: { tone: "emerald", icon: CheckCircle2, label: "Manufactured" },
  available: { tone: "slate", icon: Clock, label: "Available" },
};

export default function KnowledgeManufacturing() {
  const nav = useNavigate();
  const [krs, setKrs] = useState([]);
  const [sel, setSel] = useState(null);
  const [dash, setDash] = useState(null);
  const [loading, setLoading] = useState(false);

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
                <p className="text-[9px] text-muted-foreground">{k.kr_code} · v{k.version} · {k.asset_count} assets</p>
                <StatusChip status={k.verified_external ? "Verified External" : "Internal draft"} tone={k.verified_external ? "emerald" : "amber"} />
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
                  <span className="text-[11px] font-bold text-navy">{dash.kr.kr_code} · v{dash.kr.version}</span>
                  <StatusChip status={dash.kr.verified_external ? "Single Source of Truth · Verified" : "Not externally verified"} tone={dash.kr.verified_external ? "emerald" : "amber"} />
                  <span className="text-[10px] text-muted-foreground">{dash.summary.product_types_manufactured}/{dash.summary.product_types_total} product types · {dash.summary.total_assets} assets</span>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                  {dash.matrix.map((m) => {
                    const st = STATE[m.state]; const Ic = st.icon;
                    return (
                      <div key={m.key} data-testid={`km-product-${m.key}`}
                        className={`border rounded-md p-3 ${m.count > 0 ? "border-emerald-200 bg-emerald-50/40" : "border-navy/10"}`}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[12px] font-bold text-navy">{m.type}</span>
                          <Ic className={`w-4 h-4 ${m.count > 0 ? "text-emerald-600" : "text-muted-foreground/50"} ${st.icon === Loader2 ? "animate-spin" : ""}`} />
                        </div>
                        <div className="flex items-center justify-between">
                          <StatusChip status={m.count > 0 ? `${st.label} · ${m.count}` : "Available"} tone={st.tone} />
                          {m.route && (
                            <button onClick={() => nav(m.route)} data-testid={`km-go-${m.key}`} className="text-[10px] text-royal inline-flex items-center gap-0.5 hover:underline">
                              {m.count > 0 ? "Open" : "Manufacture"} <ArrowRight className="w-3 h-3" />
                            </button>
                          )}
                        </div>
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
                  <div className="space-y-1.5">
                    {dash.project_zero.feedback.map((f, i) => (
                      <div key={i} className="text-[11px] text-navy border-l-2 border-royal pl-2">{f.summary || JSON.stringify(f)}</div>
                    ))}
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
