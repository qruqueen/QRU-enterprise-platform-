import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel } from "@/components/qru";
import { Loader2, Layers, GitBranch, CheckCircle2 } from "lucide-react";

export default function FoundationMap() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/manufacturing/inheritance-map").then(({ data }) => setData(data)).catch(() => setData({ error: true }));
  }, []);

  if (!data) return <div className="p-10 flex justify-center"><Loader2 className="w-7 h-7 animate-spin text-royal" /></div>;

  return (
    <div className="space-y-6" data-testid="foundation-map">
      <PageHeader title="Manufacturing Foundation™" subtitle="Every engine is a Product Manufacturing Standard™ inheriting one shared Foundation — publish, PMF™ and packaging are inherited, not recreated." />

      <Panel className="p-5">
        <p className="flex items-center gap-2 text-xs font-bold text-royal uppercase tracking-wide mb-3">
          <Layers className="w-4 h-4" /> {data.foundation?.name} — shared capabilities inherited by all
        </p>
        <div className="flex flex-wrap gap-2">
          {(data.foundation?.shared_capabilities || []).map((c) => (
            <span key={c} className="text-xs bg-navy/5 text-navy rounded-full px-3 py-1 border border-navy/10">{c}</span>
          ))}
        </div>
        <p className="text-[11px] text-navy/50 mt-3">{data.rule}</p>
      </Panel>

      <div className="grid md:grid-cols-2 gap-4">
        {(data.engines || []).map((e) => (
          <Panel key={e.engine} className="p-4" data-testid={`engine-${e.engine}`}>
            <div className="flex items-center gap-2 mb-2">
              <GitBranch className="w-4 h-4 text-royal" />
              <h3 className="font-bold text-navy text-sm">{e.label}</h3>
              <span className="ml-auto text-[10px] text-navy/50">{e.product_families.length} families</span>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {e.pms.slice(0, 12).map((p) => (
                <span key={p.product_type} className="text-[10px] bg-royal/10 text-royal rounded px-1.5 py-0.5" title={p.auto_provisioned ? "Auto-provisioned PMS inheriting the Foundation" : "Hand-authored PMS"}>
                  {p.family}{p.auto_provisioned ? "" : " ★"}
                </span>
              ))}
              {e.pms.length > 12 && <span className="text-[10px] text-navy/40">+{e.pms.length - 12} more</span>}
            </div>
            <div className="border-t border-navy/10 pt-2">
              <p className="text-[10px] font-semibold text-navy/50 uppercase mb-1">Inherits from Foundation</p>
              <div className="flex flex-wrap gap-1">
                {e.inherits.map((i) => (
                  <span key={i} className="text-[9px] text-emerald-700 inline-flex items-center gap-0.5"><CheckCircle2 className="w-2.5 h-2.5" /> {i}</span>
                ))}
              </div>
            </div>
          </Panel>
        ))}
      </div>
      <p className="text-[10px] text-navy/40">★ = hand-authored Product Manufacturing Standard™. All others are auto-provisioned, inheriting the same Foundation so families never drift apart.</p>
    </div>
  );
}
