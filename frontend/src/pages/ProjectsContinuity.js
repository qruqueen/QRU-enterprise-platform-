import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import { Loader2, Workflow, CheckCircle2, Circle, Clock, ShieldAlert, Lock, Play, Pause, Square, ArrowRight, ThumbsUp } from "lucide-react";

const STAGE_ICON = { complete: CheckCircle2, in_progress: Clock, needs_approval: ShieldAlert, blocked: Lock, pending: Circle, pending_connector: Lock };
const STAGE_TONE = { complete: "emerald", in_progress: "blue", needs_approval: "amber", blocked: "rose", pending: "slate" };

export default function ProjectsContinuity() {
  const nav = useNavigate();
  const [projects, setProjects] = useState(null);
  const [busy, setBusy] = useState(null);

  const load = () => api.get("/factory-os/projects").then((r) => setProjects(r.data.projects)).catch(() => setProjects(false));
  useEffect(() => { load(); }, []);

  const act = async (pid, path, body) => {
    setBusy(pid + path);
    try {
      const { data } = await api.post(`/factory-os/projects/${pid}/${path}`, body || {});
      setProjects((ps) => ps.map((p) => (p.id === pid ? data : p)));
      if (path === "approve") toast.success("Approved — continuing automatically.");
      if (path === "complete-stage") toast.success("Stage complete — continuing.");
    } catch (e) { toast.error(e.response?.data?.detail || "Action failed."); }
    finally { setBusy(null); }
  };

  if (projects === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (projects === false) return <p className="text-sm text-muted-foreground p-8">Could not load projects.</p>;

  return (
    <div data-testid="projects-page">
      <PageHeader
        overline="Product Continuity Principle™ · Governed by QRU-CON-0001 §4/§14G"
        title="My Projects"
        description="Every project continues automatically through each approved downstream stage until it reaches its intended human experience — pausing only for your approval, a stage that needs setup, or when you pause it. The Factory thinks in completed experiences, not files."
        actions={<VerifiedBadge label="Continuous governed manufacturing" testid="projects-badge" />}
      />

      {projects.length === 0 ? (
        <Panel title="No projects yet" icon={Workflow} accent="royal" testid="projects-empty">
          <p className="text-sm text-muted-foreground mb-3">Start on the Create page and the Factory will track every project from intention to distribution here.</p>
          <button onClick={() => nav("/create")} data-testid="projects-goto-create" className="inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm font-bold text-sm">Create something <ArrowRight className="w-4 h-4" /></button>
        </Panel>
      ) : (
        <div className="space-y-5">
          {projects.map((p) => {
            const s = p.summary;
            const cur = p.chain.find((st) => ["in_progress", "needs_approval", "blocked"].includes(st.status));
            return (
              <Panel key={p.id} title={`${p.outcome_name} · ${p.topic}`} icon={Workflow} accent={p.mode === "stopped" ? "slate" : "gold"} testid={`project-${p.id}`}>
                <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <StatusChip status={`${s.completed_count}/${s.total} stages`} tone="blue" />
                    <StatusChip status={p.mode === "auto_continue" ? "Auto-continue" : p.mode === "paused" ? "Paused" : "Stopped"} tone={p.mode === "auto_continue" ? "emerald" : "amber"} />
                    {p.knowledge_record && <span className="text-[10px] text-muted-foreground">KR {p.knowledge_record.kr_code}</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    {p.mode !== "paused" ? (
                      <button onClick={() => act(p.id, "mode", { mode: "paused" })} data-testid={`project-pause-${p.id}`} className="text-[11px] inline-flex items-center gap-1 border border-navy/20 text-navy px-2 py-1 rounded-sm"><Pause className="w-3 h-3" /> Pause</button>
                    ) : (
                      <button onClick={() => act(p.id, "mode", { mode: "auto_continue" })} data-testid={`project-resume-${p.id}`} className="text-[11px] inline-flex items-center gap-1 bg-emerald-600 text-white px-2 py-1 rounded-sm"><Play className="w-3 h-3" /> Resume</button>
                    )}
                    <button onClick={() => act(p.id, "mode", { mode: "stopped" })} data-testid={`project-stop-${p.id}`} className="text-[11px] inline-flex items-center gap-1 border border-red-300 text-red-600 px-2 py-1 rounded-sm"><Square className="w-3 h-3" /> Stop</button>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full h-2 rounded-full bg-navy/[0.08] mb-3 overflow-hidden"><div className="h-full bg-gold transition-all" style={{ width: `${s.percent}%` }} /></div>

                {/* Stage pipeline */}
                <div className="flex flex-wrap gap-1.5 mb-3" data-testid={`project-stages-${p.id}`}>
                  {p.chain.map((st) => {
                    const SI = STAGE_ICON[st.status] || Circle;
                    return (
                      <span key={st.id} className={`inline-flex items-center gap-1 text-[10px] px-2 py-1 rounded-full border ${st.status === "complete" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : st.status === "in_progress" ? "bg-blue-50 text-blue-700 border-blue-200" : st.status === "needs_approval" ? "bg-amber-50 text-amber-700 border-amber-200" : st.status === "blocked" ? "bg-rose-50 text-rose-700 border-rose-200" : "bg-navy/[0.04] text-navy/50 border-navy/10"}`}>
                        <SI className="w-3 h-3" /> {st.name}
                      </span>
                    );
                  })}
                </div>

                {/* Recommended next action */}
                <div className="border-t pt-3 flex items-center justify-between flex-wrap gap-2">
                  <p className="text-[12px] text-navy" data-testid={`project-next-${p.id}`}><b className="text-royal">Next:</b> {s.recommended_next_action}</p>
                  <div className="flex items-center gap-2">
                    {cur?.status === "needs_approval" && (
                      <button onClick={() => act(p.id, "approve")} disabled={busy} data-testid={`project-approve-${p.id}`} className="text-[11px] inline-flex items-center gap-1 bg-emerald-600 text-white px-3 py-1.5 rounded-sm font-medium"><ThumbsUp className="w-3 h-3" /> Approve & continue</button>
                    )}
                    {cur?.status === "in_progress" && cur?.route && (
                      <>
                        <button onClick={() => nav(cur.route)} data-testid={`project-open-${p.id}`} className="text-[11px] inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded-sm font-medium">Open workflow <ArrowRight className="w-3 h-3" /></button>
                        <button onClick={() => act(p.id, "complete-stage")} disabled={busy} data-testid={`project-complete-${p.id}`} className="text-[11px] inline-flex items-center gap-1 border border-navy/20 text-navy px-3 py-1.5 rounded-sm font-medium">Mark stage done</button>
                      </>
                    )}
                    {cur?.status === "blocked" && cur?.route && (
                      <button onClick={() => nav(cur.route)} data-testid={`project-setup-${p.id}`} className="text-[11px] inline-flex items-center gap-1 bg-gold text-navy px-3 py-1.5 rounded-sm font-medium">{cur.id === "knowledge_record" || cur.kind === "auto" ? "Manufacture the Knowledge Record" : "Set up destination"} <ArrowRight className="w-3 h-3" /></button>
                    )}
                  </div>
                </div>
              </Panel>
            );
          })}
        </div>
      )}
    </div>
  );
}
