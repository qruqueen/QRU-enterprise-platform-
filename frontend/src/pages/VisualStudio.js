import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import {
  Loader2, Palette, LayoutDashboard, Sparkles, Film, CheckCircle2, XCircle, AlertTriangle, UserCheck,
} from "lucide-react";

const CHECK_TONE = { pass: "emerald", warn: "amber", fail: "red", human_review: "blue" };

export default function VisualStudio() {
  const [config, setConfig] = useState(null);
  const [media, setMedia] = useState(null);
  const [gov, setGov] = useState([]);
  const [products, setProducts] = useState([]);
  const [pid, setPid] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [gold, setGold] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/visual-studio/config").then((r) => setConfig(r.data)).catch(() => setConfig(false));
    api.get("/visual-studio/media/config").then((r) => setMedia(r.data)).catch(() => {});
    api.get("/governance-binding/strip/design").then((r) => setGov(r.data.governed_by)).catch(() => {});
    api.get("/founder-inbox").then((r) => setProducts((r.data.products || []).slice(0, 200))).catch(() => {});
  }, []);

  const run = async () => {
    if (!pid) return;
    setBusy(true); setAnalysis(null); setGold(null);
    try {
      const [a, g] = await Promise.all([
        api.get(`/visual-studio/analyze/${pid}`), api.get(`/visual-studio/gold-review/${pid}`),
      ]);
      setAnalysis(a.data); setGold(g.data);
    } catch { /* noop */ } finally { setBusy(false); }
  };

  if (config === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (config === false) return <p className="text-sm text-muted-foreground p-8">Could not load the Visual Studio.</p>;

  const c = config.config;
  return (
    <div>
      <PageHeader
        overline="QRU Visual Intelligence Studio™ · MO-009 / MO-010"
        title="Visual & Media Studio"
        description="Understanding should not only be explained — it should be made visible. Every product is engineered to help the learner Notice, Enter, Understand, Remember, Apply, Continue, and Share."
        actions={<VerifiedBadge label="Gold Standard™ Governed" testid="vs-badge" />}
      />
      <GovernedBy standards={gov} className="mb-6" testid="vs-governed-by" />

      {/* Product analyzer */}
      <Panel title="Layout Intelligence™ & Gold Standard Review™" icon={LayoutDashboard} accent="gold" testid="vs-analyzer" className="mb-8">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end mb-4">
          <div className="flex-1">
            <label className="text-xs font-bold text-navy uppercase tracking-wide">Product</label>
            <select data-testid="vs-product" value={pid} onChange={(e) => setPid(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
              <option value="">— Select a manufactured product —</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.product_code} — {p.title}</option>)}
            </select>
          </div>
          <button onClick={run} disabled={busy || !pid} data-testid="vs-run"
            className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Run Visual Review
          </button>
        </div>

        {analysis && (
          <div className="grid md:grid-cols-2 gap-4" data-testid="vs-results">
            <div className="border rounded-md p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="font-heading font-bold text-navy">Layout Intelligence™</p>
                <StatusChip status={analysis.passed ? "Cleared" : "Paused"} />
              </div>
              <p className="font-heading text-3xl font-bold text-navy">{analysis.layout_score}<span className="text-sm text-muted-foreground">/100</span></p>
              <p className="text-[11px] text-muted-foreground mb-2">{analysis.word_count} words · {analysis.violations.length} issue(s)</p>
              {analysis.violations.length === 0 ? <p className="text-xs text-emerald-600 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> No rendering failures detected.</p> :
                <div className="space-y-1.5">{analysis.violations.map((v, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-xs">
                    <AlertTriangle className={`w-3.5 h-3.5 shrink-0 ${v.severity === "high" ? "text-red-500" : v.severity === "medium" ? "text-amber-500" : "text-muted-foreground"}`} />
                    <span className="text-navy">{v.message}</span>
                  </div>))}</div>}
            </div>
            <div className="border rounded-md p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="font-heading font-bold text-navy">Gold Standard Experience™</p>
                <StatusChip status={gold.treasure_standard === "Met" ? "Cleared" : "Paused"} />
              </div>
              <p className="text-xs mb-2"><b className="text-navy">Treasure:</b> {gold.treasure_standard} · <b className="text-navy">Gold:</b> {gold.gold_standard}</p>
              <div className="space-y-1">
                {gold.checks.map((ck, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px]">
                    {ck.status === "human_review" ? <UserCheck className="w-3 h-3 text-blue-500" /> : ck.status === "pass" ? <CheckCircle2 className="w-3 h-3 text-emerald-500" /> : <XCircle className="w-3 h-3 text-amber-500" />}
                    <span className="text-navy capitalize">{ck.check.replace(/_/g, " ").replace(" test", "")}</span>
                    <StatusChip status={ck.status === "human_review" ? "Human Review" : ck.status} tone={CHECK_TONE[ck.status]} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Panel>

      {/* Departments + rules */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <Panel title="Studio Departments" icon={Palette} accent="royal" testid="vs-departments">
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(c.departments).map(([k, on]) => (
              <span key={k} className={`text-[11px] px-2 py-1 rounded-full border ${on ? "bg-royal/10 text-royal border-royal/25" : "bg-muted text-muted-foreground border-border"}`}>
                {config.department_labels[k] || k}
              </span>
            ))}
          </div>
        </Panel>
        <Panel title="Layout Rules & Quality Checks" icon={CheckCircle2} accent="gold" testid="vs-rules">
          <p className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground mb-1.5">Layout Rules ({Object.keys(c.layout_rules).length})</p>
          <div className="flex flex-wrap gap-1.5 mb-3">
            {Object.keys(c.layout_rules).map((k) => <span key={k} className="text-[10px] px-1.5 py-0.5 rounded border bg-navy/[0.06] text-navy border-navy/15">{k.replace(/_/g, " ")}</span>)}
          </div>
          <p className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground mb-1.5">Gold Standard Checks ({Object.keys(c.quality_checks).length})</p>
          <div className="flex flex-wrap gap-1.5">
            {Object.keys(c.quality_checks).map((k) => <span key={k} className="text-[10px] px-1.5 py-0.5 rounded border bg-gold/12 text-navy border-gold/30">{k.replace(/_test|_/g, " ").trim()}</span>)}
          </div>
        </Panel>
      </div>

      {/* Media Intelligence Division */}
      {media && (
        <Panel title="Media Intelligence Division™ · MO-010" icon={Film} accent="royal" testid="vs-media">
          <p className="text-xs text-muted-foreground mb-3">{media.capabilities.live_count}/{media.capabilities.total} integrations live. Available now: {media.capabilities.available_now.join(" · ")}.</p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {media.capabilities.integrations.map((it) => (
              <div key={it.id} className="flex items-center justify-between border rounded-sm p-2.5" data-testid={`media-${it.id}`}>
                <div>
                  <p className="text-sm font-semibold text-navy">{it.name}</p>
                  <p className="text-[10px] text-muted-foreground">{it.note}</p>
                </div>
                <StatusChip status={it.status === "live" || it.status === "connected" ? "Connected" : "Developer Setup Required"} tone={it.status === "live" || it.status === "connected" ? "emerald" : "blue"} />
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}
