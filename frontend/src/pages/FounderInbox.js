import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/shared";
import { toast } from "sonner";
import {
  Loader2, Inbox, CheckCircle2, Eye, Download, FileText, Gauge, RotateCcw, Archive, EyeOff,
  ShieldCheck, X, AlertTriangle, Store, Sparkles, Wrench,
  FileSearch, Pencil, ShieldQuestion, Ban, ExternalLink, BookOpen, Image as ImageIcon, Package,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const abs = (u) => (u ? (u.startsWith("http") ? u : `${BACKEND}${u}`) : null);

const FILTERS = [
  { key: "ready_for_review", label: "Ready for Review" },
  { key: "needs_founder_decision", label: "Needs Founder Decision" },
  { key: "ready_for_store", label: "Ready for Store" },
  { key: "needs_design_fix", label: "Needs Design Fix" },
  { key: "needs_knowledge_record", label: "Needs Knowledge Record" },
  { key: "needs_asset", label: "Needs Asset" },
  { key: "blocked", label: "Blocked" },
];

const HEALTH_STYLE = {
  ready: "bg-emerald-50 text-emerald-700 border-emerald-200",
  needs_metadata: "bg-amber-50 text-amber-700 border-amber-200",
  needs_assets: "bg-orange-50 text-orange-700 border-orange-200",
  needs_knowledge: "bg-blue-50 text-blue-700 border-blue-200",
  blocked: "bg-red-50 text-red-700 border-red-200",
};

export default function FounderInbox() {
  const [data, setData] = useState(null);
  const [filter, setFilter] = useState("ready_for_review");
  const [sel, setSel] = useState({});
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(null);
  const [ev, setEv] = useState(null); // Evidence-Based Decision Center™ dialog

  const load = () => api.get("/founder-inbox").then((r) => { setData(r.data); setSel({}); }).catch(() => {});
  useEffect(() => { load(); }, []);

  const openEvidence = async (pid) => {
    setEv({ loading: true });
    try { const { data: d } = await api.get(`/founder-inbox/${pid}/evidence`); setEv({ loading: false, d }); }
    catch (e) { setEv(null); toast.error("Could not load evidence"); }
  };

  const doAction = async (pid, action, note) => {
    setBusy(true);
    try {
      const { data: res } = await api.post(`/founder-inbox/${pid}/action`, { action, note });
      toast[res.ok ? "success" : "error"](res.message);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || "Action failed"); }
    finally { setBusy(false); }
  };

  const bulk = async (action) => {
    const ids = Object.keys(sel).filter((k) => sel[k]);
    if (ids.length === 0) return toast.error("Select at least one product");
    setBusy(true);
    try {
      const { data: res } = await api.post("/founder-inbox/bulk", { action, ids });
      toast.success(`${res.succeeded}/${res.processed} ${action}d`);
      load();
    } catch (e) { toast.error("Bulk action failed"); }
    finally { setBusy(false); }
  };

  const viewReport = async (pid) => {
    setReport({ loading: true });
    try { const { data: sc } = await api.get(`/design-director/score/${pid}`); setReport({ loading: false, sc }); }
    catch (e) { setReport(null); toast.error("Could not load design report"); }
  };

  if (!data) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  const items = data.products.filter((p) => p.filter_tags.includes(filter));
  const selCount = Object.values(sel).filter(Boolean).length;

  return (
    <div>
      <PageHeader
        overline="Founder Review Inbox™ · First Dollar Mode™"
        title="One Clean Approval Queue"
        description="Review, approve, publish, return, or archive completed products in one place. Nothing publishes without your approval — QRU governance, Treasure Standard™ and Product Protection™ are preserved."
      />

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-2 mb-4" data-testid="inbox-filters">
        {FILTERS.map((f) => (
          <button key={f.key} data-testid={`inbox-filter-${f.key}`} onClick={() => setFilter(f.key)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${filter === f.key ? "bg-primary text-primary-foreground border-primary" : "hover:border-primary"}`}>
            {f.label} <span className="opacity-70">({data.counts[f.key] || 0})</span>
          </button>
        ))}
      </div>

      {/* Bulk actions */}
      {selCount > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-4 p-3 bg-primary/[0.05] border rounded-md" data-testid="inbox-bulk-bar">
          <span className="text-sm font-medium mr-2">{selCount} selected</span>
          <button data-testid="bulk-approve" onClick={() => bulk("approve")} disabled={busy} className="flex items-center gap-1.5 text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded-sm hover:bg-primary/90 disabled:opacity-60"><Store className="w-3.5 h-3.5" /> Approve for Store</button>
          <button data-testid="bulk-return" onClick={() => bulk("return")} disabled={busy} className="flex items-center gap-1.5 text-xs border px-3 py-1.5 rounded-sm hover:border-primary"><RotateCcw className="w-3.5 h-3.5" /> Return for Improvement</button>
          <button data-testid="bulk-hide" onClick={() => bulk("hide")} disabled={busy} className="flex items-center gap-1.5 text-xs border px-3 py-1.5 rounded-sm hover:border-primary"><EyeOff className="w-3.5 h-3.5" /> Hide</button>
          <button data-testid="bulk-archive" onClick={() => bulk("archive")} disabled={busy} className="flex items-center gap-1.5 text-xs border px-3 py-1.5 rounded-sm hover:border-primary"><Archive className="w-3.5 h-3.5" /> Archive</button>
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState icon={Inbox} title="Nothing here" description="No products match this filter right now." />
      ) : (
        <div className="space-y-2" data-testid="inbox-list">
          {items.map((p) => {
            const primary = (p.customer_files || [])[0];
            const previewPdf = (p.customer_files || []).find(() => false); // placeholder
            return (
              <div key={p.id} className="bg-card border rounded-md p-4" data-testid={`inbox-row-${p.product_code}`}>
                <div className="flex items-start gap-3">
                  <input type="checkbox" data-testid={`inbox-check-${p.product_code}`} checked={!!sel[p.id]}
                    onChange={(e) => setSel({ ...sel, [p.id]: e.target.checked })} className="mt-1" />
                  <div className="w-12 h-14 rounded border overflow-hidden bg-muted shrink-0">
                    {p.cover_url && <img src={abs(p.cover_url)} alt="" className="w-full h-full object-cover" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-heading font-semibold">{p.title}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${HEALTH_STYLE[p.data_health] || "bg-muted"}`} title={(p.data_health_reasons || []).join(" · ")} data-testid={`inbox-health-${p.product_code}`}>{p.data_health_emoji} {p.data_health_label}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${p.confidence_band === "High" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : p.confidence_band === "Medium" ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-red-50 text-red-700 border-red-200"}`} data-testid={`inbox-confidence-${p.product_code}`}>Confidence {p.factory_confidence}%</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${p.design_passed ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`}>Design {p.design_score ?? "—"}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${p.treasure_standard ? "bg-gold/10 text-royal border-gold" : "bg-muted"}`}>TS™ {p.treasure_status}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full border">Market {p.marketplace_readiness}</span>
                      {p.preview_available && <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">Preview</span>}
                    </div>
                    <p className="text-[11px] text-muted-foreground mt-0.5">{p.product_code} · {p.product_type} · {p.category} · {p.status}</p>
                    {p.blockers.length > 0 && (
                      <p className="text-[11px] text-amber-700 mt-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> {p.blockers.join(" · ")}</p>
                    )}
                    {p.design_result && (
                      <p className="text-[11px] text-emerald-700 mt-1 flex items-center gap-1" data-testid={`inbox-autoimprove-${p.product_code}`}>
                        <Sparkles className="w-3 h-3" /> Autonomous improvements: {p.design_result.autonomous_improvements} pass(es) → Design {p.design_result.final_design_score}/{p.design_result.gold_standard}{p.design_result.passed ? " · Gold Standard ✓" : ""}
                      </p>
                    )}
                    {p.design_escalation && (
                      <p className="text-[11px] text-orange-700 mt-1 flex items-start gap-1" data-testid={`inbox-escalation-${p.product_code}`}>
                        <Wrench className="w-3 h-3 mt-0.5 shrink-0" /> <span><b>Founder input needed:</b> {p.design_escalation.stopped_reason} — {p.design_escalation.decision_needed}</span>
                      </p>
                    )}
                    {p.guidance && (
                      <div className="mt-1.5 flex items-center gap-2 text-[11px]" data-testid={`inbox-guidance-${p.product_code}`}>
                        <div className="h-1.5 w-20 bg-muted rounded-full overflow-hidden shrink-0"><div className="h-full bg-royal" style={{ width: `${p.guidance.progress_pct}%` }} /></div>
                        <span className="text-royal font-medium">{p.guidance.progress_pct}%</span>
                        <span className="text-muted-foreground">·</span>
                        <span className="text-navy"><b>Next:</b> {p.guidance.next_action}</span>
                        <span className={`px-1.5 py-0.5 rounded-full ${p.guidance.founder_action_required ? "bg-gold/20 text-royal" : "bg-emerald-50 text-emerald-700"}`}>{p.guidance.founder_action_required ? "You decide" : "Automatic"}</span>
                        {!p.guidance.founder_action_required && <span className="text-muted-foreground">→ then {p.guidance.after_completion}</span>}
                      </div>
                    )}
                    {/* Buttons */}
                    <div className="flex flex-wrap gap-2 mt-2">
                      {p.preview_url && <a data-testid={`inbox-preview-${p.product_code}`} href={`${BACKEND}/api/marketing/preview/${p.id}?fmt=html`} target="_blank" rel="noreferrer" className="text-xs flex items-center gap-1 border px-2 py-1 rounded-sm hover:border-primary"><Eye className="w-3.5 h-3.5" /> Open Preview</a>}
                      {primary && <a data-testid={`inbox-customer-${p.product_code}`} href={`${abs(primary.url)}?download=1&name=${encodeURIComponent(p.title)}`} className="text-xs flex items-center gap-1 border px-2 py-1 rounded-sm hover:border-primary"><Download className="w-3.5 h-3.5" /> Customer Edition</a>}
                      {p.preview_pdf_url && <a data-testid={`inbox-previewpdf-${p.product_code}`} href={`${BACKEND}/api/marketing/preview/${p.id}?fmt=pdf`} className="text-xs flex items-center gap-1 border px-2 py-1 rounded-sm hover:border-primary"><FileText className="w-3.5 h-3.5" /> Preview Edition</a>}
                      <button data-testid={`inbox-report-${p.product_code}`} onClick={() => viewReport(p.id)} className="text-xs flex items-center gap-1 border px-2 py-1 rounded-sm hover:border-primary"><Gauge className="w-3.5 h-3.5" /> Design Report</button>
                      <button data-testid={`inbox-evidence-${p.product_code}`} onClick={() => openEvidence(p.id)} className="text-xs flex items-center gap-1 bg-royal text-white px-2 py-1 rounded-sm hover:opacity-90"><FileSearch className="w-3.5 h-3.5" /> Review Evidence & Decide</button>
                    </div>
                  </div>
                  {/* Decision buttons */}
                  <div className="flex flex-col gap-1.5 shrink-0">
                    <button data-testid={`inbox-approve-${p.product_code}`} onClick={() => doAction(p.id, "approve")} disabled={busy}
                      className="flex items-center gap-1.5 text-xs bg-primary text-primary-foreground px-3 py-1.5 rounded-sm hover:bg-primary/90 disabled:opacity-60">
                      {p.publishable ? <Store className="w-3.5 h-3.5" /> : <ShieldCheck className="w-3.5 h-3.5" />} Approve for Store
                    </button>
                    <button data-testid={`inbox-return-${p.product_code}`} onClick={() => doAction(p.id, "return")} disabled={busy} className="flex items-center gap-1.5 text-xs border px-3 py-1.5 rounded-sm hover:border-primary"><RotateCcw className="w-3.5 h-3.5" /> Return</button>
                    <div className="flex gap-1.5">
                      <button data-testid={`inbox-hide-${p.product_code}`} onClick={() => doAction(p.id, "hide")} disabled={busy} className="flex-1 flex items-center justify-center gap-1 text-xs border px-2 py-1.5 rounded-sm hover:border-primary" title="Hide"><EyeOff className="w-3.5 h-3.5" /></button>
                      <button data-testid={`inbox-archive-${p.product_code}`} onClick={() => doAction(p.id, "archive")} disabled={busy} className="flex-1 flex items-center justify-center gap-1 text-xs border px-2 py-1.5 rounded-sm hover:border-primary" title="Archive"><Archive className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Design report modal */}
      {report && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setReport(null)} data-testid="inbox-report-modal">
          <div className="bg-card rounded-md max-w-xl w-full max-h-[85vh] overflow-y-auto p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3"><p className="font-heading font-semibold">Design Report</p><button onClick={() => setReport(null)}><X className="w-5 h-5 text-muted-foreground" /></button></div>
            {report.loading ? <div className="py-8 flex justify-center"><Loader2 className="w-5 h-5 animate-spin" /></div> : (
              <>
                <p className="font-heading text-3xl font-bold mb-3">{report.sc.overall}<span className="text-sm text-muted-foreground">/100 · needs {report.sc.passing_score}</span></p>
                <div className="space-y-1.5">
                  {report.sc.categories.map((c, i) => (
                    <div key={i} className="flex items-center justify-between text-sm border-b pb-1">
                      <span>{c.category}</span><span className={c.score >= 9 ? "text-emerald-600" : "text-amber-600"}>{c.score}/10</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}
      {/* MO-040 — Evidence-Based Decision Center™ */}
      {ev && (
        <EvidenceCenter ev={ev} busy={busy} onClose={() => setEv(null)}
          onDecide={async (pid, action, note) => { await doAction(pid, action, note); setEv(null); }} />
      )}
    </div>
  );
}

const DECISIONS = [
  { action: "approve", label: "Approve for Publication", icon: Store, cls: "bg-emerald-600 text-white hover:bg-emerald-700", desc: "Publishes to the QRU Store™ (only if all gates pass; otherwise records your approval and lists what remains)." },
  { action: "return", label: "Return to Factory", icon: RotateCcw, cls: "border hover:border-primary", desc: "Sends it back so Creative Studio™ and Design Director™ re-run automatically." },
  { action: "revise", label: "Request Revision", icon: Pencil, cls: "border hover:border-primary", desc: "Routes back for a specific correction and marks it Needs Revision." },
  { action: "verify", label: "Send to Verification", icon: ShieldQuestion, cls: "border hover:border-primary", desc: "Re-runs Product Protection™ verification before it returns to you." },
  { action: "reject", label: "Reject Product", icon: Ban, cls: "border border-red-300 text-red-700 hover:bg-red-50", desc: "Removes it from the manufacturing line entirely." },
];

const PREVIEW_ICON = {
  html: Eye, pdf: FileText, png: ImageIcon, mobile: Eye, print: FileText, marketplace: Store,
  thumbnail: ImageIcon, marketing: Sparkles, product_files: Package, source_assets: ImageIcon, knowledge_record: BookOpen,
};

function Ev({ label, value }) {
  return (
    <div className="border rounded-sm p-2">
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="text-sm text-navy font-medium">{value ?? "—"}</p>
    </div>
  );
}

function DisabledPreview({ pv, Icon }) {
  return (
    <div data-testid={`preview-${pv.key}`}
      className="flex items-start gap-2 border border-dashed rounded-sm px-2 py-2 text-xs bg-muted/40 opacity-70 cursor-not-allowed" title={pv.reason}>
      <Icon className="w-4 h-4 text-muted-foreground shrink-0" />
      <div className="min-w-0">
        <p className="truncate text-muted-foreground">{pv.label} · not ready</p>
        <p className="text-[10px] text-muted-foreground">{pv.reason}</p>
        <p className="text-[10px] text-royal/70 mt-0.5">Generated automatically during manufacturing.</p>
      </div>
    </div>
  );
}

function PreviewViewer({ viewer, onClose }) {
  const [loading, setLoading] = useState(true);
  const url = viewer.url;
  const ext = (url.split("?")[0].split(".").pop() || "").toLowerCase();
  const isImage = ["png", "jpg", "jpeg", "webp", "gif", "svg"].includes(ext);
  return (
    <div className="fixed inset-0 z-[60] bg-black/70 flex items-center justify-center p-4" onClick={onClose} data-testid="preview-viewer">
      <div className="bg-card rounded-md w-full max-w-4xl h-[88vh] flex flex-col overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-2.5 border-b shrink-0">
          <p className="font-heading font-semibold text-navy text-sm truncate">{viewer.title}</p>
          <div className="flex items-center gap-3 shrink-0">
            <a href={url} target="_blank" rel="noreferrer" className="text-xs text-royal inline-flex items-center gap-1 hover:underline" data-testid="preview-open-tab"><ExternalLink className="w-3.5 h-3.5" /> New tab</a>
            <button onClick={onClose} data-testid="preview-viewer-close"><X className="w-5 h-5 text-muted-foreground" /></button>
          </div>
        </div>
        <div className="relative flex-1 bg-muted/30">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center gap-2 text-sm text-muted-foreground" data-testid="preview-loading">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading preview…
            </div>
          )}
          {isImage ? (
            <div className="w-full h-full overflow-auto flex items-center justify-center p-4">
              <img src={url} alt={viewer.title} onLoad={() => setLoading(false)} className="max-w-full max-h-full object-contain" />
            </div>
          ) : (
            <iframe title={viewer.title} src={url} onLoad={() => setLoading(false)} className="w-full h-full border-0" />
          )}
        </div>
      </div>
    </div>
  );
}

function EvidenceCenter({ ev, busy, onClose, onDecide }) {
  const abs = (u) => (u ? (u.startsWith("http") ? u : `${BACKEND}${u}`) : null);
  const [reviseOpen, setReviseOpen] = useState(false);
  const [note, setNote] = useState("");
  const [viewer, setViewer] = useState(null);
  if (ev.loading) {
    return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" data-testid="evidence-center">
        <div className="bg-card rounded-md p-10"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
      </div>
    );
  }
  const d = ev.d;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="evidence-center">
      <div className="bg-card rounded-md max-w-4xl w-full max-h-[92vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="sticky top-0 bg-card border-b px-5 py-3 flex items-center justify-between z-10">
          <div>
            <p className="text-[11px] uppercase tracking-wide text-royal font-semibold">Evidence-Based Decision Center™</p>
            <p className="font-heading font-bold text-navy">{d.title}</p>
          </div>
          <button onClick={onClose} data-testid="evidence-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>

        <div className="p-5 space-y-5">
          {/* Recommendation banner */}
          <div className={`rounded-sm p-3 border ${d.publishable ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200"}`} data-testid="evidence-recommendation">
            <p className="text-xs font-semibold text-navy flex items-center gap-1.5"><Sparkles className="w-4 h-4 text-gold" /> AI Recommendation: {d.ai_recommendation}{d.ai_confidence != null ? ` · ${d.ai_confidence}% confidence` : ""}</p>
            <p className="text-[13px] text-navy mt-1"><b>Reason for escalation:</b> {d.escalation_reason}</p>
            <p className="text-[13px] text-navy"><b>Root cause:</b> {d.root_cause}</p>
            <p className="text-[13px] text-navy"><b>Recommended resolution:</b> {d.recommended_resolution}</p>
            {d.publish_blockers?.length > 0 && (
              <p className="text-[12px] text-amber-800 mt-1 flex items-start gap-1"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" /> Still required before publication: {d.publish_blockers.join(" · ")}</p>
            )}
          </div>

          {/* The 17 evidence items */}
          <div>
            <p className="text-xs font-semibold text-navy mb-2">Product Evidence</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <Ev label="Product Type" value={d.product_type} />
              <Ev label="Status" value={d.product_status} />
              <Ev label="Recipe Used" value={d.recipe_used} />
              <Ev label="Design Score" value={`${d.design_score ?? "—"} / 91${d.design_passed ? " ✓" : ""}`} />
              <Ev label="Treasure Standard™" value={d.treasure_standard_status} />
              <Ev label="Factory Confidence™" value={`${d.factory_confidence}% (${d.confidence_band})`} />
              <Ev label="Data Health™" value={`${d.data_health_emoji} ${d.data_health_label}`} />
              <Ev label="Marketplace Readiness™" value={d.marketplace_readiness} />
              <Ev label="AI Confidence" value={d.ai_confidence != null ? `${d.ai_confidence}%` : "—"} />
            </div>
          </div>

          {/* Knowledge Record + Manufacturing Report */}
          <div className="grid sm:grid-cols-2 gap-3">
            <div className="border rounded-sm p-3" data-testid="evidence-kr">
              <p className="text-xs font-semibold text-navy mb-1 flex items-center gap-1.5"><BookOpen className="w-3.5 h-3.5 text-royal" /> Knowledge Record</p>
              {d.knowledge_record ? (
                <div className="text-[13px] text-navy space-y-0.5">
                  <p>{d.knowledge_record.code} · {d.knowledge_record.title}</p>
                  <p className="text-muted-foreground text-xs">Verification: {d.knowledge_record.verification_status || "—"} · Class: {d.knowledge_record.record_class || "—"}</p>
                </div>
              ) : <p className="text-[13px] text-amber-700">No Knowledge Record linked to this product.</p>}
            </div>
            <div className="border rounded-sm p-3" data-testid="evidence-mfg-report">
              <p className="text-xs font-semibold text-navy mb-1 flex items-center gap-1.5"><Gauge className="w-3.5 h-3.5 text-royal" /> Manufacturing Report</p>
              <div className="text-[12px] text-navy space-y-0.5">
                <p>Content: {d.manufacturing_report.content_chars} chars · Formats: {(d.manufacturing_report.formats_rendered || []).join(", ") || "none"}</p>
                <p>Deliverable: {d.manufacturing_report.deliverable_ready ? "rendered" : "not rendered"}{d.manufacturing_report.deliverable_validated ? " · validated" : ""} · Marketing kit: {d.manufacturing_report.marketing_kit_ready ? "ready" : "pending"}</p>
                <p>Autonomous improvements: {d.manufacturing_report.autonomous_improvements} pass(es){(d.manufacturing_report.improved_categories || []).length ? ` (${d.manufacturing_report.improved_categories.join(", ")})` : ""}</p>
              </div>
            </div>
          </div>

          {/* Verification notes */}
          {d.verification_notes && (d.verification_notes.decision || (d.verification_notes.issues || []).length > 0) && (
            <div className="border rounded-sm p-3" data-testid="evidence-verification">
              <p className="text-xs font-semibold text-navy mb-1 flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-royal" /> Verification Notes</p>
              <p className="text-[13px] text-navy">{d.verification_notes.reviewer} · {d.verification_notes.decision} — {d.verification_notes.reasons || "No issues noted."}</p>
              {(d.verification_notes.issues || []).length > 0 && (
                <ul className="text-[12px] text-amber-700 list-disc pl-5 mt-1">{d.verification_notes.issues.map((i, k) => <li key={k}>{i}</li>)}</ul>
              )}
            </div>
          )}

          {/* MO-041 — Self-Guiding Gate Ladder™ + What Happens Next? */}
          {d.gate_ladder && (
            <div className="border rounded-sm p-3" data-testid="evidence-ladder">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-navy">Manufacturing Gates — {d.gate_ladder.progress_pct}% complete</p>
                <span className="text-[11px] text-muted-foreground">{d.gate_ladder.current_gate}</span>
              </div>
              <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden mb-3"><div className="h-full bg-royal" style={{ width: `${d.gate_ladder.progress_pct}%` }} /></div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {d.gate_ladder.gates.map((g) => (
                  <span key={g.key} className={`text-[11px] px-2 py-0.5 rounded-full border ${g.status === "complete" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : g.status === "active" ? "bg-amber-50 text-amber-700 border-amber-200" : g.status === "blocked" ? "bg-red-50 text-red-700 border-red-200" : "bg-muted text-muted-foreground"}`}>{g.emoji} {g.label}</span>
                ))}
              </div>
              <div className="bg-royal/5 rounded-sm p-3 grid sm:grid-cols-2 gap-x-4 gap-y-1 text-[13px]" data-testid="whats-next">
                <p className="sm:col-span-2 text-[11px] uppercase tracking-wide text-royal font-semibold">What Happens Next?</p>
                <p><b>Current activity:</b> {d.gate_ladder.current_status}</p>
                <p><b>Mode:</b> {d.gate_ladder.mode}</p>
                <p><b>Blocker:</b> {d.gate_ladder.current_blocker || "None"}</p>
                <p><b>Est. time:</b> {d.gate_ladder.estimated_seconds > 0 ? `~${d.gate_ladder.estimated_seconds}s` : "—"}</p>
                <p className="sm:col-span-2"><b>Recommendation:</b> {d.gate_ladder.ai_recommendation}</p>
                <p className="sm:col-span-2"><b>After completion:</b> {d.gate_ladder.after_completion} {d.gate_ladder.auto_continue ? "(continues automatically)" : ""}</p>
                <p className="sm:col-span-2"><b>Founder action required?</b> {d.gate_ladder.founder_action_required ? "Yes — your decision below." : "No — the factory handles it."}</p>
              </div>
            </div>
          )}

          {/* Autonomous Improvement — Before vs After */}
          {d.before_after && (
            <div className="border rounded-sm p-3" data-testid="evidence-before-after">
              <p className="text-xs font-semibold text-navy mb-2 flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5 text-gold" /> Autonomous Improvement — Before vs After</p>
              {d.before_after.iterations > 0 ? (
                <>
                  <div className="flex items-center gap-3 mb-2 text-sm">
                    <span className="text-muted-foreground">Overall design</span>
                    <span className="font-heading font-bold text-amber-600">{d.before_after.before_score}</span>
                    <span className="text-muted-foreground">→</span>
                    <span className="font-heading font-bold text-emerald-600">{d.before_after.after_score}</span>
                    <span className={`text-[11px] px-1.5 py-0.5 rounded-full ${d.before_after.score_delta > 0 ? "bg-emerald-50 text-emerald-700" : "bg-muted"}`}>{d.before_after.score_delta >= 0 ? "+" : ""}{d.before_after.score_delta}</span>
                    <span className="text-[11px] text-muted-foreground ml-auto">{d.before_after.iterations} improvement pass(es)</span>
                  </div>
                  <div className="space-y-1">
                    {d.before_after.categories.filter((c) => c.delta !== 0).length === 0 ? (
                      <p className="text-[12px] text-muted-foreground">Overall score improved across passes; category grades held steady.</p>
                    ) : d.before_after.categories.filter((c) => c.delta !== 0).map((c, k) => (
                      <div key={k} className="flex items-center gap-2 text-[12px] border-b pb-1">
                        <span className="flex-1 text-navy">{c.category}</span>
                        <span className="text-amber-600">{c.before}/10</span>
                        <span className="text-muted-foreground">→</span>
                        <span className="text-emerald-600 font-medium">{c.after}/10</span>
                        <span className="text-[10px] px-1 rounded bg-emerald-50 text-emerald-700">+{c.delta}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-[12px] text-emerald-700">Passed on first inspection ({d.before_after.after_score}/100) — no automated repairs were needed.</p>
              )}
            </div>
          )}

          {/* Preview section — see exactly what the customer receives (in-app viewer, instant feedback) */}
          <div>
            <p className="text-xs font-semibold text-navy mb-2">What the Customer Will Receive</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2" data-testid="evidence-previews">
              {d.previews.map((pv) => {
                const Icon = PREVIEW_ICON[pv.key] || FileText;
                const files = pv.files || [];
                const hasFiles = files.length > 0;
                // Knowledge Record links to the Promotion Pipeline; others open in the viewer.
                if (pv.key === "knowledge_record") {
                  const kr = d.knowledge_record;
                  return kr ? (
                    <button key={pv.key} data-testid={`preview-${pv.key}`} onClick={() => window.location.assign("/promotion-pipeline")}
                      className="flex items-center gap-2 border rounded-sm px-2 py-2 text-xs hover:border-primary text-left">
                      <Icon className="w-4 h-4 text-royal shrink-0" /><span className="flex-1 truncate">Knowledge Record · {kr.code}</span><ExternalLink className="w-3 h-3 text-muted-foreground" />
                    </button>
                  ) : (
                    <DisabledPreview key={pv.key} pv={pv} Icon={Icon} />
                  );
                }
                if (pv.available && pv.url) {
                  return (
                    <button key={pv.key} data-testid={`preview-${pv.key}`} onClick={() => setViewer({ url: abs(pv.url), title: pv.label })}
                      className="flex items-center gap-2 border rounded-sm px-2 py-2 text-xs hover:border-primary text-left transition-colors" title={`Open ${pv.label}`}>
                      <Icon className="w-4 h-4 text-royal shrink-0" /><span className="flex-1 truncate">{pv.label}</span><Eye className="w-3.5 h-3.5 text-royal shrink-0" />
                    </button>
                  );
                }
                if (pv.available && hasFiles) {
                  return (
                    <div key={pv.key} data-testid={`preview-${pv.key}`} className="border rounded-sm px-2 py-2 text-xs">
                      <p className="flex items-center gap-2 mb-1"><Icon className="w-4 h-4 text-royal shrink-0" /><span className="truncate">{pv.label} ({files.length})</span></p>
                      <div className="flex flex-wrap gap-1">
                        {files.slice(0, 6).map((f, k) => (
                          <button key={k} data-testid={`preview-${pv.key}-file-${k}`} onClick={() => setViewer({ url: abs(f.url), title: f.label || f.format || `${pv.label} ${k + 1}` })}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-royal/10 text-royal hover:bg-royal/20 truncate max-w-[110px] inline-flex items-center gap-1">
                            <Eye className="w-3 h-3" />{f.label || f.format || `file ${k + 1}`}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                }
                return <DisabledPreview key={pv.key} pv={pv} Icon={Icon} />;
              })}
            </div>
            <p className="text-[10px] text-muted-foreground mt-1.5">Greyed items aren't ready yet — the factory generates them automatically during manufacturing.</p>
          </div>
          {viewer && <PreviewViewer viewer={viewer} onClose={() => setViewer(null)} />}

          {/* Decisions */}
          <div className="border-t pt-4">
            <p className="text-xs font-semibold text-navy mb-2">Your Decision</p>
            <div className="grid sm:grid-cols-2 gap-2" data-testid="evidence-decisions">
              {DECISIONS.map((b) => (
                <button key={b.action} data-testid={`decide-${b.action}`} disabled={busy}
                  onClick={() => { if (b.action === "revise") { setReviseOpen((v) => !v); } else { onDecide(d.id, b.action); } }}
                  className={`text-left rounded-sm px-3 py-2.5 text-sm flex items-start gap-2 disabled:opacity-60 ${b.cls} ${b.action === "revise" && reviseOpen ? "ring-2 ring-royal" : ""}`}>
                  <b.icon className="w-4 h-4 mt-0.5 shrink-0" />
                  <span><span className="font-semibold block">{b.label}</span><span className="text-[11px] opacity-80">{b.desc}</span></span>
                </button>
              ))}
            </div>
            {reviseOpen && (
              <div className="mt-3 border rounded-sm p-3 bg-muted/30" data-testid="revise-note-panel">
                <label className="text-xs font-semibold text-navy">Revision note (optional) — tell the factory exactly what to correct</label>
                <textarea data-testid="revise-note-input" value={note} onChange={(e) => setNote(e.target.value)} rows={3}
                  placeholder="e.g. Tighten the intro, use the updated cover, expand the practice section…"
                  className="w-full mt-1 border rounded-sm p-2 text-sm" />
                <div className="flex gap-2 mt-2">
                  <button data-testid="revise-confirm" disabled={busy} onClick={() => onDecide(d.id, "revise", note.trim() || null)}
                    className="inline-flex items-center gap-1.5 bg-royal text-white text-sm px-3 py-1.5 rounded-sm disabled:opacity-60">
                    <Pencil className="w-3.5 h-3.5" /> Send Revision Request
                  </button>
                  <button data-testid="revise-cancel" onClick={() => { setReviseOpen(false); setNote(""); }} className="text-sm border px-3 py-1.5 rounded-sm hover:border-primary">Cancel</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
