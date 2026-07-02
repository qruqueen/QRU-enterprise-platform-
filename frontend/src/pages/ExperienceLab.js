import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, FlaskConical, Sparkles, ThumbsUp, AlertCircle } from "lucide-react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";

function ScoreBar({ label, value }) {
  const color = value >= 80 ? "hsl(var(--success))" : value >= 55 ? "hsl(var(--warning))" : "hsl(var(--destructive))";
  return (
    <div>
      <div className="flex justify-between text-xs mb-1"><span className="font-medium">{label}</span><span className="text-muted-foreground">{value}</span></div>
      <div className="h-2 rounded-full bg-muted"><div className="h-full rounded-full" style={{ width: `${value}%`, background: color }} /></div>
    </div>
  );
}

export default function ExperienceLab() {
  const [products, setProducts] = useState([]);
  const [selected, setSelected] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/consumer/catalog").then((r) => setProducts(r.data.products));
  }, []);

  const evaluate = async () => {
    if (!selected) { toast.error("Select a product to evaluate."); return; }
    setRunning(true); setResult(null);
    try {
      const { data } = await api.post("/experience-lab/evaluate", { product_id: selected });
      setResult(data);
    } catch { toast.error("Evaluation failed. Try again."); }
    setRunning(false);
  };

  return (
    <div>
      <PageHeader overline="QRU Experience Lab™ · Enterprise Mode" title="Experience Lab"
        description="Experience each product exactly as a customer would. Measure clarity, understanding, and delight." />

      <div className="bg-card border rounded-2xl p-5 mb-6 flex flex-col sm:flex-row gap-3 sm:items-end">
        <div className="flex-1">
          <label className="text-xs text-muted-foreground mb-1 block">Published product</label>
          <select data-testid="exp-product-select" value={selected} onChange={(e) => setSelected(e.target.value)}
            className="w-full px-3 py-2 text-sm bg-muted rounded-md border border-border outline-none focus:border-primary">
            <option value="">Select a product…</option>
            {products.map((p) => <option key={p.id} value={p.id}>{p.title} — {p.product_type}</option>)}
          </select>
        </div>
        <button data-testid="exp-run" onClick={evaluate} disabled={running}
          className="px-5 py-2 rounded-md text-white text-sm font-medium flex items-center gap-2 disabled:opacity-60" style={{ background: "hsl(var(--royal))" }}>
          {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />}
          {running ? "Experiencing…" : "Run Experience Test"}
        </button>
      </div>

      {running && (
        <div className="text-center py-16 text-muted-foreground">
          <Sparkles className="w-8 h-8 mx-auto mb-3 animate-pulse text-primary" />
          <p>Experience Lab Director™ is experiencing the product as a learner…</p>
        </div>
      )}

      {result && (
        <div className="space-y-6" data-testid="exp-result">
          <div className="bg-card border rounded-2xl p-6">
            <p className="overline text-primary mb-1">Evaluated</p>
            <h2 className="font-heading text-xl font-bold">{result.product.title}</h2>
            <div className="grid sm:grid-cols-2 gap-4 mt-5">
              {Object.entries(result.evaluation.scores || {}).map(([k, v]) => <ScoreBar key={k} label={k} value={v} />)}
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-card border rounded-2xl p-5">
              <p className="overline text-success mb-3 flex items-center gap-1.5"><ThumbsUp className="w-3.5 h-3.5" /> Strengths</p>
              <ul className="space-y-1.5 text-sm">{(result.evaluation.strengths || []).map((s, i) => <li key={i} className="flex gap-2"><span className="text-success">+</span>{s}</li>)}</ul>
            </div>
            <div className="bg-card border rounded-2xl p-5">
              <p className="overline text-warning mb-3 flex items-center gap-1.5" style={{ color: "hsl(var(--warning))" }}><AlertCircle className="w-3.5 h-3.5" /> Friction Points</p>
              <ul className="space-y-1.5 text-sm">{(result.evaluation.friction_points || []).map((s, i) => <li key={i} className="flex gap-2"><span style={{ color: "hsl(var(--warning))" }}>!</span>{s}</li>)}</ul>
            </div>
          </div>
          <div className="rounded-2xl border border-gold p-5" style={{ background: "hsl(var(--gold) / 0.06)" }}>
            <p className="overline mb-3" style={{ color: "hsl(var(--navy))" }}>Recommendations</p>
            <ul className="space-y-1.5 text-sm">{(result.evaluation.recommendations || []).map((s, i) => <li key={i} className="flex gap-2"><span className="text-gold">→</span>{s}</li>)}</ul>
          </div>
        </div>
      )}
    </div>
  );
}
