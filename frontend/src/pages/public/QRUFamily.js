import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";
import Seo from "./Seo";

export default function QRUFamily() {
  const { id } = useParams();
  const [items, setItems] = useState(null);

  useEffect(() => {
    setItems(null);
    Promise.all([
      publicApi.get("/books", { params: { family_id: id } }),
      publicApi.get("/products", { params: { family_id: id } }),
    ])
      .then(([books, products]) =>
        setItems([
          ...books.data.books.map((b) => ({ ...b, kind: "book", href: `/book/${b.slug}` })),
          ...products.data.products.map((p) => ({ ...p, kind: "product", href: `/product/${p.slug}` })),
        ])
      )
      .catch(() => setItems([]));
  }, [id]);

  // The family's name isn't in the URL (only its opaque id is) — it comes back on every member
  // item's own `family` field, so once loaded, any member tells us the collection's title.
  const name = items?.find((i) => i.family?.id === id)?.family?.title || items?.[0]?.family?.title;

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid={`qru-family-${id}`}>
      <Seo
        title={name ? `${name} Collection · QRU Press™` : "Collection · QRU Press™"}
        description={name ? `Everything QRU Press™ manufactured from the same source as ${name}.` : "A QRU Press™ product collection."}
      />
      <div className="border-b border-[#E5E5E0] pb-10 mb-14">
        <p className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-3">A QRU Online Collection</p>
        <h1 className="qru-serif text-5xl md:text-6xl font-semibold tracking-tight leading-none">
          {name ? `${name} Collection` : items === null ? "Loading…" : "Collection"}
        </h1>
        <p className="text-[#575754] mt-4 max-w-xl leading-relaxed">
          Manufactured together from the same verified source — every format QRU Press™ built from it.
        </p>
      </div>

      {items === null ? (
        <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>
      ) : items.length === 0 ? (
        <div className="border border-dashed border-[#E5E5E0] rounded-lg p-16 text-center">
          <p className="qru-serif text-2xl">This collection is not available.</p>
          <Link to="/catalog" className="inline-block mt-4 text-sm text-[#C5A059]">Explore everything instead →</Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-8 gap-y-14">
          {items.map((item) => (
            <Link key={`${item.kind}-${item.id}`} to={item.href} data-testid={`family-item-${item.kind}-${item.id}`} className="group block">
              <div className="relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-xl shadow-black/5 aspect-[2/3] transition-transform duration-500 group-hover:-translate-y-2 group-hover:shadow-2xl">
                {item.cover_url ? (
                  <img src={assetUrl(item.thumb_url || item.cover_url)} alt={item.title} decoding="async" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full grid place-items-center text-sm text-[#575754] p-4 text-center">{item.title}</div>
                )}
              </div>
              <div className="mt-4">
                <p className="text-[10px] uppercase tracking-[0.2em] text-[#C5A059]">{item.kind === "book" ? "Book" : item.product_type}</p>
                <h3 className="qru-serif text-lg font-semibold leading-snug mt-1 group-hover:text-[#C5A059] transition-colors">{item.title}</h3>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
