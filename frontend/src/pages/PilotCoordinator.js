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

  const loadReport = () => api.get("/pilot/mfg-coordinator/readiness-report").then((r) => setReport(r.data)).catch(() => setReport(false));
  useEffect(() => {
    api.get("/pilot/mfg-coordinator").then((r) => setCharter(r.data)).catch(() => {});
    loadReport();
  }, []);

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
