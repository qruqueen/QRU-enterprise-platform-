import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, Play, ShieldCheck, RotateCcw, CheckCircle2, AlertTriangle, RefreshCw,
  BookOpen, GraduationCap, Database, FileText, PauseOctagon, Search, ArrowLeftRight, FilePlus, Layers, ClipboardCheck, Trash2, Image as ImageIcon,
} from "lucide-react";

const OUTCOME = {
  CREATED: "bg-emerald-100 text-emerald-700",
  UPDATED: "bg-emerald-100 text-emerald-700",
  HELD: "bg-emerald-100 text-emerald-700",
  ADOPTED_AND_REPOINTED: "bg-emerald-100 text-emerald-700",
  CREATED_UNDER_NEW_CODE: "bg-emerald-100 text-emerald-700",
  RESTORED: "bg-blue-100 text-blue-700",
  REMOVED: "bg-blue-100 text-blue-700",
  WOULD_CREATE: "bg-amber-100 text-amber-700",
  WOULD_UPDATE: "bg-amber-100 text-amber-700",
  WOULD_HOLD: "bg-amber-100 text-amber-700",
  WOULD_RESTORE: "bg-amber-100 text-amber-700",
  WOULD_ADOPT_AND_REPOINT: "bg-amber-100 text-amber-700",
  WOULD_CREATE_UNDER_NEW_CODE: "bg-amber-100 text-amber-700",
  WOULD_REMOVE: "bg-amber-100 text-amber-700",
  SKIP: "bg-muted text-muted-foreground",
  CONFLICT: "bg-orange-100 text-orange-700",
  BLOCKED: "bg-red-100 text-red-700",
  PRESENT_BY_ID: "bg-emerald-100 text-emerald-700",
  SAME_BOOK: "bg-emerald-100 text-emerald-700",
  TITLE_CHANGED: "bg-blue-100 text-blue-700",
  NEW_EDITION: "bg-blue-100 text-blue-700",
  DIFFERENT_WORK: "bg-red-100 text-red-700",
  POSSIBLE_COLLISION: "bg-orange-100 text-orange-700",
  ID_MISMATCH_SAME_BOOK: "bg-blue-100 text-blue-700",
  ID_MISMATCH_TITLE_MATCH_AUTHOR_DIFF: "bg-orange-100 text-orange-700",
  CODE_COLLISION_DIFFERENT_CONTENT: "bg-red-100 text-red-700",
  ABSENT: "bg-muted text-muted-foreground",
  PRODUCTION_HOLD_REQUIRED: "bg-red-100 text-red-700",
  NOT_PRESENT_IN_PRODUCTION: "bg-muted text-muted-foreground",
  NOT_LEARNER_ACCESSIBLE: "bg-muted text-muted-foreground",
  FOUNDER_REVIEW_REQUIRED: "bg-amber-100 text-amber-700",
  TEST_VISIBLE_IN_CATALOG: "bg-red-100 text-red-700",
  TEST_NOT_PUBLISHED: "bg-amber-100 text-amber-700",
  TEST_ALREADY_ARCHIVED: "bg-muted text-muted-foreground",
  TEST_HAS_PAID_ORDER: "bg-orange-100 text-orange-700",
  OK: "bg-muted text-muted-foreground",
  MERGED: "bg-emerald-100 text-emerald-700",
  WOULD_MERGE: "bg-amber-100 text-amber-700",
  RESTORED_FROM_TRASH: "bg-blue-100 text-blue-700",
  WOULD_RESTORE_FROM_TRASH: "bg-amber-100 text-amber-700",
  REPAIRED: "bg-emerald-100 text-emerald-700",
  WOULD_REPAIR: "bg-amber-100 text-amber-700",
  SKIPPED_NO_REPLACEMENT: "bg-red-100 text-red-700",
};

function Badge({ v }) {
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ${OUTCOME[v] || "bg-muted text-muted-foreground"}`}>{String(v).replace(/_/g, " ")}</span>;
}

function Stat({ label, value, tone = "default" }) {
  const tones = {
    default: "bg-card", ok: "bg-emerald-50 text-emerald-700", warn: "bg-amber-50 text-amber-700", bad: "bg-red-50 text-red-700",
  };
  return (
    <div className={`rounded-lg border p-4 ${tones[tone]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-[11px] mt-1 opacity-80">{label}</div>
    </div>
  );
}

function EvidenceRows({ rows }) {
  if (!rows?.length) return null;
  return (
    <div className="mt-4 overflow-x-auto rounded-lg border" data-testid="evidence-rows">
      <table className="w-full text-xs">
        <thead><tr className="text-left text-muted-foreground border-b bg-muted/40">
          <th className="py-2 px-3">Record</th><th className="py-2 px-3">Outcome</th><th className="py-2 px-3">Detail</th>
        </tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b last:border-0" data-testid={`evidence-row-${r.code}`}>
              <td className="py-2 px-3 font-medium text-foreground whitespace-nowrap">{r.code}</td>
              <td className="py-2 px-3"><Badge v={r.outcome || r.classification} /></td>
              <td className="py-2 px-3 text-muted-foreground">{r.detail || r.title || `${r.pub_status || ""} · KR: ${r.kr_status || ""}`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ProductionOperations() {
  const [summary, setSummary] = useState(null);
  const [busy, setBusy] = useState("");
  const [reportA, setReportA] = useState(null);
  const [reportC, setReportC] = useState(null);
  const [inspect, setInspect] = useState(null);
  const [stdPre, setStdPre] = useState(null);
  const [reportD, setReportD] = useState(null);
  const [testPre, setTestPre] = useState(null);
  const [reportE, setReportE] = useState(null);
  const [assetPre, setAssetPre] = useState(null);
  const [assetJob, setAssetJob] = useState(null);
  const [imprintPre, setImprintPre] = useState(null);
  const [reportG, setReportG] = useState(null);
  const [coverPre, setCoverPre] = useState(null);
  const [reportCover, setReportCover] = useState(null);

  const loadSummary = () => api.get("/admin/migrations/summary").then((r) => setSummary(r.data)).catch(() => setSummary(false));
  useEffect(() => { loadSummary(); }, []);

  const runA = async (mode) => {
    if (mode === "apply" && !window.confirm("Apply Workstream A to THIS environment's database? Creates the 4 missing books and updates the 8 EPUB pointers. Idempotent and rollback-protected.")) return;
    setBusy(`A-${mode}`);
    try {
      let data;
      if (mode === "rollback") ({ data } = await api.post("/admin/migrations/book-cutover/rollback", { apply: true }));
      else ({ data } = await api.post("/admin/migrations/book-cutover", { stage: "all", apply: mode === "apply" }));
      setReportA(data);
      toast.success(mode === "dry" ? "Dry run complete — no changes written." : mode === "apply" ? "Workstream A applied." : "Rollback complete.");
      loadSummary();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Workstream A action failed.");
    }
    setBusy("");
  };

  const runInspect = async () => {
    setBusy("A-inspect");
    try {
      const { data } = await api.get("/admin/migrations/book-cutover/inspect");
      setInspect(data);
      toast.success("Inspection complete (read-only).");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Inspection failed.");
    }
    setBusy("");
  };

  const runResolve = async (mode) => {
    if (mode === "apply" && !window.confirm("Adopt the existing production records that are confirmed to be the SAME book (same title & author) and repoint their EPUB to the re-rendered edition? No duplicates are created; collisions are left untouched. Rollback-protected.")) return;
    setBusy(`A-resolve-${mode}`);
    try {
      const { data } = await api.post("/admin/migrations/book-cutover/resolve-conflicts", { apply: mode === "apply" });
      setReportA(data);
      toast.success(mode === "apply" ? "Conflicts resolved (adopt & repoint)." : "Resolution dry run complete.");
      loadSummary();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Resolution failed.");
    }
    setBusy("");
  };

  const runCreateFresh = async (mode) => {
    if (mode === "apply" && !window.confirm("Create the DIFFERENT_WORK migration book(s) under a FRESH production book_code? These are distinct works whose code is already used in production; the existing production works are left completely untouched. Rollback available.")) return;
    setBusy(`A-fresh-${mode}`);
    try {
      let data;
      if (mode === "rollback") ({ data } = await api.post("/admin/migrations/book-cutover/create-fresh-code/rollback", { apply: true }));
      else ({ data } = await api.post("/admin/migrations/book-cutover/create-fresh-code", { apply: mode === "apply" }));
      setReportA(data);
      toast.success(mode === "dry" ? "Create-under-new-code dry run complete." : mode === "apply" ? "Created under a fresh code." : "New-code creations rolled back.");
      loadSummary();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Action failed.");
    }
    setBusy("");
  };

  const runStdPreflight = async () => {
    setBusy("D-preflight");
    try {
      const { data } = await api.get("/admin/migrations/standards-metadata/preflight");
      setStdPre(data);
      toast.success("Production preflight complete.");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Preflight failed.");
    }
    setBusy("");
  };

  const runStdApply = async (mode) => {
    if (mode === "apply" && !window.confirm("Apply the approved additive standards metadata to THIS environment (lifecycle=ADOPTED ×39, 11 evidence-backed enforcement, 28 FOUNDER_DECISION_REQUIRED, + projection tags on the 5)? Additive-only, rollback-protected. Proceeds only when 39 canonical + 5 projections exist and no material conflict is found.")) return;
    setBusy(`D-${mode}`);
    try {
      const { data } = await api.post("/admin/migrations/standards-metadata/apply", { apply: mode === "apply" });
      setReportD(data);
      if (data.mode === "BLOCKED" || data.mode === "HALTED") toast.error(`Blocked: ${(data.block_reasons || [data.reason]).join(", ")}`);
      else toast.success(mode === "apply" ? "Standards metadata applied." : "Apply dry run complete.");
      loadSummary();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Apply failed.");
    }
    setBusy("");
  };

  const runStdRollback = async () => {
    if (!window.confirm("Roll back DQ-7C standards metadata in THIS environment (unset the added fields)? Existing standards content is untouched.")) return;
    setBusy("D-rollback");
    try {
      const { data } = await api.post("/admin/migrations/standards-metadata/rollback", { apply: true });
      setReportD(data);
      toast.success("Standards metadata rolled back.");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Rollback failed.");
    }
    setBusy("");
  };

  const runC = async (mode) => {
    if (mode === "hold" && !window.confirm("Place the qualifying lessons On Hold (Governance) in THIS environment? They leave the learner catalog immediately. Assets and purchases are preserved. One-tap rollback available.")) return;
    setBusy(`C-${mode}`);
    try {
      let data;
      if (mode === "rollback") ({ data } = await api.post("/admin/migrations/learn-containment/rollback", { apply: true }));
      else ({ data } = await api.post("/admin/migrations/learn-containment", { apply_hold: mode === "hold", apply: mode === "hold" }));
      setReportC(data);
      toast.success(mode === "classify" ? "Classification complete (read-only)." : mode === "hold" ? "Governance hold applied." : "Hold rolled back.");
      loadSummary();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Workstream C action failed.");
    }
    setBusy("");
  };

  const loadAssetStatus = () => api.get("/admin/migrations/assets-upgrade/status").then((r) => setAssetJob(r.data)).catch(() => {});

  useEffect(() => {
    if (assetJob?.status !== "running") return;
    const t = setInterval(loadAssetStatus, 3000);
    return () => clearInterval(t);
  }, [assetJob?.status]);

  const runAssetPreflight = async () => {
    setBusy("F-preflight");
    try {
      const { data } = await api.get("/admin/migrations/assets-upgrade/preflight");
      setAssetPre(data);
      await loadAssetStatus();
      toast.success("Asset scan complete (read-only).");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Scan failed.");
    }
    setBusy("");
  };

  const runAssetUpgrade = async (force) => {
    if (!window.confirm(force ? "Re-render EVERY catalog product cover through the hardened deterministic renderer? Zero AI spend. Founder-selected Asset Vault covers are always preserved." : "Re-render catalog product covers that have not yet been upgraded, through the hardened deterministic renderer? Zero AI spend. Resumable and safe to re-run.")) return;
    setBusy("F-run");
    try {
      const { data } = await api.post("/admin/migrations/assets-upgrade", { force });
      toast.success(data.status === "running" ? "A batch is already running." : "Batch Upgrade Assets started (zero AI spend).");
      await loadAssetStatus();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to start batch.");
    }
    setBusy("");
  };

  const runTestPreflight = async () => {
    setBusy("E-preflight");
    try {
      const { data } = await api.get("/admin/migrations/test-products/preflight");
      setTestPre(data);
      toast.success("Test-product scan complete (read-only).");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Scan failed.");
    }
    setBusy("");
  };

  const runTestCleanup = async (mode) => {
    if (mode === "apply" && !window.confirm("Archive (unpublish) all detected internal test/placeholder products in THIS environment? They leave the learner catalog immediately. Products tied to a paid order are always skipped. Assets are preserved and this is fully reversible via Rollback.")) return;
    setBusy(`E-${mode}`);
    try {
      let data;
      if (mode === "rollback") ({ data } = await api.post("/admin/migrations/test-products/cleanup/rollback", { apply: true }));
      else ({ data } = await api.post("/admin/migrations/test-products/cleanup", { apply: mode === "apply" }));
      setReportE(data);
      toast.success(mode === "dry" ? "Dry run complete — no changes written." : mode === "apply" ? "Test products archived." : "Rollback complete — products restored.");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Cleanup action failed.");
    }
    setBusy("");
  };

  const runImprintPreflight = async () => {
    setBusy("G-preflight");
    try {
      const { data } = await api.get("/admin/migrations/imprint-canonicalization/preflight");
      setImprintPre(data);
      toast.success("Imprint audit complete (read-only).");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Audit failed.");
    }
    setBusy("");
  };

  const runImprint = async (mode) => {
    if (mode === "apply" && !window.confirm("Apply imprint canonicalization to THIS environment? Assigns every book to its canonical imprint (E.Q. Rothwell™ literary / QRU Press™ educational), records the permanent canonical_imprint + genre, normalizes literary authorship, and merges the 'Ordinary Tuesdays FULL MANUSCRIPT' duplicate into the canonical record. Additive + fully reversible via Rollback. Covers are NOT re-rendered (no AI spend).")) return;
    setBusy(`G-${mode}`);
    try {
      let data;
      if (mode === "rollback") ({ data } = await api.post("/admin/migrations/imprint-canonicalization/rollback", { apply: true }));
      else ({ data } = await api.post("/admin/migrations/imprint-canonicalization", { apply: mode === "apply" }));
      setReportG(data);
      toast.success(mode === "dry" ? "Dry run complete — no changes written." : mode === "apply" ? "Imprints canonicalized." : "Rollback complete — imprints restored.");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Imprint action failed.");
    }
    setBusy("");
  };

  const runCoverPreflight = async () => {
    setBusy("COV-preflight");
    try {
      const { data } = await api.get("/admin/migrations/cover-repair/preflight");
      setCoverPre(data);
      toast.success("Cover audit complete (read-only).");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Cover audit failed.");
    }
    setBusy("");
  };

  const runCoverRepair = async (mode) => {
    if (mode === "apply" && !window.confirm("Repair broken cover references in THIS environment? For every book whose ACTIVE cover is missing from durable storage, the active cover is repointed to the first Founder-generated concept that IS retrievable. No AI spend, no re-render. Fully reversible via Rollback.")) return;
    setBusy(`COV-${mode}`);
    try {
      let data;
      if (mode === "rollback") ({ data } = await api.post("/admin/migrations/cover-repair/rollback", { apply: true }));
      else ({ data } = await api.post("/admin/migrations/cover-repair", { apply: mode === "apply" }));
      setReportCover(data);
      toast.success(mode === "dry" ? "Dry run complete — no changes written." : mode === "apply" ? "Cover references repaired." : "Rollback complete — original covers restored.");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Cover repair failed.");
    }
    setBusy("");
  };

  if (summary === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>;
  const a = summary?.workstream_a || {};
  const c = summary?.workstream_c || {};
  const rowsA = reportA?.stages?.flatMap((s) => s.rows) || reportA?.rows || [];
  const rowsC = reportC?.hold_actions || reportC?.rows || reportC?.classification || [];
  const rowsE = reportE?.actions || reportE?.rows || testPre?.classification || [];
  const rowsG = reportG?.actions || reportG?.rows || [];
  const rowsCover = reportCover?.rows || [];

  return (
    <div className="space-y-6" data-testid="production-operations">
      <PageHeader
        overline="FOUNDER OPERATIONS · PRODUCTION"
        title="Production Operations™"
        subtitle="Governed, idempotent data operations run against whichever database this environment is connected to — production when live. Dry-run first, review the evidence, then apply. Every action is rollback-protected."
      />

      <div className="rounded-xl border-2 border-navy/15 bg-gold/10 p-4 text-sm flex gap-3" data-testid="prod-ops-notice">
        <ShieldCheck className="w-5 h-5 text-navy mt-0.5 shrink-0" />
        <div className="text-navy/90">
          <span className="font-semibold">You are operating on: this environment's database.</span> On <span className="font-mono">qru-online.com</span> that is production. Nothing is written until you press an <span className="font-semibold">Apply</span> action and confirm. All migrations are idempotent — safe to re-run.
        </div>
      </div>

      {/* Migration Status overview */}
      {summary && (
        <div className="rounded-xl border bg-card p-5" data-testid="migration-status">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-4 h-4 text-royal" />
            <h3 className="font-heading font-bold text-navy">Migration Status</h3>
            <span className="ml-auto text-[11px] text-muted-foreground">refreshed {new Date(summary.at).toLocaleTimeString()}</span>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <Stat label="Books to create" value={a.books_to_create} tone={a.books_to_create ? "warn" : "ok"} />
            <Stat label="Pointers to update" value={a.pointers_to_update} tone={a.pointers_to_update ? "warn" : "ok"} />
            <Stat label="Assets verified" value={a.assets_verified ? "Yes" : "No"} tone={a.assets_verified ? "ok" : "bad"} />
            <Stat label="Lessons needing hold" value={c.hold_required} tone={c.hold_required ? "warn" : "ok"} />
            <Stat label="Blocked" value={a.blocked} tone={a.blocked ? "bad" : "ok"} />
          </div>
        </div>
      )}

      {/* Workstream A */}
      <section className="rounded-xl border bg-card p-5" data-testid="workstream-a">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-royal font-semibold">Workstream A · RI-MFG-0002b</div>
            <div className="flex items-center gap-2 mt-1"><BookOpen className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">Book Data & EPUB Cutover</span></div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">Creates the 4 missing book records and points all 8 books at their validated, re-rendered EPUBs. Verifies every asset exists in durable storage before touching a pointer; preserves the prior pointer for rollback. Never alters manuscripts, covers, pricing, authorization, or purchases.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={runInspect} disabled={!!busy} data-testid="a-inspect" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "A-inspect" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Inspect Records
          </button>
          <button onClick={() => runA("dry")} disabled={!!busy} data-testid="a-dry-run" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "A-dry" ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />} Run Dry Run
          </button>
          <button onClick={() => runA("apply")} disabled={!!busy} data-testid="a-apply" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {busy === "A-apply" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Apply Migration
          </button>
          <button onClick={() => runResolve("dry")} disabled={!!busy} data-testid="a-resolve-dry" className="inline-flex items-center gap-2 rounded-lg border border-blue-300 text-blue-700 px-4 py-2 text-sm font-medium hover:bg-blue-50 disabled:opacity-50">
            {busy === "A-resolve-dry" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowLeftRight className="w-4 h-4" />} Resolve Conflicts (preview)
          </button>
          <button onClick={() => runResolve("apply")} disabled={!!busy} data-testid="a-resolve-apply" className="inline-flex items-center gap-2 rounded-lg bg-blue-700 text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {busy === "A-resolve-apply" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowLeftRight className="w-4 h-4" />} Apply Resolution
          </button>
          <button onClick={() => runA("rollback")} disabled={!!busy} data-testid="a-rollback" className="inline-flex items-center gap-2 rounded-lg border border-red-200 text-red-700 px-4 py-2 text-sm font-medium hover:bg-red-50 disabled:opacity-50">
            {busy === "A-rollback" ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} Rollback
          </button>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-2 rounded-lg bg-muted/30 border border-dashed p-2.5" data-testid="a-different-work-controls">
          <span className="text-[11px] text-muted-foreground font-medium px-1">Different works sharing a code (DIFFERENT_WORK):</span>
          <button onClick={() => runCreateFresh("dry")} disabled={!!busy} data-testid="a-fresh-dry" className="inline-flex items-center gap-2 rounded-lg border border-amber-300 text-amber-700 px-3 py-1.5 text-xs font-medium hover:bg-amber-50 disabled:opacity-50">
            {busy === "A-fresh-dry" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FilePlus className="w-3.5 h-3.5" />} Create Under New Code (preview)
          </button>
          <button onClick={() => runCreateFresh("apply")} disabled={!!busy} data-testid="a-fresh-apply" className="inline-flex items-center gap-2 rounded-lg bg-amber-600 text-white px-3 py-1.5 text-xs font-medium hover:opacity-90 disabled:opacity-50">
            {busy === "A-fresh-apply" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FilePlus className="w-3.5 h-3.5" />} Apply New Code
          </button>
          <button onClick={() => runCreateFresh("rollback")} disabled={!!busy} data-testid="a-fresh-rollback" className="inline-flex items-center gap-2 rounded-lg border border-red-200 text-red-700 px-3 py-1.5 text-xs font-medium hover:bg-red-50 disabled:opacity-50">
            {busy === "A-fresh-rollback" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />} Undo
          </button>
        </div>

        {inspect && (
          <div className="mt-4 space-y-3" data-testid="inspect-a">
            <div className="text-xs text-muted-foreground flex items-center gap-1.5"><Search className="w-3.5 h-3.5" /> Publishing Lineage Inspector — identity is judged on canonical manuscript checksum, source document, author &amp; title history (not title equality alone).</div>
            {inspect.books.map((b) => (
              <div key={b.book_code} className="rounded-lg border p-4" data-testid={`inspect-book-${b.book_code}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-navy">{b.book_code}</span>
                  <Badge v={b.classification} />
                  {typeof b.confidence === "number" && (
                    <span className="text-[10px] text-muted-foreground border rounded-full px-2 py-0.5" data-testid={`confidence-${b.book_code}`}>
                      confidence {Math.round(b.confidence * 100)}%
                    </span>
                  )}
                  {b.rerender_epub_available && <span className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">re-rendered EPUB available</span>}
                  {b.adopt_eligible && <span className="text-[10px] text-blue-700 bg-blue-50 border border-blue-200 rounded-full px-2 py-0.5">adopt-eligible</span>}
                </div>
                <p className="text-xs text-foreground mt-2"><span className="font-semibold">Recommended action:</span> {b.recommendation}</p>

                {b.reasoning?.length > 0 && (
                  <div className="mt-3 rounded-md border bg-muted/20 p-3" data-testid={`reasoning-${b.book_code}`}>
                    <div className="text-[11px] font-semibold text-foreground mb-1.5">Reasoning chain</div>
                    <ol className="space-y-1">
                      {b.reasoning.map((r, i) => (
                        <li key={i} className="text-[11px] text-muted-foreground flex gap-2">
                          <span className={`shrink-0 font-semibold ${r.result === "MATCH" || r.result === "OVERLAP" || r.result === "COMPATIBLE" ? "text-emerald-700" : r.result === "DIFFER" ? "text-red-600" : "text-amber-600"}`}>{r.result}</span>
                          <span><span className="text-foreground font-medium">{r.check}:</span> {r.detail}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                <div className="grid md:grid-cols-2 gap-3 mt-3 text-xs">
                  <div className="rounded-md border bg-muted/30 p-3">
                    <div className="font-semibold text-foreground mb-1">Incoming (migration)</div>
                    <div className="space-y-0.5 text-muted-foreground">
                      <div>id: <span className="font-mono text-[10px]">{b.incoming.id}</span></div>
                      <div>title: <span className="text-foreground">{b.incoming.title}</span></div>
                      <div>author: {b.incoming.author || "—"}</div>
                      <div>source: {b.incoming.source_filename || "—"}</div>
                      <div>checksum: <span className="font-mono text-[10px]">{(b.incoming.checksum || "—").slice(0, 16)}</span></div>
                    </div>
                  </div>
                  <div className="rounded-md border bg-card p-3">
                    <div className="font-semibold text-foreground mb-1">Existing in this DB</div>
                    {b.existing_by_id || b.existing_by_code ? (
                      <div className="space-y-0.5 text-muted-foreground">
                        <div>id: <span className="font-mono text-[10px]">{(b.existing_by_id || b.existing_by_code).id}</span></div>
                        <div>title: <span className="text-foreground">{(b.existing_by_id || b.existing_by_code).title}</span></div>
                        <div>author: {(b.existing_by_id || b.existing_by_code).author || "—"}</div>
                        <div>source: {(b.existing_by_id || b.existing_by_code).source_filename || "—"}</div>
                        <div>checksum: <span className="font-mono text-[10px]">{((b.existing_by_id || b.existing_by_code).checksum || "—").slice(0, 16)}</span></div>
                        <div>status: {(b.existing_by_id || b.existing_by_code).publication_status || "—"}</div>
                        <div>purchases: <span className="text-foreground">{(b.existing_by_id || b.existing_by_code).purchases}</span></div>
                        <div>current EPUB: <span className="font-mono text-[10px]">{((b.existing_by_id || b.existing_by_code).epub || "—").split("/").pop()}</span></div>
                      </div>
                    ) : <div className="text-muted-foreground">Not present — safe to create.</div>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {reportA && (
          <div className="mt-4" data-testid="report-a">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold ${reportA.ok === false ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"}`}>
                {reportA.ok === false ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                {reportA.mode === "APPLY" ? "Applied" : reportA.action ? "Rollback" : "Dry run complete"}
              </span>
              {reportA.halted && <span className="text-red-700">{reportA.halted}</span>}
            </div>
            <EvidenceRows rows={rowsA} />
            <details className="mt-2 text-[11px] text-muted-foreground"><summary className="cursor-pointer">Raw evidence report (JSON)</summary><pre className="mt-2 p-3 bg-muted rounded-lg overflow-x-auto">{JSON.stringify(reportA, null, 2)}</pre></details>
          </div>
        )}
      </section>

      {/* Workstream C */}
      <section className="rounded-xl border bg-card p-5" data-testid="workstream-c">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-royal font-semibold">Workstream C · QRU Learn Governance</div>
            <div className="flex items-center gap-2 mt-1"><GraduationCap className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">Learn Containment</span></div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">Classifies 5 lessons that are Published to learners while their linked Knowledge Record is not yet Verified. Optionally places only those on a governed hold (removed from the learner catalog) — product, assets, and purchases fully preserved, with one-tap rollback.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={() => runC("classify")} disabled={!!busy} data-testid="c-classify" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "C-classify" ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />} Classify (read-only)
          </button>
          <button onClick={() => runC("hold")} disabled={!!busy} data-testid="c-hold" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {busy === "C-hold" ? <Loader2 className="w-4 h-4 animate-spin" /> : <PauseOctagon className="w-4 h-4" />} Apply Governance Hold
          </button>
          <button onClick={() => runC("rollback")} disabled={!!busy} data-testid="c-rollback" className="inline-flex items-center gap-2 rounded-lg border border-red-200 text-red-700 px-4 py-2 text-sm font-medium hover:bg-red-50 disabled:opacity-50">
            {busy === "C-rollback" ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} Rollback
          </button>
        </div>
        {reportC && (
          <div className="mt-4" data-testid="report-c">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold bg-emerald-100 text-emerald-700`}>
                <CheckCircle2 className="w-3.5 h-3.5" />
                {reportC.action ? "Rollback" : reportC.hold_actions ? (reportC.mode === "APPLY" ? "Hold applied" : "Hold preview") : "Classification"}
              </span>
            </div>
            <EvidenceRows rows={rowsC} />
            <details className="mt-2 text-[11px] text-muted-foreground"><summary className="cursor-pointer">Raw evidence report (JSON)</summary><pre className="mt-2 p-3 bg-muted rounded-lg overflow-x-auto">{JSON.stringify(reportC, null, 2)}</pre></details>
          </div>
        )}
      </section>

      {/* DQ-7C Standards Metadata — independent governed operation */}
      <section className="rounded-xl border bg-card p-5" data-testid="standards-metadata">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-royal font-semibold">DQ-7C · Governance Metadata</div>
            <div className="flex items-center gap-2 mt-1"><Layers className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">Standards Metadata Canonicalization</span></div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">Applies the Founder-approved, additive standards metadata: <span className="font-medium">lifecycle=ADOPTED</span> on all 39 canonical standards, the 11 evidence-backed enforcement classifications, <span className="font-medium">FOUNDER_DECISION_REQUIRED</span> on the remaining 28 (untouched), plus <span className="font-medium">owner/verification</span> on the 5 constitutional-tier records and <span className="font-medium">canonical_ref + projection</span> tags on the 5 constitutional projections. Additive-only; no overwrites, deletes or renames.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={runStdPreflight} disabled={!!busy} data-testid="d-preflight" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "D-preflight" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ClipboardCheck className="w-4 h-4" />} Production Preflight
          </button>
          <button onClick={() => runStdApply("dry")} disabled={!!busy} data-testid="d-dry" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "D-dry" ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />} Dry Run
          </button>
          <button onClick={() => runStdApply("apply")} disabled={!!busy || (stdPre && !stdPre.ready_to_apply)} data-testid="d-apply" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50" title={stdPre && !stdPre.ready_to_apply ? "Run Preflight — apply enabled only when 39 canonical + 5 projections and no conflict" : ""}>
            {busy === "D-apply" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Apply Metadata
          </button>
          <button onClick={runStdRollback} disabled={!!busy} data-testid="d-rollback" className="inline-flex items-center gap-2 rounded-lg border border-red-200 text-red-700 px-4 py-2 text-sm font-medium hover:bg-red-50 disabled:opacity-50">
            {busy === "D-rollback" ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} Rollback
          </button>
        </div>

        {stdPre && (
          <div className="mt-4 rounded-lg border p-4" data-testid="std-preflight">
            <div className="flex flex-wrap items-center gap-2 text-xs mb-3">
              <span className="font-semibold text-navy">Preflight</span>
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold ${stdPre.ready_to_apply ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                {stdPre.ready_to_apply ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                {stdPre.ready_to_apply ? "Ready to apply" : "Not ready"}
              </span>
              {!stdPre.ready_to_apply && <span className="text-red-700">{(stdPre.block_reasons || []).join(" · ")}</span>}
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <Stat label="Canonical standards" value={`${stdPre.production_counts.qiks_standards}/39`} tone={stdPre.production_counts.qiks_standards === 39 ? "ok" : "bad"} />
              <Stat label="Constitutional projections" value={`${stdPre.production_counts.constitutional_registry}/5`} tone={stdPre.production_counts.constitutional_registry === 5 ? "ok" : "bad"} />
              <Stat label="Need metadata" value={stdPre.material_differences.canonical_records_needing_metadata} tone={stdPre.material_differences.canonical_records_needing_metadata ? "warn" : "ok"} />
              <Stat label="Conflicts" value={stdPre.material_differences.field_conflicts.length} tone={stdPre.material_differences.field_conflicts.length ? "bad" : "ok"} />
            </div>
            <div className="mt-3 text-[11px] text-muted-foreground">
              <span className="font-medium text-foreground">Material differences vs validated preview:</span>{" "}
              missing: {stdPre.material_differences.missing_standard_ids.join(", ") || "none"} · unexpected: {stdPre.material_differences.unexpected_standard_ids.join(", ") || "none"} · unresolved projections: {stdPre.material_differences.unresolved_projections.length} · already applied: {stdPre.material_differences.canonical_records_already_applied}
              <div className="mt-1">Enforcement: INH {stdPre.enforcement_distribution.INHERITED_ENFORCED} · GATE {stdPre.enforcement_distribution.GATE_ENFORCED} · FOUNDER_DECISION_REQUIRED {stdPre.enforcement_distribution.FOUNDER_DECISION_REQUIRED} (left untouched)</div>
            </div>
          </div>
        )}

        {reportD && (
          <div className="mt-4" data-testid="report-d">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold ${["BLOCKED", "HALTED"].includes(reportD.mode) ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"}`}>
                {["BLOCKED", "HALTED"].includes(reportD.mode) ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                {reportD.action === "rollback" ? "Rollback" : reportD.mode === "APPLY" ? "Applied" : reportD.mode === "DRY_RUN" ? "Dry run" : reportD.mode}
              </span>
              {reportD.canonical_field_writes !== undefined && <span className="text-muted-foreground">writes: {reportD.canonical_field_writes} canonical + {reportD.projection_field_writes} projection · overwrites 0 · deletes 0 · renames 0</span>}
            </div>
            {reportD.verification && (
              <div className="mt-2 text-[11px] text-muted-foreground rounded-md border bg-muted/20 p-3">
                <div className="font-semibold text-foreground mb-1">Post-apply verification</div>
                counts stable: {String(reportD.verification.counts_stable)} · projections resolve 1:1: {String(reportD.verification.every_canonical_ref_resolves_to_exactly_one)} · founder_approval preserved: {String(reportD.verification.founder_approval_preserved)} · const-5 owner/verification present: {reportD.verification.const5_owner_verification_present}/5
                <div>lifecycle: {JSON.stringify(reportD.verification.lifecycle)} · enforcement: {JSON.stringify(reportD.verification.enforcement)}</div>
              </div>
            )}
            <details className="mt-2 text-[11px] text-muted-foreground"><summary className="cursor-pointer">Raw completion report (JSON)</summary><pre className="mt-2 p-3 bg-muted rounded-lg overflow-x-auto">{JSON.stringify(reportD, null, 2)}</pre></details>
          </div>
        )}
      </section>

      {/* Test Product Cleanup — independent governed operation */}
      <section className="rounded-xl border bg-card p-5" data-testid="test-cleanup">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-royal font-semibold">Store Hygiene · Catalog Cleanup</div>
            <div className="flex items-center gap-2 mt-1"><Trash2 className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">Test Product Cleanup</span></div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">Detects internal acceptance-test and placeholder products (e.g. <span className="font-medium">UI_TEST_PROD</span>, <span className="font-medium">QRU Factory Acceptance Test</span>, <span className="font-medium">test infographic asset</span>) and archives them so they leave the learner catalog. Detection is deterministic (known test signatures only — never a bare word). Products tied to a paid order are always skipped. Assets are preserved and every change is fully reversible via Rollback.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={runTestPreflight} disabled={!!busy} data-testid="e-preflight" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "E-preflight" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Scan (read-only)
          </button>
          <button onClick={() => runTestCleanup("dry")} disabled={!!busy} data-testid="e-dry" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "E-dry" ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />} Dry Run
          </button>
          <button onClick={() => runTestCleanup("apply")} disabled={!!busy} data-testid="e-apply" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {busy === "E-apply" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />} Archive Test Products
          </button>
          <button onClick={() => runTestCleanup("rollback")} disabled={!!busy} data-testid="e-rollback" className="inline-flex items-center gap-2 rounded-lg border border-red-200 text-red-700 px-4 py-2 text-sm font-medium hover:bg-red-50 disabled:opacity-50">
            {busy === "E-rollback" ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} Rollback
          </button>
        </div>

        {testPre && (
          <div className="mt-4 rounded-lg border p-4" data-testid="test-preflight">
            <div className="flex flex-wrap items-center gap-2 text-xs mb-3">
              <span className="font-semibold text-navy">Scan</span>
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold ${testPre.removable > 0 ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                {testPre.removable > 0 ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                {testPre.removable > 0 ? `${testPre.removable} removable` : "Catalog clean"}
              </span>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
              <Stat label="Matched total" value={testPre.counts.matched_total} />
              <Stat label="Visible in catalog" value={testPre.counts.visible_in_catalog} tone={testPre.counts.visible_in_catalog ? "warn" : "ok"} />
              <Stat label="Not published" value={testPre.counts.not_published} />
              <Stat label="Already archived" value={testPre.counts.already_archived} />
              <Stat label="Has paid order (skip)" value={testPre.counts.has_paid_order} tone={testPre.counts.has_paid_order ? "bad" : "ok"} />
            </div>
          </div>
        )}

        {(reportE || testPre) && (
          <div className="mt-4" data-testid="report-e">
            {reportE && (
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold bg-emerald-100 text-emerald-700">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {reportE.action === "rollback" ? "Rollback" : reportE.mode === "APPLY" ? "Archived" : "Dry run"}
                </span>
              </div>
            )}
            <EvidenceRows rows={rowsE} />
            <details className="mt-2 text-[11px] text-muted-foreground"><summary className="cursor-pointer">Raw report (JSON)</summary><pre className="mt-2 p-3 bg-muted rounded-lg overflow-x-auto">{JSON.stringify(reportE || testPre, null, 2)}</pre></details>
          </div>
        )}
      </section>

      {/* Imprint Canonicalization & Duplicate Merge — RI-IMPRINT-0001 */}
      <section className="rounded-xl border bg-card p-5" data-testid="imprint-canonicalization">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-royal font-semibold">Brand Identity · Imprint Governance</div>
            <div className="flex items-center gap-2 mt-1"><BookOpen className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">Imprint Canonicalization & Duplicate Merge</span></div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">Assigns every book to its canonical imprint — <span className="font-medium">E.Q. Rothwell™</span> for the literary list (The Understanding Tree, Ordinary Tuesdays, Patterns of Intelligence) and <span className="font-medium">QRU Press™</span> for all educational / institutional titles — records a permanent <span className="font-medium">canonical_imprint</span> + <span className="font-medium">genre</span>, sets literary authorship to E.Q. Rothwell, and merges the <span className="font-medium">"Ordinary Tuesdays FULL MANUSCRIPT"</span> duplicate into the canonical record (manuscript, files &amp; history preserved). Additive metadata, fully reversible. <span className="font-medium">Covers are not re-rendered</span> — no AI spend.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={runImprintPreflight} disabled={!!busy} data-testid="g-preflight" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "G-preflight" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Audit (read-only)
          </button>
          <button onClick={() => runImprint("dry")} disabled={!!busy} data-testid="g-dry" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "G-dry" ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />} Dry Run
          </button>
          <button onClick={() => runImprint("apply")} disabled={!!busy} data-testid="g-apply" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {busy === "G-apply" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />} Apply Canonicalization
          </button>
          <button onClick={() => runImprint("rollback")} disabled={!!busy} data-testid="g-rollback" className="inline-flex items-center gap-2 rounded-lg border border-red-200 text-red-700 px-4 py-2 text-sm font-medium hover:bg-red-50 disabled:opacity-50">
            {busy === "G-rollback" ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} Rollback
          </button>
        </div>

        {imprintPre && (
          <div className="mt-4 rounded-lg border p-4" data-testid="imprint-preflight">
            <div className="flex flex-wrap items-center gap-2 text-xs mb-3">
              <span className="font-semibold text-navy">Audit</span>
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold ${imprintPre.ready_to_apply ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                {imprintPre.ready_to_apply ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                {imprintPre.ready_to_apply ? `${imprintPre.removable} to apply` : "All canonical"}
              </span>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
              <Stat label="Total books" value={imprintPre.counts.total} />
              <Stat label="To update" value={imprintPre.counts.to_update} tone={imprintPre.counts.to_update ? "warn" : "ok"} />
              <Stat label="Duplicate merges" value={imprintPre.counts.to_merge} tone={imprintPre.counts.to_merge ? "warn" : "ok"} />
              <Stat label="Imprint reassignments" value={imprintPre.counts.imprint_reassignments} tone={imprintPre.counts.imprint_reassignments ? "warn" : "ok"} />
              <Stat label="E.Q. Rothwell™" value={imprintPre.counts.eq_rothwell} />
              <Stat label="QRU Press™" value={imprintPre.counts.qru_press} />
            </div>
          </div>
        )}

        {reportG && (
          <div className="mt-4" data-testid="report-g">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold bg-emerald-100 text-emerald-700">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {reportG.action === "rollback" ? "Rollback" : reportG.mode === "APPLY" ? "Applied" : "Dry run"}
              </span>
            </div>
            <EvidenceRows rows={rowsG} />
            <details className="mt-2 text-[11px] text-muted-foreground"><summary className="cursor-pointer">Raw report (JSON)</summary><pre className="mt-2 p-3 bg-muted rounded-lg overflow-x-auto">{JSON.stringify(reportG, null, 2)}</pre></details>
          </div>
        )}
      </section>

      {/* Batch Upgrade Assets™ — background, $0 AI cover re-render */}
      <section className="rounded-xl border bg-card p-5" data-testid="assets-upgrade">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-royal font-semibold">Store Hygiene · Cover Quality</div>
            <div className="flex items-center gap-2 mt-1"><ImageIcon className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">Batch Upgrade Assets™</span></div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">Re-renders every catalog product cover through the <span className="font-medium">hardened deterministic renderer</span> — legible titles, safe vertical bands, no overflow. Guaranteed <span className="font-medium">$0 AI</span>. Founder-selected Asset Vault covers are always preserved. Runs in the background; resumable and safe to re-run.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={runAssetPreflight} disabled={!!busy} data-testid="f-preflight" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "F-preflight" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Scan (read-only)
          </button>
          <button onClick={() => runAssetUpgrade(false)} disabled={!!busy || assetJob?.status === "running"} data-testid="f-run" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {busy === "F-run" || assetJob?.status === "running" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Upgrade Remaining Covers
          </button>
          <button onClick={() => runAssetUpgrade(true)} disabled={!!busy || assetJob?.status === "running"} data-testid="f-run-all" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "F-run-all" ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />} Re-render All
          </button>
        </div>

        {assetPre && (
          <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-3" data-testid="asset-preflight">
            <Stat label="Eligible products" value={assetPre.eligible_products} />
            <Stat label="Not yet upgraded" value={assetPre.not_yet_upgraded} tone={assetPre.not_yet_upgraded ? "warn" : "ok"} />
            <Stat label="Already upgraded" value={assetPre.already_upgraded} tone="ok" />
            <Stat label="AI cost" value="$0" tone="ok" />
          </div>
        )}

        {assetJob && assetJob.status !== "idle" && (
          <div className="mt-4 rounded-lg border p-4" data-testid="asset-job">
            <div className="flex flex-wrap items-center gap-2 text-xs mb-3">
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold ${assetJob.status === "complete" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                {assetJob.status === "complete" ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                {assetJob.status === "complete" ? "Complete" : "Running"}
              </span>
              <span className="text-muted-foreground">{assetJob.done}/{assetJob.total} processed</span>
            </div>
            <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-navy transition-all" style={{ width: `${assetJob.total ? Math.round((assetJob.done / assetJob.total) * 100) : 0}%` }} />
            </div>
            <div className="mt-3 grid grid-cols-2 lg:grid-cols-4 gap-3">
              <Stat label="Upgraded" value={assetJob.ok} tone="ok" />
              <Stat label="Preserved (Founder asset)" value={assetJob.skipped} />
              <Stat label="Failed" value={assetJob.failed} tone={assetJob.failed ? "bad" : "ok"} />
              <Stat label="Remaining" value={assetJob.remaining} />
            </div>
          </div>
        )}
      </section>

      {/* Cover Reference Repair — RI-COVER-REPAIR-0001 */}
      <section className="rounded-xl border bg-card p-5" data-testid="cover-repair">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-royal font-semibold">Store Hygiene · Cover Integrity</div>
            <div className="flex items-center gap-2 mt-1"><ImageIcon className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">Cover Reference Repair</span></div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">Finds books whose <span className="font-medium">active (Founder-selected) cover</span> is missing from durable object storage (the cause of broken cover thumbnails) and repoints the active cover to the first <span className="font-medium">Founder-generated concept that is still retrievable</span>. Deterministic, <span className="font-medium">no AI spend</span>, no re-render. If the original cover ever returns, the storefront restores it automatically. Fully reversible via Rollback.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={runCoverPreflight} disabled={!!busy} data-testid="cov-preflight" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "COV-preflight" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Audit (read-only)
          </button>
          <button onClick={() => runCoverRepair("dry")} disabled={!!busy} data-testid="cov-dry" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
            {busy === "COV-dry" ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />} Dry Run
          </button>
          <button onClick={() => runCoverRepair("apply")} disabled={!!busy} data-testid="cov-apply" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {busy === "COV-apply" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />} Repair Cover References
          </button>
          <button onClick={() => runCoverRepair("rollback")} disabled={!!busy} data-testid="cov-rollback" className="inline-flex items-center gap-2 rounded-lg border border-red-200 text-red-700 px-4 py-2 text-sm font-medium hover:bg-red-50 disabled:opacity-50">
            {busy === "COV-rollback" ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} Rollback
          </button>
        </div>

        {coverPre && (
          <div className="mt-4 rounded-lg border p-4" data-testid="cover-preflight">
            <div className="flex flex-wrap items-center gap-2 text-xs mb-3">
              <span className="font-semibold text-navy">Audit</span>
              <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold ${coverPre.affected > 0 ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                {coverPre.affected > 0 ? <AlertTriangle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                {coverPre.affected > 0 ? `${coverPre.repairable} repairable` : "All covers healthy"}
              </span>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              <Stat label="Books with broken cover" value={coverPre.affected} tone={coverPre.affected ? "warn" : "ok"} />
              <Stat label="Repairable (alternate available)" value={coverPre.repairable} tone={coverPre.repairable ? "warn" : "ok"} />
              <Stat label="Unrepairable (no concept survives)" value={coverPre.unrepairable} tone={coverPre.unrepairable ? "bad" : "ok"} />
            </div>
            <EvidenceRows rows={(coverPre.rows || []).map((r) => ({
              code: r.code, outcome: r.repairable ? "WOULD_REPAIR" : "SKIPPED_NO_REPLACEMENT",
              detail: `${r.title} — broken: ${r.broken_cover}${r.repairable ? ` → concept ${r.replacement_concept}` : " (no alternate)"}`,
            }))} />
          </div>
        )}

        {reportCover && (
          <div className="mt-4" data-testid="report-cover">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold bg-emerald-100 text-emerald-700">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {reportCover.action === "rollback" ? "Rollback" : reportCover.mode === "APPLY" ? "Repaired" : "Dry run"}
              </span>
            </div>
            <EvidenceRows rows={rowsCover} />
            <details className="mt-2 text-[11px] text-muted-foreground"><summary className="cursor-pointer">Raw report (JSON)</summary><pre className="mt-2 p-3 bg-muted rounded-lg overflow-x-auto">{JSON.stringify(reportCover, null, 2)}</pre></details>
          </div>
        )}
      </section>
    </div>
  );
}
