import { useEffect, useState, useCallback, useRef } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { RefreshCw, Loader2, Sparkles, Trash2, RotateCcw, AlertTriangle, ShieldAlert, FlaskConical } from "lucide-react";

const SUPER = ["Founder & CEO", "Administrator"];

export function PublicationOps() {
  const { user } = useAuth();
  const isSuper = SUPER.includes(user?.role);
  const [status, setStatus] = useState(null);
  const [confirmUpgrade, setConfirmUpgrade] = useState(false);
  const [starting, setStarting] = useState(false);
  const pollRef = useRef(null);

  const [eligible, setEligible] = useState(null);
  const [trash, setTrash] = useState(null);
  const [delTarget, setDelTarget] = useState(null);
  const [delReason, setDelReason] = useState("QA cleanup");
  const [permTarget, setPermTarget] = useState(null);
  const [permTitle, setPermTitle] = useState("");
  const [busy, setBusy] = useState("");

  const fetchStatus = useCallback(async () => {
    try { const { data } = await api.get("/products/rerender-documents/status"); setStatus(data); return data; }
    catch { return null; }
  }, []);

  const loadQA = useCallback(async () => {
    try {
      const [e, t] = await Promise.all([
        api.get("/products/qa-cleanup/eligible"),
        api.get("/products/qa-cleanup/trash"),
      ]);
      setEligible(e.data); setTrash(t.data);
    } catch (err) { /* non-super will 403 */ }
  }, []);

  useEffect(() => {
    if (!isSuper) return;
    fetchStatus().then((d) => { if (d?.status === "running") startPoll(); });
    loadQA();
    return () => pollRef.current && clearInterval(pollRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSuper]);

  const startPoll = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const d = await fetchStatus();
      if (d && d.status !== "running") { clearInterval(pollRef.current); pollRef.current = null; }
    }, 2000);
  };

  const startUpgrade = async () => {
    setConfirmUpgrade(false); setStarting(true);
    try {
      const { data } = await api.post("/products/rerender-documents");
      toast.success(data.message || "Re-render started.");
      await fetchStatus(); startPoll();
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not start."); }
    finally { setStarting(false); }
  };

  const softDelete = async () => {
    const p = delTarget; setBusy("del");
    try {
      await api.post(`/products/${p.id}/qa-cleanup`, { reason: delReason });
      toast.success(`“${p.title}” moved to Trash.`);
      setDelTarget(null); setDelReason("QA cleanup"); loadQA();
    } catch (e) { toast.error(e?.response?.data?.detail || "Delete failed."); }
    finally { setBusy(""); }
  };

  const restore = async (t) => {
    setBusy("restore" + t.id);
    try { await api.post(`/products/qa-cleanup/trash/${t.id}/restore`); toast.success("Restored."); loadQA(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Restore failed."); }
    finally { setBusy(""); }
  };

  const permDelete = async () => {
    const t = permTarget; setBusy("perm");
    try {
      await api.post(`/products/qa-cleanup/trash/${t.id}/permanent-delete`, { confirm_title: permTitle });
      toast.success("Permanently deleted.");
      setPermTarget(null); setPermTitle(""); loadQA();
    } catch (e) { toast.error(e?.response?.data?.detail || "Permanent delete failed."); }
    finally { setBusy(""); }
  };

  if (!isSuper) return null;

  const running = status?.status === "running";
  const complete = status?.status === "complete";
  const pct = status?.total ? Math.round((status.done / status.total) * 100) : 0;

  return (
    <div className="space-y-4" data-testid="publication-ops">
      {/* Upgrade all documents */}
      <div className="bg-card border rounded-sm p-6">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="min-w-0">
            <div className="flex items-center gap-2"><Sparkles className="w-4 h-4 text-royal" />
              <h3 className="font-heading text-lg text-navy">Upgrade all documents</h3></div>
            <p className="text-[13px] text-muted-foreground mt-1 max-w-2xl">
              Re-renders existing <b>document deliverables</b> using the QRU Publication Quality Standard™
              (clean Title/Copyright/Colophon, sanitization pass, governed front matter). Zero AI/LLM or
              cover-generation. Source Knowledge Records, Decoder content, product IDs, links, verification
              status and version history are preserved.
            </p>
            <p className="text-[12px] text-navy mt-2 font-semibold" data-testid="ops-eligible-count">
              Eligible document products: {status?.eligible_count ?? "…"}
            </p>
          </div>
          <button data-testid="ops-upgrade-btn" onClick={() => setConfirmUpgrade(true)} disabled={running || starting}
            className="inline-flex items-center gap-2 bg-navy text-white px-5 py-2.5 rounded-md text-sm font-bold disabled:opacity-40 shrink-0">
            {running || starting ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            {running ? "Upgrade running…" : "Upgrade all documents"}
          </button>
        </div>

        {(running || complete) && (
          <div className="mt-4" data-testid="ops-progress">
            <div className="h-2 rounded-full bg-navy/10 overflow-hidden">
              <div className="h-full bg-royal transition-all" style={{ width: `${pct}%` }} />
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-3 text-center">
              {[["Total", status.total], ["Processed", status.done], ["Succeeded", status.ok],
                ["Failed", status.failed], ["Remaining", status.remaining], ["Status", running ? "Running" : "Complete"]].map(([k, v]) => (
                <div key={k} className="bg-navy/[0.03] rounded-md py-2">
                  <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{k}</p>
                  <p className={`text-sm font-bold ${k === "Failed" && v > 0 ? "text-red-600" : "text-navy"}`}>{v}</p>
                </div>
              ))}
            </div>
            {complete && (
              <div className="mt-3 text-[13px]" data-testid="ops-complete-report">
                <p className="font-semibold text-emerald-700">Batch complete — {status.ok}/{status.total} upgraded, {status.failed} failed.</p>
                {status.failed_ids?.length > 0 && (
                  <p className="text-red-600 mt-1">Failed product IDs: {status.failed_ids.join(", ")}</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* QA Cleanup */}
      <div className="bg-card border rounded-sm p-6" data-testid="qa-cleanup-panel">
        <div className="flex items-center gap-2"><FlaskConical className="w-4 h-4 text-royal" />
          <h3 className="font-heading text-lg text-navy">QA Cleanup™</h3>
          <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full font-semibold">super-admin</span></div>
        <p className="text-[13px] text-muted-foreground mt-1 max-w-2xl">
          Removes ONLY products explicitly marked <b>test / qa / preview</b> that are not published, not
          production, and not tied to a paid order. Removal is a soft delete to Trash; permanent deletion is
          a separate, confirmed action. Every action is audit-logged.
        </p>

        <div className="mt-4">
          <div className="flex items-center justify-between">
            <p className="overline text-primary">Eligible marked products ({eligible?.count ?? 0})</p>
            <button onClick={loadQA} className="text-xs inline-flex items-center gap-1 text-navy"><RefreshCw className="w-3 h-3" /> Refresh</button>
          </div>
          <div className="mt-2 space-y-1.5" data-testid="qa-eligible-list">
            {(eligible?.products || []).length === 0 && <p className="text-xs text-muted-foreground">No products are marked test/qa/preview.</p>}
            {(eligible?.products || []).map((p) => (
              <div key={p.id} className="flex items-center gap-2 border rounded-md px-3 py-2 text-sm" data-testid={`qa-item-${p.id}`}>
                <span className="text-[10px] bg-navy/10 text-navy px-1.5 py-0.5 rounded font-semibold uppercase">{p.qa_status}</span>
                <span className="flex-1 truncate">{p.title} <span className="text-[11px] text-muted-foreground">· {p.product_code} · {p.product_type}</span></span>
                {p.eligible ? (
                  <button onClick={() => setDelTarget(p)} data-testid={`qa-delete-${p.id}`}
                    className="text-[11px] text-red-600 inline-flex items-center gap-1 hover:underline"><Trash2 className="w-3 h-3" /> Move to Trash</button>
                ) : (
                  <span className="text-[11px] text-amber-700 inline-flex items-center gap-1" title={p.blockers?.join("; ")}><ShieldAlert className="w-3 h-3" /> Protected</span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-5">
          <p className="overline text-primary">Trash ({trash?.count ?? 0})</p>
          <div className="mt-2 space-y-1.5" data-testid="qa-trash-list">
            {(trash?.trash || []).length === 0 && <p className="text-xs text-muted-foreground">Trash is empty.</p>}
            {(trash?.trash || []).map((t) => (
              <div key={t.id} className="flex items-center gap-2 border rounded-md px-3 py-2 text-sm bg-navy/[0.02]" data-testid={`trash-item-${t.id}`}>
                <span className="flex-1 truncate">{t.product?.title} <span className="text-[11px] text-muted-foreground">· deleted by {t.deleted_by}</span></span>
                <button onClick={() => restore(t)} disabled={busy === "restore" + t.id} data-testid={`trash-restore-${t.id}`}
                  className="text-[11px] text-emerald-700 inline-flex items-center gap-1 hover:underline disabled:opacity-50"><RotateCcw className="w-3 h-3" /> Restore</button>
                <button onClick={() => { setPermTarget(t); setPermTitle(""); }} data-testid={`trash-perm-${t.id}`}
                  className="text-[11px] text-red-600 inline-flex items-center gap-1 hover:underline"><Trash2 className="w-3 h-3" /> Delete forever</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Confirm upgrade */}
      <Dialog open={confirmUpgrade} onOpenChange={setConfirmUpgrade}>
        <DialogContent data-testid="ops-upgrade-confirm">
          <DialogHeader><DialogTitle>Upgrade {status?.eligible_count ?? ""} document products?</DialogTitle>
            <DialogDescription>Re-render every eligible document deliverable with the Publication Quality Standard™.</DialogDescription></DialogHeader>
          <p className="text-sm text-muted-foreground">This re-renders every eligible document deliverable using the QRU Publication Quality Standard™. No AI/LLM/cover generation. Existing IDs, links, verification and versions are preserved. You can leave this page — the batch keeps running.</p>
          <DialogFooter>
            <button onClick={() => setConfirmUpgrade(false)} className="text-sm px-4 py-2 rounded-sm border">Cancel</button>
            <button onClick={startUpgrade} data-testid="ops-upgrade-confirm-btn" className="text-sm px-4 py-2 rounded-sm bg-navy text-white font-bold">Start upgrade</button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirm soft delete */}
      <Dialog open={!!delTarget} onOpenChange={(o) => !o && setDelTarget(null)}>
        <DialogContent data-testid="qa-delete-confirm">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-amber-500" /> Move to Trash?</DialogTitle>
            <DialogDescription>Soft delete a test/qa/preview product to Trash (restorable).</DialogDescription></DialogHeader>
          {delTarget && (
            <div className="text-sm space-y-2">
              <p>You are moving this <b>{delTarget.qa_status}</b> product to Trash (soft delete, restorable):</p>
              <p className="bg-navy/[0.04] rounded p-2 font-mono text-[12px]">{delTarget.title}<br />ID: {delTarget.id}</p>
              <input value={delReason} onChange={(e) => setDelReason(e.target.value)} placeholder="Reason"
                className="w-full border rounded-md px-3 py-2 text-sm" data-testid="qa-delete-reason" />
            </div>
          )}
          <DialogFooter>
            <button onClick={() => setDelTarget(null)} className="text-sm px-4 py-2 rounded-sm border">Cancel</button>
            <button onClick={softDelete} disabled={busy === "del"} data-testid="qa-delete-confirm-btn" className="text-sm px-4 py-2 rounded-sm bg-red-600 text-white font-bold disabled:opacity-50">{busy === "del" ? "Moving…" : "Move to Trash"}</button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Confirm permanent delete */}
      <Dialog open={!!permTarget} onOpenChange={(o) => !o && setPermTarget(null)}>
        <DialogContent data-testid="qa-perm-confirm">
          <DialogHeader><DialogTitle className="flex items-center gap-2 text-red-600"><ShieldAlert className="w-5 h-5" /> Permanently delete?</DialogTitle>
            <DialogDescription>This cannot be undone. Requires typing the exact product title.</DialogDescription></DialogHeader>
          {permTarget && (
            <div className="text-sm space-y-2">
              <p className="text-red-600 font-semibold">This cannot be undone. Type the exact product title to confirm:</p>
              <p className="bg-navy/[0.04] rounded p-2 font-mono text-[12px]">{permTarget.product?.title}</p>
              <input value={permTitle} onChange={(e) => setPermTitle(e.target.value)} placeholder="Type the exact title"
                className="w-full border rounded-md px-3 py-2 text-sm" data-testid="qa-perm-title" />
            </div>
          )}
          <DialogFooter>
            <button onClick={() => setPermTarget(null)} className="text-sm px-4 py-2 rounded-sm border">Cancel</button>
            <button onClick={permDelete} disabled={busy === "perm" || permTitle.trim() !== (permTarget?.product?.title || "").trim()}
              data-testid="qa-perm-confirm-btn" className="text-sm px-4 py-2 rounded-sm bg-red-600 text-white font-bold disabled:opacity-40">{busy === "perm" ? "Deleting…" : "Delete forever"}</button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
