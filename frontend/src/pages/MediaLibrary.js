import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, Film, Music, Search, Plug, KeyRound, X, CheckCircle2, Video, Layers, ShieldAlert, Download,
} from "lucide-react";

const KIND_ICON = { video: Video, audio: Music, both: Layers };

export default function MediaLibrary() {
  const [config, setConfig] = useState(null);
  const [gov, setGov] = useState([]);
  const [providers, setProviders] = useState([]);
  const [assets, setAssets] = useState([]);
  const [provider, setProvider] = useState("");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);
  const [cfgDlg, setCfgDlg] = useState(null);
  const [proof, setProof] = useState(null);
  const [producing, setProducing] = useState(false);
  const API_BASE = (process.env.REACT_APP_BACKEND_URL || "") + "/api/media-library/asset";

  const loadProviders = () => api.get("/media-library/providers").then((r) => setProviders(r.data.providers)).catch(() => {});
  const loadAssets = () => api.get("/media-library/assets").then((r) => setAssets(r.data.assets)).catch(() => {});

  const testConn = async (id) => {
    try {
      const { data } = await api.post(`/media-library/providers/${id}/test`);
      if (data.test_code === "CONNECTED") toast.success("Connected — provider is now Active.");
      else toast.error(`Connection failed: ${data.test_code}`);
      loadProviders();
    } catch { toast.error("Test failed."); }
  };
  const revokeKey = async (id) => {
    try { await api.delete(`/media-library/providers/${id}/config`); toast.success("Credential revoked."); loadProviders(); }
    catch { toast.error("Revoke failed."); }
  };
  useEffect(() => {
    api.get("/media-library/config").then((r) => setConfig(r.data)).catch(() => setConfig(false));
    api.get("/governance-binding/strip/media").then((r) => setGov(r.data.governed_by)).catch(() => {});
    loadProviders(); loadAssets();
  }, []);

  const runProof = async () => {
    setProducing(true); setProof(null);
    try {
      const { data } = await api.post("/media-library/produce-proof", { provider_id: "pixabay_video", query: "peaceful forest sunrise", product_title: "Forex Foundations" });
      setProof(data); loadAssets();
      toast.success("Milestone 001 — first live licensed media manufactured.");
    } catch (e) { toast.error(e.response?.data?.detail || "Production pipeline failed."); }
    finally { setProducing(false); }
  };

  const runSearch = async () => {
    if (!provider || !query.trim()) return toast.error("Choose a connected provider and enter a search.");
    setBusy(true); setResults(null);
    try {
      const { data } = await api.post("/media-library/search", { provider_id: provider, query: query.trim() });
      setResults(data);
      if (!data.configured) toast.message(data.reason || "Provider not configured yet.");
    } catch (e) { toast.error(e.response?.data?.detail || "Search failed."); }
    finally { setBusy(false); }
  };

  const registerAsset = async (item) => {
    try {
      await api.post("/media-library/register", { item, collection: "QRU General Backgrounds" });
      toast.success("Registered in Master Asset Vault™.");
      loadAssets();
    } catch (e) { toast.error(e.response?.data?.detail || "Register failed."); }
  };

  if (config === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (config === false) return <p className="text-sm text-muted-foreground p-8">Could not load the Media Library.</p>;

  const connected = providers.filter((p) => p.connected);

  return (
    <div>
      <PageHeader
        overline="QRU Media Acquisition Foundation™ · MO-021 / MO-023"
        title="Stock Media Library"
        description="A governed acquisition layer for licensed video & audio. Every clip comes from an approved provider — never the open internet — and every asset preserves its source, creator, license and commercial-use rights in the Master Asset Vault™."
        actions={<VerifiedBadge label="FR-097 · No Unverified Stock Media™" testid="ml-badge" />}
      />
      <GovernedBy standards={gov} className="mb-4" testid="ml-governed-by" />

      {/* Factory rules */}
      <div className="grid sm:grid-cols-2 gap-3 mb-8">
        {config.factory_rules.map((r) => (
          <div key={r.id} className="qru-card p-3 border-l-4 border-gold" data-testid={`ml-rule-${r.id}`}>
            <p className="overline text-gold mb-1 flex items-center gap-1"><ShieldAlert className="w-3 h-3" /> {r.id} · {r.title}</p>
            <p className="text-[12px] text-navy">{r.statement}</p>
          </div>
        ))}
      </div>

      {/* First Live Media Proof — Milestone 001 */}
      <Panel title="First Live Media Manufacturing Proof · Milestone 001" icon={Film} accent="gold" testid="ml-proof" className="mb-8">
        <div className="flex items-center justify-between flex-wrap gap-3 mb-3">
          <p className="text-[12px] text-muted-foreground max-w-2xl">End-to-end governed workflow on a real licensed clip: live search → recommend → approve → license verify → download+checksum → register → narration (OpenAI TTS) → captions → MP4 render → quality review → Master Asset Vault™ → distribution ready.</p>
          <button onClick={runProof} disabled={producing} data-testid="ml-run-proof"
            className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
            {producing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Film className="w-4 h-4" />} {producing ? "Manufacturing… (~40s)" : "Run Live Proof"}
          </button>
        </div>
        {proof && (
          <div className="grid md:grid-cols-2 gap-4" data-testid="ml-proof-result">
            <div className="space-y-1">
              {proof.steps.map((s, i) => (
                <div key={i} className="flex items-start gap-2 text-[11px]" data-testid={`ml-step-${s.step}`}>
                  {s.status === "ok" ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" /> : <ShieldAlert className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />}
                  <span><b className="text-navy capitalize">{s.step.replace(/_/g, " ")}</b> — <span className="text-muted-foreground">{s.detail}</span></span>
                </div>
              ))}
            </div>
            <div>
              {proof.showcase_asset && (
                <>
                  <video src={`${API_BASE}/${proof.showcase_asset.qru_asset_id}/file`} controls className="w-full rounded-md border" data-testid="ml-proof-video" />
                  <p className="text-[11px] text-navy mt-2 font-mono">{proof.showcase_asset.qru_asset_id}</p>
                  <p className="text-[10px] text-muted-foreground">{proof.showcase_asset.width}×{proof.showcase_asset.height} · {proof.showcase_asset.duration_seconds}s · narration: {String(proof.showcase_asset.has_narration)} · checksum {String(proof.showcase_asset.checksum).slice(0, 16)}…</p>
                  <p className="text-[10px] text-emerald-600 mt-1">Source: {proof.source_asset.qru_asset_id} · {proof.source_asset.creator_name} · {proof.source_asset.license_type}</p>
                </>
              )}
            </div>
          </div>
        )}
      </Panel>

      {/* Providers */}
      <Panel title="Approved Providers" icon={Plug} accent="royal" testid="ml-providers" className="mb-8">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {providers.map((p) => {
            const Icon = KIND_ICON[p.kind] || Film;
            const statusLabel = { ACTIVE: "Active", DEVELOPER_SETUP_REQUIRED: "Developer Setup Required", PREPARED_NOT_ACTIVATED: "Prepared — Not Activated" }[p.status] || p.status;
            return (
              <div key={p.id} className="border rounded-md p-3" data-testid={`ml-provider-${p.id}`}>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-semibold text-navy flex items-center gap-1.5"><Icon className="w-3.5 h-3.5 text-royal" /> {p.name}</p>
                  <StatusChip status={statusLabel} tone={p.connected ? "emerald" : p.configurable ? "blue" : "slate"} />
                </div>
                <p className="text-[10px] text-muted-foreground mb-1">Tier {p.tier} · {p.kind} · {p.license}</p>
                {p.masked_key && <p className="text-[10px] font-mono text-navy/70 mb-1" data-testid={`ml-masked-${p.id}`}>Key: {p.masked_key}</p>}
                {p.env_provided && <p className="text-[10px] text-emerald-600 mb-1">Environment-provided access (Emergent egress)</p>}
                {p.last_validated && <p className="text-[10px] text-muted-foreground mb-1">Validated · {String(p.last_validated).slice(0, 10)}</p>}
                {p.configurable && (
                  <div className="flex items-center gap-3 mt-1">
                    {p.env_provided ? (
                      <span role="button" tabIndex={0} data-testid={`ml-test-${p.id}`} onClick={() => testConn(p.id)}
                        className="text-[11px] text-royal font-semibold hover:underline cursor-pointer inline-flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Test Connection</span>
                    ) : (
                      <span role="button" tabIndex={0} data-testid={`ml-config-${p.id}`} onClick={() => setCfgDlg(p)}
                        className="text-[11px] text-royal font-semibold hover:underline cursor-pointer inline-flex items-center gap-1"><KeyRound className="w-3 h-3" /> {p.connected ? "Edit key" : "Developer Setup"}</span>
                    )}
                    {p.connected && !p.env_provided && (
                      <span role="button" tabIndex={0} data-testid={`ml-revoke-${p.id}`} onClick={() => revokeKey(p.id)}
                        className="text-[11px] text-red-500 hover:underline cursor-pointer">Revoke</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Panel>

      {/* Search */}
      <Panel title="Search Approved Providers" icon={Search} accent="gold" testid="ml-search" className="mb-8">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end mb-4">
          <div>
            <label className="text-xs font-bold text-navy uppercase tracking-wide">Provider</label>
            <select data-testid="ml-provider-select" value={provider} onChange={(e) => setProvider(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
              <option value="">— Select —</option>
              {providers.filter((p) => p.configurable).map((p) => <option key={p.id} value={p.id} disabled={!p.connected}>{p.name}{p.connected ? "" : " (setup required)"}</option>)}
            </select>
          </div>
          <div className="flex-1">
            <label className="text-xs font-bold text-navy uppercase tracking-wide">Search</label>
            <input data-testid="ml-query" value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && runSearch()}
              placeholder="e.g. global financial network, forex, world map" className="w-full mt-1 border rounded-sm p-2 text-sm" />
          </div>
          <button onClick={runSearch} disabled={busy} data-testid="ml-search-run"
            className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Search
          </button>
        </div>
        {connected.length === 0 && <p className="text-[12px] text-blue-700 bg-blue-50 border border-blue-200 rounded-sm p-2.5" data-testid="ml-no-providers">No providers are connected yet. Add a Pexels or Pixabay API key above to enable live search. Nothing is faked — search stays disabled until a real key is configured.</p>}
        {results && !results.configured && <p className="text-[12px] text-amber-700 bg-amber-50 border border-amber-200 rounded-sm p-2.5" data-testid="ml-search-needssetup">{results.reason}</p>}
        {results?.configured && results.error && <p className="text-[12px] text-red-700 bg-red-50 border border-red-200 rounded-sm p-2.5" data-testid="ml-search-error">{results.error}</p>}
        {results?.configured && !results.error && results.results?.length === 0 && <p className="text-[12px] text-muted-foreground" data-testid="ml-search-empty">No matches for that search. Try a broader keyword.</p>}
        {results?.results?.length > 0 && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="ml-results">
            {results.results.map((it, i) => (
              <div key={i} className="border rounded-md p-2.5" data-testid={`ml-result-${i}`}>
                {it.preview_url && <img src={it.preview_url} alt="" className="w-full h-28 object-cover rounded-sm mb-2" />}
                <p className="text-[12px] font-medium text-navy truncate">{it.title || it.provider_asset_id}</p>
                <p className="text-[10px] text-muted-foreground">{it.creator_name} · {it.license_type}</p>
                <button onClick={() => registerAsset(it)} data-testid={`ml-register-${i}`} className="mt-1.5 text-[11px] inline-flex items-center gap-1 bg-gold text-navy px-2 py-1 rounded-sm font-medium"><Download className="w-3 h-3" /> Register to Vault</button>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* Collections + Vault */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Panel title="QRU Stockpile Collections" icon={Layers} accent="royal" testid="ml-collections">
          <p className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground mb-1.5">Video ({config.video_collections.length})</p>
          <div className="flex flex-wrap gap-1 mb-3">{config.video_collections.map((c) => <span key={c} className="text-[10px] px-1.5 py-0.5 rounded border bg-navy/[0.06] text-navy border-navy/15">{c}</span>)}</div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground mb-1.5">Audio ({config.audio_collections.length})</p>
          <div className="flex flex-wrap gap-1">{config.audio_collections.map((c) => <span key={c} className="text-[10px] px-1.5 py-0.5 rounded border bg-gold/12 text-navy border-gold/30">{c}</span>)}</div>
        </Panel>
        <Panel title={`Master Asset Vault (${assets.length})`} icon={CheckCircle2} accent="gold" testid="ml-vault">
          {assets.length === 0 ? <p className="text-sm text-muted-foreground">No assets registered yet. Connect a provider, search, and register clips here with full license provenance.</p> : (
            <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
              {assets.map((a) => (
                <div key={a.id} className="flex items-center justify-between border rounded-sm p-2 text-sm" data-testid={`ml-asset-${a.qru_asset_id}`}>
                  <div className="min-w-0"><p className="text-navy font-medium truncate">{a.title || a.qru_asset_id}</p><p className="text-[10px] font-mono text-muted-foreground">{a.provider} · {a.license_type}</p></div>
                  <StatusChip status={a.approval_status} tone={a.approval_status === "Approved" ? "emerald" : "amber"} />
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>

      {cfgDlg && <ProviderConfig p={cfgDlg} onClose={() => setCfgDlg(null)} onDone={() => { setCfgDlg(null); loadProviders(); }} />}
    </div>
  );
}

function ProviderConfig({ p, onClose, onDone }) {
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try { await api.post(`/media-library/providers/${p.id}/config`, { api_key: key }); toast.success(`${p.name} connected.`); onDone(); }
    catch (e) { toast.error(e.response?.data?.detail || "Could not save key"); }
    finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="ml-config-dialog">
      <div className="bg-card rounded-md max-w-md w-full p-5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <p className="font-heading font-bold text-navy flex items-center gap-2"><KeyRound className="w-4 h-4 text-royal" /> {p.name} · Developer Setup</p>
          <button onClick={onClose} data-testid="ml-config-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>
        <p className="text-xs text-muted-foreground mb-3">{p.hint}</p>
        <input data-testid="ml-config-key" type="password" value={key} onChange={(e) => setKey(e.target.value)} className="w-full border rounded-sm p-2 text-sm" placeholder="Paste API key" />
        <button onClick={save} disabled={busy || !key} data-testid="ml-config-save" className="w-full mt-3 bg-navy text-white px-4 py-2 rounded-sm text-sm disabled:opacity-60 inline-flex items-center justify-center gap-2">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />} Save & Connect
        </button>
        <p className="text-[10px] text-muted-foreground mt-2">Stored encrypted. Requests are proxied through the backend — the key is never exposed to the browser.</p>
      </div>
    </div>
  );
}
