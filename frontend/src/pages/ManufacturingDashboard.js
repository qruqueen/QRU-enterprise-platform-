import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { useNavigate } from "react-router-dom";
import {
  Loader2, BookOpenCheck, Package, ListChecks, Plug, UploadCloud, DollarSign, KeyRound,
  Activity, Gauge, ShieldCheck, HeartPulse, AlertTriangle, CheckCircle2, Info, ChevronRight,
} from "lucide-react";

const PROV = {
  LIVE: "bg-emerald-50 text-emerald-700 border-emerald-200",
  TEST: "bg-amber-50 text-amber-700 border-amber-200",
  NOT_TRACKED: "bg-slate-100 text-slate-500 border-slate-200",
};
const PROV_LABEL = { LIVE: "LIVE", TEST: "TEST", NOT_TRACKED: "NOT TRACKED YET", SIMULATED: "SIMULATED" };
const ALERT_ICON = { warn: AlertTriangle, info: Info, ok: CheckCircle2 };
const ALERT_COLOR = { warn: "text-amber-600", info: "text-royal", ok: "text-emerald-600" };

function Metric({ icon: Icon, label, value, sub, provenance, onClick, testid }) {
  return (
    <button onClick={onClick} disabled={!onClick} data-testid={testid}
      className={`text-left bg-card border border-border rounded-xl p-4 ${onClick ? "hover:border-primary hover:shadow-sm" : ""} transition-colors`}>
      <div className="flex items-center justify-between mb-2">
        <Icon className="w-4 h-4 text-royal" />
        {provenance && <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${PROV[provenance] || PROV.NOT_TRACKED}`}>{PROV_LABEL[provenance]}</span>}
      </div>
      <p className="font-heading text-2xl font-bold text-navy">{value}</p>
      <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">{label}</p>
      {sub && <p className="text-[10px] text-muted-foreground mt-1">{sub}</p>}
    </button>
  );
}

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
      />

      {/* Alerts */}
      <div className="mb-6 space-y-2" data-testid="mfg-alerts">
        {d.alerts.map((a, i) => {
          const Icon = ALERT_ICON[a.level] || Info;
          return (
            <div key={i} onClick={() => a.link && nav(a.link)}
              className={`flex items-center gap-2 text-xs border rounded-lg p-2.5 ${a.link ? "cursor-pointer hover:bg-muted/40" : ""} ${a.level === "warn" ? "bg-amber-50 border-amber-200" : a.level === "ok" ? "bg-emerald-50 border-emerald-200" : "bg-muted/40 border-border"}`}>
              <Icon className={`w-4 h-4 shrink-0 ${ALERT_COLOR[a.level]}`} />
              <span className="text-navy flex-1">{a.message}</span>
              {a.link && <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />}
            </div>
          );
        })}
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-8" data-testid="mfg-metrics">
        <Metric testid="mfg-knowledge" icon={BookOpenCheck} label="Knowledge Records" value={d.knowledge_records.total} sub={`${d.knowledge_records.verified} verified`} provenance={d.knowledge_records.provenance} />
        <Metric testid="mfg-products" icon={Package} label="Products Manufactured" value={d.products_manufactured.total} sub={`${d.products_manufactured.published} published`} provenance={d.products_manufactured.provenance} onClick={() => nav("/evidence")} />
        <Metric testid="mfg-queue" icon={ListChecks} label="Products In Queue" value={d.products_in_queue.value} sub={`${d.products_in_queue.completed} completed`} provenance={d.products_in_queue.provenance} />
        <Metric testid="mfg-quality" icon={Gauge} label="Avg Quality Score" value={d.quality_scores.average} sub={`${d.quality_scores.cleared} cleared · ${d.quality_scores.paused} paused`} provenance={d.quality_scores.provenance} onClick={() => nav("/inspection")} />
        <Metric testid="mfg-treasure" icon={ShieldCheck} label="Treasure Standard™ Certified" value={`${d.treasure_standard.certified}/${d.treasure_standard.total}`} provenance={d.treasure_standard.provenance} onClick={() => nav("/inspection")} />
        <Metric testid="mfg-connectors" icon={Plug} label="Operational Connectors" value={`${d.connector_status.operational}/${d.connector_status.total}`} provenance={d.connector_status.provenance} onClick={() => nav("/connectors")} />
        <Metric testid="mfg-publishing" icon={UploadCloud} label="Published" value={d.publishing_status.published} provenance={d.publishing_status.provenance} onClick={() => nav("/evidence")} />
        <Metric testid="mfg-revenue" icon={DollarSign} label="Revenue" value={`$${d.revenue.value.toLocaleString()}`} sub={`${d.revenue.orders} paid orders`} provenance={d.revenue.provenance} onClick={() => nav("/evidence")} />
        <Metric testid="mfg-licensing" icon={KeyRound} label="Licensing" value={d.licensing.value} provenance={d.licensing.provenance} />
        <Metric testid="mfg-throughput" icon={Activity} label="Throughput (7 days)" value={d.manufacturing_throughput.last_7_days} sub={`${d.manufacturing_throughput.total_orders} orders total`} provenance={d.manufacturing_throughput.provenance} />
      </div>

      {/* Connector health */}
      <p className="overline text-primary mb-3 flex items-center gap-1.5"><HeartPulse className="w-3.5 h-3.5" /> Connector Health</p>
      <div className="bg-card border rounded-xl overflow-hidden mb-8" data-testid="mfg-connector-health">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50"><tr>{["Connector", "Category", "Status", "Account"].map((h) => <th key={h} className="text-left font-semibold text-navy px-3 py-2 text-xs whitespace-nowrap">{h}</th>)}</tr></thead>
            <tbody>
              {d.connector_health.map((c) => (
                <tr key={c.name} className="border-t hover:bg-muted/30 cursor-pointer" onClick={() => nav("/connectors")}>
                  <td className="px-3 py-2 text-navy">{c.name}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">{c.category}</td>
                  <td className={`px-3 py-2 text-xs font-medium ${HEALTH[c.status] || "text-muted-foreground"}`}>{c.status}</td>
                  <td className="px-3 py-2 text-xs text-muted-foreground">{c.account || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
