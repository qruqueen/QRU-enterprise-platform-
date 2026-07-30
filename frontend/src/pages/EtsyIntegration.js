import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, Store, Plug, PlugZap, Unplug, RefreshCw, CheckCircle2, AlertTriangle,
  Eye, FilePlus, ExternalLink, GitCompare, UploadCloud, ShieldCheck,
} from "lucide-react";

const STATUS_TONE = {
  connected: "bg-emerald-100 text-emerald-700",
  disconnected: "bg-muted text-muted-foreground",
  expired: "bg-amber-100 text-amber-700",
  error: "bg-red-100 text-red-700",
};

function Stat({ label, value }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="text-2xl font-bold text-navy">{value}</div>
      <div className="text-[11px] mt-1 text-muted-foreground">{label}</div>
    </div>
  );
}

export default function EtsyIntegration() {
  const [params, setParams] = useSearchParams();
  const [status, setStatus] = useState(null);
  const [products, setProducts] = useState([]);
  const [busy, setBusy] = useState("");
  const [test, setTest] = useState(null);
  const [preview, setPreview] = useState(null);

  const loadStatus = useCallback(async () => {
    const { data } = await api.get("/integrations/etsy/status");
    setStatus(data);
  }, []);

  const loadProducts = useCallback(async () => {
    const { data } = await api.get("/integrations/etsy/products");
    setProducts(data.products || []);
  }, []);

  useEffect(() => {
    loadStatus();
    loadProducts();
  }, [loadStatus, loadProducts]);

  useEffect(() => {
    if (params.get("connected") === "1") {
      toast.success(params.get("msg") || "Etsy connected.");
      loadStatus();
      setParams({});
    } else if (params.get("connected") === "0") {
      toast.error(params.get("msg") || "Etsy connection failed.");
      setParams({});
    }
  }, [params, setParams, loadStatus]);

  const connect = async () => {
    setBusy("connect");
    try {
      const { data } = await api.get("/integrations/etsy/connect");
      if (data.error) { toast.error(data.error); setBusy(""); return; }
      window.location.href = data.authorize_url; // top-level redirect to Etsy consent
    } catch (e) {
      toast.error(e.response?.data?.detail || "Could not start Etsy connect.");
      setBusy("");
    }
  };

  const disconnect = async () => {
    if (!window.confirm("Disconnect the Etsy shop? Stored Etsy credentials will be deleted. Existing Etsy listings are NOT changed.")) return;
    setBusy("disconnect");
    try {
      await api.post("/integrations/etsy/disconnect");
      toast.success("Etsy disconnected.");
      await loadStatus();
    } catch (e) { toast.error("Disconnect failed."); }
    setBusy("");
  };

  const runTest = async () => {
    setBusy("test");
    try {
      const { data } = await api.post("/integrations/etsy/test");
      setTest(data);
      toast[data.ok ? "success" : "error"](data.ok ? "Connection OK." : "Connection test found issues.");
      await loadStatus();
    } catch (e) { toast.error(e.response?.data?.detail || "Test failed."); }
    setBusy("");
  };

  const doPreview = async (p) => {
    setBusy(`pv-${p.id}`);
    try {
      const { data } = await api.post(`/integrations/etsy/products/${p.id}/preview`);
      setPreview({ product: p, data });
    } catch (e) { toast.error(e.response?.data?.detail || "Preview failed."); }
    setBusy("");
  };

  const createDraft = async (p) => {
    if (!window.confirm(`Create an Etsy DRAFT listing for "${p.title}"? It will NOT be activated — you approve activation separately on Etsy.`)) return;
    setBusy(`draft-${p.id}`);
    try {
      const { data } = await api.post(`/integrations/etsy/products/${p.id}/publish`, { approved: true });
      if (data.error) toast.error(data.error);
      else toast.success(data.idempotent ? "Draft already exists (no duplicate)." : "Etsy draft created.");
      await loadProducts(); await loadStatus();
      if (preview?.product?.id === p.id) await doPreview(p);
    } catch (e) { toast.error(e.response?.data?.detail || "Draft creation failed."); }
    setBusy("");
  };

  const updateEtsy = async (p) => {
    setBusy(`upd-${p.id}`);
    try {
      const { data } = await api.patch(`/integrations/etsy/products/${p.id}`);
      toast[data.error ? "error" : "success"](data.error || "Etsy listing updated.");
      await loadProducts();
    } catch (e) { toast.error("Update failed."); }
    setBusy("");
  };

  const syncOne = async (p) => {
    setBusy(`sync-${p.id}`);
    try {
      const { data } = await api.post(`/integrations/etsy/products/${p.id}/sync`);
      toast.info(data.in_sync ? "In sync with Etsy." : (data.proposed || (data.proposed_changes || []).join("; ") || "Sync compared."));
    } catch (e) { toast.error("Sync failed."); }
    setBusy("");
  };

  if (!status) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>;

  const connected = status.status === "connected";

  return (
    <div className="space-y-6" data-testid="etsy-integration">
      <PageHeader title="Etsy Integration™" subtitle="Connect the Founder's Etsy shop and publish approved QRU products as governed DRAFT listings. Credentials stay encrypted server-side and never reach the browser." />

      {/* Connection card */}
      <section className="rounded-xl border bg-card p-5" data-testid="etsy-connection-card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-[#F1641E]/10 p-2"><Store className="w-5 h-5 text-[#F1641E]" /></div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-heading font-bold text-navy">Etsy Open API v3</span>
                <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${STATUS_TONE[status.status] || "bg-muted"}`} data-testid="etsy-status-badge">
                  {connected ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                  {status.status}
                </span>
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                {connected ? <>Shop: <span className="font-medium text-foreground" data-testid="etsy-shop-name">{status.connected_shop || status.shop_id}</span> · Scopes: {status.granted_scopes}</> : "Not connected. Connect the Founder's Etsy shop to begin."}
              </div>
              {status.last_error && <div className="text-xs text-red-600 mt-1" data-testid="etsy-last-error">Last error: {status.last_error}</div>}
              {status.last_synced_at && <div className="text-[11px] text-muted-foreground mt-1">Last sync: {new Date(status.last_synced_at).toLocaleString()}</div>}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {!connected ? (
              <button onClick={connect} disabled={!!busy || !status.configured} data-testid="etsy-connect-btn" className="inline-flex items-center gap-2 rounded-lg bg-[#F1641E] text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
                {busy === "connect" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plug className="w-4 h-4" />} Connect Etsy
              </button>
            ) : (
              <>
                <button onClick={runTest} disabled={!!busy} data-testid="etsy-test-btn" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
                  {busy === "test" ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlugZap className="w-4 h-4" />} Test Connection
                </button>
                <button onClick={disconnect} disabled={!!busy} data-testid="etsy-disconnect-btn" className="inline-flex items-center gap-2 rounded-lg border border-red-200 text-red-700 px-4 py-2 text-sm font-medium hover:bg-red-50 disabled:opacity-50">
                  {busy === "disconnect" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Unplug className="w-4 h-4" />} Disconnect
                </button>
              </>
            )}
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Stat label="Mapped products" value={status.mapped_products} />
          <Stat label="Draft listings" value={status.draft_listings} />
          <Stat label="Active listings" value={status.active_listings} />
          <Stat label="Permissions" value={connected ? (status.granted_scopes || "").split(" ").length : 0} />
        </div>
        {test && (
          <div className="mt-4 rounded-lg border p-4" data-testid="etsy-test-report">
            <div className="text-xs font-semibold text-navy mb-2">Connection report</div>
            <ul className="space-y-1">
              {test.checks.map((c, i) => (
                <li key={i} className="flex items-center gap-2 text-xs">
                  {c.ok ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <AlertTriangle className="w-3.5 h-3.5 text-red-600" />}
                  <span className="font-medium">{c.name}</span><span className="text-muted-foreground">— {c.detail}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* Eligible products */}
      <section className="rounded-xl border bg-card p-5" data-testid="etsy-products">
        <div className="flex items-center justify-between">
          <div className="font-heading font-bold text-navy">QRU products · Etsy controls</div>
          <button onClick={loadProducts} disabled={!!busy} className="inline-flex items-center gap-1 text-xs text-royal hover:underline"><RefreshCw className="w-3.5 h-3.5" /> Refresh</button>
        </div>
        <p className="text-xs text-muted-foreground mt-1">Only products that pass QRU governance (QA complete, authorized, files + images valid, metadata populated, no blocking issue) can be sent to Etsy — and always as a DRAFT first.</p>
        <div className="mt-4 overflow-x-auto rounded-lg border">
          <table className="w-full text-xs">
            <thead><tr className="text-left text-muted-foreground border-b bg-muted/40">
              <th className="py-2 px-3">Product</th><th className="py-2 px-3">Imprint</th><th className="py-2 px-3">Eligible</th><th className="py-2 px-3">Etsy</th><th className="py-2 px-3">Actions</th>
            </tr></thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} className="border-b last:border-0" data-testid={`etsy-product-${p.code}`}>
                  <td className="py-2 px-3"><div className="font-medium text-foreground">{p.title}</div><div className="text-[10px] text-muted-foreground">{p.code}</div></td>
                  <td className="py-2 px-3 text-muted-foreground">{p.imprint}</td>
                  <td className="py-2 px-3">{p.eligible ? <span className="inline-flex items-center gap-1 text-emerald-700"><CheckCircle2 className="w-3.5 h-3.5" /> Yes</span> : <span className="inline-flex items-center gap-1 text-muted-foreground"><AlertTriangle className="w-3.5 h-3.5" /> No</span>}</td>
                  <td className="py-2 px-3">{p.etsy_listing_id ? <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold bg-emerald-100 text-emerald-700">{p.etsy_state || "draft"}</span> : <span className="text-muted-foreground">—</span>}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap gap-1.5">
                      <button onClick={() => doPreview(p)} disabled={!!busy} data-testid={`etsy-preview-${p.code}`} className="inline-flex items-center gap-1 rounded border px-2 py-1 hover:bg-muted"><Eye className="w-3 h-3" /> Preview</button>
                      {!p.etsy_listing_id && connected && (
                        <button onClick={() => createDraft(p)} disabled={!!busy || !p.eligible} data-testid={`etsy-draft-${p.code}`} className="inline-flex items-center gap-1 rounded bg-[#F1641E] text-white px-2 py-1 hover:opacity-90 disabled:opacity-40"><FilePlus className="w-3 h-3" /> Create Draft</button>
                      )}
                      {p.etsy_url && <a href={p.etsy_url} target="_blank" rel="noreferrer" data-testid={`etsy-view-${p.code}`} className="inline-flex items-center gap-1 rounded border px-2 py-1 hover:bg-muted"><ExternalLink className="w-3 h-3" /> View</a>}
                      {p.etsy_listing_id && <button onClick={() => syncOne(p)} disabled={!!busy} data-testid={`etsy-sync-${p.code}`} className="inline-flex items-center gap-1 rounded border px-2 py-1 hover:bg-muted"><GitCompare className="w-3 h-3" /> Sync</button>}
                      {p.etsy_listing_id && connected && <button onClick={() => updateEtsy(p)} disabled={!!busy} data-testid={`etsy-update-${p.code}`} className="inline-flex items-center gap-1 rounded border px-2 py-1 hover:bg-muted"><UploadCloud className="w-3 h-3" /> Update</button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Preview drawer */}
      {preview && (
        <section className="rounded-xl border bg-card p-5" data-testid="etsy-preview-panel">
          <div className="flex items-center justify-between">
            <div className="font-heading font-bold text-navy">Etsy publication preview — {preview.product.title}</div>
            <button onClick={() => setPreview(null)} className="text-xs text-muted-foreground hover:underline">Close</button>
          </div>
          <div className="mt-3 grid md:grid-cols-2 gap-4">
            <div>
              <div className="text-xs font-semibold text-navy mb-2 flex items-center gap-1"><ShieldCheck className="w-4 h-4" /> Governance</div>
              <ul className="space-y-1">
                {preview.data.eligibility?.checks?.map((c, i) => (
                  <li key={i} className="flex items-center gap-2 text-xs">{c.ok ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <AlertTriangle className="w-3.5 h-3.5 text-red-600" />}<span className="font-medium">{c.name}</span> <span className="text-muted-foreground">— {c.detail}</span></li>
                ))}
              </ul>
            </div>
            <div>
              <div className="text-xs font-semibold text-navy mb-2">Listing (draft)</div>
              <div className="text-xs space-y-1">
                <div><span className="text-muted-foreground">Title:</span> {preview.data.listing_preview?.title}</div>
                <div><span className="text-muted-foreground">Price:</span> {preview.data.listing_preview?.currency} {preview.data.listing_preview?.price} · Qty {preview.data.listing_preview?.quantity}</div>
                <div><span className="text-muted-foreground">Type:</span> {preview.data.listing_preview?.type} · State: {preview.data.listing_preview?.state}</div>
                <div><span className="text-muted-foreground">Tags:</span> {(preview.data.listing_preview?.tags || []).join(", ")}</div>
                <div><span className="text-muted-foreground">Images:</span> {(preview.data.listing_preview?.images || []).length} · <span className="text-muted-foreground">Files:</span> {(preview.data.listing_preview?.files || []).length}</div>
                <div className="text-[11px] text-muted-foreground pt-1">{preview.data.note}</div>
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
