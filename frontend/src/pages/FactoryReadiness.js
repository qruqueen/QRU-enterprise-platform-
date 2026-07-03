import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Loader2, Gauge, Factory, ClipboardCheck, Rocket, ShoppingCart, Star, Sparkles } from "lucide-react";

const BUCKETS = [
  { key: "ready_to_manufacture", label: "Ready to Manufacture", icon: Factory, hint: "Verified Knowledge Records ready to become products" },
  { key: "ready_for_review", label: "Ready for Review", icon: ClipboardCheck, hint: "In Quality Control or awaiting review" },
  { key: "ready_for_publication", label: "Ready for Publication", icon: Rocket, hint: "Certified + deliverable rendered, awaiting Founder approval" },
  { key: "ready_for_sale", label: "Ready for Sale", icon: ShoppingCart, hint: "Published with a validated customer deliverable" },
];

function scoreColor(s) {
  if (s >= 90) return "hsl(var(--success))";
  if (s >= 75) return "hsl(var(--primary))";
  if (s >= 50) return "hsl(var(--warning))";
  return "hsl(var(--destructive))";
}

export default function FactoryReadiness() {
  const [data, setData] = useState(null);
  const [open, setOpen] = useState(null);

  useEffect(() => { api.get("/readiness/overview").then((r) => setData(r.data)).catch(() => {}); }, []);

  if (!data) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  const { types, dashboard, component_labels } = data;

  return (
    <div className="animate-fade-up" data-testid="factory-readiness-page">
      <PageHeader overline="First Dollar Mode™ · Decision Support" title="Factory Readiness Score™"
        description="Which product should we manufacture first? Scores blend factory capability with live results and improve automatically as capabilities complete. Informational only — this never changes manufacturing, approvals, or publishing." />

      {/* Pipeline buckets */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {BUCKETS.map((b) => {
          const Icon = b.icon;
          return (
            <div key={b.key} className="bg-card border rounded-2xl p-5" data-testid={`bucket-${b.key}`} title={b.hint}>
              <div className="flex items-center gap-2 text-muted-foreground mb-2"><Icon className="w-4 h-4" /><span className="text-xs font-medium">{b.label}</span></div>
              <p className="font-heading text-3xl font-bold text-navy">{dashboard[b.key]}</p>
            </div>
          );
        })}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Highest readiness */}
        <div className="bg-card border rounded-2xl p-5">
          <p className="overline text-primary mb-3 flex items-center gap-1.5"><Star className="w-3.5 h-3.5" /> Highest Readiness Products</p>
          <div className="space-y-2" data-testid="highest-readiness">
            {dashboard.highest_readiness.map((h, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs w-4 text-muted-foreground">{i + 1}</span>
                <span className="text-sm flex-1">{h.product_type}</span>
                <span className="text-sm font-semibold" style={{ color: scoreColor(h.score) }}>{h.score}%</span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t">
            <p className="overline text-gold mb-2 flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> Recommended for First Dollar Mode™</p>
            <div className="flex flex-wrap gap-1.5" data-testid="recommended-types">
              {dashboard.recommended_types.length ? dashboard.recommended_types.map((t) => (
                <span key={t} className="text-xs px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">{t}</span>
              )) : <p className="text-sm text-muted-foreground">None yet — keep manufacturing.</p>}
            </div>
          </div>
        </div>

        {/* Readiness table */}
        <div className="lg:col-span-2 bg-card border rounded-2xl p-5">
          <p className="overline text-primary mb-3 flex items-center gap-1.5"><Gauge className="w-3.5 h-3.5" /> Readiness by Product Type</p>
          <div className="space-y-2" data-testid="readiness-list">
            {types.map((r) => (
              <div key={r.product_type}>
                <button onClick={() => setOpen(open === r.product_type ? null : r.product_type)}
                  className="w-full flex items-center gap-3 text-left" data-testid={`readiness-row-${r.product_type.replace(/\s+/g, "-")}`}>
                  <span className="text-sm w-40 shrink-0 flex items-center gap-1.5">
                    {r.product_type}
                    {r.recommended_for_first_dollar && <Star className="w-3 h-3 text-gold fill-gold" />}
                  </span>
                  <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{ width: `${r.score}%`, background: scoreColor(r.score) }} />
                  </div>
                  <span className="text-sm font-semibold w-12 text-right" style={{ color: scoreColor(r.score) }}>{r.score}%</span>
                </button>
                {open === r.product_type && (
                  <div className="mt-2 mb-3 ml-40 grid sm:grid-cols-2 gap-x-6 gap-y-1" data-testid={`readiness-detail-${r.product_type.replace(/\s+/g, "-")}`}>
                    {Object.entries(r.components).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-[11px]">
                        <span className="text-muted-foreground">{component_labels[k]}</span>
                        <span className="font-medium" style={{ color: scoreColor(v) }}>{v}%</span>
                      </div>
                    ))}
                    <p className="sm:col-span-2 text-[11px] text-muted-foreground mt-1">
                      Live: {r.live.total} made · {r.live.certified} certified · {r.live.published} published · {r.live.delivered} delivered
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
