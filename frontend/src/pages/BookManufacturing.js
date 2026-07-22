import { useEffect, useRef, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, MetricCard } from "@/components/qru";
import { ManifestDialog } from "@/components/ManifestDialog";
import {
  Upload, SpellCheck, Palette, Mic, Video, Send, Activity, Loader2, CheckCircle2,
  Lock, FileText, ShieldCheck, ChevronRight, BookOpen, AlertTriangle, Download, MapPin, Share2, Play, DollarSign, ClipboardCheck, Sparkles, FileCheck2, Pencil, X, SearchCheck,
} from "lucide-react";

const ICONS = { upload: Upload, "spell-check": SpellCheck, palette: Palette, mic: Mic, video: Video, send: Send, activity: Activity };
const FINDING_TONE = { "Required correction": "amber", "Recommended improvement": "royal", "Optional stylistic suggestion": "slate", "Founder decision required": "gold" };
const STATE_TONE = (s) => /live|ready for founder|authorized|passed/i.test(s) ? "emerald" : /missing|rejected|not ready|not configured/i.test(s) ? "amber" : "slate";
const A = process.env.REACT_APP_BACKEND_URL;

function abs(u) { return u && u.startsWith("/") ? `${A}${u}` : u; }

async function copyText(text) {
  // Robust copy: clipboard API where available, otherwise a hidden-textarea execCommand fallback.
  try {
    if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); return true; }
  } catch (e) { /* fall through */ }
  try {
    const ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.focus(); ta.select();
    const ok = document.execCommand("copy"); document.body.removeChild(ta); return ok;
  } catch (e) { return false; }
}

export default function BookManufacturing() {
  const [buttons, setButtons] = useState([]);
  const [book, setBook] = useState(null);
  const [tab, setTab] = useState("upload");
  const [busy, setBusy] = useState(false);
  const [proof, setProof] = useState(null);
  const [audio, setAudio] = useState(null);
  const [video, setVideo] = useState(null);
  const [publish, setPublish] = useState(null);
  const [kdp, setKdp] = useState(null);
  const [postPub, setPostPub] = useState(null);
  const [monitor, setMonitor] = useState(null);
  const [shareInfo, setShareInfo] = useState(null);
  const [allBooks, setAllBooks] = useState([]);
  const [systemTitle, setSystemTitle] = useState("QRU Product Manufacturing System™");
  const [editIdentity, setEditIdentity] = useState(false);
  const [inspection, setInspection] = useState(null);
  const [inspecting, setInspecting] = useState(false);
  const [titleDraft, setTitleDraft] = useState("");
  const [authorDraft, setAuthorDraft] = useState("");
  const [subtitleDraft, setSubtitleDraft] = useState("");

  const loadBooks = async () => {
    const { data } = await api.get("/book-mfg/books");
    setAllBooks(data.books || []);
    return data.books || [];
  };
  const reload = async (id) => {
    const { data } = await api.get(`/book-mfg/books/${id}`);
    setBook(data);
    setProof(data.proofing_report || null);
    setPublish(null); setAudio(null); setVideo(null); setMonitor(null);
  };
  const selectBook = async (id) => { setTab("upload"); setShareInfo(null); setInspection(null); await reload(id); };
  useEffect(() => {
    api.get("/book-mfg/config").then((r) => { setButtons(r.data.buttons); if (r.data.system_title) setSystemTitle(r.data.system_title); }).catch(() => {});
    loadBooks().then((books) => {
      const wanted = new URLSearchParams(window.location.search).get("book");
      const target = (wanted && books.find((b) => b.id === wanted)) ? wanted : books[0]?.id;
      if (target) reload(target);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!book) return;
    if (tab === "audio" && !audio) api.get(`/book-mfg/books/${book.id}/audio`).then((r) => setAudio(r.data));
    if (tab === "video" && !video) api.get(`/book-mfg/books/${book.id}/video`).then((r) => setVideo(r.data));
    if (tab === "publish") { api.get(`/book-mfg/books/${book.id}/publish`).then((r) => setPublish(r.data)); api.get(`/book-mfg/books/${book.id}/kdp-checklist`).then((r) => setKdp(r.data)).catch(() => {}); api.get(`/book-mfg/books/${book.id}/post-publish`).then((r) => setPostPub(r.data)).catch(() => {}); }
    if (tab === "monitor" && !monitor) api.get(`/book-mfg/books/${book.id}/monitor`).then((r) => setMonitor(r.data));
  }, [tab, book]); // eslint-disable-line

  const run = async (fn, ok) => {
    setBusy(true);
    try { await fn(); if (ok) toast.success(ok); await reload(book.id); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const doInspect = async () => {
    setInspecting(true);
    try {
      const { data } = await api.get(`/book-mfg/books/${book.id}/inspection`);
      setInspection(data);
      toast[data.summary.clean ? "success" : "message"](
        data.summary.clean ? "No exceptions — inspection clean." : `${data.summary.total_exceptions} exception(s) flagged for your review.`);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setInspecting(false); }
  };

  const doProof = () => run(async () => { const { data } = await api.post(`/book-mfg/books/${book.id}/proof`); setProof(data.report); }, "Proof & Polish complete.");
  const doOpenRevision = () => run(async () => { await api.post(`/book-mfg/books/${book.id}/open-revision`); const { data } = await api.post(`/book-mfg/books/${book.id}/proof`); setProof(data.report); }, "Governed revision opened — you can now edit & resolve findings.");
  const doResolveFinding = (payload) => run(async () => { const { data } = await api.post(`/book-mfg/books/${book.id}/resolve-finding`, payload); setProof(data.report); }, payload.action === "keep" ? "Kept as written (intentional)." : "Correction applied & re-proofed.");
  const doSaveManuscript = (content) => run(async () => { const { data } = await api.post(`/book-mfg/books/${book.id}/manuscript`, { content }); setProof(data.report); }, "Manuscript saved & re-proofed.");
  const doApprove = () => run(() => api.post(`/book-mfg/books/${book.id}/approve-edition`), "Editorial edition locked.");
  const doDesign = () => run(() => api.post(`/book-mfg/books/${book.id}/design`, { base_url: A }), "Design drafted.");
  const doSelectCover = (concept) => run(() => api.post(`/book-mfg/books/${book.id}/select-cover`, { concept, base_url: A }), `Cover ${concept} selected — clean retail edition prepared.`);
  const doAssemble = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/book-mfg/books/${book.id}/assemble-package`);
      toast.success(`Master Output Package assembled (${data.size_kb} KB). Saved to your Factory Library™ below.`);
      await reload(book.id);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const doRenderAudio = (opts) => run(async () => { await api.post(`/book-mfg/books/${book.id}/audio-prototype`, opts || {}); const { data } = await api.get(`/book-mfg/books/${book.id}/audio`); setAudio(data); }, "Narration prototype rendered.");
  const doPricing = (price, currency) => run(() => api.post(`/book-mfg/books/${book.id}/pricing`, { list_price: parseFloat(price), currency }), "Pricing approved.").then(() => api.get(`/book-mfg/books/${book.id}/publish`).then((r) => setPublish(r.data)));
  const doAuthorize = () => run(() => api.post(`/book-mfg/books/${book.id}/authorize`), "Release authorized — the Factory is manufacturing your publication assets.").then(() => { api.get(`/book-mfg/books/${book.id}/publish`).then((r) => setPublish(r.data)); api.get(`/book-mfg/books/${book.id}/post-publish`).then((r) => setPostPub(r.data)).catch(() => {}); });
  const doSanitize = () => run(() => api.post(`/book-mfg/books/${book.id}/sanitize`, { base_url: A }), "Publication Sanitization Pass™ complete — clean retail edition prepared.").then(() => api.get(`/book-mfg/books/${book.id}/publish`).then((r) => setPublish(r.data)));
  const doDraftBlurb = () => run(async () => { const { data } = await api.post(`/book-mfg/books/${book.id}/draft-blurb`); toast.message("Blurb drafted — review & approve.", { description: data.status }); });
  const doSavePublication = (fields, ok) => run(() => api.post(`/book-mfg/books/${book.id}/publication-details`, fields), ok || "Publication details saved.");
  const openEditIdentity = () => { setTitleDraft(book.title || ""); setAuthorDraft(book.author || ""); setSubtitleDraft(book.subtitle || ""); setEditIdentity(true); };
  const applyCleanTitle = () => doSavePublication({ title: book.title_cleanup_suggestion }, `Title cleaned up to “${book.title_cleanup_suggestion}”.`);
  const saveIdentity = async () => {
    if (!titleDraft.trim()) { toast.error("Title cannot be empty."); return; }
    await doSavePublication({ title: titleDraft.trim(), author: authorDraft.trim(), subtitle: subtitleDraft.trim() }, "Title, subtitle & author updated. Re-run Design & Audio to refresh the cover and narration.");
    setEditIdentity(false);
  };
  const doPrintWrap = (paperType) => run(() => api.post(`/book-mfg/books/${book.id}/print-wrap`, { paper_type: paperType }), "Print-ready cover wrap built.");
  const doUploadFile = async (file, meta) => {
    if (!file) return;
    setBusy(true);
    try {
      const b64 = await new Promise((res, rej) => {
        const r = new FileReader();
        r.onload = () => res(String(r.result).split(",")[1]);
        r.onerror = rej; r.readAsDataURL(file);
      });
      const { data } = await api.post(`/book-mfg/upload-file`, { filename: file.name, file_base64: b64, meta });
      toast.success(`“${data.title}” uploaded — immutable original sealed. Working copy ready for Proof & Polish.`);
      await loadBooks();
      await reload(data.id);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const doShare = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/book-mfg/books/${book.id}/share`, { hours: 72, base_url: A });
      const url = abs(data.share_url);
      const copied = await copyText(url);
      setShareInfo({ url, expires_at: data.expires_at, copied });
      toast.success(copied ? "Share link created & copied. Also saved to your Factory Library™." : "Share link created & saved to your Factory Library™ — copy it from the box.");
      await reload(book.id);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  if (!book) return <div className="p-8 text-muted-foreground" data-testid="book-mfg-loading">Loading Book Manufacturing System™…</div>;

  const nav = founderNav(book, tab);

  return (
    <div data-testid="book-mfg-page">
      <PageHeader
        overline={`${systemTitle} · Book Recipe`}
        title="One Product In · One Publication Package Out"
        description="A governed seven-button workflow that manufactures any product type. Each product supplies its own recipe behind the same interface — the Factory does the work; you make the decisions that require judgment. Honest states only — nothing is ever marked done, uploaded, or published unless it truly is."
        actions={<VerifiedBadge label="Treasure Standard™" testid="book-mfg-badge" />}
      />

      <ActivePublicationBanner book={book} tab={tab} buttons={buttons} />

      {/* Book identity — title ALWAYS before Book Record ID */}
      <div className="qru-card qru-goldline p-4 mb-5" data-testid="book-identity">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="min-w-0">
            {editIdentity ? (
              <div className="space-y-2" data-testid="edit-identity-form">
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Book Title</label>
                  <input data-testid="edit-title-input" value={titleDraft} onChange={(e) => setTitleDraft(e.target.value)}
                    className="w-full mt-0.5 border rounded-md p-2 text-sm font-heading text-navy" autoFocus />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Subtitle</label>
                  <input data-testid="edit-subtitle-input" value={subtitleDraft} onChange={(e) => setSubtitleDraft(e.target.value)}
                    placeholder="Optional — shown under the title on the cover" className="w-full mt-0.5 border rounded-md p-2 text-sm text-navy" />
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Author</label>
                  <input data-testid="edit-author-input" value={authorDraft} onChange={(e) => setAuthorDraft(e.target.value)}
                    className="w-full mt-0.5 border rounded-md p-2 text-sm text-navy" />
                </div>
                <p className="text-[10px] text-muted-foreground">Tip: remove file-name artifacts like “FINAL”, “v2”, “DRAFT”. Re-run Design &amp; Audio afterward so the cover and narration pick up the new title.</p>
                <div className="flex gap-2">
                  <button onClick={saveIdentity} disabled={busy} data-testid="save-identity-btn"
                    className="inline-flex items-center gap-1.5 bg-navy text-white px-3 py-1.5 rounded-md text-[12px] font-bold disabled:opacity-40">
                    {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />} Save
                  </button>
                  <button onClick={() => setEditIdentity(false)} data-testid="cancel-identity-btn"
                    className="inline-flex items-center gap-1.5 border border-navy/20 text-navy px-3 py-1.5 rounded-md text-[12px] font-bold">
                    <X className="w-3.5 h-3.5" /> Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <h2 className="font-heading text-xl font-bold text-navy" data-testid="book-title">{book.title}{book.subtitle ? ` — ${book.subtitle}` : ""}</h2>
                  <button onClick={openEditIdentity} data-testid="edit-identity-btn" title="Edit title & author"
                    className="text-muted-foreground hover:text-royal transition-colors shrink-0"><Pencil className="w-3.5 h-3.5" /></button>
                </div>
                <div className="flex items-center gap-2 flex-wrap mt-1">
                  <span className="text-[11px] text-muted-foreground">by {book.author || "—"}</span>
                  <span className="font-mono text-[10px] text-muted-foreground">{book.book_code}</span>
                  <StatusChip status={book.imprint} tone="royal" />
                </div>
                {allBooks.length > 1 && (
                  <select data-testid="book-switcher" value={book.id} onChange={(e) => selectBook(e.target.value)}
                    className="mt-2 text-[12px] border border-border rounded-md bg-card px-2 py-1 text-navy outline-none max-w-full">
                    {allBooks.map((bk) => <option key={bk.id} value={bk.id}>{bk.title} · {bk.book_code}</option>)}
                  </select>
                )}
                {book.content_integrity && book.content_integrity.ok === false && (
                  <div className="mt-2 flex items-start gap-2 bg-red-50 border border-red-300 rounded-md px-3 py-2" data-testid="content-integrity-warning">
                    <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[11px] font-bold text-red-800">Content may be internal Factory documentation — not the book's subject</p>
                      <p className="text-[10px] text-red-700 mt-0.5">{book.content_integrity.message}</p>
                    </div>
                  </div>
                )}
                {book.title_cleanup_suggestion && (
                  <div className="mt-2 flex items-center gap-2 flex-wrap bg-amber-50 border border-amber-200 rounded-md px-3 py-2" data-testid="title-cleanup-banner">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                    <span className="text-[11px] text-amber-900">
                      Looks like a file-name artifact in the title. Clean up to <b>“{book.title_cleanup_suggestion}”</b>?
                    </span>
                    <button onClick={applyCleanTitle} disabled={busy} data-testid="apply-clean-title-btn"
                      className="inline-flex items-center gap-1 bg-navy text-white px-2.5 py-1 rounded text-[11px] font-bold disabled:opacity-40">
                      {busy ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />} Clean up
                    </button>
                    <button onClick={openEditIdentity} data-testid="cleanup-edit-instead-btn"
                      className="text-[11px] text-navy/70 underline">edit manually</button>
                  </div>
                )}
              </>
            )}
          </div>
          <div className="flex flex-col items-end gap-1">
            <StatusChip status={`Source: ${book.source_status}`} tone="amber" testid="source-status" />
            <StatusChip status={`Editorial: ${book.editorial_status}`} tone={book.editorial_locked ? "emerald" : "amber"} testid="editorial-status" />
            <StatusChip status={`Publication: ${book.publication_status}`} tone="slate" testid="publication-status" />
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-border/60 flex items-center justify-between gap-3 flex-wrap">
          <p className="text-[11px] text-muted-foreground">Master Output Package™ — one governed, provenance-stamped bundle of everything the Factory has truly produced.</p>
          <button data-testid="assemble-package-btn" onClick={doAssemble} disabled={busy}
            className="inline-flex items-center gap-1.5 bg-gold text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-50">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Assemble &amp; Download Package
          </button>
          <button data-testid="share-package-btn" onClick={doShare} disabled={busy}
            className="inline-flex items-center gap-1.5 border border-navy/30 text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-50">
            <Share2 className="w-4 h-4" /> Share Link
          </button>
        </div>
      </div>

      {/* QRU Automated Pre-Review Inspection™ — read-only exception list (never rewrites) */}
      <div className="qru-card p-4 mb-5 border-l-4 border-royal" data-testid="preview-inspection-panel">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div>
            <p className="text-sm font-bold text-navy flex items-center gap-1.5">
              <SearchCheck className="w-4 h-4 text-royal" /> Automated Pre-Review Inspection™
            </p>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Runs every automatable check and lists only exceptions — so you review what's flagged, never every word. It never rewrites your book.
            </p>
          </div>
          <button data-testid="run-inspection-btn" onClick={doInspect} disabled={inspecting}
            className="inline-flex items-center gap-1.5 bg-navy text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-50">
            {inspecting ? <Loader2 className="w-4 h-4 animate-spin" /> : <SearchCheck className="w-4 h-4" />} Run Inspection
          </button>
        </div>
        {inspection && (
          <div className="mt-3" data-testid="inspection-report">
            <div className="flex items-center gap-2 flex-wrap mb-3">
              {inspection.summary.clean ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1" data-testid="inspection-clean">
                  <CheckCircle2 className="w-3.5 h-3.5" /> No exceptions — clean
                </span>
              ) : (
                <>
                  <span className={`inline-flex items-center gap-1 text-[11px] font-bold rounded-full px-2.5 py-1 border ${inspection.summary.blocking ? "text-red-700 bg-red-50 border-red-200" : "text-emerald-700 bg-emerald-50 border-emerald-200"}`} data-testid="inspection-blocking">
                    {inspection.summary.blocking} blocking
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2.5 py-1" data-testid="inspection-recommended">
                    {inspection.summary.recommended} recommended
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 bg-slate-50 border border-slate-200 rounded-full px-2.5 py-1" data-testid="inspection-advisory">
                    {inspection.summary.advisory} advisory
                  </span>
                  {inspection.summary.publish_ready && (
                    <span className="text-[10px] text-emerald-700 font-semibold">No blocking issues — publish-ready</span>
                  )}
                </>
              )}
            </div>
            <div className="space-y-2">
              {inspection.exceptions.map((e) => (
                <div key={e.id} data-testid={`inspection-exc-${e.id}`}
                  className={`rounded-md border px-3 py-2 ${e.severity === "blocking" ? "bg-red-50 border-red-200" : e.severity === "recommended" ? "bg-amber-50 border-amber-200" : "bg-muted/30 border-border"}`}>
                  <div className="flex items-center gap-2">
                    <span className={`text-[9px] font-bold uppercase tracking-wide rounded px-1.5 py-0.5 ${e.severity === "blocking" ? "bg-red-600 text-white" : e.severity === "recommended" ? "bg-amber-500 text-white" : "bg-slate-400 text-white"}`}>{e.severity}</span>
                    <p className="text-[12px] font-bold text-navy">{e.label}</p>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1">{e.detail}</p>
                  {e.examples && e.examples.length > 0 && (
                    <p className="text-[10px] text-muted-foreground/80 mt-1 font-mono truncate">{e.examples.slice(0, 6).join(" · ")}</p>
                  )}
                </div>
              ))}
            </div>
            <p className="text-[10px] text-muted-foreground/70 mt-3 italic">
              {inspection.note} Your judgment owns: {(inspection.founder_judgment || []).join(", ")}.
            </p>
          </div>
        )}
      </div>

      {shareInfo && (
        <div className="qru-card p-4 mb-5 border-l-4 border-royal" data-testid="share-box">
          <div className="flex items-center justify-between gap-2 mb-2">
            <p className="text-sm font-bold text-navy flex items-center gap-1.5"><Share2 className="w-4 h-4" /> Read-only review link</p>
            <button data-testid="share-box-close" onClick={() => setShareInfo(null)} className="text-xs text-muted-foreground hover:text-navy">Dismiss</button>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <input data-testid="share-link-input" readOnly value={shareInfo.url} onFocus={(e) => e.target.select()}
              className="flex-1 min-w-[220px] px-2 py-1.5 text-sm border border-border rounded-md bg-muted/40 font-mono text-navy outline-none" />
            <button data-testid="share-copy-btn" onClick={async () => { const ok = await copyText(shareInfo.url); toast[ok ? "success" : "error"](ok ? "Link copied — paste it into Messenger." : "Copy failed — select the text and copy manually."); }}
              className="bg-navy text-white px-3 py-1.5 rounded-md text-sm font-bold">Copy</button>
            <a data-testid="share-open-btn" href={shareInfo.url} target="_blank" rel="noreferrer"
              className="border border-navy/30 text-navy px-3 py-1.5 rounded-md text-sm font-bold">Open</a>
          </div>
          <p className="text-[11px] text-muted-foreground mt-2">Expires {new Date(shareInfo.expires_at).toLocaleString()} · read-only · this is the <b>clean reading copy</b> (finished book only — no manufacturing internals). Anyone with the link can open it (no login).</p>
        </div>
      )}

      <FactoryLibrary book={book} />

      {/* Founder navigation — always answers the five questions */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6" data-testid="founder-nav">
        <NavCard label="Current Stage" value={nav.stage} tone="navy" icon={MapPin} />
        <NavCard label="Completed" value={nav.completed} tone="emerald" icon={CheckCircle2} />
        <NavCard label="Missing" value={nav.missing} tone="amber" icon={AlertTriangle} />
        <NavCard label="Decision Needed" value={nav.decision} tone="gold" icon={ShieldCheck} />
        <NavCard label="Next Step" value={nav.next} tone="royal" icon={ChevronRight} />
      </div>

      {/* The seven buttons */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-6" data-testid="seven-buttons">
        {buttons.map((b) => {
          const Icon = ICONS[b.icon] || FileText;
          const active = tab === b.key;
          return (
            <button key={b.key} data-testid={`btn-${b.key}`} onClick={() => setTab(b.key)}
              className={`shrink-0 inline-flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-bold transition-colors ${active ? "bg-navy text-white" : "bg-muted/50 text-navy hover:bg-muted"}`}>
              <Icon className="w-4 h-4" /> {b.label}
            </button>
          );
        })}
      </div>

      {/* Panels */}
      {tab === "upload" && <UploadPanel book={book} busy={busy} doUploadFile={doUploadFile} />}
      {tab === "proof" && <ProofPanel book={book} proof={proof} busy={busy} doProof={doProof} doApprove={doApprove} doOpenRevision={doOpenRevision} doResolveFinding={doResolveFinding} doSaveManuscript={doSaveManuscript} />}
      {tab === "design" && <DesignPanel book={book} busy={busy} doDesign={doDesign} doSelectCover={doSelectCover} />}
      {tab === "audio" && <AudioPanel book={book} audio={audio} busy={busy} onRender={doRenderAudio} />}
      {tab === "video" && <PlanPanel title="Video" icon={Video} data={video} render={renderVideo} />}
      {tab === "publish" && <PublishPanel data={publish} kdp={kdp} postPub={postPub} book={book} busy={busy} doPricing={doPricing} doAuthorize={doAuthorize} doSanitize={doSanitize} doDraftBlurb={doDraftBlurb} doSavePublication={doSavePublication} doPrintWrap={doPrintWrap} />}
      {tab === "monitor" && <PlanPanel title="Monitor" icon={Activity} data={monitor} render={renderMonitor} />}
    </div>
  );
}

function NavCard({ label, value, tone, icon: Icon }) {
  return (
    <div className="border border-border rounded-md p-3 bg-card">
      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wide flex items-center gap-1"><Icon className="w-3 h-3" />{label}</p>
      <p className="text-[13px] font-semibold text-navy mt-1 leading-tight">{value}</p>
    </div>
  );
}

function ActivePublicationBanner({ book, tab, buttons }) {
  if (!book) return null;
  const auth = book.founder_authorization?.authorized;
  const cover = !!book.artifacts?.design?.selected_cover;
  const sanitized = !!book.artifacts?.sanitization;
  const priced = !!book.pricing?.approved;
  const locked = !!book.editorial_locked;
  const stage = book.manufacturing_job?.stage || (buttons.find((b) => b.key === tab)?.label) || "Upload";
  let status;
  if (auth) status = "Authorized — ready for KDP upload";
  else if (locked && cover && sanitized && priced) status = "Ready for Founder Release Review™ — approve blurb & authorize (Publish tab)";
  else if (locked && cover && sanitized) status = "Next: approve pricing (Publish tab)";
  else if (locked && cover) status = "Next: run Publication Sanitization (Publish tab)";
  else if (locked) status = "Next: choose the final cover (Design tab)";
  else if (book.proofing_report) status = "Next: approve & lock the editorial edition (Proof tab)";
  else if (book.source_status) status = "Next: Proof & Polish";
  else status = "Awaiting manuscript upload";
  const Field = ({ label, value, testid, mono }) => (
    <div className="min-w-0">
      <p className="text-[9px] font-bold uppercase tracking-wider text-gold/80">{label}</p>
      <p className={`text-[13px] font-semibold text-white truncate ${mono ? "font-mono text-[11px]" : ""}`} data-testid={testid} title={value}>{value}</p>
    </div>
  );
  return (
    <div className="sticky top-0 z-30 mb-4 rounded-lg border border-gold/40 bg-navy shadow-lg" data-testid="active-publication-banner">
      <div className="flex items-center gap-3 px-4 py-2.5 flex-wrap">
        <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-navy bg-gold px-2 py-1 rounded-full shrink-0">
          <BookOpen className="w-3 h-3" /> Active Publication™
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-x-6 gap-y-1.5 flex-1 min-w-0">
          <Field label="Book Title" value={book.title || "—"} testid="banner-book-title" />
          <Field label="Book ID" value={`${book.book_code || "—"} · ${book.id}`} testid="banner-book-id" mono />
          <Field label="Author" value={book.author || "—"} testid="banner-author" />
          <Field label="Current Stage" value={stage} testid="banner-current-stage" />
          <Field label="Current Status" value={status} testid="banner-current-status" />
        </div>
      </div>
    </div>
  );
}


function founderNav(b, tab) {
  const design = b.artifacts?.design;
  const completed = [];
  if (b.source_status) completed.push("Upload");
  if (b.proofing_report) completed.push("Proof");
  if (b.editorial_locked) completed.push("Editorial lock");
  if (design) completed.push("Design");
  const missing = [];
  (b.intake_scan?.missing_essentials || []).forEach((m) => {
    if (/cover/i.test(m) && design) return; // resolved once Design runs
    missing.push(m);
  });
  if (design && !design.selected_cover) missing.push("Select final cover");
  if (b.editorial_locked && !b.pricing?.approved) missing.push("Approve pricing");
  if (b.editorial_locked && !b.founder_authorization?.authorized) missing.push("Founder authorization");
  let decision = "None right now";
  if ((b.proofing_report?.unresolved_questions || []).length) decision = b.proofing_report.unresolved_questions[0];
  else if (!b.editorial_locked && b.proofing_report) decision = "Approve & lock editorial edition";
  else if (design && !design.selected_cover) decision = "Select the final cover";
  return {
    stage: b.manufacturing_job?.stage || "Upload",
    completed: completed.join(", ") || "—",
    missing: missing.slice(0, 2).join("; ") || "None",
    decision,
    next: b.manufacturing_job?.next || "Proof & Polish",
  };
}

function UploadManuscript({ busy, doUploadFile }) {
  const [file, setFile] = useState(null);
  const [author, setAuthor] = useState("");
  const [genre, setGenre] = useState("");
  return (
    <Panel title="Upload a New Manuscript" icon={Upload} accent="gold" testid="upload-manuscript">
      <p className="text-[12px] text-muted-foreground mb-3">
        Bring any manuscript into the Factory — <b>.docx, .pdf, .txt or .md</b>. The Factory automatically seals an
        immutable original and creates a separate working copy for you. You never assemble governance by hand — uploading the file is enough.
      </p>
      <div className="space-y-3" data-testid="upload-form">
        <input data-testid="manuscript-file-input" type="file" accept=".docx,.pdf,.txt,.md,.markdown,.text"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-navy file:mr-3 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-navy file:text-white file:font-bold file:cursor-pointer" />
        <div className="grid sm:grid-cols-2 gap-3">
          <input data-testid="manuscript-author" value={author} onChange={(e) => setAuthor(e.target.value)}
            placeholder="Author (optional)" className="px-2 py-1.5 text-sm border border-border rounded-md bg-card outline-none" />
          <input data-testid="manuscript-genre" value={genre} onChange={(e) => setGenre(e.target.value)}
            placeholder="Genre (optional)" className="px-2 py-1.5 text-sm border border-border rounded-md bg-card outline-none" />
        </div>
        <button data-testid="upload-manuscript-btn" disabled={busy || !file}
          onClick={() => doUploadFile(file, { author, genre, source_filename: file?.name })}
          className="inline-flex items-center gap-1.5 bg-gold text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} Upload Manuscript
        </button>
        {file && <p className="text-[11px] text-muted-foreground">Selected: {file.name} ({Math.round(file.size / 1024)} KB)</p>}
      </div>
    </Panel>
  );
}

function UploadPanel({ book, busy, doUploadFile }) {
  const p = book.transparent_provenance || {};
  const ds = book.intake_scan?.detected_structure || {};
  return (
    <div className="space-y-5" data-testid="panel-upload">
      <UploadManuscript busy={busy} doUploadFile={doUploadFile} />
      <div className="grid lg:grid-cols-2 gap-5">
      <Panel title="Canonical Book Record" icon={BookOpen} accent="gold" testid="canonical-record">
        <dl className="text-sm space-y-1.5">
          {[["Title", book.title], ["Subtitle", book.subtitle], ["Author", book.author], ["Imprint", book.imprint],
            ["Edition", book.edition], ["Language", book.language], ["Audience", book.audience], ["Genre", book.genre],
            ["Rights holder", book.rights_holder], ["Book Record ID", book.book_code]].map(([k, v]) => v ? (
            <div key={k} className="flex justify-between gap-3 border-b border-border/50 pb-1">
              <dt className="text-muted-foreground">{k}</dt><dd className="text-navy font-medium text-right">{v}</dd>
            </div>
          ) : null)}
        </dl>
        <div className="mt-3 flex items-center gap-2 text-[11px] text-emerald-700">
          <Lock className="w-3.5 h-3.5" /> Immutable original sealed · separate working copy for edits
        </div>
      </Panel>
      <div className="space-y-5">
        <Panel title="Intake Scan" icon={FileText} accent="royal" testid="intake-scan">
          <div className="space-y-2 text-sm">
            <p><b className="text-navy">Files received:</b> {(book.intake_scan?.files_received || []).join(", ")}</p>
            <p><b className="text-navy">Detected structure:</b> {ds.chapter_count} chapters · {ds.word_count?.toLocaleString()} words</p>
            <p><b className="text-navy">Readiness:</b> <StatusChip status={book.intake_scan?.readiness_status} tone="amber" /></p>
            <p><b className="text-navy">Missing essentials:</b> {(book.intake_scan?.missing_essentials || []).join("; ") || "None"}</p>
            <p><b className="text-navy">Next action:</b> {book.intake_scan?.recommended_next_action}</p>
          </div>
          <ol className="mt-3 grid grid-cols-2 gap-1 text-[11px] text-muted-foreground" data-testid="detected-chapters">
            {(ds.chapters || []).map((c) => <li key={c.number}>Ch {c.number}: {c.title.replace(/^CHAPTER [A-Z]+:?\s*/i, "")}</li>)}
          </ol>
        </Panel>
        <Panel title="Transparent Provenance™" icon={ShieldCheck} accent="gold" testid="provenance">
          <dl className="text-[12px] space-y-1 text-foreground/90">
            <p><b>Source file:</b> {p.source_filename}</p>
            <p><b>Original checksum:</b> <span className="font-mono">{(p.immutable_original_checksum || "").slice(0, 24)}…</span></p>
            <p><b>Received:</b> {p.received_at} by {p.received_by}</p>
            <p><b>Rights holder:</b> {p.rights_holder}</p>
            <p><b>AI contribution:</b> {p.ai_contribution}</p>
            <p className="text-amber-700">{p.governance}</p>
          </dl>
        </Panel>
      </div>
      </div>
    </div>
  );
}

function FactoryLibrary({ book }) {
  const pkgs = [...(book.deliverables || [])].reverse();
  const now = Date.now();
  const shares = [...(book.share_links || [])].reverse();
  if (!pkgs.length && !shares.length) return null;
  return (
    <div className="qru-card p-4 mb-5" data-testid="factory-library">
      <p className="text-sm font-bold text-navy flex items-center gap-1.5 mb-1"><BookOpen className="w-4 h-4" /> Factory Library™</p>
      <p className="text-[11px] text-muted-foreground mb-3">Every rendering the Factory produces is kept here, inside the Factory — download or re-copy any time. Nothing depends on your browser's Downloads folder.</p>
      {pkgs.length > 0 && (
        <div className="mb-3" data-testid="library-packages">
          <p className="text-[10px] font-bold text-royal uppercase tracking-wide mb-1">Packages & Deliverables</p>
          <div className="space-y-1.5">
            {pkgs.map((d, i) => (
              <div key={i} className="flex items-center justify-between gap-2 border-b border-border/50 pb-1.5 text-[12px]">
                <div className="min-w-0">
                  <p className="text-navy font-medium truncate">{d.type} · {d.size_kb} KB</p>
                  <p className="text-[10px] text-muted-foreground">{new Date(d.assembled_at).toLocaleString()} · by {d.by}</p>
                </div>
                <a data-testid={`library-download-${i}`} href={abs(d.url)} target="_blank" rel="noreferrer" download
                  className="shrink-0 inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded-md font-bold">
                  <Download className="w-3.5 h-3.5" /> Download
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
      {shares.length > 0 && (
        <div data-testid="library-shares">
          <p className="text-[10px] font-bold text-royal uppercase tracking-wide mb-1">Review Share Links</p>
          <div className="space-y-1.5">
            {shares.map((s, i) => {
              const expired = new Date(s.expires_at).getTime() < now;
              return (
                <div key={i} className="flex items-center justify-between gap-2 border-b border-border/50 pb-1.5 text-[12px]">
                  <div className="min-w-0">
                    <p className="font-mono text-navy truncate">{abs(s.share_url)}</p>
                    <p className="text-[10px] text-muted-foreground">{expired ? "Expired" : "Active"} · expires {new Date(s.expires_at).toLocaleString()}</p>
                  </div>
                  {!expired && (
                    <button data-testid={`library-copy-share-${i}`} onClick={async () => { const ok = await copyText(abs(s.share_url)); toast[ok ? "success" : "error"](ok ? "Link copied." : "Copy failed — select manually."); }}
                      className="shrink-0 bg-navy text-white px-3 py-1.5 rounded-md font-bold">Copy</button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function ProofPanel({ book, proof, busy, doProof, doApprove, doOpenRevision, doResolveFinding, doSaveManuscript }) {
  const locked = book.editorial_locked;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  useEffect(() => { setDraft(book?.working_copy?.content || ""); setEditing(false); }, [book?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div data-testid="panel-proof" className="space-y-4">
      <Panel title="Proof & Polish" icon={SpellCheck} accent="royal"
        right={
          <div className="flex gap-2 flex-wrap">
            <button data-testid="run-proof-btn" onClick={doProof} disabled={busy || locked}
              className="inline-flex items-center gap-1.5 bg-navy text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <SpellCheck className="w-4 h-4" />} Run Proof
            </button>
            {locked ? (
              <button data-testid="open-revision-btn" onClick={doOpenRevision} disabled={busy}
                className="inline-flex items-center gap-1.5 border border-navy/30 text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40">
                <Lock className="w-4 h-4" /> Open a Governed Revision
              </button>
            ) : (
              <button data-testid="approve-edition-btn" onClick={doApprove} disabled={busy || !proof}
                className="inline-flex items-center gap-1.5 bg-gold text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40">
                <Lock className="w-4 h-4" /> Approve &amp; Lock
              </button>
            )}
          </div>
        }>
        {locked && (
          <div className="mb-3 rounded-md bg-emerald-50 border border-emerald-200 px-3 py-2 text-[12px] text-emerald-800" data-testid="locked-note">
            This editorial edition is <b>approved &amp; locked</b> — your immutable master. To fix or keep a flagged word, open a governed revision (the current version is archived, never overwritten).
          </div>
        )}
        {!proof ? (
          <p className="text-sm text-muted-foreground py-4">Run Proof &amp; Polish to generate a proofing report. The Factory reports findings — it never silently rewrites the author's voice.</p>
        ) : (
          <div>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-4" data-testid="proof-counts">
              {[["Words", proof.counts.words], ["Chapters", proof.counts.chapters], ["Required", proof.counts.required],
                ["Recommended", proof.counts.recommended], ["Decisions", proof.counts.founder_decision], ["Kept", proof.counts.kept || 0]].map(([k, v]) => (
                <div key={k} className="border border-border rounded-md px-2 py-1.5 text-center">
                  <p className="text-lg font-bold text-navy">{v}</p><p className="text-[10px] text-muted-foreground">{k}</p>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-muted-foreground italic mb-2">{proof.voice_note}</p>
            <div className="space-y-2" data-testid="proof-findings">
              {proof.findings.length === 0 ? <p className="text-sm text-emerald-700">No issues found. Clean manuscript.</p> :
                proof.findings.map((f, i) => {
                  const kept = f.status === "kept";
                  return (
                    <div key={f.id || i} data-testid={`finding-${i}`} className="flex items-start justify-between gap-2 border-b border-border/50 pb-2.5">
                      <div className="flex items-start gap-2 min-w-0">
                        <StatusChip status={f.type} tone={FINDING_TONE[f.type]} />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-navy">{f.issue}</p>
                          <p className="text-[12px] text-muted-foreground">{f.detail}</p>
                          {f.snippet && <p className="text-[11px] text-muted-foreground mt-0.5 italic truncate">…{f.snippet}…</p>}
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {kept ? (
                          <StatusChip status="Kept as written ✓" tone="emerald" testid={`finding-kept-${i}`} />
                        ) : locked ? (
                          <span className="text-[10px] text-muted-foreground">Open a revision to resolve</span>
                        ) : (
                          <>
                            <button data-testid={`finding-keep-${i}`} onClick={() => doResolveFinding({ issue: f.issue, action: "keep" })} disabled={busy}
                              className="text-[11px] font-bold border border-emerald-300 text-emerald-700 px-2 py-1 rounded-md disabled:opacity-40">Keep as written</button>
                            {f.correctable && (
                              <button data-testid={`finding-correct-${i}`} onClick={() => doResolveFinding({ issue: f.issue, action: "correct", span: f.span, suggested_fix: f.suggested_fix, fix_kind: f.fix_kind })} disabled={busy}
                                className="text-[11px] font-bold bg-navy text-white px-2 py-1 rounded-md disabled:opacity-40">Correct it</button>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </Panel>

      {!locked && (
        <Panel title="Manuscript Editor" icon={FileText} accent="royal" testid="manuscript-editor"
          right={
            <button data-testid="toggle-editor-btn" onClick={() => setEditing((e) => !e)}
              className="text-sm font-bold text-navy border border-navy/30 px-3 py-1.5 rounded-md">
              {editing ? "Close editor" : "Edit manuscript"}
            </button>
          }>
          {!editing ? (
            <p className="text-[12px] text-muted-foreground">Make surgical fixes above, or open the full editor to edit anywhere. Every save is a tracked revision and automatically re-proofs — nothing changes silently.</p>
          ) : (
            <div className="space-y-2" data-testid="manuscript-edit-area">
              <textarea data-testid="manuscript-textarea" value={draft} onChange={(e) => setDraft(e.target.value)} rows={16}
                className="w-full px-3 py-2 text-sm border border-border rounded-md bg-card outline-none font-mono resize-y" />
              <div className="flex items-center gap-2">
                <button data-testid="save-manuscript-btn" onClick={() => doSaveManuscript(draft)} disabled={busy || !draft.trim() || draft === (book?.working_copy?.content || "")}
                  className="inline-flex items-center gap-1.5 bg-gold text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40">
                  <CheckCircle2 className="w-4 h-4" /> Save &amp; Re-proof
                </button>
                <button onClick={() => setDraft(book?.working_copy?.content || "")} disabled={busy}
                  className="text-sm text-muted-foreground hover:text-navy">Reset</button>
                <span className="text-[11px] text-muted-foreground ml-auto">{draft.split(/\s+/).filter(Boolean).length} words</span>
              </div>
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}

function LegibilityPreview({ concepts }) {
  // Inherited part of the Cover Design Recipe™ — proves each concept stays legible at retail sizes.
  // Retail contexts (approx pixel widths at which shoppers actually see a cover):
  const sizes = [
    { key: "full", label: "Full cover", w: 96 },
    { key: "amazon", label: "Amazon thumb", w: 60 },
    { key: "mobile", label: "Mobile search", w: 40 },
  ];
  return (
    <div data-testid="legibility-preview" className="rounded-md border border-border p-3 bg-muted/30">
      <p className="text-xs font-bold text-navy uppercase tracking-wide mb-1">Thumbnail Legibility Preview</p>
      <p className="text-[11px] text-muted-foreground mb-3">Every concept shown at the sizes shoppers actually see it — plus a grayscale check for contrast. Prove the title & author read before you choose.</p>
      <div className="space-y-4">
        {concepts.map((c) => (
          <div key={c.concept} data-testid={`legibility-concept-${c.concept}`} className="flex flex-wrap items-end gap-4 pb-3 border-b border-border/60 last:border-0 last:pb-0">
            <div className="min-w-[120px]">
              <p className="text-[11px] font-bold text-navy">{c.name}</p>
              {c.status === "success"
                ? <StatusChip status="AI art ✓" tone="emerald" />
                : <StatusChip status="AI art failed" tone="amber" />}
              <p className="text-[10px] text-muted-foreground mt-1 max-w-[160px] leading-tight">{c.readability_status}</p>
            </div>
            {sizes.map((s) => (
              <div key={s.key} className="text-center">
                <img src={abs(c.url)} alt={`${c.name} ${s.label}`} style={{ width: s.w }}
                  className="aspect-[2/3] object-cover rounded-sm border border-border shadow-sm" />
                <p className="text-[9px] text-muted-foreground mt-1">{s.label}</p>
              </div>
            ))}
            <div className="text-center">
              <img src={abs(c.url)} alt={`${c.name} grayscale`} style={{ width: 60, filter: "grayscale(1) contrast(1.15)" }}
                className="aspect-[2/3] object-cover rounded-sm border border-border shadow-sm" />
              <p className="text-[9px] text-muted-foreground mt-1">Grayscale</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DesignPanel({ book, busy, doDesign, doSelectCover }) {
  const d = book.artifacts?.design;
  const prov = d?.cover_provenance;
  return (
    <div data-testid="panel-design">
      <Panel title="Design" icon={Palette} accent="gold"
        right={
          <button data-testid="run-design-btn" onClick={doDesign} disabled={busy || !book.editorial_locked}
            className="inline-flex items-center gap-1.5 bg-navy text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40"
            title={book.editorial_locked ? "" : "Lock the editorial edition first"}>
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Palette className="w-4 h-4" />} Generate Design
          </button>
        }>
        {!book.editorial_locked && <p className="text-sm text-amber-700 py-2">Approve & lock the editorial edition in Proof & Polish first — no downstream format may change approved text.</p>}
        {!d ? (
          <p className="text-sm text-muted-foreground py-4">Generate print interior, EPUB, and three cover concepts from the approved edition.</p>
        ) : (
          <div className="space-y-5">
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-bold text-navy uppercase tracking-wide">Cover Concepts (choose one)</p>
                {prov && <span data-testid="cover-provenance" className="text-[10px] text-muted-foreground">
                  {prov.concepts_with_ai_art}/{prov.concepts_requested} with AI art · {prov.art_model}
                </span>}
              </div>
              <div className="grid grid-cols-3 gap-3" data-testid="cover-concepts">
                {d.cover_concepts.map((c) => {
                  const sel = d.selected_cover?.concept === c.concept;
                  const ok = c.status === "success";
                  return (
                    <button key={c.concept} data-testid={`cover-${c.concept}`} onClick={() => ok && doSelectCover(c.concept)}
                      disabled={!ok}
                      title={ok ? "" : (c.failure_reason || "AI art could not be generated for this concept")}
                      className={`text-left rounded-md overflow-hidden border-2 transition-colors ${sel ? "border-gold" : ok ? "border-border hover:border-navy" : "border-amber-300 cursor-not-allowed opacity-90"}`}>
                      <div className="relative">
                        <img src={abs(c.url)} alt={c.name} className="w-full aspect-[2/3] object-cover" />
                        {!ok && <span data-testid={`cover-failed-${c.concept}`}
                          className="absolute top-1 left-1 right-1 text-[9px] font-bold text-white bg-amber-600/90 rounded px-1 py-0.5 text-center">
                          AI art failed — not real art
                        </span>}
                      </div>
                      <div className="p-1.5">
                        <p className="text-[11px] font-bold text-navy">{c.name}</p>
                        {sel ? <StatusChip status="Selected" tone="gold" />
                          : ok ? <StatusChip status="AI art ✓" tone="emerald" />
                          : <StatusChip status="Failed" tone="amber" />}
                        {!ok && c.failure_reason && <p className="text-[9px] text-amber-700 mt-1 leading-tight">{c.failure_reason}</p>}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
            <LegibilityPreview concepts={d.cover_concepts} />
            <div className="flex flex-wrap gap-3" data-testid="design-files">
              {d.print?.paperback_interior_pdf && (
                <a href={abs(d.print.paperback_interior_pdf)} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1.5 border border-navy/20 text-navy px-4 py-2 rounded-md text-sm font-medium">
                  <Download className="w-4 h-4" /> Paperback Interior (PDF · {d.print.trim_size})
                </a>
              )}
              {d.ebook?.epub && (
                <a href={abs(d.ebook.epub)} target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1.5 border border-navy/20 text-navy px-4 py-2 rounded-md text-sm font-medium">
                  <Download className="w-4 h-4" /> EPUB (Kindle-ready)
                </a>
              )}
            </div>
            <p className="text-[11px] text-muted-foreground">{d.notes}</p>
          </div>
        )}
      </Panel>
    </div>
  );
}

const NARRATION_VOICES = [
  { id: "sage", label: "Sage — warm, calm (default)" },
  { id: "alloy", label: "Alloy — neutral, clear" },
  { id: "ash", label: "Ash — steady, grounded" },
  { id: "coral", label: "Coral — bright, friendly" },
  { id: "echo", label: "Echo — smooth, measured" },
  { id: "fable", label: "Fable — expressive, storytelling" },
  { id: "nova", label: "Nova — energetic, youthful" },
  { id: "onyx", label: "Onyx — deep, authoritative" },
  { id: "shimmer", label: "Shimmer — soft, gentle" },
];

function AudioPanel({ book, audio, busy, onRender }) {
  const proto = book.artifacts?.audio?.prototype || audio?.prototype;
  const timing = book.artifacts?.audio || {};
  const [voice, setVoice] = useState(book.narration_voice || proto?.voice_id || "sage");
  const [speed, setSpeed] = useState(book.narration_speed || proto?.speed || 1.0);
  const [useCustom, setUseCustom] = useState(false);
  const [script, setScript] = useState(proto?.custom_script || "");
  const render = () => onRender({ voice, speed: Number(speed), custom_script: useCustom ? script : null });

  const [ab, setAb] = useState(book.artifacts?.audio?.full_audiobook || null);
  const [abJob, setAbJob] = useState(null);
  const abTimer = useRef(null);
  const abRunning = abJob?.status === "running";
  useEffect(() => () => { if (abTimer.current) clearInterval(abTimer.current); }, []);
  const pollAb = () => {
    if (abTimer.current) clearInterval(abTimer.current);
    abTimer.current = setInterval(async () => {
      try {
        const { data } = await api.get(`/book-mfg/books/${book.id}/audiobook/status`);
        setAbJob(data);
        if (data.status !== "running") {
          clearInterval(abTimer.current); abTimer.current = null;
          if (data.status === "complete") {
            const { data: bk } = await api.get(`/book-mfg/books/${book.id}`);
            setAb(bk.artifacts?.audio?.full_audiobook || null);
            toast.success(`Full audiobook ready — ${(bk.artifacts?.audio?.full_audiobook?.duration_min) || "?"} min.`);
          } else if (data.status === "failed") {
            toast.error(`Audiobook render failed: ${data.error || "unknown error"}`);
          }
        }
      } catch { clearInterval(abTimer.current); abTimer.current = null; }
    }, 3000);
  };
  const startAudiobook = async () => {
    try {
      const { data } = await api.post(`/book-mfg/books/${book.id}/audiobook`, { voice, speed: Number(speed) });
      setAbJob({ status: "running", done: 0, total: data.total });
      toast.message(`Rendering full audiobook (${data.total} chapters)… this runs in the background.`);
      pollAb();
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not start audiobook render."); }
  };

  return (
    <div data-testid="panel-audio">
      <Panel title="Audio" icon={Mic} accent="royal"
        right={
          <button data-testid="render-audio-btn" onClick={render} disabled={busy}
            className="inline-flex items-center gap-1.5 bg-navy text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-60">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Render Narration Prototype
          </button>
        }>
        {/* Voice & tone controls */}
        <div className="mb-4 border border-border rounded-md p-3 bg-muted/20" data-testid="narration-controls">
          <p className="text-[11px] font-bold uppercase tracking-wide text-navy mb-2">Narrator voice &amp; pace</p>
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Voice</label>
              <select data-testid="narration-voice" value={voice} onChange={(e) => setVoice(e.target.value)}
                className="w-full mt-0.5 border rounded-md p-2 text-sm text-navy bg-card">
                {NARRATION_VOICES.map((v) => <option key={v.id} value={v.id}>{v.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Speed · {Number(speed).toFixed(2)}×</label>
              <input type="range" min="0.5" max="1.5" step="0.05" value={speed} data-testid="narration-speed"
                onChange={(e) => setSpeed(e.target.value)} className="w-full mt-2 accent-navy" />
            </div>
          </div>
          <label className="flex items-center gap-2 text-[12px] text-navy mt-3">
            <input type="checkbox" checked={useCustom} data-testid="narration-custom-toggle"
              onChange={(e) => setUseCustom(e.target.checked)} /> Write my own narration text (instead of the auto Chapter-1 opening)
          </label>
          {useCustom && (
            <textarea data-testid="narration-script" value={script} onChange={(e) => setScript(e.target.value)}
              rows={5} placeholder="Type exactly what the narrator should read…"
              className="w-full mt-2 border rounded-md p-2 text-sm text-navy" />
          )}
          <p className="text-[10px] text-muted-foreground mt-2">Voices are OpenAI TTS presets. Each render uses AI credits. Your choice is saved to this book.</p>
        </div>
        {proto ? (
          <div className="mb-4 border border-gold/40 bg-gold/[0.06] rounded-md p-3" data-testid="audio-prototype">
            <p className="text-[12px] text-amber-800 font-semibold mb-2">{proto.label}</p>
            <audio controls src={abs(proto.url)} className="w-full" data-testid="audio-player" />
            <p className="text-[11px] text-muted-foreground mt-1">Voice: {proto.voice} · {proto.duration_sec}s · Full-book estimate ~{timing.full_book_estimate_min} min</p>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground mb-4">Render a real AI narration prototype of Chapter 1's opening for pacing review. It is honestly labeled — not for commercial distribution.</p>
        )}

        {/* Full-length audiobook */}
        <div className="mb-4 border border-royal/30 bg-royal/[0.04] rounded-md p-3" data-testid="full-audiobook-section">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <p className="text-[12px] font-bold text-navy flex items-center gap-1.5"><BookOpen className="w-3.5 h-3.5 text-royal" /> Full-length audiobook</p>
            <button onClick={startAudiobook} disabled={abRunning} data-testid="render-audiobook-btn"
              className="inline-flex items-center gap-1.5 bg-royal text-white px-3 py-1.5 rounded-md text-[12px] font-bold disabled:opacity-50">
              {abRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              {abRunning ? `Rendering ${abJob.done}/${abJob.total}…` : (ab ? "Re-render full audiobook" : "Render full audiobook")}
            </button>
          </div>
          {abRunning && (
            <div className="mt-2" data-testid="audiobook-progress">
              <div className="h-1.5 bg-navy/10 rounded-full overflow-hidden">
                <div className="h-full bg-royal transition-all" style={{ width: `${Math.round((abJob.done / Math.max(1, abJob.total)) * 100)}%` }} />
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">Narrating chapter {abJob.done} of {abJob.total}. This runs in the background — you can keep working.</p>
            </div>
          )}
          {ab && !abRunning && (
            <div className="mt-2" data-testid="full-audiobook-player">
              <audio controls src={abs(ab.url)} className="w-full" />
              <p className="text-[11px] text-muted-foreground mt-1">{ab.duration_min} min · {ab.chapters?.length || 0} chapters · voice {ab.voice_id}</p>
              <p className="text-[10px] text-amber-700 mt-1">{ab.label}</p>
            </div>
          )}
          {!ab && !abRunning && (
            <p className="text-[11px] text-muted-foreground mt-1.5">Narrates every chapter in your chosen voice and stitches them into one MP3 (with chapter markers). Runs in the background; uses AI credits per run.</p>
          )}
        </div>

        {audio && renderAudio(audio)}
      </Panel>
    </div>
  );
}

function PlanPanel({ title, icon, data, render }) {
  return (
    <Panel title={title} icon={icon} accent="royal" testid={`panel-${title.toLowerCase()}`}>
      {!data ? <p className="text-sm text-muted-foreground py-4">Loading…</p> : render(data)}
    </Panel>
  );
}

function renderAudio(d) {
  return (
    <div className="space-y-4 text-sm">
      {Object.entries(d.paths).map(([k, v]) => (
        <div key={k} className="border border-border rounded-md p-3">
          <div className="flex items-center gap-2"><b className="text-navy capitalize">{k.replace(/_/g, " ")}</b><StatusChip status={v.state} tone={STATE_TONE(v.state)} /></div>
          {v.note && <p className="text-[12px] text-muted-foreground mt-1">{v.note}</p>}
          {v.deliverables && <p className="text-[12px] mt-1"><b>Deliverables:</b> {v.deliverables.join(", ")}</p>}
        </div>
      ))}
      <p className="text-[11px] text-amber-700">{d.honesty}</p>
    </div>
  );
}

function renderVideo(d) {
  return (
    <div className="space-y-4 text-sm">
      {["youtube", "youtube_shorts", "tiktok", "podcast"].map((k) => d[k] ? (
        <div key={k} className="border border-border rounded-md p-3">
          <div className="flex items-center gap-2"><b className="text-navy capitalize">{k.replace(/_/g, " ")}</b><StatusChip status={d[k].state} tone={STATE_TONE(d[k].state)} /></div>
          <p className="text-[12px] mt-1">{d[k].items.join(" · ")}</p>
        </div>
      ) : null)}
      <p className="text-[11px] text-amber-700">{d.policy}</p>
    </div>
  );
}

function renderMonitor(d) {
  return (
    <div className="space-y-3 text-sm">
      {["retail", "youtube", "tiktok", "audio"].map((k) => (
        <div key={k} className="border border-border rounded-md p-3">
          <div className="flex items-center gap-2"><b className="text-navy capitalize">{k}</b><StatusChip status={d[k].state} tone={STATE_TONE(d[k].state)} /></div>
          <p className="text-[12px] text-muted-foreground mt-1">{d[k].metrics.join(" · ")}</p>
        </div>
      ))}
      <p className="text-[11px] text-amber-700">{d.honesty}</p>
    </div>
  );
}

function SanitizationPanel({ book, busy, doSanitize }) {
  const s = book?.artifacts?.sanitization;
  return (
    <Panel title="Publication Sanitization Pass™" icon={ShieldCheck} accent="royal" testid="sanitization-panel"
      right={
        <button data-testid="run-sanitize-btn" onClick={doSanitize} disabled={busy}
          className="inline-flex items-center gap-1.5 bg-navy text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-50">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <SpellCheck className="w-4 h-4" />} {s ? "Re-run" : "Run"} Sanitization
        </button>
      }>
      <p className="text-[12px] text-muted-foreground mb-3">
        Prepares the clean <b>retail edition</b> before Final Release: removes internal placeholders (e.g. "(working title)"),
        strips manufacturing metadata from reader-facing pages, and generates a proper Title Page, Copyright Page & Colophon.
        Manufacturing metadata stays in the Canonical Book Record & Master Package — never printed in the retail edition.
      </p>
      {!s ? (
        <p className="text-sm text-amber-700 py-2" data-testid="sanitize-not-run">Not yet run — the Final Release Gate stays closed until the retail edition is sanitized.</p>
      ) : (
        <div className="space-y-3" data-testid="sanitize-result">
          <div className="flex flex-wrap gap-3 text-[12px]">
            <StatusChip status={`${s.placeholders_removed} internal marker(s) removed`} tone={s.placeholders_removed ? "gold" : "emerald"} />
            {s.front_matter_block_removed && <StatusChip status="Embedded title block removed" tone="royal" />}
            <StatusChip status="Clean retail edition prepared" tone="emerald" />
          </div>
          {s.placeholders_found?.length > 0 && (
            <div data-testid="sanitize-findings" className="text-[11px] text-muted-foreground border border-border rounded-md p-2 max-h-28 overflow-y-auto">
              {s.placeholders_found.map((f, i) => (
                <div key={i} className="border-b border-border/50 py-1 last:border-0">
                  <span className="font-bold text-navy">{f.marker}</span> — “{f.text}” <span className="opacity-70">… {f.context}</span>
                </div>
              ))}
            </div>
          )}
          <div className="grid sm:grid-cols-3 gap-3" data-testid="clean-pages">
            {[["Title Page", [s.title_page?.title, s.title_page?.subtitle, s.title_page?.author, s.title_page?.imprint]],
              ["Copyright Page", s.copyright_page],
              ["Colophon", s.colophon?.slice(1)]].map(([label, lines], i) => (
              <div key={i} className="rounded-md border border-border p-2 bg-card">
                <p className="text-[10px] font-bold text-royal uppercase tracking-wide mb-1">{label}</p>
                <div className="text-[10px] text-navy space-y-1 max-h-32 overflow-y-auto">
                  {(lines || []).filter(Boolean).map((ln, j) => <p key={j}>{ln}</p>)}
                </div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-3" data-testid="retail-files">
            {s.retail_edition?.paperback_interior_pdf && (
              <a href={abs(s.retail_edition.paperback_interior_pdf)} target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1.5 border border-navy/20 text-navy px-3 py-1.5 rounded-md text-[12px] font-medium">
                <Download className="w-4 h-4" /> Retail Interior (PDF)
              </a>
            )}
            {s.retail_edition?.epub && (
              <a href={abs(s.retail_edition.epub)} target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-1.5 border border-navy/20 text-navy px-3 py-1.5 rounded-md text-[12px] font-medium">
                <Download className="w-4 h-4" /> Retail EPUB
              </a>
            )}
          </div>
          <p className="text-[10px] text-muted-foreground">{s.separation_note}</p>
        </div>
      )}
    </Panel>
  );
}

function KdpChecklist({ kdp }) {
  if (!kdp) return null;
  const icon = { confirmed: "✓", suggested: "~", needs_founder: "○" };
  const tone = { confirmed: "text-emerald-600", suggested: "text-amber-600", needs_founder: "text-rose-600" };
  return (
    <Panel title="Ready-for-KDP™ Checklist" icon={ClipboardCheck} accent="gold" testid="kdp-panel">
      <div className="flex items-center gap-2 mb-2">
        <StatusChip status={kdp.ready ? "All fields ready" : `${kdp.pending_founder.length} field(s) need you`} tone={kdp.ready ? "emerald" : "amber"} />
        <span className="text-[11px] text-muted-foreground">Also saved in your Master Package → 07_METADATA</span>
      </div>
      <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1" data-testid="kdp-fields">
        {kdp.fields.map((f, i) => (
          <div key={i} className="flex items-start gap-1.5 text-[12px] border-b border-border/40 py-1">
            <span className={`font-bold ${tone[f.status]}`}>{icon[f.status]}</span>
            <span className="font-medium text-navy min-w-[120px]">{f.field}:</span>
            <span className="text-muted-foreground break-words">{String(f.value)}</span>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-muted-foreground mt-2">✓ confirmed · ~ suggested (confirm on KDP) · ○ needs your input. {kdp.note}</p>
    </Panel>
  );
}

function PricingAdvisorPanel({ book, busy, doPricing }) {
  const [adv, setAdv] = useState(null);
  const [loading, setLoading] = useState(false);
  const [paper, setPaper] = useState("white");
  const [scenIn, setScenIn] = useState("9.99, 12.99, 14.99");
  const [scen, setScen] = useState(null);
  if (!book) return null;

  const getAdvice = async () => {
    setLoading(true);
    try { const { data } = await api.get(`/book-mfg/books/${book.id}/pricing-advisor?paper_type=${paper}`); setAdv(data); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setLoading(false); }
  };
  const runScenarios = async () => {
    const prices = scenIn.split(",").map((s) => parseFloat(s.trim())).filter((n) => !isNaN(n));
    if (!prices.length) return;
    setLoading(true);
    try { const { data } = await api.post(`/book-mfg/books/${book.id}/pricing-scenarios`, { prices, paper_type: paper }); setScen(data.scenarios || []); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setLoading(false); }
  };
  const r = adv?.recommendation;
  const posTone = (p) => (p === "Premium" ? "gold" : p === "Budget" ? "slate" : "royal");
  const confTone = (c) => (c === "High" ? "emerald" : c === "Medium" ? "amber" : "slate");

  return (
    <Panel title="QRU Pricing Advisor™" icon={DollarSign} accent="gold" testid="pricing-advisor">
      <p className="text-[11px] text-muted-foreground mb-3">Evidence-based recommendation. Recommends, never sets — you always make the final call.</p>
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <select value={paper} onChange={(e) => setPaper(e.target.value)} data-testid="advisor-paper-select"
          className="px-2 py-1.5 text-sm border border-border rounded-md bg-card outline-none">
          <option value="white">White paper (B&W)</option>
          <option value="cream">Cream paper (B&W)</option>
          <option value="color">Premium color</option>
        </select>
        <button data-testid="get-pricing-advice-btn" onClick={getAdvice} disabled={loading}
          className="inline-flex items-center gap-1.5 bg-navy text-white px-3 py-1.5 rounded-md text-sm font-bold disabled:opacity-40">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <DollarSign className="w-4 h-4" />} Get Recommendation
        </button>
      </div>

      {r && (
        <div className="space-y-3" data-testid="advisor-result">
          <div className="grid sm:grid-cols-2 gap-3">
            <div className="rounded-lg border border-border/60 p-3 bg-card">
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Recommended eBook</p>
              <p className="text-2xl font-bold text-navy" data-testid="rec-ebook-price">${r.ebook_price}</p>
              <p className="text-[11px] text-muted-foreground">Est. royalty ${r.estimated_royalty.ebook.amount} ({r.estimated_royalty.ebook.rate})</p>
            </div>
            <div className="rounded-lg border border-border/60 p-3 bg-card">
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground">Recommended Paperback</p>
              <p className="text-2xl font-bold text-navy" data-testid="rec-paperback-price">${r.paperback_price}</p>
              <p className="text-[11px] text-muted-foreground">Est. royalty ${r.estimated_royalty.paperback.amount} · print ${adv.inputs.print_cost}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <StatusChip status={`Position: ${r.price_position}`} tone={posTone(r.price_position)} testid="price-position" />
            <StatusChip status={`Confidence: ${r.confidence_level}`} tone={confTone(r.confidence_level)} testid="confidence-level" />
            <StatusChip status={`${adv.inputs.page_count}${adv.inputs.page_count_exact ? "" : "~"} pp · ${adv.inputs.genre_bucket}`} tone="slate" />
          </div>
          <div className="text-[12px] text-navy/90">
            <span className="font-semibold">Comparable market range:</span> eBook {r.comparable_market_range.ebook} · Paperback {r.comparable_market_range.paperback}
            <p className="text-[11px] text-muted-foreground mt-0.5">{r.comparable_market_range.basis}</p>
          </div>
          <div className="rounded-lg bg-muted/40 border border-border/50 p-3" data-testid="founder-notes">
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1">Founder Notes</p>
            <p className="text-sm text-navy/90">{r.founder_notes}</p>
          </div>
          <button data-testid="approve-recommended-price-btn" onClick={() => doPricing(r.paperback_price, "USD")} disabled={busy}
            className="inline-flex items-center gap-1.5 bg-gold text-navy px-3 py-1.5 rounded-md text-sm font-bold disabled:opacity-40">
            <CheckCircle2 className="w-4 h-4" /> Approve ${r.paperback_price} paperback (Founder)
          </button>
          <p className="text-[10px] text-amber-700">{adv.provenance.disclaimer} · Notes by {adv.provenance.founder_notes_model}.</p>

          {/* Scenario comparison */}
          <div className="pt-3 border-t border-border/50">
            <p className="text-[11px] font-semibold text-navy mb-1.5">Compare pricing scenarios</p>
            <div className="flex items-center gap-2 mb-2">
              <input value={scenIn} onChange={(e) => setScenIn(e.target.value)} data-testid="scenario-input"
                placeholder="e.g. 9.99, 12.99, 14.99" className="flex-1 px-2 py-1.5 text-sm border border-border rounded-md bg-card outline-none" />
              <button data-testid="run-scenarios-btn" onClick={runScenarios} disabled={loading}
                className="bg-navy text-white px-3 py-1.5 rounded-md text-sm font-bold disabled:opacity-40">Compare</button>
            </div>
            {scen && scen.length > 0 && (
              <div className="overflow-x-auto" data-testid="scenario-table">
                <table className="w-full text-[12px]">
                  <thead><tr className="text-left text-muted-foreground border-b border-border/50">
                    <th className="py-1 pr-2">Price</th><th className="py-1 pr-2">PB royalty</th><th className="py-1 pr-2">Margin</th><th className="py-1 pr-2">eBook royalty</th><th className="py-1">Position</th></tr></thead>
                  <tbody>
                    {scen.map((s, i) => (
                      <tr key={i} className="border-b border-border/30" data-testid={`scenario-row-${i}`}>
                        <td className="py-1 pr-2 font-semibold text-navy">${s.price}</td>
                        <td className={`py-1 pr-2 ${s.paperback_royalty < 0 ? "text-red-600" : "text-emerald-700"}`}>${s.paperback_royalty}</td>
                        <td className="py-1 pr-2">{s.paperback_margin_pct}%</td>
                        <td className="py-1 pr-2">${s.ebook_royalty} ({s.ebook_rate})</td>
                        <td className="py-1"><StatusChip status={s.position} tone={posTone(s.position)} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </Panel>
  );
}

function PublicationDetailsPanel({ book, busy, doDraftBlurb, doSavePublication }) {
  const [blurb, setBlurb] = useState("");
  const [include, setInclude] = useState(true);
  useEffect(() => { if (book) { setBlurb(book.description || ""); setInclude(book.include_blurb !== false); } }, [book?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!book) return null;
  return (
    <Panel title="Back-Cover Blurb & Publication Details" icon={FileText} accent="royal" testid="publication-details">
      <p className="text-[11px] text-muted-foreground mb-3">The blurb prints on the back cover. Draft it with AI, then edit & approve — nothing is published without your review.</p>
      <div className="flex items-center gap-2 mb-2">
        <button data-testid="draft-blurb-btn" onClick={doDraftBlurb} disabled={busy}
          className="inline-flex items-center gap-1.5 bg-navy text-white px-3 py-1.5 rounded-md text-sm font-bold disabled:opacity-40">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <SpellCheck className="w-4 h-4" />} Draft with AI
        </button>
        {book.blurb_status && <StatusChip status={book.blurb_status} tone="amber" testid="blurb-status" />}
      </div>
      <textarea data-testid="blurb-textarea" value={blurb} onChange={(e) => setBlurb(e.target.value)} rows={5}
        placeholder="120–170 word back-cover blurb…" className="w-full px-3 py-2 text-sm border border-border rounded-md bg-card outline-none resize-y" />
      <label className="flex items-center gap-2 mt-2 text-sm text-navy">
        <input type="checkbox" checked={include} onChange={(e) => setInclude(e.target.checked)} data-testid="include-blurb-toggle" />
        Include blurb on back cover (uncheck for an intentionally minimal back cover)
      </label>
      <button data-testid="save-blurb-btn" onClick={() => doSavePublication({ description: blurb, include_blurb: include, blurb_status: "approved by Founder" }, "Blurb saved & approved.")} disabled={busy}
        className="mt-2 inline-flex items-center gap-1.5 bg-gold text-navy px-3 py-1.5 rounded-md text-sm font-bold disabled:opacity-40">
        <CheckCircle2 className="w-4 h-4" /> Save & Approve
      </button>
    </Panel>
  );
}

function PrintWrapPanel({ book, busy, doPrintWrap }) {
  const [paper, setPaper] = useState("white");
  const wrap = book?.artifacts?.design?.print?.paperback_cover_wrap;
  if (!book) return null;
  return (
    <Panel title="KDP Print-Ready Cover Wrap" icon={BookOpen} accent="royal" testid="print-wrap">
      <p className="text-[11px] text-muted-foreground mb-3">Complete paperback wrap — back cover + spine + front — sized from the final page count, trim, paper & bleed at 300 DPI. Run Sanitize + select a cover first.</p>
      <div className="flex flex-wrap items-center gap-2">
        <select value={paper} onChange={(e) => setPaper(e.target.value)} data-testid="wrap-paper-select"
          className="px-2 py-1.5 text-sm border border-border rounded-md bg-card outline-none">
          <option value="white">White paper (B&W)</option>
          <option value="cream">Cream paper (B&W)</option>
          <option value="color">Premium color</option>
        </select>
        <button data-testid="build-print-wrap-btn" onClick={() => doPrintWrap(paper)} disabled={busy}
          className="inline-flex items-center gap-1.5 bg-navy text-white px-3 py-1.5 rounded-md text-sm font-bold disabled:opacity-40">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />} Build Print-Ready Wrap
        </button>
      </div>
      {wrap && (
        <div className="mt-3 space-y-2" data-testid="wrap-result">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[12px]">
            <div><span className="text-muted-foreground">Pages:</span> <b>{wrap.page_count}</b></div>
            <div><span className="text-muted-foreground">Paper:</span> <b>{wrap.paper_type}</b></div>
            <div><span className="text-muted-foreground">Spine:</span> <b>{wrap.spine_in}"</b></div>
            <div><span className="text-muted-foreground">Trim:</span> <b>{wrap.trim}</b></div>
            <div><span className="text-muted-foreground">Full size:</span> <b>{wrap.full_size_in}</b></div>
            <div><span className="text-muted-foreground">DPI:</span> <b>{wrap.dpi}</b></div>
          </div>
          <StatusChip status={wrap.spine_note} tone={wrap.spine_text ? "emerald" : "amber"} testid="spine-note" />
          {wrap.paperback_cover_wrap_png && <img src={abs(wrap.paperback_cover_wrap_png)} alt="Cover wrap" className="w-full rounded-md border border-border/60" data-testid="wrap-preview" />}
          <div className="flex gap-2">
            <a href={abs(wrap.paperback_cover_wrap_pdf)} target="_blank" rel="noreferrer" data-testid="download-wrap-pdf"
              className="inline-flex items-center gap-1.5 bg-gold text-navy px-3 py-1.5 rounded-md text-sm font-bold">
              <Download className="w-4 h-4" /> Download Print PDF
            </a>
          </div>
          <p className="text-[10px] text-muted-foreground">{wrap.components}</p>
        </div>
      )}
    </Panel>
  );
}

const PP_TONE = { "Ready": "emerald", "Prototype": "amber", "Planned": "slate", "Not Implemented": "red" };

function PostPublishPanel({ postPub, book }) {
  const [showManifest, setShowManifest] = useState(false);
  if (!book) return null;
  if (!postPub || postPub.not_run || !postPub.sections?.length) {
    return (
      <Panel title="Post-Publish Manufacturing™" icon={Sparkles} accent="royal" testid="post-publish">
        <p className="text-[12px] text-muted-foreground">Publishing isn't the end of manufacturing. When you <b>Authorize Release</b>, the Factory automatically manufactures every inherited publication asset — Marketplace, Marketing, Website, Media scripts, Distribution prep, and your Founder package. You won't need to trigger anything.</p>
      </Panel>
    );
  }
  const c = postPub.counts || {};
  return (
    <Panel title="Post-Publish Manufacturing™" icon={Sparkles} accent="royal" testid="post-publish">
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <StatusChip status={`${c.Ready || 0} Ready`} tone="emerald" testid="pp-ready" />
        {c.Planned ? <StatusChip status={`${c.Planned} Planned`} tone="slate" /> : null}
        {c["Not Implemented"] ? <StatusChip status={`${c["Not Implemented"]} Not Implemented`} tone="rose" /> : null}
        {postPub.assets_zip && (
          <a href={abs(postPub.assets_zip)} target="_blank" rel="noreferrer" data-testid="download-publication-assets"
            className="ml-auto inline-flex items-center gap-1.5 bg-gold text-navy px-3 py-1.5 rounded-md text-sm font-bold">
            <Download className="w-4 h-4" /> Download Publication Assets
          </a>
        )}
        <button onClick={() => setShowManifest(true)} data-testid="view-manifest-btn"
          className={`${postPub.assets_zip ? "" : "ml-auto "}inline-flex items-center gap-1.5 border border-royal/40 text-royal px-3 py-1.5 rounded-md text-sm font-bold hover:bg-royal/5`}>
          <FileCheck2 className="w-4 h-4" /> View Product Manifest™
        </button>
      </div>
      <ManifestDialog bookId={book.id} name={book.title} open={showManifest} onOpenChange={setShowManifest} />
      <div className="grid sm:grid-cols-2 gap-3" data-testid="pp-sections">
        {postPub.sections.map((s, i) => (
          <div key={i} className="rounded-lg border border-border/60 p-3 bg-card">
            <p className="text-[13px] font-bold text-navy mb-1.5">{s.name}</p>
            <div className="space-y-1">
              {s.items.map((it, j) => (
                <div key={j} className="flex items-center justify-between gap-2" data-testid={`pp-item-${i}-${j}`}>
                  <span className={`text-[12px] ${it.status === "Ready" ? "text-navy" : "text-muted-foreground"}`}>{it.name}</span>
                  <StatusChip status={it.status} tone={PP_TONE[it.status] || "slate"} />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <p className="text-[11px] text-muted-foreground italic mt-3">{postPub.honesty}</p>
    </Panel>
  );
}

function FounderReleaseReview({ book, data, busy, doAuthorize }) {
  const CHECKS = [
    { key: "manuscript", label: "I have reviewed the manuscript." },
    { key: "cover", label: "I have reviewed the cover." },
    { key: "blurb", label: "I have reviewed the blurb." },
    { key: "price", label: "I approve the price." },
    { key: "public", label: "I understand publication creates a public edition." },
  ];
  const [checked, setChecked] = useState({});
  if (!book) return null;
  const authorized = book?.founder_authorization?.authorized;
  const allChecked = CHECKS.every((c) => checked[c.key]);
  const gateReady = data?.gate_ready_for_authorization ?? data?.gate_ready;
  const canAuthorize = gateReady && allChecked && !busy;
  const price = book?.pricing?.ebook_price && book?.pricing?.paperback_price
    ? `eBook ${book.pricing.currency} ${book.pricing.ebook_price} · Paperback ${book.pricing.currency} ${book.pricing.paperback_price}`
    : (book?.pricing?.list_price ? `${book.pricing.currency} ${book.pricing.list_price}` : "Not set");

  return (
    <div className="p-6 rounded-lg border-2 border-gold/50 bg-navy text-white shadow-xl" data-testid="founder-release-review">
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="w-5 h-5 text-gold" />
        <h3 className="font-heading text-lg font-bold text-gold">Founder Release Review™</h3>
      </div>
      <div className="grid sm:grid-cols-2 gap-x-8 gap-y-1.5 mb-5 text-sm">
        <p><span className="text-gold/80">Title:</span> <b className="text-white" data-testid="review-title">{book.title}</b></p>
        <p><span className="text-gold/80">Author:</span> <b className="text-white" data-testid="review-author">{book.author || "—"}</b></p>
        <p><span className="text-gold/80">Edition:</span> <b className="text-white">{book.edition || "First Edition"}</b></p>
        <p><span className="text-gold/80">Price:</span> <b className="text-white" data-testid="review-price">{price}</b></p>
        <p className="sm:col-span-2"><span className="text-gold/80">Status:</span> <b className="text-emerald-300" data-testid="review-status">{authorized ? "Authorized — Ready for KDP Submission" : (gateReady ? "Ready for KDP Submission" : "Preparing…")}</b></p>
      </div>

      <p className="text-[13px] text-white/90 mb-3">You are about to publish the first QRU Press™ title. Please confirm that:</p>
      <div className="space-y-2.5 mb-5" data-testid="review-checkboxes">
        {CHECKS.map((c) => (
          <label key={c.key} className="flex items-center gap-3 text-sm text-white cursor-pointer select-none">
            <input type="checkbox" data-testid={`review-check-${c.key}`} checked={!!checked[c.key]} disabled={authorized}
              onChange={(e) => setChecked((p) => ({ ...p, [c.key]: e.target.checked }))}
              className="w-4 h-4 accent-gold shrink-0" />
            <span>{c.label}</span>
          </label>
        ))}
      </div>

      {authorized ? (
        <div className="flex items-center gap-2 text-emerald-300 font-bold text-sm" data-testid="release-authorized-chip">
          <CheckCircle2 className="w-5 h-5" /> Release authorized by {book.founder_authorization.by} · {new Date(book.founder_authorization.at).toLocaleString()}
        </div>
      ) : (
        <>
          <button data-testid="authorize-btn" onClick={doAuthorize} disabled={!canAuthorize}
            className="w-full inline-flex items-center justify-center gap-2 bg-gold text-navy px-4 py-3.5 rounded-md text-base font-bold transition-opacity disabled:opacity-40 hover:opacity-90">
            <ShieldCheck className="w-5 h-5" /> Authorize Release
          </button>
          {!gateReady && <p className="text-[11px] text-amber-300 mt-2 text-center">The Final Release Gate is not yet complete — resolve pending items above first.</p>}
          {gateReady && !allChecked && <p className="text-[11px] text-white/60 mt-2 text-center">Confirm all five statements to enable authorization.</p>}
        </>
      )}
    </div>
  );
}

function PublishPanel({ data, kdp, postPub, book, busy, doPricing, doAuthorize, doSanitize, doDraftBlurb, doSavePublication, doPrintWrap }) {
  const [price, setPrice] = useState(book?.pricing?.paperback_price || book?.pricing?.list_price || "");
  if (!data) return <Panel title="Publish" icon={Send}><p className="text-sm text-muted-foreground py-4">Loading…</p></Panel>;
  const g = data.final_release_gate;
  return (
    <div className="space-y-5" data-testid="panel-publish">
      <SanitizationPanel book={book} busy={busy} doSanitize={doSanitize} />
      <PricingAdvisorPanel book={book} busy={busy} doPricing={doPricing} />
      <PublicationDetailsPanel book={book} busy={busy} doDraftBlurb={doDraftBlurb} doSavePublication={doSavePublication} />
      <PrintWrapPanel book={book} busy={busy} doPrintWrap={doPrintWrap} />
      <KdpChecklist kdp={kdp} />
      <div className="grid lg:grid-cols-2 gap-5">
      <Panel title="Publication Control Center" icon={Send} accent="royal" testid="publish-destinations">
        <div className="space-y-2" data-testid="destinations-list">
          {data.destinations.map((d, i) => (
            <div key={i} className="flex items-center justify-between gap-2 border-b border-border/50 pb-1.5">
              <div><p className="text-sm font-medium text-navy">{d.destination}</p>
                <p className="text-[10px] text-muted-foreground">{d.integration}</p></div>
              <StatusChip status={d.state} tone={STATE_TONE(d.state)} />
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Final Release Gate" icon={ShieldCheck} accent="gold" testid="release-gate">
        <div className="space-y-1.5" data-testid="gate-items">
          {Object.entries(g).map(([k, v]) => (
            <div key={k} className="flex items-center justify-between gap-2 text-sm">
              <span className="text-navy capitalize">{k.replace(/_/g, " ").replace(/\btitle author\b/i, "Title & Author").replace(/\bai\b/gi, "AI")}</span>
              {v ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <StatusChip status="Pending" tone="amber" />}
            </div>
          ))}
        </div>

        {/* Pricing input — always editable (the founder's pencil); pre-filled with the current/estimated price */}
        <div className="mt-3 flex items-center gap-2" data-testid="pricing-input">
          <DollarSign className="w-4 h-4 text-muted-foreground" />
          <input type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)}
            placeholder="List price (USD)" className="flex-1 px-2 py-1.5 text-sm border border-border rounded-md bg-card outline-none" />
          <button data-testid="approve-pricing-btn" onClick={() => doPricing(price, "USD")} disabled={busy || !price}
            className="bg-navy text-white px-3 py-1.5 rounded-md text-sm font-bold disabled:opacity-40">
            {book?.pricing?.approved ? "Update Price" : "Approve Price"}
          </button>
        </div>
        {book?.pricing?.approved && (
          <p className="text-[12px] text-emerald-700 mt-2" data-testid="pricing-approved-text">
            Pricing approved: {book.pricing.ebook_price && book.pricing.paperback_price
              ? `eBook ${book.pricing.currency} ${book.pricing.ebook_price} · Paperback ${book.pricing.currency} ${book.pricing.paperback_price}`
              : `${book.pricing.currency} ${book.pricing.list_price}`} — edit above to change it.
          </p>
        )}

        <div className="mt-4">
          {book?.founder_authorization?.authorized
            ? <StatusChip status={`Authorized by ${book.founder_authorization.by}`} tone="emerald" testid="authorized-chip" />
            : <StatusChip status={(data.gate_ready_for_authorization ?? data.gate_ready) ? "Gate ready — complete the Founder Release Review™ below to authorize" : "Gate not yet ready"} tone={(data.gate_ready_for_authorization ?? data.gate_ready) ? "emerald" : "amber"} testid="gate-ready" />}
        </div>
        <p className="text-[11px] text-amber-700 mt-2">{data.honesty}</p>
      </Panel>
      </div>

      <FounderReleaseReview book={book} data={data} busy={busy} doAuthorize={doAuthorize} />
      <PostPublishPanel postPub={postPub} book={book} />
    </div>
  );
}
