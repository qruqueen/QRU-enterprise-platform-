import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "@/lib/api";
import { StatusBadge, Markdown } from "@/components/shared";
import { normalizeProduct } from "@/lib/safeRender";
import { toast } from "sonner";
import { ArrowLeft, Loader2, CheckCircle2, Send, Archive, Wand2, Sparkles, FileText, BookOpen, Presentation, Image as ImageIcon, FileType2, Download, Eye, PackageCheck, Megaphone } from "lucide-react";

const FMT_ICON = { pdf: FileText, epub: BookOpen, pptx: Presentation, png: ImageIcon, html: FileType2 };

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [p, setP] = useState(null);
  const [briefBusy, setBriefBusy] = useState(false);
  const [renderBusy, setRenderBusy] = useState(false);
  const [kit, setKit] = useState(null);
  const [kitBusy, setKitBusy] = useState(false);
  const BACKEND = process.env.REACT_APP_BACKEND_URL;
  const abs = (u) => (u ? (u.startsWith("http") ? u : `${BACKEND}${u}`) : null);
  const load = () => api.get(`/products/${id}`).then((r) => setP(normalizeProduct(r.data))).catch(() => {});
  const loadKit = () => api.get(`/marketing/${id}`).then((r) => setKit(r.data)).catch(() => {});
  useEffect(() => { load(); loadKit(); }, [id]);

  const buildKit = async () => {
    setKitBusy(true);
    try {
      await api.post(`/marketing/${id}/build`);
      toast.success("Preview & Marketing Kit™ manufactured");
      loadKit();
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not build the marketing kit"); }
    finally { setKitBusy(false); }
  };

  const setStatus = async (status) => {
    try {
      await api.patch(`/products/${id}/status`, { status });
      toast.success(`Product ${status}`);
      load();
    } catch (e) { toast.error(e.response?.data?.detail || "Failed"); }
  };

  const renderReviewCopy = async () => {
    setRenderBusy(true);
    try {
      await api.post(`/manufacturing2/${id}/render-deliverable`);
      toast.success("Founder Review Copy™ rendered");
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not render the review copy"); }
    finally { setRenderBusy(false); }
  };

  const enhance = async () => {
    setBriefBusy(true);
    try {
      const { data } = await api.post(`/products/${id}/creative-brief`);
      if (data?.enhancement_stage_note) toast.warning(data.enhancement_stage_note);
      else toast.success("Creative Studio enhanced this product page");
      load();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      toast.error(detail ? `Creative Studio stage failed: ${detail}` : "Creative Studio enhancement could not complete — please retry.");
    } finally { setBriefBusy(false); }
  };

  if (!p) return <div className="flex items-center justify-center py-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  const b = p.creative_brief;

  return (
    <div className="animate-fade-up">
      <button onClick={() => navigate("/products")} data-testid="pd-back" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="w-4 h-4" /> Product Library
      </button>

      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-xs text-muted-foreground">{p.product_code}</span>
            <span className="text-xs text-primary font-medium">{p.product_type}</span>
            <StatusBadge status={p.status} testid="pd-status" />
          </div>
          <h1 className="font-heading text-3xl font-bold tracking-tight max-w-3xl">{p.title}</h1>
          <p className="text-muted-foreground mt-2">{p.family} · {p.audience} · {p.learning_level}</p>
        </div>
        <div className="flex flex-wrap gap-2 shrink-0">
          <button data-testid="pd-creative-btn" onClick={enhance} disabled={briefBusy} className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors disabled:opacity-60">
            {briefBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} Creative Studio
          </button>
          <button data-testid="pd-review-btn" onClick={() => setStatus("In Review")} className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-warning hover:text-warning transition-colors">
            <Send className="w-4 h-4" /> Submit for Review
          </button>
          <button data-testid="pd-publish-btn" onClick={() => setStatus("Published")} className="flex items-center gap-2 bg-primary text-primary-foreground px-3 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
            <CheckCircle2 className="w-4 h-4" /> Approve & Publish
          </button>
          <button data-testid="pd-archive-btn" onClick={() => setStatus("Archived")} className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-destructive hover:text-destructive transition-colors">
            <Archive className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Founder Review Copy™ — MT-024/025: inspect the exact customer-ready deliverable before publishing */}
      {(() => {
        const cd = p.customer_deliverable;
        const dz = cd?.design_review;
        const designApproved = cd?.design_approved ?? !p.design_review_required;
        const contentReviewRequired = cd?.customer_content_review_required ?? p.customer_content_review_required;
        const removedSections = cd?.removed_internal_sections || p.removed_internal_sections || [];
        const dlHref = (f) => `${abs(f.url)}?download=1&name=${encodeURIComponent(p.title + " — " + p.product_type)}`;
        return (
          <div className="bg-card border rounded-md p-6 mb-6 max-w-4xl" data-testid="pd-review-copy">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <PackageCheck className="w-4 h-4 text-gold" />
              <h3 className="font-heading font-semibold">Founder Review Copy™</h3>
              {cd?.files?.length ? (
                designApproved ? (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200" data-testid="pd-design-approved">Treasure Standard™ Approved{dz?.grade != null ? ` · ${dz.grade}/100` : ""}</span>
                ) : (
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200" data-testid="pd-design-review-required">Rendered — Design Review Required{dz?.grade != null ? ` · ${dz.grade}/100` : ""}</span>
                )
              ) : null}
            </div>
            <p className="text-sm text-muted-foreground mb-4">Review the exact file your customers will receive before you approve &amp; publish.</p>
            {cd?.files?.length ? (
              <>
                <div className="grid sm:grid-cols-2 gap-2 mb-3">
                  {cd.files.map((f, i) => {
                    const Icon = FMT_ICON[f.format] || FileText;
                    return (
                      <a key={i} href={dlHref(f)} className="flex items-center gap-2 text-sm px-3 py-2 rounded-md border hover:border-primary hover:bg-primary/[0.03] transition-colors"
                        data-testid={`pd-download-${f.format}`}>
                        <Icon className="w-4 h-4 text-primary shrink-0" />
                        <span className="flex-1">{f.label}</span>
                        <span className="text-[10px] text-muted-foreground">{Math.max(1, Math.round((f.bytes || 0) / 1024))} KB</span>
                        <Download className="w-3.5 h-3.5 text-muted-foreground" />
                      </a>
                    );
                  })}
                </div>
                {!designApproved && dz?.recommendations?.length > 0 && (
                  <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md p-3 mb-3" data-testid="pd-design-recs">
                    <p className="font-semibold mb-1">Design review needed before publication:</p>
                    <ul className="list-disc pl-4">{dz.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul>
                  </div>
                )}
                {contentReviewRequired && (
                  <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-md p-3 mb-3" data-testid="pd-content-review">
                    <p className="font-semibold mb-1">Customer Content Review Required</p>
                    <p>Internal production notes remain in the deliverable{cd?.leftover_internal_notes?.length ? `: ${cd.leftover_internal_notes.join(", ")}` : ""}. Return to Creative Studio™, remove them, then re-render before publishing.</p>
                  </div>
                )}
                {removedSections.length > 0 && (
                  <p className="text-[11px] text-muted-foreground mb-3" data-testid="pd-removed-sections">
                    Customer-facing filter applied — {removedSections.length} internal section{removedSections.length > 1 ? "s" : ""} excluded from the customer edition ({removedSections.join(", ")}).
                  </p>
                )}
                <div className="flex flex-wrap gap-2">
                  {cd.preview_url && (
                    <a data-testid="pd-open-reader" href={abs(cd.preview_url)} target="_blank" rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border hover:border-primary"><Eye className="w-4 h-4" /> Open Review Copy (read &amp; scroll)</a>
                  )}
                  {(!designApproved || contentReviewRequired) && (
                    <button data-testid="pd-return-creative" onClick={enhance} disabled={briefBusy}
                      className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border border-warning text-warning hover:bg-warning/5 disabled:opacity-60">
                      {briefBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} Return to Creative Studio™</button>
                  )}
                  <button data-testid="pd-rerender" onClick={renderReviewCopy} disabled={renderBusy}
                    className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border hover:border-primary disabled:opacity-60">
                    {renderBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} Re-render</button>
                </div>
              </>
            ) : (
              <button data-testid="pd-render-review" onClick={renderReviewCopy} disabled={renderBusy}
                className="inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm text-sm font-medium hover:bg-navy/90 disabled:opacity-60">
                {renderBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <PackageCheck className="w-4 h-4" />} Render Founder Review Copy™
              </button>
            )}
          </div>
        );
      })()}

      {/* MT-033 — Preview & Marketing Kit™: One Run → Many Deliverables */}
      {(() => {
        const mk = kit?.marketing_kit;
        const dl2 = (u, nm) => `${abs(u)}?download=1&name=${encodeURIComponent(nm)}`;
        return (
          <div className="bg-card border rounded-md p-6 mb-6 max-w-4xl" data-testid="pd-marketing-kit">
            <div className="flex items-center justify-between gap-2 mb-1 flex-wrap">
              <div className="flex items-center gap-2">
                <Megaphone className="w-4 h-4 text-gold" />
                <h3 className="font-heading font-semibold">Preview &amp; Marketing Kit™</h3>
                {mk && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">Manufactured</span>}
              </div>
              <button data-testid="pd-build-kit" onClick={buildKit} disabled={kitBusy}
                className="flex items-center gap-2 border px-3 py-2 rounded-sm text-sm font-medium hover:border-primary hover:text-primary transition-colors disabled:opacity-60">
                {kitBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} {mk ? "Re-manufacture Kit" : "Manufacture Marketing Kit™"}
              </button>
            </div>
            <p className="text-sm text-muted-foreground mb-4">One manufacturing run produces the complete ecosystem — customer, preview, store, and social deliverables.</p>
            {!mk ? (
              <p className="text-sm text-muted-foreground italic">No marketing kit yet. Click “Manufacture Marketing Kit™”. It’s also produced automatically when a product’s deliverable is rendered.</p>
            ) : (
              <div className="space-y-4">
                {/* Editions */}
                <div className="grid sm:grid-cols-3 gap-2">
                  <div className="border rounded-md p-3" data-testid="pd-edition-founder">
                    <p className="text-xs font-semibold text-royal">Founder Master Edition™</p>
                    <p className="text-[11px] text-muted-foreground">{mk.founder_master_edition?.content_chars} chars · editable master</p>
                  </div>
                  <div className="border rounded-md p-3" data-testid="pd-edition-customer">
                    <p className="text-xs font-semibold text-royal">Customer Edition™</p>
                    <p className="text-[11px] text-muted-foreground">{(mk.customer_edition?.files || []).length} file(s) · clean product</p>
                  </div>
                  <div className="border rounded-md p-3" data-testid="pd-edition-preview">
                    <p className="text-xs font-semibold text-royal">Preview Edition™</p>
                    <p className="text-[11px] text-muted-foreground">{mk.preview_edition?.sections_included} shown · {mk.preview_edition?.sections_locked} locked</p>
                  </div>
                </div>
                {/* Preview download */}
                <div className="flex flex-wrap gap-2">
                  {(mk.preview_edition?.files || []).map((f, i) => (
                    f.format === "html" ? (
                      <a key={i} data-testid="pd-preview-read" href={abs(f.url)} target="_blank" rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border hover:border-primary"><Eye className="w-4 h-4" /> {f.label}</a>
                    ) : (
                      <a key={i} data-testid="pd-preview-download" href={dl2(f.url, p.title + " — Preview")}
                        className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border hover:border-primary"><Download className="w-4 h-4" /> {f.label}</a>
                    )
                  ))}
                </div>
                {/* Store images */}
                <div>
                  <p className="overline text-primary mb-2">Store Preview Images™</p>
                  <div className="flex gap-2 flex-wrap" data-testid="pd-store-images">
                    {(mk.store_images || []).map((s, i) => (
                      <a key={i} href={abs(s.url)} target="_blank" rel="noreferrer" title={s.label}
                        className="w-20 h-24 rounded border overflow-hidden hover:ring-2 hover:ring-primary">
                        <img src={abs(s.url)} alt={s.label} className="w-full h-full object-cover" />
                      </a>
                    ))}
                  </div>
                </div>
                {/* Social kit */}
                <div>
                  <p className="overline text-primary mb-2">Social Media Kit™</p>
                  <div className="flex gap-2 flex-wrap" data-testid="pd-social-kit">
                    {(mk.social_kit || []).map((s, i) => (
                      <a key={i} href={abs(s.url)} target="_blank" rel="noreferrer" title={s.label}
                        className="flex flex-col items-center gap-1 w-24">
                        <div className="w-24 h-24 rounded border overflow-hidden hover:ring-2 hover:ring-primary">
                          <img src={abs(s.url)} alt={s.platform} className="w-full h-full object-cover" />
                        </div>
                        <span className="text-[10px] text-muted-foreground">{s.platform}</span>
                      </a>
                    ))}
                  </div>
                </div>
                {/* Flyer + graphics */}
                <div className="flex gap-2 flex-wrap items-center">
                  {mk.product_flyer?.url && (
                    <a data-testid="pd-flyer" href={abs(mk.product_flyer.url)} target="_blank" rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border hover:border-primary"><ImageIcon className="w-4 h-4" /> Product Flyer™</a>
                  )}
                  {(mk.marketing_graphics || []).map((g, i) => (
                    <a key={i} href={abs(g.url)} target="_blank" rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-sm border hover:border-primary"><ImageIcon className="w-4 h-4" /> {g.label}</a>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })()}

        <div className="bg-card border rounded-md p-6 mb-6 max-w-4xl" data-testid="pd-creative-brief">
          <div className="flex flex-wrap items-center gap-2 mb-4"><Sparkles className="w-4 h-4 text-gold" /><h3 className="font-heading font-semibold">Product Page · by Creative Studio™</h3>
            {p.creative_brief_source === "deterministic" && (
              <span data-testid="pd-brief-source" className="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">On-brand fallback · AI Brief Writer™ unavailable</span>
            )}
            {p.creative_brief_source === "ai" && (
              <span data-testid="pd-brief-source" className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">AI-enhanced</span>
            )}
          </div>
          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div><p className="overline text-primary mb-1">Who this is for</p><p>{b.who_for}</p></div>
            <div><p className="overline text-primary mb-1">Problem it solves</p><p>{b.problem_solved}</p></div>
            <div className="sm:col-span-2"><p className="overline text-primary mb-1">What you'll understand</p><p>{b.will_understand}</p></div>
            <div><p className="overline text-primary mb-1">Skills gained</p><ul className="list-disc pl-4 text-muted-foreground">{(b.skills_gained || []).map((s, i) => <li key={i}>{s}</li>)}</ul></div>
            <div><p className="overline text-primary mb-1">What's included</p><ul className="list-disc pl-4 text-muted-foreground">{(b.whats_included || []).map((s, i) => <li key={i}>{s}</li>)}</ul></div>
            <div className="flex gap-6">
              <div><p className="overline text-primary mb-1">Reading level</p><p>{b.reading_level}</p></div>
              <div><p className="overline text-primary mb-1">Est. time</p><p>{b.completion_time}</p></div>
            </div>
            <div><p className="overline text-primary mb-1">Next learning path</p><p>{b.next_path}</p></div>
          </div>
          {p.related_products?.length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <p className="overline text-primary mb-2">Related QRU products</p>
              <div className="flex flex-wrap gap-2">
                {p.related_products.map((r) => (
                  <Link key={r.id} to={`/products/${r.id}`} className="text-xs border rounded-sm px-2 py-1 hover:border-primary">{r.product_type}: {r.title}</Link>
                ))}
              </div>
            </div>
          )}
        </div>

      <div className="bg-card border rounded-md p-8 max-w-4xl">
        <Markdown text={p.content} />
      </div>
    </div>
  );
}
