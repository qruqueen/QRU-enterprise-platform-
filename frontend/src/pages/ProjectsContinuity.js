import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { ManufacturingGPS } from "@/components/ManufacturingGPS";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import { Loader2, Workflow, CheckCircle2, Circle, Clock, ShieldAlert, Lock, Play, Pause, Square, ArrowRight, ThumbsUp, Award, FileText, ChevronDown, ChevronRight, Download } from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";

const STAGE_ICON = { complete: CheckCircle2, in_progress: Clock, needs_approval: ShieldAlert, blocked: Lock, pending: Circle, pending_connector: Lock };
const STAGE_TONE = { complete: "emerald", in_progress: "blue", needs_approval: "amber", blocked: "rose", pending: "slate" };

export default function ProjectsContinuity() {
  const nav = useNavigate();
  const [projects, setProjects] = useState(null);
  const [effort, setEffort] = useState(null);
  const [busy, setBusy] = useState(null);
  const [itemsOpen, setItemsOpen] = useState({});
  const [items, setItems] = useState({});
  const [itemsLoading, setItemsLoading] = useState(null);

  const toggleItems = async (pid) => {
    const willOpen = !itemsOpen[pid];
    setItemsOpen((o) => ({ ...o, [pid]: willOpen }));
    if (willOpen && !items[pid]) {
      setItemsLoading(pid);
      try {
        const { data } = await api.get(`/factory-os/projects/${pid}/items`);
        setItems((m) => ({ ...m, [pid]: data }));
      } catch { toast.error("Could not load items."); }
      finally { setItemsLoading(null); }
    }
  };

  const load = () => api.get("/factory-os/projects").then((r) => setProjects(r.data.projects)).catch(() => setProjects(false));
  useEffect(() => {
    load();
    api.get("/factory-os/effort-summary").then((r) => setEffort(r.data)).catch(() => {});
  }, []);

  const act = async (pid, path, body) => {
    setBusy(pid + path);
    try {
      const { data } = await api.post(`/factory-os/projects/${pid}/${path}`, body || {});
      setProjects((ps) => ps.map((p) => (p.id === pid ? data : p)));
      if (data?.requires_certification) toast.message("Gold Master needs certification (QA 100), not simple approval.");
      else if (path === "approve") toast.success("Approved — continuing automatically.");
      if (path === "complete-stage") toast.success("Stage complete — continuing.");
    } catch (e) { toast.error(e.response?.data?.detail || "Action failed."); }
    finally { setBusy(null); }
  };

  const certifyGoldMaster = async (p) => {
    if (!p.showcase_asset_id) { nav("/flagship-showcase"); return; }
    setBusy(p.id + "certify");
    try {
      await api.post(`/media-library/showcase/${p.showcase_asset_id}/certify-gold-master`);
      toast.success("Gold Master Certified™.");
      const { data } = await api.get(`/factory-os/projects/${p.id}`);
      setProjects((ps) => ps.map((x) => (x.id === p.id ? data : x)));
    } catch (e) { toast.error(e.response?.data?.detail || "Certification blocked — QA gates must pass."); }
    finally { setBusy(null); }
  };

  const renderProduct = async (p) => {
    setBusy(p.id + "render");
    toast.message("Manufacturing your product from the verified Knowledge Record…");
    try {
      const { data } = await api.post(`/factory-os/projects/${p.id}/render`);
      if (data?.project) setProjects((ps) => ps.map((x) => (x.id === p.id ? data.project : x)));
      const primary = (data.deliverables || []).find((f) => f.format === "pdf") || (data.deliverables || [])[0];
      toast.success("Product manufactured — your downloadable file is ready.");
      setItems((m) => ({ ...m, [p.id]: undefined }));
      setItemsOpen((o) => ({ ...o, [p.id]: true }));
      const { data: it } = await api.get(`/factory-os/projects/${p.id}/items`);
      setItems((m) => ({ ...m, [p.id]: it }));
      if (primary?.url) window.open(`${BACKEND}${primary.url}`, "_blank");
    } catch (e) { toast.error(e.response?.data?.detail || "Could not manufacture the product."); }
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

      {effort && (effort.minutes_saved > 0 || effort.automated_actions > 0) && (
        <div className="qru-card p-4 mb-6 border-l-4 border-gold bg-gold/[0.04]" data-testid="projects-effort">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="overline text-royal">Founder Freedom Ledger</p>
              <p className="text-sm text-navy mt-0.5">The Factory has absorbed <b>{effort.hours_saved}h</b> of operational effort across <b>{effort.automated_actions}</b> automated actions — {effort.auto_published} auto-published. You decide, approve, and lead; the civilization executes.</p>
            </div>
            <div className="flex flex-wrap gap-1">{effort.eliminated_tasks.map((t) => <span key={t} className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 line-through">{t}</span>)}</div>
          </div>
        </div>
      )}

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

                {/* Manufacturing GPS™ — persistent production awareness (STD-EIP-0002) */}
                <ManufacturingGPS projectId={p.id} route="/projects" />

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
                    {cur?.status === "needs_approval" && cur?.id === "gold_master" && (
                      <button onClick={() => certifyGoldMaster(p)} disabled={busy} data-testid={`project-certify-gm-${p.id}`} className="text-[11px] inline-flex items-center gap-1 bg-gold text-navy px-3 py-1.5 rounded-sm font-bold"><Award className="w-3 h-3" /> Certify Gold Master™</button>
                    )}
                    {cur?.status === "needs_approval" && cur?.id !== "gold_master" && (
                      <button onClick={() => act(p.id, "approve")} disabled={busy} data-testid={`project-approve-${p.id}`} className="text-[11px] inline-flex items-center gap-1 bg-emerald-600 text-white px-3 py-1.5 rounded-sm font-medium"><ThumbsUp className="w-3 h-3" /> Approve & continue</button>
                    )}
                    {cur?.status === "in_progress" && cur?.route && (
                      <>
                        {!["video", "podcast", "audiobook"].includes(p.outcome_id) && (
                          <button onClick={() => renderProduct(p)} disabled={busy === p.id + "render"} data-testid={`project-render-${p.id}`}
                            className="text-[11px] inline-flex items-center gap-1 bg-gold text-navy px-3 py-1.5 rounded-sm font-bold disabled:opacity-60">
                            {busy === p.id + "render" ? <Loader2 className="w-3 h-3 animate-spin" /> : <FileText className="w-3 h-3" />}
                            Manufacture the {p.outcome_name}
                          </button>
                        )}
                        <button onClick={() => nav(cur.route + (cur.route === "/flagship-showcase" ? `?project=${p.id}` : ""))} data-testid={`project-open-${p.id}`} className="text-[11px] inline-flex items-center gap-1 border border-navy/20 text-navy px-3 py-1.5 rounded-sm font-medium">Open workflow <ArrowRight className="w-3 h-3" /></button>
                      </>
                    )}
                    {cur?.status === "blocked" && cur?.route && (
                      <button onClick={() => nav(cur.route)} data-testid={`project-setup-${p.id}`} className="text-[11px] inline-flex items-center gap-1 bg-gold text-navy px-3 py-1.5 rounded-sm font-medium">{cur.id === "knowledge_record" || cur.kind === "auto" ? "Manufacture the Knowledge Record" : "Set up destination"} <ArrowRight className="w-3 h-3" /></button>
                    )}
                  </div>
                </div>

                {/* View items — governed script/narration + produced deliverables */}
                <div className="mt-3 border-t pt-3" data-testid={`project-items-wrap-${p.id}`}>
                  <button onClick={() => toggleItems(p.id)} data-testid={`project-view-items-${p.id}`}
                    className="inline-flex items-center gap-1.5 text-[11px] font-bold text-royal hover:text-navy transition-colors">
                    <FileText className="w-3.5 h-3.5" /> View items {itemsOpen[p.id] ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  </button>
                  {itemsOpen[p.id] && (
                    <div className="mt-2" data-testid={`project-items-${p.id}`}>
                      {itemsLoading === p.id ? (
                        <p className="text-[11px] text-muted-foreground flex items-center gap-1"><Loader2 className="w-3 h-3 animate-spin" /> Loading items…</p>
                      ) : items[p.id] ? (
                        <div className="space-y-3">
                          {/* Script & narration */}
                          {items[p.id].script?.available ? (
                            <div className="border border-navy/10 rounded-md p-3 bg-navy/[0.02]" data-testid={`project-script-${p.id}`}>
                              <p className="text-[10px] font-bold uppercase tracking-wide text-navy mb-1.5">Video Script & Narration <span className="text-muted-foreground font-normal">· from {items[p.id].kr?.code || "verified KR"}</span></p>
                              <ol className="space-y-1.5 list-decimal ml-4">
                                {items[p.id].script.scenes.map((sc) => (
                                  <li key={sc.n} className="text-[11px] text-navy">
                                    <span>{sc.beat}</span>
                                    <span className="block text-[10px] text-muted-foreground italic">Visual: {sc.visual}</span>
                                  </li>
                                ))}
                              </ol>
                            </div>
                          ) : items[p.id].script?.reason ? (
                            <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-md p-2" data-testid={`project-script-pending-${p.id}`}>{items[p.id].script.reason}</p>
                          ) : null}

                          {/* Deliverables */}
                          {items[p.id].deliverables?.length > 0 ? (
                            <div data-testid={`project-deliverables-${p.id}`}>
                              <p className="text-[10px] font-bold uppercase tracking-wide text-navy mb-1">Produced deliverables</p>
                              <div className="flex flex-wrap gap-1.5">
                                {items[p.id].deliverables.map((d, i) => (
                                  <a key={i} href={`${BACKEND}${d.url}`} target="_blank" rel="noreferrer" data-testid={`project-deliverable-${p.id}-${i}`}
                                    className="inline-flex items-center gap-1 text-[10px] border border-navy/15 rounded-sm px-2 py-1 text-navy hover:border-royal">
                                    <Download className="w-3 h-3" /> {d.label}
                                  </a>
                                ))}
                              </div>
                            </div>
                          ) : (
                            <p className="text-[11px] text-muted-foreground">No downloadable deliverables produced yet for this project.</p>
                          )}
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>

                {/* Auto-linked published destinations (zero-touch) */}
                {(p.published_to || []).length > 0 && (
                  <div className="mt-3 border-t pt-3" data-testid={`project-published-${p.id}`}>
                    <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-700 mb-1">Published destinations</p>
                    {p.published_to.map((d, i) => (
                      <div key={i} className="flex items-center gap-2 text-[11px] text-navy">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                        <span className="capitalize font-semibold">{d.platform}</span>
                        <a href={d.url} target="_blank" rel="noreferrer" className="text-royal underline font-mono">{d.video_id}</a>
                        <span className="text-muted-foreground">· {new Date(d.at).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Failure isolation — Gold Master preserved, retry per destination */}
                {(p.failed_destinations || []).length > 0 && (
                  <div className="mt-2 border border-rose-200 bg-rose-50 rounded-sm p-2" data-testid={`project-failed-${p.id}`}>
                    <p className="text-[10px] font-bold uppercase tracking-wide text-rose-700 mb-1">Publishing needs attention (Gold Master preserved)</p>
                    {p.failed_destinations.map((f, i) => (
                      <div key={i} className="flex items-center justify-between text-[11px] text-rose-700">
                        <span><b className="capitalize">{f.platform}</b> — {f.reason}</span>
                        <button onClick={() => nav("/youtube")} data-testid={`project-retry-${p.id}`} className="inline-flex items-center gap-1 border border-rose-300 px-2 py-0.5 rounded-sm">Retry</button>
                      </div>
                    ))}
                  </div>
                )}
              </Panel>
            );
          })}
        </div>
      )}
    </div>
  );
}
