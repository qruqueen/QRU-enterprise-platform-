import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Loader2, Gift, ShieldCheck, Check, ArrowLeft } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";
import Seo from "./Seo";

export default function QRUBundlePage() {
  const { slug } = useParams();
  const [bundle, setBundle] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [buying, setBuying] = useState(false);

  useEffect(() => {
    publicApi.get(`/bundles/${slug}`).then((r) => setBundle(r.data)).catch(() => setNotFound(true));
  }, [slug]);

  const buy = async () => {
    setBuying(true);
    try {
      const { data } = await publicApi.post("/bundle-checkout", { bundle_id: bundle.id, origin_url: window.location.origin });
      if (data.checkout_url) window.location.href = data.checkout_url;
    } catch { setBuying(false); }
  };

  if (notFound) return (
    <div className="max-w-2xl mx-auto px-6 py-24 text-center" data-testid="bundle-not-found">
      <h1 className="qru-serif text-3xl">This bundle is not available.</h1>
      <Link to="/bundles" className="text-[#C5A059] hover:underline mt-4 inline-block">Back to Bundles</Link>
    </div>
  );
  if (!bundle) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;

  return (
    <div className="max-w-6xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid="qru-bundle-page">
      <Seo title={`${bundle.title} · QRU Bundles`} description={bundle.subtitle || bundle.description} />
      <Link to="/bundles" className="inline-flex items-center gap-1.5 text-sm text-[#575754] hover:text-[#C5A059] mb-8"><ArrowLeft className="w-4 h-4" /> All bundles</Link>
      <div className="grid md:grid-cols-2 gap-12 lg:gap-16">
        <div>
          <div className="rounded-lg border border-[#E5E5E0] bg-[#EDEBE4] overflow-hidden aspect-[16/12]">
            {bundle.cover_url ? <img src={assetUrl(bundle.cover_url)} alt={bundle.title} className="w-full h-full object-cover" />
              : <div className="w-full h-full grid place-items-center"><Gift className="w-12 h-12 text-[#C5A059]" /></div>}
          </div>
        </div>
        <div>
          <div className="inline-flex items-center gap-2 text-[#C5A059] mb-3">
            <ShieldCheck className="w-4 h-4" /><span className="text-xs uppercase tracking-[0.2em]">Bundle · {bundle.item_count} items</span>
          </div>
          <h1 className="qru-serif text-4xl md:text-5xl font-semibold leading-tight">{bundle.title}</h1>
          {bundle.subtitle && <p className="text-lg text-[#575754] mt-3">{bundle.subtitle}</p>}
          {bundle.description && <p className="text-[#3A3A37] mt-4 leading-relaxed">{bundle.description}</p>}

          <div className="flex items-baseline gap-3 mt-6">
            <span className="qru-serif text-4xl font-semibold text-[#1C1C1A]" data-testid="bundle-price">${bundle.price.toFixed(2)}</span>
            {bundle.savings > 0 && <>
              <span className="text-lg text-[#8A8A85] line-through">${bundle.sum_price.toFixed(2)}</span>
              <span className="rounded-full bg-[#C5A059]/15 text-sm font-semibold px-3 py-1" style={{ color: "#8a6d2f" }} data-testid="bundle-savings">Save ${bundle.savings.toFixed(2)}</span>
            </>}
          </div>

          <button onClick={buy} disabled={buying} data-testid="buy-bundle-btn"
            style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
            className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 text-sm font-medium mt-6 transition-opacity hover:opacity-90 disabled:opacity-60">
            {buying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Gift className="w-4 h-4" />} Buy the bundle
          </button>
          <p className="mt-4 text-xs text-[#8A8A85]">One purchase · every item delivered instantly · full refund within 14 days.</p>

          <div className="mt-10">
            <p className="text-xs uppercase tracking-[0.2em] text-[#575754] mb-4">What's included</p>
            <div className="space-y-3" data-testid="bundle-items">
              {bundle.items.map((it) => (
                <Link key={it.id} to={`/book/${it.id}`} className="flex items-center gap-4 rounded-lg border border-[#E5E5E0] p-3 hover:border-[#C5A059] transition-colors" data-testid={`bundle-item-${it.id}`}>
                  <img src={assetUrl(it.cover_thumb)} alt={it.title} className="w-12 h-16 object-cover rounded border border-[#E5E5E0]" />
                  <div className="flex-1">
                    <p className="qru-serif font-semibold leading-snug">{it.title}</p>
                    <p className="text-xs text-[#575754]">{it.author} · {it.imprint}</p>
                  </div>
                  <span className="text-sm text-[#8A8A85]">${it.price.toFixed(2)}</span>
                  <Check className="w-4 h-4 text-emerald-600" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
