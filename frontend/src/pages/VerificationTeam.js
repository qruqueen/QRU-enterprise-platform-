import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { ShieldCheck, Loader2, AlertTriangle, ScrollText, Gavel } from "lucide-react";

export default function VerificationTeam() {
  const [escalations, setEscalations] = useState([]);
  const [log, setLog] = useState([]);
  const [config, setConfig] = useState(null);
  const [running, setRunning] = useState(false);

  const load = async () => {
    const [e, l, c] = await Promise.all([
      api.get("/verification/escalations", { params: { status: "Open" } }),
      api.get("/verification/log", { params: { limit: 60 } }),
      api.get("/verification/config"),
    ]);
    setEscalations(e.data); setLog(l.data.entries || []); setConfig(c.data);
  };
  useEffect(() => { load(); }, []);

  const reviewAll = async () => {
    setRunning(true);
    try {
      const { data } = await api.post("/verification/ai-review-all");
      toast.success(`Queued ${data.queued} record(s) for autonomous verification`);
      setTimeout(load, 4000);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setRunning(false); }
  };

  const resolve = async (id, decision) => {
    try {
      await api.post(`/verification/escalations/${id}/resolve`, { decision });
      toast.success(`Escalation ${decision}d`);
      load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  return (
    <div className="space-y-8" data-testid="verification-team-page">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <p className="overline text-primary mb-1">Autonomous Quality</p>
          <h1 className="font-heading text-3xl font-bold tracking-tight">QRU Verification Team™</h1>
          <p className="text-muted-foreground text-sm mt-1">
            AI verifies every record so the Founder only reviews true exceptions
            {config ? ` (confidence threshold ${config.confidence_threshold}%)` : ""}.
          </p>
        </div>
        <button data-testid="verify-all-btn" onClick={reviewAll} disabled={running}
          className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium disabled:opacity-60">
          {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
          Run AI Verification on Pending
        </button>
      </div>

      {/* Founder escalations */}
      <div className="bg-card border rounded-sm">
        <div className="flex items-center gap-2 p-4 border-b">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          <h2 className="font-heading font-semibold">Founder Escalations</h2>
          <span className="text-xs text-muted-foreground ml-2">Only true exceptions reach you.</span>
        </div>
        <div className="divide-y">
          {escalations.length === 0 && (
            <p className="p-6 text-sm text-muted-foreground text-center" data-testid="no-escalations">
              No open escalations. The Verification Team is handling everything autonomously.
            </p>
          )}
          {escalations.map((e) => (
            <div key={e.id} className="p-4 flex items-start justify-between gap-4" data-testid={`escalation-${e.id}`}>
              <div>
                <p className="font-medium text-sm">{e.kr_code || e.product_code} · {e.title}</p>
                <p className="text-xs text-amber-700 mt-0.5">{e.reason}</p>
                <p className="text-xs text-muted-foreground mt-1">Confidence: {e.confidence_score ?? "—"}%</p>
              </div>
              <div className="flex gap-1 shrink-0">
                <button data-testid={`escalation-approve-${e.id}`} onClick={() => resolve(e.id, "approve")}
                  className="text-xs px-2.5 py-1.5 rounded-sm bg-emerald-600 text-white">Approve</button>
                <button data-testid={`escalation-reject-${e.id}`} onClick={() => resolve(e.id, "reject")}
                  className="text-xs px-2.5 py-1.5 rounded-sm border">Reject</button>
                <button onClick={() => resolve(e.id, "acknowledge")}
                  className="text-xs px-2.5 py-1.5 rounded-sm border">Acknowledge</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Verification log */}
      <div className="bg-card border rounded-sm">
        <div className="flex items-center gap-2 p-4 border-b">
          <ScrollText className="w-4 h-4 text-primary" />
          <h2 className="font-heading font-semibold">Verification Log</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="text-left px-4 py-2">Record</th>
                <th className="text-left px-4 py-2">Decision</th>
                <th className="text-left px-4 py-2">Confidence</th>
                <th className="text-left px-4 py-2">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {log.length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                <Gavel className="w-6 h-6 mx-auto mb-2 opacity-40" />No verification decisions logged yet.</td></tr>}
              {log.map((e, i) => (
                <tr key={i} data-testid={`vlog-row-${i}`}>
                  <td className="px-4 py-2 font-mono text-xs">{e.kr_code}</td>
                  <td className="px-4 py-2">
                    <span className={`text-[11px] px-2 py-0.5 rounded-full ${
                      e.decision === "approve" ? "bg-emerald-100 text-emerald-700" :
                      e.decision === "reject" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"
                    }`}>{e.decision}</span>
                  </td>
                  <td className="px-4 py-2">{e.confidence_score ?? "—"}%</td>
                  <td className="px-4 py-2 text-muted-foreground text-xs max-w-md truncate">{e.reasons}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
