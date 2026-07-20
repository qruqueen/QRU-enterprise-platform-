import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { mintFileToken, downloadDeliverable } from "@/lib/deliverable";
import { Loader2, Download, ExternalLink, FileText, Info } from "lucide-react";

const RENDERABLE = ["pdf", "png", "jpg", "jpeg", "html", "mp3", "mp4"];
const NON_NATIVE = ["epub", "pptx", "docx"]; // shown via generated PDF representation

// In-Factory deliverable PREVIEW (never downloads). PDF/image/audio/video render inline;
// EPUB/PPTX/DOCX show the generated PDF representation with a separate "Download original".
export function DeliverablePreview({ open, onOpenChange, product }) {
  const files = (product?.customer_deliverable?.files) || product?.files || [];
  const previewableFormats = files.map((f) => f.format).filter((f) => RENDERABLE.includes(f) || NON_NATIVE.includes(f));
  const [fmt, setFmt] = useState(null);
  const [tok, setTok] = useState(null);
  const [loading, setLoading] = useState(false);
  const [busyDl, setBusyDl] = useState(false);

  const defaultFmt = previewableFormats.includes("pdf") ? "pdf" : (previewableFormats[0] || "pdf");

  const load = useCallback(async (f) => {
    if (!product?.id) return;
    setLoading(true); setTok(null);
    try {
      const t = await mintFileToken(product.id, f, "preview");
      setTok(t);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not open preview.");
    } finally { setLoading(false); }
  }, [product?.id]);

  useEffect(() => {
    if (open) { setFmt(defaultFmt); load(defaultFmt); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, product?.id]);

  const pickFormat = (f) => { setFmt(f); load(f); };

  const download = async (f) => {
    setBusyDl(true);
    try { await downloadDeliverable(product.id, f); }
    catch (e) { toast.error(e?.response?.data?.detail || "Download failed."); }
    finally { setBusyDl(false); }
  };

  const isRep = tok?.is_representation || (NON_NATIVE.includes(fmt) && tok?.format === "pdf");
  const media = tok?.media_type || "";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[92vh] overflow-hidden flex flex-col" data-testid="deliverable-preview">
        <DialogHeader>
          <DialogTitle className="font-heading text-xl text-navy truncate">{product?.title || "Preview"}</DialogTitle>
          <p className="text-xs text-muted-foreground">{product?.product_type} · Preview only — this never downloads or regenerates the product.</p>
        </DialogHeader>

        {previewableFormats.length > 1 && (
          <div className="flex flex-wrap gap-1.5" data-testid="preview-format-tabs">
            {previewableFormats.map((f) => (
              <button key={f} onClick={() => pickFormat(f)} data-testid={`preview-tab-${f}`}
                className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border ${fmt === f ? "bg-navy text-white border-navy" : "border-border text-navy hover:border-navy"}`}>
                {f.toUpperCase()}
              </button>
            ))}
          </div>
        )}

        {isRep && (
          <div className="flex items-start gap-2 text-[12px] bg-amber-50 border border-amber-200 text-amber-800 rounded-md px-3 py-2" data-testid="preview-representation-note">
            <Info className="w-4 h-4 mt-0.5 shrink-0" />
            <span>Showing the generated <b>PDF representation</b> of the {fmt?.toUpperCase()} (browsers can't render {fmt?.toUpperCase()} reliably). Use “Download original” for the real {fmt?.toUpperCase()} file.</span>
          </div>
        )}

        <div className="flex-1 min-h-[420px] rounded-lg border border-border bg-navy/[0.03] overflow-hidden flex items-center justify-center" data-testid="preview-stage">
          {loading ? (
            <div className="text-center text-muted-foreground"><Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" /><p className="text-xs">Opening secure preview…</p></div>
          ) : !tok ? (
            <div className="text-center text-muted-foreground"><FileText className="w-10 h-10 mx-auto mb-2" /><p className="text-xs">No previewable file.</p></div>
          ) : media.startsWith("image/") ? (
            <img src={tok.absUrl} alt={product?.title} className="max-h-[70vh] w-auto object-contain" data-testid="preview-image" />
          ) : media.startsWith("audio/") ? (
            <audio src={tok.absUrl} controls className="w-4/5" data-testid="preview-audio" />
          ) : media.startsWith("video/") ? (
            <video src={tok.absUrl} controls className="max-h-[70vh] w-auto" data-testid="preview-video" />
          ) : (
            <iframe title="deliverable-preview" src={tok.absUrl} className="w-full h-[70vh] bg-white" data-testid="preview-frame" />
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 pt-3 border-t">
          {tok && (
            <a href={tok.absUrl} target="_blank" rel="noreferrer" data-testid="preview-open-newtab"
              className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border border-border hover:border-navy">
              <ExternalLink className="w-4 h-4" /> Open in new tab
            </a>
          )}
          <button onClick={() => download(isRep ? fmt : (fmt || "pdf"))} disabled={busyDl} data-testid="preview-download-original"
            className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm bg-navy text-white hover:bg-navy/90 disabled:opacity-50 ml-auto">
            {busyDl ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Download {isRep ? `original ${fmt?.toUpperCase()}` : (fmt ? fmt.toUpperCase() : "file")}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
