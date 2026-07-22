import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared";
import { Panel } from "@/components/qru";
import {
  Loader2, Layers, CheckCircle2, XCircle, ShieldCheck, ShieldAlert, PackageCheck,
  ArrowRight, Boxes, Download,
} from "lucide-react";

const A = process.env.REACT_APP_BACKEND_URL;
function abs(u) { return u && u.startsWith("/") ? `${A}${u}` : u; }

export default function ProductFamily() {
  const [sources, setSources] = useState([]);
  const [intents, setIntents] = useState([]);
  const [available, setAvailable] = useState([]);
  const [decoderId, setDecoderId] = useState("");
  const [intentId, setIntentId] = useState("");
  const [checked, setChecked] = useState({});
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  useEffect(() => {
    api.get("/family/eligible-sources").then((r) => setSources(r.data.sources || [])).catch(() => {});
    api.get("/family/intents").then((r) => { setIntents(r.data.intents || []); setAvailable(r.data.available_families || []); }).catch(() => {});
  }, []);

  useEffect(() => {
    setPreview(null); setResult(null);
    if (decoderId && intentId) {
      api.get(`/family/preview?decoder_id=${decoderId}&intent=${intentId}`)
        .then((r) => {
          setPreview(r.data);
          const init = {}; (r.data.families || []).forEach((f) => { init[f] = true; });
          setChecked(init);
        })
        .catch((e) => toast.error(formatApiError(e.response?.data?.detail)));
    }
  }, [decoderId, intentId]);

  const selectedFamilies = Object.keys(checked).filter((k) => checked[k]);

  const doAssemble = async () => {
    setBusy(true); setResult(null);
    try {
      const { data } = await api.post("/family/assemble", {
        decoder_id: decoderId, intent: intentId, families: selectedFamilies,
      });
      setResult(data);
      toast[data.ok ? "success" : "error"](
        data.ok ? `Family assembled — ${data.succeeded}/${data.requested} products manufactured.`
                : "Assembly did not produce any products.");
    } catch (e) {
      const d = e.response?.data?.detail;
      if (d && d.error === "source_verification_failed") toast.error(d.message || "Source verification failed.");
      else toast.error(formatApiError(d));
    } finally { setBusy(false); }
  };

  return (
    <div className="space-y-6" data-testid="product-family-page">
      <PageHeader
        overline="Universal Distribution Framework™"
        title="Product Family Manufacturing™"
        description="Manufacture once from a Verified source, assemble a whole product family. Pick a source, pick who it's for, confirm the bundle — one action produces the family."
      />

      <div className="grid lg:grid-cols-2 gap-4">
        {/* Step 1 — Source */}
        <Panel title="1 · Verified Source" icon={ShieldCheck} accent="navy" testid="family-source-panel">
          <p className="text-[11px] text-muted-foreground mb-2">Choose a manufacturing-eligible understanding (each traces to a Verified Universal Knowledge Record™).</p>
          <select data-testid="family-source-select" value={decoderId} onChange={(e) => setDecoderId(e.target.value)}
            className="w-full text-[13px] border border-border rounded-md bg-card px-2 py-2 text-navy outline-none">
            <option value="">Select a source…</option>
            {sources.map((s) => (
              <option key={s.decoder_id} value={s.decoder_id}>{s.title} · {s.review_state}</option>
            ))}
          </select>
        </Panel>

        {/* Step 2 — Intent */}
        <Panel title="2 · Manufacturing Intent™" icon={Layers} accent="royal" testid="family-intent-panel">
          <p className="text-[11px] text-muted-foreground mb-2">Who is this family for? The intent pre-selects the right product bundle.</p>
          <div className="grid grid-cols-2 gap-2" data-testid="family-intent-options">
            {intents.map((it) => (
              <button key={it.id} data-testid={`intent-${it.id}`} onClick={() => setIntentId(it.id)}
                className={`text-left rounded-md border px-3 py-2 transition-colors ${intentId === it.id ? "border-royal bg-royal/5" : "border-border hover:border-royal/40"}`}>
                <p className="text-[12px] font-bold text-navy">{it.label}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">{it.families.length} product(s)</p>
              </button>
            ))}
          </div>
        </Panel>
      </div>

      {/* Step 3 — Preview + confirm */}
      {preview && (
        <Panel title="3 · Confirm the Family" icon={Boxes} accent="gold" testid="family-preview-panel">
          <div className={`rounded-md border px-3 py-2 mb-3 flex items-start gap-2 ${preview.gate?.match?.level === "critical" ? "bg-red-50 border-red-200" : "bg-emerald-50 border-emerald-200"}`} data-testid="family-gate-verdict">
            {preview.gate?.match?.level === "critical"
              ? <ShieldAlert className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
              : <ShieldCheck className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />}
            <div>
              <p className={`text-[12px] font-bold ${preview.gate?.match?.level === "critical" ? "text-red-800" : "text-emerald-800"}`}>
                Source Verification Gate™: {preview.gate?.match?.level === "critical" ? "Mismatch — manufacturing blocked" : "Source matches the subject"}
              </p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{preview.gate?.match?.reason}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">Intent: <b>{preview.intent?.label}</b> · Audience: {preview.intent?.audience}</p>
            </div>
          </div>

          <p className="text-[11px] font-semibold text-navy mb-2">Products to manufacture (uncheck any you don't need):</p>
          <div className="flex flex-wrap gap-2 mb-4" data-testid="family-checkboxes">
            {(preview.families || []).map((f) => (
              <label key={f} data-testid={`family-check-${f.replace(/\s+/g, "-")}`}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 cursor-pointer text-[12px] font-semibold ${checked[f] ? "border-navy bg-navy/5 text-navy" : "border-border text-muted-foreground"}`}>
                <input type="checkbox" checked={!!checked[f]} onChange={(e) => setChecked({ ...checked, [f]: e.target.checked })} className="accent-navy" />
                {f}
              </label>
            ))}
          </div>

          <button data-testid="assemble-family-btn" onClick={doAssemble}
            disabled={busy || !preview.can_manufacture || selectedFamilies.length === 0}
            className="inline-flex items-center gap-1.5 bg-gold text-navy px-5 py-2.5 rounded-md text-sm font-bold disabled:opacity-40">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <PackageCheck className="w-4 h-4" />}
            Manufacture Family ({selectedFamilies.length})
          </button>
          {!preview.can_manufacture && (
            <p className="text-[11px] text-red-700 mt-2">This source cannot be manufactured (not eligible or a critical source mismatch).</p>
          )}
        </Panel>
      )}

      {/* Result */}
      {result && (
        <Panel title="Family Manufactured" icon={PackageCheck} accent="emerald" testid="family-result-panel">
          <div className="flex items-center gap-2 mb-3">
            <span className="font-mono text-[11px] text-muted-foreground">{result.family_code}</span>
            <span className="text-[11px] font-bold text-emerald-700">{result.succeeded}/{result.requested} manufactured · {result.intent}</span>
          </div>
          <div className="space-y-2">
            {(result.items || []).map((it, i) => (
              <div key={i} data-testid={`family-result-${it.family.replace(/\s+/g, "-")}`}
                className={`rounded-md border px-3 py-2 flex items-center justify-between gap-2 ${it.ok ? "bg-emerald-50 border-emerald-200" : "bg-red-50 border-red-200"}`}>
                <div className="flex items-center gap-2 min-w-0">
                  {it.ok ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <XCircle className="w-4 h-4 text-red-600 shrink-0" />}
                  <div className="min-w-0">
                    <p className="text-[12px] font-bold text-navy">{it.family}</p>
                    <p className="text-[10px] text-muted-foreground truncate">{it.ok ? `${it.code} · ${it.title}` : it.error}</p>
                  </div>
                </div>
                {it.ok && it.route && (
                  <button data-testid={`family-open-${it.family.replace(/\s+/g, "-")}`}
                    onClick={() => nav(it.engine === "book" ? `/book-manufacturing?book=${it.book_id || it.id}` : `/products/${it.id}`)}
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-royal shrink-0">
                    Open <ArrowRight className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
          {result.package?.url && (
            <a data-testid="family-package-download" href={abs(result.package.url)} target="_blank" rel="noreferrer"
              className="inline-flex items-center gap-1.5 mt-4 border border-navy/30 text-navy px-4 py-2 rounded-md text-sm font-bold">
              <Download className="w-4 h-4" /> Download Family Package™ ({result.package.size_kb} KB)
            </a>
          )}
        </Panel>
      )}
    </div>
  );
}
