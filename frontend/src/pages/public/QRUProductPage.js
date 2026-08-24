import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Download, Loader2, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { publicApi, assetUrl } from "./publicApi";
import Seo from "./Seo";
import FounderStorefrontControls from "@/components/FounderStorefrontControls";
import CollectionTeaser from "./CollectionTeaser";

function Meta({ label, value }) {
  if (!value) return null;
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-[0.2em] text-[#575754]">{label}</dt>
      <dd className="qru-serif text-lg text-[#1C1C1A] mt-0.5">{value}</dd>
    </div>
  );
}

export default function QRUProductPage() {
  const { slug } = useParams();
  const [product, setProduct] = useState(null);
  const [purchase, setPurchase] = useState(null);
  const [error, setError] = useState(false);
  const [buying, setBuying] = useState(false);

  const load = useCallback(() => {
    setProduct(null);
    setPurchase(null);
    setError(false);
    const token = localStorage.getItem("qru_token");
    publicApi.get(`/products/${slug}`, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined)
      .then(async (r) => {
        const item = r.data;
        setProduct(item);
        try {
          const ready = await publicApi.get(`/product-purchase-readiness/${item.id}`);
          setPurchase(ready.data);
        } catch {
          setPurchase({ purchasable: false, price: null, currency: "USD", purchase_format: null });
        }
      }).catch(() => setError(true));
  }, [slug]);

  useEffect(() => { load(); }, [load]);

  const buy = async () => {
    if (!product || !purchase?.purchasable) return;
    setBuying(true);
    try {
      const { data } = await publicApi.post("/product-checkout", {
        product_id: product.id,
        origin_url: window.location.origin,
      });
      window.location.href = data.checkout_url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start checkout. Please try again.");
      setBuying(false);
    }
  };

  if (error) return (
    <div className="min-h-[60vh] grid place-items-center text-center px-6" data-testid="product-not-found">
      <div>
        <p className="qru-serif text-3xl">This product is not available.</p>
        <Link to="/catalog" className="inline-flex items-center gap-2 mt-6 text-sm text-[#C5A059]"><ArrowLeft className="w-4 h-4" /> Back to Explore All</Link>
      </div>
    </div>
  );

  if (!product) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;

  const coverAbs = product.cover_url ? assetUrl(product.cover_url) : null;
  const price = purchase?.price != null ? `$${Number(purchase.price).toFixed(2)}` : null;
  const purchaseFormat = (purchase?.purchase_format || product.format || "digital").toUpperCase();

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-12 md:py-20" data-testid="qru-product-page">
      <Seo
        title={`${product.title} · QRU Press™`}
        description={product.description || `${product.title} — published by QRU Press™.`}
        image={coverAbs}
      />
      <Link to="/catalog" data-testid="product-back" className="inline-flex items-center gap-2 text-sm text-[#575754] hover:text-[#C5A059] transition-colors mb-6">
        <ArrowLeft className="w-4 h-4" /> Explore All
      </Link>

      <FounderStorefrontControls kind="product" id={product.id} published={product.published} onChanged={load} />

      <div className="grid lg:grid-cols-12 gap-12 lg:gap-16">
        <div className="lg:col-span-5">
          <div className="lg:sticky lg:top-28">
            <div className="relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-2xl shadow-black/10 aspect-[2/3] max-w-sm">
              {product.cover_url ? (
                <img src={coverAbs} alt={product.title} decoding="async" className="w-full h-full object-cover" data-testid="product-cover" />
              ) : (
                <div className="w-full h-full grid place-items-center text-[#575754]">{product.title}</div>
              )}
            </div>

            {purchase === null ? (
              <div className="mt-5 max-w-sm flex items-center gap-2 text-xs" style={{ color: "#8A8A85" }}>
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Checking purchase readiness…
              </div>
            ) : purchase.purchasable ? (
              <div className="mt-6 max-w-sm" data-testid="product-commerce">
                <div className="flex items-baseline gap-2">
                  <span className="qru-serif text-3xl" style={{ color: "#1C1C1A" }} data-testid="product-price">{price}</span>
                  <span className="text-sm" style={{ color: "#3A3A37" }}>· {purchaseFormat} download</span>
                </div>
                <button onClick={buy} disabled={buying} data-testid="buy-product-btn"
                  style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
                  className="mt-4 w-full inline-flex items-center justify-center gap-2 rounded-full px-6 py-3.5 text-sm font-medium transition-opacity hover:opacity-90 disabled:opacity-60">
                  {buying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  {buying ? "Redirecting to secure checkout…" : `Buy the ${purchaseFormat}`}
                </button>
                <p className="text-xs mt-2 text-center" style={{ color: "#8A8A85" }}>Secure checkout by Stripe · instant digital delivery</p>
                <p className="text-xs mt-1 text-center" style={{ color: "#8A8A85" }}>14-day satisfaction guarantee · full refund on request</p>
              </div>
            ) : (
              <p className="text-xs mt-4 max-w-sm" style={{ color: "#8A8A85" }} data-testid="product-not-purchasable">
                Not yet available for direct purchase on QRU Online.
              </p>
            )}
          </div>
        </div>

        <div className="lg:col-span-7">
          <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
            <span className="text-xs uppercase tracking-[0.2em]">{product.product_type}</span>
          </div>
          <h1 className="qru-serif text-4xl md:text-5xl font-semibold tracking-tight leading-tight" style={{ color: "#1C1C1A" }} data-testid="product-title">
            {product.title}
          </h1>

          {product.description && (
            <div className="mt-10 pt-10 border-t border-[#E5E5E0]">
              <h2 className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-4">About</h2>
              <div className="whitespace-pre-line" style={{ color: "#1C1C1A" }} data-testid="product-description">
                {product.description}
              </div>
            </div>
          )}

          <dl className="mt-10 pt-10 border-t border-[#E5E5E0] grid grid-cols-2 sm:grid-cols-3 gap-6">
            <Meta label="Subject" value={product.subject} />
            <Meta label="Format" value={purchase?.purchase_format || product.format} />
            <Meta label="Layout" value={product.layout_family} />
          </dl>

          <div className="mt-10 pt-8 border-t border-[#E5E5E0] flex items-start gap-3 text-sm" style={{ color: "#575754" }}>
            <ShieldCheck className="w-5 h-5 text-[#C5A059] shrink-0 mt-0.5" />
            <p>Manufactured and verified to the <span style={{ color: "#1C1C1A", fontWeight: 500 }}>Treasure Standard™</span>.</p>
          </div>

          <CollectionTeaser family={product.family} excludeKind="product" excludeId={product.id} />
        </div>
      </div>
    </div>
  );
}
