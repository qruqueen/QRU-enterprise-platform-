import { useEffect, useState, useCallback } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Rocket, Loader2, Sparkles, CheckCircle2, Package, Wand2 } from "lucide-react";

const MEDITATION_PRESETS = ["Meditation Package", "Morning Motivation™", "Sleep Meditation™", "Brain Focus™", "Stress Relief™", "Faith & Hope™", "Gratitude™", "Healing Journey™", "Deep Learning™"];
const SUGGESTIONS = ["Heart Health", "Brain Health", "Faith", "Forex Trading", "Programming", "AI Literacy", "Parenting", "Leadership", "Homeschool", "Entrepreneurship"];

export default function ProductionLine() {
  const [packages, setPackages] = useState({});
  const [profiles, setProfiles] = useState({});
  const [frequencies, setFrequencies] = useState([]);
  const [runs, setRuns] = useState([]);
  const [form, setForm] = useState({ topic: "", preset: "Core Package", division: "Health", audience: "", difficulty: "", inspiration_profile: "Calm Teacher", frequency: "Ocean" });
  const [launching, setLaunching] = useState(false);

  const loadRuns = useCallback(async () => {
    const { data } = await api.get("/automation/production-line/runs");
    setRuns(data);
  }, []);

  useEffect(() => {
    (async () => {
      const [p, pr] = await Promise.all([api.get("/automation/packages"), api.get("/automation/meditation/profiles")]);
      setPackages(p.data.packages); setProfiles(pr.data.profiles); setFrequencies(pr.data.frequencies);
      loadRuns();
    })();
  }, [loadRuns]);

  useEffect(() => {
    const active = runs.some((r) => !["completed", "failed", "escalated", "timeout"].includes(r.status));
    const iv = setInterval(loadRuns, active ? 3000 : 10000);
    return () => clearInterval(iv);
  }, [runs, loadRuns]);

  const isMeditation = MEDITATION_PRESETS.includes(form.preset);

  const launch = async () => {
    if (!form.topic.trim()) { toast.error("Tell the factory what you want to teach"); return; }
    setLaunching(true);
    try {
      const payload = { topic: form.topic, preset: form.preset, division: form.division, audience: form.audience, difficulty: form.difficulty };
      if (isMeditation) { payload.inspiration_profile = form.inspiration_profile; payload.frequency = form.frequency; }
      await api.post("/automation/production-line", payload);
      toast.success("QRU Factory™ is manufacturing. Sit back — the divisions are working.");
      setForm({ ...form, topic: "" });
      loadRuns();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setLaunching(false); }
  };

  return (
    <div className="space-y-8" data-testid="production-line-page">
      {/* Hero */}
      <div className="rounded-lg bg-navy text-white p-8 md:p-10 relative overflow-hidden">
        <div className="absolute inset-0 opacity-20" style={{ background: "radial-gradient(circle at 20% 20%, #35106A, transparent 60%)" }} />
        <div className="relative">
          <p className="overline text-gold mb-2 flex items-center gap-2"><Rocket className="w-4 h-4" /> QRU Digital Production Line™</p>
          <h1 className="font-heading text-4xl md:text-5xl font-bold tracking-tight">What do you want to teach today?</h1>
          <p className="text-white/70 text-sm mt-3 max-w-2xl">Enter a topic. The QRU Factory™ finds or manufactures a verified Knowledge Record, then autonomously produces, verifies, brands, publishes, and distributes an entire product collection.</p>

          <div className="mt-6 flex flex-col md:flex-row gap-3">
            <input data-testid="teach-topic-input" value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })}
              onKeyDown={(e) => e.key === "Enter" && launch()}
              placeholder="e.g. Heart Health, Faith, Forex Trading…"
              className="flex-1 px-5 py-4 rounded-sm text-navy text-lg font-medium focus:outline-none focus:ring-2 focus:ring-gold" />
            <button data-testid="start-manufacturing-btn" onClick={launch} disabled={launching}
              className="flex items-center justify-center gap-2 bg-gold text-navy px-6 py-4 rounded-sm font-bold text-sm uppercase tracking-wide hover:brightness-110 transition disabled:opacity-60">
              {launching ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />} Start Manufacturing
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button key={s} data-testid={`suggest-${s}`} onClick={() => setForm({ ...form, topic: s })}
                className="text-xs px-3 py-1 rounded-full bg-white/10 hover:bg-white/20 transition">{s}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Options */}
      <div className="grid md:grid-cols-4 gap-4">
        <div>
          <label className="text-xs text-muted-foreground">Product Package</label>
          <select data-testid="teach-package" value={form.preset} onChange={(e) => setForm({ ...form, preset: e.target.value })}
            className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm">
            {Object.keys(packages).map((p) => <option key={p} value={p}>{p} ({packages[p].length})</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Division</label>
          <select data-testid="teach-division" value={form.division} onChange={(e) => setForm({ ...form, division: e.target.value })}
            className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm">
            {["Health", "Faith", "Trading", "Finance", "AI", "Programming", "Parenting", "Business"].map((d) => <option key={d}>{d}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Audience (optional)</label>
          <input data-testid="teach-audience" value={form.audience} onChange={(e) => setForm({ ...form, audience: e.target.value })}
            placeholder="e.g. Families, Teachers" className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm" />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Difficulty (optional)</label>
          <select data-testid="teach-difficulty" value={form.difficulty} onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
            className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm">
            <option value="">Auto</option><option>Beginner</option><option>Intermediate</option><option>Advanced</option>
          </select>
        </div>
        {isMeditation && (
          <>
            <div>
              <label className="text-xs text-muted-foreground flex items-center gap-1"><Wand2 className="w-3 h-3" /> Inspiration Profile™</label>
              <select data-testid="teach-profile" value={form.inspiration_profile} onChange={(e) => setForm({ ...form, inspiration_profile: e.target.value })}
                className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm">
                {Object.keys(profiles).map((p) => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Frequency / Soundscape</label>
              <select data-testid="teach-frequency" value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm">
                {frequencies.map((f) => <option key={f}>{f}</option>)}
              </select>
            </div>
          </>
        )}
      </div>

      {/* Package preview */}
      {packages[form.preset] && (
        <div className="bg-card border rounded-sm p-4">
          <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1"><Package className="w-3 h-3" /> This package manufactures:</p>
          <div className="flex flex-wrap gap-2">
            {packages[form.preset].map((t) => <span key={t} className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary">{t}</span>)}
          </div>
        </div>
      )}

      {/* Runs */}
      <div className="bg-card border rounded-sm">
        <div className="p-4 border-b"><h2 className="font-heading font-semibold">Production Runs</h2></div>
        <div className="divide-y">
          {runs.length === 0 && <p className="p-6 text-sm text-muted-foreground text-center">No production runs yet. Ask the factory to teach something above.</p>}
          {runs.map((r) => (
            <div key={r.id} className="p-4" data-testid={`run-${r.id}`}>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <p className="font-medium text-sm">{r.topic}</p>
                  <p className="text-xs text-muted-foreground">{r.kr_code ? `${r.kr_code} · ` : ""}{r.product_types?.length} products · {r.phase}</p>
                </div>
                <span className={`text-[11px] px-2 py-0.5 rounded-full ${
                  r.status === "completed" ? "bg-emerald-100 text-emerald-700" :
                  r.status === "escalated" ? "bg-amber-100 text-amber-700" :
                  r.status === "failed" || r.status === "timeout" ? "bg-red-100 text-red-700" :
                  "bg-blue-100 text-blue-700"}`}>
                  {r.status === "completed" ? <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> {r.review_state || "completed"}</span> : r.status.replace(/_/g, " ")}
                </span>
              </div>
              <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-gold transition-all" style={{ width: `${r.progress || 0}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
