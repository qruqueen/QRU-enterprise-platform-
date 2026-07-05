import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { toast } from "sonner";
import {
  Plug, Loader2, CheckCircle2, AlertTriangle, ShieldCheck, KeyRound, ExternalLink, X,
  Radio, Factory, Eye, Upload, Store,
} from "lucide-react";

const STATUS_STYLE = {
  "Connected Healthy": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Connected": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Needs Authorization": "bg-amber-50 text-amber-700 border-amber-200",
  "Setup Required": "bg-blue-50 text-blue-700 border-blue-200",
  "Connection Error": "bg-red-50 text-red-700 border-red-200",
};

const LIFECYCLE = ["Connect", "Test", "Manufacture", "Preview", "Publish"];

export default function Connectors() {
  const [items, setItems] = useState(null);
  const [connectDlg, setConnectDlg] = useState(null); // connector being connected
  const [publishDlg, setPublishDlg] = useState(null); // connector to publish to
  const [busy, setBusy] = useState("");

  const load = () => api.get("/connectors").then((r) => setItems(r.data.connectors)).catch(() => {});
  useEffect(() => { load(); }, []);

  const test = async (id) => {
    setBusy(id);
    try {
      const { data } = await api.post(`/connectors/${id}/verify`);
      toast[data.healthy ? "success" : "message"](`${id}: ${data.message}`);
      load();
    } catch (e) { toast.error("Could not test connection"); }
    finally { setBusy(""); }
  };

  if (!items) return <div className="flex items-center gap-2 text-sm text-muted-foreground p-8"><Loader2 className="w-4 h-4 animate-spin" /> Loading connectors…</div>;

  return (
    <div>
      <PageHeader
        overline="Universal Connector Framework™ · Treasure Standard™"
        title="Publishing Connectors"
        description="Every platform, one experience. Connect → Test → Manufacture → Preview → Publish. QRU handles the technical differences behind the scenes."
      />

      {/* Uniform 5-step lifecycle banner */}
      <div className="flex items-center gap-2 flex-wrap mb-5 text-xs" data-testid="connector-lifecycle">
        {LIFECYCLE.map((s, i) => (
          <span key={s} className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full bg-navy/5 text-navy font-medium">{i + 1}. {s}</span>
            {i < LIFECYCLE.length - 1 && <span className="text-muted-foreground">→</span>}
          </span>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="connector-grid">
        {items.map((c) => (
          <div key={c.id} className="bg-card border rounded-xl p-4" data-testid={`connector-${c.id}`}>
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-heading font-bold text-navy">{c.name}</p>
                <p className="text-[11px] text-muted-foreground">{c.category} · {c.auth_method === "native" ? "Built-in" : c.auth_method === "oauth" ? "OAuth" : "API key"}</p>
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full border ${STATUS_STYLE[c.status]}`} data-testid={`connector-status-${c.id}`}>{c.status}</span>
            </div>

            <div className="flex flex-wrap gap-1 mb-3">
              {c.asset_types.slice(0, 4).map((a) => (
                <span key={a} className="text-[10px] px-1.5 py-0.5 rounded bg-gold/10 text-navy">{a}</span>
              ))}
              {c.asset_types.length > 4 && <span className="text-[10px] text-muted-foreground">+{c.asset_types.length - 4}</span>}
            </div>

            {!c.operational && (
              <p className="text-[11px] text-muted-foreground mb-2 flex items-start gap-1"><AlertTriangle className="w-3 h-3 mt-0.5 shrink-0 text-amber-500" /> {c.setup_hint}</p>
            )}

            <div className="flex flex-wrap gap-1.5">
              {!c.connected ? (
                <button data-testid={`connector-connect-${c.id}`} onClick={() => setConnectDlg(c)}
                  className="text-xs inline-flex items-center gap-1 bg-navy text-white px-2.5 py-1.5 rounded-sm">
                  <Plug className="w-3.5 h-3.5" /> Connect
                </button>
              ) : (
                <span className="text-xs inline-flex items-center gap-1 text-emerald-700 px-2 py-1.5"><CheckCircle2 className="w-3.5 h-3.5" /> Connected</span>
              )}
              <button data-testid={`connector-test-${c.id}`} onClick={() => test(c.id)} disabled={busy === c.id}
                className="text-xs inline-flex items-center gap-1 border px-2.5 py-1.5 rounded-sm hover:border-primary disabled:opacity-60">
                {busy === c.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Radio className="w-3.5 h-3.5" />} Test
              </button>
              {c.can_publish ? (
                <button data-testid={`connector-publish-${c.id}`} onClick={() => setPublishDlg(c)}
                  className="text-xs inline-flex items-center gap-1 bg-gold text-navy px-2.5 py-1.5 rounded-sm font-medium">
                  <Upload className="w-3.5 h-3.5" /> Publish
                </button>
              ) : (
                <button data-testid={`connector-publish-disabled-${c.id}`} disabled title={c.publish_disabled_reason}
                  className="text-xs inline-flex items-center gap-1 border px-2.5 py-1.5 rounded-sm opacity-50 cursor-not-allowed">
                  <Upload className="w-3.5 h-3.5" /> Publish
                </button>
              )}
            </div>
            {!c.can_publish && c.publish_disabled_reason && (
              <p className="text-[10px] text-muted-foreground mt-1.5">Publish: {c.publish_disabled_reason}</p>
            )}
          </div>
        ))}
      </div>

      {connectDlg && <ConnectDialog c={connectDlg} onClose={() => setConnectDlg(null)} onDone={() => { setConnectDlg(null); load(); }} />}
      {publishDlg && <PublishDialog c={publishDlg} onClose={() => setPublishDlg(null)} onDone={() => { setPublishDlg(null); load(); }} />}
    </div>
  );
}

function ConnectDialog({ c, onClose, onDone }) {
  const [apiKey, setApiKey] = useState("");
  const [account, setAccount] = useState("");
  const [busy, setBusy] = useState(false);
  const [guided, setGuided] = useState(null);

  const submit = async () => {
    setBusy(true);
    try {
      const body = c.auth_method === "api_key" ? { credentials: { api_key: apiKey, account } } : {};
      const { data } = await api.post(`/connectors/${c.id}/connect`, body);
      if (data.guided) { setGuided(data.message); }
      else { toast.success(`${c.name} connected`); onDone(); }
    } catch (e) { toast.error(e.response?.data?.detail || "Could not connect"); }
    finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="connect-dialog">
      <div className="bg-card rounded-md max-w-md w-full p-5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <p className="font-heading font-bold text-navy flex items-center gap-2"><Plug className="w-4 h-4 text-royal" /> Connect {c.name}</p>
          <button onClick={onClose} data-testid="connect-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>
        {guided ? (
          <div className="text-sm text-navy" data-testid="connect-guided">
            <ShieldCheck className="w-8 h-8 text-royal mb-2" />
            <p>{guided}</p>
            <button onClick={onDone} className="mt-4 bg-navy text-white px-4 py-2 rounded-sm text-sm w-full">Got it</button>
          </div>
        ) : c.auth_method === "oauth" ? (
          <div className="text-sm text-muted-foreground" data-testid="connect-oauth">
            <p><b className="text-navy">{c.name}</b> uses secure OAuth. QRU will launch the official {c.name} authorization — you approve access on {c.name} directly, and your credentials are never typed here.</p>
            <button onClick={submit} disabled={busy} data-testid="connect-oauth-start"
              className="mt-4 bg-navy text-white px-4 py-2 rounded-sm text-sm w-full inline-flex items-center justify-center gap-2">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <ExternalLink className="w-4 h-4" />} Authorize {c.name}
            </button>
          </div>
        ) : (
          <div className="space-y-3" data-testid="connect-apikey">
            <p className="text-xs text-muted-foreground">{c.setup_hint}</p>
            <div>
              <label className="text-xs font-medium text-navy flex items-center gap-1"><KeyRound className="w-3.5 h-3.5" /> API Key</label>
              <input data-testid="connect-apikey-input" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                className="w-full mt-1 border rounded-sm p-2 text-sm" placeholder="Paste your API key" />
            </div>
            <div>
              <label className="text-xs font-medium text-navy">Account / Store name (optional)</label>
              <input value={account} onChange={(e) => setAccount(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm" placeholder="e.g. my-shop" />
            </div>
            <button onClick={submit} disabled={busy || !apiKey} data-testid="connect-apikey-submit"
              className="bg-navy text-white px-4 py-2 rounded-sm text-sm w-full disabled:opacity-60 inline-flex items-center justify-center gap-2">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />} Connect & Verify
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function PublishDialog({ c, onClose, onDone }) {
  const [products, setProducts] = useState(null);
  const [busy, setBusy] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/founder-inbox").then((r) => setProducts(r.data.products.filter((p) => p.publishable))).catch(() => setProducts([]));
  }, []);

  const publish = async (pid) => {
    setBusy(pid);
    try {
      const { data } = await api.post(`/connectors/${c.id}/publish`, { product_id: pid });
      setResult(data);
      toast.success(`Published to ${c.name}`);
    } catch (e) { toast.error(e.response?.data?.detail || "Publish failed"); }
    finally { setBusy(""); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="publish-dialog">
      <div className="bg-card rounded-md max-w-lg w-full p-5 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <p className="font-heading font-bold text-navy flex items-center gap-2"><Upload className="w-4 h-4 text-royal" /> Publish to {c.name}</p>
          <button onClick={onClose} data-testid="publish-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>
        {result ? (
          <div className="text-sm" data-testid="publish-result">
            <CheckCircle2 className="w-10 h-10 text-emerald-600 mb-2" />
            <p className="font-medium text-navy">Published successfully to {result.platform}.</p>
            <div className="mt-2 text-xs text-muted-foreground space-y-0.5">
              <p>Product: {result.product_code} · Version {result.version}</p>
              <p>Published: {String(result.published_at).slice(0, 19).replace("T", " ")}</p>
              <p>Store status: {result.store_status} · Treasure Standard™: {result.treasure_standard}</p>
              {result.platform_url && <a href={result.platform_url} target="_blank" rel="noreferrer" className="text-royal inline-flex items-center gap-1"><ExternalLink className="w-3 h-3" /> View on {result.platform}</a>}
            </div>
          </div>
        ) : products === null ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading ready products…</div>
        ) : products.length === 0 ? (
          <p className="text-sm text-muted-foreground">No products are fully ready to publish yet. Finish manufacturing & review a product first — it'll appear here automatically.</p>
        ) : (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">Only products that passed every QRU gate appear here.</p>
            {products.map((p) => (
              <div key={p.id} className="flex items-center gap-2 border rounded-sm p-2 text-sm" data-testid={`publish-product-${p.product_code}`}>
                <Store className="w-4 h-4 text-gold shrink-0" />
                <span className="flex-1 truncate text-navy">{p.title}</span>
                <span className="text-[11px] text-muted-foreground">{p.factory_confidence}%</span>
                <button onClick={() => publish(p.id)} disabled={busy === p.id} data-testid={`publish-go-${p.product_code}`}
                  className="text-xs bg-gold text-navy px-2.5 py-1 rounded-sm font-medium disabled:opacity-60 inline-flex items-center gap-1">
                  {busy === p.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />} Publish
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
