import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, Gavel, CheckCircle2, XCircle, ShieldCheck, Rocket, History, Settings2, RefreshCw,
} from "lucide-react";

const DESTINATIONS = ["qru_online", "etsy", "amazon_kdp", "tpt", "shopify"];
const MODES = ["Export Only", "Review Ready", "Authorized Auto Publish", "Scheduled Publish", "Enterprise Workflow", "Disabled"];
const DECISION_TONE = {
  AUTHORIZED: "bg-emerald-100 text-emerald-700", REVIEW_READY: "bg-blue-100 text-blue-700",
  EXPORT_ONLY: "bg-muted text-muted-foreground", BLOCKED: "bg-red-100 text-red-700",
};

function Badge({ tone, children }) {
  return <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold ${tone || "bg-muted text-muted-foreground"}`}>{children}</span>;
}

export default function PublicationGovernance() {
  const [books, setBooks] = useState([]);
  const [sel, setSel] = useState("");
  const [decisions, setDecisions] = useState({});
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState("");
  const [ov, setOv] = useState({ scope: "product", destination: "etsy", mode: "Authorized Auto Publish", reason: "" });

  useEffect(() => {
    api.get("/book-mfg/books").then(({ data }) => setBooks(data.books || [])).catch(() => {});
  }, []);

  const load = useCallback(async (id) => {
    if (!id) return;
    setBusy("load");
    try {
      const results = await Promise.all(DESTINATIONS.map((d) =>
        api.get(`/publication/decide/book/${id}`, { params: { destination: d } }).then((r) => [d, r.data]).catch(() => [d, null])));
      setDecisions(Object.fromEntries(results));
      const h = await api.get("/publication/history", { params: { product_id: id } });
      setHistory(h.data.history || []);
    } finally { setBusy(""); }
  }, []);

  useEffect(() => { if (sel) load(sel); }, [sel, load]);

  const publish = async (dest) => {
    setBusy(`pub-${dest}`);
    try {
      const { data } = await api.post(`/publication/publish/book/${sel}`, { destination: dest });
      if (data.published) toast.success(`Published to ${dest} · ${data.verification?.status}`);
      else toast.error(`Not published — ${data.decision?.decision}: ${data.decision?.human_readable?.slice(0, 90)}`);
      await load(sel);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(""); }
  };

  const saveOverride = async () => {
    setBusy("ov");
    try {
      const scope_id = ov.scope === "product" ? sel : (ov.scope === "enterprise" ? "QRU" : ov.scope_id || "QRU");
      await api.post("/publication/policy", { ...ov, scope_id });
      toast.success(`Policy set: ${ov.destination} → ${ov.mode}`);
      await load(sel);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(""); }
  };

  return (
    <div className="space-y-6" data-testid="publication-governance-page">
      <PageHeader title="Publication Governance™" subtitle="Governed Publication Policy™ (STD-PUB-0001) — publishing is decided by inherited policy + constitutional requirements, never by code defaults." icon={Gavel} />

      <div className="rounded-lg border bg-card p-4">
        <label className="text-xs font-semibold text-navy uppercase tracking-wide">Product</label>
        <div className="mt-2 flex gap-3 items-center">
          <select data-testid="pg-product-select" value={sel} onChange={(e) => setSel(e.target.value)} className="block w-full rounded-md border px-3 py-2 text-sm">
            <option value="">Select a product…</option>
            {books.map((b) => <option key={b.id} value={b.id}>{b.book_code} — {b.title}</option>)}
          </select>
          {sel && <button data-testid="pg-refresh" onClick={() => load(sel)} className="inline-flex items-center gap-1 text-navy hover:underline text-sm"><RefreshCw className="w-4 h-4" /></button>}
        </div>
      </div>

      {sel && (
        <div className="grid gap-3" data-testid="pg-destinations">
          {DESTINATIONS.map((d) => {
            const dec = decisions[d];
            return (
              <div key={d} data-testid={`pg-dest-${d}`} className="rounded-lg border bg-card p-4">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-navy capitalize">{d.replace("_", " ")}</span>
                    {dec && <Badge tone="bg-navy/10 text-navy">{dec.policy?.effective_mode}</Badge>}
                    {dec && <Badge tone={DECISION_TONE[dec.decision]}>{dec.decision}</Badge>}
                    {dec?.policy && <span className="text-[11px] text-muted-foreground">from {dec.policy.resolved_from}</span>}
                  </div>
                  <button data-testid={`pg-publish-${d}`} onClick={() => publish(d)} disabled={busy === `pub-${d}` || !dec?.auto_publish_authorized}
                    title={dec?.auto_publish_authorized ? "" : "Auto-publish not authorized by policy/requirements"}
                    className="inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded text-[12px] font-semibold disabled:opacity-40">
                    {busy === `pub-${d}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Rocket className="w-3.5 h-3.5" />} Publish
                  </button>
                </div>
                {dec && (
                  <div className="mt-2 text-[12px]">
                    <div className="text-muted-foreground">{dec.human_readable}</div>
                    <div className="mt-2 flex flex-wrap gap-1">
                      <span className="text-[11px] text-emerald-700 font-semibold">✓ {dec.requirements?.satisfied?.length} passed</span>
                      {dec.requirements?.missing?.length > 0 && (
                        <span className="text-[11px] text-red-600 font-semibold ml-2" data-testid={`pg-missing-${d}`}>✗ Missing: {dec.requirements.missing.join(", ")}</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {sel && (
        <div className="rounded-lg border bg-card p-4" data-testid="pg-override">
          <h3 className="text-sm font-bold text-navy mb-3 flex items-center gap-2"><Settings2 className="w-4 h-4" /> Governed Policy Override</h3>
          <div className="flex flex-wrap gap-2 items-end">
            <div><label className="text-[11px] text-muted-foreground">Scope</label>
              <select data-testid="pg-ov-scope" value={ov.scope} onChange={(e) => setOv({ ...ov, scope: e.target.value })} className="block rounded border px-2 py-1 text-[12px]">
                <option value="enterprise">enterprise</option><option value="imprint">imprint</option><option value="product">product (this)</option></select></div>
            {ov.scope === "imprint" && <div><label className="text-[11px] text-muted-foreground">Imprint</label>
              <input data-testid="pg-ov-scopeid" value={ov.scope_id || ""} onChange={(e) => setOv({ ...ov, scope_id: e.target.value })} placeholder="QRU Press™" className="block rounded border px-2 py-1 text-[12px]" /></div>}
            <div><label className="text-[11px] text-muted-foreground">Destination</label>
              <select data-testid="pg-ov-dest" value={ov.destination} onChange={(e) => setOv({ ...ov, destination: e.target.value })} className="block rounded border px-2 py-1 text-[12px]">
                {DESTINATIONS.map((d) => <option key={d} value={d}>{d}</option>)}</select></div>
            <div><label className="text-[11px] text-muted-foreground">Mode</label>
              <select data-testid="pg-ov-mode" value={ov.mode} onChange={(e) => setOv({ ...ov, mode: e.target.value })} className="block rounded border px-2 py-1 text-[12px]">
                {MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></div>
            <button data-testid="pg-ov-save" onClick={saveOverride} disabled={busy === "ov"} className="inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded text-[12px] font-semibold">
              {busy === "ov" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />} Set Policy
            </button>
          </div>
        </div>
      )}

      {sel && (
        <div className="rounded-lg border bg-card p-4" data-testid="pg-history">
          <h3 className="text-sm font-bold text-navy mb-3 flex items-center gap-2"><History className="w-4 h-4" /> Publication History</h3>
          {history.length === 0 ? <p className="text-[12px] text-muted-foreground">No publication attempts yet.</p> : (
            <div className="space-y-1">
              {history.map((h) => (
                <div key={h.id} className="text-[12px] flex items-center gap-2 border-b py-1">
                  <Badge tone={DECISION_TONE[h.decision]}>{h.decision}</Badge>
                  <span className="capitalize font-semibold">{h.destination?.replace("_", " ")}</span>
                  <span className="text-muted-foreground">{h.result}</span>
                  {h.verification && <span className="text-emerald-700">· {h.verification.status}</span>}
                  <span className="ml-auto text-[10px] text-muted-foreground">{h.at?.slice(0, 19).replace("T", " ")}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
