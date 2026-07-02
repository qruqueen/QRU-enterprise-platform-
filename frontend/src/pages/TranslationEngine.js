import { useState } from "react";
import api from "@/lib/api";
import { PageHeader, QRUMethodology } from "@/components/shared";
import { toast } from "sonner";
import { Wand2, Loader2, Sparkles } from "lucide-react";

const SAMPLE = "Mitochondria are membrane-bound organelles that generate most of the cell's supply of adenosine triphosphate (ATP) through oxidative phosphorylation, serving as the primary site of cellular respiration.";

export default function TranslationEngine() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const run = async () => {
    if (!content.trim()) return toast.error("Paste some technical content to transform");
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post("/translation-engine", { title, content });
      setResult(data.result);
      toast.success("Understanding manufactured");
    } catch { toast.error("Translation failed — try again"); } finally { setLoading(false); }
  };

  return (
    <div>
      <PageHeader
        overline="QRU Translation Engine™"
        title="Manufacture Understanding"
        description="Paste any technical content. The QRU Translation Engine™ transforms it into the complete QRU teaching methodology — accurate, but understandable. We never simplify the truth; we simplify the path to it."
      />

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-card border rounded-md p-6 h-fit lg:sticky lg:top-24">
          <label className="text-sm font-medium">Title (optional)</label>
          <input data-testid="te-title" value={title} onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. What are mitochondria?"
            className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm" />
          <div className="flex items-center justify-between mt-4 mb-1">
            <label className="text-sm font-medium">Technical Content</label>
            <button onClick={() => setContent(SAMPLE)} className="text-xs text-primary hover:underline" data-testid="te-sample">Load sample</button>
          </div>
          <textarea data-testid="te-content" rows={10} value={content} onChange={(e) => setContent(e.target.value)}
            placeholder="Paste research, documentation, a definition, or any complex explanation…"
            className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm resize-none" />
          <button data-testid="te-run" onClick={run} disabled={loading}
            className="mt-4 w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground py-2.5 rounded-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Manufacturing…</> : <><Wand2 className="w-4 h-4" /> Transform to Understanding</>}
          </button>
        </div>

        <div>
          {loading && (
            <div className="bg-card border rounded-md p-12 flex flex-col items-center text-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
              <p className="font-heading font-semibold">Applying QRU methodology…</p>
            </div>
          )}
          {!loading && !result && (
            <div className="bg-card border border-dashed rounded-md p-12 flex flex-col items-center text-center">
              <Sparkles className="w-10 h-10 text-muted-foreground mb-4" strokeWidth={1.5} />
              <p className="font-heading font-semibold">Your transformation appears here</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">10 sections of QRU understanding, generated from your content.</p>
            </div>
          )}
          {result && (
            <div className="animate-fade-up" data-testid="te-result">
              <QRUMethodology record={result} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
