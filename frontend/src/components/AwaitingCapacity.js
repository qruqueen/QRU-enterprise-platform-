import { useEffect, useRef, useState } from "react";
import api from "@/lib/api";
import { Loader2, RefreshCw, XCircle, Radio } from "lucide-react";

// MT-003 — Automatic Workflow Resume. When a workflow pauses ONLY because the AI provider
// is temporarily unavailable, this panel monitors capacity and auto-resumes when it returns.
// The Founder can Continue waiting, Retry immediately, or Cancel.
export function AwaitingCapacity({ reason, onResume, onCancel, intervalMs = 20000 }) {
  const [waiting, setWaiting] = useState(true);
  const [checking, setChecking] = useState(false);
  const [countdown, setCountdown] = useState(intervalMs / 1000);
  const [lastReason, setLastReason] = useState(reason);
  const timer = useRef(null);
  const tick = useRef(null);

  const check = async () => {
    setChecking(true);
    try {
      const { data } = await api.get("/continuous/capacity");
      setLastReason(data.reason);
      if (data.available) { stop(); onResume(); }
    } catch { /* keep waiting */ }
    finally { setChecking(false); setCountdown(intervalMs / 1000); }
  };

  const stop = () => { clearInterval(timer.current); clearInterval(tick.current); };

  useEffect(() => {
    if (!waiting) return;
    timer.current = setInterval(check, intervalMs);
    tick.current = setInterval(() => setCountdown((c) => (c > 1 ? c - 1 : intervalMs / 1000)), 1000);
    return stop;
  }, [waiting]);

  return (
    <div className="rounded-md border border-sky-300 bg-sky-50 p-4" data-testid="awaiting-capacity">
      <div className="flex items-start gap-3">
        <Radio className={`w-5 h-5 text-sky-600 shrink-0 ${waiting ? "animate-pulse" : ""}`} />
        <div className="flex-1">
          <p className="font-heading font-semibold text-navy">Waiting for AI provider availability…</p>
          <p className="text-sm text-foreground/70 mt-0.5">{lastReason || "The AI provider is temporarily unavailable. Your completed work is preserved."}</p>
          <p className="text-xs text-muted-foreground mt-1">
            {waiting ? <>Auto-resuming when capacity returns · next check in {countdown}s {checking && <Loader2 className="inline w-3 h-3 animate-spin ml-1" />}</> : "Auto-resume paused."}
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <button data-testid="ac-retry-now" onClick={check} disabled={checking}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm bg-navy text-white hover:bg-navy/90 disabled:opacity-60">
              <RefreshCw className={`w-3.5 h-3.5 ${checking ? "animate-spin" : ""}`} /> Retry immediately
            </button>
            <button data-testid="ac-toggle-wait" onClick={() => setWaiting((w) => !w)}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border border-border hover:border-navy">
              {waiting ? "Pause auto-resume" : "Continue waiting"}
            </button>
            <button data-testid="ac-cancel" onClick={() => { stop(); onCancel(); }}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-sm border border-red-200 text-red-600 hover:bg-red-50">
              <XCircle className="w-3.5 h-3.5" /> Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
