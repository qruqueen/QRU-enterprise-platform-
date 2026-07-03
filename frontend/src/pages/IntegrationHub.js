import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Plug, ShieldCheck, Loader2, Radio, Route as RouteIcon, Trash2, Send } from "lucide-react";

export default function IntegrationHub() {
  const [catalog, setCatalog] = useState({});
  const [oauth, setOauth] = useState([]);
  const [connections, setConnections] = useState([]);
  const [monitor, setMonitor] = useState(null);
  const [routing, setRouting] = useState({});
  const [form, setForm] = useState({ platform: "", account_name: "", display_name: "", store_name: "", channel_name: "", publisher_name: "", credential: "", default_pricing: "" });
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const [c, cn, m, r] = await Promise.all([
      api.get("/integrations/catalog"), api.get("/integrations/connections"),
      api.get("/integrations/monitor"), api.get("/integrations/routing"),
    ]);
    setCatalog(c.data.catalog); setOauth(c.data.oauth_platforms);
    setConnections(cn.data); setMonitor(m.data); setRouting(r.data.rules);
  };
  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.platform) { toast.error("Select a platform"); return; }
    setSaving(true);
    try {
      await api.post("/integrations/connections", form);
      toast.success(`${form.platform} configured`);
      setForm({ platform: "", account_name: "", display_name: "", store_name: "", channel_name: "", publisher_name: "", credential: "", default_pricing: "" });
      load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  const test = async (id) => { try { await api.post(`/integrations/connections/${id}/test`); toast.success("Connection tested"); load(); } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } };
  const del = async (id) => { try { await api.delete(`/integrations/connections/${id}`); toast.success("Removed"); load(); } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } };

  const allPlatforms = Object.entries(catalog);
  const isOauth = oauth.includes(form.platform);

  return (
    <div className="space-y-8" data-testid="integration-hub-page">
      <div>
        <p className="overline text-primary mb-1">Connect Once · Manufacture Forever · Distribute Everywhere</p>
        <h1 className="font-heading text-3xl font-bold tracking-tight">QRU Integration Hub™</h1>
        <p className="text-muted-foreground text-sm mt-1">Configure each platform once. The factory publishes & distributes automatically.</p>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-sm p-3 text-xs text-amber-800" data-testid="hub-simulation-note">
        Live external publishing runs through a connector layer. Platforms are <strong>SIMULATED</strong> until their real OAuth/API credentials are activated — the full manufacture → publish → distribute workflow operates end-to-end today.
      </div>

      {monitor && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[["Platforms Configured", monitor.platforms_configured], ["Connected", monitor.platforms_connected],
            ["Distributions", monitor.distributions_total], ["Failed", monitor.distributions_failed],
            ["Open Issues", monitor.open_distribution_escalations]].map(([l, v]) => (
            <div key={l} className="bg-card border rounded-sm p-4"><p className="text-2xl font-heading font-bold">{v}</p><p className="text-xs text-muted-foreground mt-1">{l}</p></div>
          ))}
        </div>
      )}

      {/* Configure a connection */}
      <div className="bg-card border rounded-sm p-6">
        <div className="flex items-center gap-2 mb-4"><Plug className="w-4 h-4 text-gold" /><h2 className="font-heading font-semibold">Configure a Platform</h2></div>
        <div className="grid md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-muted-foreground">Platform</label>
            <select data-testid="hub-platform-select" value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value })}
              className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm">
              <option value="">Select…</option>
              {allPlatforms.map(([cat, ps]) => (
                <optgroup key={cat} label={cat}>{ps.map((p) => <option key={p} value={p}>{p}</option>)}</optgroup>
              ))}
            </select>
          </div>
          <div><label className="text-xs text-muted-foreground">Account / Store / Channel name</label>
            <input data-testid="hub-account-name" value={form.account_name} onChange={(e) => setForm({ ...form, account_name: e.target.value, store_name: e.target.value })}
              className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm" /></div>
          <div><label className="text-xs text-muted-foreground">{isOauth ? "OAuth token" : "API key"} (encrypted)</label>
            <input data-testid="hub-credential" type="password" value={form.credential} onChange={(e) => setForm({ ...form, credential: e.target.value })}
              placeholder={form.platform ? (isOauth ? "OAuth access token" : "API key") : ""}
              className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm" /></div>
          <div><label className="text-xs text-muted-foreground">Publisher name</label>
            <input value={form.publisher_name} onChange={(e) => setForm({ ...form, publisher_name: e.target.value })} className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm" /></div>
          <div><label className="text-xs text-muted-foreground">Default pricing</label>
            <input value={form.default_pricing} onChange={(e) => setForm({ ...form, default_pricing: e.target.value })} placeholder="e.g. $9.99" className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm" /></div>
          <div className="flex items-end">
            <button data-testid="hub-save-btn" onClick={save} disabled={saving}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium disabled:opacity-60">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plug className="w-4 h-4" />} Save Connection
            </button>
          </div>
        </div>
      </div>

      {/* Connections */}
      <div className="bg-card border rounded-sm">
        <div className="flex items-center gap-2 p-4 border-b"><Radio className="w-4 h-4 text-primary" /><h2 className="font-heading font-semibold">Connections</h2></div>
        <div className="divide-y">
          {connections.length === 0 && <p className="p-6 text-sm text-muted-foreground text-center">No platforms configured yet.</p>}
          {connections.map((c) => (
            <div key={c.id} className="flex items-center justify-between p-4" data-testid={`hub-conn-${c.id}`}>
              <div>
                <p className="font-medium text-sm">{c.platform} <span className="text-xs text-muted-foreground">· {c.category} · {c.auth_type}</span></p>
                <p className="text-xs text-muted-foreground">{c.account_name || c.store_name || "—"} · {c.has_credentials ? "credentials stored (encrypted)" : "no credentials"}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[11px] px-2 py-0.5 rounded-full ${c.connection_health === "healthy" ? "bg-emerald-100 text-emerald-700" : c.connection_health === "error" || c.connection_health === "expired" ? "bg-red-100 text-red-700" : "bg-muted text-muted-foreground"}`}>{c.status} · {c.connection_health}</span>
                <button data-testid={`hub-test-${c.id}`} onClick={() => test(c.id)} className="flex items-center gap-1 text-xs px-2 py-1 rounded-sm border hover:bg-muted"><ShieldCheck className="w-3 h-3" /> Test</button>
                <button onClick={() => del(c.id)} className="text-muted-foreground hover:text-destructive p-1"><Trash2 className="w-3.5 h-3.5" /></button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Smart routing */}
      <div className="bg-card border rounded-sm">
        <div className="flex items-center gap-2 p-4 border-b"><RouteIcon className="w-4 h-4 text-primary" /><h2 className="font-heading font-semibold">Smart Routing</h2>
          <span className="text-xs text-muted-foreground ml-1">Each product type auto-routes to its platforms.</span></div>
        <div className="grid md:grid-cols-2 gap-x-8 gap-y-1 p-4 text-sm">
          {Object.entries(routing).map(([ptype, targets]) => (
            <div key={ptype} className="flex items-center justify-between py-1 border-b border-dashed">
              <span className="font-medium">{ptype}</span>
              <span className="text-xs text-muted-foreground flex items-center gap-1"><Send className="w-3 h-3" /> {targets.join(", ")}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
