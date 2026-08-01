import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, FileText, UploadCloud, ArrowUp, ArrowDown, X, ImagePlus, Wand2,
  CheckCircle2, AlertTriangle, ShieldCheck, Download, FileCheck2, Maximize2, Layers, Store, Paperclip,
} from "lucide-react";

const RESULT_TONE = {
  PASS: "bg-emerald-100 text-emerald-700", "PASS WITH WARNINGS": "bg-amber-100 text-amber-700",
  REVISION_REQUIRED: "bg-orange-100 text-orange-700", FAIL: "bg-red-100 text-red-700",
};
const DPI_TONE = { CLEAN: "text-emerald-700", ACCEPTABLE: "text-amber-600", LOW_RES: "text-red-600" };

const fileToB64 = (file) => new Promise((res, rej) => {
  const r = new FileReader(); r.onload = () => res(r.result); r.onerror = rej; r.readAsDataURL(file);
});

export default function PrintableStudio() {
  const [config, setConfig] = useState(null);
  const [books, setBooks] = useState([]);
  const [sel, setSel] = useState("");
  const [ptype, setPtype] = useState("five_page_mini_workbook");
  const [pages, setPages] = useState([]);            // [{name, dataUrl}]
  const [incCover, setIncCover] = useState(true);
  const [incInstr, setIncInstr] = useState(true);
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [pageSize, setPageSize] = useState("letter");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [activityLayout, setActivityLayout] = useState(null);
  const [history, setHistory] = useState([]);
  const [bundleSel, setBundleSel] = useState([]);
  const [bundleTitle, setBundleTitle] = useState("");
  const [bundleResult, setBundleResult] = useState(null);
  const [presets, setPresets] = useState([]);
  const [library, setLibrary] = useState([]);
  const [layout, setLayout] = useState("poster");
  const [marginIn, setMarginIn] = useState(0.25);
  const [customScale, setCustomScale] = useState(100);
  const [preview, setPreview] = useState(null);
  const [previewing, setPreviewing] = useState(false);

  const loadLibrary = useCallback(() => {
    api.get("/printables/library").then(({ data }) => setLibrary(data.printables || [])).catch(() => {});
  }, []);

  // Load the user's saved default layout/margin.
  useEffect(() => {
    api.get("/printables/settings").then(({ data }) => {
      if (data.layout) setLayout(data.layout);
      if (data.margin_in != null) setMarginIn(data.margin_in);
      if (data.custom_scale) setCustomScale(data.custom_scale);
    }).catch(() => {});
  }, []);

  // Live single-page preview whenever the first image or layout/margin changes.
  useEffect(() => {
    if (!pages.length) { setPreview(null); return; }
    let cancelled = false;
    setPreviewing(true);
    const t = setTimeout(() => {
      api.post("/printables/preview-page", {
        image_base64: pages[0].dataUrl, layout, page_size: pageSize,
        margin_in: marginIn, custom_scale: customScale, title: title || null,
      }).then(({ data }) => { if (!cancelled) setPreview(data); })
        .catch(() => { if (!cancelled) setPreview(null); })
        .finally(() => { if (!cancelled) setPreviewing(false); });
    }, 350);
    return () => { cancelled = true; clearTimeout(t); };
  }, [pages, layout, pageSize, marginIn, customScale, title]);

  useEffect(() => {
    api.get("/printables/config").then(({ data }) => setConfig(data)).catch(() => {});
    api.get("/book-mfg/books").then(({ data }) => setBooks(data.books || [])).catch(() => {});
    loadLibrary();
  }, [loadLibrary]);

  const loadHistory = useCallback((id) => {
    if (!id) { setHistory([]); return; }
    api.get(`/printables/history/book/${id}`).then(({ data }) => setHistory(data.printables || [])).catch(() => {});
  }, []);
  useEffect(() => { loadHistory(sel); }, [sel, loadHistory]);

  const typeDef = config?.product_types?.find((t) => t.id === ptype);
  const isActivity = activityLayout === null ? !!typeDef?.activity : activityLayout;

  const enhancePage = async (i) => {
    setBusy(true);
    try {
      const { data } = await api.post("/printables/enhance-image", {
        image_base64: pages[i].dataUrl, page_size: pageSize, activity: isActivity,
      });
      setPages((p) => p.map((pg, idx) => idx === i ? { ...pg, dataUrl: data.image_base64, enhanced: data.upscaled } : pg));
      toast.success(data.upscaled ? `Regenerated larger: ${data.original_px.join("×")} → ${data.new_px.join("×")}` : "Already large enough.");
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(false); }
  };

  const attach = async (printableId, destination) => {
    try {
      const { data } = await api.post(`/printables/attach/book/${sel}`, { printable_id: printableId, destination });
      const d = data.attachment;
      toast[data.decision.can_publish ? "success" : "message"](
        `Attached to ${destination.replace("_", " ")} — policy: ${d.policy_mode} (${d.publication_decision})`);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  const toggleBundle = (id) => setBundleSel((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id]);

  const buildBundle = async () => {
    if (bundleSel.length < 2) { toast.error("Select at least two printables."); return; }
    setBusy(true); setBundleResult(null);
    try {
      const { data } = await api.post(`/printables/bundle/book/${sel}`, { printable_ids: bundleSel, title: bundleTitle || null });
      setBundleResult(data); loadHistory(sel);
      toast.success(`Bundle built — ${data.page_count} pages.`);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(false); }
  };

  const addFiles = useCallback(async (fileList) => {
    const files = Array.from(fileList || []).filter((f) => /image\/(png|jpe?g|webp)/.test(f.type));
    if (!files.length) { toast.error("Please choose PNG or JPEG images."); return; }
    const loaded = await Promise.all(files.map(async (f) => ({ name: f.name, dataUrl: await fileToB64(f) })));
    setPages((p) => [...p, ...loaded]);
  }, []);

  const move = (i, dir) => setPages((p) => {
    const n = [...p]; const j = i + dir; if (j < 0 || j >= n.length) return p;
    [n[i], n[j]] = [n[j], n[i]]; return n;
  });
  const removeAt = (i) => setPages((p) => p.filter((_, idx) => idx !== i));

  const build = async () => {
    if (!pages.length) { toast.error("Upload at least one page image."); return; }
    setBusy(true); setResult(null);
    try {
      const { data } = await api.post(`/printables/build/book/${sel || "standalone"}`, {
        product_type: ptype, images_base64: pages.map((p) => p.dataUrl),
        include_cover: incCover, include_instructions: incInstr,
        title: title || null, subtitle: subtitle || null, page_size: pageSize,
        activity_layout: activityLayout, worksheet_presets: isActivity ? presets : null,
        layout, margin_in: marginIn, custom_scale: customScale,
      });
      setResult(data); if (sel) loadHistory(sel); loadLibrary();
      const r = data.qa.result;
      toast[r === "FAIL" ? "error" : r === "REVISION_REQUIRED" ? "warning" : "success"](
        `${data.page_count}-page PDF built — QA: ${r.replace("_", " ")}`);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); } finally { setBusy(false); }
  };

  const contentSlots = pages.length;
  const totalPages = contentSlots + (incCover ? 1 : 0) + (incInstr ? 1 : 0);

  return (
    <div className="space-y-6" data-testid="printable-studio-page">
      <PageHeader title="Printable Studio™"
        subtitle="Governed Printable Product Manufacturing™ (STD-PPB-0001) — upload artwork, choose a product type, arrange pages, QA the print resolution, and export a distributable PDF."
        icon={FileText} />

      {/* Step 1 — product + type */}
      <div className="rounded-lg border bg-card p-4 space-y-4">
        <div>
          <label className="text-xs font-semibold text-navy uppercase tracking-wide">Product <span className="text-muted-foreground normal-case font-normal">— optional (needed only to bundle or attach to a listing)</span></label>
          <select data-testid="ps-product-select" value={sel} onChange={(e) => { setSel(e.target.value); setResult(null); }}
            className="mt-2 block w-full rounded-md border px-3 py-2 text-sm">
            <option value="">No product — build a standalone printable</option>
            {books.map((b) => <option key={b.id} value={b.id}>{b.book_code} — {b.title}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-navy uppercase tracking-wide">Product Type</label>
          <div className="mt-2 grid grid-cols-2 lg:grid-cols-4 gap-2" data-testid="ps-types">
            {(config?.product_types || []).map((t) => (
              <button key={t.id} data-testid={`ps-type-${t.id}`} onClick={() => setPtype(t.id)}
                className={`text-left rounded-md border p-3 transition-colors ${ptype === t.id ? "border-navy bg-navy/5 ring-1 ring-navy" : "hover:border-navy/40"}`}>
                <div className="text-[13px] font-bold text-navy">{t.label}</div>
                <div className="text-[11px] text-muted-foreground mt-0.5">
                  {t.pages} page{t.pages > 1 ? "s" : ""}{t.cover ? " · cover" : ""}{t.instructions ? " · instructions" : ""}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-navy uppercase tracking-wide">Page Layout <span className="text-muted-foreground normal-case font-normal">— Universal Page Layout Engine™ (default Poster = full page)</span></label>
          <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2" data-testid="ps-layouts">
            {(config?.layouts || []).map((l) => (
              <button key={l.id} data-testid={`ps-layout-${l.id}`} onClick={() => setLayout(l.id)}
                className={`text-left rounded-md border p-2.5 transition-colors ${layout === l.id ? "border-navy bg-navy/5 ring-1 ring-navy" : "hover:border-navy/40"}`}>
                <div className="text-[12px] font-bold text-navy">{l.label}</div>
                <div className="text-[10px] text-muted-foreground mt-0.5 leading-tight">{l.desc}</div>
              </button>
            ))}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-4 text-[12px]">
            <label className="flex items-center gap-2">Safe margin (in)
              <input data-testid="ps-margin" type="number" step="0.05" min="0" max="1" value={marginIn}
                onChange={(e) => setMarginIn(parseFloat(e.target.value) || 0)} className="rounded border px-2 py-1 w-20" />
            </label>
            <button data-testid="ps-fullbleed" onClick={() => setMarginIn(0)} className={`px-2.5 py-1 rounded-full border ${marginIn === 0 ? "bg-navy text-white border-navy" : "text-navy hover:border-navy"}`}>Full-bleed (0")</button>
            {layout === "custom_scale" && (
              <label className="flex items-center gap-2">Scale %
                <input data-testid="ps-customscale" type="number" step="5" min="5" max="400" value={customScale}
                  onChange={(e) => setCustomScale(parseInt(e.target.value) || 100)} className="rounded border px-2 py-1 w-20" />
              </label>
            )}
            <span className="text-[10px] text-muted-foreground">Your last-used layout &amp; margin are saved as your default.</span>
          </div>
        </div>

        {pages.length > 0 && (
          <div data-testid="ps-live-preview" className="rounded-md border bg-muted/30 p-3 flex gap-4 items-start">
            <div className="shrink-0 w-[220px]">
              {preview?.preview_base64 ? (
                <img src={preview.preview_base64} alt="Live layout preview" className="w-full rounded border bg-white shadow-sm" />
              ) : (
                <div className="w-full h-[285px] rounded border bg-white flex items-center justify-center text-[11px] text-muted-foreground">{previewing ? "Rendering preview…" : "Preview will appear here"}</div>
              )}
            </div>
            <div className="text-[12px] space-y-1">
              <p className="font-bold text-navy">Live Preview {previewing && <Loader2 className="inline w-3 h-3 animate-spin ml-1" />}</p>
              <p className="text-muted-foreground">Layout: <b className="text-navy">{(config?.layouts || []).find((l) => l.id === layout)?.label || layout}</b></p>
              <p className="text-muted-foreground">Margin: <b className="text-navy">{marginIn}"</b>{marginIn === 0 && " (full-bleed)"}</p>
              {preview && <p className="text-muted-foreground">Print resolution (page 1): <b className={preview.status === "LOW_RES" ? "text-red-600" : preview.status === "ACCEPTABLE" ? "text-amber-600" : "text-emerald-700"}>{preview.effective_dpi} DPI · {preview.status}</b></p>}
              <p className="text-[10px] text-muted-foreground pt-1">This is page 1 only — the full PDF renders every page in this layout on Build.</p>
            </div>
          </div>
        )}
        <div className="flex flex-wrap gap-4 items-center text-[12px]">
          <label className="flex items-center gap-2 cursor-pointer"><input data-testid="ps-cover" type="checkbox" checked={incCover} onChange={(e) => setIncCover(e.target.checked)} className="accent-navy" /> Add branded cover page</label>
          <label className="flex items-center gap-2 cursor-pointer"><input data-testid="ps-instr" type="checkbox" checked={incInstr} onChange={(e) => setIncInstr(e.target.checked)} className="accent-navy" /> Add instructions page</label>
          <label className="flex items-center gap-2 cursor-pointer"><input data-testid="ps-activity" type="checkbox" checked={isActivity} onChange={(e) => setActivityLayout(e.target.checked)} className="accent-navy" /> Activity layout (title strip + worksheet lines + auto-fill pages)</label>
          <label className="flex items-center gap-2">Page size
            <select data-testid="ps-pagesize" value={pageSize} onChange={(e) => setPageSize(e.target.value)} className="rounded border px-2 py-1">
              {(config?.page_sizes || []).map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
          </label>
          <input data-testid="ps-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Cover title (optional)" className="rounded border px-2 py-1 w-56" />
          <input data-testid="ps-subtitle" value={subtitle} onChange={(e) => setSubtitle(e.target.value)} placeholder="Cover subtitle (optional)" className="rounded border px-2 py-1 w-56" />
        </div>
        {isActivity && (
          <div data-testid="ps-presets" className="flex flex-wrap items-center gap-2 text-[12px]">
            <span className="font-semibold text-navy">Worksheet presets:</span>
            {(config?.worksheet_presets || []).map((wp) => {
              const on = presets.includes(wp.id);
              return (
                <button key={wp.id} data-testid={`ps-preset-${wp.id}`}
                  onClick={() => setPresets((s) => on ? s.filter((x) => x !== wp.id) : [...s, wp.id])}
                  className={`px-2.5 py-1 rounded-full border transition-colors ${on ? "bg-navy text-white border-navy" : "text-navy border-border hover:border-navy"}`}>
                  {wp.label}
                </button>
              );
            })}
            <span className="text-[10px] text-muted-foreground">Added as ready-made pages after your artwork.</span>
          </div>
        )}
      </div>

      {/* Step 2 — upload + arrange */}
      <div className="rounded-lg border bg-card p-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h3 className="text-sm font-bold text-navy flex items-center gap-2"><ImagePlus className="w-4 h-4" /> Artwork Pages ({contentSlots})</h3>
          <label data-testid="ps-upload" className="inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded text-[12px] font-semibold cursor-pointer">
            <UploadCloud className="w-3.5 h-3.5" /> Upload PNG / JPEG
            <input type="file" accept="image/png,image/jpeg,image/webp" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />
          </label>
        </div>
        <p className="text-[11px] text-muted-foreground mt-1">
          Arrange them in reading order. Final PDF = {incCover ? "cover + " : ""}{incInstr ? "instructions + " : ""}{contentSlots} artwork page{contentSlots === 1 ? "" : "s"} = <b>{totalPages}</b> page{totalPages === 1 ? "" : "s"}.
          {typeDef && totalPages !== typeDef.pages && <span className="text-amber-600"> ({typeDef.label} targets {typeDef.pages}.)</span>}
        </p>
        {(incCover || incInstr) && (
          <p className="text-[11px] text-muted-foreground mt-1" data-testid="ps-frontmatter-note">
            Note: {incCover && "the cover"}{incCover && incInstr ? " and instructions pages" : incInstr ? "the instructions page" : " page"} are auto-added at the front (pages {incCover ? "1" : ""}{incCover && incInstr ? "–2" : ""}). To make your artwork the first page, uncheck them above.
          </p>
        )}
        {pages.length === 0 ? (
          <div className="mt-3 border-2 border-dashed rounded-lg p-8 text-center text-muted-foreground text-[13px]">
            No pages yet — upload PNG/JPEG artwork to begin.
          </div>
        ) : (
          <div className="mt-3 grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="ps-pages">
            {pages.map((pg, i) => (
              <div key={i} data-testid={`ps-page-${i}`} className="relative rounded-md border bg-muted/30 p-1.5">
                <img src={pg.dataUrl} alt={pg.name} className="w-full h-28 object-contain rounded bg-white" />
                {pg.enhanced && <span className="absolute top-1 left-1 text-[9px] bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded-full font-semibold">upscaled</span>}
                <div className="mt-1 flex items-center justify-between">
                  <span className="text-[10px] font-semibold text-navy">Artwork {i + 1}/{pages.length} · p.{i + 1 + (incCover ? 1 : 0) + (incInstr ? 1 : 0)}</span>
                  <div className="flex gap-0.5">
                    <button data-testid={`ps-enhance-${i}`} title="Regenerate Larger (upscale to print size)" onClick={() => enhancePage(i)} className="p-0.5 rounded hover:bg-muted text-emerald-700"><Maximize2 className="w-3.5 h-3.5" /></button>
                    <button data-testid={`ps-up-${i}`} title="Move earlier" disabled={i === 0} onClick={() => move(i, -1)} className="p-0.5 rounded hover:bg-muted text-navy disabled:opacity-30 disabled:cursor-not-allowed"><ArrowUp className="w-3.5 h-3.5" /></button>
                    <button data-testid={`ps-down-${i}`} title="Move later" disabled={i === pages.length - 1} onClick={() => move(i, 1)} className="p-0.5 rounded hover:bg-muted text-navy disabled:opacity-30 disabled:cursor-not-allowed"><ArrowDown className="w-3.5 h-3.5" /></button>
                    <button data-testid={`ps-remove-${i}`} onClick={() => removeAt(i)} className="p-0.5 rounded hover:bg-red-50 text-red-600"><X className="w-3.5 h-3.5" /></button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        <button data-testid="ps-build" onClick={build} disabled={busy || !pages.length}
          className="mt-4 inline-flex items-center gap-2 bg-gold text-navy px-4 py-2 rounded-md text-[13px] font-bold disabled:opacity-40">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} Build Governed PDF
        </button>
      </div>

      {/* Step 3 — QA + preview */}
      {result && (
        <div className="rounded-lg border bg-card p-4" data-testid="ps-result">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="text-sm font-bold text-navy flex items-center gap-2"><FileCheck2 className="w-4 h-4" /> {result.product_type_label} · {result.page_count} pages · {result.page_size_label} @ {result.dpi} DPI</h3>
            <div className="flex items-center gap-2">
              <span data-testid="ps-qa-result" className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${RESULT_TONE[result.qa.result]}`}>QA: {result.qa.result.replace("_", " ")}</span>
              <a data-testid="ps-download" href={result.pdf_url} target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded text-[12px] font-semibold"><Download className="w-3.5 h-3.5" /> Open / Download PDF</a>
            </div>
          </div>

          {result.quality_review_required && (
            <div className="mt-3 rounded-md border border-orange-200 bg-orange-50 p-3 text-[12px] text-orange-800 flex items-start gap-2" data-testid="ps-review">
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <div>Human review required — one or more pages are below {result.qa.gate.min_print_dpi} DPI and may print blurry. Upload higher-resolution artwork or approve after reviewing the preview.</div>
            </div>
          )}

          <div className="mt-3 grid lg:grid-cols-2 gap-4">
            <div>
              <p className="text-[11px] font-semibold text-navy uppercase tracking-wide mb-1">Per-page QA (print resolution)</p>
              <div className="rounded-md border divide-y" data-testid="ps-pages-meta">
                {result.pages_meta.map((m) => (
                  <div key={m.page} className="flex items-center justify-between px-3 py-1.5 text-[12px]">
                    <span>Page {m.page} · <span className="text-muted-foreground capitalize">{m.type}</span>{m.source_px ? <span className="text-muted-foreground"> · src {m.source_px[0]}×{m.source_px[1]}</span> : ""}</span>
                    <span className={`font-semibold ${DPI_TONE[m.status]}`}>{m.effective_dpi} DPI · {m.status}</span>
                  </div>
                ))}
              </div>
              {result.qa.warnings?.length > 0 && (
                <ul className="mt-2 text-[11px] text-amber-700 list-disc pl-4 space-y-0.5">
                  {result.qa.warnings.map((w, i) => <li key={i}>{w}</li>)}
                </ul>
              )}
              <div className="mt-3">
                <p className="text-[11px] font-semibold text-navy uppercase tracking-wide mb-1 flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5" /> Attach as download to a listing</p>
                {result.product_id ? (
                  <>
                    <div className="flex flex-wrap gap-2" data-testid="ps-attach">
                      {result.suitable_destinations.map((d) => (
                        <button key={d.id} data-testid={`ps-attach-${d.id}`} onClick={() => attach(result.printable_id, d.id)}
                          className="inline-flex items-center gap-1 text-[11px] bg-navy text-white px-2.5 py-1 rounded-full hover:brightness-110">
                          <Paperclip className="w-3 h-3" /> {d.label}
                        </button>
                      ))}
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1">Attaching registers the deliverable and runs Governed Publication Policy™ — the Factory never auto-publishes.</p>
                  </>
                ) : (
                  <p className="text-[11px] text-muted-foreground">Select a product above (before building) to attach this PDF to an Etsy / QRU / TpT listing. Standalone PDFs can still be downloaded and shared.</p>
                )}
              </div>
            </div>
            <div>
              <p className="text-[11px] font-semibold text-navy uppercase tracking-wide mb-1">PDF preview</p>
              <iframe data-testid="ps-preview" title="PDF preview" src={result.pdf_url} className="w-full h-[520px] rounded-md border bg-white" />
            </div>
          </div>
        </div>
      )}
      {/* Step 4 — Bundle Builder */}
      {sel && history.length > 0 && (
        <div className="rounded-lg border bg-card p-4" data-testid="ps-bundle">
          <h3 className="text-sm font-bold text-navy flex items-center gap-2"><Layers className="w-4 h-4" /> Bundle Builder — combine printables into one activity pack (with Table of Contents)</h3>
          <p className="text-[11px] text-muted-foreground mt-1">Select two or more finished printables, then build a single merged PDF with a branded Contents page.</p>
          <div className="mt-3 rounded-md border divide-y" data-testid="ps-history">
            {history.map((h) => (
              <label key={h.id} data-testid={`ps-hist-${h.id}`} className="flex items-center gap-3 px-3 py-2 text-[12px] cursor-pointer hover:bg-muted/40">
                <input type="checkbox" className="accent-navy" checked={bundleSel.includes(h.id)} onChange={() => toggleBundle(h.id)} disabled={h.product_type === "activity_pack_bundle"} />
                <span className="flex-1 truncate"><b className="text-navy">{h.title || h.product_type}</b> <span className="text-muted-foreground">· {h.product_type.replace(/_/g, " ")} · {h.page_count} pages</span></span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${RESULT_TONE[h.qa_result] || "bg-muted text-muted-foreground"}`}>{(h.qa_result || "").replace("_", " ")}</span>
                <a href={h.pdf_url} target="_blank" rel="noreferrer" className="text-navy hover:underline inline-flex items-center gap-1"><Download className="w-3.5 h-3.5" /></a>
              </label>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <input data-testid="ps-bundle-title" value={bundleTitle} onChange={(e) => setBundleTitle(e.target.value)} placeholder="Activity pack title (optional)" className="rounded border px-2 py-1 text-[12px] w-64" />
            <button data-testid="ps-bundle-build" onClick={buildBundle} disabled={busy || bundleSel.length < 2}
              className="inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded text-[12px] font-semibold disabled:opacity-40">
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Layers className="w-3.5 h-3.5" />} Build Bundle ({bundleSel.length})
            </button>
          </div>
          {bundleResult && (
            <div className="mt-3 rounded-md border p-3 text-[12px]" data-testid="ps-bundle-result">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="font-bold text-navy">{bundleResult.title} · {bundleResult.page_count} pages</span>
                <div className="flex items-center gap-2">
                  <a href={bundleResult.pdf_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded text-[12px] font-semibold"><Download className="w-3.5 h-3.5" /> Open Bundle PDF</a>
                  {bundleResult.suitable_destinations?.map((d) => (
                    <button key={d.id} onClick={() => attach(bundleResult.bundle_id, d.id)} className="inline-flex items-center gap-1 text-[11px] bg-muted text-navy px-2.5 py-1 rounded-full"><Paperclip className="w-3 h-3" /> {d.label}</button>
                  ))}
                </div>
              </div>
              <div className="mt-2">
                <p className="text-[11px] font-semibold text-navy">Table of Contents</p>
                <ul className="mt-1 space-y-0.5">
                  {bundleResult.table_of_contents.map((t, i) => (
                    <li key={i} className="flex justify-between border-b border-dashed py-0.5"><span>{t.title}</span><span className="text-muted-foreground">p.{t.start_page}</span></li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
      {/* Printables Library — standalone home to find & reuse without a product */}
      {library.length > 0 && (
        <div className="rounded-lg border bg-card p-4" data-testid="ps-library">
          <h3 className="text-sm font-bold text-navy flex items-center gap-2"><FileText className="w-4 h-4" /> Printables Library <span className="text-[11px] font-normal text-muted-foreground">({library.length}) — every printable you've built, newest first</span></h3>
          <div className="mt-3 grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {library.slice(0, 18).map((h) => (
              <div key={h.id} data-testid={`ps-lib-${h.id}`} className="rounded-md border p-2.5 text-[12px] flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-semibold text-navy truncate">{h.title || h.product_type}</div>
                  <div className="text-[10px] text-muted-foreground truncate">{h.product_type.replace(/_/g, " ")} · {h.page_count}p{h.product_id ? "" : " · standalone"}</div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-semibold ${RESULT_TONE[h.qa_result] || "bg-muted text-muted-foreground"}`}>{(h.qa_result || "").replace("_", " ")}</span>
                  <a href={h.pdf_url} target="_blank" rel="noreferrer" className="text-navy hover:underline inline-flex items-center gap-1"><Download className="w-3.5 h-3.5" /></a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
