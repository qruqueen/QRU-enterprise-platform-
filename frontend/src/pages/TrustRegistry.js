import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, ShieldCheck, Fingerprint, QrCode, ScrollText, Layers, Globe2, Lock, BadgeCheck,
  Award, History, CheckCircle2, Clock, Search,
} from "lucide-react";

const LAYER_TONE = { enforced: "emerald", configurable: "blue", platform_provided: "amber", planned: "slate" };
const LAYER_LABEL = { enforced: "Enforced Now", configurable: "Configurable", platform_provided: "Platform-Provided", planned: "Planned" };

export default function TrustRegistry() {
  const [config, setConfig] = useState(null);
  const [gov, setGov] = useState([]);
  const [products, setProducts] = useState([]);
  const [pid, setPid] = useState("");
  const [cert, setCert] = useState(null);
  const [busy, setBusy] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [records, setRecords] = useState([]);
  const [verifyCode, setVerifyCode] = useState("");
  const [verifyResult, setVerifyResult] = useState(null);

  const loadRegistry = () => api.get("/trust/registry").then((r) => setRecords(r.data.records)).catch(() => {});
  useEffect(() => {
    api.get("/trust/config").then((r) => setConfig(r.data)).catch(() => setConfig(false));
    api.get("/governance-binding/strip/trust").then((r) => setGov(r.data.governed_by)).catch(() => {});
    api.get("/founder-inbox").then((r) => setProducts((r.data.products || []).slice(0, 200))).catch(() => {});
    loadRegistry();
  }, []);

  const loadCert = async (id) => {
    setPid(id); setCert(null);
    if (!id) return;
    setBusy(true);
    try { const { data } = await api.get(`/trust/certificate/${id}`); setCert(data); }
    catch { toast.error("Could not load the certificate."); }
    finally { setBusy(false); }
  };

  const register = async () => {
    if (!pid) return;
    setRegistering(true);
    try {
      await api.post(`/trust/register/${pid}`);
      toast.success("Product registered in the Trust & Authenticity Registry™.");
      loadRegistry();
    } catch (e) { toast.error(e.response?.data?.detail || "Registration failed."); }
    finally { setRegistering(false); }
  };

  const runVerify = async () => {
    if (!verifyCode.trim()) return;
    try { const { data } = await api.get(`/trust/verify/${encodeURIComponent(verifyCode.trim())}`); setVerifyResult(data); }
    catch { toast.error("Verification lookup failed."); }
  };

  if (config === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (config === false) return <p className="text-sm text-muted-foreground p-8">Could not load the Trust & Authenticity System™.</p>;

  return (
    <div>
      <PageHeader
        overline="QRU Trust & Authenticity System™ · MO-015 / MO-016 / MO-017"
        title="Trust & Authenticity"
        description="Layered content protection, rights management, a permanent authenticity registry, and platform-aware controls — governed by FR-095 Protect Without Punishing™: protect QRU IP while preserving an excellent learning experience."
        actions={<VerifiedBadge label="QRU-SEAL™ · Treasure Standard™" testid="trust-badge" />}
      />
      <GovernedBy standards={gov} className="mb-4" testid="trust-governed-by" />

      {/* FR-095 */}
      <div className="qru-card p-4 mb-8 border-l-4 border-gold" data-testid="trust-factory-rule">
        <p className="overline text-gold mb-1">{config.factory_rule.id} · {config.factory_rule.title}</p>
        <p className="text-sm text-navy">{config.factory_rule.statement}</p>
      </div>

      {/* Protection layers */}
      <Panel title="Protection Layers" icon={Layers} accent="royal" testid="trust-layers" className="mb-8">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(config.protection_layers).map(([k, l]) => (
            <div key={k} className="border rounded-md p-3" data-testid={`trust-layer-${k}`}>
              <div className="flex items-center justify-between mb-1.5">
                <p className="text-sm font-semibold text-navy flex items-center gap-1.5"><Lock className="w-3.5 h-3.5 text-royal" /> {l.label}</p>
                <StatusChip status={LAYER_LABEL[l.status]} tone={LAYER_TONE[l.status]} />
              </div>
              <p className="text-[11px] text-muted-foreground mb-2">{l.detail}</p>
              <div className="flex flex-wrap gap-1">
                {l.features.map((f) => <span key={f} className="text-[10px] px-1.5 py-0.5 rounded bg-navy/[0.06] text-navy border border-navy/10">{f.replace(/_/g, " ")}</span>)}
              </div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Security levels + Platform capability awareness */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <Panel title="Security Levels" icon={ShieldCheck} accent="gold" testid="trust-security-levels">
          <div className="space-y-2">
            {Object.entries(config.security_levels).map(([k, s]) => (
              <div key={k} className="flex items-center justify-between border rounded-sm p-2.5" data-testid={`trust-seclevel-${k}`}>
                <div><p className="text-sm font-semibold text-navy">{s.label}</p><p className="text-[11px] text-muted-foreground">{s.detail}</p></div>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-gold/12 text-navy border border-gold/30">{s.requirement.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Platform Capability Awareness™ · MO-017" icon={Globe2} accent="royal" testid="trust-platforms">
          <div className="space-y-2 max-h-[360px] overflow-y-auto">
            {Object.entries(config.platform_capabilities).map(([k, c]) => (
              <div key={k} className="border rounded-sm p-2.5" data-testid={`trust-platform-${k}`}>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-semibold text-navy">{c.label}</p>
                  <span className="text-[10px] text-muted-foreground">{c.supported.length} native control(s)</span>
                </div>
                <p className="text-[11px] text-muted-foreground">{c.best_available}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* Certificate lookup */}
      <Panel title="Authenticity Certificate™ & Registry" icon={Fingerprint} accent="gold" testid="trust-cert-panel" className="mb-8">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end mb-4">
          <div className="flex-1">
            <label className="text-xs font-bold text-navy uppercase tracking-wide">Product</label>
            <select data-testid="trust-product" value={pid} onChange={(e) => loadCert(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
              <option value="">— Select a product —</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.product_code} — {p.title}</option>)}
            </select>
          </div>
          <button onClick={register} disabled={registering || !cert} data-testid="trust-register"
            className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
            {registering ? <Loader2 className="w-4 h-4 animate-spin" /> : <BadgeCheck className="w-4 h-4" />} Register in Trust Registry
          </button>
        </div>

        {busy && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Building certificate…</div>}

        {cert && (
          <div className="grid md:grid-cols-3 gap-4" data-testid="trust-cert">
            <div className="border rounded-md p-4 md:col-span-2">
              <div className="flex items-center gap-2 mb-3">
                <Award className="w-5 h-5 text-gold" />
                <div>
                  <p className="font-heading font-bold text-navy">{cert.authenticity_certificate}</p>
                  <p className="text-[11px] text-muted-foreground">{cert.qruseal} · {cert.author}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-y-2 text-[12px]">
                <p><span className="text-muted-foreground">QRU Product ID:</span> <b className="text-navy">{cert.qru_product_id}</b></p>
                <p><span className="text-muted-foreground">Version:</span> <b className="text-navy">{cert.version}</b></p>
                <p><span className="text-muted-foreground">Treasure Standard™:</span> <StatusChip status={cert.treasure_standard_status} tone={cert.treasure_standard_status === "Met" ? "emerald" : "amber"} /></p>
                <p><span className="text-muted-foreground">Gold Standard™:</span> <StatusChip status={cert.gold_standard_status} tone={cert.gold_standard_status === "Met" ? "emerald" : "blue"} /></p>
                <p className="col-span-2"><span className="text-muted-foreground">Copyright:</span> <span className="text-navy">{cert.copyright}</span></p>
              </div>
              <p className="overline text-muted-foreground mt-4 mb-1.5 flex items-center gap-1"><History className="w-3 h-3" /> Approval History</p>
              <div className="space-y-1">
                {cert.approval_history.length === 0 ? <p className="text-[11px] text-muted-foreground">No approval events recorded yet.</p> :
                  cert.approval_history.map((h, i) => (
                    <div key={i} className="flex items-center gap-2 text-[11px]" data-testid={`trust-approval-${i}`}>
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                      <span className="text-navy font-medium">{h.stage}</span>
                      <span className="text-muted-foreground">— {h.decision} · {h.authority}</span>
                    </div>
                  ))}
              </div>
            </div>
            <div className="border rounded-md p-4 flex flex-col items-center justify-center text-center">
              <p className="overline text-muted-foreground mb-2 flex items-center gap-1"><QrCode className="w-3 h-3" /> Verify Authenticity</p>
              <img src={cert.qr_code} alt="Authenticity QR" className="w-36 h-36" data-testid="trust-qr" />
              <p className="text-[10px] text-muted-foreground mt-2 break-all">{cert.verify_url}</p>
            </div>
          </div>
        )}
      </Panel>

      {/* Public verification + Registry */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Panel title="Public Authenticity Lookup" icon={Search} accent="royal" testid="trust-verify-panel">
          <div className="flex gap-2 mb-3">
            <input data-testid="trust-verify-input" value={verifyCode} onChange={(e) => setVerifyCode(e.target.value)} onKeyDown={(e) => e.key === "Enter" && runVerify()}
              placeholder="Enter a QRU Product ID (e.g. PRD-00078)" className="flex-1 border rounded-sm p-2 text-sm" />
            <button onClick={runVerify} data-testid="trust-verify-run" className="bg-navy text-white px-4 rounded-sm text-sm font-medium">Verify</button>
          </div>
          {verifyResult && (
            <div className={`border rounded-md p-3 ${verifyResult.found && verifyResult.authentic ? "border-emerald-300 bg-emerald-50" : "border-amber-300 bg-amber-50"}`} data-testid="trust-verify-result">
              <p className="text-sm font-semibold text-navy flex items-center gap-1.5">
                {verifyResult.found && verifyResult.authentic ? <BadgeCheck className="w-4 h-4 text-emerald-600" /> : <Clock className="w-4 h-4 text-amber-600" />}
                {verifyResult.found ? verifyResult.title : "Not Found"}
              </p>
              <p className="text-[12px] text-navy mt-1">{verifyResult.message}</p>
              {verifyResult.found && <p className="text-[11px] text-muted-foreground mt-1">{verifyResult.qruseal} · v{verifyResult.version} · {verifyResult.active_status}</p>}
            </div>
          )}
        </Panel>
        <Panel title={`Trust Registry (${records.length})`} icon={ScrollText} accent="gold" testid="trust-registry">
          {records.length === 0 ? <p className="text-sm text-muted-foreground">No products registered yet. Select a product above and click Register.</p> : (
            <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
              {records.map((r) => (
                <div key={r.id} className="flex items-center justify-between border rounded-sm p-2 text-sm" data-testid={`trust-record-${r.product_code}`}>
                  <div className="min-w-0"><p className="text-navy font-medium truncate">{r.title}</p><p className="text-[10px] font-mono text-muted-foreground">{r.certificate_id}</p></div>
                  <StatusChip status={r.registry.active_status} tone={r.registry.active_status === "Active" ? "emerald" : "slate"} />
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
