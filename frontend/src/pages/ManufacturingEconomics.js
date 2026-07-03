import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, Cpu, DollarSign, TrendingUp, PiggyBank, FileDown, FileSpreadsheet,
  Sparkles, Zap, Star,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const TIER_COLOR = { high: "text-red-600", medium: "text-amber-600", free: "text-emerald-600" };

const Stat = ({ icon: Icon, label, value, sub, testid }) => (
  <div className="bg-card border rounded-2xl p-5" data-testid={testid}>
    <div className="flex items-center gap-2 text-muted-foreground mb-2"><Icon className="w-4 h-4" /><span className="text-xs font-medium">{label}</span></div>
    <p className="font-heading text-3xl font-bold text-navy">{value}</p>
    {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
  </div>
);

export default function ManufacturingEconomics() {
  const [data, setData] = useState(null);

  useEffect(() => { api.get("/economics/overview").then((r) => setData(r.data)).catch(() => {}); }, []);
  if (!data) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  const ai = data.ai_dashboard || {};
  const s = data.summary;
  const dl = (fmt) => window.open(`${BACKEND}/api/economics/export/${fmt}`, "_blank");
  const money = (n) => `$${Number(n || 0).toFixed(2)}`;

  return (
    <div className="animate-fade-up" data-testid="economics-page">
      <PageHeader overline="Founder Decision Support · Informational Only" title="Manufacturing Economics™"
        description="What does each product cost to manufacture, what should you charge, and which are the most profitable to make first? All figures are estimated — this changes no factory behavior."
        actions={<div className="flex gap-2">
          <button data-testid="economics-export-pdf" onClick={() => dl("pdf")} className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border hover:border-primary"><FileDown className="w-4 h-4" /> PDF</button>
          <button data-testid="economics-export-csv" onClick={() => dl("csv")} className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border hover:border-primary"><FileSpreadsheet className="w-4 h-4" /> Spreadsheet</button>
        </div>} />

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Stat icon={DollarSign} label="Avg Cost / Product" value={money(s.avg_manufacturing_cost)} sub="Estimated AI + rendering" testid="stat-avg-cost" />
        <Stat icon={TrendingUp} label="Avg Gross Margin" value={`${s.avg_gross_margin_pct}%`} sub="After processing fees" testid="stat-avg-margin" />
        <Stat icon={PiggyBank} label="Total Reuse Savings" value={money(s.total_reuse_savings)} sub="Avoided via reuse & deterministic rendering" testid="stat-savings" />
        <Stat icon={Cpu} label="Est. AI Spend Today" value={money(ai?.budget?.spent_today)} sub={`Budget ${money(ai?.budget?.daily_budget_usd)}`} testid="stat-ai-today" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        {/* AI Cost Dashboard */}
        <div className="bg-card border rounded-2xl p-5">
          <p className="overline text-primary mb-3 flex items-center gap-1.5"><Cpu className="w-3.5 h-3.5" /> AI Cost Dashboard</p>
          <div className="space-y-1.5 text-sm" data-testid="ai-dashboard">
            <Line k="Provider" v={ai?.provider || "OpenAI / Gemini (Emergent Universal Key)"} />
            <Line k="Text model" v={ai?.model || "GPT (via Universal Key)"} />
            <Line k="Est. spend — today" v={money(ai?.daily?.total)} />
            <Line k="Est. spend — week" v={money(ai?.weekly_total)} />
            <Line k="Est. spend — month" v={money(ai?.monthly_total)} />
            {ai?.daily?.by_service && Object.entries(ai.daily.by_service).map(([k, v]) => (
              <Line key={k} k={`· ${k}`} v={`${v.calls} calls · ${money(v.est_cost)}`} muted />
            ))}
          </div>
        </div>

        {/* Credit consumption */}
        <div className="bg-card border rounded-2xl p-5">
          <p className="overline text-primary mb-3 flex items-center gap-1.5"><Zap className="w-3.5 h-3.5" /> What Consumes Credits</p>
          <div className="space-y-2" data-testid="credit-consumption">
            {data.credit_consumption.map((c, i) => (
              <div key={i} className="text-sm">
                <div className="flex justify-between">
                  <span className={TIER_COLOR[c.tier]}>{c.operation}</span>
                  <span className="text-muted-foreground">{c.unit_cost ? `~$${c.unit_cost}/call` : "free"}</span>
                </div>
                <p className="text-[11px] text-muted-foreground">{c.note}</p>
              </div>
            ))}
          </div>
        </div>

        {/* First Dollar recommendations */}
        <div className="bg-card border rounded-2xl p-5">
          <p className="overline text-gold mb-3 flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> First Dollar Mode™ — Make These First</p>
          <p className="text-[11px] text-muted-foreground mb-2">Highest margin, lowest cost, ready to sell.</p>
          <div className="space-y-2" data-testid="economics-recommendations">
            {data.recommendations.length ? data.recommendations.map((r) => (
              <div key={r.id} className="flex items-center gap-2 text-sm">
                <Star className="w-3.5 h-3.5 text-gold fill-gold shrink-0" />
                <span className="flex-1 truncate">{r.title}</span>
                <span className="text-emerald-600 font-semibold">{r.gross_margin_pct}%</span>
              </div>
            )) : <p className="text-sm text-muted-foreground">No sellable products yet.</p>}
          </div>
        </div>
      </div>

      {/* Product economics table */}
      <div className="bg-card border rounded-2xl p-5">
        <p className="overline text-primary mb-3 flex items-center gap-1.5"><DollarSign className="w-3.5 h-3.5" /> Product Manufacturing Economics</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="economics-table">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b">
                <th className="py-2 pr-3">Product</th><th className="pr-3">Type</th>
                <th className="pr-3 text-right">Mfg Cost</th><th className="pr-3 text-right">Price</th>
                <th className="pr-3 text-right">Fees</th><th className="pr-3 text-right">Gross Profit</th>
                <th className="pr-3 text-right">Margin</th><th className="pr-3 text-right">Reuse Saved</th>
              </tr>
            </thead>
            <tbody>
              {data.products.slice(0, 60).map((r) => (
                <tr key={r.id} className="border-b last:border-0 hover:bg-muted/30" data-testid={`economics-row-${r.product_code}`}>
                  <td className="py-2 pr-3">
                    <span className="font-medium">{r.title}</span>
                    <span className="block text-[10px] text-muted-foreground">{r.product_code} · {r.cost_basis}</span>
                  </td>
                  <td className="pr-3 text-muted-foreground">{r.product_type}</td>
                  <td className="pr-3 text-right">{money(r.manufacturing_cost)}</td>
                  <td className="pr-3 text-right">{money(r.suggested_price)}</td>
                  <td className="pr-3 text-right text-muted-foreground">{money(r.processing_fee + r.marketplace_fee)}</td>
                  <td className="pr-3 text-right font-medium">{money(r.gross_profit)}</td>
                  <td className="pr-3 text-right font-semibold" style={{ color: r.gross_margin_pct >= 80 ? "hsl(var(--success))" : "hsl(var(--warning))" }}>{r.gross_margin_pct}%</td>
                  <td className="pr-3 text-right text-emerald-600">{money(r.reuse_savings)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[11px] text-muted-foreground mt-3">{data.assumptions?.note}</p>
      </div>
    </div>
  );
}

const Line = ({ k, v, muted }) => (
  <div className={`flex justify-between ${muted ? "text-[11px] text-muted-foreground" : ""}`}>
    <span className={muted ? "" : "text-muted-foreground"}>{k}</span><span className="font-medium">{v}</span>
  </div>
);
