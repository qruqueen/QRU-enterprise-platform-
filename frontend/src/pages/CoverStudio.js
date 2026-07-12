import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import { Loader2, Image as ImageIcon, Sparkles, ShieldCheck, CheckCircle2, RotateCcw, Ban, Award, Wand2 } from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";

const STATE_TONE = {
  DRAFT_CONCEPT: "slate", UNDER_REVIEW: "blue", REVISION_REQUIRED: "amber",
  APPROVED_DESIGN: "emerald", GOLD_MASTER: "gold", RETIRED_SUPERSEDED: "rose",
};
const NEXT_ACTIONS = [
  { state: "UNDER_REVIEW", label: "Send to Review", icon: ShieldCheck },
  { state: "REVISION_REQUIRED", label: "Request Revision", icon: RotateCcw },
  { state: "APPROVED_DESIGN", label: "Approve Design", icon: CheckCircle2 },
  { state: "GOLD_MASTER", label: "Certify Gold Master", icon: Award },
  { state: "RETIRED_SUPERSEDED", label: "Retire", icon: Ban },
];

export default function CoverStudio() {
  const [form, setForm] = useState({
    title: "The Science of Understanding",
    subtitle: "What We Keep Mistaking for Understanding — and What It Actually Is",
    series: "QRU Foundations", edition: "Consumer Edition", trim: "kdp_ebook",
    concept_notes: "A luminous human head profile made of interlocking gears becoming clear glass — real comprehension emerging from mechanism",
    concepts: 2, mode: "ai",
  });
  const [busy, setBusy] = useState(false);
  const [covers, setCovers] = useState([]);
  const [states, setStates] = useState([]);

  const load = () => api.get("/publishing/covers").then((r) => { setCovers(r.data.covers); setStates(r.data.states); }).catch(() => {});
  useEffect(() => { load(); }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const generate = async () => {
    if (!form.title.trim()) return toast.error("Enter a title.");
    setBusy(true);
    try {
      const { data } = await api.post("/publishing/cover/generate", form);
      if (data.ok) toast.success(`${data.concepts.length} draft concept(s) generated. Human approval required.`);
      else toast.error(data.note || "Generation unavailable — try spec-only or upload a manual asset.");
      load();
    } catch (e) { toast.error(e.response?.data?.detail || "Cover generation failed."); }
    finally { setBusy(false); }
  };

  const transition = async (cid, state) => {
    try { await api.post(`/publishing/cover/${cid}/state`, { state }); toast.success(`State → ${state.replace(/_/g, " ")}`); load(); }
    catch (e) { toast.error(e.response?.data?.detail || "State change blocked."); }
  };

  return (
    <div data-testid="cover-studio-page">
      <PageHeader
        overline="QRU Cover & Visual Identity Standard™ · QRU-CON-0002"
        title="Cover Studio"
        description="A governed cover-production environment — not text over a background. Generate original concepts in the QRU design family, then move each through Draft → Review → Approved → Gold Master with full provenance. AI is a governed tool; every cover requires human approval."
        actions={<VerifiedBadge label="Provenance tracked · Human approval always" testid="cover-badge" />}
      />

      <div className="grid lg:grid-cols-3 gap-5">
        {/* Brief */}
        <Panel title="Cover Brief" icon={Sparkles} accent="royal" testid="cover-brief">
          <div className="space-y-2.5">
            {[["title", "Title"], ["subtitle", "Subtitle"], ["series", "Series"], ["edition", "Edition"]].map(([k, label]) => (
              <div key={k}>
                <label className="text-[10px] font-bold uppercase tracking-wide text-navy">{label}</label>
                <input data-testid={`cover-${k}`} value={form[k]} onChange={(e) => set(k, e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm" />
              </div>
            ))}
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Trim / format</label>
              <select data-testid="cover-trim" value={form.trim} onChange={(e) => set("trim", e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm">
                <option value="kdp_ebook">eBook / KDP (2:3)</option>
                <option value="us_trade_6x9">US Trade 6×9</option>
                <option value="square_1x1">Square (podcast/social)</option>
                <option value="video_16x9">Video thumbnail 16:9</option>
                <option value="reel_9x16">Reel 9:16</option>
              </select>
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Visual concept (no manuscript)</label>
              <textarea data-testid="cover-notes" value={form.concept_notes} onChange={(e) => set("concept_notes", e.target.value)} rows={3} className="w-full mt-0.5 border rounded-sm p-2 text-sm" />
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Concepts</label>
                <select data-testid="cover-count" value={form.concepts} onChange={(e) => set("concepts", Number(e.target.value))} className="w-full mt-0.5 border rounded-sm p-2 text-sm">
                  {[1, 2, 3].map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <div className="flex-1">
                <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Mode</label>
                <select data-testid="cover-mode" value={form.mode} onChange={(e) => set("mode", e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm">
                  <option value="ai">AI concepts (governed)</option>
                  <option value="spec_only">Spec-only / manual asset</option>
                </select>
              </div>
            </div>
            <button onClick={generate} disabled={busy} data-testid="cover-generate"
              className="w-full inline-flex items-center justify-center gap-2 bg-navy text-white px-4 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} {busy ? "Manufacturing concepts…" : "Generate Concepts"}
            </button>
            <p className="text-[10px] text-muted-foreground">Draft concepts require human approval before becoming an Approved Design or Gold Master. Provider outage falls back to spec-only — publishing is never blocked.</p>
          </div>
        </Panel>

        {/* Gallery */}
        <div className="lg:col-span-2">
          <Panel title="Cover Concepts & Production States" icon={ImageIcon} accent="gold" testid="cover-gallery">
            {covers.length === 0 ? (
              <p className="text-sm text-muted-foreground py-8 text-center">No covers yet. Generate your first governed concept.</p>
            ) : (
              <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
                {covers.map((c) => (
                  <div key={c.id} className="border rounded-md overflow-hidden border-navy/10" data-testid={`cover-item-${c.id}`}>
                    {c.file_url ? <img src={`${BACKEND}${c.file_url}`} alt={c.title} className="w-full h-56 object-cover bg-navy/5" />
                      : <div className="w-full h-56 grid place-items-center bg-navy/[0.04] text-[11px] text-muted-foreground text-center px-3">Spec-only concept<br />(attach a manual/licensed asset)</div>}
                    <div className="p-2.5">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <p className="text-[11px] font-bold text-navy truncate">{c.title}</p>
                        <StatusChip status={c.state.replace(/_/g, " ")} tone={STATE_TONE[c.state] || "slate"} />
                      </div>
                      <p className="text-[9px] text-muted-foreground">{c.provenance?.provider || "manual"} · {c.provenance?.model || "—"} · v{c.provenance?.version || "—"}</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {NEXT_ACTIONS.filter((a) => a.state !== c.state).map((a) => {
                          const Ic = a.icon;
                          return (
                            <button key={a.state} onClick={() => transition(c.id, a.state)} data-testid={`cover-state-${c.id}-${a.state}`}
                              className="text-[9px] inline-flex items-center gap-1 px-1.5 py-0.5 rounded border border-navy/15 text-navy hover:border-royal hover:text-royal transition-colors">
                              <Ic className="w-2.5 h-2.5" /> {a.label}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
