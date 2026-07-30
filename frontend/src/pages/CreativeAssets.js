import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, Layers, FileCog, UploadCloud, CheckCircle2, XCircle, AlertTriangle,
  Lock, ShieldCheck, Package, QrCode, Ban, RefreshCw,
} from "lucide-react";

const STATE_TONE = {
  Locked: "bg-emerald-100 text-emerald-700", Approved: "bg-emerald-50 text-emerald-700",
  "Under Review": "bg-blue-50 text-blue-700", "Rights Hold": "bg-amber-100 text-amber-700",
  Rejected: "bg-red-100 text-red-700", "Distribution Authorized": "bg-emerald-100 text-emerald-700",
};
const RESULT_TONE = {
  PASS: "bg-emerald-100 text-emerald-700", "PASS WITH WARNINGS": "bg-amber-100 text-amber-700",
  FAIL: "bg-red-100 text-red-700", HOLD: "bg-amber-100 text-amber-700",
};
const RIGHTS_OK = { creator: "QRU Design Studio", creation_method: "governed manufacturing",
  license: "QRU-owned", commercial_use_authorization: true, ai_disclosure_status: "No AI used" };
const MARKETPLACES = ["etsy", "amazon_kdp", "tpt", "shopify", "qru_online"];

const fileToB64 = (file) => new Promise((res, rej) => {
  const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(file);
});

function Badge({ tone, children, testid }) {
  return <span data-testid={testid} className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold ${tone || "bg-muted text-muted-foreground"}`}>{children}</span>;
}

export default function CreativeAssets() {
  const [books, setBooks] = useState([]);
  const [sel, setSel] = useState("");
  const [inherited, setInherited] = useState([]);
  const [assets, setAssets] = useState([]);
  const [spec, setSpec] = useState(null);
  const [busy, setBusy] = useState("");
  const [pkg, setPkg] = useState(null);
  const [rightsOk, setRightsOk] = useState(true);
  const [qrUrl, setQrUrl] = useState("");

  useEffect(() => {
    api.get("/book-mfg/books").then(({ data }) => setBooks(data.books || [])).catch(() => {});
  }, []);

  const load = useCallback(async (id) => {
    if (!id) return;
    const [inh, asr] = await Promise.all([
      api.get(`/creative-assets/inherited/book/${id}`),
      api.get(`/creative-assets/assets/book/${id}`),
    ]);
    setInherited(inh.data.inherited_specs || []);
    setAssets(asr.data.assets || []);
  }, []);

  useEffect(() => { if (sel) load(sel); }, [sel, load]);

  const genSpec = async (role, platform) => {
    setBusy(`spec-${platform}`);
    try {
      const { data } = await api.post(`/creative-assets/spec/book/${sel}`, { asset_role: role, platform_id: platform, pages: 120 });
      setSpec(data); toast.success(`Specification generated (${data.spec_id}).`);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(""); }
  };

  const uploadArtwork = async (role, platform, file) => {
    if (!file) return;
    setBusy(`up-${platform}`);
    try {
      const b64 = await fileToB64(file);
      const { data } = await api.post(`/creative-assets/upload/book/${sel}`, {
        asset_role: role, platform_id: platform, filename: file.name, file_base64: b64, pages: 120,
        rights: rightsOk ? RIGHTS_OK : null, expected_qr_url: qrUrl || null,
      });
      const v = data.validation;
      toast[v.result === "FAIL" || v.result === "HOLD" ? "error" : "success"](`Validation: ${v.result}`);
      await load(sel);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(""); }
  };

  const setState = async (assetId, state) => {
    setBusy(`st-${assetId}`);
    try {
      await api.post(`/creative-assets/assets/${assetId}/state`, { state });
      toast.success(`Asset → ${state}`); await load(sel);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(""); }
  };

  const buildPackage = async (mk) => {
    setBusy(`pkg-${mk}`);
    try {
      const { data } = await api.get(`/creative-assets/package/book/${sel}`, { params: { marketplace: mk } });
      setPkg(data);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(""); }
  };

  const assetsFor = (role, platform) => assets.filter((a) => a.asset_role === role && a.platform_id === platform);

  return (
    <div className="space-y-6" data-testid="creative-assets-page">
      <PageHeader title="Creative Assets™" subtitle="Universal Creative Asset Manufacturing System™ (STD-UCAMS-0001) — specify, validate, approve, lock & package every visual asset." icon={Layers} />

      <div className="rounded-lg border bg-card p-4">
        <label className="text-xs font-semibold text-navy uppercase tracking-wide">Product</label>
        <select data-testid="ca-product-select" value={sel} onChange={(e) => { setSel(e.target.value); setSpec(null); setPkg(null); }}
          className="mt-2 block w-full rounded-md border px-3 py-2 text-sm">
          <option value="">Select a product…</option>
          {books.map((b) => <option key={b.id} value={b.id}>{b.book_code} — {b.title}</option>)}
        </select>
        {sel && (
          <div className="mt-3 flex flex-wrap gap-4 items-center text-[12px]">
            <label className="flex items-center gap-2 cursor-pointer" data-testid="ca-rights-ok">
              <input type="checkbox" checked={rightsOk} onChange={(e) => setRightsOk(e.target.checked)} className="accent-navy" />
              Confirm QRU owns the rights (creator, license, commercial use, no AI)
            </label>
            <span className="flex items-center gap-1"><QrCode className="w-3.5 h-3.5" />
              <input data-testid="ca-qr-url" value={qrUrl} onChange={(e) => setQrUrl(e.target.value)} placeholder="Expected QR URL (optional)"
                className="rounded border px-2 py-1 text-[12px] w-64" />
            </span>
            <button data-testid="ca-refresh" onClick={() => load(sel)} className="inline-flex items-center gap-1 text-navy hover:underline"><RefreshCw className="w-3.5 h-3.5" /> Refresh</button>
          </div>
        )}
      </div>

      {sel && (
        <div className="rounded-lg border bg-card p-4" data-testid="ca-required-specs">
          <h3 className="text-sm font-bold text-navy mb-3">Required Assets (inherited specifications)</h3>
          <div className="space-y-2">
            {inherited.map((s) => {
              const present = assetsFor(s.asset_role, s.platform_id);
              return (
                <div key={`${s.asset_role}-${s.platform_id}`} data-testid={`ca-spec-${s.platform_id}`} className="rounded-md border p-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div>
                      <div className="text-[13px] font-semibold text-navy">{s.asset_role} <span className="text-muted-foreground">· {s.platform_name || s.platform_id}</span></div>
                      <div className="mt-1 flex gap-2 items-center">
                        <Badge tone={s.profile_status === "Verified" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}>Profile {s.profile_status}</Badge>
                        {present.length ? <Badge tone="bg-emerald-100 text-emerald-700">{present.length} asset(s)</Badge> : <Badge tone="bg-red-50 text-red-700">Missing</Badge>}
                      </div>
                    </div>
                    <div className="flex gap-2 items-center">
                      <button data-testid={`ca-genspec-${s.platform_id}`} onClick={() => genSpec(s.asset_role, s.platform_id)} disabled={busy === `spec-${s.platform_id}`}
                        className="inline-flex items-center gap-1 bg-muted text-navy px-3 py-1.5 rounded text-[12px] font-semibold">
                        {busy === `spec-${s.platform_id}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileCog className="w-3.5 h-3.5" />} Spec
                      </button>
                      <label data-testid={`ca-upload-${s.platform_id}`} className="inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded text-[12px] font-semibold cursor-pointer">
                        {busy === `up-${s.platform_id}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <UploadCloud className="w-3.5 h-3.5" />} Upload
                        <input type="file" className="hidden" onChange={(e) => uploadArtwork(s.asset_role, s.platform_id, e.target.files[0])} />
                      </label>
                    </div>
                  </div>
                  {present.map((a) => (
                    <div key={a.asset_id} data-testid={`ca-asset-${a.asset_id}`} className="mt-2 rounded bg-muted/40 p-2 flex items-center justify-between flex-wrap gap-2">
                      <div className="text-[12px]">
                        <span className="font-mono">{a.asset_id}</span> · {a.version} ·{" "}
                        <Badge tone={STATE_TONE[a.lifecycle_state]}>{a.lifecycle_state}</Badge>{" "}
                        <Badge tone={RESULT_TONE[a.validation?.result]} testid={`ca-val-${a.asset_id}`}>{a.validation?.result}</Badge>
                        {a.validation?.qr_validation && <Badge tone={RESULT_TONE[a.validation.qr_validation.result]}>QR {a.validation.qr_validation.result}</Badge>}
                      </div>
                      <div className="flex gap-1">
                        <button data-testid={`ca-approve-${a.asset_id}`} onClick={() => setState(a.asset_id, "Approved")} className="inline-flex items-center gap-1 text-emerald-700 hover:bg-emerald-50 px-2 py-1 rounded text-[11px]"><CheckCircle2 className="w-3.5 h-3.5" />Approve</button>
                        <button data-testid={`ca-lock-${a.asset_id}`} onClick={() => setState(a.asset_id, "Locked")} className="inline-flex items-center gap-1 text-navy hover:bg-muted px-2 py-1 rounded text-[11px]"><Lock className="w-3.5 h-3.5" />Lock</button>
                        <button data-testid={`ca-reject-${a.asset_id}`} onClick={() => setState(a.asset_id, "Rejected")} className="inline-flex items-center gap-1 text-red-600 hover:bg-red-50 px-2 py-1 rounded text-[11px]"><XCircle className="w-3.5 h-3.5" />Reject</button>
                        <button data-testid={`ca-archive-${a.asset_id}`} onClick={() => setState(a.asset_id, "Archived")} className="inline-flex items-center gap-1 text-muted-foreground hover:bg-muted px-2 py-1 rounded text-[11px]"><Ban className="w-3.5 h-3.5" />Archive</button>
                      </div>
                      {(a.validation?.issues?.length > 0) && <div className="w-full text-[11px] text-red-600 flex items-center gap-1"><AlertTriangle className="w-3 h-3" />{a.validation.issues.join("; ")}</div>}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {spec && (
        <div className="rounded-lg border bg-card p-4" data-testid="ca-spec-panel">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-navy">Specification · {spec.spec_id}</h3>
            <Badge tone="bg-navy/10 text-navy">checksum {spec.spec_checksum?.slice(0, 12)}</Badge>
          </div>
          <pre className="mt-2 text-[11px] bg-muted/50 rounded p-3 overflow-auto max-h-72">{JSON.stringify({ requirements: spec.requirements, geometry: spec.geometry, target_px: spec.target_px, design_intent: spec.design_intent, cost_controls: spec.cost_controls }, null, 2)}</pre>
        </div>
      )}

      {sel && (
        <div className="rounded-lg border bg-card p-4" data-testid="ca-package">
          <h3 className="text-sm font-bold text-navy mb-3 flex items-center gap-2"><Package className="w-4 h-4" /> Marketplace Packages</h3>
          <div className="flex flex-wrap gap-2">
            {MARKETPLACES.map((mk) => (
              <button key={mk} data-testid={`ca-pkg-${mk}`} onClick={() => buildPackage(mk)} disabled={busy === `pkg-${mk}`}
                className="inline-flex items-center gap-1 bg-muted text-navy px-3 py-1.5 rounded text-[12px] font-semibold capitalize">
                {busy === `pkg-${mk}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}{mk.replace("_", " ")}
              </button>
            ))}
          </div>
          {pkg && (
            <div className="mt-3 rounded-md border p-3 text-[12px]" data-testid="ca-package-result">
              <div className="flex gap-2 items-center flex-wrap">
                <span className="font-bold capitalize">{pkg.marketplace}</span>
                <Badge tone={pkg.package_ready ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}>{pkg.package_ready ? "Review-Ready" : "Not Ready"}</Badge>
                <Badge tone="bg-navy/10 text-navy">Policy: {pkg.governed_publication_mode}</Badge>
                <Badge tone="bg-muted text-muted-foreground">Decision: {pkg.publication_decision}</Badge>
              </div>
              {pkg.missing_assets?.length > 0 && <div className="mt-2 text-red-600">Missing: {pkg.missing_assets.map((m) => m.asset_role).join(", ")}</div>}
              {pkg.blocked_reason && <div className="mt-1 text-muted-foreground">{pkg.blocked_reason}</div>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
