import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { Coins, Loader2, Trophy, Target, ListChecks, Snowflake, TrendingUp, ShoppingCart, RefreshCw, CheckCircle2 } from "lucide-react";

function Stat({ icon: Icon, label, value, accent }) {
  return (
    <div className="rounded-md border border-border bg-card p-4">
      <div className="flex items-center gap-2 text-muted-foreground"><Icon className="w-4 h-4" /><span className="text-[11px] uppercase tracking-wide">{label}</span></div>
      <p className={`text-2xl font-heading font-bold mt-1 ${accent || "text-navy"}`}>{value}</p>
    </div>
  );
}

export default function FirstDollarMode() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = () => api.get("/first-dollar/status").then(({ data }) => setData(data)).catch(() => {}).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const check = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/first-dollar/check-milestone");
      toast[data.achieved ? "success" : "message"](data.achieved ? (data.newly_recorded ? "FOUNDATION MILESTONE #001 recorded!" : "Milestone already achieved") : "No verified purchase yet — awaiting the first dollar.");
      load();
    } finally { setBusy(false); }
  };

  if (loading) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading First Dollar Mode…</div>;
  if (!data) return <div className="p-8 text-sm text-muted-foreground">Unable to load First Dollar Mode.</div>;

  const p = data.progress;

  return (
    <div className="space-y-6" data-testid="first-dollar-page">
      {/* Mode banner */}
      <div className="rounded-lg overflow-hidden border border-gold/40 bg-gradient-to-r from-[#1a1147] to-[#0A1A3F] text-white p-6" data-testid="mode-banner">
        <div className="flex items-center gap-2 text-gold text-xs font-semibold tracking-widest uppercase"><Coins className="w-4 h-4" /> {data.mode_label} · ACTIVE</div>
        <h1 className="font-heading text-3xl font-bold mt-2">Prove the Factory Works.</h1>
        <p className="text-sm text-white/80 mt-2 max-w-3xl">{data.primary_objective}</p>
        <p className="text-xs text-gold/90 italic mt-2">{data.philosophy}</p>
      </div>

      {/* Milestone */}
      <div data-testid="milestone-card" className={`rounded-lg border p-5 ${data.first_dollar_achieved ? "border-emerald-300 bg-emerald-50" : "border-amber-300 bg-amber-50"}`}>
        <div className="flex items-start gap-3">
          <Trophy className={`w-6 h-6 shrink-0 ${data.first_dollar_achieved ? "text-emerald-600" : "text-amber-500"}`} />
          <div className="flex-1">
            {data.first_dollar_achieved ? (
              <>
                <p className="font-heading font-bold text-navy text-lg">FOUNDATION MILESTONE #001 — "The Factory Works."</p>
                <p className="text-sm text-foreground/70 mt-1">A verified customer voluntarily exchanged ${data.milestone?.amount_usd} for a QRU-manufactured product. Recorded permanently.</p>
              </>
            ) : (
              <>
                <p className="font-heading font-bold text-navy text-lg">Awaiting FOUNDATION MILESTONE #001</p>
                <p className="text-sm text-foreground/70 mt-1">The first milestone is not a million dollars — it is <span className="font-semibold">one verified customer</span> voluntarily paying for a QRU product. When it happens, it is recorded permanently as "The Factory Works."</p>
              </>
            )}
          </div>
          <button data-testid="check-milestone-btn" onClick={check} disabled={busy} className="text-xs px-3 py-1.5 rounded-sm border border-navy/30 hover:border-navy flex items-center gap-1.5 disabled:opacity-50 shrink-0">
            <RefreshCw className={`w-3.5 h-3.5 ${busy ? "animate-spin" : ""}`} /> Check
          </button>
        </div>
      </div>

      {/* Progress */}
      <div>
        <p className="overline text-primary mb-3 flex items-center gap-2"><TrendingUp className="w-4 h-4" /> First-Dollar Progress</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <Stat icon={ShoppingCart} label="Published Products" value={p.published_products} />
          <Stat icon={Coins} label="In Storefront" value={p.storefront_products} />
          <Stat icon={CheckCircle2} label="Paid Orders" value={p.paid_orders} accent="text-emerald-600" />
          <Stat icon={TrendingUp} label="Revenue (USD)" value={`$${p.revenue_usd}`} accent="text-emerald-600" />
          <Stat icon={Trophy} label="Fulfilled" value={p.fulfilled_purchases} />
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div>
          <p className="overline text-primary mb-3 flex items-center gap-2"><ListChecks className="w-4 h-4" /> Priorities</p>
          <div className="space-y-2">
            {data.priorities.map((pr, i) => (
              <div key={i} className="rounded-md border border-border bg-card p-3 text-sm text-foreground/80">{pr}</div>
            ))}
          </div>
        </div>
        <div>
          <p className="overline text-primary mb-3 flex items-center gap-2"><Snowflake className="w-4 h-4" /> Factory Freeze Policy</p>
          <div className="rounded-md border border-sky-200 bg-sky-50 p-4">
            <p className="text-xs text-sky-800 mb-2">Unless a critical issue is discovered:</p>
            <ul className="space-y-1.5">
              {data.freeze_policy.map((f, i) => (
                <li key={i} className="text-sm text-foreground/80 flex items-start gap-2"><Snowflake className="w-3.5 h-3.5 text-sky-500 mt-0.5 shrink-0" /> {f}</li>
              ))}
            </ul>
            <div className="mt-3 pt-3 border-t border-sky-200 flex items-start gap-2 text-sm">
              <Target className="w-4 h-4 text-navy mt-0.5 shrink-0" />
              <p className="text-foreground/70"><span className="font-semibold text-navy">Success metric:</span> {data.success_metric}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
