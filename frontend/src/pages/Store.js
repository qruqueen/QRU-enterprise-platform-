import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Store as StoreIcon, ShoppingCart, Loader2, DollarSign, TrendingUp, Download, X, Eye, FileText } from "lucide-react";

export default function Store() {
  const [products, setProducts] = useState([]);
  const [revenue, setRevenue] = useState(null);
  const [buying, setBuying] = useState(null);
  const [loading, setLoading] = useState(true);
  const [formatsFor, setFormatsFor] = useState(null);
  const [formats, setFormats] = useState(null);
  const [loadingFormats, setLoadingFormats] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const [p, r] = await Promise.all([api.get("/commerce/storefront"), api.get("/commerce/revenue")]);
        setProducts(p.data);
        setRevenue(r.data);
      } catch (_) {} finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const buy = async (product) => {
    setBuying(product.id);
    try {
      const { data } = await api.post("/commerce/checkout", {
        product_id: product.id,
        origin_url: window.location.origin,
      });
      window.location.href = data.url;
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
      setBuying(null);
    }
  };

  const openFormats = async (product) => {
    setFormatsFor(product);
    setFormats(null);
    setLoadingFormats(true);
    try {
      const { data } = await api.post(`/rendering/${product.id}/export-formats`);
      setFormats(data.formats);
    } catch (e) {
      toast.error("Could not generate formats.");
    } finally {
      setLoadingFormats(false);
    }
  };

  if (loading)
    return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading QRU Store™…</div>;

  return (
    <div className="space-y-6" data-testid="store-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
            <StoreIcon className="w-7 h-7 text-gold" /> QRU Store™
          </h1>
          <p className="text-sm text-muted-foreground mt-1">Certified Treasure Standard™ products — secure Stripe checkout.</p>
        </div>
        {revenue && (
          <div className="flex gap-3">
            <div className="bg-card border rounded-sm px-4 py-2" data-testid="store-revenue">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground"><TrendingUp className="w-3.5 h-3.5 text-gold" /> Revenue</div>
              <p className="font-heading font-bold text-navy">${revenue.revenue_usd}</p>
            </div>
            <div className="bg-card border rounded-sm px-4 py-2">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground"><ShoppingCart className="w-3.5 h-3.5 text-gold" /> Paid Orders</div>
              <p className="font-heading font-bold text-navy">{revenue.paid_orders}</p>
            </div>
          </div>
        )}
      </div>

      {products.length === 0 && <p className="text-sm text-muted-foreground">No published products available yet.</p>}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map((p) => {
          const accent = p.design_palette?.accent || "#F5B21A";
          return (
          <div key={p.id} data-testid={`store-product-${p.product_code}`} className="bg-card border rounded-sm overflow-hidden flex flex-col group hover:shadow-lg transition-shadow" style={{ borderTop: `3px solid ${accent}` }}>
            <div className="h-52 bg-navy/90 flex items-center justify-center overflow-hidden relative">
              {p.cover_url ? (
                <img src={`${process.env.REACT_APP_BACKEND_URL}${p.cover_url}`} alt={p.title} className="h-full w-full object-contain transition-transform group-hover:scale-105" />
              ) : (
                <span className="font-heading text-gold text-lg">QRU</span>
              )}
              {p.treasure_standard && (
                <span className="absolute top-2 right-2 text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ background: accent, color: "#1A1434" }}>★ Treasure Standard™</span>
              )}
            </div>
            <div className="p-4 flex-1 flex flex-col">
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-wide text-muted-foreground">
                <span className="px-1.5 py-0.5 rounded" style={{ background: `${accent}22`, color: "#1A1434" }}>{p.product_type}</span>
                <span className="truncate">{p.family}</span>
              </div>
              <p className="text-sm font-semibold text-navy mt-1.5 line-clamp-2 flex-1">{p.title}</p>
              {p.audience && <p className="text-xs text-muted-foreground mt-1">For {p.audience}</p>}
              {(p.preview_url || p.preview_pdf_url) && (
                <div className="flex items-center gap-2 mt-2" data-testid={`store-preview-${p.product_code}`}>
                  {p.preview_url && (
                    <a href={`${process.env.REACT_APP_BACKEND_URL}/api/marketing/preview/${p.id}?fmt=html`} target="_blank" rel="noreferrer"
                      data-testid={`read-sample-${p.product_code}`}
                      className="flex items-center gap-1 text-primary text-xs font-medium hover:underline">
                      <Eye className="w-3.5 h-3.5" /> Read Sample
                    </a>
                  )}
                  {p.preview_pdf_url && (
                    <a href={`${process.env.REACT_APP_BACKEND_URL}/api/marketing/preview/${p.id}?fmt=pdf`}
                      data-testid={`preview-pdf-${p.product_code}`}
                      className="flex items-center gap-1 text-navy text-xs font-medium hover:underline">
                      <FileText className="w-3.5 h-3.5" /> Preview PDF
                    </a>
                  )}
                </div>
              )}
              <div className="flex items-center justify-between mt-3">
                <span className="font-heading text-lg font-bold text-navy flex items-center"><DollarSign className="w-4 h-4" />{p.price}</span>
                <div className="flex items-center gap-2">
                  <button
                    data-testid={`formats-btn-${p.product_code}`}
                    onClick={() => openFormats(p)}
                    className="flex items-center gap-1 text-navy border border-navy/20 px-2.5 py-1.5 rounded-sm text-xs font-semibold hover:bg-navy/5"
                    title="Download optimized formats (KDP, Etsy, TpT, social…)"
                  >
                    <Download className="w-3.5 h-3.5" /> Formats
                  </button>
                  <button
                    data-testid={`buy-btn-${p.product_code}`}
                    onClick={() => buy(p)}
                    disabled={buying === p.id}
                    className="flex items-center gap-1.5 bg-gold text-navy px-3 py-1.5 rounded-sm text-sm font-semibold hover:bg-gold/90 disabled:opacity-60"
                  >
                    {buying === p.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShoppingCart className="w-4 h-4" />} Buy
                  </button>
                </div>
              </div>
            </div>
          </div>
          );
        })}
      </div>

      {formatsFor && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setFormatsFor(null)} data-testid="formats-modal">
          <div className="bg-card rounded-sm max-w-lg w-full max-h-[80vh] overflow-y-auto p-5" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-heading font-semibold text-navy">Download Formats — {formatsFor.title}</h3>
              <button onClick={() => setFormatsFor(null)} data-testid="formats-close"><X className="w-5 h-5 text-muted-foreground" /></button>
            </div>
            <p className="text-xs text-muted-foreground mb-3">Multi-Format Output™ — marketplace & print-ready, each preserving the QRU frame.</p>
            {loadingFormats && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Generating optimized formats…</div>}
            {formats && (
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(formats).map(([key, f]) => (
                  <a
                    key={key}
                    href={`${process.env.REACT_APP_BACKEND_URL}${f.url}?download=true&name=${encodeURIComponent(`${formatsFor.title} - ${f.label}`)}`}
                    target="_blank" rel="noreferrer"
                    data-testid={`format-download-${key}`}
                    className="flex items-center gap-2 border rounded-sm p-2 hover:bg-muted transition-colors"
                  >
                    <Download className="w-4 h-4 text-gold shrink-0" />
                    <span className="text-xs">
                      <span className="block font-medium text-navy">{f.label}</span>
                      <span className="text-muted-foreground">{f.size[0]}×{f.size[1]}</span>
                    </span>
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
