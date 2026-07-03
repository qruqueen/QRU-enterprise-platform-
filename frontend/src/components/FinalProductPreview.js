import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { CheckCircle2, Eye, Download, Pencil, Rocket, Package, Loader2, ExternalLink } from "lucide-react";

// MT-021 — Final Product Preview. Auto-opens when manufacturing completes successfully so the
// Founder immediately sees the finished deliverable(s) exactly as the customer would receive it.
export function FinalProductPreview({ open, onOpenChange, pipeline, render }) {
  const navigate = useNavigate();
  const [formats, setFormats] = useState(null);
  const [busy, setBusy] = useState("");
  const [published, setPublished] = useState(pipeline?.status === "Published");

  useEffect(() => { setPublished(pipeline?.status === "Published"); }, [pipeline?.status]);
  if (!pipeline) return null;

  const cover = render?.cover_url || render?.assets?.cover;
  const deliverables = pipeline.deliverables || [];

  const download = async () => {
    setBusy("download");
    try {
      const { data } = await api.post(`/rendering/${pipeline.id}/export-formats`);
      setFormats(data.formats || data.exports || data);
      toast.success("Export formats ready");
    } catch { toast.error("Could not generate export formats"); }
    finally { setBusy(""); }
  };

  const publish = async () => {
    setBusy("publish");
    try {
      await api.patch(`/products/${pipeline.id}/status`, { status: "Published" });
      setPublished(true);
      toast.success("Published to the QRU Store™ 🚀");
    } catch (e) { toast.error(e?.response?.data?.detail || "Publish blocked — complete Creative Studio + Verification first."); }
    finally { setBusy(""); }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[88vh] overflow-y-auto" data-testid="final-product-preview">
        <DialogHeader>
          <div className="flex items-center gap-2 text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
            <span className="text-xs font-semibold tracking-widest uppercase">Manufacturing Complete · Final Product Preview</span>
          </div>
          <DialogTitle className="font-heading text-2xl text-navy">{pipeline.title}</DialogTitle>
          <p className="text-sm text-muted-foreground">{pipeline.product_type} · {pipeline.product_code} · Seen exactly as the customer receives it</p>
        </DialogHeader>

        <div className="grid sm:grid-cols-[220px_1fr] gap-5 mt-2">
          <div className="rounded-lg overflow-hidden border border-border bg-navy/5 flex items-center justify-center min-h-[240px]">
            {cover ? <img src={cover} alt={pipeline.title} className="w-full object-cover" data-testid="fpp-cover" />
              : <div className="text-center text-muted-foreground p-4"><Package className="w-10 h-10 mx-auto mb-2" /><p className="text-xs">Branded cover pending render</p></div>}
          </div>
          <div>
            <p className="text-[11px] font-semibold text-gold uppercase tracking-wide mb-2">Finished Deliverables</p>
            <div className="space-y-1.5">
              {deliverables.length ? deliverables.map((d, i) => (
                <div key={i} className="flex items-center gap-2 text-sm text-foreground/80" data-testid={`fpp-deliverable-${i}`}>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> {d.name || d}
                  <span className="text-[10px] text-muted-foreground">· {d.status || "assembled"}</span>
                </div>
              )) : <p className="text-sm text-muted-foreground">Single deliverable ready.</p>}
            </div>

            {formats && (
              <div className="mt-3">
                <p className="text-[11px] font-semibold text-gold uppercase tracking-wide mb-1">Download Formats</p>
                <div className="flex flex-wrap gap-1.5">
                  {(Array.isArray(formats) ? formats : Object.entries(formats).map(([k, v]) => ({ label: k, url: v }))).map((f, i) => (
                    <a key={i} href={f.url || f} target="_blank" rel="noreferrer" className="text-xs inline-flex items-center gap-1 px-2 py-1 rounded-sm border border-border hover:border-navy" data-testid={`fpp-format-${i}`}>
                      {f.label || f.name || `Format ${i + 1}`} <ExternalLink className="w-3 h-3" />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t">
          <button data-testid="fpp-preview" onClick={() => { onOpenChange(false); navigate(`/products/${pipeline.id}`); }}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm bg-primary text-primary-foreground hover:bg-primary/90"><Eye className="w-4 h-4" /> Preview</button>
          <button data-testid="fpp-download" onClick={download} disabled={busy === "download"}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border border-border hover:border-navy disabled:opacity-60">
            {busy === "download" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Download</button>
          <button data-testid="fpp-edit" onClick={() => { onOpenChange(false); navigate(`/products/${pipeline.id}`); }}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border border-border hover:border-navy"><Pencil className="w-4 h-4" /> Edit</button>
          <button data-testid="fpp-publish" onClick={publish} disabled={busy === "publish" || published}
            className={`inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm ${published ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-navy text-white hover:bg-navy/90"} disabled:opacity-60`}>
            {busy === "publish" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Rocket className="w-4 h-4" />} {published ? "Published" : "Approve & Publish"}</button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
