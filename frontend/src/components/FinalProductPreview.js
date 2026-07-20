import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DeliverablePreview } from "@/components/DeliverablePreview";
import { downloadDeliverable } from "@/lib/deliverable";
import { CheckCircle2, Eye, Download, Rocket, Package, Loader2, ExternalLink, FileText, BookOpen, Presentation, Image as ImageIcon, FileType2 } from "lucide-react";

const FMT_ICON = { pdf: FileText, epub: BookOpen, pptx: Presentation, png: ImageIcon, html: FileType2 };

// MT-021 + MT-024 — Final Product Preview. Auto-opens when manufacturing completes so the
// Founder can OPEN, READ, SCROLL, DOWNLOAD and REVIEW the exact customer-ready deliverable
// before approving publication.
export function FinalProductPreview({ open, onOpenChange, pipeline, render }) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState("");
  const [published, setPublished] = useState(pipeline?.status === "Published");
  const [showReader, setShowReader] = useState(false);
  const [dlFmt, setDlFmt] = useState(null);
  const BACKEND = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => { setPublished(pipeline?.status === "Published"); }, [pipeline?.status]);
  if (!pipeline) return null;

  const abs = (u) => (u ? (u.startsWith("http") ? u : `${BACKEND}${u}`) : null);
  const deliverable = pipeline.customer_deliverable || null;
  const files = deliverable?.files || [];
  const hasPreviewable = files.length > 0;
  const coverRel = render?.rendered_assets?.cover || render?.cover_url || pipeline.cover_url;
  const cover = abs(coverRel);
  const ready = pipeline.deliverable_ready || deliverable?.ready;
  const dz = deliverable?.design_review;
  const designApproved = deliverable?.design_approved ?? !pipeline.design_review_required;
  const contentReviewRequired = deliverable?.customer_content_review_required ?? pipeline.customer_content_review_required;
  const removedSections = deliverable?.removed_internal_sections || pipeline.removed_internal_sections || [];
  const canPublish = ready && designApproved && !contentReviewRequired;
  const doDl = async (fmt) => {
    setDlFmt(fmt);
    try { await downloadDeliverable(pipeline.id, fmt); }
    catch (e) { toast.error(e?.response?.data?.detail || "Download failed."); }
    finally { setDlFmt(null); }
  };

  const publish = async () => {
    setBusy("publish");
    try {
      await api.post(`/manufacturing2/${pipeline.id}/release`);
      setPublished(true);
      toast.success("Approved & published to the QRU Store™ 🚀");
    } catch (e) { toast.error(e?.response?.data?.detail || "Publish blocked — complete Quality Control + design review first."); }
    finally { setBusy(""); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="final-product-preview">
        <DialogHeader>
          <div className="flex items-center gap-2 text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
            <span className="text-xs font-semibold tracking-widest uppercase">Manufacturing Complete · Final Product Preview</span>
          </div>
          <DialogTitle className="font-heading text-2xl text-navy">{pipeline.title}</DialogTitle>
          <p className="text-sm text-muted-foreground">{pipeline.product_type} · {pipeline.product_code} · Inspect the finished product exactly as the customer receives it</p>
        </DialogHeader>

        <div className="grid sm:grid-cols-[200px_1fr] gap-5 mt-2">
          <div className="rounded-lg overflow-hidden border border-border bg-navy/5 flex items-center justify-center min-h-[240px]">
            {cover ? <img src={cover} alt={pipeline.title} className="w-full object-cover" data-testid="fpp-cover" />
              : <div className="text-center text-muted-foreground p-4"><Package className="w-10 h-10 mx-auto mb-2" /><p className="text-xs">Branded cover pending render</p></div>}
          </div>
          <div>
            <p className="text-[11px] font-semibold text-gold uppercase tracking-wide mb-2">Customer-Ready Deliverables</p>
            {files.length ? (
              <div className="space-y-1.5 mb-3" data-testid="fpp-deliverable-files">
                {files.map((f, i) => {
                  const Icon = FMT_ICON[f.format] || FileText;
                  return (
                    <button key={i} onClick={() => doDl(f.format)} disabled={dlFmt === f.format}
                      className="w-full flex items-center gap-2 text-sm text-foreground/80 px-2.5 py-1.5 rounded-md border border-border hover:border-navy hover:bg-navy/[0.03] transition-colors disabled:opacity-50 text-left"
                      data-testid={`fpp-file-${f.format}`}>
                      <Icon className="w-4 h-4 text-navy shrink-0" />
                      <span className="flex-1">{f.label}</span>
                      <span className="text-[10px] text-muted-foreground">{Math.max(1, Math.round((f.bytes || 0) / 1024))} KB</span>
                      {dlFmt === f.format ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5 text-muted-foreground" />}
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground mb-3">Deliverable rendering pending — it will appear here automatically once manufacturing finishes.</p>
            )}
            <div className={`inline-flex items-center gap-1.5 text-xs px-2 py-1 rounded-full ${designApproved ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`} data-testid="fpp-validation">
              <CheckCircle2 className="w-3.5 h-3.5" /> {designApproved ? `Treasure Standard™ Approved${dz?.grade != null ? ` · ${dz.grade}/100` : ""}` : `Rendered — Design Review Required${dz?.grade != null ? ` · ${dz.grade}/100` : ""}`}
            </div>
            {!designApproved && dz?.recommendations?.length > 0 && (
              <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md p-2.5 mt-2" data-testid="fpp-design-recs">
                Design review needed: {dz.recommendations.join(", ")}.
              </div>
            )}
            {contentReviewRequired && (
              <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-md p-2.5 mt-2" data-testid="fpp-content-review">
                <b>Customer Content Review Required.</b> Internal production notes were detected in the deliverable{deliverable?.leftover_internal_notes?.length ? `: ${deliverable.leftover_internal_notes.join(", ")}` : ""}. Return to Creative Studio™, remove them, then re-render before publishing.
              </div>
            )}
            {removedSections.length > 0 && (
              <p className="text-[11px] text-muted-foreground mt-2" data-testid="fpp-removed-sections">
                Customer-facing filter applied — {removedSections.length} internal section{removedSections.length > 1 ? "s" : ""} excluded from the customer edition ({removedSections.join(", ")}).
              </p>
            )}
          </div>
        </div>

        {hasPreviewable && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-[11px] font-semibold text-gold uppercase tracking-wide">Founder Inspection · Read the finished product</p>
              <button data-testid="fpp-toggle-reader" onClick={() => setShowReader(true)} className="text-xs inline-flex items-center gap-1 text-primary">
                <Eye className="w-3.5 h-3.5" /> Open preview
              </button>
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t">
          <button data-testid="fpp-preview" onClick={() => { onOpenChange(false); navigate(`/products/${pipeline.id}`); }}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border border-border hover:border-navy"><Eye className="w-4 h-4" /> Product Page</button>
          {deliverable?.primary_format && (
            <button data-testid="fpp-download" onClick={() => doDl(deliverable.primary_format)} disabled={dlFmt === deliverable.primary_format}
              className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border border-border hover:border-navy disabled:opacity-50">
              {dlFmt === deliverable.primary_format ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Download {deliverable.primary_format?.toUpperCase()}</button>
          )}
          <button data-testid="fpp-publish" onClick={publish} disabled={busy === "publish" || published || !canPublish}
            className={`inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm ml-auto ${published ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-navy text-white hover:bg-navy/90"} disabled:opacity-50`}>
            {busy === "publish" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Rocket className="w-4 h-4" />} {published ? "Published" : "Approve & Publish"}</button>
        </div>
      </DialogContent>
      <DeliverablePreview open={showReader}
        product={{ id: pipeline.id, title: pipeline.title, product_type: pipeline.product_type, customer_deliverable: deliverable }}
        onOpenChange={setShowReader} />
    </Dialog>
  );
}
