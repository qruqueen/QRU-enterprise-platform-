import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Loader2, Compass, MapPin, ArrowRight, HelpCircle, AlertTriangle, CheckCircle2, CircleDot, Circle } from "lucide-react";

// QRU Manufacturing GPS™ + Why-Am-I-Here™ (STD-EIP-0002) — persistent production awareness on any project.
export function ManufacturingGPS({ projectId, route = "/projects" }) {
  const [nsi, setNsi] = useState(null);
  const [why, setWhy] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (projectId) api.get(`/flow/next-stage/${projectId}`).then((r) => setNsi(r.data)).catch(() => setNsi(false));
    api.get(`/architecture/why?route=${encodeURIComponent(route)}`).then((r) => setWhy(r.data)).catch(() => {});
  }, [projectId, route]);

  const healthTone = { "On Track": "text-emerald-600", "Awaiting Approval": "text-amber-600", Blocked: "text-red-600", Complete: "text-emerald-600" };

  return (
    <div className="border border-navy/15 rounded-md bg-white mb-4" data-testid="manufacturing-gps">
      <div className="flex items-center justify-between px-3 py-2 border-b border-navy/10 bg-navy/[0.03]">
        <span className="text-[11px] font-bold text-navy inline-flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-royal" /> Manufacturing GPS™</span>
        {nsi && nsi !== false && <span className={`text-[10px] font-bold ${healthTone[nsi.production_health] || "text-navy"}`}>{nsi.production_health} · {nsi.percent}%</span>}
      </div>
      {nsi && nsi !== false ? (
        <div className="p-3">
          <div className="flex items-center gap-2 text-[11px] mb-2 flex-wrap" data-testid="gps-timeline">
            {nsi.previous_stage && <span className="inline-flex items-center gap-1 text-emerald-600"><CheckCircle2 className="w-3 h-3" />{nsi.previous_stage}</span>}
            <CircleDot className="w-3 h-3 text-royal shrink-0" />
            <span className="font-bold text-navy">{nsi.current_stage}</span>
            {nsi.next_stage && nsi.next_stage !== "Complete" && <><ArrowRight className="w-3 h-3 text-navy/30" /><span className="inline-flex items-center gap-1 text-navy/50"><Circle className="w-3 h-3" />{nsi.next_stage}</span></>}
          </div>
          <p className="text-[11px] text-navy/80 flex items-start gap-1.5"><ArrowRight className="w-3 h-3 mt-0.5 shrink-0 text-royal" />{nsi.recommended_next_action}</p>
          {nsi.blockers?.length > 0 && <p className="text-[10px] text-red-600 mt-1 flex items-start gap-1"><AlertTriangle className="w-3 h-3 mt-0.5" />{nsi.blockers[0].reason}</p>}
          {nsi.approvals_required?.length > 0 && <p className="text-[10px] text-amber-700 mt-1">Waiting on your approval: {nsi.approvals_required.join(", ")}</p>}
          {nsi.remaining_stages?.length > 0 && <p className="text-[9px] text-muted-foreground mt-1">Remaining: {nsi.remaining_stages.join(" · ")}</p>}
        </div>
      ) : (
        <p className="p-3 text-[11px] text-muted-foreground">{nsi === false ? "Select a project to see its location in the flow." : "Loading production location…"}</p>
      )}

      {/* Why Am I Here */}
      {why && (
        <div className="border-t border-navy/10">
          <button onClick={() => setOpen((v) => !v)} data-testid="gps-why-toggle" className="w-full flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold text-royal">
            <HelpCircle className="w-3 h-3" /> Why am I here? {open ? "▲" : "▼"}
          </button>
          {open && (
            <div className="px-3 pb-3 text-[10px] text-navy/80 space-y-1" data-testid="gps-why-content">
              <p><b>Why:</b> {why.why}</p>
              <p><b>Objective:</b> {why.objective}</p>
              <p><b>Success:</b> {why.success}</p>
              <p><b>Next:</b> {why.next}</p>
              <p className="text-amber-700"><b>Common mistakes:</b> {why.common_mistakes?.join("; ")}</p>
              <p className="text-muted-foreground">Governed by {why.standards?.join(", ")} · Domain: {why.domain}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
