import { useState, useRef, useCallback, useEffect } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import {
  Wrench, Loader2, HardDriveDownload, RefreshCw, ShieldCheck, Activity,
  FileSearch, CheckCircle2, XCircle, AlertTriangle, CloudUpload,
} from "lucide-react";

const SUPER = ["Founder & CEO", "Administrator"];
const BACKEND = process.env.REACT_APP_BACKEND_URL;

// A small governed panel that runs production operations from the Founder's
// authenticated Factory session — no tokens to copy, no command line.
export function FounderOpsToolkit() {
  const { user } = useAuth();
  const isSuper = SUPER.includes(user?.role);

  const [ukr, setUkr] = useState(null);
  const [audit, setAudit] = useState(null);
  const [recovery, setRecovery] = useState(null);
  const [backfill, setBackfill] = useState(null);
  const [health, setHealth] = useState(null);
  const [jwt, setJwt] = useState(null);
  const [busy, setBusy] = useState("");
  const polls = useRef({});

  const stopPoll = (key) => { if (polls.current[key]) { clearInterval(polls.current[key]); polls.current[key] = null; } };
  useEffect(() => () => Object.keys(polls.current).forEach(stopPoll), []);

  const poll = useCallback((key, url, setter) => {
    stopPoll(key);
    polls.current[key] = setInterval(async () => {
      try {
        const { data } = await api.get(url);
        setter(data);
        if (data?.status && data.status !== "running") stopPoll(key);
      } catch { stopPoll(key); }
    }, 3000);
  }, []);

  const runUkr = async () => {
    setBusy("ukr");
    try { const { data } = await api.get("/manufacturing/ukr/migration-status"); setUkr(data); }
    catch (e) { toast.error(e?.response?.data?.detail || "UKR status failed."); }
    finally { setBusy(""); }
  };

  const startJob = async (key, startUrl, statusUrl, setter) => {
    setBusy(key);
    try {
      const { data } = await api.post(startUrl);
      toast.success(data.message || "Started.");
      const s = await api.get(statusUrl); setter(s.data);
      poll(key, statusUrl, setter);
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not start."); }
    finally { setBusy(""); }
  };

  const runHealth = async () => {
    setBusy("health");
    try {
      const [books, ukrRes] = await Promise.all([
        api.get("/public/books"),
        api.get("/manufacturing/ukr/migration-status"),
      ]);
      const b = Array.isArray(books.data) ? books.data : (books.data?.books || []);
      setHealth({
        storefront_ok: true, books_live: b.length,
        ukr_migrated: ukrRes.data?.migrated, ukr_total: ukrRes.data?.total,
        checked_at: new Date().toLocaleString(),
      });
      toast.success("Health check complete.");
    } catch (e) { setHealth({ storefront_ok: false }); toast.error("Health check failed."); }
    finally { setBusy(""); }
  };

  const verifyJwt = async () => {
    setBusy("jwt"); setJwt(null);
    try {
      const { data } = await api.get("/products");
      const items = Array.isArray(data) ? data : (data?.products || data?.items || []);
      const prod = items.find((p) =>
        ((p.customer_deliverable || {}).files || []).some(
          (f) => f.format === "pdf" && String(f.filename || "").startsWith("deliverable-")));
      if (!prod) { setJwt({ error: "No product with a rendered PDF deliverable found." }); return; }
      const tok = (await api.post(`/products/${prod.id}/file-token`, { format: "pdf", action: "preview" })).data;
      const okRes = await fetch(`${BACKEND}${tok.url}`);
      const fid = tok.url.split("/asset/")[1].split("?")[0];
      const noTokRes = await fetch(`${BACKEND}/api/rendering/asset/${fid}`);
      setJwt({
        product: prod.title, tokened_status: okRes.status, notoken_status: noTokRes.status,
        pass: okRes.status === 200 && noTokRes.status === 403,
      });
    } catch (e) { setJwt({ error: e?.response?.data?.detail || "JWT verify failed." }); }
    finally { setBusy(""); }
  };

  if (!isSuper) return null;

  const jobStat = (j) => j ? `${j.status} · done ${j.done ?? 0}/${j.total ?? 0}` : null;

  return (
    <div className="bg-card border rounded-sm p-6" data-testid="founder-ops-toolkit">
      <div className="flex items-center gap-2">
        <Wrench className="w-4 h-4 text-royal" />
        <h3 className="font-heading text-lg text-navy">Founder Operations Toolkit™</h3>
        <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-semibold">super-admin</span>
      </div>
      <p className="text-[13px] text-muted-foreground mt-1 max-w-2xl">
        Governed production operations, run from your authenticated Factory session — no tokens, no command line.
        Audits are read-only; recovery is deterministic ($0 AI; AI-art/audio are listed for approval, never auto-run).
      </p>

      <div className="grid sm:grid-cols-2 gap-3 mt-5">
        {/* UKR migration status */}
        <OpCard icon={ShieldCheck} title="UKR Migration Status"
          desc="Confirm all Knowledge Records are on the canonical v1.1 spec."
          btn="Check" testid="ops-ukr" onClick={runUkr} loading={busy === "ukr"}>
          {ukr && (
            <Result testid="ops-ukr-result" ok={ukr.not_migrated === 0}>
              {ukr.migrated}/{ukr.total} migrated · {ukr.not_migrated} pending ·
              {ukr.fully_backward_compatible ? " backward-compatible" : " ⚠ compat issue"}
            </Result>
          )}
        </OpCard>

        {/* Health check */}
        <OpCard icon={Activity} title="Production Health Check"
          desc="Storefront reachability + live catalog + UKR state at a glance."
          btn="Run" testid="ops-health" onClick={runHealth} loading={busy === "health"}>
          {health && (
            <Result testid="ops-health-result" ok={health.storefront_ok}>
              {health.storefront_ok
                ? `Storefront OK · ${health.books_live} books live · UKR ${health.ukr_migrated}/${health.ukr_total}`
                : "Storefront check failed"}
            </Result>
          )}
        </OpCard>

        {/* Storage audit */}
        <OpCard icon={FileSearch} title="Storage Audit"
          desc="Compare DB references vs. local disk + durable object storage (read-only)."
          btn="Run audit" testid="ops-audit"
          onClick={() => startJob("audit", "/rendering/storage-audit", "/rendering/storage-audit/status", setAudit)}
          loading={busy === "audit"}>
          {audit && audit.totals && (
            <Result testid="ops-audit-result" ok={audit.totals.missing === 0}>
              {audit.totals.referenced} referenced · {audit.totals.local} local · {audit.totals.object} durable ·
              <b> {audit.totals.missing} missing</b>
              {audit.missing_classification && (
                <span className="block mt-1 text-[11px]">
                  deterministic {audit.missing_classification.deterministic?.count ?? 0} ·
                  ai-art {audit.missing_classification.ai_art?.count ?? 0} ·
                  audio {audit.missing_classification.ai_tts?.count ?? 0} ·
                  other {audit.missing_classification.other?.count ?? 0}
                </span>
              )}
            </Result>
          )}
        </OpCard>

        {/* Storage recovery */}
        <OpCard icon={RefreshCw} title="Deterministic Recovery"
          desc="Rebuild missing document deliverables at $0. Resumable + idempotent."
          btn="Run recovery" testid="ops-recovery"
          onClick={() => startJob("recovery", "/rendering/storage-recovery", "/rendering/storage-recovery/status", setRecovery)}
          loading={busy === "recovery"}>
          {recovery && (
            <Result testid="ops-recovery-result" ok={recovery.status === "complete" && recovery.failed === 0}>
              {recovery.status} · recovered {recovery.recovered ?? 0} · skipped {recovery.skipped ?? 0} · failed {recovery.failed ?? 0}
              {recovery.approval_needed && (
                <span className="block mt-1 text-[11px] text-amber-700">
                  approval needed — ai-art {recovery.approval_needed.ai_art?.length ?? 0}, audio {recovery.approval_needed.ai_tts?.length ?? 0}
                </span>
              )}
            </Result>
          )}
        </OpCard>

        {/* Storage backfill */}
        <OpCard icon={CloudUpload} title="Durability Backfill"
          desc="Push current on-disk files into durable object storage (idempotent)."
          btn="Run backfill" testid="ops-backfill"
          onClick={() => startJob("backfill", "/rendering/storage-backfill", "/rendering/storage-backfill/status", setBackfill)}
          loading={busy === "backfill"}>
          {backfill && (
            <Result testid="ops-backfill-result" ok={backfill.status === "complete" && (backfill.failed ?? 0) === 0}>
              {backfill.status} · {backfill.done ?? 0}/{backfill.total ?? 0} · uploaded {backfill.uploaded ?? 0} · already {backfill.already ?? 0} · failed {backfill.failed ?? 0}
            </Result>
          )}
        </OpCard>

        {/* JWT deliverable verify */}
        <OpCard icon={HardDriveDownload} title="Verify JWT Deliverables"
          desc="A real paid file must open WITH a token (200) and be denied WITHOUT one (403)."
          btn="Verify" testid="ops-jwt" onClick={verifyJwt} loading={busy === "jwt"}>
          {jwt && (
            jwt.error
              ? <Result testid="ops-jwt-result" ok={false}>{jwt.error}</Result>
              : <Result testid="ops-jwt-result" ok={jwt.pass}>
                  {jwt.product}: tokened {jwt.tokened_status} (want 200), no-token {jwt.notoken_status} (want 403) — {jwt.pass ? "PASS" : "FAIL"}
                </Result>
          )}
        </OpCard>
      </div>
    </div>
  );
}

function OpCard({ icon: Icon, title, desc, btn, testid, onClick, loading, children }) {
  return (
    <div className="border rounded-md p-4 flex flex-col" data-testid={`${testid}-card`}>
      <div className="flex items-center gap-2"><Icon className="w-4 h-4 text-navy" />
        <h4 className="text-sm font-bold text-navy">{title}</h4></div>
      <p className="text-[12px] text-muted-foreground mt-1 flex-1">{desc}</p>
      <button onClick={onClick} disabled={loading} data-testid={`${testid}-btn`}
        className="mt-3 inline-flex items-center justify-center gap-2 bg-navy text-white px-4 py-2 rounded-md text-[13px] font-bold disabled:opacity-40 self-start">
        {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}{btn}
      </button>
      {children}
    </div>
  );
}

function Result({ ok, testid, children }) {
  return (
    <div className={`mt-3 text-[12px] rounded-md px-3 py-2 flex items-start gap-2 ${ok ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"}`}
      data-testid={testid}>
      {ok ? <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0" /> : <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />}
      <span>{children}</span>
    </div>
  );
}
