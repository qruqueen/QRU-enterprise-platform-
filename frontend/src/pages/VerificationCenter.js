import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Slider } from "@/components/ui/slider";
import { toast } from "sonner";
import { ShieldCheck, Loader2, CheckCircle2, XCircle, RotateCcw, Eye } from "lucide-react";

const FIELDS = [
  ["evidence", "Evidence", "Summarize the supporting evidence…"],
  ["observed_facts", "Observed Facts", "What can be directly observed?"],
  ["calculated_data", "Calculated Data", "Any figures, calculations, or measured data?"],
  ["analytical_judgment", "Analytical Judgment", "Your professional analytical assessment…"],
  ["conflicting_evidence", "Conflicting Evidence", "Any evidence that contradicts the claim?"],
  ["open_questions", "Open Questions", "What remains uncertain or unresolved?"],
  ["reviewer_comments", "Reviewer Comments", "Notes for the record…"],
];

function ReviewDialog({ record, onDone, onClose }) {
  const [form, setForm] = useState({
    confidence_score: record?.confidence_score || 80, sources_text: (record?.sources || []).join("\n"),
    evidence: "", observed_facts: "", calculated_data: "", analytical_judgment: "",
    conflicting_evidence: "", open_questions: "", reviewer_comments: "",
  });
  const [busy, setBusy] = useState("");

  const submit = async (decision) => {
    setBusy(decision);
    try {
      await api.post(`/knowledge-records/${record.id}/review`, {
        decision,
        confidence_score: form.confidence_score,
        sources: form.sources_text.split("\n").map((s) => s.trim()).filter(Boolean),
        evidence: form.evidence, observed_facts: form.observed_facts,
        calculated_data: form.calculated_data, analytical_judgment: form.analytical_judgment,
        conflicting_evidence: form.conflicting_evidence, open_questions: form.open_questions,
        reviewer_comments: form.reviewer_comments,
      });
      const msg = { approve: "Record verified & approved", reject: "Record rejected", request_revision: "Revision requested" }[decision];
      toast.success(msg);
      onDone();
    } catch { toast.error("Review failed"); } finally { setBusy(""); }
  };

  return (
    <Dialog open={!!record} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="rounded-md max-w-2xl max-h-[88vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-heading flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-primary" /> Verification Review — {record?.kr_code}
          </DialogTitle>
          <DialogDescription className="sr-only">Evaluate evidence and decide to approve, reject, or request revision.</DialogDescription>
        </DialogHeader>
        <p className="text-sm font-medium">{record?.title}</p>
        <p className="text-sm text-muted-foreground mb-2">{record?.verified_truth}</p>

        <div className="space-y-4 py-2">
          <div>
            <div className="flex justify-between text-sm font-medium mb-2">
              <span>Confidence Score</span><span className="text-primary">{form.confidence_score}%</span>
            </div>
            <Slider data-testid="review-confidence" value={[form.confidence_score]} max={100} step={1}
              onValueChange={(v) => setForm({ ...form, confidence_score: v[0] })} />
          </div>
          <div>
            <label className="text-sm font-medium">Sources (one per line)</label>
            <textarea data-testid="review-sources" rows={2} value={form.sources_text}
              onChange={(e) => setForm({ ...form, sources_text: e.target.value })}
              className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm resize-none" />
          </div>
          {FIELDS.map(([key, label, ph]) => (
            <div key={key}>
              <label className="text-sm font-medium">{label}</label>
              <textarea data-testid={`review-${key}`} rows={2} value={form[key]} placeholder={ph}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm resize-none" />
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-2 pt-2 border-t sticky bottom-0 bg-card">
          <button data-testid="review-approve" onClick={() => submit("approve")} disabled={busy}
            className="flex items-center gap-2 bg-success text-white px-4 py-2 rounded-sm text-sm font-medium hover:opacity-90 disabled:opacity-60">
            {busy === "approve" ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />} Approve
          </button>
          <button data-testid="review-revision" onClick={() => submit("request_revision")} disabled={busy}
            className="flex items-center gap-2 border px-4 py-2 rounded-sm text-sm font-medium hover:border-warning transition-colors disabled:opacity-60"
            style={{ color: "hsl(var(--navy))" }}>
            {busy === "request_revision" ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} Request Revision
          </button>
          <button data-testid="review-reject" onClick={() => submit("reject")} disabled={busy}
            className="flex items-center gap-2 border border-destructive/40 text-destructive px-4 py-2 rounded-sm text-sm font-medium hover:bg-destructive/5 disabled:opacity-60">
            {busy === "reject" ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />} Reject
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function VerificationCenter() {
  const [needs, setNeeds] = useState([]);
  const [awaiting, setAwaiting] = useState([]);
  const [counts, setCounts] = useState({ verified: 0, pending: 0, awaiting_manufacturing: 0, total: 0 });
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState("");

  const load = async () => {
    const res = await api.get("/verification/queue");
    setNeeds(res.data.needs_verification || []);
    setAwaiting(res.data.awaiting_manufacturing || []);
    setCounts(res.data.counts || {});
  };
  useEffect(() => { load().catch(() => {}); }, []);

  const verifyKr2 = async (id, decision) => {
    setBusy(id + decision);
    try {
      await api.post(`/verification/kr2/${id}/verify`, { decision });
      toast.success(decision === "approve" ? "Marked Verified External™ · Gold Standard." : "Record rejected.");
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Action failed."); }
    finally { setBusy(""); }
  };

  const allClear = counts.pending === 0 && counts.awaiting_manufacturing === 0;

  return (
    <div>
      <PageHeader
        overline="Verification Center · Verification Lion™"
        title="Guard the Truth"
        description="Reviewers evaluate evidence, sources, observed facts, calculated data, and conflicting evidence — then Approve, Reject, or Request Revision. Nothing becomes verified truth without rigorous scrutiny."
      />

      <div className="flex flex-wrap gap-2 mb-6" data-testid="verification-counts">
        <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-emerald-100 text-emerald-700" data-testid="count-verified">✓ {counts.verified} verified</span>
        <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-amber-100 text-amber-800" data-testid="count-pending">{counts.pending} need verification</span>
        {counts.awaiting_manufacturing > 0 && <span className="text-xs font-bold px-3 py-1.5 rounded-full bg-blue-50 text-blue-700" data-testid="count-awaiting">{counts.awaiting_manufacturing} awaiting manufacturing</span>}
        <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-navy/5 text-navy">{counts.total} total</span>
      </div>

      {allClear && needs.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="Nothing pending" description={`All ${counts.verified} knowledge records are verified. Excellent.`} />
      ) : (
        <div className="space-y-8">
          {needs.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-navy mb-3">Needs your verification ({needs.length})</h3>
              <div className="space-y-3">
                {needs.map((r) => (
                  <div key={r.id} data-testid={`verify-row-${r.id}`} className="bg-card border rounded-md p-5 flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-1 flex-wrap">
                        <span className="font-mono text-xs text-muted-foreground">{r.code}</span>
                        <StatusBadge status={r.status} />
                        {r.collection === "kr2" && <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">KR 2.0</span>}
                        <span className="text-xs text-muted-foreground">{r.category}</span>
                      </div>
                      <Link to={r.collection === "kr2" ? `/knowledge` : `/knowledge/${r.id}`} className="font-medium hover:text-primary transition-colors">{r.title}</Link>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{r.summary}</p>
                    </div>
                    {r.collection === "kr2" ? (
                      <div className="flex items-center gap-2 shrink-0">
                        <button data-testid={`kr2-approve-${r.id}`} disabled={busy === r.id + "approve"} onClick={() => verifyKr2(r.id, "approve")}
                          className="flex items-center gap-1.5 bg-emerald-600 text-white px-3 py-2 rounded-sm text-sm font-medium hover:bg-emerald-700 disabled:opacity-50">
                          <CheckCircle2 className="w-4 h-4" /> Mark Verified External™
                        </button>
                        <button data-testid={`kr2-reject-${r.id}`} disabled={busy === r.id + "reject"} onClick={() => verifyKr2(r.id, "reject")}
                          className="flex items-center gap-1.5 border px-3 py-2 rounded-sm text-sm font-medium hover:bg-red-50 text-red-600">
                          <XCircle className="w-4 h-4" /> Reject
                        </button>
                      </div>
                    ) : (
                      <button data-testid={`verify-open-${r.id}`} onClick={() => setSelected(r)}
                        className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors shrink-0">
                        <Eye className="w-4 h-4" /> Review
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {awaiting.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-navy mb-1">Awaiting full manufacturing ({awaiting.length})</h3>
              <p className="text-xs text-muted-foreground mb-3">These are Topic Seeds — the knowledge hasn't been fully manufactured yet, so they can't be verified until their full content is generated.</p>
              <div className="space-y-2">
                {awaiting.map((r) => (
                  <div key={r.id} data-testid={`awaiting-row-${r.id}`} className="bg-blue-50/40 border border-blue-100 rounded-md p-4 flex items-center gap-3">
                    <span className="font-mono text-[11px] text-muted-foreground">{r.code}</span>
                    <Link to={`/knowledge/${r.id}`} className="text-sm font-medium hover:text-primary flex-1 min-w-0 truncate">{r.title}</Link>
                    <StatusBadge status={r.status} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {selected && <ReviewDialog record={selected} onClose={() => setSelected(null)} onDone={() => { setSelected(null); load(); }} />}
    </div>
  );
}
