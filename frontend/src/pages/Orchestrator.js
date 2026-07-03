import { useEffect, useState, useCallback } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Factory, Play, Pause, RotateCw, CheckCircle2, Loader2, Plus, ChevronRight } from "lucide-react";

export default function Orchestrator() {
  const [stats, setStats] = useState(null);
  const [batches, setBatches] = useState([]);
  const [colleges, setColleges] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [form, setForm] = useState({ name: "", from_college: "", batch_size: 25 });
  const [creating, setCreating] = useState(false);

  const loadList = useCallback(async () => {
    const [s, b, rs] = await Promise.all([
      api.get("/orchestrator/stats"),
      api.get("/orchestrator/batches"),
      api.get("/topic-registry/stats"),
    ]);
    setStats(s.data); setBatches(b.data); setColleges(rs.data.colleges || []);
    if (rs.data.colleges?.length && !form.from_college)
      setForm((f) => ({ ...f, from_college: rs.data.colleges[0] }));
  }, [form.from_college]);

  useEffect(() => { loadList(); }, []);

  const loadDetail = useCallback(async (id) => {
    const { data } = await api.get(`/orchestrator/batches/${id}`);
    setDetail(data);
  }, []);

  useEffect(() => {
    if (!selected) return;
    loadDetail(selected);
    const running = detail?.status === "running";
    const iv = setInterval(() => { loadDetail(selected); loadList(); }, running ? 2500 : 6000);
    return () => clearInterval(iv);
  }, [selected, detail?.status, loadDetail, loadList]);

  const create = async () => {
    if (!form.name || !form.from_college) { toast.error("Name and college required"); return; }
    setCreating(true);
    try {
      const { data } = await api.post("/orchestrator/batches", {
        name: form.name, from_college: form.from_college,
        division: null, batch_size: Number(form.batch_size),
      });
      toast.success(`Batch created with ${data.total} topics`);
      setForm((f) => ({ ...f, name: "" }));
      await loadList(); setSelected(data.id);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setCreating(false); }
  };

  const action = async (id, verb) => {
    try {
      await api.post(`/orchestrator/batches/${id}/${verb}`);
      toast.success(`Batch ${verb}`);
      loadList(); if (selected === id) loadDetail(id);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  const toggleHandsFree = async () => {
    try {
      const { data } = await api.post("/orchestrator/settings", { hands_free_mode: !stats?.hands_free_mode });
      toast.success(`Hands-Free Manufacturing Mode™ ${data.hands_free_mode ? "ON" : "OFF"}`);
      loadList();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  const runAutopilot = async () => {
    try {
      await api.post("/orchestrator/autopilot");
      toast.success("Autopilot running — AI teams advancing eligible products");
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  return (
    <div className="space-y-8" data-testid="orchestrator-page">
      <div>
        <p className="overline text-primary mb-1">Phase 3 · Scale</p>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Intelligent Bulk Manufacturing Orchestrator™</h1>
        <p className="text-muted-foreground text-sm mt-1">Manufacture → AI Verification → Revision → Re-Verify → Approve → Publish.</p>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[["Batches", stats.total_batches], ["Running", stats.running], ["Completed", stats.completed],
            ["Open Escalations", stats.open_escalations], ["Est. Tokens", stats.est_tokens?.toLocaleString?.() || 0]].map(([l, v]) => (
            <div key={l} className="bg-card border rounded-sm p-4">
              <p className="text-2xl font-heading font-bold">{v}</p>
              <p className="text-xs text-muted-foreground mt-1">{l}</p>
            </div>
          ))}
        </div>
      )}

      {/* Create batch */}
      <div className="bg-card border rounded-sm p-6">
        <div className="flex items-center gap-2 mb-4"><Plus className="w-4 h-4 text-gold" />
          <h2 className="font-heading font-semibold">New Manufacturing Batch</h2></div>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <label className="text-xs text-muted-foreground">Batch name</label>
            <input data-testid="batch-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Health Batch 1" className="mt-1 w-full px-3 py-2 rounded-sm border bg-background text-sm" />
          </div>
          <div>
            <label className="text-xs text-muted-foreground">College</label>
            <select data-testid="batch-college" value={form.from_college} onChange={(e) => setForm({ ...form, from_college: e.target.value })}
              className="mt-1 block px-3 py-2 rounded-sm border bg-background text-sm min-w-[180px]">
              {colleges.length === 0 && <option value="">Seed topics first</option>}
              {colleges.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Batch size (25–50)</label>
            <input data-testid="batch-size" type="number" min={1} max={50} value={form.batch_size}
              onChange={(e) => setForm({ ...form, batch_size: e.target.value })}
              className="mt-1 block w-28 px-3 py-2 rounded-sm border bg-background text-sm" />
          </div>
          <button data-testid="batch-create-btn" onClick={create} disabled={creating}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium disabled:opacity-60">
            {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Factory className="w-4 h-4" />} Create Batch
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Batch list */}
        <div className="bg-card border rounded-sm">
          <div className="p-4 border-b"><h2 className="font-heading font-semibold">Batches</h2></div>
          <div className="divide-y max-h-[520px] overflow-y-auto">
            {batches.length === 0 && <p className="p-6 text-sm text-muted-foreground text-center">No batches yet.</p>}
            {batches.map((b) => (
              <button key={b.id} data-testid={`batch-item-${b.id}`} onClick={() => setSelected(b.id)}
                className={`w-full text-left p-4 hover:bg-muted transition-colors ${selected === b.id ? "bg-muted" : ""}`}>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{b.name}</span>
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-primary/10 text-primary">{b.status}</span>
                </div>
                <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div className="h-full bg-gold" style={{ width: `${b.progress || 0}%` }} />
                </div>
                <p className="text-xs text-muted-foreground mt-1">{b.completed}/{b.total} done · {b.escalated} escalated · {b.failed} failed</p>
              </button>
            ))}
          </div>
        </div>

        {/* Detail */}
        <div className="bg-card border rounded-sm">
          {!detail ? (
            <p className="p-6 text-sm text-muted-foreground text-center">Select a batch to manage it.</p>
          ) : (
            <div>
              <div className="p-4 border-b flex items-center justify-between flex-wrap gap-2">
                <div><h2 className="font-heading font-semibold">{detail.name}</h2>
                  <p className="text-xs text-muted-foreground">{detail.college} · {detail.division} · {detail.est_tokens?.toLocaleString?.()} tokens</p></div>
                <div className="flex gap-1">
                  {detail.status !== "running" && <IconBtn t="start" onClick={() => action(detail.id, "start")} icon={Play} label="Start" />}
                  {detail.status === "running" && <IconBtn t="pause" onClick={() => action(detail.id, "pause")} icon={Pause} label="Pause" />}
                  {detail.status === "paused" && <IconBtn t="resume" onClick={() => action(detail.id, "resume")} icon={Play} label="Resume" />}
                  {detail.failed > 0 && <IconBtn t="retry" onClick={() => action(detail.id, "retry")} icon={RotateCw} label="Retry" />}
                  <IconBtn t="approve" onClick={() => action(detail.id, "approve")} icon={CheckCircle2} label={detail.approved ? "Approved" : "Approve"} />
                </div>
              </div>
              <div className="max-h-64 overflow-y-auto divide-y">
                {detail.items?.map((it, i) => (
                  <div key={i} className="flex items-center justify-between px-4 py-2 text-sm">
                    <span className="flex items-center gap-2"><ChevronRight className="w-3 h-3 text-muted-foreground" />{it.topic_name}</span>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full ${
                      it.status === "done" ? "bg-emerald-100 text-emerald-700" :
                      it.status === "escalated" ? "bg-amber-100 text-amber-700" :
                      it.status === "failed" ? "bg-red-100 text-red-700" :
                      it.status === "running" ? "bg-blue-100 text-blue-700" : "bg-muted text-muted-foreground"
                    }`}>{it.stage}</span>
                  </div>
                ))}
              </div>
              <div className="border-t p-3 bg-muted/40 max-h-40 overflow-y-auto">
                <p className="text-[11px] font-semibold text-muted-foreground mb-1">Manufacturing Log</p>
                {detail.logs?.map((l, i) => (
                  <p key={i} className="text-[11px] text-muted-foreground font-mono">[{l.level}] {l.message}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function IconBtn({ onClick, icon: Icon, label, t }) {
  return (
    <button data-testid={`batch-${t}-btn`} onClick={onClick}
      className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-sm border hover:bg-muted transition-colors">
      <Icon className="w-3.5 h-3.5" /> {label}
    </button>
  );
}
