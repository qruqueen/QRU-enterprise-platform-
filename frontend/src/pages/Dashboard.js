import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, StatusBadge } from "@/components/shared";
import {
  BookOpen, Factory, Library, Bot, ShieldCheck, Users, ArrowUpRight, Activity,
} from "lucide-react";

const WORKFLOW = [
  "Idea", "Research", "Evidence", "Verification", "Knowledge Record",
  "Translation", "Manufacturing Order", "AI Collaboration", "Manufacturing",
  "Quality Review", "Approval", "Publication", "Delivery", "Improvement",
];

const PIPELINE_STAGES = ["Queued", "Research", "Manufacturing", "Quality Review", "Approved", "Published"];

function Stat({ icon: Icon, label, value, sub, to, testid }) {
  return (
    <Link
      to={to}
      data-testid={testid}
      className="group bg-card border rounded-md p-5 hover:-translate-y-1 hover:shadow-sm transition-all"
    >
      <div className="flex items-start justify-between">
        <div className="w-9 h-9 rounded-sm bg-primary/10 text-primary flex items-center justify-center">
          <Icon className="w-5 h-5" />
        </div>
        <ArrowUpRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
      <p className="font-heading text-3xl font-bold mt-4 tracking-tight">{value}</p>
      <p className="text-sm text-muted-foreground">{label}</p>
      {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
    </Link>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get("/dashboard/stats").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  const s = stats || {};
  const pipeline = s.pipeline || {};

  return (
    <div>
      <PageHeader
        overline="Executive Command Center"
        title="Enterprise Overview"
        description="Knowledge enters the system. Understanding leaves the system. Monitor the full manufacturing pipeline in real time."
        actions={
          <Link to="/command" data-testid="dashboard-command-cta" className="bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
            Open Command Console
          </Link>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat icon={BookOpen} label="Knowledge Records" value={s.knowledge_records ?? "—"} sub={`${s.verified_records ?? 0} verified`} to="/knowledge" testid="stat-knowledge" />
        <Stat icon={Factory} label="Manufacturing Orders" value={s.manufacturing_orders ?? "—"} sub={`${s.active_orders ?? 0} active`} to="/manufacturing" testid="stat-orders" />
        <Stat icon={Library} label="Products" value={s.products ?? "—"} sub={`${s.published_products ?? 0} published`} to="/products" testid="stat-products" />
        <Stat icon={Bot} label="Digital Workforce" value={s.digital_employees ?? "—"} sub="AI employees active" to="/workforce" testid="stat-workforce" />
      </div>

      {/* Pipeline */}
      <div className="mt-8 bg-card border rounded-md p-6">
        <div className="flex items-center gap-2 mb-5">
          <Activity className="w-4 h-4 text-primary" />
          <h2 className="font-heading font-semibold text-lg">Manufacturing Pipeline</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {PIPELINE_STAGES.map((stage) => (
            <div key={stage} data-testid={`pipeline-${stage.toLowerCase().replace(/\s/g, "-")}`} className="border rounded-sm p-4 bg-muted/40">
              <p className="font-heading text-2xl font-bold">{pipeline[stage] || 0}</p>
              <p className="text-xs text-muted-foreground mt-1">{stage}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-8 grid lg:grid-cols-3 gap-6">
        {/* Workflow visualization */}
        <div className="lg:col-span-2 bg-card border rounded-md p-6">
          <h2 className="font-heading font-semibold text-lg mb-1">Primary Enterprise Workflow</h2>
          <p className="text-sm text-muted-foreground mb-5">The path from confusion to understanding.</p>
          <div className="flex flex-wrap gap-2">
            {WORKFLOW.map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <span className="inline-flex items-center gap-2 border rounded-sm px-3 py-1.5 text-xs font-medium bg-muted/40">
                  <span className="text-primary font-heading font-bold">{String(i + 1).padStart(2, "0")}</span>
                  {step}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Activity */}
        <div className="bg-card border rounded-md p-6">
          <h2 className="font-heading font-semibold text-lg mb-4">Recent Activity</h2>
          <div className="space-y-3">
            {(s.recent_activity || []).length === 0 && (
              <p className="text-sm text-muted-foreground">No recent activity yet.</p>
            )}
            {(s.recent_activity || []).map((a) => (
              <div key={a.id} className="flex items-start gap-3 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                <div>
                  <span className="font-medium">{a.actor}</span>{" "}
                  <span className="text-muted-foreground">{a.action}</span>{" "}
                  <span className="text-foreground">{a.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
