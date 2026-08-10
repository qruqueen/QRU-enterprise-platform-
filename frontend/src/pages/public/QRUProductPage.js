import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Loader2, ShieldCheck } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";
import Seo from "./Seo";
import FounderStorefrontControls from "@/components/FounderStorefrontControls";

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
  const [error, setError] = useState(false);

  const load = useCallback(() => {
    setProduct(null);
    setError(false);
    publicApi.get(`/products/${slug}`).then((r) => setProduct(r.data)).catch(() => setError(true));
  }, [slug]);

  useEffect(() => { load(); }, [load]);

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
            {!product.purchasable && (
              <p className="text-xs mt-4 max-w-sm" style={{ color: "#8A8A85" }}>
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
            <Meta label="Format" value={product.format} />
            <Meta label="Family" value={product.family} />
          </dl>

          <div className="mt-10 pt-8 border-t border-[#E5E5E0] flex items-start gap-3 text-sm" style={{ color: "#575754" }}>
            <ShieldCheck className="w-5 h-5 text-[#C5A059] shrink-0 mt-0.5" />
            <p>Manufactured and verified to the <span style={{ color: "#1C1C1A", fontWeight: 500 }}>Treasure Standard™</span>.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
