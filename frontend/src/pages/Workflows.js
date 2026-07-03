import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import {
  Workflow, Play, Loader2, CheckCircle2, XCircle, AlertTriangle, FlaskConical, ChevronDown, ChevronUp,
} from "lucide-react";

const STATUS_BADGE = {
  running: "bg-blue-100 text-blue-700", queued: "bg-slate-100 text-slate-600",
  completed: "bg-emerald-100 text-emerald-700", completed_with_errors: "bg-amber-100 text-amber-700",
  escalated: "bg-purple-100 text-purple-700", failed: "bg-red-100 text-red-700", Completed: "bg-emerald-100 text-emerald-700",
};

function JobDetail({ jobId }) {
  const [job, setJob] = useState(null);
  useEffect(() => {
    let live = true;
    const load = async () => {
      try {
        const { data } = await api.get(`/workflow/jobs/${jobId}`);
        if (live) setJob(data);
      } catch (_) {}
    };
    load();
    const iv = setInterval(load, 4000);
    return () => { live = false; clearInterval(iv); };
  }, [jobId]);
  if (!job) return <div className="p-3 text-xs text-muted-foreground">Loading job…</div>;
  return (
    <div className="p-3 border-t bg-muted/30 text-xs space-y-2" data-testid={`job-detail-${job.job_number}`}>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground">
        <span>Stage: <b className="text-navy">{job.stage}</b></span>
        <span>Est. cost: <b className="text-navy">${(job.est_cost_usd || 0).toFixed(4)}</b> (Estimated)</span>
        <span>Retries: <b className="text-navy">{job.retry_count}</b></span>
        <span>ETA: {job.eta ? new Date(job.eta).toLocaleTimeString() : "—"}</span>
      </div>
      <div>
        <p className="font-semibold text-navy mb-1">Completed stages</p>
        <div className="flex flex-wrap gap-1">
          {(job.completed_tasks || []).map((t) => (
            <span key={t} className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">{t}</span>
          ))}
        </div>
      </div>
      <div>
        <p className="font-semibold text-navy mb-1">Products ({(job.products || []).length}/{(job.planned_products || []).length})</p>
        <div className="grid sm:grid-cols-2 gap-1">
          {(job.products || []).map((p, i) => (
            <div key={i} className="flex items-center gap-1.5">
              {p.status === "done" ? <CheckCircle2 className="w-3 h-3 text-emerald-600" /> :
               p.status === "failed" ? <XCircle className="w-3 h-3 text-red-500" /> :
               <AlertTriangle className="w-3 h-3 text-amber-500" />}
              <span className="text-navy">{p.product_type}</span>
            </div>
          ))}
        </div>
      </div>
      {(job.warnings || []).length > 0 && (
        <p className="text-amber-600">Warnings: {job.warnings.join("; ")}</p>
      )}
      {(job.errors || []).length > 0 && (
        <p className="text-red-600">Errors: {job.errors.join("; ")}</p>
      )}
      <div>
        <p className="font-semibold text-navy mb-1">Production Log</p>
        <div className="space-y-0.5 max-h-40 overflow-y-auto">
          {(job.logs || []).slice(-30).reverse().map((l, i) => (
            <p key={i} className="text-muted-foreground">
              <span className="text-gold">[{l.division}]</span> {l.message}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Workflows() {
  const [templates, setTemplates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [topic, setTopic] = useState("");
  const [template, setTemplate] = useState("");
  const [running, setRunning] = useState(false);
  const [fatRunning, setFatRunning] = useState(false);
  const [fatJobId, setFatJobId] = useState(null);
  const [fatResult, setFatResult] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [params] = useSearchParams();

  useEffect(() => {
    const t = params.get("topic");
    const tpl = params.get("template");
    if (t) setTopic(t);
    if (tpl) setTemplate(tpl);
  }, [params]);

  const loadJobs = async () => {
    try {
      const { data } = await api.get("/workflow/jobs", { params: { limit: 30 } });
      setJobs(data);
    } catch (_) {}
  };

  useEffect(() => {
    api.get("/workflow/templates").then(({ data }) => {
      setTemplates(data.templates);
      if (data.templates[0]) setTemplate(data.templates[0].name);
    });
    loadJobs();
    const iv = setInterval(loadJobs, 5000);
    return () => clearInterval(iv);
  }, []);

  const runWorkflow = async () => {
    if (!topic.trim() || !template) return toast.error("Enter a topic and choose a workflow.");
    setRunning(true);
    try {
      await api.post("/workflow/run", { template, topic: topic.trim() });
      toast.success("Workflow started — manufacturing in parallel.");
      setTopic("");
      loadJobs();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setRunning(false);
    }
  };

  const runFAT = async () => {
    setFatRunning(true);
    setFatResult(null);
    try {
      const { data } = await api.post("/workflow/factory-acceptance-test");
      setFatJobId(data.id);
      toast.success(`Factory Acceptance Test™ launched (${data.job_number}).`);
      loadJobs();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setFatRunning(false);
    }
  };

  useEffect(() => {
    if (!fatJobId) return;
    const iv = setInterval(async () => {
      try {
        const { data } = await api.get(`/workflow/factory-acceptance-test/${fatJobId}`);
        setFatResult(data);
        if (data.status === "completed" || data.status === "completed_with_errors" || data.status === "escalated" || data.status === "failed")
          clearInterval(iv);
      } catch (_) {}
    }, 5000);
    return () => clearInterval(iv);
  }, [fatJobId]);

  return (
    <div className="space-y-6" data-testid="workflows-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <Workflow className="w-7 h-7 text-gold" /> QRU Enterprise Workflow Engine™
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Answer one question — the factory coordinates every division automatically, in parallel.
        </p>
      </div>

      {/* Run a workflow */}
      <div className="bg-card border rounded-sm p-5 space-y-3" data-testid="run-workflow-panel">
        <h2 className="font-heading font-semibold text-navy">What do you want to teach today?</h2>
        <input
          data-testid="workflow-topic-input"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. Why sleep restores the brain"
          className="w-full px-3 py-2 text-sm bg-muted rounded-sm border border-transparent focus:border-primary focus:bg-card outline-none"
        />
        <div className="flex flex-wrap gap-3 items-center">
          <select
            data-testid="workflow-template-select"
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            className="px-3 py-2 text-sm bg-muted rounded-sm border border-transparent focus:border-primary outline-none"
          >
            {templates.map((t) => (
              <option key={t.name} value={t.name}>{t.name} ({t.product_count} products)</option>
            ))}
          </select>
          <button
            data-testid="run-workflow-btn"
            onClick={runWorkflow}
            disabled={running}
            className="flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm text-sm font-semibold hover:bg-navy/90 disabled:opacity-60"
          >
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Run Workflow
          </button>
        </div>
        {template && (
          <p className="text-xs text-muted-foreground">
            Manufactures in parallel: {templates.find((t) => t.name === template)?.products.join(", ")}
          </p>
        )}
      </div>

      {/* Factory Acceptance Test */}
      <div className="bg-gold/10 border border-gold/40 rounded-sm p-5 space-y-3" data-testid="fat-panel">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="font-heading font-semibold text-navy flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-gold" /> Factory Acceptance Test™
          </h2>
          <button
            data-testid="run-fat-btn"
            onClick={runFAT}
            disabled={fatRunning}
            className="flex items-center gap-2 bg-gold text-navy px-4 py-2 rounded-sm text-sm font-semibold hover:bg-gold/90 disabled:opacity-60"
          >
            {fatRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <FlaskConical className="w-4 h-4" />} Run Full End-to-End Test
          </button>
        </div>
        <p className="text-xs text-muted-foreground">
          Manufactures one complete Treasure Standard™ package end-to-end and validates every division before bulk manufacturing.
        </p>
        {fatResult && (
          <div className="bg-card border rounded-sm p-4 space-y-2" data-testid="fat-result">
            <div className="flex items-center gap-3">
              <span className={`text-lg font-heading font-bold ${fatResult.acceptance === "PASS" ? "text-emerald-600" : "text-amber-600"}`}>
                {fatResult.acceptance} · {fatResult.score}%
              </span>
              <span className="text-xs text-muted-foreground">
                {fatResult.products_made} made · {fatResult.products_failed} failed · ${fatResult.est_cost_usd} est.
              </span>
            </div>
            <div className="grid sm:grid-cols-2 gap-1">
              {fatResult.checks.map((c, i) => (
                <div key={i} className="flex items-center gap-1.5 text-xs">
                  {c.pass ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <XCircle className="w-3.5 h-3.5 text-red-500" />}
                  <span className="text-navy font-medium">{c.division}</span>
                  <span className="text-muted-foreground">— {c.detail}</span>
                </div>
              ))}
            </div>
            {fatResult.defects.length > 0 && (
              <p className="text-xs text-amber-600">Defects to review: {fatResult.defects.join(", ")}</p>
            )}
          </div>
        )}
      </div>

      {/* Job queue */}
      <div className="bg-card border rounded-sm p-5" data-testid="job-queue-panel">
        <h2 className="font-heading font-semibold text-navy mb-3">Job Queue™</h2>
        {jobs.length === 0 && <p className="text-sm text-muted-foreground">No jobs yet.</p>}
        <div className="space-y-2">
          {jobs.map((j) => (
            <div key={j.id} className="border rounded-sm" data-testid={`workflow-job-${j.job_number}`}>
              <button
                onClick={() => setExpanded(expanded === j.id ? null : j.id)}
                className="w-full text-left p-3 flex items-center justify-between gap-2"
              >
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-navy truncate">
                    {j.job_number} · {j.template} {j.is_fat && <span className="text-gold">· FAT</span>}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">{j.topic} · {j.division}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-muted-foreground">{j.progress}%</span>
                  <span className={`text-[11px] px-2 py-0.5 rounded-full ${STATUS_BADGE[j.status] || "bg-slate-100"}`}>{j.status}</span>
                  {expanded === j.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </div>
              </button>
              {expanded === j.id && <JobDetail jobId={j.id} />}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
