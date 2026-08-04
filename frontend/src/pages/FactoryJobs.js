import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Loader2, Boxes, RefreshCw, RotateCcw, Ban, CheckCircle2, XCircle, Clock, Cog, AlertTriangle, PlayCircle } from "lucide-react";

const STATUS_TONE = {
  queued: "bg-blue-50 text-blue-700",
  running: "bg-amber-100 text-amber-800",
  complete: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-neutral-200 text-neutral-600",
};
const STATUS_ICON = {
  queued: Clock, running: Loader2, complete: CheckCircle2, failed: XCircle, cancelled: Ban,
};

const FILTERS = ["all", "running", "queued", "failed", "complete"];

export default function FactoryJobs() {
  const [data, setData] = useState({ jobs: [], counts: {}, total: 0 });
  const [attention, setAttention] = useState({ items: [], count: 0 });
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState({});

  const load = useCallback(async () => {
    try {
      const params = filter === "all" ? {} : { status: filter };
      const [jobsRes, attnRes] = await Promise.all([
        api.get("/factory-jobs", { params }),
        api.get("/factory-jobs/attention").catch(() => ({ data: { items: [], count: 0 } })),
      ]);
      setData(jobsRes.data);
      setAttention(attnRes.data);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    load();
    const t = setInterval(load, 4000); // live view
    return () => clearInterval(t);
  }, [load]);

  const act = async (id, verb) => {
    setBusy((b) => ({ ...b, [id]: true }));
    try {
      await api.post(`/factory-jobs/${id}/${verb}`);
      toast.success(verb === "retry" ? "Job re-queued." : "Job cancelled.");
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setBusy((b) => ({ ...b, [id]: false }));
    }
  };

  const resume = async (item) => {
    if (!item.resume_path) return;
    setBusy((b) => ({ ...b, [item.id]: true }));
    try {
      await api.post(item.resume_path);
      toast.success(`${item.title} resumed.`);
      load();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setBusy((b) => ({ ...b, [item.id]: false }));
    }
  };

  const counts = data.counts || {};

  return (
    <div className="space-y-6" data-testid="factory-jobs-page">
      <PageHeader title="Factory Jobs™" icon={Boxes}
        subtitle="Orchestration Spine™ — every long-running job (storybook renders, audiobook videos, and more) runs here durably. Jobs survive server restarts: an interrupted job is automatically reclaimed and resumed, never left hanging." />

      {attention.count > 0 && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 space-y-3" data-testid="needs-attention-panel">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <h3 className="font-bold text-amber-900 text-sm" data-testid="needs-attention-title">
              Needs attention — {attention.count} {attention.count === 1 ? "item" : "items"} interrupted by a restart
            </h3>
          </div>
          <p className="text-[12px] text-amber-800/80 -mt-1">These were paused mid-run and are safe to resume — nothing is lost.</p>
          <div className="space-y-2">
            {attention.items.map((it) => (
              <div key={`${it.kind}-${it.id}`} className="flex items-start gap-3 rounded-lg bg-white border border-amber-200 p-3" data-testid={`attention-${it.kind}-${it.id}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-navy text-sm truncate">{it.title}</span>
                    <span className="text-[10px] font-mono text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">{it.kind}</span>
                  </div>
                  <p className="text-[12px] text-muted-foreground mt-0.5">{it.detail}</p>
                </div>
                {it.resume_path && (
                  <button onClick={() => resume(it)} disabled={busy[it.id]} data-testid={`attention-resume-${it.id}`}
                    className="text-[11px] font-bold px-3 py-1.5 rounded-md bg-royal text-white hover:bg-royal/90 disabled:opacity-50 flex items-center gap-1 shrink-0">
                    {busy[it.id] ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <PlayCircle className="w-3.5 h-3.5" />} {it.resume_label}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2" data-testid="job-status-summary">
        {["running", "queued", "complete", "failed", "cancelled"].map((s) => (
          <span key={s} className={`text-xs font-bold px-3 py-1.5 rounded-full ${STATUS_TONE[s]}`} data-testid={`count-${s}`}>
            {s}: {counts[s] || 0}
          </span>
        ))}
        <button onClick={load} className="ml-auto text-xs font-semibold px-3 py-1.5 rounded-md border border-navy/20 hover:bg-navy/5 flex items-center gap-1.5" data-testid="jobs-refresh-btn">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {FILTERS.map((f) => (
          <button key={f} onClick={() => setFilter(f)} data-testid={`filter-${f}`}
            className={`text-xs font-bold px-3 py-1.5 rounded-full transition-colors ${filter === f ? "bg-navy text-white" : "bg-navy/5 text-navy hover:bg-navy/10"}`}>
            {f}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-16 text-center text-muted-foreground"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div>
      ) : data.jobs.length === 0 ? (
        <div className="py-16 text-center text-muted-foreground text-sm" data-testid="jobs-empty">No jobs in this view yet.</div>
      ) : (
        <div className="space-y-3">
          {data.jobs.map((j) => {
            const Icon = STATUS_ICON[j.status] || Cog;
            const pr = j.progress || {};
            const pct = pr.total ? Math.round((pr.done / pr.total) * 100) : 0;
            return (
              <div key={j.id} className="rounded-lg border border-navy/10 bg-white p-4 space-y-2" data-testid={`job-${j.id}`}>
                <div className="flex items-start gap-3">
                  <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${j.status === "running" ? "animate-spin text-amber-600" : j.status === "complete" ? "text-emerald-600" : j.status === "failed" ? "text-red-500" : "text-navy/50"}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-navy text-sm truncate">{j.title}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${STATUS_TONE[j.status]}`} data-testid={`job-status-${j.id}`}>{j.status}</span>
                      <span className="text-[10px] text-muted-foreground font-mono">{j.job_type}</span>
                    </div>
                    <p className="text-[12px] text-muted-foreground mt-0.5">{pr.message}{j.attempts > 1 ? ` · attempt ${j.attempts}/${j.max_attempts}` : ""}</p>
                    {j.status === "running" && pr.total > 0 && (
                      <div className="h-1.5 bg-navy/10 rounded-full mt-2 overflow-hidden">
                        <div className="h-full bg-amber-500 transition-all" style={{ width: `${pct}%` }} />
                      </div>
                    )}
                    {j.error && <p className="text-[12px] text-red-600 mt-1" data-testid={`job-error-${j.id}`}>{j.error}</p>}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {(j.status === "failed" || j.status === "cancelled") && (
                      <button onClick={() => act(j.id, "retry")} disabled={busy[j.id]} data-testid={`job-retry-${j.id}`}
                        className="text-[11px] font-bold px-3 py-1.5 rounded-md bg-royal text-white hover:bg-royal/90 disabled:opacity-50 flex items-center gap-1"><RotateCcw className="w-3.5 h-3.5" /> Retry</button>
                    )}
                    {(j.status === "queued" || j.status === "failed") && (
                      <button onClick={() => act(j.id, "cancel")} disabled={busy[j.id]} data-testid={`job-cancel-${j.id}`}
                        className="text-[11px] font-semibold px-3 py-1.5 rounded-md border border-navy/20 hover:bg-navy/5 flex items-center gap-1"><Ban className="w-3.5 h-3.5" /> Cancel</button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
