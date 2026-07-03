import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Link } from "react-router-dom";
import { Activity, BookOpen, Factory, Cpu, Plug, Store, BarChart3, AlertTriangle, CheckCircle2 } from "lucide-react";

const ICONS = { knowledge: BookOpen, manufacturing: Factory, ai_services: Cpu, integration: Plug, commerce: Store, analytics: BarChart3 };
const LINKS = { knowledge: "/knowledge", manufacturing: "/manufacturing", ai_services: "/ai-services", integration: "/integration-hub", commerce: "/product-protection", analytics: "/analytics" };

export default function EnterpriseCommandCenter() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const load = () => api.get("/enterprise/command-center").then((r) => setData(r.data));
    load();
    const iv = setInterval(load, 15000);
    return () => clearInterval(iv);
  }, []);

  if (!data) return <div className="p-8 text-sm text-muted-foreground">Loading Enterprise Command Center™…</div>;

  const healthy = data.factory_health === "healthy";

  return (
    <div className="space-y-8" data-testid="command-center-page">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <p className="overline text-primary mb-1">Founder Dashboard</p>
          <h1 className="font-heading text-3xl font-bold tracking-tight">Enterprise Command Center™</h1>
          <p className="text-muted-foreground text-sm mt-1">Visibility across every Enterprise Operating Division™. Routine work runs autonomously.</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium ${healthy ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`} data-testid="factory-health">
          {healthy ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
          Factory Health: {data.factory_health}
        </div>
      </div>

      {data.exceptions > 0 && (
        <Link to="/verification-team" className="block bg-amber-50 border border-amber-200 rounded-sm p-3 text-sm text-amber-800" data-testid="cc-exceptions">
          <AlertTriangle className="w-4 h-4 inline mr-1" /> {data.exceptions} open exception(s) awaiting Founder review →
        </Link>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.divisions.map((d) => {
          const Icon = ICONS[d.key] || Activity;
          return (
            <Link key={d.key} to={LINKS[d.key] || "/"} className="bg-card border rounded-sm p-5 hover:shadow-md transition-shadow" data-testid={`division-${d.key}`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2"><Icon className="w-5 h-5 text-primary" /><h3 className="font-heading font-semibold text-sm">{d.name}</h3></div>
                <span className={`w-2 h-2 rounded-full ${d.health === "warning" ? "bg-amber-500" : d.health === "active" ? "bg-blue-500" : "bg-emerald-500"}`} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(d.metrics).map(([k, v]) => (
                  <div key={k}><p className="text-xl font-heading font-bold">{v}</p><p className="text-[11px] text-muted-foreground">{k}</p></div>
                ))}
              </div>
            </Link>
          );
        })}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-card border rounded-sm p-5">
          <h3 className="font-heading font-semibold text-sm mb-3">Product Portfolio</h3>
          <div className="grid grid-cols-3 gap-3">
            <div><p className="text-2xl font-heading font-bold">{data.portfolio.products}</p><p className="text-xs text-muted-foreground">Products</p></div>
            <div><p className="text-2xl font-heading font-bold">{data.portfolio.published}</p><p className="text-xs text-muted-foreground">Published</p></div>
            <div><p className="text-2xl font-heading font-bold">{data.portfolio.protected}</p><p className="text-xs text-muted-foreground">Protected</p></div>
          </div>
        </div>
        <div className="bg-card border rounded-sm p-5">
          <h3 className="font-heading font-semibold text-sm mb-2">Revenue</h3>
          <p className="text-sm text-muted-foreground">{data.revenue.note}</p>
          <p className="text-xs text-muted-foreground mt-2">Licenses granted: {data.revenue.licenses_granted}</p>
          <Link to="/integration-hub" className="text-xs text-primary underline mt-2 inline-block">Connect a payment provider →</Link>
        </div>
      </div>
    </div>
  );
}
