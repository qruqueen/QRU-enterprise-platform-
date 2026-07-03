import { useEffect, useState, useCallback, useRef } from "react";
import { toast } from "sonner";
import {
  Loader2, Factory, CheckCircle2, Circle, XCircle, Lock, Sparkles, ShieldCheck,
  AlertTriangle, PackageCheck, Rocket, ChevronDown, Image as ImageIcon, FileText, QrCode, Download,
} from "lucide-react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { CompletionSummary } from "@/components/CompletionSummary";
import { FinalProductPreview } from "@/components/FinalProductPreview";

const STAGE_ICON = { done: CheckCircle2, running: Loader2, failed: XCircle, waiting: Circle, locked: Lock };
const STAGE_COLOR = { done: "hsl(var(--success))", running: "hsl(var(--primary))", failed: "hsl(var(--destructive))", waiting: "hsl(var(--muted-foreground))" };

function StageRow({ s }) {
  const Icon = STAGE_ICON[s.status] || Circle;
  return (
    <div className="flex items-center gap-3 py-2" data-testid={`stage-${s.label}`}>
      <Icon className={`w-4 h-4 shrink-0 ${s.status === "running" ? "animate-spin" : ""}`} style={{ color: STAGE_COLOR[s.status] }} />
      <span className="text-sm font-medium flex-1">{s.label}</span>
      <span className="text-xs text-muted-foreground">{s.detail || s.status}</span>
    </div>
  );
}

export default function ManufacturingStudio() {
  const [records, setRecords] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [krId, setKrId] = useState("");
  const [ptype, setPtype] = useState("");
  const [missing, setMissing] = useState(null);
  const [pipeline, setPipeline] = useState(null);
  const [busy, setBusy] = useState(false);
  const [showScores, setShowScores] = useState(false);
  const [render, setRender] = useState(null);
  const [rendering, setRendering] = useState(false);
  const renderPollRef = useRef(null);
  const pollRef = useRef(null);
  const [completion, setCompletion] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewShownFor, setPreviewShownFor] = useState(null);
  const BACKEND = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    api.get("/knowledge-records?status=Verified").then((r) => setRecords(r.data));
    api.get("/manufacturing2/recipes").then((r) => setRecipes(r.data.recipes));
  }, []);

  useEffect(() => {
    if (krId && ptype) {
      api.post("/manufacturing2/detect-missing", { knowledge_record_id: krId, product_type: ptype })
        .then((r) => setMissing(r.data)).catch(() => setMissing(null));
    } else setMissing(null);
  }, [krId, ptype]);

  const poll = useCallback((pid) => {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const { data } = await api.get(`/manufacturing2/${pid}/pipeline`);
      setPipeline(data);
      if (!["Manufacturing", "Quality Control", "Improving"].includes(data.status)) {
        clearInterval(pollRef.current);
      }
    }, 3000);
  }, []);

  useEffect(() => () => { clearInterval(pollRef.current); clearInterval(renderPollRef.current); }, []);

  useEffect(() => {
    if (pipeline?.id && pipeline.treasure_standard) {
      api.get(`/rendering/${pipeline.id}`).then((r) => setRender(r.data)).catch(() => {});
    }
  }, [pipeline?.id, pipeline?.treasure_standard]);

  // MT-021 — auto-transition to Final Product Preview when manufacturing completes successfully
  // (no blocking condition). Only fires once per completed pipeline.
  useEffect(() => {
    const done = pipeline?.treasure_standard && !["Manufacturing", "Quality Control", "Improving"].includes(pipeline?.status);
    if (done && previewShownFor !== pipeline.id) {
      setShowPreview(true);
      setPreviewShownFor(pipeline.id);
    }
  }, [pipeline?.id, pipeline?.treasure_standard, pipeline?.status, previewShownFor]);

  const runRender = async () => {
    if (!pipeline) return;
    setRendering(true);
    await api.post(`/rendering/${pipeline.id}/render`);
    toast.info("Creative Studio™ is rendering branded assets…");
    clearInterval(renderPollRef.current);
    renderPollRef.current = setInterval(async () => {
      const { data } = await api.get(`/rendering/${pipeline.id}`);
      setRender(data);
      if (data.render_status === "rendered" || data.render_status === "failed") {
        clearInterval(renderPollRef.current);
        setRendering(false);
        if (data.render_status === "rendered") toast.success("Branded product rendered 🎨");
      }
    }, 3000);
  };

  const assemble = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/manufacturing2/assemble", { knowledge_record_id: krId, product_type: ptype });
      const { data: pl } = await api.get(`/manufacturing2/${data.id}/pipeline`);
      setPipeline(pl);
      toast.success("Product assembled from verified Understanding Assets™.");
    } catch (e) { toast.error("Assembly failed."); }
    setBusy(false);
  };

  const manufactureMissing = async () => {
    if (!pipeline) return;
    setBusy(true);
    await api.post(`/manufacturing2/${pipeline.id}/manufacture-missing`);
    toast.info("Manufacturing missing fields…");
    poll(pipeline.id);
    setBusy(false);
  };

  const runQC = async () => {
    if (!pipeline) return;
    await api.post(`/manufacturing2/${pipeline.id}/quality-control`);
    toast.info("QRU Manufacturing Quality Control™ started — improving to Treasure Standard™.");
    poll(pipeline.id);
  };

  const release = async () => {
    const started = Date.now();
    try {
      await api.post(`/manufacturing2/${pipeline.id}/release`);
      const { data } = await api.get(`/manufacturing2/${pipeline.id}/pipeline`);
      setPipeline(data);
      setCompletion({
        status: "success",
        workflowName: "Manufacturing Studio™ — Release",
        timeCompleted: Date.now(), durationMs: Date.now() - started, estimatedCost: 0,
        assets: [{ label: data?.title || "Product", sub: "Released to customers · Treasure Standard™" }],
        actions: [
          { label: "Open Product", testid: "completion-open-product", to: `/products/${pipeline.product_id || pipeline.id}`, primary: true },
          { label: "Open Store™", testid: "completion-store", to: "/store" },
          { label: "Product Library™", testid: "completion-library", to: "/products" },
        ],
      });
    } catch (e) { toast.error(e.response?.data?.detail || "Release locked."); }
  };

  const canRelease = pipeline?.treasure_standard;
  const qcActive = pipeline && ["Quality Control", "Improving"].includes(pipeline.status);

  return (
    <div>
      <CompletionSummary open={!!completion} onOpenChange={(v) => !v && setCompletion(null)} data={completion} />
      <FinalProductPreview open={showPreview} onOpenChange={setShowPreview} pipeline={pipeline} render={render} />
      <PageHeader overline="Manufacturing Engine 2.0 · Enterprise Mode" title="Manufacturing Studio"
        description="Assemble finished QRU Products™ from verified Understanding Assets™, then let Quality Control improve them to Treasure Standard™ before release." />

      <div className="bg-card border rounded-2xl p-5 mb-6 grid sm:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Verified Knowledge Master Record™</label>
          <select data-testid="ms-kr-select" value={krId} onChange={(e) => { setKrId(e.target.value); setPipeline(null); }}
            className="w-full px-3 py-2 text-sm bg-muted rounded-md border border-border outline-none focus:border-primary">
            <option value="">Select a record…</option>
            {records.map((r) => <option key={r.id} value={r.id}>{r.kr_code} · {r.title}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Manufacturing Recipe™</label>
          <select data-testid="ms-type-select" value={ptype} onChange={(e) => { setPtype(e.target.value); setPipeline(null); }}
            className="w-full px-3 py-2 text-sm bg-muted rounded-md border border-border outline-none focus:border-primary">
            <option value="">Select a product type…</option>
            {recipes.map((r) => <option key={r.product_type} value={r.product_type}>{r.product_type} Recipe™</option>)}
          </select>
        </div>
      </div>

      {missing && !pipeline && (
        <div className="bg-card border rounded-2xl p-5 mb-6" data-testid="missing-panel">
          {missing.ready ? (
            <div className="flex items-center gap-2 text-sm mb-4"><CheckCircle2 className="w-4 h-4" style={{ color: "hsl(var(--success))" }} /> All {missing.required_count} required fields are present. Ready to assemble.</div>
          ) : (
            <div className="mb-4">
              <div className="flex items-center gap-2 text-sm mb-2"><AlertTriangle className="w-4 h-4" style={{ color: "hsl(var(--warning))" }} /> {missing.missing.length} of {missing.required_count} required components are missing:</div>
              <div className="flex flex-wrap gap-2">{missing.missing.map((m) => <span key={m.field} className="text-xs px-2 py-1 rounded-full bg-muted border">{m.label}</span>)}</div>
            </div>
          )}
          <button data-testid="ms-assemble" onClick={assemble} disabled={busy}
            className="px-5 py-2 rounded-md text-white text-sm font-medium flex items-center gap-2 disabled:opacity-60" style={{ background: "hsl(var(--royal))" }}>
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <PackageCheck className="w-4 h-4" />} Assemble QRU Product™
          </button>
        </div>
      )}

      {pipeline && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-card border rounded-2xl p-5">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-xs text-muted-foreground">{pipeline.product_code} · {pipeline.recipe_type} Recipe™</p>
                  <h2 className="font-heading font-bold text-lg">{pipeline.title}</h2>
                </div>
                <span className="text-xs px-2.5 py-1 rounded-full font-semibold" style={{ background: "hsl(var(--secondary))", color: "hsl(var(--primary))" }} data-testid="pipeline-status">{pipeline.status}</span>
              </div>
              <div className="divide-y divide-border">
                {pipeline.stages.map((s) => <StageRow key={s.label} s={s} />)}
              </div>
            </div>

            {pipeline.missing_fields?.length > 0 && (
              <div className="rounded-2xl border border-warning p-4" style={{ background: "hsl(var(--warning) / 0.06)" }}>
                <p className="text-sm font-medium mb-2">Missing components — manufacture only what's needed:</p>
                <div className="flex flex-wrap gap-2 mb-3">{pipeline.missing_fields.map((m) => <span key={m.field} className="text-xs px-2 py-1 rounded-full bg-white border">{m.label}</span>)}</div>
                <button data-testid="ms-manufacture-missing" onClick={manufactureMissing} disabled={busy || qcActive}
                  className="px-4 py-1.5 rounded-md text-sm font-medium border border-primary text-primary disabled:opacity-50">Manufacture Missing Fields™</button>
              </div>
            )}
          </div>

          <div className="space-y-6">
            {/* Quality Control */}
            <div className="bg-card border rounded-2xl p-5" data-testid="qc-panel">
              <p className="overline text-primary mb-3 flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> Quality Control™</p>
              {pipeline.qc?.status === "certified" ? (
                <div className="flex items-center gap-2 text-sm mb-3"><ShieldCheck className="w-4 h-4" style={{ color: "hsl(var(--success))" }} /> Treasure Standard™ Certified</div>
              ) : qcActive ? (
                <div className="text-sm mb-3">
                  <div className="flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin text-primary" /> Improving automatically (round {pipeline.qc?.iterations})</div>
                  {pipeline.qc?.current_issue && <p className="text-xs text-muted-foreground mt-1">{pipeline.qc.current_issue}</p>}
                </div>
              ) : pipeline.qc?.status === "needs_review" ? (
                <p className="text-xs text-destructive mb-3">{pipeline.qc.current_issue}</p>
              ) : (
                <p className="text-xs text-muted-foreground mb-3">Not yet run. Quality Control will improve this product to Treasure Standard™.</p>
              )}
              {!qcActive && pipeline.qc?.status !== "certified" && (
                <button data-testid="ms-run-qc" onClick={runQC} className="w-full px-4 py-2 rounded-md text-white text-sm font-medium" style={{ background: "hsl(var(--navy))" }}>Run Quality Control™</button>
              )}
              {pipeline.qc?.scores && Object.keys(pipeline.qc.scores).length > 0 && (
                <div className="mt-3">
                  <button onClick={() => setShowScores(!showScores)} className="text-xs text-primary flex items-center gap-1">Internal quality report <ChevronDown className={`w-3 h-3 transition-transform ${showScores ? "rotate-180" : ""}`} /></button>
                  {showScores && (
                    <div className="mt-2 space-y-1.5">
                      {Object.entries(pipeline.qc.scores).map(([k, v]) => (
                        <div key={k}>
                          <div className="flex justify-between text-[11px]"><span>{k}</span><span>{v}</span></div>
                          <div className="h-1.5 rounded-full bg-muted"><div className="h-full rounded-full" style={{ width: `${v}%`, background: v >= 88 ? "hsl(var(--success))" : "hsl(var(--warning))" }} /></div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Release gates */}
            <div className="bg-card border rounded-2xl p-5">
              <p className="overline text-primary mb-3">Release Gates</p>
              <div className="space-y-1.5" data-testid="release-gates">
                {Object.entries(pipeline.gates).map(([g, v]) => (
                  <div key={g} className="flex items-center gap-2 text-sm">
                    {v.status === "passed" ? <CheckCircle2 className="w-3.5 h-3.5" style={{ color: "hsl(var(--success))" }} /> : <Lock className="w-3.5 h-3.5 text-muted-foreground" />}
                    <span className={v.status === "passed" ? "" : "text-muted-foreground"}>{g}</span>
                  </div>
                ))}
              </div>
              <button data-testid="ms-release" onClick={release} disabled={!canRelease}
                className="w-full mt-4 px-4 py-2.5 rounded-md text-white text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: canRelease ? "hsl(var(--success))" : "hsl(var(--muted-foreground))" }}>
                {canRelease ? <Rocket className="w-4 h-4" /> : <Lock className="w-4 h-4" />} Release Product™
              </button>
              {pipeline.status === "Published" && <p className="text-xs text-center mt-2" style={{ color: "hsl(var(--success))" }}>Released & live for learners.</p>}
            </div>

            {/* Deliverables */}
            {pipeline.deliverables?.length > 0 && (
              <div className="bg-card border rounded-2xl p-5">
                <p className="overline text-primary mb-3">Assembled Deliverables</p>
                <div className="grid grid-cols-2 gap-1.5">
                  {pipeline.deliverables.map((d, i) => <span key={i} className="text-xs px-2 py-1 rounded bg-muted">{d.name}</span>)}
                </div>
              </div>
            )}

            {/* Product Rendering Engine */}
            {pipeline.treasure_standard && (
              <div className="bg-card border rounded-2xl p-5" data-testid="render-panel">
                <p className="overline text-primary mb-3 flex items-center gap-1.5"><ImageIcon className="w-3.5 h-3.5" /> Product Rendering Engine™</p>
                {(!render || render.render_status === "not_started") && !rendering && (
                  <>
                    <p className="text-xs text-muted-foreground mb-3">Render fully branded QRU assets — cover, thumbnail, store graphic, QR code, and print-ready PDF — using Design Intelligence™.</p>
                    <button data-testid="ms-render" onClick={runRender} className="w-full px-4 py-2 rounded-md text-white text-sm font-medium" style={{ background: "hsl(var(--navy))" }}>Render Branded Product™</button>
                  </>
                )}
                {rendering && <div className="flex items-center gap-2 text-sm"><Loader2 className="w-4 h-4 animate-spin text-primary" /> Rendering branded assets…</div>}
                {render?.render_status === "rendered" && render.rendered_assets && (
                  <div data-testid="rendered-gallery">
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      {["cover", "thumbnail", "store_graphic"].map((k) => render.rendered_assets[k] && (
                        <a key={k} href={`${BACKEND}${render.rendered_assets[k]}`} target="_blank" rel="noreferrer" className="block">
                          <img src={`${BACKEND}${render.rendered_assets[k]}`} alt={k} className="w-full h-20 object-cover rounded-lg border" />
                          <p className="text-[10px] text-muted-foreground mt-0.5 capitalize">{k.replace("_", " ")}</p>
                        </a>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      {render.rendered_assets.qr_code && <a data-testid="asset-qr" href={`${BACKEND}${render.rendered_assets.qr_code}`} target="_blank" rel="noreferrer" className="flex-1 flex items-center justify-center gap-1.5 text-xs px-3 py-2 rounded-md border hover:border-primary"><QrCode className="w-3.5 h-3.5" /> QR Code</a>}
                      {render.rendered_assets.print_pdf && <a data-testid="asset-pdf" href={`${BACKEND}${render.rendered_assets.print_pdf}`} target="_blank" rel="noreferrer" className="flex-1 flex items-center justify-center gap-1.5 text-xs px-3 py-2 rounded-md border hover:border-primary"><FileText className="w-3.5 h-3.5" /> Print PDF</a>}
                    </div>
                    <button onClick={runRender} className="w-full mt-2 text-xs text-primary">Re-render</button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
