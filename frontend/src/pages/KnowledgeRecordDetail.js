import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/api";
import { StatusBadge, TreasureBadge, QRUMethodology } from "@/components/shared";
import { toast } from "sonner";
import { ArrowLeft, Wand2, Factory, Loader2, BookText, Quote, ShieldCheck } from "lucide-react";

export default function KnowledgeRecordDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [rec, setRec] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => api.get(`/knowledge-records/${id}`).then((r) => setRec(r.data)).catch(() => {});
  useEffect(() => { load(); }, [id]);

  const manufacture = async () => {
    setBusy(true);
    try {
      const { data } = await api.post(`/knowledge-records/${id}/manufacture-understanding`);
      setRec(data);
      toast.success("Understanding manufactured — new sections marked Draft for review");
    } catch { toast.error("Manufacturing failed — try again"); } finally { setBusy(false); }
  };

  if (!rec) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div className="animate-fade-up">
      <button onClick={() => navigate("/knowledge")} data-testid="kr-back" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="w-4 h-4" /> Knowledge Records
      </button>

      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            <span className="font-mono text-xs text-muted-foreground">{rec.kr_code}</span>
            <StatusBadge status={rec.verification_status} testid="kr-detail-status" />
            {rec.is_master_file && <span className="text-[11px] px-2 py-0.5 rounded-sm border border-primary/30 bg-primary/10 text-primary font-medium">Knowledge Master File™</span>}
            {rec.treasure_standard && <TreasureBadge testid="kr-treasure" />}
          </div>
          <h1 className="font-heading text-3xl font-bold tracking-tight max-w-3xl">{rec.title}</h1>
          <p className="text-muted-foreground mt-2">{rec.category} · Confidence {rec.confidence_score}% · v{rec.version}
            {rec.reviewer && ` · Reviewed by ${rec.reviewer}`}</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <button data-testid="kr-manufacture-understanding-btn" onClick={manufacture} disabled={busy}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-3 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60">
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} Manufacture Understanding
          </button>
          <Link to="/verification" data-testid="kr-review-link"
            className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors">
            <ShieldCheck className="w-4 h-4" /> Review
          </Link>
          <Link to={`/manufacture?kr=${rec.id}`} data-testid="kr-manufacture-btn"
            className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors">
            <Factory className="w-4 h-4" /> Products
          </Link>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <p className="overline text-primary mb-3">QRU Teaching Methodology</p>
          <QRUMethodology record={rec} sectionStatus={rec.section_status || {}} />
        </div>

        <div className="space-y-5">
          <div className="bg-card border rounded-md p-5">
            <div className="flex items-center gap-2 mb-3"><BookText className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">Verified Truth</h3></div>
            <p className="text-sm leading-relaxed">{rec.verified_truth}</p>
          </div>
          <div className="bg-card border rounded-md p-5">
            <h3 className="font-heading font-semibold mb-3">Record Meta</h3>
            <dl className="text-sm space-y-2">
              <div className="flex justify-between"><dt className="text-muted-foreground">Division</dt><dd>{rec.division || "Health"}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Approval</dt><dd><StatusBadge status={rec.approval_status} /></dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Understanding</dt><dd>{rec.understanding_status}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Products created</dt><dd>{rec.products_created}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Created by</dt><dd>{rec.created_by}</dd></div>
            </dl>
          </div>
          {rec.sources?.length > 0 && (
            <div className="bg-card border rounded-md p-5">
              <div className="flex items-center gap-2 mb-3"><Quote className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">Sources</h3></div>
              <ul className="text-sm space-y-1 text-muted-foreground list-disc pl-4">
                {rec.sources.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
