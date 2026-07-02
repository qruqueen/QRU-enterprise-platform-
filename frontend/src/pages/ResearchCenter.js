import { useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { toast } from "sonner";
import { FlaskConical, Loader2, Sparkles, CornerDownRight } from "lucide-react";

export default function ResearchCenter() {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const research = async () => {
    if (!topic.trim()) return toast.error("Enter a topic to research");
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post("/command", { message: `Start research on ${topic}` });
      setResult(data);
      toast.success("Research complete — draft record created");
    } catch { toast.error("Research failed"); } finally { setLoading(false); }
  };

  return (
    <div>
      <PageHeader
        overline="Research Center"
        title="Discover Verified Knowledge"
        description="The Research Director™ investigates a topic, produces an evidence-based brief, and drafts a Knowledge Record for verification."
      />

      <div className="max-w-2xl">
        <div className="bg-card border rounded-md p-6">
          <label className="text-sm font-medium">Research Topic</label>
          <div className="flex gap-2 mt-2">
            <input data-testid="research-topic-input" value={topic} onChange={(e) => setTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && research()}
              placeholder="e.g. How does the human liver detoxify the body?"
              className="flex-1 px-3 py-2.5 rounded-sm border outline-none focus:border-primary text-sm" />
            <button data-testid="research-start-btn" onClick={research} disabled={loading}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-4 rounded-sm text-sm font-medium hover:bg-primary/90 disabled:opacity-60">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />} Research
            </button>
          </div>
        </div>

        {result && (
          <div className="bg-card border rounded-md p-6 mt-5 animate-fade-up" data-testid="research-result">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-primary" />
              <h3 className="font-heading font-semibold">Research Brief</h3>
            </div>
            <p className="text-sm leading-relaxed">{result.reply}</p>
            {result.created && (
              <Link to={`/knowledge/${result.created.id}`} className="inline-flex items-center gap-1.5 mt-4 text-sm text-primary font-medium hover:underline">
                <CornerDownRight className="w-4 h-4" /> Open {result.created.code} · {result.created.title}
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
