import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Library, Loader2, Search, Network, Lightbulb, GitBranch, ShieldCheck, ArrowRight, CheckCircle2, FileText, Download, Archive } from "lucide-react";

const TABS = [
  { key: "standards", label: "Standards Registry™", icon: ShieldCheck },
  { key: "graph", label: "Knowledge Graph™", icon: Network },
  { key: "memory", label: "Enterprise Memory™", icon: Lightbulb },
  { key: "promotion", label: "Knowledge Promotion™", icon: GitBranch },
];

function Metric({ label, value }) {
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <p className="text-2xl font-heading font-bold text-navy">{value}</p>
      <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">{label}</p>
    </div>
  );
}

function Field({ label, value }) {
  if (!value || (Array.isArray(value) && !value.length)) return null;
  return (
    <div className="mb-3">
      <p className="text-[11px] font-semibold tracking-wide text-gold uppercase mb-1">{label}</p>
      {Array.isArray(value) ? (
        <ul className="list-disc pl-4 space-y-0.5 text-sm text-foreground/80">
          {value.map((v, i) => <li key={i}>{typeof v === "string" ? v : (v.reason ? `v${v.version} · ${v.reason} (${v.reviewer})` : JSON.stringify(v))}</li>)}
        </ul>
      ) : <p className="text-sm text-foreground/80">{value}</p>}
    </div>
  );
}

export default function InstitutionalKnowledge() {
  const [tab, setTab] = useState("standards");
  const [overview, setOverview] = useState(null);
  const [standards, setStandards] = useState([]);
  const [graph, setGraph] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [cat, setCat] = useState("");
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(null);
  const [loading, setLoading] = useState(true);
  const [auditFiles, setAuditFiles] = useState([]);

  useEffect(() => {
    api.get("/audit/exports").then(({ data }) => setAuditFiles(data.exports || [])).catch(() => {});
  }, []);

  const downloadAudit = async (f) => {
    const { toast } = await import("sonner");
    try {
      const res = await api.get(f.download_url, { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url; a.download = f.filename; document.body.appendChild(a); a.click();
      a.remove(); window.URL.revokeObjectURL(url);
      toast.success(`Downloaded ${f.filename}`);
    } catch { toast.error("Download failed"); }
  };

  useEffect(() => {
    api.get("/qiks/overview").then(({ data }) => setOverview(data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (cat) params.set("category", cat);
    if (q) params.set("q", q);
    api.get(`/qiks/standards?${params}`).then(({ data }) => setStandards(data.standards || [])).catch(() => {});
  }, [cat, q]);

  useEffect(() => {
    if (tab === "graph" && !graph) api.get("/qiks/graph").then(({ data }) => setGraph(data)).catch(() => {});
    if (tab === "memory" && !lessons.length) api.get("/qiks/lessons").then(({ data }) => setLessons(data.lessons || [])).catch(() => {});
  }, [tab]);

  const approveLesson = async (id) => {
    const { toast } = await import("sonner");
    try {
      await api.post(`/qiks/lessons/${id}/approve`);
      toast.success("Lesson promoted to Institutional Knowledge™");
      const { data } = await api.get("/qiks/lessons");
      setLessons(data.lessons || []);
    } catch { toast.error("Could not approve lesson"); }
  };

  if (loading) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading Institutional Knowledge System…</div>;

  return (
    <div className="space-y-6" data-testid="qiks-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <Library className="w-7 h-7 text-gold" /> QRU Institutional Knowledge System™
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          The permanent enterprise memory. Every verified discovery, principle, and standard is preserved, versioned, and cross-linked.
          <span className="font-semibold text-navy"> Build the factory once. Improve it forever.</span>
        </p>
      </div>

      {overview && (
        <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="qiks-metrics">
          <Metric label="QRU Standards™" value={overview.standards} />
          <Metric label="Frameworks" value={overview.frameworks} />
          <Metric label="Methodologies" value={overview.methodologies} />
          <Metric label="Product Recipes™" value={overview.recipes} />
          <Metric label="Lessons Learned™" value={overview.lessons_learned} />
          <Metric label="Character Assets" value={overview.character_assets} />
          <Metric label="Ideas Awaiting Review" value={overview.ideas_awaiting_review} />
          <Metric label="Versions Tracked" value={overview.standards_updated_this_month} />
          <Metric label="Knowledge Growth" value={overview.knowledge_growth} />
          <Metric label="Institutional Health™" value={`${overview.institutional_health}%`} />
        </div>
      )}

      <div className="flex flex-wrap gap-2 border-b border-border" data-testid="qiks-tabs">
        {TABS.map((t) => (
          <button key={t.key} data-testid={`qiks-tab-${t.key}`} onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm border-b-2 -mb-px transition-colors ${tab === t.key ? "border-gold text-navy font-semibold" : "border-transparent text-muted-foreground hover:text-foreground"}`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === "standards" && (
        <div className="space-y-4">
          {auditFiles.length > 0 && (
            <div className="qru-card p-4 border-l-4 border-gold" data-testid="audit-exports-panel">
              <div className="flex items-center gap-2 mb-1">
                <Archive className="w-4 h-4 text-gold" />
                <p className="text-sm font-bold text-navy">Standards Audit™ — Preserved Baseline Snapshot</p>
              </div>
              <p className="text-[11px] text-muted-foreground mb-3">Read-only export of the current governance registry (iteration 94). Download for Founder review.</p>
              <div className="flex flex-wrap gap-2">
                {auditFiles.map((f) => (
                  <button key={f.filename} data-testid={`audit-download-${f.filename}`} onClick={() => downloadAudit(f)}
                    className="inline-flex items-center gap-1.5 border border-navy/30 text-navy hover:bg-navy/5 px-3 py-1.5 rounded-md text-[12px] font-semibold">
                    <Download className="w-3.5 h-3.5" /> {f.filename} <span className="text-muted-foreground">({f.size_kb} KB)</span>
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[220px] max-w-md">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input data-testid="qiks-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search standards by keyword, ID, category…"
                className="w-full pl-9 pr-3 py-2 text-sm bg-muted rounded-sm border border-transparent focus:border-primary focus:bg-card outline-none" />
            </div>
            <select data-testid="qiks-category-filter" value={cat} onChange={(e) => setCat(e.target.value)}
              className="text-sm bg-muted rounded-sm px-3 py-2 border border-transparent focus:border-primary outline-none">
              <option value="">All Categories ({overview?.categories?.length || 0})</option>
              {overview?.categories?.map((c) => <option key={c} value={c}>{c}{overview.by_category?.[c] ? ` (${overview.by_category[c]})` : ""}</option>)}
            </select>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {standards.map((s) => (
              <button key={s.id} data-testid={`std-card-${s.id}`} onClick={() => setOpen(s)}
                className="text-left rounded-md border border-border bg-card p-4 hover:border-gold hover:shadow-md transition-all group">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-muted-foreground">{s.standard_id}{s.alias ? ` · ${s.alias}` : ""} · v{s.version}</span>
                  <span className={`text-[10px] rounded-full px-1.5 py-0.5 border ${s.status === "Active" ? "text-emerald-700 bg-emerald-50 border-emerald-200" : "text-amber-700 bg-amber-50 border-amber-200"}`}>{s.status}</span>
                </div>
                <p className="font-heading font-semibold text-navy text-[15px] mt-1">{s.name}</p>
                <p className="text-[11px] text-gold mt-0.5">{s.category}</p>
                {s.designation && (
                  <span data-testid={`std-designation-${s.id}`}
                    className={`inline-flex items-center gap-1 mt-2 text-[9px] font-bold uppercase tracking-wide rounded px-1.5 py-0.5 ${/canonical/i.test(s.designation) ? "bg-gold/20 text-gold-foreground text-navy border border-gold/40" : "bg-royal/10 text-royal border border-royal/30"}`}>
                    {/canonical/i.test(s.designation) ? "⭐ Canonical" : "Supporting"}
                  </span>
                )}
                {s.inherits_from?.length > 0 && (
                  <p className="text-[10px] text-muted-foreground mt-1">Inherits from: <span className="font-mono">{s.inherits_from.join(", ")}</span></p>
                )}
                <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{s.description}</p>
                <span className="mt-3 inline-flex items-center gap-1 text-xs text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity">Open record <ArrowRight className="w-3 h-3" /></span>
              </button>
            ))}
            {!standards.length && <p className="text-sm text-muted-foreground">No standards match your filters.</p>}
          </div>
        </div>
      )}

      {tab === "graph" && graph && (
        <div className="space-y-3" data-testid="qiks-graph">
          <p className="text-sm text-muted-foreground">{graph.nodes.length} nodes · {graph.edges.length} connections. Knowledge exists as an interconnected graph, never isolated documents.</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {graph.nodes.map((n) => {
              const links = graph.edges.filter((e) => e.from === n.id);
              return (
                <div key={n.id} className="rounded-md border border-border bg-card p-3">
                  <p className="font-semibold text-navy text-sm">{n.label} <span className="text-[10px] font-mono text-muted-foreground">{n.id}</span></p>
                  <p className="text-[11px] text-gold">{n.category}</p>
                  {links.length ? (
                    <div className="mt-2 space-y-1">
                      {links.map((e, i) => {
                        const target = graph.nodes.find((x) => x.id === e.to);
                        return <p key={i} className="text-xs text-foreground/70 flex items-center gap-1"><ArrowRight className="w-3 h-3 text-gold" /> <span className="italic">{e.relation}</span> → {target?.label || e.to}</p>;
                      })}
                    </div>
                  ) : <p className="text-xs text-muted-foreground mt-1">No outbound links.</p>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {tab === "memory" && (
        <div className="space-y-3" data-testid="qiks-memory">
          <p className="text-sm text-muted-foreground">Every division contributes lessons learned. Founder-approved lessons become permanent Institutional Knowledge™.</p>
          {lessons.map((l) => (
            <div key={l.id} className="rounded-md border border-border bg-card p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-navy text-sm">{l.title}</p>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] rounded-full px-2 py-0.5 bg-navy/5 text-navy">{l.division}</span>
                  {l.founder_approval ? (
                    <span className="text-[10px] rounded-full px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 inline-flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Institutional</span>
                  ) : (
                    <button data-testid={`approve-lesson-${l.id}`} onClick={() => approveLesson(l.id)}
                      className="text-[10px] rounded-full px-2 py-0.5 bg-gold/15 text-navy border border-gold hover:bg-gold/30 transition-colors">Approve → Institutional</button>
                  )}
                </div>
              </div>
              <p className="text-sm text-foreground/80 mt-1">{l.lesson}</p>
              <p className="text-[10px] text-muted-foreground mt-2 font-mono">{l.id} · {l.source} · {l.date}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "promotion" && overview && (
        <div className="space-y-4" data-testid="qiks-promotion">
          <p className="text-sm text-muted-foreground">Ideas are promoted through stages. Only Founder-approved knowledge enters the permanent registry.</p>
          <div className="flex flex-wrap items-center gap-2">
            {overview.promotion_stages.map((st, i) => (
              <div key={st} className="flex items-center gap-2">
                <span className={`text-xs rounded-full px-3 py-1.5 border ${i >= 6 ? "bg-gold/10 border-gold text-navy font-semibold" : "bg-card border-border text-foreground/70"}`}>{st}</span>
                {i < overview.promotion_stages.length - 1 && <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" />}
              </div>
            ))}
          </div>
        </div>
      )}

      <Dialog open={!!open} onOpenChange={(v) => !v && setOpen(null)}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto" data-testid="std-dialog">
          {open && (
            <>
              <DialogHeader>
                <p className="overline text-gold text-[10px] font-semibold tracking-widest uppercase">{open.standard_id} · {open.category} · v{open.version}</p>
                <DialogTitle className="font-heading text-2xl text-navy">{open.name}</DialogTitle>
                <p className="text-sm text-muted-foreground">{open.status} · {open.implementation_status} · Founder Approved: {open.founder_approval ? "Yes" : "No"} · Stage: {open.promotion_stage}</p>
                {open.designation && (
                  <span data-testid="std-detail-designation"
                    className={`inline-flex w-fit items-center gap-1 mt-1 text-[10px] font-bold uppercase tracking-wide rounded px-2 py-0.5 ${/canonical/i.test(open.designation) ? "bg-gold/20 text-navy border border-gold/40" : "bg-royal/10 text-royal border border-royal/30"}`}>
                    {/canonical/i.test(open.designation) ? "⭐ " : ""}{open.designation}
                  </span>
                )}
              </DialogHeader>
              <div className="grid sm:grid-cols-2 gap-x-8 mt-2">
                <div>
                  <Field label="Description" value={open.description} />
                  <Field label="Purpose" value={open.purpose} />
                  <Field label="Standard Type" value={open.standard_type} />
                  <Field label="Inherits From" value={open.inherits_from} />
                  <Field label="Implemented By" value={open.implemented_by} />
                  <Field label="Alias (backward-compatible)" value={open.alias} />
                  <Field label="Related Standards" value={open.related_standards} />
                  <Field label="Related AI Agents" value={open.related_ai_agents} />
                  <Field label="Related Colleges" value={open.related_colleges} />
                </div>
                <div>
                  <Field label="Enterprise References" value={open.enterprise_references} />
                  <Field label="Change History" value={open.change_history} />
                  <Field label="Supersedes" value={open.supersedes} />
                  <Field label="Superseded Versions" value={open.superseded_versions?.map(v => `v${v.version} — archived ${(v.archived_at||'').slice(0,10)}`)} />
                  <Field label="Date Adopted" value={open.date_adopted} />
                  <Field label="Classification" value={open.classification} />
                  <Field label="Source Document" value={open.source_document} />
                </div>
              </div>
              {open.document_content && (
                <div className="mt-4 border-t border-border pt-4" data-testid="std-document">
                  <p className="text-[11px] font-semibold tracking-wide text-gold uppercase mb-2 flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5" /> Full Document {open.word_count ? `· ${open.word_count.toLocaleString()} words` : ""} <span className="text-muted-foreground normal-case font-normal">(verbatim · Founder source)</span>
                  </p>
                  <pre className="text-[13px] leading-relaxed text-foreground/85 whitespace-pre-wrap font-body bg-muted/40 rounded-md p-4 max-h-[45vh] overflow-y-auto">{open.document_content}</pre>
                </div>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
