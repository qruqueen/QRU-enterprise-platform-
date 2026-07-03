import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/shared";
import { toast } from "sonner";
import {
  Activity, CheckCircle2, XCircle, Loader2, PauseCircle, Crown, Package, BookOpen, Cpu, Plug,
  AlertTriangle, RefreshCw, ArrowRight, ShieldAlert,
} from "lucide-react";

const TILES = [
  { key: "total_runs", label: "Total Runs", icon: Activity, color: "text-navy" },
  { key: "successful", label: "Successful", icon: CheckCircle2, color: "text-emerald-600" },
  { key: "failed", label: "Failed", icon: XCircle, color: "text-red-600" },
  { key: "in_progress", label: "In Progress", icon: Loader2, color: "text-primary" },
  { key: "paused", label: "Paused", icon: PauseCircle, color: "text-amber-600" },
  { key: "waiting_on_founder", label: "Waiting on Founder", icon: Crown, color: "text-purple-600" },
  { key: "waiting_on_assets", label: "Waiting on Assets", icon: Package, color: "text-amber-600" },
  { key: "waiting_on_knowledge", label: "Waiting on Knowledge", icon: BookOpen, color: "text-blue-600" },
  { key: "waiting_on_ai", label: "Waiting on AI", icon: Cpu, color: "text-rose-600" },
  { key: "waiting_on_external", label: "Waiting on External", icon: Plug, color: "text-slate-600" },
];

export default function FailureIntelligence() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState("");
  const navigate = useNavigate();

  const load = () => api.get("/failure-intelligence/dashboard").then((r) => setData(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const doFix = async (run, diag) => {
    const route = diag.action?.route;
    if (route === "__retry__") {
      setBusy(run.run_id);
      try {
        const { data: res } = await api.post(`/failure-intelligence/run/${run.run_id}/retry`);
        toast[res.ok ? "success" : "info"](res.message || "Retry requested");
        setTimeout(load, 1200);
      } catch (e) { toast.error(e.response?.data?.detail || "Retry failed"); }
      finally { setBusy(""); }
    } else if (route) {
      navigate(route);
    }
  };

  const retryRun = async (run) => {
    setBusy(run.run_id);
    try {
      const { data: res } = await api.post(`/failure-intelligence/run/${run.run_id}/retry`);
      toast[res.ok ? "success" : "info"](res.message || "Retry requested");
      setTimeout(load, 1200);
    } catch (e) { toast.error(e.response?.data?.detail || "Retry failed"); }
    finally { setBusy(""); }
  };

  if (!data) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  const d = data.dashboard || {};
  const runsWithFailures = (data.runs || []).filter((r) => (r.failures || []).length > 0);

  return (
    <div>
      <PageHeader
        overline="Production Failure Intelligence™"
        title="Every Failure, Explained"
        description="The QRU Factory™ never simply reports “Failed.” Every Production Run records exactly why it failed, what it means, and the next action — with a one-click fix."
        actions={
          <button data-testid="fi-refresh" onClick={load} className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        }
      />

      {/* Failure Dashboard */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-8" data-testid="fi-dashboard">
        {TILES.map((t) => (
          <div key={t.key} className="bg-card border rounded-md p-4" data-testid={`fi-tile-${t.key}`}>
            <div className="flex items-center gap-2 text-muted-foreground">
              <t.icon className={`w-4 h-4 ${t.color}`} />
              <span className="text-xs">{t.label}</span>
            </div>
            <p className="font-heading text-2xl font-bold mt-1">{d[t.key] ?? 0}</p>
          </div>
        ))}
      </div>

      {/* Failing runs */}
      {runsWithFailures.length === 0 ? (
        <EmptyState icon={CheckCircle2} title="No failing production runs" description="Every run is healthy, in progress, or safely waiting for capacity." />
      ) : (
        <div className="space-y-4">
          {runsWithFailures.map((run) => (
            <div key={run.run_id} className="bg-card border rounded-md p-5" data-testid={`fi-run-${run.run_id}`}>
              <div className="flex items-center justify-between gap-3 mb-3 pb-3 border-b">
                <div className="flex items-center gap-2 min-w-0">
                  <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
                  <div className="min-w-0">
                    <p className="font-heading font-semibold truncate">{run.name || run.run_id}</p>
                    <p className="text-xs text-muted-foreground">{run.source} · {run.done}/{run.total} done · {run.failed} failed{run.escalated ? ` · ${run.escalated} escalated` : ""}</p>
                  </div>
                </div>
                {run.retryable && (
                  <button data-testid={`fi-retry-${run.run_id}`} onClick={() => retryRun(run)} disabled={busy === run.run_id}
                    className="flex items-center gap-1.5 bg-primary text-primary-foreground px-3 py-1.5 rounded-sm text-xs font-medium hover:bg-primary/90 transition-colors disabled:opacity-60 shrink-0">
                    {busy === run.run_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />} Retry Failed Run
                  </button>
                )}
              </div>
              <div className="space-y-3">
                {run.failures.map((f, i) => (
                  <div key={i} className="border rounded-md p-4 bg-muted/20" data-testid={`fi-failure-${run.run_id}-${i}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      <p className="text-sm font-semibold">{f.title}</p>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200">{f.root_cause}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-1"><b className="text-foreground">Why:</b> {f.explanation}</p>
                    <p className="text-sm text-muted-foreground mb-2"><b className="text-foreground">Resolution:</b> {f.resolution}</p>
                    {f.action && (
                      <button data-testid={f.action.testid} onClick={() => doFix(run, f)} disabled={busy === run.run_id}
                        className="inline-flex items-center gap-1.5 text-sm text-primary font-medium hover:underline disabled:opacity-60">
                        {f.action.route === "__retry__"
                          ? (busy === run.run_id ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />)
                          : <ArrowRight className="w-4 h-4" />}
                        {f.action.label}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
