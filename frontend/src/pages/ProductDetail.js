import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { StatusBadge, Markdown } from "@/components/shared";
import { toast } from "sonner";
import { ArrowLeft, Loader2, CheckCircle2, Send, Archive } from "lucide-react";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [p, setP] = useState(null);
  const load = () => api.get(`/products/${id}`).then((r) => setP(r.data)).catch(() => {});
  useEffect(() => { load(); }, [id]);

  const setStatus = async (status) => {
    try {
      await api.patch(`/products/${id}/status`, { status });
      toast.success(`Product ${status}`);
      load();
    } catch { toast.error("Failed"); }
  };

  if (!p) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

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

      <div className="bg-card border rounded-md p-8 max-w-4xl">
        <Markdown text={p.content} />
      </div>
    </div>
  );
}
