import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import {
  Factory, Inbox, AlertTriangle, CheckCircle2, Rocket, ArrowRight, Loader2, Power,
} from "lucide-react";

const CARDS = [
  { key: "q1_doing", q: "What is the factory doing?", icon: Factory, tone: "royal", route: "/autonomy" },
  { key: "q2_waiting", q: "What is waiting for me?", icon: Inbox, tone: "gold", route: "/founder-inbox" },
  { key: "q3_blocked", q: "What is blocked?", icon: AlertTriangle, tone: "red", route: "/founder-inbox" },
  { key: "q4_finished_today", q: "What finished today?", icon: CheckCircle2, tone: "emerald", route: "/factory-health" },
  { key: "q5_publish_readiness", q: "How close are we to publishing?", icon: Rocket, tone: "navy", route: "/founder-inbox" },
];

const TONE = {
  royal: "border-royal/30", gold: "border-gold/40", red: "border-red-200",
  emerald: "border-emerald-200", navy: "border-navy/20",
};

export default function FounderBetaDashboard() {
  const nav = useNavigate();
  const [d, setD] = useState(null);
  const load = () => api.get("/autonomy-engine/founder-beta").then((r) => setD(r.data)).catch(() => {});
  useEffect(() => { load(); const t = setInterval(load, 25000); return () => clearInterval(t); }, []);

  if (!d) return (
    <div className="rounded-2xl border p-6 mb-8 flex items-center gap-2 text-sm text-muted-foreground" data-testid="beta-loading">
      <Loader2 className="w-4 h-4 animate-spin" /> Loading your factory status…
    </div>
  );

  const count = (c) => c.key === "q4_finished_today" ? d[c.key].count : (c.key === "q5_publish_readiness" ? d[c.key].ready_to_publish : d[c.key].count);

  return (
    <div className="mb-8" data-testid="founder-beta-dashboard">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-gold/20 text-royal" data-testid="beta-badge">FOUNDER BETA™</span>
        <h2 className="font-heading text-lg font-bold text-navy">Your Factory at a Glance</h2>
        <span className={`ml-auto text-[11px] px-2 py-0.5 rounded-full inline-flex items-center gap-1 ${d.autonomy_on ? "bg-emerald-50 text-emerald-700" : "bg-muted text-muted-foreground"}`}>
          <Power className="w-3 h-3" /> Autonomy {d.autonomy_on ? "ON" : "OFF"}
        </span>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {CARDS.map((c) => {
          const block = d[c.key];
          return (
            <button key={c.key} data-testid={`beta-card-${c.key}`} onClick={() => nav(c.route)}
              className={`text-left bg-card border rounded-xl p-4 hover:shadow-md transition-shadow ${TONE[c.tone]}`}>
              <div className="flex items-center gap-2 mb-2">
                <c.icon className={`w-4 h-4 ${c.tone === "gold" ? "text-gold" : c.tone === "red" ? "text-red-500" : c.tone === "emerald" ? "text-emerald-600" : "text-royal"}`} />
                <p className="text-[11px] text-muted-foreground leading-tight">{c.q}</p>
              </div>
              <p className="font-heading text-3xl font-bold text-navy">{count(c)}{c.key === "q5_publish_readiness" && <span className="text-sm text-muted-foreground font-normal"> ready</span>}</p>
              <p className="text-[12px] text-navy mt-1 leading-snug">{block.headline}</p>
              {c.key === "q5_publish_readiness" && (
                <div className="mt-2 h-1.5 w-full bg-muted rounded-full overflow-hidden"><div className="h-full bg-royal" style={{ width: `${block.avg_progress_pct}%` }} /></div>
              )}
              <span className="text-[11px] text-royal mt-2 inline-flex items-center gap-1">Open <ArrowRight className="w-3 h-3" /></span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
