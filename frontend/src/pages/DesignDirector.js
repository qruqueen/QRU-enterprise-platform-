import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/shared";
import { toast } from "sonner";
import {
  Loader2, Gauge, Wand2, ShieldCheck, Settings2, Award, CheckCircle2, AlertTriangle,
  Sparkles, RefreshCw, X,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const abs = (u) => (u ? (u.startsWith("http") ? u : `${BACKEND}${u}`) : null);

const scoreColor = (n) => (n == null ? "text-muted-foreground" : n >= 90 ? "text-emerald-600" : n >= 70 ? "text-amber-600" : "text-red-600");

export default function DesignDirector() {
  const [queue, setQueue] = useState(null);
  const [settings, setSettings] = useState(null);
  const [refs, setRefs] = useState([]);
  const [sel, setSel] = useState(null);
  const [scoring, setScoring] = useState(false);
  const [reviewing, setReviewing] = useState("");
  const [showSettings, setShowSettings] = useState(false);

  const loadQueue = () => api.get("/design-director/queue").then((r) => setQueue(r.data)).catch(() => {});
  const loadRefs = () => api.get("/design-director/references").then((r) => setRefs(r.data.references || [])).catch(() => {});
  useEffect(() => {
    loadQueue(); loadRefs();
    api.get("/design-director/settings").then((r) => setSettings(r.data)).catch(() => {});
  }, []);

  const openScore = async (p) => {
    setSel({ product: p, scorecard: null });
    setScoring(true);
    try {
      const { data } = await api.get(`/design-director/score/${p.id}`);
      setSel({ product: p, scorecard: data });
    } catch (e) { toast.error("Could not score product"); }
    finally { setScoring(false); }
  };

  const runReview = async (p) => {
    setReviewing(p.id);
    try {
      const { data } = await api.post(`/design-director/review/${p.id}`);
      const cost = data.estimated_ai_cost_usd || 0;
      toast[data.passed ? "success" : "info"](
        `${data.passed ? "Passed" : "Best effort"} — ${data.final.overall}/100 after ${data.iterations} pass(es)` +
        (cost ? ` · ~$${cost} AI` : " · $0 AI"));
      loadQueue(); loadRefs();
      if (sel?.product?.id === p.id) openScore(p);
    } catch (e) { toast.error(e.response?.data?.detail || "Review failed"); }
    finally { setReviewing(""); }
  };

  const saveSettings = async (patch) => {
    const next = { ...settings, ...patch };
    setSettings(next);
    try { await api.put("/design-director/settings", patch); toast.success("Settings saved"); }
    catch (e) { toast.error("Could not save settings"); }
  };

  if (!queue || !settings) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  const prods = queue.products || [];
  const scored = prods.filter((p) => p.scored);
  const passing = scored.filter((p) => p.passed).length;

  return (
    <div>
      <PageHeader
        overline="QRU Design Director™ · Autonomous Review (MT-032)"
        title="Every Product Reviewed Before You See It"
        description="The Design Director scores every product on 11 Treasure Standard™ categories and auto-improves it (re-render → re-score) until it passes. Deterministic-first — re-renders spend $0 AI unless you enable AI hero art."
        actions={
          <button data-testid="dd-settings-btn" onClick={() => setShowSettings(true)}
            className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors">
            <Settings2 className="w-4 h-4" /> Settings
          </button>
        }
      />

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <Tile icon={Gauge} label="Passing Score" value={`${settings.passing_score}/100`} testid="dd-tile-passing" />
        <Tile icon={CheckCircle2} label="Products Passing" value={`${passing}/${scored.length}`} testid="dd-tile-passcount" />
        <Tile icon={Wand2} label="Auto-Improve" value={settings.auto_improve ? "On" : "Off"} testid="dd-tile-auto" />
        <Tile icon={Sparkles} label="AI Hero Art" value={settings.allow_ai_hero_art ? "Enabled ($)" : "Off ($0)"} testid="dd-tile-ai" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Review queue */}
        <div className="lg:col-span-2">
          <p className="overline text-primary mb-2">Review Queue</p>
          {prods.length === 0 ? (
            <EmptyState icon={Gauge} title="Nothing to review yet" description="Products appear here once they have a rendered deliverable." />
          ) : (
            <div className="space-y-2" data-testid="dd-queue">
              {prods.map((p) => (
                <div key={p.id} className="bg-card border rounded-md p-3 flex items-center gap-3" data-testid={`dd-row-${p.product_code}`}>
                  <div className="w-10 h-12 rounded border overflow-hidden bg-muted shrink-0">
                    {p.cover_url && <img src={abs(p.cover_url)} alt="" className="w-full h-full object-cover" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{p.title}</p>
                    <p className="text-[11px] text-muted-foreground">{p.product_code} · {p.product_type}</p>
                  </div>
                  <div className={`font-heading font-bold text-lg ${scoreColor(p.overall)}`}>{p.overall == null ? "—" : p.overall}</div>
                  <button data-testid={`dd-score-${p.product_code}`} onClick={() => openScore(p)}
                    className="text-xs border px-2.5 py-1.5 rounded-sm hover:border-primary">Scorecard</button>
                  <button data-testid={`dd-review-${p.product_code}`} onClick={() => runReview(p)} disabled={reviewing === p.id}
                    className="flex items-center gap-1.5 text-xs bg-primary text-primary-foreground px-2.5 py-1.5 rounded-sm hover:bg-primary/90 disabled:opacity-60">
                    {reviewing === p.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5" />} Auto-Improve
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Reference gallery */}
        <div>
          <p className="overline text-gold mb-2 flex items-center gap-1.5"><Award className="w-3.5 h-3.5" /> Design References™</p>
          <p className="text-[11px] text-muted-foreground mb-2">Every passing / Founder-approved product becomes a reusable reference the factory learns from.</p>
          {refs.length === 0 ? (
            <p className="text-sm text-muted-foreground italic">No references yet. Products that pass review are recorded here.</p>
          ) : (
            <div className="grid grid-cols-3 gap-2" data-testid="dd-references">
              {refs.map((r) => (
                <div key={r.product_id} className="rounded border overflow-hidden" title={`${r.product_code} · ${r.overall}/100`}>
                  <div className="aspect-[3/4] bg-muted overflow-hidden">{r.cover_url && <img src={abs(r.cover_url)} alt="" className="w-full h-full object-cover" />}</div>
                  <div className="px-1.5 py-1 text-[10px] flex justify-between"><span className="truncate">{r.product_type}</span><span className="text-emerald-600 font-semibold">{r.overall}</span></div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Scorecard drawer */}
      {sel && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setSel(null)} data-testid="dd-scorecard-modal">
          <div className="bg-card rounded-md max-w-2xl w-full max-h-[85vh] overflow-y-auto p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="font-heading font-semibold">{sel.product.title}</p>
                <p className="text-xs text-muted-foreground">{sel.product.product_code} · Design Scorecard</p>
              </div>
              <button onClick={() => setSel(null)}><X className="w-5 h-5 text-muted-foreground" /></button>
            </div>
            {scoring || !sel.scorecard ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-8 justify-center"><Loader2 className="w-4 h-4 animate-spin" /> Scoring…</div>
            ) : (
              <>
                <div className="flex items-center gap-3 mb-4">
                  <div className={`font-heading text-4xl font-bold ${scoreColor(sel.scorecard.overall)}`}>{sel.scorecard.overall}</div>
                  <div>
                    <p className="text-sm">/ 100 · needs {sel.scorecard.passing_score}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${sel.scorecard.passed ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`}>
                      {sel.scorecard.passed ? "Passes Treasure Standard™" : "Needs improvement"}
                    </span>
                  </div>
                  <button data-testid="dd-modal-review" onClick={() => runReview(sel.product)} disabled={reviewing === sel.product.id}
                    className="ml-auto flex items-center gap-1.5 text-sm bg-primary text-primary-foreground px-3 py-2 rounded-sm hover:bg-primary/90 disabled:opacity-60">
                    {reviewing === sel.product.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />} Auto-Improve
                  </button>
                </div>
                <div className="space-y-2" data-testid="dd-scorecard-categories">
                  {sel.scorecard.categories.map((c, i) => (
                    <div key={i} className="border rounded-md p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium flex items-center gap-1.5">
                          {c.score >= 9 ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />}
                          {c.category}
                        </span>
                        <span className={`text-sm font-bold ${c.score >= 9 ? "text-emerald-600" : c.score >= 6 ? "text-amber-600" : "text-red-600"}`}>{c.score}/10</span>
                      </div>
                      <p className="text-[12px] text-muted-foreground mt-1">{c.reason}</p>
                      {c.priority !== "Pass" && <p className="text-[12px] text-primary mt-0.5">→ {c.recommendation}</p>}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Settings modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setShowSettings(false)} data-testid="dd-settings-modal">
          <div className="bg-card rounded-md max-w-md w-full p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <p className="font-heading font-semibold flex items-center gap-2"><Settings2 className="w-4 h-4" /> Design Director™ Settings</p>
              <button onClick={() => setShowSettings(false)}><X className="w-5 h-5 text-muted-foreground" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Passing score: {settings.passing_score}/100</label>
                <input data-testid="dd-set-passing" type="range" min="60" max="100" value={settings.passing_score}
                  onChange={(e) => setSettings({ ...settings, passing_score: +e.target.value })}
                  onMouseUp={(e) => saveSettings({ passing_score: +e.target.value })} className="w-full" />
              </div>
              <div>
                <label className="text-sm font-medium">Max improvement passes: {settings.max_iterations}</label>
                <input type="range" min="1" max="5" value={settings.max_iterations}
                  onChange={(e) => setSettings({ ...settings, max_iterations: +e.target.value })}
                  onMouseUp={(e) => saveSettings({ max_iterations: +e.target.value })} className="w-full" />
              </div>
              <Toggle label="Auto-improve on review" desc="Re-render & re-score until it passes." checked={settings.auto_improve}
                onChange={(v) => saveSettings({ auto_improve: v })} testid="dd-set-auto" />
              <Toggle label="Allow AI hero art in re-renders" desc="Off = $0 AI (deterministic covers). On = ~$0.04 per re-render image."
                checked={settings.allow_ai_hero_art} onChange={(v) => saveSettings({ allow_ai_hero_art: v })} testid="dd-set-ai" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const Tile = ({ icon: Icon, label, value, testid }) => (
  <div className="bg-card border rounded-md p-4" data-testid={testid}>
    <div className="flex items-center gap-2 text-muted-foreground"><Icon className="w-4 h-4 text-primary" /><span className="text-xs">{label}</span></div>
    <p className="font-heading text-xl font-bold mt-1">{value}</p>
  </div>
);

const Toggle = ({ label, desc, checked, onChange, testid }) => (
  <button data-testid={testid} onClick={() => onChange(!checked)} className="w-full flex items-start gap-3 text-left">
    <span className={`mt-0.5 w-10 h-6 rounded-full transition-colors shrink-0 ${checked ? "bg-primary" : "bg-muted"} relative`}>
      <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-all ${checked ? "left-[18px]" : "left-0.5"}`} />
    </span>
    <span><span className="text-sm font-medium block">{label}</span><span className="text-[11px] text-muted-foreground">{desc}</span></span>
  </button>
);
