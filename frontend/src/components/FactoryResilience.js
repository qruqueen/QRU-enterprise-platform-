import { useEffect, useState } from "react";
import api from "@/lib/api";
import { ShieldCheck, CircleCheck, CircleSlash, Cpu, Layers } from "lucide-react";

const MODE_META = {
  deterministic: { label: "Deterministic", cls: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  hybrid: { label: "Hybrid", cls: "text-sky-700 bg-sky-50 border-sky-200" },
  ai: { label: "AI-required", cls: "text-amber-700 bg-amber-50 border-amber-200" },
};

export function FactoryResilience() {
  const [d, setD] = useState(null);
  useEffect(() => { api.get("/continuous/resilience").then(({ data }) => setD(data)).catch(() => {}); }, []);
  if (!d) return null;

  return (
    <div className="rounded-xl border border-border bg-card p-5 mb-8" data-testid="factory-resilience">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-gold" />
          <h3 className="font-heading font-semibold text-navy">Factory Resilience™</h3>
        </div>
        <span className="text-sm text-muted-foreground">{d.runnable_now}/{d.total} workflows runnable now</span>
      </div>
      <p className="text-xs text-muted-foreground mt-1">{d.message}</p>
      <div className="grid sm:grid-cols-2 gap-2 mt-3">
        {d.workflows.map((w, i) => {
          const m = MODE_META[w.mode] || MODE_META.hybrid;
          return (
            <div key={i} className="flex items-center gap-2 rounded-sm border border-border p-2.5" data-testid={`resilience-wf-${i}`}>
              {w.available ? <CircleCheck className="w-4 h-4 text-emerald-600 shrink-0" /> : <CircleSlash className="w-4 h-4 text-amber-500 shrink-0" />}
              <div className="min-w-0 flex-1">
                <p className="text-sm text-navy truncate">{w.name}</p>
                {w.note && <p className="text-[10px] text-muted-foreground truncate">{w.note}</p>}
              </div>
              <span className={`text-[9px] px-1.5 py-0.5 rounded-full border shrink-0 ${m.cls}`}>{m.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
