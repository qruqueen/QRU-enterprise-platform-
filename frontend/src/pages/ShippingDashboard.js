import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { MetricCard, Panel } from "@/components/qru";
import {
  Loader2, CheckCircle2, Circle, Truck, PackageCheck, Database, ArrowRight, ChevronRight,
} from "lucide-react";

export default function ShippingDashboard() {
  const [data, setData] = useState(null);
  const [env, setEnv] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    api.get("/publishing/shipping-status").then((r) => setData(r.data)).catch(() => setData(false));
    api.get("/publishing/environment").then((r) => setEnv(r.data)).catch(() => {});
  }, []);

  if (data === null) {
    return <div className="flex items-center justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>;
  }
  if (data === false) {
    return <div className="p-8 text-sm text-muted-foreground">Could not load shipping status.</div>;
  }

  return (
    <div className="space-y-6" data-testid="shipping-dashboard">
      <PageHeader
        overline="Universal Distribution Framework™"
        title="Publish Success Dashboard™"
        subtitle="The Factory's definitive shipping status — every stage from Knowledge Record to confirmed customer delivery. Green means truly shipped."
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard icon={PackageCheck} accent="emerald" label="Fully Shipped" value={data.fully_shipped} testid="stat-shipped" />
        <MetricCard icon={Truck} accent="royal" label="In Progress" value={data.in_progress} testid="stat-progress" />
        <MetricCard icon={Circle} accent="navy" label="Total Products" value={data.total_products} testid="stat-total" />
        <MetricCard icon={Database} accent="gold"
          label="Database" value={env ? (env.verdict === "shared_database" ? "Shared" : "Single") : "…"} testid="stat-db" />
      </div>

      {env && (
        <div className="rounded-lg border border-border bg-muted/20 p-3 flex items-start gap-2" data-testid="env-verdict">
          <Database className="w-4 h-4 text-royal mt-0.5 shrink-0" />
          <div>
            <p className="text-[12px] font-bold text-navy">Environment auto-detection</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">{env.explanation}</p>
            <p className="text-[10px] text-muted-foreground mt-1">Known hosts: {env.distinct_hosts.join(", ")} · DB: {env.db_name}</p>
          </div>
        </div>
      )}

      <Panel title="Product Shipping Status" icon={Truck} accent="navy" testid="shipping-table">
        <div className="space-y-2">
          {data.products.map((p) => (
            <button key={p.id} onClick={() => nav(`/book-manufacturing?book=${p.id}`)}
              data-testid={`shipping-row-${p.book_code}`}
              className="w-full text-left border border-border rounded-lg p-3 hover:border-royal/50 transition-colors group">
              <div className="flex items-center justify-between gap-3 mb-2">
                <div className="min-w-0">
                  <p className="text-sm font-bold text-navy truncate">{p.title}</p>
                  <span className="font-mono text-[10px] text-muted-foreground">{p.book_code}</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {p.shipped ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-1"><CheckCircle2 className="w-3.5 h-3.5" /> Shipped</span>
                  ) : (
                    <span className="text-[11px] font-semibold text-amber-700">{p.green}/{p.total} · next: {p.next_action}</span>
                  )}
                  <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-royal" />
                </div>
              </div>
              <div className="flex items-center gap-1 flex-wrap">
                {p.stages.map((s, i) => (
                  <div key={s.stage} className="flex items-center gap-1" title={`${s.stage}: ${s.detail}`}>
                    <span className={`inline-flex items-center gap-1 text-[9.5px] font-semibold rounded-full px-2 py-0.5 border ${s.passed ? "text-emerald-700 bg-emerald-50 border-emerald-200" : "text-muted-foreground bg-muted/40 border-border"}`}>
                      {s.passed ? <CheckCircle2 className="w-2.5 h-2.5" /> : <Circle className="w-2.5 h-2.5" />}
                      {s.stage}
                    </span>
                    {i < p.stages.length - 1 && <ArrowRight className="w-2.5 h-2.5 text-muted-foreground/40" />}
                  </div>
                ))}
              </div>
            </button>
          ))}
        </div>
      </Panel>
    </div>
  );
}
