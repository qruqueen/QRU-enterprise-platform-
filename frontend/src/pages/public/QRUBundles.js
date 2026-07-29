import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, Gift } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";
import Seo from "./Seo";

export default function QRUBundles() {
  const [data, setData] = useState(null);
  useEffect(() => { publicApi.get("/bundles").then((r) => setData(r.data)).catch(() => setData({ bundles: [], count: 0 })); }, []);

  if (!data) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;
  const bundles = data.bundles || [];

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid="qru-bundles">
      <Seo title="Bundles · QRU Press™" description="Curated QRU bundles — more understanding for less. Every bundle is verified to the Treasure Standard™." />
      <div className="border-b border-[#E5E5E0] pb-10 mb-14">
        <p className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-3">The Bundles Experience</p>
        <h1 className="qru-serif text-5xl md:text-6xl font-semibold tracking-tight leading-none">Bundles</h1>
        <p className="text-[#575754] mt-4 max-w-xl leading-relaxed">
          {data.count} curated {data.count === 1 ? "bundle" : "bundles"} — carefully paired titles, one price, more understanding for less.
        </p>
      </div>

      {bundles.length === 0 ? (
        <div className="border border-dashed border-[#E5E5E0] rounded-lg p-16 text-center" data-testid="bundles-empty">
          <Gift className="w-8 h-8 text-[#C5A059] mx-auto mb-3" />
          <p className="qru-serif text-2xl">No bundles published yet.</p>
          <p className="text-sm text-[#575754] mt-2">Curated collections will appear here.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {bundles.map((b) => (
            <Link key={b.id} to={`/bundle/${b.slug || b.id}`} data-testid={`bundle-card-${b.id}`}
              className="group block rounded-lg border border-[#E5E5E0] bg-white overflow-hidden shadow-xl shadow-black/5 transition-transform duration-500 hover:-translate-y-2 hover:shadow-2xl">
              <div className="relative aspect-[16/10] bg-[#EDEBE4]">
                {b.cover_url ? <img src={assetUrl(b.cover_url)} alt={b.title} className="w-full h-full object-cover" />
                  : <div className="w-full h-full grid place-items-center"><Gift className="w-8 h-8 text-[#C5A059]" /></div>}
                {b.savings > 0 && (
                  <span className="absolute top-3 right-3 rounded-full bg-[#C5A059] text-white text-xs font-semibold px-3 py-1">Save ${b.savings.toFixed(2)}</span>
                )}
              </div>
              <div className="p-5">
                <p className="text-[10px] uppercase tracking-[0.2em] text-[#C5A059]">{b.item_count} items</p>
                <h3 className="qru-serif text-xl font-semibold leading-snug mt-1 group-hover:text-[#C5A059] transition-colors">{b.title}</h3>
                {b.subtitle && <p className="text-sm text-[#575754] mt-1">{b.subtitle}</p>}
                <div className="flex items-baseline gap-2 mt-3">
                  <span className="qru-serif text-2xl font-semibold text-[#1C1C1A]">${b.price.toFixed(2)}</span>
                  {b.savings > 0 && <span className="text-sm text-[#8A8A85] line-through">${b.sum_price.toFixed(2)}</span>}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
