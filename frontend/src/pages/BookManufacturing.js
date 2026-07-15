import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, MetricCard } from "@/components/qru";
import {
  Upload, SpellCheck, Palette, Mic, Video, Send, Activity, Loader2, CheckCircle2,
  Lock, FileText, ShieldCheck, ChevronRight, BookOpen, AlertTriangle, Download, MapPin, Share2, Play, DollarSign, ClipboardCheck,
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
  const [monitor, setMonitor] = useState(null);
  const [shareInfo, setShareInfo] = useState(null);
  const [allBooks, setAllBooks] = useState([]);
  const [systemTitle, setSystemTitle] = useState("QRU Product Manufacturing System™");

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
  const selectBook = async (id) => { setTab("upload"); setShareInfo(null); await reload(id); };
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
    if (tab === "publish") { api.get(`/book-mfg/books/${book.id}/publish`).then((r) => setPublish(r.data)); api.get(`/book-mfg/books/${book.id}/kdp-checklist`).then((r) => setKdp(r.data)).catch(() => {}); }
    if (tab === "monitor" && !monitor) api.get(`/book-mfg/books/${book.id}/monitor`).then((r) => setMonitor(r.data));
  }, [tab, book]); // eslint-disable-line

  const run = async (fn, ok) => {
    setBusy(true);
    try { await fn(); if (ok) toast.success(ok); await reload(book.id); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const doProof = () => run(async () => { const { data } = await api.post(`/book-mfg/books/${book.id}/proof`); setProof(data.report); }, "Proof & Polish complete.");
  const doApprove = () => run(() => api.post(`/book-mfg/books/${book.id}/approve-edition`), "Editorial edition locked.");
  const doDesign = () => run(() => api.post(`/book-mfg/books/${book.id}/design`, { base_url: A }), "Design drafted.");
  const doSelectCover = (concept) => run(() => api.post(`/book-mfg/books/${book.id}/select-cover`, { concept, base_url: A }), `Cover ${concept} selected — clean retail edition prepared.`).then(() => reload(book.id));
  const doAssemble = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/book-mfg/books/${book.id}/assemble-package`);
      toast.success(`Master Output Package assembled (${data.size_kb} KB). Saved to your Factory Library™ below.`);
      await reload(book.id);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };
  const doRenderAudio = () => run(async () => { await api.post(`/book-mfg/books/${book.id}/audio-prototype`); const { data } = await api.get(`/book-mfg/books/${book.id}/audio`); setAudio(data); }, "Narration prototype rendered.");
  const doPricing = (price, currency) => run(() => api.post(`/book-mfg/books/${book.id}/pricing`, { list_price: parseFloat(price), currency }), "Pricing approved.").then(() => api.get(`/book-mfg/books/${book.id}/publish`).then((r) => setPublish(r.data)));
  const doAuthorize = () => run(() => api.post(`/book-mfg/books/${book.id}/authorize`), "Release authorized.").then(() => api.get(`/book-mfg/books/${book.id}/publish`).then((r) => setPublish(r.data)));
  const doSanitize = () => run(() => api.post(`/book-mfg/books/${book.id}/sanitize`, { base_url: A }), "Publication Sanitization Pass™ complete — clean retail edition prepared.").then(() => api.get(`/book-mfg/books/${book.id}/publish`).then((r) => setPublish(r.data)));
  const doDraftBlurb = () => run(async () => { const { data } = await api.post(`/book-mfg/books/${book.id}/draft-blurb`); toast.message("Blurb drafted — review & approve.", { description: data.status }); });
  const doSavePublication = (fields, ok) => run(() => api.post(`/book-mfg/books/${book.id}/publication-details`, fields), ok || "Publication details saved.");
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

      {/* Book identity — title ALWAYS before Book Record ID */}
      <div className="qru-card qru-goldline p-4 mb-5" data-testid="book-identity">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="min-w-0">
            <h2 className="font-heading text-xl font-bold text-navy" data-testid="book-title">{book.title}{book.subtitle ? ` — ${book.subtitle}` : ""}</h2>
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

      {/* Share link box — always copyable (never a one-shot clipboard write) */}
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
      {tab === "proof" && <ProofPanel book={book} proof={proof} busy={busy} doProof={doProof} doApprove={doApprove} />}
      {tab === "design" && <DesignPanel book={book} busy={busy} doDesign={doDesign} doSelectCover={doSelectCover} />}
      {tab === "audio" && <AudioPanel book={book} audio={audio} busy={busy} onRender={doRenderAudio} />}
      {tab === "video" && <PlanPanel title="Video" icon={Video} data={video} render={renderVideo} />}
      {tab === "publish" && <PublishPanel data={publish} kdp={kdp} book={book} busy={busy} doPricing={doPricing} doAuthorize={doAuthorize} doSanitize={doSanitize} doDraftBlurb={doDraftBlurb} doSavePublication={doSavePublication} doPrintWrap={doPrintWrap} />}
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
          <p className="text-[10px] font-bold text-royal uppercase tracking-wide mb-1">Master Output Packages</p>
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

function ProofPanel({ book, proof, busy, doProof, doApprove }) {
  return (
    <div data-testid="panel-proof">
      <Panel title="Proof & Polish" icon={SpellCheck} accent="royal"
        right={
          <div className="flex gap-2">
            <button data-testid="run-proof-btn" onClick={doProof} disabled={busy}
              className="inline-flex items-center gap-1.5 bg-navy text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-60">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <SpellCheck className="w-4 h-4" />} Run Proof
            </button>
            <button data-testid="approve-edition-btn" onClick={doApprove} disabled={busy || !proof || book.editorial_locked}
              className="inline-flex items-center gap-1.5 bg-gold text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40">
              <Lock className="w-4 h-4" /> {book.editorial_locked ? "Edition Locked" : "Approve & Lock"}
            </button>
          </div>
        }>
        {!proof ? (
          <p className="text-sm text-muted-foreground py-4">Run Proof & Polish to generate a proofing report. The Factory reports findings — it never silently rewrites the author's voice.</p>
        ) : (
          <div>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 mb-4" data-testid="proof-counts">
              {[["Words", proof.counts.words], ["Chapters", proof.counts.chapters], ["Required", proof.counts.required],
                ["Recommended", proof.counts.recommended], ["Decisions", proof.counts.founder_decision]].map(([k, v]) => (
                <div key={k} className="border border-border rounded-md px-2 py-1.5 text-center">
                  <p className="text-lg font-bold text-navy">{v}</p><p className="text-[10px] text-muted-foreground">{k}</p>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-muted-foreground italic mb-2">{proof.voice_note}</p>
            <div className="space-y-2" data-testid="proof-findings">
              {proof.findings.length === 0 ? <p className="text-sm text-emerald-700">No issues found. Clean manuscript.</p> :
                proof.findings.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 border-b border-border/50 pb-2">
                    <StatusChip status={f.type} tone={FINDING_TONE[f.type]} />
                    <div><p className="text-sm font-medium text-navy">{f.issue}</p>
                      <p className="text-[12px] text-muted-foreground">{f.detail}</p></div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </Panel>
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

function AudioPanel({ book, audio, busy, onRender }) {
  const proto = book.artifacts?.audio?.prototype || audio?.prototype;
  const timing = book.artifacts?.audio || {};
  return (
    <div data-testid="panel-audio">
      <Panel title="Audio" icon={Mic} accent="royal"
        right={
          <button data-testid="render-audio-btn" onClick={onRender} disabled={busy}
            className="inline-flex items-center gap-1.5 bg-navy text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-60">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Render Narration Prototype
          </button>
        }>
        {proto ? (
          <div className="mb-4 border border-gold/40 bg-gold/[0.06] rounded-md p-3" data-testid="audio-prototype">
            <p className="text-[12px] text-amber-800 font-semibold mb-2">{proto.label}</p>
            <audio controls src={abs(proto.url)} className="w-full" data-testid="audio-player" />
            <p className="text-[11px] text-muted-foreground mt-1">Voice: {proto.voice} · {proto.duration_sec}s · Full-book estimate ~{timing.full_book_estimate_min} min</p>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground mb-4">Render a real AI narration prototype of Chapter 1's opening for pacing review. It is honestly labeled — not for commercial distribution.</p>
        )}
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
  useEffect(() => { if (book) { setBlurb(book.description || ""); setInclude(book.include_blurb !== false); } }, [book?.id, book?.description, book?.include_blurb]);
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

function PublishPanel({ data, kdp, book, busy, doPricing, doAuthorize, doSanitize, doDraftBlurb, doSavePublication, doPrintWrap }) {
  const [price, setPrice] = useState("");
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
              <span className="text-navy capitalize">{k.replace(/_/g, " ").replace(/\bai\b/gi, "AI")}</span>
              {v ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <StatusChip status="Pending" tone="amber" />}
            </div>
          ))}
        </div>

        {/* Pricing input */}
        {!g.pricing_approved && (
          <div className="mt-3 flex items-center gap-2" data-testid="pricing-input">
            <DollarSign className="w-4 h-4 text-muted-foreground" />
            <input type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)}
              placeholder="List price (USD)" className="flex-1 px-2 py-1.5 text-sm border border-border rounded-md bg-card outline-none" />
            <button data-testid="approve-pricing-btn" onClick={() => doPricing(price, "USD")} disabled={busy || !price}
              className="bg-navy text-white px-3 py-1.5 rounded-md text-sm font-bold disabled:opacity-40">Approve Price</button>
          </div>
        )}
        {book?.pricing?.approved && <p className="text-[12px] text-emerald-700 mt-2">Pricing approved: {book.pricing.currency} {book.pricing.list_price}</p>}

        {/* Founder authorization — human final judgment for irreversible action */}
        <div className="mt-4">
          {book?.founder_authorization?.authorized ? (
            <StatusChip status={`Authorized by ${book.founder_authorization.by}`} tone="emerald" testid="authorized-chip" />
          ) : (
            <button data-testid="authorize-btn" onClick={doAuthorize} disabled={busy}
              className="w-full inline-flex items-center justify-center gap-1.5 bg-gold text-navy px-4 py-2.5 rounded-md text-sm font-bold disabled:opacity-50">
              <ShieldCheck className="w-4 h-4" /> Authorize Release (Founder)
            </button>
          )}
        </div>
        <div className="mt-3">
          <StatusChip status={data.gate_ready ? "Gate ready for Founder authorization" : "Gate not yet ready"} tone={data.gate_ready ? "emerald" : "amber"} testid="gate-ready" />
        </div>
        <p className="text-[11px] text-amber-700 mt-2">{data.honesty}</p>
      </Panel>
      </div>
    </div>
  );
}
