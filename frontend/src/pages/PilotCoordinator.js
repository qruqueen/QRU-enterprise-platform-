import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, Eye, ShieldCheck, CheckCircle2, AlertTriangle, HelpCircle, Play,
  FileText, Info, Ban,
} from "lucide-react";

const CLASS = {
  READY_FOR_BATCH_RERENDER: { label: "Ready for batch re-render", cls: "bg-emerald-100 text-emerald-700", Icon: CheckCircle2 },
  CORRECTION_REQUIRED: { label: "Correction required", cls: "bg-amber-100 text-amber-700", Icon: AlertTriangle },
  FOUNDER_DECISION_REQUIRED: { label: "Founder decision required", cls: "bg-red-100 text-red-700", Icon: HelpCircle },
};

function ClassBadge({ c }) {
  const b = CLASS[c] || { label: c, cls: "bg-muted text-foreground", Icon: Info };
  const Icon = b.Icon;
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${b.cls}`}><Icon className="w-3.5 h-3.5" /> {b.label}</span>;
}

export default function PilotCoordinator() {
  const [charter, setCharter] = useState(null);
  const [report, setReport] = useState(null);
  const [running, setRunning] = useState(false);
  const [post, setPost] = useState(null);
  const [rerunning, setRerunning] = useState(false);

  const loadReport = () => api.get("/pilot/mfg-coordinator/readiness-report").then((r) => setReport(r.data)).catch(() => setReport(false));
  const loadPost = () => api.get("/pilot/mfg-coordinator/post-render-report").then((r) => setPost(r.data?.empty ? false : r.data)).catch(() => setPost(false));
  useEffect(() => {
    api.get("/pilot/mfg-coordinator").then((r) => setCharter(r.data)).catch(() => {});
    loadReport();
    loadPost();
  }, []);

  const runRerender = async () => {
    if (!window.confirm("Run the authorized RI-MFG-0002 batch re-render of the 8 books? Reuses existing cover art (no AI spend). Nothing is published or deployed.")) return;
    setRerunning(true);
    try {
      const { data } = await api.post("/pilot/mfg-coordinator/batch-rerender");
      setPost(data);
      toast.success(`Batch re-render complete: ${data.total_succeeded}/${data.total_attempted} validated. Nothing deployed.`);
    } catch {
      toast.error("Batch re-render could not complete.");
    }
    setRerunning(false);
  };

  const run = async () => {
    setRunning(true);
    try {
      const { data } = await api.post("/pilot/mfg-coordinator/readiness-report/run");
      setReport(data);
      toast.success("Readiness review complete — filed to the pilot's evidence journal. No live records changed.");
    } catch {
      toast.error("Could not run the readiness review.");
    }
    setRunning(false);
  };

  if (report === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>;
  if (report === false) return <div className="p-8 text-sm text-muted-foreground">Could not load the pilot report.</div>;

  return (
    <div className="space-y-6" data-testid="pilot-coordinator">
      <PageHeader
        overline="PILOT-MFG-0001 · RI-MFG-0001"
        title="Manufacturing Operations Coordinator™"
        subtitle="A governed Shadow-Mode digital role. It observes and evaluates manufacturing work and prepares your brief — it never changes live Factory records."
      />

      {/* Shadow-mode charter */}
      <div className="rounded-xl border bg-card p-5" data-testid="pilot-charter">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-navy text-white px-3 py-1 text-xs font-semibold"><Eye className="w-3.5 h-3.5" /> Shadow Mode</span>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 text-emerald-700 px-3 py-1 text-xs"><ShieldCheck className="w-3.5 h-3.5" /> Observes only · changes nothing</span>
        </div>
        <div className="grid md:grid-cols-2 gap-5 text-sm">
          <div>
            <p className="text-xs uppercase tracking-wide text-emerald-700 font-semibold mb-2">It may</p>
            <ul className="space-y-1 text-muted-foreground">
              {(charter?.may || []).map((m, i) => <li key={i} className="flex gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />{m}</li>)}
            </ul>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-red-700 font-semibold mb-2">It may not (yet)</p>
            <ul className="space-y-1 text-muted-foreground">
              {(charter?.may_not || []).map((m, i) => <li key={i} className="flex gap-2"><Ban className="w-3.5 h-3.5 text-red-500 mt-0.5 shrink-0" />{m}</li>)}
            </ul>
          </div>
        </div>
      </div>

      {/* Workstream + run */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-muted-foreground max-w-2xl">
          <span className="font-semibold text-foreground">First workstream:</span> {report.workstream}
        </div>
        <button onClick={run} disabled={running} data-testid="pilot-run-btn"
          className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
          {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Run readiness review
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" data-testid="pilot-summary">
        <div className="rounded-xl border bg-card p-4"><div className="text-2xl font-bold">{report.total_books_reviewed}</div><div className="text-xs text-muted-foreground mt-1">Books reviewed</div></div>
        <div className="rounded-xl border bg-emerald-50 p-4"><div className="text-2xl font-bold text-emerald-700">{report.counts.READY_FOR_BATCH_RERENDER}</div><div className="text-xs text-emerald-700/80 mt-1">Ready for batch re-render</div></div>
        <div className="rounded-xl border bg-amber-50 p-4"><div className="text-2xl font-bold text-amber-700">{report.counts.CORRECTION_REQUIRED}</div><div className="text-xs text-amber-700/80 mt-1">Correction required</div></div>
        <div className="rounded-xl border bg-red-50 p-4"><div className="text-2xl font-bold text-red-700">{report.estimated_founder_decisions_required}</div><div className="text-xs text-red-700/80 mt-1">Founder decisions needed</div></div>
      </div>

      {/* Per-book */}
      <div className="space-y-3" data-testid="pilot-items">
        {report.items.map((it) => (
          <div key={it.book_code} className="rounded-xl border bg-card p-4" data-testid={`pilot-item-${it.book_code}`}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-royal" />
                  <span className="font-semibold text-foreground">{it.title}</span>
                  <span className="text-[11px] text-muted-foreground">{it.book_code}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-2 max-w-3xl"><span className="font-medium text-foreground">Recommended route:</span> {it.recommended_route}</p>
              </div>
              <ClassBadge c={it.classification} />
            </div>

            {it.blockers.length > 0 && (
              <ul className="mt-3 space-y-1">{it.blockers.map((b, i) => <li key={i} className="flex gap-2 text-sm text-amber-700"><AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />{b}</li>)}</ul>
            )}
            {it.founder_decisions.length > 0 && (
              <ul className="mt-3 space-y-1">{it.founder_decisions.map((f, i) => <li key={i} className="flex gap-2 text-sm text-red-700"><HelpCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />{f}</li>)}</ul>
            )}
            {it.notes.length > 0 && (
              <ul className="mt-3 space-y-1">{it.notes.map((n, i) => <li key={i} className="flex gap-2 text-xs text-muted-foreground"><Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />{n}</li>)}</ul>
            )}

            <div className="mt-3 flex flex-wrap gap-1.5">
              {Object.entries({
                Source: it.evidence.source_manuscript, EPUB: it.evidence.epub_present, Cover: it.evidence.cover_present,
                "Cover legible": it.evidence.cover_legibility_validated, Authorized: it.evidence.authorized,
                "KR linked": it.evidence.knowledge_record_linked, "Print wrap": it.evidence.print_wrap_present,
              }).map(([k, v]) => (
                <span key={k} className={`text-[10px] px-2 py-0.5 rounded-full border ${v ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-muted text-muted-foreground"}`}>{k}: {v ? "✓" : "—"}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* RI-MFG-0002 · Batch re-render */}
      <div className="rounded-xl border-2 border-navy/20 bg-card p-5" data-testid="pilot-rerender-panel">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-royal font-semibold">RI-MFG-0002 · Authorized action</div>
            <div className="font-semibold text-foreground mt-1">Governed batch re-render (8 books)</div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">Re-renders EPUB interiors under the current Publication Quality Standard™, reusing existing cover art (no AI, no spend). Rollback-protected, validated. Never publishes or deploys.</p>
          </div>
          <button onClick={runRerender} disabled={rerunning} data-testid="pilot-rerender-btn"
            className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
            {rerunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Run authorized re-render
          </button>
        </div>

        {post && (
          <div className="mt-5 space-y-4" data-testid="pilot-postrender">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="rounded-lg border bg-card p-3"><div className="text-xl font-bold">{post.total_attempted}</div><div className="text-[11px] text-muted-foreground">Attempted</div></div>
              <div className="rounded-lg border bg-emerald-50 p-3"><div className="text-xl font-bold text-emerald-700">{post.total_succeeded}</div><div className="text-[11px] text-emerald-700/80">Rendered & validated</div></div>
              <div className="rounded-lg border bg-red-50 p-3"><div className="text-xl font-bold text-red-700">{post.total_failed}</div><div className="text-[11px] text-red-700/80">Failed</div></div>
              <div className="rounded-lg border bg-card p-3"><div className="text-xl font-bold">{post.rollback_confirmation?.all_books_rollback_protected ? "✓" : "—"}</div><div className="text-[11px] text-muted-foreground">Rollback protected</div></div>
            </div>

            <div className="rounded-lg bg-navy/5 border border-navy/10 p-3 text-sm" data-testid="pilot-deploy-rec">
              <span className="font-semibold text-navy">Deployment recommendation:</span> {post.deployment_recommendation}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs" data-testid="pilot-postrender-table">
                <thead><tr className="text-left text-muted-foreground border-b"><th className="py-2 pr-3">Book</th><th className="py-2 pr-3">Status</th><th className="py-2 pr-3">EPUB</th><th className="py-2 pr-3">Validated</th><th className="py-2 pr-3">Guards</th><th className="py-2 pr-3">Rollback</th><th className="py-2 pr-3">Purchases</th></tr></thead>
                <tbody>
                  {post.items?.map((i) => (
                    <tr key={i.book_code} className="border-b last:border-0" data-testid={`postrender-row-${i.book_code}`}>
                      <td className="py-2 pr-3"><span className="font-medium text-foreground">{i.book_code}</span> <span className="text-muted-foreground">{(i.title || "").slice(0, 20)}</span></td>
                      <td className="py-2 pr-3">{i.status === "success" ? <span className="text-emerald-700 font-medium">success</span> : <span className="text-red-700">{i.status}</span>}</td>
                      <td className="py-2 pr-3 text-muted-foreground">{i.after?.epub_bytes ? `${(i.after.epub_bytes / 1024).toFixed(0)} KB` : "—"}</td>
                      <td className="py-2 pr-3">{i.validation?.passed ? "✓" : "✗"}</td>
                      <td className="py-2 pr-3">{i.guards_passed ? "✓" : "✗"}</td>
                      <td className="py-2 pr-3">{i.rollback?.all_present ? "✓" : "✗"}</td>
                      <td className="py-2 pr-3 text-muted-foreground">{i.existing_purchase_relationships ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="grid md:grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg border p-3">
                <div className="font-semibold text-foreground mb-1">Pilot metrics</div>
                <div className="text-muted-foreground space-y-0.5">
                  <div>Founder touches: <span className="text-foreground">{post.metrics?.founder_touches}</span></div>
                  <div>Founder time: <span className="text-foreground">{post.metrics?.founder_time_minutes} min</span></div>
                  <div>Classification accuracy: <span className="text-foreground">{post.metrics?.classification_accuracy?.accuracy_pct}%</span> ({post.metrics?.classification_accuracy?.rendered_successfully}/{post.metrics?.classification_accuracy?.predicted_ready})</div>
                  <div>Missing-context rate: <span className="text-foreground">{post.metrics?.missing_context_rate?.pct}%</span></div>
                  <div>Exception quality: <span className="text-foreground">{post.metrics?.exception_quality}</span></div>
                </div>
              </div>
              <div className="rounded-lg border p-3">
                <div className="font-semibold text-foreground mb-1">Governance</div>
                <div className="text-muted-foreground">{post.governance_note}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-xl border bg-muted/30 p-4 text-xs text-muted-foreground flex gap-2" data-testid="pilot-governance-note">
        <ShieldCheck className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
        <div>
          <span className="font-medium text-foreground">Next action:</span> {report.closure?.next_action}
          <div className="mt-1">{report.governance_note}</div>
        </div>
      </div>
    </div>
  );
}
