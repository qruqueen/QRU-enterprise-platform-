import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { useNavigate } from "react-router-dom";
import { Loader2, Search, Download, Headphones, ArrowRight, PackageOpen, BookText, Clapperboard, LayoutTemplate, FileText, Rocket, FileCheck2, Eye } from "lucide-react";
import { ManifestDialog } from "@/components/ManifestDialog";
import { DeliverablePreview } from "@/components/DeliverablePreview";
import { DestinationChips } from "@/components/DestinationPreview";
import { downloadDeliverable } from "@/lib/deliverable";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";
const ENGINES = [
  { key: "all", label: "Everything" },
  { key: "publication", label: "Books & Products", icon: BookText },
  { key: "media", label: "Video & Audio", icon: Clapperboard },
  { key: "poster", label: "Posters", icon: LayoutTemplate },
  { key: "recipe", label: "PDF Recipes", icon: FileText },
];

export default function ProductShelf() {
  const nav = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [engine, setEngine] = useState("all");
  const [publishing, setPublishing] = useState(null);
  const [manifestFor, setManifestFor] = useState(null);
  const [previewFor, setPreviewFor] = useState(null);
  const [dlBusy, setDlBusy] = useState(null);
  const [destMap, setDestMap] = useState([]);

  const doDownload = async (p) => {
    setDlBusy(p.id);
    try { await downloadDeliverable(p.id, "pdf"); }
    catch (e) { toast.error(e?.response?.data?.detail || "Download failed."); }
    finally { setDlBusy(null); }
  };

  const publish = async (p) => {
    setPublishing(p.id);
    try {
      await api.post(`/manufacturing/publish`, { engine: p.engine, id: p.id });
      setData((d) => ({
        ...d,
        products: d.products.map((x) =>
          x.id === p.id && x.engine === p.engine
            ? { ...x, status: "Published", tone: "green", publishable: false, badges: [...(x.badges || []).filter((b) => b !== "In QRU Store"), "In QRU Store"] }
            : x
        ),
      }));
      toast.success("Published for distribution", { description: `${p.name} is now live in the QRU Store™ with a Product Manifest™.` });
    } catch (e) {
      const msg = e?.response?.data?.detail || "Publishing is blocked — the product needs a real deliverable and to pass its review gate first.";
      toast.error("Not published", { description: msg });
    } finally {
      setPublishing(null);
    }
  };

  useEffect(() => {
    api.get("/media-studio/products-shelf")
      .then((r) => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
    api.get("/distribution-architecture/destinations-map").then((r) => setDestMap(r.data.map || [])).catch(() => {});
  }, []);

  const items = useMemo(() => {
    if (!data) return [];
    let list = data.products;
    if (engine !== "all") list = list.filter((p) => p.engine === engine);
    const s = q.trim().toLowerCase();
    if (s) list = list.filter((p) => (p.name || "").toLowerCase().includes(s) || (p.topic || "").toLowerCase().includes(s));
    return list;
  }, [data, engine, q]);

  return (
    <div data-testid="product-shelf-page">
      <PageHeader
        overline="QRU Factory™ · My Products"
        title="My Products"
        description="Every product the Factory has manufactured — books, videos, audio, posters and PDFs — in one place, with its real status and next action. Nothing gets lost between engines."
        actions={<VerifiedBadge label="One shelf · every engine" testid="shelf-badge" />}
      />

      <Panel title="Product Shelf" icon={PackageOpen} accent="gold" testid="shelf-panel">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <input data-testid="shelf-search" value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Search by product or topic…"
              className="w-full border border-navy/15 rounded-md pl-9 pr-3 py-2 text-sm focus:border-royal outline-none" />
          </div>
          <div className="flex flex-wrap gap-1.5">
            {ENGINES.map((e) => (
              <button key={e.key} onClick={() => setEngine(e.key)} data-testid={`shelf-filter-${e.key}`}
                className={`text-[11px] px-2.5 py-1.5 rounded-full border font-semibold transition-colors ${engine === e.key ? "bg-navy text-white border-navy" : "border-navy/15 text-navy hover:border-royal"}`}>
                {e.label}{data?.by_engine && e.key !== "all" ? ` · ${data.by_engine[e.key] || 0}` : ""}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="py-12 flex items-center justify-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading your products…</div>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground py-12 text-center" data-testid="shelf-empty">No products match. Manufacture one from a Knowledge Record to see it here.</p>
        ) : (
          <div className="space-y-1.5">
            {items.map((p) => (
              <div key={`${p.engine}-${p.id}`} data-testid={`shelf-item-${p.id}`}
                className="flex flex-wrap items-center gap-2 border border-navy/10 rounded-md p-2.5 hover:border-royal/40 transition-colors">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-bold text-navy truncate">{p.name || "Untitled"}</span>
                    <span className="text-[9px] uppercase tracking-wide text-muted-foreground border border-navy/10 rounded px-1.5 py-0.5 shrink-0">{p.kind}</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground">{p.topic ? `Knowledge: ${p.topic}` : "No linked Knowledge Record"}</span>
                </div>
                <StatusChip status={(p.status || "").replace(/_/g, " ")} tone={p.tone} />
                {(p.badges || []).map((b) => <span key={b} className="text-[9px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">{b}</span>)}
                <div className="flex items-center gap-2 ml-auto">
                  {p.audiobook_url && (
                    <a href={`${BACKEND}${p.audiobook_url}`} target="_blank" rel="noreferrer" data-testid={`shelf-audio-${p.id}`} className="text-[10px] text-royal inline-flex items-center gap-1 hover:underline"><Headphones className="w-3 h-3" /> Audio</a>
                  )}
                  {p.download && (p.download.includes("/api/rendering/asset/deliverable-") ? (
                    <>
                      <button onClick={() => setPreviewFor({ id: p.id, title: p.name, product_type: p.kind })} data-testid={`shelf-preview-${p.id}`}
                        className="text-[10px] text-navy inline-flex items-center gap-1 hover:text-royal font-semibold"><Eye className="w-3 h-3" /> Preview</button>
                      <button onClick={() => doDownload(p)} disabled={dlBusy === p.id} data-testid={`shelf-download-${p.id}`}
                        className="text-[10px] text-royal inline-flex items-center gap-1 hover:underline disabled:opacity-50">
                        {dlBusy === p.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />} Download</button>
                    </>
                  ) : (
                    <a href={`${BACKEND}${p.download}`} target="_blank" rel="noreferrer" data-testid={`shelf-download-${p.id}`} className="text-[10px] text-royal inline-flex items-center gap-1 hover:underline"><Download className="w-3 h-3" /> Download</a>
                  ))}
                  {p.status !== "Published" && p.publishable && (
                    <>
                      <DestinationChips productType={p.kind} destMap={destMap} />
                      <button onClick={() => publish(p)} disabled={publishing === p.id} data-testid={`shelf-publish-${p.id}`}
                        className="text-[10px] font-semibold text-white bg-royal hover:bg-navy disabled:opacity-50 rounded-full px-2.5 py-1 inline-flex items-center gap-1 transition-colors">
                        {publishing === p.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Rocket className="w-3 h-3" />} Publish for Distribution
                      </button>
                    </>
                  )}
                  {p.has_manifest && (
                    <button onClick={() => setManifestFor(p)} data-testid={`shelf-manifest-${p.id}`}
                      className="text-[10px] text-navy/70 inline-flex items-center gap-1 hover:text-royal font-semibold">
                      <FileCheck2 className="w-3 h-3" /> Manifest™
                    </button>
                  )}
                  <button onClick={() => nav(p.kr_id ? `${p.route}?kr=${p.kr_id}` : p.route)} data-testid={`shelf-open-${p.id}`} className="text-[10px] text-navy inline-flex items-center gap-0.5 hover:text-royal font-semibold">Open <ArrowRight className="w-3 h-3" /></button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
      {manifestFor && (
        <ManifestDialog engine={manifestFor.engine} productId={manifestFor.id} name={manifestFor.name}
          open={!!manifestFor} onOpenChange={(o) => !o && setManifestFor(null)} />
      )}
      <DeliverablePreview open={!!previewFor} product={previewFor} onOpenChange={(o) => !o && setPreviewFor(null)} />
    </div>
  );
}
