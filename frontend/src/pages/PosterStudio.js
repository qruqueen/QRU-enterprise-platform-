import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import { Loader2, LayoutTemplate, Wand2, ShieldCheck, Download, CheckCircle2, AlertTriangle, FileText } from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";

const STATUS_TONE = {
  DRAFT: "slate", INTERNAL_REVIEW: "blue", VERIFICATION_REQUIRED: "amber", REVISION_REQUIRED: "rose",
  DESIGN_APPROVED: "emerald", PRINT_READY: "emerald", PUBLISHING_READY: "emerald",
  QRU_GOLD_STANDARD: "gold", SUPERSEDED: "slate",
};

export default function PosterStudio() {
  const [templates, setTemplates] = useState([]);
  const [posters, setPosters] = useState([]);
  const [busy, setBusy] = useState(false);
  const [sel, setSel] = useState(null);
  const [form, setForm] = useState({
    template_id: "process-formula-v1", is_factual: false, kr_id: "",
    eyebrow: "THE QRU", title: "LEARNING FORMULA", trademark: true,
    tagline: "SIMPLE.  POWERFUL.  TRANSFORMATIVE.",
    subtitle: "WE DON'T JUST TEACH INFORMATION. WE CREATE UNDERSTANDING.",
    footer: "CURIOSITY STARTS THE JOURNEY.  UNDERSTANDING CHANGES EVERYTHING.",
  });

  const load = () => {
    api.get("/publishing/poster/templates").then((r) => setTemplates(r.data.templates)).catch(() => {});
    api.get("/publishing/posters").then((r) => setPosters(r.data.posters || [])).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const generate = async () => {
    setBusy(true);
    try {
      const payload = { ...form, kr_id: form.kr_id || null };
      const { data } = await api.post("/publishing/poster/generate", payload);
      setSel(data);
      setPosters((p) => [data, ...p.filter((x) => x.id !== data.id)]);
      if (data.validation.blocked) toast.warning("Poster rendered with blocking issues — see validation.");
      else toast.success(`Poster manufactured · ${data.status.replace(/_/g, " ")}.`);
    } catch (e) { toast.error(e.response?.data?.detail || "Poster generation failed."); }
    finally { setBusy(false); }
  };

  const setStatus = async (pid, status) => {
    try {
      const { data } = await api.post(`/publishing/poster/${pid}/status`, { status });
      setSel(data); load();
      toast.success(`Status → ${status.replace(/_/g, " ")}`);
    } catch (e) { toast.error(e.response?.data?.detail || "Status change blocked."); }
  };

  const selTmpl = templates.find((t) => t.id === form.template_id);

  return (
    <div data-testid="poster-studio-page">
      <PageHeader
        overline="QRU Poster Studio™ · Governed Templates · QRU-CON-0002"
        title="Poster Studio"
        description="Machine-rendered infographic posters — templates control every word, number, citation and dimension. AI art is composited only. Factual posters require a verified Knowledge Record™ before Gold Standard."
        actions={<VerifiedBadge label="Template-controlled · Knowledge-First" testid="poster-badge" />}
      />

      <div className="grid lg:grid-cols-[360px_1fr] gap-5">
        {/* Brief */}
        <Panel title="Poster Brief" icon={LayoutTemplate} accent="royal" testid="poster-brief">
          <div className="space-y-2.5">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Template family</label>
              <select data-testid="poster-template" value={form.template_id} onChange={(e) => set("template_id", e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm">
                {templates.map((t) => <option key={t.id} value={t.id}>{t.family} · {t.dimensions.aspect}</option>)}
              </select>
            </div>
            {[["eyebrow", "Eyebrow"], ["title", "Title"], ["tagline", "Tagline"], ["subtitle", "Subtitle"], ["footer", "Footer"]].map(([k, label]) => (
              <div key={k}>
                <label className="text-[10px] font-bold uppercase tracking-wide text-navy">{label}</label>
                <input data-testid={`poster-${k}`} value={form[k]} onChange={(e) => set(k, e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm" />
              </div>
            ))}
            <label className="flex items-center gap-2 text-[11px] text-navy">
              <input type="checkbox" data-testid="poster-trademark" checked={form.trademark} onChange={(e) => set("trademark", e.target.checked)} /> Show ™ on title
            </label>
            <div className="border-t border-navy/10 pt-2">
              {selTmpl?.factual && (
                <p className="text-[10px] text-amber-700 font-bold mb-1">This template is data/factual — a verified Knowledge Record is required for Gold Standard.</p>
              )}
              <label className="flex items-center gap-2 text-[11px] text-navy font-bold">
                <input type="checkbox" data-testid="poster-factual" checked={form.is_factual || !!selTmpl?.factual} disabled={!!selTmpl?.factual} onChange={(e) => set("is_factual", e.target.checked)} /> Contains factual data / statistics
              </label>
              {(form.is_factual || selTmpl?.factual) && (
                <div className="mt-2">
                  <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Verified Knowledge Record ID (required for Gold)</label>
                  <input data-testid="poster-kr-id" value={form.kr_id} onChange={(e) => set("kr_id", e.target.value)} placeholder="KR id from Refinement / Verify & Promote" className="w-full mt-0.5 border rounded-sm p-2 text-xs" />
                  <p className="text-[9px] text-amber-700 mt-1">Knowledge-First: factual posters stay INTERNAL DRAFT until the source KR is externally verified.</p>
                </div>
              )}
            </div>
            <button onClick={generate} disabled={busy} data-testid="poster-generate"
              className="w-full inline-flex items-center justify-center gap-2 bg-navy text-white px-4 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} {busy ? "Manufacturing…" : "Manufacture Poster"}
            </button>
          </div>
        </Panel>

        {/* Preview + gallery */}
        <div className="space-y-5">
          {sel && (
            <Panel title={`Preview · ${sel.title}`} icon={ShieldCheck} accent="gold" testid="poster-preview">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <StatusChip status={sel.status.replace(/_/g, " ")} tone={STATUS_TONE[sel.status] || "slate"} />
                <StatusChip status={`Treasure: ${sel.treasure_status === "TREASURE_STANDARD_PASSED" ? "Passed" : "Return"}`} tone={sel.treasure_status === "TREASURE_STANDARD_PASSED" ? "emerald" : "rose"} />
                {sel.is_factual && <StatusChip status={`Verify: ${sel.verification_status}`} tone={sel.verification_status === "VERIFIED_EXTERNAL" ? "emerald" : "amber"} />}
                <span className="text-[10px] text-muted-foreground">{sel.resolution_px} · sRGB · template v{sel.template_version}</span>
              </div>
              <div className="grid md:grid-cols-[1fr_240px] gap-4">
                <img data-testid="poster-preview-img" src={`${BACKEND}${sel.png_url}`} alt={sel.title} className="w-full rounded-md border border-navy/10 bg-ink" />
                <div className="space-y-2">
                  <a href={`${BACKEND}${sel.png_url}`} target="_blank" rel="noreferrer" data-testid="poster-dl-png" className="flex items-center gap-2 text-[12px] border border-navy/15 rounded-sm px-3 py-2 hover:border-royal text-navy"><Download className="w-3.5 h-3.5" /> PNG (screen)</a>
                  <a href={`${BACKEND}${sel.pdf_url}`} target="_blank" rel="noreferrer" data-testid="poster-dl-pdf" className="flex items-center gap-2 text-[12px] border border-navy/15 rounded-sm px-3 py-2 hover:border-royal text-navy"><FileText className="w-3.5 h-3.5" /> PDF (print · vector)</a>
                  <div className="border rounded-md p-2.5 border-navy/10">
                    <p className="text-[10px] font-bold uppercase tracking-wide text-navy mb-1">Pre-Ship Gate</p>
                    {sel.validation.checks.map((c, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-[10px] mb-0.5" data-testid={`poster-check-${i}`}>
                        {c.passed ? <CheckCircle2 className="w-3 h-3 text-emerald-600 mt-0.5 shrink-0" /> : <AlertTriangle className="w-3 h-3 text-rose-600 mt-0.5 shrink-0" />}
                        <span className={c.passed ? "text-navy/70" : "text-rose-700"}>{c.check}</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {sel.status === "DRAFT" && <button onClick={() => setStatus(sel.id, "DESIGN_APPROVED")} data-testid="poster-approve" className="text-[10px] px-2 py-1 rounded border border-emerald-300 text-emerald-800 bg-emerald-50 font-bold">Approve Design</button>}
                    {sel.status === "DESIGN_APPROVED" && <button onClick={() => setStatus(sel.id, "QRU_GOLD_STANDARD")} data-testid="poster-gold" className="text-[10px] px-2 py-1 rounded border border-amber-400 text-amber-800 bg-amber-50 font-bold">Certify Gold Standard</button>}
                  </div>
                </div>
              </div>
            </Panel>
          )}

          <Panel title="Manufactured Posters" icon={LayoutTemplate} accent="royal" testid="poster-gallery">
            {posters.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">No posters yet. Manufacture your first governed poster.</p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {posters.map((p) => (
                  <button key={p.id} onClick={() => setSel(p)} data-testid={`poster-item-${p.id}`} className="text-left border rounded-md overflow-hidden border-navy/10 hover:border-royal transition-colors">
                    <img src={`${BACKEND}${p.thumb_url}`} alt={p.title} className="w-full aspect-[4/5] object-cover bg-ink" />
                    <div className="p-2">
                      <p className="text-[10px] font-bold text-navy truncate">{p.title}</p>
                      <StatusChip status={p.status.replace(/_/g, " ")} tone={STATUS_TONE[p.status] || "slate"} />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
