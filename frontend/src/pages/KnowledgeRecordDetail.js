import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/api";
import { StatusBadge, TreasureBadge, SectionStatusPill, FieldValue, fieldLabel } from "@/components/shared";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { toast } from "sonner";
import {
  ArrowLeft, Factory, Loader2, BookText, ShieldCheck, RefreshCw, Check, Boxes, CheckCircle2, XCircle, Clock, Sprout,
} from "lucide-react";

export default function KnowledgeRecordDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [rec, setRec] = useState(null);
  const [schema, setSchema] = useState([]);
  const [job, setJob] = useState(null);
  const [fieldBusy, setFieldBusy] = useState("");
  const pollRef = useRef(null);

  const load = () => api.get(`/knowledge-records/${id}`).then((r) => setRec(r.data)).catch(() => {});
  useEffect(() => {
    load();
    api.get("/manufacturing-jobs/schema").then((r) => setSchema(r.data.groups)).catch(() => {});
    return () => clearInterval(pollRef.current);
  }, [id]);

  const pollJob = (jid) => {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const { data } = await api.get(`/manufacturing-jobs/${jid}`);
      setJob(data);
      if (data.status !== "running") {
        clearInterval(pollRef.current);
        load();
        if (data.status === "complete") toast.success(`Understanding manufactured — ${data.fields_manufactured} fields ready for review`);
        setTimeout(() => setJob(null), 4000);
      }
    }, 2500);
  };

  const manufactureAll = async () => {
    try {
      const { data } = await api.post(`/knowledge-records/${id}/manufacture-all`);
      toast.success("AI Manufacturing Pipeline started");
      setJob({ status: "running", progress: 0, current_step: "Starting…", steps: [] });
      pollJob(data.job_id);
    } catch { toast.error("Failed to start manufacturing"); }
  };

  const regen = async (field) => {
    setFieldBusy(field);
    try { const { data } = await api.post(`/knowledge-records/${id}/fields/${field}/regenerate`); setRec(data); toast.success(`${fieldLabel(field)} regenerated`); }
    catch { toast.error("Regeneration failed"); } finally { setFieldBusy(""); }
  };

  const approveField = async (field) => {
    try { const { data } = await api.patch(`/knowledge-records/${id}/fields/${field}/approve`, { status: "Approved" }); setRec(data); toast.success(`${fieldLabel(field)} approved`); }
    catch { toast.error("Failed"); }
  };

  if (!rec) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  const fs = rec.field_status || {};

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
            <span className="text-xs text-muted-foreground">v{rec.version}</span>
            {rec.is_master_file && <span className="text-[11px] px-2 py-0.5 rounded-sm border border-primary/30 bg-primary/10 text-primary font-medium">Knowledge Master File™</span>}
            {rec.treasure_standard && <TreasureBadge testid="kr-treasure" />}
          </div>
          <h1 className="font-heading text-3xl font-bold tracking-tight max-w-3xl">{rec.title}</h1>
          <p className="text-muted-foreground mt-2">{rec.category} · Confidence {rec.confidence_score}%{rec.reviewer && ` · Reviewed by ${rec.reviewer}`}</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          {rec.record_class === "Topic Seed" ? (
            <Link to="/promotion-pipeline" data-testid="kr-promote-btn"
              className="flex items-center gap-2 bg-primary text-primary-foreground px-3 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
              <Sprout className="w-4 h-4" /> Promote to Verified Knowledge Record™
            </Link>
          ) : (
            <button data-testid="kr-manufacture-all-btn" onClick={manufactureAll} disabled={job?.status === "running"}
              className="flex items-center gap-2 bg-primary text-primary-foreground px-3 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60">
              {job?.status === "running" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Boxes className="w-4 h-4" />} Manufacture Full Understanding
            </button>
          )}
          <Link to="/verification" data-testid="kr-review-link" className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors">
            <ShieldCheck className="w-4 h-4" /> Review
          </Link>
          <Link to={`/manufacture?kr=${rec.id}`} data-testid="kr-products-btn" className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors">
            <Factory className="w-4 h-4" /> Products
          </Link>
        </div>
      </div>

      {/* Manufacturing job progress */}
      {job && (
        <div className="bg-card border rounded-md p-5 mb-6" data-testid="kr-job-progress">
          <div className="flex items-center justify-between mb-3">
            <p className="font-heading font-semibold flex items-center gap-2"><Boxes className="w-4 h-4 text-primary" /> AI Manufacturing Pipeline</p>
            <span className="text-sm text-muted-foreground">{job.progress}%</span>
          </div>
          <div className="w-full h-2 bg-muted rounded-full overflow-hidden mb-4">
            <div className="h-full bg-gold transition-all" style={{ width: `${job.progress}%` }} />
          </div>
          <div className="flex flex-wrap gap-2">
            {(job.steps || []).map((s, i) => (
              <span key={i} className="inline-flex items-center gap-1.5 text-xs border rounded-sm px-2 py-1">
                {s.status === "done" ? <CheckCircle2 className="w-3 h-3 text-success" />
                  : s.status === "running" ? <Loader2 className="w-3 h-3 animate-spin text-primary" />
                  : s.status === "failed" ? <XCircle className="w-3 h-3 text-destructive" />
                  : <Clock className="w-3 h-3 text-muted-foreground" />}
                {s.label}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <p className="overline text-primary mb-3">Manufactured Understanding</p>
          <Accordion type="multiple" defaultValue={["Core Understanding"]} className="space-y-3">
            {schema.map((group) => (
              <AccordionItem key={group.label} value={group.label} className="border rounded-md bg-card px-4" data-testid={`kr-group-${group.label.toLowerCase().replace(/\s|&/g, "-")}`}>
                <AccordionTrigger className="hover:no-underline">
                  <span className="font-heading font-semibold">{group.label}</span>
                  <span className="ml-auto mr-3 text-xs text-muted-foreground">
                    {group.fields.filter((f) => (fs[f] || "Empty") !== "Empty").length}/{group.fields.length}
                  </span>
                </AccordionTrigger>
                <AccordionContent className="space-y-4 pb-4">
                  {group.fields.map((f) => (
                    <div key={f} className="border-t pt-3 first:border-0 first:pt-0" data-testid={`kr-field-${f}`}>
                      <div className="flex items-center justify-between mb-1.5">
                        <p className="text-sm font-semibold">{fieldLabel(f)}</p>
                        <div className="flex items-center gap-2">
                          <SectionStatusPill status={fs[f] || "Empty"} />
                          <button onClick={() => regen(f)} disabled={fieldBusy === f} data-testid={`kr-regen-${f}`} title="Regenerate" className="text-muted-foreground hover:text-primary">
                            {fieldBusy === f ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                          </button>
                          {(fs[f] === "Draft") && (
                            <button onClick={() => approveField(f)} data-testid={`kr-approve-${f}`} title="Approve field" className="text-muted-foreground hover:text-success">
                              <Check className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>
                      <FieldValue value={rec[f]} />
                    </div>
                  ))}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>

        <div className="space-y-5">
          <div className="bg-card border rounded-md p-5">
            <div className="flex items-center gap-2 mb-3"><BookText className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">Verified Truth</h3></div>
            <p className="text-sm leading-relaxed">{rec.verified_truth}</p>
          </div>
          <div className="bg-card border rounded-md p-5">
            <h3 className="font-heading font-semibold mb-3">Traceability & Meta</h3>
            <dl className="text-sm space-y-2">
              <div className="flex justify-between"><dt className="text-muted-foreground">Division</dt><dd>{rec.division || "Health"}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Version</dt><dd>v{rec.version}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Understanding</dt><dd>{rec.understanding_status}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Products created</dt><dd>{rec.products_created}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Manufacturing runs</dt><dd>{(rec.manufacturing_history || []).length}</dd></div>
            </dl>
          </div>
          {rec.image_prompt && (
            <div className="bg-card border rounded-md p-5">
              <h3 className="font-heading font-semibold mb-2">Visual Image Prompt</h3>
              <p className="text-sm text-muted-foreground italic">{rec.image_prompt}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
