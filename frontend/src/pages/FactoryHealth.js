import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/shared";
import { toast } from "sonner";
import {
  Loader2, Activity, Play, CheckCircle2, AlertTriangle, TrendingUp, Clock, PiggyBank,
  Award, ArrowUpRight, Recycle, Stethoscope, Trophy, ThumbsDown, Wand2, ClipboardCheck,
} from "lucide-react";

const ISSUE_LABELS = {
  unclear_content: "Unclear content", weak_teaching_flow: "Weak teaching flow",
  weak_visual_hierarchy: "Weak visual hierarchy", inconsistent_typography: "Inconsistent typography",
  poor_spacing: "Poor spacing", readability_problems: "Readability problems",
  branding_imbalance: "Branding imbalance", treasure_standard_gap: "Treasure Standard™ gap",
  print_readiness_issues: "Print readiness issues", marketplace_export_issues: "Marketplace export issues",
  recipe_violations: "Recipe violations", cover_only_posters: "Cover-only posters",
};

const Tile = ({ icon: Icon, label, value, sub, testid }) => (
  <div className="bg-card border rounded-md p-4" data-testid={testid}>
    <div className="flex items-center gap-2 text-muted-foreground"><Icon className="w-4 h-4 text-primary" /><span className="text-xs">{label}</span></div>
    <p className="font-heading text-2xl font-bold mt-1">{value}</p>
    {sub && <p className="text-[11px] text-muted-foreground mt-0.5">{sub}</p>}
  </div>
);

const IssueList = ({ title, items, keyField, labelMap, testid }) => (
  <div>
    <p className="text-xs font-semibold text-muted-foreground mb-2">{title}</p>
    {(!items || items.length === 0) ? (
      <p className="text-sm text-emerald-600">None detected.</p>
    ) : (
      <div className="space-y-1.5" data-testid={testid}>
        {items.map((it, i) => (
          <div key={i} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1.5 min-w-0"><AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" /><span className="truncate">{labelMap ? (labelMap[it[keyField]] || it[keyField]) : it[keyField]}</span></span>
            <span className="font-semibold text-amber-700 ml-2">{it.count}</span>
          </div>
        ))}
      </div>
    )}
  </div>
);

export default function FactoryHealth() {
  const [data, setData] = useState(null);
  const [report, setReport] = useState(null);
  const [running, setRunning] = useState(false);
  const [gate, setGate] = useState(null);      // {status, processed, total, report}
  const [gating, setGating] = useState(false);

  const loadReport = () => api.get("/factory-audit/learning-report").then((r) => setReport(r.data)).catch(() => {});
  useEffect(() => { loadReport(); }, []);

  const run = async () => {
    setRunning(true);
    try {
      const { data: res } = await api.post("/factory-audit/run");
      setData(res);
      toast.success(`Audit complete — ${res.dashboard.products_passing}/${res.dashboard.total_products} passing`);
      loadReport();
    } catch (e) { toast.error(e.response?.data?.detail || "Audit failed"); }
    finally { setRunning(false); }
  };

  const gateLibrary = async () => {
    setGating(true);
    try {
      const { data: res } = await api.post("/factory-audit/gate-library");
      setGate({ status: "running", processed: 0, total: res.total });
      const poll = setInterval(async () => {
        try {
          const { data: st } = await api.get(`/factory-audit/gate-library/${res.run_id}`);
          setGate(st);
          if (st.status === "done") {
            clearInterval(poll);
            setGating(false);
            toast.success(`Library gated — ${st.report.ready_for_founder_review} products ready for review`);
            loadReport();
          }
        } catch (e) { clearInterval(poll); setGating(false); }
      }, 3000);
    } catch (e) { toast.error(e.response?.data?.detail || "Could not start"); setGating(false); }
  };

  const d = data?.dashboard;
  const m = report?.available && !report.baseline ? report.metrics : null;

  return (
    <div>
      <PageHeader
        overline="Factory Intelligence™ · MO-036"
        title="QRU Factory Health Audit™"
        description="A one-click, fully deterministic inspection of the entire Product Library ($0 AI, no regeneration). Measures the health, maturity, efficiency, and learning progress of the factory over time."
        actions={
          <div className="flex gap-2">
            <button data-testid="fh-gate-btn" onClick={gateLibrary} disabled={gating || running}
              className="flex items-center gap-2 border px-4 py-2.5 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors disabled:opacity-60">
              {gating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} Gate Entire Library
            </button>
            <button data-testid="fh-run-btn" onClick={run} disabled={running || gating}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2.5 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60">
              {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Run Factory Health Audit™
            </button>
          </div>
        }
      />

      {/* QRU Library Auto-Gate™ progress + report */}
      {gate && (
        <div className="bg-card border rounded-md p-5 mb-6" data-testid="fh-gate-panel">
          <p className="overline text-primary mb-2 flex items-center gap-1.5"><Wand2 className="w-3.5 h-3.5" /> QRU Library Auto-Gate™ {gate.status === "running" ? "— running…" : "— complete"}</p>
          {gate.status === "running" ? (
            <div>
              <div className="flex items-center justify-between text-sm mb-1"><span className="text-muted-foreground">Deterministic gating ($0 AI)…</span><span>{gate.processed}/{gate.total}</span></div>
              <div className="h-2 bg-muted rounded-full overflow-hidden"><div className="h-full bg-gold transition-all" style={{ width: `${gate.total ? (gate.processed / gate.total) * 100 : 0}%` }} /></div>
            </div>
          ) : gate.report ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" data-testid="fh-gate-report">
              <Tile icon={ClipboardCheck} label="Processed" value={gate.report.processed} testid="fh-g-processed" />
              <Tile icon={CheckCircle2} label="Ready for Founder Review" value={gate.report.ready_for_founder_review} testid="fh-g-ready" />
              <Tile icon={ArrowUpRight} label="Improved" value={gate.report.improved} sub={`${gate.report.rendered} newly rendered`} testid="fh-g-improved" />
              <Tile icon={Clock} label="Founder Hours Saved" value={`${gate.report.estimated_founder_hours_saved}h`} testid="fh-g-saved" />
              <Tile icon={AlertTriangle} label="Still Need Rendering" value={gate.report.requires_rendering} testid="fh-g-render" />
              <Tile icon={Activity} label="Need Knowledge Records" value={gate.report.requires_knowledge_record} testid="fh-g-kr" />
              <Tile icon={Activity} label="Need AI (after cap)" value={gate.report.requires_ai_after_cap} testid="fh-g-ai" />
              <Tile icon={AlertTriangle} label="Still Blocked" value={gate.report.still_blocked} testid="fh-g-blocked" />
            </div>
          ) : null}
          <p className="text-[11px] text-muted-foreground mt-3">Preparation & QC only. Live products are scored (not changed); nothing is published without your review and approval.</p>
        </div>
      )}

      {/* Learning Report */}
      {report?.available && (
        <div className="bg-card border rounded-md p-5 mb-6" data-testid="fh-learning-report">
          <p className="overline text-gold mb-3 flex items-center gap-1.5"><TrendingUp className="w-3.5 h-3.5" /> Factory Learning Report™ — What Did the Factory Get Better At?</p>
          {report.baseline ? (
            <p className="text-sm text-muted-foreground">{report.message}</p>
          ) : m ? (
            <div className="grid md:grid-cols-2 gap-5">
              <div className="grid grid-cols-2 gap-3">
                <Tile icon={ArrowUpRight} label="Design Score Change" value={`${m.avg_design_score_change_pct >= 0 ? "+" : ""}${m.avg_design_score_change_pct}%`} sub={`${m.avg_design_score_before} → ${m.avg_design_score_now}`} testid="fh-m-score" />
                <Tile icon={Recycle} label="Asset Reuse Change" value={`${m.asset_reuse_change_points >= 0 ? "+" : ""}${m.asset_reuse_change_points}pt`} sub={`${m.asset_reuse_before}% → ${m.asset_reuse_now}%`} testid="fh-m-reuse" />
                <Tile icon={CheckCircle2} label="Founder Corrections ↓" value={`${m.founder_corrections_reduced_pct}pt`} testid="fh-m-corr" />
                <Tile icon={PiggyBank} label="AI Savings" value={`$${m.estimated_ai_savings_usd}`} sub={`${m.founder_hours_saved}h saved`} testid="fh-m-ai" />
              </div>
              <div>
                <p className="text-xs font-semibold text-muted-foreground mb-2">Improved Areas</p>
                {report.improved_at.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Holding steady — no regressions.</p>
                ) : (
                  <div className="space-y-1.5">
                    {report.improved_at.map((a, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-1.5"><ArrowUpRight className="w-3.5 h-3.5 text-emerald-600" /> {a.area}</span>
                        <span className="text-emerald-600 font-medium">{a.from} → {a.to}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {!d ? (
        <EmptyState icon={Stethoscope} title="Run your first Factory Health Audit™"
          description="Deterministically inspect every product in the library. No AI, no regeneration — a read-only health check." />
      ) : (
        <>
          {/* Dashboard */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4" data-testid="fh-dashboard">
            <Tile icon={Activity} label="Total Products" value={d.total_products} testid="fh-total" />
            <Tile icon={CheckCircle2} label="Passing Design Standards" value={d.products_passing} sub={`${d.products_requiring_review} need review`} testid="fh-passing" />
            <Tile icon={Award} label="Avg Design Score" value={`${d.avg_design_score}`} testid="fh-avgscore" />
            <Tile icon={Award} label="Avg Treasure Standard™" value={`${d.avg_treasure_score}`} testid="fh-treasure" />
            <Tile icon={TrendingUp} label="Avg Product Readiness" value={`${d.avg_product_readiness}`} testid="fh-readiness" />
            <Tile icon={TrendingUp} label="Avg Marketplace Readiness" value={`${d.avg_marketplace_readiness}`} testid="fh-market" />
            <Tile icon={Recycle} label="Avg Asset Reuse" value={`${d.avg_asset_reuse_pct}%`} sub={`Preview coverage ${d.preview_coverage_pct}%`} testid="fh-reuse" />
            <Tile icon={Clock} label="Founder Time Saved" value={`${d.founder_time_saved_hours}h`} sub={`~$${d.estimated_ai_cost_avoided_usd} AI avoided`} testid="fh-time" />
          </div>

          {/* Issues + rankings */}
          <div className="grid lg:grid-cols-3 gap-6 mb-6">
            <div className="bg-card border rounded-md p-5"><IssueList title="Most Common Design Issues" items={d.most_common_design_issues} keyField="issue" labelMap={ISSUE_LABELS} testid="fh-design-issues" /></div>
            <div className="bg-card border rounded-md p-5"><IssueList title="Most Common Manufacturing Issues" items={d.most_common_manufacturing_issues} keyField="issue" testid="fh-mfg-issues" /></div>
            <div className="bg-card border rounded-md p-5"><IssueList title="Most Common Recipe Violations" items={d.most_common_recipe_violations} keyField="violation" testid="fh-recipe-violations" /></div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-card border rounded-md p-5">
              <p className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1.5"><Trophy className="w-3.5 h-3.5 text-gold" /> Best Performing Product Types</p>
              <div className="space-y-1.5" data-testid="fh-best-types">
                {d.best_performing_types.map((t) => (
                  <div key={t.product_type} className="flex items-center justify-between text-sm">
                    <span>{t.product_type}</span><span className="text-muted-foreground">{t.count} · {t.pass_rate}% pass · avg {t.avg_score}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-card border rounded-md p-5">
              <p className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1.5"><ThumbsDown className="w-3.5 h-3.5 text-red-500" /> Lowest Performing Product Types</p>
              <div className="space-y-1.5" data-testid="fh-low-types">
                {d.lowest_performing_types.length === 0 ? <p className="text-sm text-muted-foreground">Not enough variety yet.</p> :
                  d.lowest_performing_types.map((t) => (
                    <div key={t.product_type} className="flex items-center justify-between text-sm">
                      <span>{t.product_type}</span><span className="text-muted-foreground">{t.count} · {t.pass_rate}% pass · avg {t.avg_score}</span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
