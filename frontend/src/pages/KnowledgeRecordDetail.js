import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/api";
import { StatusBadge } from "@/components/shared";
import { toast } from "sonner";
import {
  ArrowLeft, ShieldCheck, Sparkles, Factory, Loader2, BookText, Lightbulb, Quote, ListChecks,
} from "lucide-react";

function Section({ icon: Icon, title, children }) {
  return (
    <div className="bg-card border rounded-md p-5">
      <div className="flex items-center gap-2 mb-3">
        <Icon className="w-4 h-4 text-primary" />
        <h3 className="font-heading font-semibold">{title}</h3>
      </div>
      {children}
    </div>
  );
}

export default function KnowledgeRecordDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [rec, setRec] = useState(null);
  const [busy, setBusy] = useState("");

  const load = () => api.get(`/knowledge-records/${id}`).then((r) => setRec(r.data)).catch(() => {});
  useEffect(() => { load(); }, [id]);

  const translate = async () => {
    setBusy("translate");
    try {
      const { data } = await api.post(`/knowledge-records/${id}/translate`);
      setRec(data);
      toast.success("Understanding translation generated");
    } catch { toast.error("Translation failed"); } finally { setBusy(""); }
  };

  const verify = async () => {
    setBusy("verify");
    try {
      const { data } = await api.post(`/knowledge-records/${id}/verify`);
      setRec(data);
      toast.success("Record verified & approved");
    } catch { toast.error("Verification failed"); } finally { setBusy(""); }
  };

  if (!rec) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div className="animate-fade-up">
      <button onClick={() => navigate("/knowledge")} data-testid="kr-back" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="w-4 h-4" /> Knowledge Records
      </button>

      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-xs text-muted-foreground">{rec.kr_code}</span>
            <StatusBadge status={rec.verification_status} testid="kr-detail-status" />
          </div>
          <h1 className="font-heading text-3xl font-bold tracking-tight max-w-3xl">{rec.title}</h1>
          <p className="text-muted-foreground mt-2">{rec.category} · Confidence {rec.confidence_score}% · v{rec.version}
            {rec.reviewer && ` · Verified by ${rec.reviewer}`}</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <button data-testid="kr-translate-btn" onClick={translate} disabled={busy}
            className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors disabled:opacity-60">
            {busy === "translate" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Translate
          </button>
          <button data-testid="kr-verify-btn" onClick={verify} disabled={busy || rec.verification_status === "Verified"}
            className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-success hover:text-success transition-colors disabled:opacity-60">
            {busy === "verify" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />} Verify
          </button>
          <Link to={`/manufacture?kr=${rec.id}`} data-testid="kr-manufacture-btn"
            className="flex items-center gap-2 bg-primary text-primary-foreground px-3 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
            <Factory className="w-4 h-4" /> Manufacture Product
          </Link>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-5">
          <Section icon={BookText} title="Verified Truth">
            <p className="leading-relaxed">{rec.verified_truth}</p>
          </Section>
          <Section icon={Sparkles} title="Consumer Translation">
            {rec.consumer_translation
              ? <p className="leading-relaxed">{rec.consumer_translation}</p>
              : <p className="text-sm text-muted-foreground italic">Not translated yet. Click "Translate" to generate understanding.</p>}
          </Section>
          {rec.everyday_analogy && (
            <Section icon={Lightbulb} title="Everyday Analogy">
              <p className="leading-relaxed">{rec.everyday_analogy}</p>
            </Section>
          )}
          {rec.story && (
            <Section icon={Quote} title="Story">
              <p className="leading-relaxed italic">{rec.story}</p>
            </Section>
          )}
        </div>

        <div className="space-y-5">
          {rec.memory_sentence && (
            <div className="bg-primary text-primary-foreground rounded-md p-5">
              <p className="overline opacity-70 mb-2">Memory Sentence</p>
              <p className="font-heading text-lg font-semibold leading-snug">{rec.memory_sentence}</p>
            </div>
          )}
          {rec.practice_activities?.length > 0 && (
            <Section icon={ListChecks} title="Practice Activities">
              <ul className="space-y-2 text-sm">
                {rec.practice_activities.map((a, i) => (
                  <li key={i} className="flex gap-2"><span className="text-primary font-heading font-bold">{i + 1}</span>{a}</li>
                ))}
              </ul>
            </Section>
          )}
          <Section icon={BookText} title="Record Meta">
            <dl className="text-sm space-y-2">
              <div className="flex justify-between"><dt className="text-muted-foreground">Approval</dt><dd><StatusBadge status={rec.approval_status} /></dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Products created</dt><dd>{rec.products_created}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Created by</dt><dd>{rec.created_by}</dd></div>
            </dl>
          </Section>
          {rec.sources?.length > 0 && (
            <Section icon={Quote} title="Sources">
              <ul className="text-sm space-y-1 text-muted-foreground list-disc pl-4">
                {rec.sources.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </Section>
          )}
        </div>
      </div>
    </div>
  );
}
