import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/shared";
import { toast } from "sonner";
import {
  Loader2, Inbox, CheckCircle2, Eye, Download, FileText, Gauge, RotateCcw, Archive, EyeOff,
  ShieldCheck, X, AlertTriangle, Store,
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

export default function FounderInbox() {
  const [data, setData] = useState(null);
  const [filter, setFilter] = useState("ready_for_review");
  const [sel, setSel] = useState({});
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(null);

  const load = () => api.get("/founder-inbox").then((r) => { setData(r.data); setSel({}); }).catch(() => {});
  useEffect(() => { load(); }, []);

  const doAction = async (pid, action) => {
    setBusy(true);
    try {
      const { data: res } = await api.post(`/founder-inbox/${pid}/action`, { action });
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
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${p.design_passed ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`}>Design {p.design_score ?? "—"}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${p.treasure_standard ? "bg-gold/10 text-royal border-gold" : "bg-muted"}`}>TS™ {p.treasure_status}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full border">Market {p.marketplace_readiness}</span>
                      {p.preview_available && <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">Preview</span>}
                    </div>
                    <p className="text-[11px] text-muted-foreground mt-0.5">{p.product_code} · {p.product_type} · {p.category} · {p.status}</p>
                    {p.blockers.length > 0 && (
                      <p className="text-[11px] text-amber-700 mt-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> {p.blockers.join(" · ")}</p>
                    )}
                    {/* Buttons */}
                    <div className="flex flex-wrap gap-2 mt-2">
                      {p.preview_url && <a data-testid={`inbox-preview-${p.product_code}`} href={`${BACKEND}/api/marketing/preview/${p.id}?fmt=html`} target="_blank" rel="noreferrer" className="text-xs flex items-center gap-1 border px-2 py-1 rounded-sm hover:border-primary"><Eye className="w-3.5 h-3.5" /> Open Preview</a>}
                      {primary && <a data-testid={`inbox-customer-${p.product_code}`} href={`${abs(primary.url)}?download=1&name=${encodeURIComponent(p.title)}`} className="text-xs flex items-center gap-1 border px-2 py-1 rounded-sm hover:border-primary"><Download className="w-3.5 h-3.5" /> Customer Edition</a>}
                      {p.preview_pdf_url && <a data-testid={`inbox-previewpdf-${p.product_code}`} href={`${BACKEND}/api/marketing/preview/${p.id}?fmt=pdf`} className="text-xs flex items-center gap-1 border px-2 py-1 rounded-sm hover:border-primary"><FileText className="w-3.5 h-3.5" /> Preview Edition</a>}
                      <button data-testid={`inbox-report-${p.product_code}`} onClick={() => viewReport(p.id)} className="text-xs flex items-center gap-1 border px-2 py-1 rounded-sm hover:border-primary"><Gauge className="w-3.5 h-3.5" /> Design Report</button>
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
    </div>
  );
}
