import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, FileCheck2, ShieldCheck, BookOpen, Boxes, Truck, Landmark, Network } from "lucide-react";

const Row = ({ label, value }) =>
  value === undefined || value === null || value === "" ? null : (
    <div className="flex gap-3 py-1 text-[12px]">
      <span className="text-navy/50 w-40 shrink-0">{label}</span>
      <span className="text-navy font-medium break-words">{String(value)}</span>
    </div>
  );

const Section = ({ icon: Icon, title, children }) => (
  <div className="border border-navy/10 rounded-lg p-3">
    <p className="flex items-center gap-2 text-[11px] font-bold text-royal uppercase tracking-wide mb-1.5">
      <Icon className="w-3.5 h-3.5" /> {title}
    </p>
    {children}
  </div>
);

// Reusable Product Manifest™ (PMF™ = EVIDENCE) viewer. Fetches on open.
export function ManifestDialog({ engine, productId, bookId, name, open, onOpenChange }) {
  const [pmf, setPmf] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const load = async () => {
    setLoading(true); setErr(null); setPmf(null);
    try {
      const url = bookId ? `/book-mfg/books/${bookId}/manifest` : `/manufacturing/manifest/${engine}/${productId}`;
      const { data } = await api.get(url);
      if (data?.not_generated) setErr(data.note || "No manufacturing evidence yet.");
      else setPmf(data);
    } catch (e) {
      setErr(e?.response?.data?.detail || "Could not load the manifest.");
    } finally { setLoading(false); }
  };

  useEffect(() => {
    if (open) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, engine, productId, bookId]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="manifest-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-navy">
            <FileCheck2 className="w-5 h-5 text-royal" /> Product Manifest™ <span className="text-[11px] font-normal text-navy/50">· Evidence of exactly what happened during manufacturing</span>
          </DialogTitle>
        </DialogHeader>
        {loading && <div className="py-10 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>}
        {err && <p className="text-[13px] text-navy/60 py-6" data-testid="manifest-empty">{err}</p>}
        {pmf && !err && (
          <div className="space-y-2.5" data-testid="manifest-body">
            <div className="text-[11px] text-navy/50">{pmf.manifest_id}</div>
            <Section icon={BookOpen} title="Source Intelligence (UKR™ = Truth)">
              <Row label="Knowledge Record ID" value={pmf.source_intelligence?.ukr_id || "— (manuscript-originated)"} />
              <Row label="Knowledge Title" value={pmf.source_intelligence?.knowledge_title} />
              <Row label="Published Title" value={pmf.source_intelligence?.published_title} />
              <Row label="UKR™ version" value={pmf.source_intelligence?.ukr_version} />
              <Row label="Standard version" value={pmf.source_intelligence?.manufacturing_standard_version} />
            </Section>
            <Section icon={ShieldCheck} title="Inherited Standards">
              <div className="flex flex-wrap gap-1.5">
                {(pmf.inherited_standards || []).map((s) => (
                  <span key={s.id} className="text-[10px] bg-royal/10 text-royal rounded-full px-2 py-0.5" title={`${s.owns}`}>
                    {s.name}{s.version_used ? ` · ${s.version_used}` : ""}
                  </span>
                ))}
              </div>
            </Section>
            <Section icon={Boxes} title="Assets & Production">
              {Object.entries(pmf.assets_used || {}).map(([k, v]) => <Row key={k} label={k.replace(/_/g, " ")} value={typeof v === "boolean" ? (v ? "yes" : "no") : v} />)}
              <Row label="files produced" value={(pmf.production_results?.files_produced || []).length} />
              <Row label="export formats" value={(pmf.production_results?.export_formats || []).join(", ")} />
            </Section>
            <Section icon={ShieldCheck} title="Quality (Treasure Standard™)">
              <Row label="validation" value={pmf.quality_results?.validation_status} />
              <Row label="verification" value={pmf.quality_results?.verification_status} />
              <Row label="treasure standard" value={pmf.quality_results?.treasure_standard} />
            </Section>
            <Section icon={Truck} title="Distribution">
              <Row label="status" value={pmf.distribution?.product_status} />
              <Row label="launch" value={pmf.distribution?.launch_status} />
              <Row label="channels" value={(pmf.distribution?.channels || pmf.distribution?.publishing_targets || []).join(", ")} />
            </Section>
            <Section icon={Landmark} title="Governance">
              <Row label="manufacturing engine" value={pmf.governance?.manufacturing_engine} />
              <Row label="responsible standard" value={pmf.governance?.responsible_standard} />
            </Section>
            <Section icon={Network} title="Enterprise Memory™">
              <Row label="source record" value={pmf.enterprise_memory?.source_record} />
              <Row label="related products" value={(pmf.enterprise_memory?.related_products || []).length} />
            </Section>
            <p className="text-[10px] text-navy/40 pt-1">The manifest references the UKR™ — it never duplicates the knowledge. Truth → Manufacturing → Evidence.</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
