import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { StatusChip, Panel } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, Save, FileText, CheckCircle2, Clock, ChevronDown, ChevronRight, Layers, Boxes,
} from "lucide-react";

const STATUS_STYLE = {
  Pending: "bg-slate-100 text-slate-500 border-slate-200",
  Draft: "bg-blue-50 text-blue-700 border-blue-200",
  "Under Review": "bg-amber-50 text-amber-700 border-amber-200",
  Verified: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Superseded: "bg-slate-100 text-slate-400 border-slate-200",
  Archived: "bg-slate-100 text-slate-400 border-slate-200",
};
const STATUS_VALUES = ["Pending", "Draft", "Under Review", "Verified", "Approved", "Superseded", "Archived"];
const SOURCE_VALUES = ["Founder", "AI", "Deterministic", "Imported", "Human Expert"];

function SectionCard({ krId, section, onSaved }) {
  const [open, setOpen] = useState(false);
  const [content, setContent] = useState(section.content || "");
  const [status, setStatus] = useState(section.status);
  const [source, setSource] = useState(section.source || "Founder");
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      const { data } = await api.put(`/kr2/${krId}/section/${section.section_id}`, { content, status, source });
      toast.success(`${section.title} saved (v${data.version})`);
      onSaved();
    } catch (e) { toast.error(e.response?.data?.detail || "Save failed"); }
    finally { setBusy(false); }
  };

  return (
    <div className="border rounded-lg" data-testid={`kr2-section-${section.section_id}`}>
      <button onClick={() => setOpen((v) => !v)} className="w-full flex items-center justify-between p-3 text-left">
        <div className="flex items-center gap-2 min-w-0">
          {open ? <ChevronDown className="w-4 h-4 text-muted-foreground shrink-0" /> : <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />}
          <span className="text-sm font-medium text-navy truncate">{section.title}</span>
          {section.manufacturing_ready && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <StatusChip status={section.status} />
          {section.version > 0 && <span className="text-[9px] text-muted-foreground">v{section.version}</span>}
        </div>
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2">
          {section.depended_on_by?.length > 0 && (
            <p className="text-[10px] text-muted-foreground flex items-center gap-1"><Boxes className="w-3 h-3" /> Manufactures: {section.depended_on_by.join(", ")}</p>
          )}
          <textarea data-testid={`kr2-content-${section.section_id}`} value={content} onChange={(e) => setContent(e.target.value)} rows={4}
            className="w-full border rounded-sm p-2 text-sm" placeholder={`Write the ${section.title} (AI can fill this later)…`} />
          <div className="flex items-center gap-2 flex-wrap">
            <select data-testid={`kr2-status-${section.section_id}`} value={status} onChange={(e) => setStatus(e.target.value)} className="text-xs border rounded-sm p-1.5">
              {STATUS_VALUES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <select value={source} onChange={(e) => setSource(e.target.value)} className="text-xs border rounded-sm p-1.5">
              {SOURCE_VALUES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <button onClick={save} disabled={busy} data-testid={`kr2-save-${section.section_id}`}
              className="text-xs inline-flex items-center gap-1 bg-navy text-white px-3 py-1.5 rounded-sm disabled:opacity-60">
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />} Save
            </button>
            <span className="text-[10px] text-muted-foreground">Verification: {section.verification_status}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function KnowledgeRecord2() {
  const [krs, setKrs] = useState(null);
  const [selId, setSelId] = useState("");
  const [kr, setKr] = useState(null);

  useEffect(() => { api.get("/knowledge-records").then((r) => { const list = Array.isArray(r.data) ? r.data : (r.data.records || []); setKrs(list); if (list[0]) setSelId(list[0].id); }).catch(() => setKrs([])); }, []);
  const load = () => selId && api.get(`/kr2/${selId}`).then((r) => setKr(r.data)).catch(() => {});
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [selId]);

  if (!krs) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div>
      <PageHeader
        overline="QRU Knowledge Record 2.0™ · Manufacturing Blueprint"
        title="Knowledge Architecture"
        description="Each Knowledge Record is a manufacturing blueprint of independent, versioned sections. Products are manufactured FROM these sections. Fill sections now or let AI fill them later — the architecture is permanent and extensible."
      />

      <div className="flex items-center gap-2 mb-5">
        <select data-testid="kr2-selector" value={selId} onChange={(e) => setSelId(e.target.value)} className="border rounded-sm p-2 text-sm min-w-[280px]">
          {krs.map((k) => <option key={k.id} value={k.id}>{k.kr_code} — {k.title}</option>)}
        </select>
      </div>

      {!kr ? <div className="flex justify-center py-16"><Loader2 className="w-5 h-5 animate-spin text-primary" /></div> : (
        <>
          <Panel testid="kr2-completeness" accent="gold" className="mb-6">
            <div className="flex items-center justify-between mb-2.5">
              <p className="font-heading font-bold text-navy flex items-center gap-2 text-lg"><FileText className="w-4 h-4 text-royal" /> {kr.kr_code} — {kr.title}</p>
              <span className="text-xs text-muted-foreground font-medium">{kr.completeness.complete}/{kr.completeness.total} sections · {kr.completeness.verified} verified</span>
            </div>
            <div className="h-2.5 rounded-full bg-muted overflow-hidden"><div className="h-full bg-gold transition-[width] duration-500 ease-out" style={{ width: `${kr.completeness.percent}%` }} /></div>
            <p className="text-[11px] text-muted-foreground mt-1.5">{kr.completeness.percent}% complete · schema v{kr.schema_version}</p>
          </Panel>

          <p className="overline text-royal mb-3 flex items-center gap-1.5"><Layers className="w-3.5 h-3.5" /> Sections ({kr.sections.length})</p>
          <div className="space-y-2" data-testid="kr2-sections">
            {kr.sections.map((s) => <SectionCard key={s.section_id} krId={kr.id} section={s} onSaved={load} />)}
          </div>
        </>
      )}
    </div>
  );
}
