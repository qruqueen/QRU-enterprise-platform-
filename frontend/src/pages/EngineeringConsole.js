import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Terminal, Loader2, RefreshCw, Wrench, Activity } from "lucide-react";

export default function EngineeringConsole() {
  const [ov, setOv] = useState(null);
  const load = () => api.get("/autonomy-engine/overview").then((r) => setOv(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  return (
    <div>
      <PageHeader
        overline="Engineering Console · Not shown to the Founder Beta home"
        title="Engineering Console"
        description="Technical diagnostics for developers — autonomous action log, manufacturing memory, recovery telemetry and factory learning. The Founder dashboard stays clean; this is where the engineering detail lives."
      />

      <div className="flex justify-end mb-3">
        <button onClick={load} data-testid="eng-refresh" className="text-sm inline-flex items-center gap-1.5 border px-3 py-1.5 rounded-sm hover:border-primary">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {!ov ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading diagnostics…</div>
      ) : (
        <div className="space-y-4">
          {/* Factory Learning */}
          {ov.factory_learning && (
            <div className="bg-card border rounded-md p-4" data-testid="eng-learning">
              <p className="font-heading font-semibold text-navy flex items-center gap-2 mb-2"><Wrench className="w-4 h-4 text-royal" /> Recovery & Learning Telemetry</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                <Stat label="Auto-recovery rate" value={`${ov.factory_learning.auto_recovery_rate}%`} />
                <Stat label="Failures learned" value={ov.factory_learning.failures_seen} />
                <Stat label="Auto-recovered" value={ov.factory_learning.auto_recovered} />
                <Stat label="Interruptions prevented" value={ov.factory_learning.founder_interruptions_prevented} />
              </div>
              {ov.factory_learning.common_failures?.length > 0 && (
                <div className="mt-3 text-xs text-muted-foreground">
                  Common failure steps: {ov.factory_learning.common_failures.map((f) => `${f.step} (${f.count})`).join(" · ")}
                </div>
              )}
            </div>
          )}

          {/* Autonomous action log */}
          <div className="bg-card border rounded-md p-4" data-testid="eng-actions">
            <p className="font-heading font-semibold text-navy flex items-center gap-2 mb-2"><Activity className="w-4 h-4 text-royal" /> Autonomous Action Log</p>
            {(ov.recent_actions || []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No autonomous actions recorded yet.</p>
            ) : (
              <div className="font-mono text-[12px] bg-navy/5 rounded-sm p-3 max-h-96 overflow-y-auto space-y-1">
                {ov.recent_actions.map((a, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="text-muted-foreground shrink-0">{String(a.at).slice(0, 19).replace("T", " ")}</span>
                    <span className="text-royal shrink-0">[{a.kind}]</span>
                    <span className="text-navy">{a.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="border rounded-sm p-2">
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="font-heading text-xl font-bold text-navy">{value}</p>
    </div>
  );
}
