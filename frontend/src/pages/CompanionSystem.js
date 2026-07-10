import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, QrCode, Sparkles, CheckCircle2, Clock, Compass, Fingerprint, BarChart3, Rocket,
  BookOpen, Layers, Radio,
} from "lucide-react";

export default function CompanionSystem() {
  const [config, setConfig] = useState(null);
  const [gov, setGov] = useState([]);
  const [products, setProducts] = useState([]);
  const [pid, setPid] = useState("");
  const [busy, setBusy] = useState(false);
  const [portal, setPortal] = useState(null);
  const [portals, setPortals] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  const loadPortals = () => api.get("/qics/portals").then((r) => setPortals(r.data.portals)).catch(() => {});
  useEffect(() => {
    api.get("/qics/config").then((r) => setConfig(r.data)).catch(() => setConfig(false));
    api.get("/governance-binding/strip/trust").then((r) => setGov(r.data.governed_by)).catch(() => {});
    api.get("/founder-inbox").then((r) => setProducts((r.data.products || []).slice(0, 200))).catch(() => {});
    loadPortals();
  }, []);

  const activate = async () => {
    if (!pid) return;
    setBusy(true); setPortal(null); setAnalytics(null);
    try {
      const { data } = await api.post(`/qics/activate/${pid}`);
      setPortal(data);
      const a = await api.get(`/qics/analytics/${pid}`);
      setAnalytics(a.data);
      toast.success(`Companion Portal™ activated · ${data.qics_identity}`);
      loadPortals();
    } catch (e) { toast.error(e.response?.data?.detail || "Activation failed."); }
    finally { setBusy(false); }
  };

  if (config === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (config === false) return <p className="text-sm text-muted-foreground p-8">Could not load the Companion System.</p>;

  return (
    <div>
      <PageHeader
        overline="QRU Intelligent Companion System™ · MO-018 (QICS)"
        title="Intelligent Companion System"
        description="Every product continues beyond the page. A Gold Standard product receives an immutable QRU identity, a permanent dynamic QR gateway, and a living Companion Portal™ connecting the product to its media, resources, assessments, updates and related products — one connected ecosystem."
        actions={<VerifiedBadge label="QICS · Treasure Standard™" testid="qics-badge" />}
      />
      <GovernedBy standards={gov} className="mb-4" testid="qics-governed-by" />

      {/* FR-096 */}
      <div className="qru-card p-4 mb-8 border-l-4 border-gold" data-testid="qics-factory-rule">
        <p className="overline text-gold mb-1">{config.factory_rule.id} · {config.factory_rule.title}</p>
        <p className="text-sm text-navy">{config.factory_rule.statement}</p>
      </div>

      {/* Activate */}
      <Panel title="Activate a Companion Portal™" icon={Rocket} accent="gold" testid="qics-activator" className="mb-8">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end">
          <div className="flex-1">
            <label className="text-xs font-bold text-navy uppercase tracking-wide">Product</label>
            <select data-testid="qics-product" value={pid} onChange={(e) => setPid(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
              <option value="">— Select a Gold Standard product —</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.product_code} — {p.title}</option>)}
            </select>
          </div>
          <button onClick={activate} disabled={busy || !pid} data-testid="qics-activate"
            className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Activate Companion
          </button>
        </div>

        {portal && (
          <div className="grid md:grid-cols-3 gap-4 mt-5" data-testid="qics-portal">
            <div className="border rounded-md p-4 md:col-span-2">
              <div className="flex items-center gap-2 mb-2">
                <Fingerprint className="w-5 h-5 text-royal" />
                <div>
                  <p className="font-heading font-bold text-navy">{portal.qics_identity}</p>
                  <p className="text-[11px] text-muted-foreground">{portal.portal.resource_home} · {portal.portal.available_count}/{portal.portal.section_total} sections live</p>
                </div>
              </div>
              <div className="grid sm:grid-cols-2 gap-1.5">
                {Object.entries(portal.portal.sections).map(([k, s]) => (
                  <div key={k} className="flex items-center gap-1.5 text-[11px]" data-testid={`qics-section-${k}`}>
                    {s.status === "available" ? <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" /> : <Clock className="w-3 h-3 text-amber-500 shrink-0" />}
                    <span className="text-navy capitalize">{k.replace(/_/g, " ")}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="border rounded-md p-4 flex flex-col items-center text-center">
              <p className="overline text-muted-foreground mb-2 flex items-center gap-1"><QrCode className="w-3 h-3" /> Dynamic QR Gateway</p>
              <img src={portal.qr_code} alt="Companion QR" className="w-32 h-32" data-testid="qics-qr" />
              <p className="text-[10px] text-emerald-600 mt-2">Permanent · destination updatable · never expires</p>
            </div>
          </div>
        )}

        {analytics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4" data-testid="qics-analytics">
            {[["Scans", analytics.scan_count], ["Repeat Scans", analytics.repeat_scans],
              ["Downloads", analytics.resource_downloads], ["Total Events", analytics.total_events]].map(([l, v]) => (
              <div key={l} className="qru-card p-3">
                <p className="font-heading text-2xl font-bold text-navy">{v}</p>
                <p className="text-[11px] text-muted-foreground">{l}</p>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* Identity + resources */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <Panel title="Immutable Identity Formats" icon={Fingerprint} accent="royal" testid="qics-identity-formats">
          <div className="grid grid-cols-2 gap-1.5">
            {Object.entries(config.identity_formats).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between border rounded-sm p-2 text-[12px]">
                <span className="text-muted-foreground capitalize">{k.replace(/_/g, " ")}</span>
                <span className="font-mono text-navy font-semibold">{v}</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Companion Resource Catalog" icon={Layers} accent="gold" testid="qics-resources">
          <div className="flex flex-wrap gap-1.5">
            {config.resource_catalog.map((r) => (
              <span key={r} className="text-[10px] px-1.5 py-0.5 rounded border bg-navy/[0.06] text-navy border-navy/15 capitalize">{r.replace(/_/g, " ")}</span>
            ))}
          </div>
          <p className="overline text-muted-foreground mt-4 mb-1.5">Future Support (Roadmap)</p>
          <div className="flex flex-wrap gap-1.5">
            {config.future_support.map((f) => (
              <span key={f} className="text-[10px] px-1.5 py-0.5 rounded border bg-muted text-muted-foreground border-border capitalize">{f.replace(/_/g, " ")}</span>
            ))}
          </div>
        </Panel>
      </div>

      {/* Portals list */}
      <Panel title={`Active Companion Portals (${portals.length})`} icon={Radio} accent="royal" testid="qics-portals">
        {portals.length === 0 ? <p className="text-sm text-muted-foreground">No companion portals activated yet. Select a product above and click Activate.</p> : (
          <div className="space-y-1.5 max-h-[320px] overflow-y-auto">
            {portals.map((p) => (
              <div key={p.id} className="flex items-center justify-between border rounded-sm p-2.5 text-sm" data-testid={`qics-portal-${p.qics_identity}`}>
                <div className="min-w-0 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-gold shrink-0" />
                  <div className="min-w-0"><p className="text-navy font-medium truncate">{p.title}</p><p className="text-[10px] font-mono text-muted-foreground">{p.qics_identity}</p></div>
                </div>
                <StatusChip status="Live" tone="emerald" />
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
