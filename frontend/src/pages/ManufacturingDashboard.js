import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { MetricCard, Panel, VerifiedBadge } from "@/components/qru";
import { useNavigate } from "react-router-dom";
import {
  Loader2, BookOpenCheck, Package, ListChecks, Plug, UploadCloud, DollarSign, KeyRound,
  Activity, Gauge, ShieldCheck, HeartPulse, AlertTriangle, CheckCircle2, Info, ChevronRight,
} from "lucide-react";

const ALERT_ICON = { warn: AlertTriangle, info: Info, ok: CheckCircle2 };
const ALERT_COLOR = { warn: "text-amber-600", info: "text-royal", ok: "text-emerald-600" };

export default function ManufacturingDashboard() {
  const [d, setD] = useState(null);
  const nav = useNavigate();

  useEffect(() => { api.get("/manufacturing-dashboard").then((r) => setD(r.data)).catch(() => {}); }, []);
  if (!d) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  const HEALTH = {
    "Ready to Publish": "text-emerald-600", "Connected": "text-emerald-600",
    "Needs Authorization": "text-amber-600", "Developer Setup Required": "text-blue-600",
    "Reconnect Required": "text-amber-600", "Connection Expired": "text-amber-600", "Failed": "text-red-600",
  };

  return (
    <div>
      <PageHeader
        overline="QRU Enterprise Manufacturing Dashboard™ · Command Center"
        title="Manufacturing Command Center"
        description="One live view of the entire factory — every number is real and traceable. Click Evidence-backed cards to drill into the underlying records."
        actions={<VerifiedBadge testid="mfg-treasure-badge" />}
      />

      {/* Alerts */}
      <div className="mb-6 space-y-2" data-testid="mfg-alerts">
        {d.alerts.map((a, i) => {
          const Icon = ALERT_ICON[a.level] || Info;
          return (
            <div key={i} onClick={() => a.link && nav(a.link)}
              className={`flex items-center gap-2 text-xs border rounded-md p-3 transition-colors ${a.link ? "cursor-pointer hover:bg-muted/40" : ""} ${a.level === "warn" ? "bg-amber-50 border-amber-200" : a.level === "ok" ? "bg-emerald-50 border-emerald-200" : "bg-muted/40 border-border"}`}>
              <Icon className={`w-4 h-4 shrink-0 ${ALERT_COLOR[a.level]}`} />
              <span className="text-navy flex-1 font-medium">{a.message}</span>
              {a.link && <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />}
            </div>
          );
        })}
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-10" data-testid="mfg-metrics">
        <MetricCard testid="mfg-knowledge" icon={BookOpenCheck} label="Knowledge Records" value={d.knowledge_records.total} sub={`${d.knowledge_records.verified} verified`} provenance={d.knowledge_records.provenance} />
        <MetricCard testid="mfg-products" icon={Package} label="Products Manufactured" value={d.products_manufactured.total} sub={`${d.products_manufactured.published} published`} provenance={d.products_manufactured.provenance} onClick={() => nav("/evidence")} />
        <MetricCard testid="mfg-queue" icon={ListChecks} label="Products In Queue" value={d.products_in_queue.value} sub={`${d.products_in_queue.completed} completed`} provenance={d.products_in_queue.provenance} />
        <MetricCard testid="mfg-quality" icon={Gauge} label="Avg Quality Score" value={d.quality_scores.average} sub={`${d.quality_scores.cleared} cleared · ${d.quality_scores.paused} paused`} provenance={d.quality_scores.provenance} onClick={() => nav("/inspection")} />
        <MetricCard testid="mfg-treasure" icon={ShieldCheck} accent="gold" label="Treasure Standard™ Certified" value={`${d.treasure_standard.certified}/${d.treasure_standard.total}`} provenance={d.treasure_standard.provenance} onClick={() => nav("/inspection")} />
        <MetricCard testid="mfg-connectors" icon={Plug} label="Operational Connectors" value={`${d.connector_status.operational}/${d.connector_status.total}`} provenance={d.connector_status.provenance} onClick={() => nav("/connectors")} />
        <MetricCard testid="mfg-publishing" icon={UploadCloud} label="Published" value={d.publishing_status.published} provenance={d.publishing_status.provenance} onClick={() => nav("/evidence")} />
        <MetricCard testid="mfg-revenue" icon={DollarSign} accent="gold" label="Revenue" value={`$${d.revenue.value.toLocaleString()}`} sub={`${d.revenue.orders} paid orders`} provenance={d.revenue.provenance} onClick={() => nav("/evidence")} />
        <MetricCard testid="mfg-licensing" icon={KeyRound} label="Licensing" value={d.licensing.value} provenance={d.licensing.provenance} />
        <MetricCard testid="mfg-throughput" icon={Activity} label="Throughput (7 days)" value={d.manufacturing_throughput.last_7_days} sub={`${d.manufacturing_throughput.total_orders} orders total`} provenance={d.manufacturing_throughput.provenance} />
      </div>

      {/* Connector health */}
      <Panel title="Connector Health" icon={HeartPulse} accent="gold" testid="mfg-connector-health" className="mb-8">
        <div className="overflow-x-auto -m-5">
          <table className="w-full text-sm">
            <thead className="bg-muted/40"><tr>{["Connector", "Category", "Status", "Account"].map((h) => <th key={h} className="text-left font-bold text-navy px-5 py-2.5 text-[11px] uppercase tracking-wide whitespace-nowrap">{h}</th>)}</tr></thead>
            <tbody>
              {d.connector_health.map((c) => (
                <tr key={c.name} className="border-t border-border hover:bg-muted/30 cursor-pointer transition-colors" onClick={() => nav("/connectors")}>
                  <td className="px-5 py-2.5 text-navy font-medium">{c.name}</td>
                  <td className="px-5 py-2.5 text-xs text-muted-foreground">{c.category}</td>
                  <td className={`px-5 py-2.5 text-xs font-semibold ${HEALTH[c.status] || "text-muted-foreground"}`}>{c.status}</td>
                  <td className="px-5 py-2.5 text-xs text-muted-foreground">{c.account || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
