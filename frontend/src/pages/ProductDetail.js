import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/api";
import { StatusBadge, Markdown } from "@/components/shared";
import { toast } from "sonner";
import { ArrowLeft, Loader2, CheckCircle2, Send, Archive, Wand2, Sparkles } from "lucide-react";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [p, setP] = useState(null);
  const [briefBusy, setBriefBusy] = useState(false);
  const load = () => api.get(`/products/${id}`).then((r) => setP(r.data)).catch(() => {});
  useEffect(() => { load(); }, [id]);

  const setStatus = async (status) => {
    try {
      await api.patch(`/products/${id}/status`, { status });
      toast.success(`Product ${status}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || "Failed"); }
  };

  const enhance = async () => {
    setBriefBusy(true);
    try { await api.post(`/products/${id}/creative-brief`); toast.success("Creative Studio enhanced this product page"); load(); }
    catch { toast.error("Enhancement failed"); } finally { setBriefBusy(false); }
  };

  if (!p) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  const b = p.creative_brief;

  return (
    <div className="animate-fade-up">
      <button onClick={() => navigate("/products")} data-testid="pd-back" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="w-4 h-4" /> Product Library
      </button>

      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-xs text-muted-foreground">{p.product_code}</span>
            <span className="text-xs text-primary font-medium">{p.product_type}</span>
            <StatusBadge status={p.status} testid="pd-status" />
          </div>
          <h1 className="font-heading text-3xl font-bold tracking-tight max-w-3xl">{p.title}</h1>
          <p className="text-muted-foreground mt-2">{p.family} · {p.audience} · {p.learning_level}</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <button data-testid="pd-creative-btn" onClick={enhance} disabled={briefBusy} className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors disabled:opacity-60">
            {briefBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} Creative Studio
          </button>
          <button data-testid="pd-review-btn" onClick={() => setStatus("In Review")} className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-warning hover:text-warning transition-colors">
            <Send className="w-4 h-4" /> Submit for Review
          </button>
          <button data-testid="pd-publish-btn" onClick={() => setStatus("Published")} className="flex items-center gap-2 bg-primary text-primary-foreground px-3 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
            <CheckCircle2 className="w-4 h-4" /> Approve & Publish
          </button>
          <button data-testid="pd-archive-btn" onClick={() => setStatus("Archived")} className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-destructive hover:text-destructive transition-colors">
            <Archive className="w-4 h-4" />
          </button>
        </div>
      </div>

      {b && (
        <div className="bg-card border rounded-md p-6 mb-6 max-w-4xl" data-testid="pd-creative-brief">
          <div className="flex items-center gap-2 mb-4"><Sparkles className="w-4 h-4 text-gold" /><h3 className="font-heading font-semibold">Product Page · by Creative Studio™</h3></div>
          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div><p className="overline text-primary mb-1">Who this is for</p><p>{b.who_for}</p></div>
            <div><p className="overline text-primary mb-1">Problem it solves</p><p>{b.problem_solved}</p></div>
            <div className="sm:col-span-2"><p className="overline text-primary mb-1">What you'll understand</p><p>{b.will_understand}</p></div>
            <div><p className="overline text-primary mb-1">Skills gained</p><ul className="list-disc pl-4 text-muted-foreground">{(b.skills_gained || []).map((s, i) => <li key={i}>{s}</li>)}</ul></div>
            <div><p className="overline text-primary mb-1">What's included</p><ul className="list-disc pl-4 text-muted-foreground">{(b.whats_included || []).map((s, i) => <li key={i}>{s}</li>)}</ul></div>
            <div className="flex gap-6">
              <div><p className="overline text-primary mb-1">Reading level</p><p>{b.reading_level}</p></div>
              <div><p className="overline text-primary mb-1">Est. time</p><p>{b.completion_time}</p></div>
            </div>
            <div><p className="overline text-primary mb-1">Next learning path</p><p>{b.next_path}</p></div>
          </div>
          {p.related_products?.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <p className="overline text-primary mb-2">Related QRU products</p>
              <div className="flex flex-wrap gap-2">
                {p.related_products.map((r) => (
                  <Link key={r.id} to={`/products/${r.id}`} className="text-xs border rounded-sm px-2 py-1 hover:border-primary">{r.product_type}: {r.title}</Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="bg-card border rounded-md p-8 max-w-4xl">
        <Markdown text={p.content} />
      </div>
    </div>
  );
}
