import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { publicApi, assetUrl } from "./publicApi";

/**
 * "More from this collection" — the real, click-reachable entry point into a product family
 * (see backend/public_family.py) from any item that's actually part of one. Renders nothing
 * when the item has no family or has no other published siblings, so it never appears as a
 * dead end.
 */
export default function CollectionTeaser({ family, excludeKind, excludeId }) {
  const [siblings, setSiblings] = useState(null);

  useEffect(() => {
    if (!family?.id) {
      setSiblings(null);
      return;
    }
    setSiblings(null);
    Promise.all([
      publicApi.get("/books", { params: { family_id: family.id } }),
      publicApi.get("/products", { params: { family_id: family.id } }),
    ])
      .then(([books, products]) => {
        const items = [
          ...books.data.books.map((b) => ({ ...b, kind: "book", href: `/book/${b.slug}` })),
          ...products.data.products.map((p) => ({ ...p, kind: "product", href: `/product/${p.slug}` })),
        ].filter((item) => !(item.kind === excludeKind && item.id === excludeId));
        setSiblings(items);
      })
      .catch(() => setSiblings([]));
  }, [family?.id, excludeKind, excludeId]);

  if (!family?.id || !siblings || siblings.length === 0) return null;

  return (
    <div className="mt-10 pt-10 border-t border-[#E5E5E0]" data-testid="collection-teaser">
      <div className="flex items-end justify-between mb-6 gap-4">
        <h2 className="text-xs uppercase tracking-[0.2em] text-[#C5A059]">More from the {family.title} Collection</h2>
        <Link to={`/family/${family.id}`} data-testid="collection-teaser-view-all" className="text-sm text-[#575754] hover:text-[#C5A059] transition-colors shrink-0">
          View collection →
        </Link>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
        {siblings.map((item) => (
          <Link key={`${item.kind}-${item.id}`} to={item.href} data-testid={`collection-teaser-${item.kind}-${item.id}`} className="group block">
            <div className="relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-md shadow-black/5 aspect-[2/3]">
              {item.cover_url ? (
                <img src={assetUrl(item.thumb_url || item.cover_url)} alt={item.title} decoding="async" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full grid place-items-center text-xs text-[#575754] p-2 text-center">{item.title}</div>
              )}
            </div>
            <p className="text-sm mt-2 group-hover:text-[#C5A059] transition-colors">{item.title}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
