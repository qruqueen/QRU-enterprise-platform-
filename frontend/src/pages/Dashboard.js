import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  BookOpen, Factory, Library, Bot, ShieldCheck, TrendingUp, Activity, ArrowUpRight,
  Gem, DollarSign, Sparkles, Users,
} from "lucide-react";

const WORKFLOW = [
  "Idea", "Research", "Knowledge Record", "Verification", "Master File",
  "Manufacturing Order", "Product Recipe", "AI Manufacturing", "Quality Inspection",
  "Publication", "Marketplace", "Customer Feedback", "Improvement",
];
const PIPELINE_STAGES = ["Queued", "Research", "Manufacturing", "Quality Review", "Approved", "Published"];

function Stat({ icon: Icon, label, value, sub, to, testid, gold }) {
  return (
    <Link to={to} data-testid={testid}
      className="group bg-card border rounded-md p-5 hover:-translate-y-1 hover:shadow-sm transition-all">
      <div className="flex items-start justify-between">
        <div className={`w-9 h-9 rounded-sm flex items-center justify-center ${gold ? "bg-gold/15 text-gold" : "bg-primary/10 text-primary"}`}>
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
  const [s, setS] = useState({});
  useEffect(() => { api.get("/dashboard/stats").then((r) => setS(r.data)).catch(() => {}); }, []);
  const pipeline = s.pipeline || {};

  return (
    <div>
      <PageHeader
        overline="Executive Command Center"
        title="Enterprise Overview"
        description="Knowledge enters the system. Understanding leaves the system. QRU simplifies the path to understanding the truth."
        actions={
          <Link to="/command" data-testid="dashboard-command-cta" className="bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
            Open Command Console
          </Link>
        }
      />

      {/* Enterprise Health + Revenue banner */}
      <div className="grid md:grid-cols-3 gap-4 mb-4">
        <div className="rounded-md p-5 text-white md:col-span-2 flex items-center justify-between" style={{ background: "hsl(var(--navy))" }}>
          <div>
            <p className="overline text-gold mb-1">Enterprise Health</p>
            <p className="font-heading text-4xl font-bold">{s.enterprise_health ?? "—"}%</p>
            <p className="text-white/60 text-sm mt-1">Composite of verification, publication & workforce activity</p>
          </div>
          <div className="text-right">
            <p className="overline text-gold mb-1">Revenue</p>
            <p className="font-heading text-3xl font-bold text-gold">${(s.revenue ?? 0).toLocaleString()}</p>
          </div>
        </div>
        <div className="rounded-md p-5 border bg-card flex flex-col justify-center">
          <div className="flex items-center gap-2"><Gem className="w-4 h-4 text-gold" /><p className="overline text-primary">Treasure Standard™</p></div>
          <p className="font-heading text-3xl font-bold mt-2">{s.treasure_standard ?? 0}</p>
          <p className="text-xs text-muted-foreground">records at the QRU gold standard</p>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat icon={BookOpen} label="Knowledge Records" value={s.knowledge_records ?? "—"} sub={`${s.verified_records ?? 0} verified · ${s.master_files ?? 0} master files`} to="/knowledge" testid="stat-knowledge" />
        <Stat icon={ShieldCheck} label="Verification Queue" value={s.verification_queue ?? "—"} sub="awaiting the Verification Lion™" to="/verification" testid="stat-verification" gold />
        <Stat icon={Factory} label="Manufacturing Orders" value={s.manufacturing_orders ?? "—"} sub={`${s.active_orders ?? 0} active`} to="/manufacturing" testid="stat-orders" />
        <Stat icon={Library} label="Products" value={s.products ?? "—"} sub={`${s.published_products ?? 0} published`} to="/products" testid="stat-products" />
        <Stat icon={Bot} label="Digital Workforce" value={s.digital_employees ?? "—"} sub={`${s.digital_employees_active ?? 0} active`} to="/workforce" testid="stat-workforce" />
        <Stat icon={TrendingUp} label="Marketplace Ops" value={s.marketplace_opportunities ?? "—"} sub="verified topics not yet productized" to="/analytics" testid="stat-marketplace" gold />
        <Stat icon={Users} label="Customers" value={s.customers ?? "—"} sub="institutions & individuals" to="/customers" testid="stat-customers" />
        <Stat icon={Sparkles} label="Translation Engine™" value="Live" sub="manufacture understanding" to="/translation-engine" testid="stat-engine" gold />
      </div>

      {/* Pipeline */}
      <div className="mt-8 bg-card border rounded-md p-6">
        <div className="flex items-center gap-2 mb-5"><Activity className="w-4 h-4 text-primary" /><h2 className="font-heading font-semibold text-lg">Manufacturing Pipeline</h2></div>
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
        <div className="lg:col-span-2 bg-card border rounded-md p-6">
          <h2 className="font-heading font-semibold text-lg mb-1">The QRU Manufacturing Workflow</h2>
          <p className="text-sm text-muted-foreground mb-5">From idea to continuous improvement — governed at every step.</p>
          <div className="flex flex-wrap gap-2">
            {WORKFLOW.map((step, i) => (
              <span key={step} className="inline-flex items-center gap-2 border rounded-sm px-3 py-1.5 text-xs font-medium bg-muted/40">
                <span className="text-gold font-heading font-bold">{String(i + 1).padStart(2, "0")}</span>{step}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-card border rounded-md p-6">
          <h2 className="font-heading font-semibold text-lg mb-4">Recent Activity</h2>
          <div className="space-y-3">
            {(s.recent_activity || []).length === 0 && <p className="text-sm text-muted-foreground">No recent activity yet.</p>}
            {(s.recent_activity || []).map((a) => (
              <div key={a.id} className="flex items-start gap-3 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-gold mt-2 shrink-0" />
                <div><span className="font-medium">{a.actor}</span> <span className="text-muted-foreground">{a.action}</span> <span>{a.detail}</span></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
