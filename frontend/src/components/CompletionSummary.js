import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { CheckCircle2, AlertTriangle, Loader2, Clock, Timer, DollarSign, Package, ArrowRight } from "lucide-react";

// Factory Completion Standard™ — a single standardized summary shown after ANY
// successful QRU workflow. Data-driven and reusable across every department.
function fmtDuration(ms) {
  if (ms == null) return "—";
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return `${m}m ${s % 60}s`;
}

export function CompletionSummary({ open, onOpenChange, data }) {
  const navigate = useNavigate();
  if (!data) return null;

  const warning = data.status === "warning";
  const finalizing = !!data.finalizing;

  const doAction = (a) => {
    if (a.onClick) a.onClick();
    if (a.to) { onOpenChange(false); navigate(a.to); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg" data-testid="completion-summary">
        <DialogHeader>
          <div className={`flex items-center gap-2 ${warning ? "text-amber-600" : "text-emerald-600"}`}>
            {finalizing ? <Loader2 className="w-6 h-6 animate-spin" /> : warning ? <AlertTriangle className="w-6 h-6" /> : <CheckCircle2 className="w-6 h-6" />}
            <span className="text-xs font-semibold tracking-widest uppercase">
              {finalizing ? "Finalizing output…" : warning ? "Completed with Warnings" : "Completed Successfully"}
            </span>
          </div>
          <DialogTitle className="font-heading text-2xl text-navy mt-1" data-testid="completion-workflow-name">{data.workflowName}</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-3 mt-1">
          <div className="rounded-sm bg-muted/40 p-2.5 flex items-center gap-2"><Clock className="w-4 h-4 text-muted-foreground" /><div><p className="text-[10px] text-muted-foreground uppercase">Completed</p><p className="text-sm font-medium text-navy">{data.timeCompleted ? new Date(data.timeCompleted).toLocaleTimeString() : "Just now"}</p></div></div>
          <div className="rounded-sm bg-muted/40 p-2.5 flex items-center gap-2"><Timer className="w-4 h-4 text-muted-foreground" /><div><p className="text-[10px] text-muted-foreground uppercase">Duration</p><p className="text-sm font-medium text-navy">{fmtDuration(data.durationMs)}</p></div></div>
          <div className="rounded-sm bg-muted/40 p-2.5 flex items-center gap-2"><DollarSign className="w-4 h-4 text-muted-foreground" /><div><p className="text-[10px] text-muted-foreground uppercase">Est. Cost</p><p className="text-sm font-medium text-navy">{data.estimatedCost != null ? `$${Number(data.estimatedCost).toFixed(3)}` : "—"}<span className="text-[9px] text-muted-foreground ml-1">est.</span></p></div></div>
          <div className="rounded-sm bg-muted/40 p-2.5 flex items-center gap-2"><Package className="w-4 h-4 text-muted-foreground" /><div><p className="text-[10px] text-muted-foreground uppercase">Status</p><p className="text-sm font-medium text-navy">{warning ? "With warnings" : "Success"}</p></div></div>
        </div>

        {data.assets?.length > 0 && (
          <div className="mt-2">
            <p className="text-[11px] font-semibold text-gold uppercase tracking-wide mb-1">Products / Assets Created</p>
            <div className="space-y-1">
              {data.assets.map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-sm text-foreground/80" data-testid="completion-asset">
                  <Package className="w-3.5 h-3.5 text-muted-foreground" /> {a.label}{a.sub ? <span className="text-xs text-muted-foreground">· {a.sub}</span> : null}
                </div>
              ))}
            </div>
          </div>
        )}

        {warning && data.warnings?.length > 0 && (
          <div className="mt-2 rounded-sm bg-amber-50 border border-amber-200 p-3" data-testid="completion-warnings">
            <p className="text-sm font-medium text-amber-800">Warnings</p>
            <ul className="list-disc pl-4 text-sm text-amber-700 mt-1">{data.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
            {data.recommendedAction && <p className="text-xs text-amber-800 mt-2"><span className="font-semibold">Recommended:</span> {data.recommendedAction}</p>}
          </div>
        )}

        {finalizing && (
          <div className="mt-2 rounded-sm bg-navy/5 p-3 text-sm text-foreground/70 flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Background processing in progress — this will refresh automatically.
          </div>
        )}

        {!finalizing && data.actions?.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {data.actions.map((a, i) => (
              <button key={i} data-testid={a.testid || `completion-action-${i}`} onClick={() => doAction(a)}
                className={`inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm transition-colors ${a.primary ? "bg-primary text-primary-foreground hover:bg-primary/90" : "border border-border hover:border-navy text-navy"}`}>
                {a.label} {a.to && <ArrowRight className="w-3.5 h-3.5" />}
              </button>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
