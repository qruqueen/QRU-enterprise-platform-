import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { toast } from "sonner";
import { ShieldCheck, Loader2 } from "lucide-react";

export default function VerificationCenter() {
  const [records, setRecords] = useState([]);
  const [busy, setBusy] = useState("");

  const load = async () => {
    const [draft, review] = await Promise.all([
      api.get("/knowledge-records", { params: { status: "Draft" } }),
      api.get("/knowledge-records", { params: { status: "In Review" } }),
    ]);
    setRecords([...draft.data, ...review.data]);
  };
  useEffect(() => { load().catch(() => {}); }, []);

  const verify = async (id) => {
    setBusy(id);
    try {
      await api.post(`/knowledge-records/${id}/verify`);
      toast.success("Record verified by Verification Lion™");
      await load();
    } catch { toast.error("Verification failed"); } finally { setBusy(""); }
  };

  return (
    <div>
      <PageHeader
        overline="Verification Center"
        title="Guard the Truth"
        description="The Verification Lion™ reviews records. Nothing becomes verified truth without rigorous scrutiny and human approval."
      />

      {records.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="Nothing pending" description="All knowledge records are verified. Excellent." />
      ) : (
        <div className="space-y-3">
          {records.map((r) => (
            <div key={r.id} data-testid={`verify-row-${r.id}`} className="bg-card border rounded-md p-5 flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <span className="font-mono text-xs text-muted-foreground">{r.kr_code}</span>
                  <StatusBadge status={r.verification_status} />
                  <span className="text-xs text-muted-foreground">{r.category}</span>
                </div>
                <Link to={`/knowledge/${r.id}`} className="font-medium hover:text-primary transition-colors">{r.title}</Link>
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{r.verified_truth}</p>
              </div>
              <button data-testid={`verify-btn-${r.id}`} onClick={() => verify(r.id)} disabled={busy === r.id}
                className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors shrink-0 disabled:opacity-60">
                {busy === r.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />} Verify & Approve
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
