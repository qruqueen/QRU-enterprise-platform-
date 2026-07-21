import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, Radio, Store, Youtube, Globe, HardDrive, Mail, ShoppingBag, BookText, PackageCheck,
  CheckCircle2, XCircle, RotateCw, ShieldCheck, BarChart3, ExternalLink, Send, Lock, Settings2, KeyRound, X,
} from "lucide-react";

const CAT_ICON = { Store, Video: Youtube, Blog: Globe, Storage: HardDrive, Email: Mail, Marketplace: ShoppingBag };
const JOB_TONE = { published: "emerald", delivered: "emerald", private: "slate", unlisted: "amber", scheduled: "amber", failed: "red", needs_setup: "blue", queued: "navy" };

export default function DistributionCenter() {
  const nav = useNavigate();
  const [connectors, setConnectors] = useState([]);
  const [products, setProducts] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [productId, setProductId] = useState("");
  const [selected, setSelected] = useState({}); // connector_id -> mode
  const [busy, setBusy] = useState(false);
  const [analytics, setAnalytics] = useState({}); // job_id -> data
  const [configDlg, setConfigDlg] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadConnectors = () => api.get("/distribution/connectors").then((r) => setConnectors(r.data.connectors)).catch(() => {});
  const loadJobs = () => api.get("/distribution/jobs").then((r) => setJobs(r.data.jobs)).catch(() => {});
  useEffect(() => {
    Promise.all([
      loadConnectors(),
      api.get("/founder-inbox").then((r) => setProducts((r.data.products || []).slice(0, 200))),
      loadJobs(),
    ]).finally(() => setLoading(false));
  }, []);

  const toggle = (c) => {
    setSelected((prev) => {
      const next = { ...prev };
      if (next[c.id]) delete next[c.id];
      else next[c.id] = c.modes.includes("public") ? "public" : c.modes[0];
      return next;
    });
  };

  const distribute = async () => {
    if (!productId) return toast.error("Select a product to distribute.");
    const targets = Object.entries(selected).map(([connector_id, mode]) => ({ connector_id, mode }));
    if (!targets.length) return toast.error("Select at least one destination.");
    setBusy(true);
    try {
      const { data } = await api.post("/distribution/distribute", { product_id: productId, targets });
      toast.success(`Distributed: ${data.distributed} · Failed: ${data.failed} · Needs setup: ${data.needs_setup}`);
      loadJobs();
    } catch (e) { toast.error(e.response?.data?.detail || "Distribution failed"); }
    finally { setBusy(false); }
  };

  const verify = async (id) => {
    try { const { data } = await api.post(`/distribution/jobs/${id}/verify`); toast[data.verified ? "success" : "error"](data.detail); loadJobs(); }
    catch (e) { toast.error(e.response?.data?.detail || "Verify failed"); }
  };
  const retry = async (id) => {
    try { await api.post(`/distribution/jobs/${id}/retry`); toast.success("Retried"); loadJobs(); }
    catch (e) { toast.error(e.response?.data?.detail || "Retry failed"); }
  };
  const loadAnalytics = async (id) => {
    try { const { data } = await api.get(`/distribution/jobs/${id}/analytics`); setAnalytics((p) => ({ ...p, [id]: data })); }
    catch { toast.error("No analytics available"); }
  };

  if (loading) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div>
      <PageHeader
        overline="QRU Universal Distribution Framework™ · MO-007"
        title="Distribution Center"
        description="Manufacture once, publish everywhere — verified. Every destination implements one Connector SDK™; the Publishing, Delivery, Verification and Analytics engines run one consistent workflow: distribute → verify → store external IDs → analytics."
        actions={<VerifiedBadge label="Connector SDK™ · Treasure Standard™" testid="dist-badge" />}
      />

      <button onClick={() => nav("/shipping-status")} data-testid="open-publish-dashboard"
        className="w-full mb-6 flex items-center justify-between gap-3 rounded-lg border border-royal/30 bg-royal/[0.05] hover:bg-royal/[0.09] transition-colors p-4 text-left">
        <div className="flex items-center gap-3">
          <PackageCheck className="w-5 h-5 text-royal shrink-0" />
          <div>
            <p className="text-sm font-bold text-navy">Publish Success Dashboard™</p>
            <p className="text-[11px] text-muted-foreground">The definitive 8-stage shipping status for every product — Knowledge → Manufacturing → QA → Authorized → Published → Store Sync → Purchase → Delivery.</p>
          </div>
        </div>
        <ExternalLink className="w-4 h-4 text-royal shrink-0" />
      </button>

      {/* Connectors grid */}
      <p className="overline text-royal mb-3 flex items-center gap-1.5"><Radio className="w-3.5 h-3.5" /> Connectors ({connectors.length})</p>
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-8" data-testid="dist-connectors">
        {connectors.map((c) => {
          const Icon = CAT_ICON[c.category] || Send;
          const on = !!selected[c.id];
          return (
            <div key={c.id} data-testid={`connector-${c.id}`} onClick={() => c.can_distribute && toggle(c)}
              className={`text-left qru-card p-4 transition-all ${on ? "border-navy ring-1 ring-navy" : c.can_distribute ? "qru-interactive cursor-pointer" : "opacity-70"}`}>
              <div className="flex items-center justify-between mb-2">
                <Icon className={`w-5 h-5 ${c.native ? "text-gold" : "text-royal"}`} />
                <StatusChip status={c.can_distribute ? "Connected" : "Developer Setup Required"} tone={c.can_distribute ? "emerald" : "blue"} />
              </div>
              <p className="font-heading font-bold text-navy text-[15px]">{c.name}</p>
              <p className="text-[11px] text-muted-foreground">{c.category} · {c.kind === "publish" ? "Publishing" : "Delivery"} · {c.native ? "Native" : "External"}</p>
              {c.can_distribute && on && (
                <select data-testid={`mode-${c.id}`} value={selected[c.id]} onClick={(e) => e.stopPropagation()} onChange={(e) => setSelected((p) => ({ ...p, [c.id]: e.target.value }))}
                  className="mt-2 w-full border rounded-sm p-1 text-xs">
                  {c.modes.map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              )}
              {c.requires_file && <p className="text-[10px] text-amber-600 mt-1 flex items-center gap-1"><Lock className="w-2.5 h-2.5" /> requires a file asset</p>}
              {c.configurable && !c.can_distribute && (
                <span role="button" tabIndex={0} data-testid={`config-${c.id}`}
                  onClick={(e) => { e.stopPropagation(); setConfigDlg(c); }}
                  className="mt-2 inline-flex items-center gap-1 text-[11px] text-royal font-semibold hover:underline cursor-pointer">
                  <Settings2 className="w-3 h-3" /> Developer Setup
                </span>
              )}
              {c.configurable && c.can_distribute && (
                <span role="button" tabIndex={0} data-testid={`reconfig-${c.id}`}
                  onClick={(e) => { e.stopPropagation(); setConfigDlg(c); }}
                  className="mt-2 inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-navy cursor-pointer">
                  <Settings2 className="w-3 h-3" /> Edit credentials
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Distribute bar */}
      <Panel title="Distribute a Product" icon={Send} accent="gold" testid="dist-composer" className="mb-8">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end">
          <div className="flex-1">
            <label className="text-xs font-bold text-navy uppercase tracking-wide">Product</label>
            <select data-testid="dist-product" value={productId} onChange={(e) => setProductId(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
              <option value="">— Select a manufactured product —</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.product_code} — {p.title} ({p.status})</option>)}
            </select>
          </div>
          <button onClick={distribute} disabled={busy || !productId || !Object.keys(selected).length} data-testid="dist-distribute"
            className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />} Distribute to {Object.keys(selected).length || 0} destination(s)
          </button>
        </div>
        <p className="text-[11px] text-muted-foreground mt-2">Video connectors (YouTube) need a file — use <button onClick={() => nav("/youtube")} className="text-royal font-semibold underline">YouTube Publisher™</button>. QRU Store™ lists instantly.</p>
      </Panel>

      {/* Jobs */}
      <Panel title={`Distribution Jobs (${jobs.length})`} icon={Radio} testid="dist-jobs" className="overflow-hidden">
        {jobs.length === 0 ? <p className="text-sm text-muted-foreground">No distribution jobs yet.</p> : (
          <div className="overflow-x-auto -m-5">
            <table className="w-full text-sm">
              <thead className="bg-muted/40"><tr>{["Product", "Destination", "Mode", "Status", "External ID", "Actions"].map((h) => <th key={h} className="text-left font-bold text-navy px-5 py-2.5 text-[11px] uppercase tracking-wide whitespace-nowrap">{h}</th>)}</tr></thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id} className="border-t border-border align-top" data-testid={`job-${j.id}`}>
                    <td className="px-5 py-2.5 text-navy max-w-[220px] truncate">{j.product_title}</td>
                    <td className="px-5 py-2.5 text-xs text-navy font-medium">{j.connector_name}</td>
                    <td className="px-5 py-2.5 text-xs text-muted-foreground">{j.mode}</td>
                    <td className="px-5 py-2.5">
                      <StatusChip status={j.status.replace(/_/g, " ")} tone={JOB_TONE[j.status]} />
                      {j.verified && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 inline ml-1" title="Verified" />}
                      {j.detail && <p className="text-[10px] text-muted-foreground mt-1 max-w-[240px]">{j.detail}</p>}
                    </td>
                    <td className="px-5 py-2.5 text-xs">
                      {j.external_id ? (
                        j.url ? <a href={j.url} target={j.url.startsWith("http") ? "_blank" : undefined} rel="noreferrer" className="text-royal font-mono inline-flex items-center gap-1">{j.external_id.slice(0, 14)}… <ExternalLink className="w-3 h-3" /></a>
                          : <span className="font-mono text-muted-foreground">{j.external_id.slice(0, 16)}…</span>
                      ) : "—"}
                      {analytics[j.id]?.metrics && <p className="text-[10px] text-navy mt-1">{Object.entries(analytics[j.id].metrics).map(([k, v]) => `${k}: ${v}`).join(" · ")}</p>}
                    </td>
                    <td className="px-5 py-2.5">
                      <div className="flex gap-1.5">
                        {j.external_id && <button onClick={() => verify(j.id)} data-testid={`verify-${j.id}`} title="Verify" className="p-1.5 rounded border hover:border-navy"><ShieldCheck className="w-3.5 h-3.5 text-navy" /></button>}
                        {j.status === "failed" && <button onClick={() => retry(j.id)} data-testid={`retry-${j.id}`} title="Retry" className="p-1.5 rounded border hover:border-navy"><RotateCw className="w-3.5 h-3.5 text-royal" /></button>}
                        {j.external_id && <button onClick={() => loadAnalytics(j.id)} data-testid={`analytics-${j.id}`} title="Analytics" className="p-1.5 rounded border hover:border-navy"><BarChart3 className="w-3.5 h-3.5 text-gold" /></button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
      {configDlg && <ConnectorConfigDialog c={configDlg} onClose={() => setConfigDlg(null)} onDone={() => { setConfigDlg(null); loadConnectors(); }} />}
    </div>
  );
}

const FIELD_LABELS = {
  site_url: "Site URL", username: "Username", app_password: "Application Password",
  api_key: "API Key", store_domain: "Store Domain", access_token: "Admin API Access Token",
};

function ConnectorConfigDialog({ c, onClose, onDone }) {
  const [vals, setVals] = useState({});
  const [busy, setBusy] = useState(false);
  const secret = c.config_secret || [];

  const save = async () => {
    setBusy(true);
    try {
      await api.post(`/distribution/connectors/${c.id}/config`, { credentials: vals });
      toast.success(`${c.name} configured. Testing connection…`);
      onDone();
    } catch (e) { toast.error(e.response?.data?.detail || "Could not save credentials"); }
    finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose} data-testid="connector-config-dialog">
      <div className="bg-card rounded-md max-w-md w-full p-5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <p className="font-heading font-bold text-navy flex items-center gap-2"><Settings2 className="w-4 h-4 text-royal" /> {c.name} · Developer Setup</p>
          <button onClick={onClose} data-testid="connector-config-close"><X className="w-5 h-5 text-muted-foreground" /></button>
        </div>
        {c.config_hint && <p className="text-xs text-muted-foreground mb-3">{c.config_hint}</p>}
        <div className="space-y-3">
          {(c.config_fields || []).map((f) => (
            <div key={f}>
              <label className="text-xs font-medium text-navy flex items-center gap-1">
                {secret.includes(f) && <KeyRound className="w-3.5 h-3.5" />} {FIELD_LABELS[f] || f}
              </label>
              <input data-testid={`config-field-${f}`} type={secret.includes(f) ? "password" : "text"}
                value={vals[f] || ""} onChange={(e) => setVals((p) => ({ ...p, [f]: e.target.value }))}
                className="w-full mt-1 border rounded-sm p-2 text-sm" placeholder={`Enter ${FIELD_LABELS[f] || f}`} />
            </div>
          ))}
          <button onClick={save} disabled={busy || (c.config_fields || []).some((f) => !vals[f])} data-testid="connector-config-save"
            className="w-full bg-navy text-white px-4 py-2 rounded-sm text-sm disabled:opacity-60 inline-flex items-center justify-center gap-2">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />} Save & Verify
          </button>
          <p className="text-[10px] text-muted-foreground flex items-start gap-1"><Lock className="w-3 h-3 mt-0.5 shrink-0" /> Secrets are encrypted at rest. Treasure Standard™: the connector only reports “Connected” after QRU confirms real access.</p>
        </div>
      </div>
    </div>
  );
}
