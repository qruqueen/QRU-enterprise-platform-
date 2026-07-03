import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/shared";
import { toast } from "sonner";
import {
  Sprout, ArrowUpCircle, Loader2, Save, ShieldCheck, FileText, CheckCircle2, Circle, Search,
} from "lucide-react";

const REQUIRED_HINT = "Required to promote";

export default function PromotionPipeline() {
  const [seeds, setSeeds] = useState([]);
  const [schema, setSchema] = useState({ fields: [], required: [] });
  const [q, setQ] = useState("");
  const [selId, setSelId] = useState(null);
  const [form, setForm] = useState({});
  const [source, setSource] = useState({ source_note: "", source_document: "" });
  const [saving, setSaving] = useState(false);
  const [promoting, setPromoting] = useState(false);

  const loadSeeds = () =>
    api.get("/promotion/seeds", { params: q ? { q } : {} }).then((r) => setSeeds(r.data)).catch(() => {});

  useEffect(() => {
    api.get("/promotion/schema").then((r) => setSchema(r.data)).catch(() => {});
  }, []);
  useEffect(() => { loadSeeds(); }, [q]);

  const selectSeed = async (id) => {
    setSelId(id);
    const { data } = await api.get(`/promotion/${id}`);
    const f = {};
    (schema.fields || []).forEach((fd) => { f[fd.key] = data[fd.key] || ""; });
    f.verified_truth = data.verified_truth || "";
    setForm(f);
    setSource({ source_note: data.source_note || "", source_document: data.source_document || "" });
  };

  const sel = seeds.find((s) => s.id === selId);
  const isReq = (k) => (schema.required || []).includes(k);
  const filled = (k) => !!(form[k] && String(form[k]).trim());
  const missingRequired = (schema.required || []).filter((k) => !filled(k));
  const canPromote = missingRequired.length === 0 && !!source.source_note.trim();

  const saveDraft = async () => {
    if (!selId) return;
    setSaving(true);
    try {
      await api.put(`/promotion/${selId}/fields`, form);
      toast.success("Draft saved");
      loadSeeds();
    } catch (e) { toast.error(e.response?.data?.detail || "Save failed"); }
    finally { setSaving(false); }
  };

  const promote = async () => {
    if (!selId) return;
    if (!canPromote) return toast.error("Complete all required fields and add a source note first");
    setPromoting(true);
    try {
      await api.put(`/promotion/${selId}/fields`, form);
      await api.post(`/promotion/${selId}/promote`, source);
      toast.success("Promoted to Verified Knowledge Record™");
      setSelId(null); setForm({}); setSource({ source_note: "", source_document: "" });
      loadSeeds();
    } catch (e) { toast.error(e.response?.data?.detail || "Promotion failed"); }
    finally { setPromoting(false); }
  };

  return (
    <div>
      <PageHeader
        overline="Knowledge Record Promotion Pipeline™"
        title="Promote Topic Seeds to Verified Knowledge"
        description="Knowledge-First Manufacturing. Enter verified content from your Founder source documents — no AI generation. Once complete, promote a Topic Seed into an Imported Verified Knowledge Record™ ready for manufacturing."
      />

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Seed list */}
        <div className="bg-card border rounded-md p-4 h-fit lg:sticky lg:top-24" data-testid="promotion-seed-list">
          <div className="relative mb-3">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input data-testid="promotion-search" value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Search Topic Seeds…"
              className="w-full pl-9 pr-3 py-2 text-sm border rounded-sm bg-card outline-none focus:border-primary" />
          </div>
          {seeds.length === 0 ? (
            <EmptyState icon={Sprout} title="No Topic Seeds" description="All seeds have been promoted, or none exist yet." />
          ) : (
            <div className="space-y-1.5 max-h-[70vh] overflow-y-auto pr-1">
              {seeds.map((s) => {
                const p = s.promotion || {};
                return (
                  <button key={s.id} data-testid={`promotion-seed-${s.kr_code}`} onClick={() => selectSeed(s.id)}
                    className={`w-full text-left p-3 rounded-md border transition-colors ${selId === s.id ? "border-primary bg-primary/[0.05]" : "hover:border-primary/40"}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-[10px] text-muted-foreground">{s.kr_code}</span>
                      {p.ready_to_promote
                        ? <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">Ready</span>
                        : <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">Seed</span>}
                    </div>
                    <p className="text-sm font-medium mt-0.5 leading-snug">{s.title}</p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-gold" style={{ width: `${p.required_total ? (p.required_done / p.required_total) * 100 : 0}%` }} />
                      </div>
                      <span className="text-[10px] text-muted-foreground">{p.required_done || 0}/{p.required_total || 0}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Editing workspace */}
        <div className="lg:col-span-2">
          {!sel ? (
            <div className="bg-card border border-dashed rounded-md p-12 flex flex-col items-center justify-center text-center">
              <ArrowUpCircle className="w-10 h-10 text-muted-foreground mb-4" strokeWidth={1.5} />
              <p className="font-heading font-semibold">Select a Topic Seed</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">Choose a seed on the left to open its Guided Understanding System™ editing workspace.</p>
            </div>
          ) : (
            <div className="bg-card border rounded-md p-6 space-y-5 animate-fade-up" data-testid="promotion-workspace">
              <div className="flex items-start justify-between gap-3 pb-4 border-b">
                <div>
                  <span className="font-mono text-xs text-muted-foreground">{sel.kr_code} · {sel.curriculum || sel.category}</span>
                  <h2 className="font-heading text-xl font-bold mt-1">{sel.title}</h2>
                  <p className="text-xs text-muted-foreground mt-1">Topic Seed · Founder Approved · Treasure Standard™ Pending · AI Content: None</p>
                </div>
                <span className="text-[10px] px-2 py-1 rounded bg-navy/5 border shrink-0">Guided Understanding System™</span>
              </div>

              {/* Verified Truth — the source of truth */}
              <div>
                <label className="text-sm font-semibold flex items-center gap-1.5">
                  Verified Truth {isReq("verified_truth") && <span className="text-destructive" title={REQUIRED_HINT}>*</span>}
                </label>
                <p className="text-[11px] text-muted-foreground mb-1">The verified truth imported from your Founder source document.</p>
                <textarea data-testid="promotion-field-verified_truth" rows={3} value={form.verified_truth || ""}
                  onChange={(e) => setForm({ ...form, verified_truth: e.target.value })}
                  className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm resize-y" />
              </div>

              {(schema.fields || []).map((fd) => (
                <div key={fd.key}>
                  <label className="text-sm font-semibold flex items-center gap-1.5">
                    {fd.label} {fd.required && <span className="text-destructive" title={REQUIRED_HINT}>*</span>}
                    {filled(fd.key) ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <Circle className="w-3.5 h-3.5 text-muted-foreground/40" />}
                  </label>
                  {fd.help && <p className="text-[11px] text-muted-foreground mb-1">{fd.help}</p>}
                  {fd.type === "textarea" ? (
                    <textarea data-testid={`promotion-field-${fd.key}`} rows={3} value={form[fd.key] || ""}
                      onChange={(e) => setForm({ ...form, [fd.key]: e.target.value })}
                      className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm resize-y" />
                  ) : (
                    <input data-testid={`promotion-field-${fd.key}`} value={form[fd.key] || ""}
                      onChange={(e) => setForm({ ...form, [fd.key]: e.target.value })}
                      className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm" />
                  )}
                </div>
              ))}

              {/* Provenance */}
              <div className="border-t pt-4">
                <p className="text-sm font-semibold flex items-center gap-1.5 mb-1"><FileText className="w-4 h-4 text-primary" /> Source & Provenance</p>
                <p className="text-[11px] text-muted-foreground mb-2">Required. Cite the Founder document this content came from (Knowledge-First Manufacturing).</p>
                <input data-testid="promotion-source-note" value={source.source_note}
                  onChange={(e) => setSource({ ...source, source_note: e.target.value })}
                  placeholder="e.g. Imported verbatim from QFC-001_Master_Manuscript_v0.5.docx, §2.1"
                  className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm mb-2" />
                <input data-testid="promotion-source-doc" value={source.source_document}
                  onChange={(e) => setSource({ ...source, source_document: e.target.value })}
                  placeholder="Source document name (optional)"
                  className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm" />
              </div>

              {missingRequired.length > 0 && (
                <p className="text-[12px] text-amber-700 bg-amber-50 border border-amber-200 rounded-sm px-3 py-2">
                  Complete all required fields (*) and a source note to promote.
                </p>
              )}

              <div className="flex flex-wrap gap-2 pt-1">
                <button data-testid="promotion-save-btn" onClick={saveDraft} disabled={saving || promoting}
                  className="flex items-center gap-2 border px-4 py-2.5 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors disabled:opacity-60">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Save Draft
                </button>
                <button data-testid="promotion-promote-btn" onClick={promote} disabled={!canPromote || promoting || saving}
                  className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2.5 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50">
                  {promoting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />} Promote to Verified Knowledge Record™
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
