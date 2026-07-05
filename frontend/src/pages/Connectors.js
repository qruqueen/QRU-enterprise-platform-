import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader } from "@/components/shared";
import { StageTimeline, StatusChip } from "@/components/qru";
import { toast } from "sonner";
import {
  Plug, Loader2, CheckCircle2, AlertTriangle, ShieldCheck, KeyRound, ExternalLink, X,
  Radio, Upload, Store, Settings2, Unplug, XCircle, CircleDot, Wrench, RefreshCw, Lock,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const ADMIN_ROLES = ["Founder & CEO", "Administrator"];

const STATUS_STYLE = {
  "Ready to Publish": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Connected": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Published": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Publishing": "bg-royal/10 text-royal border-royal/30",
  "Needs Authorization": "bg-amber-50 text-amber-700 border-amber-200",
  "Developer Setup Required": "bg-blue-50 text-blue-700 border-blue-200",
  "Developer Setup Complete": "bg-blue-50 text-blue-700 border-blue-200",
  "Connection Expired": "bg-amber-50 text-amber-700 border-amber-200",
  "Reconnect Required": "bg-amber-50 text-amber-700 border-amber-200",
  "Not Connected": "bg-slate-100 text-slate-500 border-slate-200",
  "Failed": "bg-red-50 text-red-700 border-red-200",
  "Connection Error": "bg-red-50 text-red-700 border-red-200",
};

const LIFECYCLE = ["Connect", "Test", "Manufacture", "Preview", "Publish"];

export default function Connectors() {
  const { user } = useAuth();
  const isAdmin = ADMIN_ROLES.includes(user?.role);
  const [devMode, setDevMode] = useState(false);
  const [items, setItems] = useState(null);
  const [connectDlg, setConnectDlg] = useState(null);
  const [publishDlg, setPublishDlg] = useState(null);
  const [devDlg, setDevDlg] = useState(null);
  const [testDlg, setTestDlg] = useState(null);
  const [busy, setBusy] = useState("");

  const load = () => api.get("/connectors").then((r) => setItems(r.data.connectors)).catch(() => {});
  useEffect(() => { load(); }, []);

  // Handle the OAuth provider redirect back to /connectors?oauth=success|error&platform=&message=
  useEffect(() => {
    const p = new URLSearchParams(window.location.search);
    const oauth = p.get("oauth");
    if (oauth) {
      const msg = p.get("message") || (oauth === "success" ? "Connected." : "Authorization failed.");
      toast[oauth === "success" ? "success" : "error"](`${p.get("platform") || ""}: ${msg}`);
      window.history.replaceState({}, "", "/connectors");
      load();
    }
  }, []);

  const test = async (c) => {
    setBusy(c.id);
    try {
      const { data } = await api.post(`/connectors/${c.id}/verify`);
      if (data.checks && data.checks.length) setTestDlg({ c, result: data });
      else toast[data.healthy ? "success" : "message"](`${c.name}: ${data.message}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || "Could not test connection"); }
    finally { setBusy(""); }
  };

  const connectOAuth = async (c) => {
    setBusy(c.id);
    // Open a top-level tab synchronously (inside the click) so it isn't blocked and
    // escapes the Emergent preview iframe — Google refuses to load its sign-in inside a frame.
    const win = window.open("", "_blank");
    try {
      const { data } = await api.get(`/connectors/${c.id}/authorize-url?frontend_origin=${encodeURIComponent(window.location.origin)}`);
      if (win) win.location.href = data.authorize_url;
      else {
        // Popup blocked — fall back to navigating the top-level window out of the iframe.
        try { window.top.location.href = data.authorize_url; }
        catch { window.location.href = data.authorize_url; }
      }
    } catch (e) {
      if (win) win.close();
      toast.error(e.response?.data?.detail || "Could not start authorization");
    } finally { setBusy(""); }
  };

  const disconnect = async (c) => {
    setBusy(c.id);
    try { await api.post(`/connectors/${c.id}/disconnect`); toast.success(`${c.name} disconnected`); load(); }
    catch (e) { toast.error("Could not disconnect"); }
    finally { setBusy(""); }
  };

  if (!items) return <div className="flex items-center gap-2 text-sm text-muted-foreground p-8"><Loader2 className="w-4 h-4 animate-spin" /> Loading connectors…</div>;

  return (
    <div>
      <PageHeader
        overline="Universal Connector & OAuth Framework™ · Treasure Standard™"
        title="Publishing Connectors"
        description="Every platform, one experience: Connect → official provider login → Approve → Connected → Test → Publish. You never see tokens or credentials — QRU handles the technical differences behind the scenes."
      />

      <div className="flex items-center justify-between gap-3 flex-wrap mb-5">
        <StageTimeline steps={LIFECYCLE} current={-1} testid="connector-lifecycle" />
        {isAdmin && (
          <button data-testid="developer-mode-toggle" onClick={() => setDevMode((v) => !v)}
            className={`text-xs inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm border font-medium ${devMode ? "bg-navy text-white border-navy" : "text-navy border-navy/30 hover:border-navy"}`}>
            <Wrench className="w-3.5 h-3.5" /> Developer Mode {devMode ? "ON" : "OFF"}
          </button>
        )}
      </div>
      {devMode && (
        <div className="mb-5 bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-800 flex items-start gap-2" data-testid="developer-mode-banner">
          <Lock className="w-4 h-4 shrink-0 mt-0.5" /> <span><b>Developer Mode</b> — administrator-only. Configure each platform's OAuth app / API credentials here. These are encrypted and never shown to the Founder during normal use.</span>
        </div>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="connector-grid">
        {items.map((c) => (
          <div key={c.id} className="bg-card border rounded-xl p-4 flex flex-col" data-testid={`connector-${c.id}`}>
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-heading font-bold text-navy">{c.name}</p>
                <p className="text-[11px] text-muted-foreground">{c.category} · {c.auth_method === "native" ? "Built-in" : c.auth_method === "oauth" ? "OAuth" : "API key"}</p>
              </div>
              <StatusChip status={c.status} testid={`connector-status-${c.id}`} />
            </div>

            {c.account && (c.authorized || c.connected) && (
              <p className="text-[11px] text-emerald-700 mb-1.5 flex items-center gap-1" data-testid={`connector-account-${c.id}`}><CircleDot className="w-3 h-3" /> {c.account}</p>
            )}

            <div className="flex flex-wrap gap-1 mb-3">
              {c.asset_types.slice(0, 4).map((a) => (
                <span key={a} className="text-[10px] px-1.5 py-0.5 rounded bg-gold/10 text-navy">{a}</span>
              ))}
              {c.asset_types.length > 4 && <span className="text-[10px] text-muted-foreground">+{c.asset_types.length - 4}</span>}
            </div>

            {c.oauth_supported === false && c.oauth_unsupported_reason && (
              <p className="text-[11px] text-muted-foreground mb-2 flex items-start gap-1" data-testid={`connector-unsupported-${c.id}`}><AlertTriangle className="w-3 h-3 mt-0.5 shrink-0 text-amber-500" /> {c.oauth_unsupported_reason}</p>
            )}
            {c.configurable && !c.developer_configured && !devMode && (
              <p className="text-[11px] text-blue-700 mb-2 flex items-start gap-1" data-testid={`connector-setup-note-${c.id}`}><Settings2 className="w-3 h-3 mt-0.5 shrink-0" />
                {isAdmin
                  ? "Turn on Developer Mode (top-right) → click Developer Setup to paste the Client ID & Secret. The status will change to “Needs Authorization”, then you can Connect."
                  : "An administrator must complete developer setup before this platform can be connected."}
              </p>
            )}
            {devMode && c.configurable && (
              <p className="text-[11px] text-muted-foreground mb-2" data-testid={`connector-cred-needs-${c.id}`}><b className="text-navy">Needs:</b> {c.credential_needs}</p>
            )}

            <div className="mt-auto flex flex-wrap gap-1.5">
              {/* Developer Setup — administrator-only, Developer Mode only */}
              {devMode && c.configurable && (
                <button data-testid={`connector-devconfig-${c.id}`}
                  onClick={() => (c.auth_method === "oauth" ? setDevDlg(c) : setConnectDlg(c))}
                  className="text-xs inline-flex items-center gap-1 border border-navy/40 text-navy px-2.5 py-1.5 rounded-sm hover:border-navy">
                  <Settings2 className="w-3.5 h-3.5" /> Developer Setup
                </button>
              )}

              {/* Founder Connect / Reconnect — only after developer setup is complete */}
              {c.auth_method === "oauth" && c.oauth_supported !== false && c.developer_configured && !c.authorized && !c.reconnect_required && (
                <button data-testid={`connector-connect-${c.id}`} onClick={() => connectOAuth(c)} disabled={busy === c.id}
                  className="text-xs inline-flex items-center gap-1 bg-navy text-white px-2.5 py-1.5 rounded-sm disabled:opacity-60">
                  {busy === c.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ExternalLink className="w-3.5 h-3.5" />} Connect
                </button>
              )}
              {c.auth_method === "oauth" && c.reconnect_required && (
                <button data-testid={`connector-reconnect-${c.id}`} onClick={() => connectOAuth(c)} disabled={busy === c.id}
                  className="text-xs inline-flex items-center gap-1 bg-amber-500 text-white px-2.5 py-1.5 rounded-sm disabled:opacity-60">
                  <RefreshCw className="w-3.5 h-3.5" /> Reconnect
                </button>
              )}

              {/* Test Connection — once developer setup is complete */}
              {(c.auth_method === "native" || (c.configurable && c.developer_configured)) && (
                <button data-testid={`connector-test-${c.id}`} onClick={() => test(c)} disabled={busy === c.id}
                  className="text-xs inline-flex items-center gap-1 border px-2.5 py-1.5 rounded-sm hover:border-primary disabled:opacity-60">
                  {busy === c.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Radio className="w-3.5 h-3.5" />} Test
                </button>
              )}

              {/* Disconnect */}
              {c.authorized && (
                <button data-testid={`connector-disconnect-${c.id}`} onClick={() => disconnect(c)} disabled={busy === c.id}
                  className="text-xs inline-flex items-center gap-1 border px-2.5 py-1.5 rounded-sm hover:border-red-300 text-red-600">
                  <Unplug className="w-3.5 h-3.5" /> Disconnect
                </button>
              )}

              {/* Publish */}
              {c.can_publish ? (
                <button data-testid={`connector-publish-${c.id}`} onClick={() => setPublishDlg(c)}
                  className="text-xs inline-flex items-center gap-1 bg-gold text-navy px-2.5 py-1.5 rounded-sm font-medium">
                  <Upload className="w-3.5 h-3.5" /> Publish
                </button>
              ) : (
                <button data-testid={`connector-publish-disabled-${c.id}`} disabled title={c.publish_disabled_reason || "Publishing unavailable"}
                  className="text-xs inline-flex items-center gap-1 border px-2.5 py-1.5 rounded-sm opacity-50 cursor-not-allowed">
                  <Upload className="w-3.5 h-3.5" /> Publish
                </button>
              )}
            </div>

            {/* Always tell the Founder the exact next step (Treasure Standard™) */}
            <p className="text-[10px] text-navy/70 mt-2 flex items-start gap-1" data-testid={`connector-next-step-${c.id}`}>
              <span className="font-semibold shrink-0">Next:</span> {c.next_step}
            </p>
            {!c.can_publish && c.publish_disabled_reason && (
              <p className="text-[10px] text-muted-foreground mt-1" data-testid={`connector-publish-reason-${c.id}`}>Publish: {c.publish_disabled_reason}</p>
            )}
          </div>
        ))}
      </div>

      {connectDlg && <ConnectDialog c={connectDlg} onClose={() => setConnectDlg(null)} onDone={() => { setConnectDlg(null); load(); }} />}
      {publishDlg && <PublishDialog c={publishDlg} onClose={() => setPublishDlg(null)} onDone={() => { setPublishDlg(null); load(); }} />}
      {devDlg && <DevConfigDialog c={devDlg} onClose={() => setDevDlg(null)} onDone={() => { setDevDlg(null); load(); }} />}
      {testDlg && <TestResultDialog c={testDlg.c} result={testDlg.result} onClose={() => setTestDlg(null)} />}
    </div>
  );
}

function DevConfigDialog({ c, onClose, onDone }) {
  const [cfg, setCfg] = useState(null);
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [redirectUri, setRedirectUri] = useState(`${BACKEND}/api/oauth/callback`);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get(`/connectors/${c.id}/developer-config`).then((r) => {
      setCfg(r.data);
      if (r.data.redirect_uri) setRedirectUri(r.data.redirect_uri);
    }).catch(() => setCfg({ configured: false }));
  }, [c.id]);

  const save = async () => {
    setBusy(true);
    try {
      await api.post(`/connectors/${c.id}/developer-config`, { client_id: clientId, client_secret: clientSecret, redirect_uri: redirectUri });
      toast.success(`${c.name} OAuth app configured`);
      onDone();
    } catch (e) { toast.error(e.response?.data?.detail || "Could not save configuration"); }
    finally { setBusy(false); }
  };

  const remove = async () => {
    setBusy(true);
    try { await api.delete(`/connectors/${c.id}/developer-config`); toast.success("Configuration removed"); onDone(); }
    catch (e) { toast.error("Could not remove"); }
    finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="devconfig-dialog">
      <div className="bg-card rounded-md max-w-md w-full p-5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <p className="font-heading font-bold text-navy flex items-center gap-2"><Settings2 className="w-4 h-4 text-royal" /> {c.name} · Developer Setup</p>
          <button onClick={onClose} data-testid="devconfig-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>
        <p className="text-xs text-muted-foreground mb-3">Register an OAuth app in the {c.name} developer console, then paste its credentials here. Stored encrypted — the Founder never sees or handles tokens.</p>
        {cfg?.configured && (
          <div className="text-[11px] bg-emerald-50 border border-emerald-200 rounded p-2 mb-3 text-emerald-800" data-testid="devconfig-current">
            Currently configured: Client ID {cfg.client_id_masked} · {cfg.has_secret ? "secret set" : "no secret"}.
          </div>
        )}
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-navy">OAuth Client ID</label>
            <input data-testid="devconfig-client-id" value={clientId} onChange={(e) => setClientId(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm" placeholder="Paste Client ID" />
          </div>
          <div>
            <label className="text-xs font-medium text-navy flex items-center gap-1"><KeyRound className="w-3.5 h-3.5" /> OAuth Client Secret</label>
            <input data-testid="devconfig-client-secret" type="password" value={clientSecret} onChange={(e) => setClientSecret(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm" placeholder={cfg?.has_secret ? "•••• (leave blank to keep)" : "Paste Client Secret"} />
          </div>
          <div>
            <label className="text-xs font-medium text-navy">Redirect URI (register this exact value)</label>
            <input data-testid="devconfig-redirect-uri" value={redirectUri} onChange={(e) => setRedirectUri(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm font-mono text-[11px]" />
          </div>
          <div className="flex gap-2">
            <button onClick={save} disabled={busy || !clientId || !redirectUri} data-testid="devconfig-save"
              className="flex-1 bg-navy text-white px-4 py-2 rounded-sm text-sm disabled:opacity-60 inline-flex items-center justify-center gap-2">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />} Save Configuration
            </button>
            {cfg?.configured && (
              <button onClick={remove} disabled={busy} data-testid="devconfig-remove" className="border text-red-600 px-3 py-2 rounded-sm text-sm hover:border-red-300">Remove</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const CHECK_ICON = { pass: CheckCircle2, fail: XCircle, warn: AlertTriangle };
const CHECK_COLOR = { pass: "text-emerald-600", fail: "text-red-600", warn: "text-amber-600" };

function TestResultDialog({ c, result, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="test-result-dialog">
      <div className="bg-card rounded-md max-w-md w-full p-5 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-2">
          <p className="font-heading font-bold text-navy flex items-center gap-2"><Radio className="w-4 h-4 text-royal" /> {c.name} · Test Connection</p>
          <button onClick={onClose} data-testid="test-result-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>
        <p className={`text-sm font-medium mb-3 ${result.overall === "passed" ? "text-emerald-700" : "text-amber-700"}`}>{result.message}</p>
        <div className="space-y-1.5" data-testid="test-checks">
          {result.checks.map((chk, i) => {
            const Icon = CHECK_ICON[chk.status] || AlertTriangle;
            return (
              <div key={i} className="flex gap-2 text-xs border-b border-border/50 py-1.5">
                <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${CHECK_COLOR[chk.status]}`} />
                <div><p className="font-medium text-navy">{chk.name}</p><p className="text-muted-foreground">{chk.detail}</p></div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ConnectDialog({ c, onClose, onDone }) {
  const [apiKey, setApiKey] = useState("");
  const [account, setAccount] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    try {
      await api.post(`/connectors/${c.id}/connect`, { credentials: { api_key: apiKey, account } });
      toast.success(`${c.name} connected`);
      onDone();
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
