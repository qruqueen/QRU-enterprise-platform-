import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Store as StoreIcon, ShoppingCart, Loader2, DollarSign, TrendingUp } from "lucide-react";

export default function Store() {
  const [products, setProducts] = useState([]);
  const [revenue, setRevenue] = useState(null);
  const [buying, setBuying] = useState(null);
  const [loading, setLoading] = useState(true);

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
              <div className="flex items-center justify-between mt-3">
                <span className="font-heading text-lg font-bold text-navy flex items-center"><DollarSign className="w-4 h-4" />{p.price}</span>
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
          );
        })}
      </div>
    </div>
  );
}
