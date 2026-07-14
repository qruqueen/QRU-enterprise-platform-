import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, MetricCard } from "@/components/qru";
import {
  Loader2, Sparkles, ShieldCheck, ThumbsUp, RotateCcw, Archive, Award, ArrowLeft,
  Brain, BookOpen, Layers, Eye, ChevronDown, ChevronRight, Download, Lightbulb,
  GitBranch, ScrollText, ListChecks, CheckCircle2, Clock, FlaskConical,
} from "lucide-react";

const SUPER = ["Founder & CEO", "Administrator"];
const SHELVES = ["Founder Review Required", "Revision Requested", "Founder Approved", "Treasure Standard Certified", "Archived"];

const EVAL_BADGE = {
  deterministic: { label: "Deterministic", tone: "navy" },
  "AI-assisted advisory": { label: "AI-Advisory", tone: "royal" },
  "human-reviewed": { label: "Human-Reviewed", tone: "emerald" },
};

function Section({ title, icon: Icon, children, defaultOpen = false, testid }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-border rounded-md overflow-hidden" data-testid={testid}>
      <button onClick={() => setOpen((o) => !o)} data-testid={testid ? `${testid}-toggle` : undefined}
        className="w-full flex items-center justify-between px-4 py-3 bg-muted/30 hover:bg-muted/50 transition-colors">
        <span className="font-heading font-bold text-navy flex items-center gap-2 text-sm">
          {Icon && <Icon className="w-4 h-4 text-royal" />} {title}
        </span>
        {open ? <ChevronDown className="w-4 h-4 text-muted-foreground" /> : <ChevronRight className="w-4 h-4 text-muted-foreground" />}
      </button>
      {open && <div className="p-4 space-y-4">{children}</div>}
    </div>
  );
}

function Field({ label, value }) {
  if (value == null || value === "") return null;
  let body;
  if (typeof value === "string" || typeof value === "number") {
    body = <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-line">{value}</p>;
  } else if (Array.isArray(value)) {
    body = <ul className="list-disc pl-5 text-sm text-foreground/90 space-y-1">
      {value.map((v, i) => <li key={i}>{typeof v === "object" ? Object.entries(v).map(([k, val]) => `${k}: ${val}`).join(" — ") : String(v)}</li>)}
    </ul>;
  } else if (typeof value === "object") {
    body = <dl className="text-sm space-y-1">
      {Object.entries(value).map(([k, v]) => (
        <div key={k}><dt className="font-semibold text-navy inline capitalize">{k.replace(/_/g, " ")}: </dt>
          <dd className="inline text-foreground/90">{typeof v === "object" ? JSON.stringify(v) : String(v)}</dd></div>
      ))}
    </dl>;
  } else {
    body = <p className="text-sm text-foreground/90">{String(value)}</p>;
  }
  return (
    <div>
      <p className="text-[11px] font-bold text-navy uppercase tracking-wide mb-1">{label}</p>
      {body}
    </div>
  );
}

export default function DecoderEngine() {
  const { user } = useAuth();
  const isSuper = SUPER.includes(user?.role);
  const [stats, setStats] = useState(null);
  const [krs, setKrs] = useState([]);
  const [form, setForm] = useState({ kr_id: "", audience: "", level: "" });
  const [busy, setBusy] = useState(false);
  const [shelf, setShelf] = useState([]);
  const [filter, setFilter] = useState("Founder Review Required");
  const [selected, setSelected] = useState(null);
  const [acting, setActing] = useState(false);

  const loadShelf = (state) => {
    api.get("/decoder/shelf", { params: state ? { state } : {} })
      .then((r) => setShelf(r.data.decoders)).catch(() => {});
    api.get("/decoder/stats").then((r) => setStats(r.data)).catch(() => {});
  };
  useEffect(() => {
    api.get("/decoder/verified-krs").then((r) => setKrs(r.data.records || [])).catch(() => {});
  }, []);
  useEffect(() => { loadShelf(filter); }, [filter]);

  const decode = async () => {
    if (!form.kr_id) { toast.error("Select a Verified Knowledge Record to decode."); return; }
    setBusy(true);
    toast.message("Decoding governed knowledge into understanding… establishing the core mental model.");
    try {
      const { data } = await api.post("/decoder/decode", form);
      toast.success(`${data.decoder.decoder_id} decoded → Founder Review Shelf™.`);
      setFilter("Founder Review Required");
      setSelected(data.decoder);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const act = async (path, label, revisionNotes) => {
    if (!selected) return;
    setActing(true);
    try {
      const body = revisionNotes != null ? { notes: revisionNotes } : {};
      const { data } = await api.post(`/decoder/${selected.id}/${path}`, body);
      toast.success(label);
      setSelected(data);
      loadShelf(filter);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setActing(false); }
  };

  const exportJson = () => {
    if (!selected) return;
    const blob = new Blob([JSON.stringify(selected, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${selected.decoder_id || "decoder-record"}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <div data-testid="decoder-engine-page">
      <PageHeader
        overline="QRU Decoder Engine™ · Version 2.0 · Understanding Engine™"
        title="Decode Verified Knowledge into Governed Understanding"
        description="Transform a Verified Knowledge Record™ into a governed 38-field Decoder Record™ — one core mental model, honest analogy, story, visual spec and a 5-part Understanding Test. AI drafts & scores advisory only; the Founder is the final authority."
        actions={<VerifiedBadge label="Knowledge-First™" testid="decoder-badge" />}
      />

      {stats && (
        <div className="grid grid-cols-3 gap-3 mb-8" data-testid="decoder-stats">
          <MetricCard icon={Layers} label="Decoders Manufactured" value={stats.total} testid="stat-total" />
          <MetricCard icon={Clock} accent="royal" label="Pending Founder Review" value={stats.pending_review}
            testid="stat-pending" onClick={() => { setFilter("Founder Review Required"); setSelected(null); }} />
          <MetricCard icon={ShieldCheck} accent="gold" label="Founder Approved" value={stats.approved} testid="stat-approved" />
        </div>
      )}

      {!selected ? (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Decode form */}
          <div className="lg:col-span-1">
            <Panel title="Decode a Knowledge Record" icon={Sparkles} accent="gold" testid="decoder-form">
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Verified Knowledge Record™</label>
                  <select data-testid="decoder-kr-select" value={form.kr_id}
                    onChange={(e) => setForm((f) => ({ ...f, kr_id: e.target.value }))}
                    className="w-full mt-1.5 px-3 py-2 text-sm border border-border rounded-md bg-card outline-none focus:border-navy">
                    <option value="">Select a verified topic…</option>
                    {krs.map((k) => (
                      <option key={k.id} value={k.id}>{k.title}{k.category ? ` · ${k.category}` : ""}</option>
                    ))}
                  </select>
                  <p className="text-[10px] text-muted-foreground mt-1">Only Verified records are eligible (Knowledge-First™).</p>
                </div>
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Audience (optional)</label>
                  <input data-testid="decoder-audience-input" value={form.audience}
                    onChange={(e) => setForm((f) => ({ ...f, audience: e.target.value }))}
                    placeholder="e.g. Teens, Parents, Beginners"
                    className="w-full mt-1.5 px-3 py-2 text-sm border border-border rounded-md bg-card outline-none focus:border-navy" />
                </div>
                <div>
                  <label className="text-xs font-bold text-navy uppercase tracking-wide">Level (optional)</label>
                  <input data-testid="decoder-level-input" value={form.level}
                    onChange={(e) => setForm((f) => ({ ...f, level: e.target.value }))}
                    placeholder="e.g. Introductory, Intermediate"
                    className="w-full mt-1.5 px-3 py-2 text-sm border border-border rounded-md bg-card outline-none focus:border-navy" />
                </div>
                <button data-testid="decoder-decode-btn" onClick={decode} disabled={busy}
                  className="w-full inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-md font-bold text-sm hover:bg-navy/90 disabled:opacity-60">
                  {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
                  Decode into Understanding
                </button>
              </div>
            </Panel>
          </div>

          {/* Founder Review Shelf */}
          <div className="lg:col-span-2">
            <Panel title="Founder Review Shelf™" icon={Eye} accent="royal" testid="decoder-shelf"
              right={
                <select data-testid="shelf-filter" value={filter} onChange={(e) => setFilter(e.target.value)}
                  className="text-xs border border-border rounded-md px-2 py-1 bg-card outline-none">
                  {SHELVES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              }>
              {shelf.length === 0 ? (
                <p className="text-sm text-muted-foreground py-6 text-center">No Decoder Records on this shelf. Decode a Knowledge Record to begin.</p>
              ) : (
                <div className="space-y-3" data-testid="shelf-list">
                  {shelf.map((d) => (
                    <button key={d.id} data-testid={`shelf-item-${d.id}`} onClick={() => setSelected(d)}
                      className="w-full text-left border border-border rounded-md p-3 hover:border-navy transition-colors">
                      <div className="flex items-start justify-between gap-2 flex-wrap">
                        <div className="min-w-0">
                          <p className="font-bold text-navy text-sm">{d.title}</p>
                          <div className="flex items-center gap-2 flex-wrap mt-1">
                            <span className="font-mono text-[10px] text-muted-foreground">{d.decoder_id}</span>
                            <StatusChip status={d.review_state} />
                            {d.is_canonical && <StatusChip status="Canonical" tone="gold" />}
                            <StatusChip status={`v${d.decoder_version}`} tone="navy" />
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
                      </div>
                      <p className="text-[12px] text-muted-foreground mt-1.5 line-clamp-2">{d.definition}</p>
                    </button>
                  ))}
                </div>
              )}
            </Panel>
          </div>
        </div>
      ) : (
        <DecoderDetail
          d={selected} isSuper={isSuper} acting={acting} act={act} exportJson={exportJson}
          onBack={() => { setSelected(null); loadShelf(filter); }}
        />
      )}
    </div>
  );
}

function DecoderDetail({ d, isSuper, acting, act, exportJson, onBack }) {
  const uc = d.understanding_checks || {};
  const vs = d.visual_spec || {};
  const rows = (d.scorecard || {}).rows || [];
  const canApprove = d.review_state === "Founder Review Required" || d.review_state === "Revision Requested";
  const canCertify = d.review_state === "Founder Approved";

  const requestRevision = () => {
    const notes = window.prompt("What should be revised? (educational feedback)", "");
    if (notes === null) return;
    act("request-revision", "Revision requested — returned to author.", notes);
  };

  return (
    <div data-testid="decoder-detail">
      <button onClick={onBack} data-testid="detail-back" className="inline-flex items-center gap-1.5 text-sm text-navy font-semibold mb-4 hover:underline">
        <ArrowLeft className="w-4 h-4" /> Back to Founder Review Shelf™
      </button>

      {/* Header */}
      <div className="qru-card qru-goldline p-5 mb-5">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div className="min-w-0">
            <h2 className="font-heading text-2xl font-bold text-navy leading-tight" data-testid="detail-title">{d.title}</h2>
            <div className="flex items-center gap-2 flex-wrap mt-2">
              <span className="font-mono text-[11px] text-muted-foreground" data-testid="detail-decoder-id">{d.decoder_id}</span>
              <StatusChip status={d.review_state} testid="detail-state" />
              {d.is_canonical && <StatusChip status="Canonical" tone="gold" />}
              <StatusChip status={`v${d.decoder_version}`} tone="navy" />
              <StatusChip status={d.domain || "General"} tone="royal" />
              <StatusChip status={d.audience || "General"} tone="navy" />
            </div>
            <p className="text-[11px] text-muted-foreground mt-2">{d.governance_banner}</p>
          </div>
        </div>

        {d.safety_notes && (
          <div className="mt-3 text-[12px] bg-amber-50 border border-amber-200 text-amber-800 rounded-md px-3 py-2" data-testid="detail-safety">
            <b>Safety:</b> {d.safety_notes}
          </div>
        )}
        {(d.flags || []).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5" data-testid="detail-flags">
            {d.flags.map((f, i) => <StatusChip key={i} status={f} tone="amber" />)}
          </div>
        )}

        {/* Founder actions */}
        <div className="mt-4 flex items-center gap-2 flex-wrap" data-testid="detail-actions">
          <button data-testid="action-approve" onClick={() => act("approve", "Educational quality approved by Founder.")}
            disabled={acting || !isSuper || !canApprove}
            className="inline-flex items-center gap-1.5 bg-emerald-600 text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40">
            {acting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ThumbsUp className="w-4 h-4" />} Approve
          </button>
          <button data-testid="action-revise" onClick={requestRevision} disabled={acting || !isSuper}
            className="inline-flex items-center gap-1.5 border border-royal/40 text-royal px-4 py-2 rounded-md text-sm font-semibold disabled:opacity-40">
            <RotateCcw className="w-4 h-4" /> Request Revision
          </button>
          <button data-testid="action-certify" onClick={() => act("certify-treasure", "Treasure Standard™ certified.")}
            disabled={acting || !isSuper || !canCertify}
            className="inline-flex items-center gap-1.5 bg-gold text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-40"
            title={canCertify ? "Certify Treasure Standard™" : "Requires Founder Approved first"}>
            <Award className="w-4 h-4" /> Certify Treasure Standard™
          </button>
          <button data-testid="action-archive" onClick={() => act("archive", "Archived.")} disabled={acting || !isSuper}
            className="inline-flex items-center gap-1.5 border border-border text-muted-foreground px-4 py-2 rounded-md text-sm font-medium disabled:opacity-40">
            <Archive className="w-4 h-4" /> Archive
          </button>
          <button data-testid="action-export" onClick={exportJson}
            className="inline-flex items-center gap-1.5 border border-navy/20 text-navy px-4 py-2 rounded-md text-sm font-medium ml-auto">
            <Download className="w-4 h-4" /> Export
          </button>
        </div>
        {!isSuper && <p className="text-[11px] text-amber-700 mt-2">Only the Founder / Administrator can approve, certify, or archive.</p>}
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        {/* Key learning fields */}
        <div className="lg:col-span-2 space-y-4">
          <Panel title="Understanding" icon={Lightbulb} accent="gold" testid="detail-understanding">
            <div className="space-y-4">
              <Field label="Purpose" value={d.purpose} />
              <Field label="Definition" value={d.definition} />
              <Field label="Why It Matters" value={d.why_it_matters} />
              <Field label="How It Works" value={d.how_it_works} />
              <div className="rounded-md bg-royal/[0.05] border border-royal/15 p-3">
                <Field label="Core Mental Model™" value={d.core_mental_model} />
              </div>
              <Field label="Analogy" value={d.analogy} />
              <Field label="Analogy Mapping" value={d.analogy_mapping} />
              <Field label="Analogy Limitations (where it breaks down)" value={d.analogy_limitations} />
              <Field label="Story" value={d.story} />
              {(vs.purpose || vs.primary_subject || vs.alt_text) && (
                <div>
                  <p className="text-[11px] font-bold text-navy uppercase tracking-wide mb-1">Visual Specification</p>
                  <div className="text-sm text-foreground/90 space-y-1">
                    {vs.purpose && <p><b>Purpose:</b> {vs.purpose}</p>}
                    {vs.primary_subject && <p><b>Subject:</b> {vs.primary_subject}</p>}
                    {vs.relationship && <p><b>Relationship:</b> {vs.relationship}</p>}
                    {vs.composition && <p><b>Composition:</b> {vs.composition}</p>}
                    {(vs.labels || []).length > 0 && <p><b>Labels:</b> {vs.labels.join(", ")}</p>}
                    {(vs.must_not_appear || []).length > 0 && <p><b>Must not appear:</b> {vs.must_not_appear.join(", ")}</p>}
                    {vs.alt_text && <p><b>Alt text:</b> {vs.alt_text}</p>}
                  </div>
                </div>
              )}
              <div className="rounded-md bg-gold/[0.08] border border-gold/30 p-3">
                <Field label="Memory Anchor™" value={d.memory_anchor} />
              </div>
              <Field label="Verification" value={d.verification} />
            </div>
          </Panel>

          <Panel title="Five-Part Understanding Test™" icon={ListChecks} accent="royal" testid="detail-understanding-test">
            <div className="space-y-3" data-testid="understanding-checks">
              {[["explain", "Explain"], ["recognize", "Recognize"], ["apply", "Apply"], ["correct", "Correct"], ["teach", "Teach"]].map(([k, label]) => (
                uc[k] ? (
                  <div key={k} className="flex items-start gap-2">
                    <span className="w-5 h-5 shrink-0 rounded-full bg-royal/15 text-royal text-[10px] font-bold flex items-center justify-center">{label[0]}</span>
                    <div><span className="font-bold text-navy text-[12px] uppercase tracking-wide">{label}</span>
                      <p className="text-sm text-foreground/90">{typeof uc[k] === "object" ? JSON.stringify(uc[k]) : uc[k]}</p></div>
                  </div>
                ) : null
              ))}
            </div>
          </Panel>

          <Section title="Practice, Examples & More" icon={BookOpen} testid="detail-secondary-learning">
            <Field label="Guided Example" value={d.guided_example} />
            <Field label="Practice" value={d.practice} />
            <Field label="Reflection" value={d.reflection} />
            <Field label="Next Understanding" value={d.next_understanding} />
            {(d.applications || []).length > 0 && (
              <div>
                <p className="text-[11px] font-bold text-navy uppercase tracking-wide mb-1">Applications</p>
                <ul className="list-disc pl-5 text-sm text-foreground/90 space-y-1">{d.applications.map((a, i) => <li key={i}>{typeof a === "object" ? Object.values(a).join(" — ") : a}</li>)}</ul>
              </div>
            )}
            {(d.vocabulary || []).length > 0 && (
              <div>
                <p className="text-[11px] font-bold text-navy uppercase tracking-wide mb-1">Vocabulary</p>
                <dl className="text-sm space-y-1">{d.vocabulary.map((v, i) => (
                  <div key={i}><dt className="font-semibold text-navy inline">{v.term}: </dt><dd className="inline text-foreground/90">{v.definition}</dd></div>
                ))}</dl>
              </div>
            )}
            {(d.misconceptions || []).length > 0 && (
              <div>
                <p className="text-[11px] font-bold text-navy uppercase tracking-wide mb-1">Misconceptions → Corrections</p>
                <ul className="text-sm space-y-1.5">{d.misconceptions.map((m, i) => (
                  <li key={i}><span className="text-red-600 line-through">{m.misconception}</span> — <span className="text-emerald-700">{m.why_wrong}</span></li>
                ))}</ul>
              </div>
            )}
            <Field label="Accessibility Notes" value={d.accessibility_notes} />
            <Field label="Downstream Notes" value={d.downstream_notes} />
          </Section>

          {d.educational_design_rationale && Object.keys(d.educational_design_rationale).length > 0 && (
            <Section title="Educational Design Rationale™ (auditable)" icon={GitBranch} testid="detail-rationale">
              {Object.entries(d.educational_design_rationale).map(([k, v]) => (
                v ? <Field key={k} label={k.replace(/_/g, " ")} value={typeof v === "string" ? v : JSON.stringify(v)} /> : null
              ))}
            </Section>
          )}
        </div>

        {/* Scorecard + provenance */}
        <div className="space-y-4">
          <Panel title="Decoder Scorecard™" icon={FlaskConical} accent="royal" testid="detail-scorecard">
            <p className="text-[11px] text-muted-foreground mb-3">
              {(d.scorecard || {}).model_note || "Advisory scores support — never replace — Founder judgment."}
            </p>
            <div className="space-y-2" data-testid="scorecard-rows">
              {rows.map((r, i) => {
                const badge = EVAL_BADGE[r.evaluator] || { label: r.evaluator, tone: "slate" };
                const awaiting = r.score == null || r.score === "";
                return (
                  <div key={i} className="flex items-start justify-between gap-2 text-[12px] border-b border-border/60 pb-1.5">
                    <div className="min-w-0">
                      <p className="text-navy leading-tight">{r.dimension}</p>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <StatusChip status={badge.label} tone={badge.tone} />
                        {r.evaluator === "deterministic" && <StatusChip status={r.score ? "pass" : "review"} />}
                        {awaiting && r.evaluator !== "deterministic" && <StatusChip status="Awaiting Review" tone="amber" />}
                      </div>
                    </div>
                    {r.evaluator !== "deterministic" && !awaiting && (
                      <span className="font-bold text-navy shrink-0">{r.score}</span>
                    )}
                    {r.evaluator === "deterministic" && (
                      r.score ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <Clock className="w-4 h-4 text-amber-600 shrink-0" />
                    )}
                  </div>
                );
              })}
            </div>
            {(d.scorecard || {}).advisory_notes && (
              <p className="text-[11px] text-muted-foreground mt-3 italic">{d.scorecard.advisory_notes}</p>
            )}
          </Panel>

          <Section title="Provenance & Metadata" icon={ScrollText} testid="detail-provenance">
            <div className="text-[12px] space-y-1.5 text-foreground/90">
              <p><b>Decoder ID:</b> <span className="font-mono">{d.decoder_id}</span></p>
              <p><b>Version:</b> v{d.decoder_version} {d.is_canonical && "(Canonical)"}</p>
              <p><b>Confidence Status:</b> {d.confidence_status}</p>
              <p><b>Domain:</b> {d.domain}{d.subdomain ? ` › ${d.subdomain}` : ""}</p>
              <p><b>Audience / Level:</b> {d.audience} · {d.level}</p>
              <p><b>Shelf:</b> {d.shelf_location}</p>
              <div>
                <b>Source Knowledge Record(s):</b>
                <ul className="list-disc pl-5 mt-0.5">
                  {(d.source_kr_ids || []).map((s, i) => (
                    <li key={i} className="font-mono text-[11px]">{s.kr_code || s.kr_id} · v{s.version}</li>
                  ))}
                </ul>
              </div>
              <p><b>Decoded by:</b> {(d.provenance || {}).decoded_by} · {(d.provenance || {}).at}</p>
            </div>
          </Section>

          <Section title="Review History (audit log)" icon={ListChecks} testid="detail-history">
            <ol className="space-y-2" data-testid="review-history">
              {(d.review_history || []).map((h, i) => (
                <li key={i} className="text-[12px] border-l-2 border-royal/30 pl-3">
                  <p className="font-semibold text-navy">{h.state}</p>
                  <p className="text-muted-foreground">{h.by} · {h.at}</p>
                  {h.note && <p className="text-foreground/80">{h.note}</p>}
                </li>
              ))}
            </ol>
          </Section>
        </div>
      </div>
    </div>
  );
}
