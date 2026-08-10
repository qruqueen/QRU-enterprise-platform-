import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";
import Seo from "./Seo";

export default function QRUCatalog() {
  const [data, setData] = useState(null);
  const [products, setProducts] = useState(null);
  const [collections, setCollections] = useState([]);
  const [imprint, setImprint] = useState(null);
  const [format, setFormat] = useState(null);
  const [subject, setSubject] = useState(null);

  useEffect(() => {
    const params = {};
    if (imprint) params.imprint = imprint;
    if (subject) params.subject = subject;
    publicApi.get("/books", { params })
      .then((r) => setData(r.data)).catch(() => setData({ books: [], count: 0, imprints: [] }));
    publicApi.get("/products", { params: subject ? { subject } : {} })
      .then((r) => setProducts(r.data.products)).catch(() => setProducts([]));
  }, [imprint, subject]);

  // Subject options come from the whole catalog (not the currently-filtered view), same
  // reasoning as imprints below — so picking a subject never hides the other subject options.
  useEffect(() => {
    publicApi.get("/collections").then((r) => setCollections(r.data.collections || [])).catch(() => setCollections([]));
  }, []);

  if (!data || products === null) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;

  const books = data.books || [];
  const imprints = data.imprints || [];
  const formats = Array.from(new Set(products.map((p) => p.format).filter(Boolean))).sort();
  const items = [
    ...books.map((b) => ({ ...b, kind: "book", href: `/book/${b.slug || b.id}`, label: b.genre || b.imprint, format: "epub" })),
    ...products.map((p) => ({ ...p, kind: "product", href: `/product/${p.slug}`, label: p.subject || p.product_type })),
  ].filter((item) => !format || item.format === format);
  const total = items.length;

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid="qru-catalog">
      <Seo title="Explore All · QRU Press™" description="Browse every authorized title and product from QRU Press™ — each one manufactured and verified to the Treasure Standard™." />
      <div className="border-b border-[#E5E5E0] pb-10 mb-14">
        <p className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-3">Explore All</p>
        <h1 className="qru-serif text-5xl md:text-6xl font-semibold tracking-tight leading-none">Explore All</h1>
        <p className="text-[#575754] mt-4 max-w-xl leading-relaxed">
          {total} authorized {total === 1 ? "item" : "items"}, each manufactured and verified to the Treasure Standard™.
        </p>
        {imprints.length > 1 && (
          <div className="flex flex-wrap items-center gap-2 mt-6" data-testid="imprint-filter">
            <span className="text-xs uppercase tracking-[0.15em] text-[#575754] mr-1">Imprint</span>
            <button onClick={() => setImprint(null)} data-testid="imprint-all"
              className={`rounded-full px-4 py-1.5 text-xs border transition-colors ${!imprint ? "bg-[#1C1C1A] text-[#FAFAF8] border-[#1C1C1A]" : "border-[#E5E5E0] text-[#575754] hover:border-[#C5A059]"}`}>All Imprints</button>
            {imprints.map((im) => (
              <button key={im} onClick={() => setImprint(im)} data-testid={`imprint-${im}`}
                className={`rounded-full px-4 py-1.5 text-xs border transition-colors ${imprint === im ? "bg-[#C5A059] text-[#FAFAF8] border-[#C5A059]" : "border-[#E5E5E0] text-[#575754] hover:border-[#C5A059]"}`}>{im}</button>
            ))}
          </div>
        )}
        {formats.length > 1 && (
          <div className="flex flex-wrap items-center gap-2 mt-3" data-testid="format-filter">
            <span className="text-xs uppercase tracking-[0.15em] text-[#575754] mr-1">Format</span>
            <button onClick={() => setFormat(null)} data-testid="format-all"
              className={`rounded-full px-4 py-1.5 text-xs border transition-colors ${!format ? "bg-[#1C1C1A] text-[#FAFAF8] border-[#1C1C1A]" : "border-[#E5E5E0] text-[#575754] hover:border-[#C5A059]"}`}>All Formats</button>
            {formats.map((f) => (
              <button key={f} onClick={() => setFormat(f)} data-testid={`format-${f}`}
                className={`rounded-full px-4 py-1.5 text-xs border transition-colors ${format === f ? "bg-[#C5A059] text-[#FAFAF8] border-[#C5A059]" : "border-[#E5E5E0] text-[#575754] hover:border-[#C5A059]"}`}>{f}</button>
            ))}
          </div>
        )}
        {collections.length > 1 && (
          <div className="flex flex-wrap items-center gap-2 mt-3" data-testid="subject-filter">
            <span className="text-xs uppercase tracking-[0.15em] text-[#575754] mr-1">Subject</span>
            <button onClick={() => setSubject(null)} data-testid="subject-all"
              className={`rounded-full px-4 py-1.5 text-xs border transition-colors ${!subject ? "bg-[#1C1C1A] text-[#FAFAF8] border-[#1C1C1A]" : "border-[#E5E5E0] text-[#575754] hover:border-[#C5A059]"}`}>All Subjects</button>
            {collections.map((c) => (
              <button key={c.id} onClick={() => setSubject(c.id)} data-testid={`subject-${c.id}`}
                className={`rounded-full px-4 py-1.5 text-xs border transition-colors ${subject === c.id ? "bg-[#C5A059] text-[#FAFAF8] border-[#C5A059]" : "border-[#E5E5E0] text-[#575754] hover:border-[#C5A059]"}`}>{c.name} ({c.count})</button>
            ))}
          </div>
        )}
      </div>

      {items.length === 0 ? (
        <div className="border border-dashed border-[#E5E5E0] rounded-lg p-16 text-center" data-testid="catalog-empty">
          <p className="qru-serif text-2xl">No titles published yet.</p>
          <p className="text-sm text-[#575754] mt-2">Authorized releases will appear here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-8 gap-y-14">
          {items.map((item) => (
            <div key={`${item.kind}-${item.id}`}>
              <Link to={item.href} data-testid={`catalog-${item.kind}-${item.id}`} className="group block">
                <div className="relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-xl shadow-black/5 aspect-[2/3] transition-transform duration-500 group-hover:-translate-y-2 group-hover:shadow-2xl">
                  {item.cover_url ? (
                    <img src={assetUrl(item.thumb_url || item.cover_url)} alt={item.title} decoding="async"
                      className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full grid place-items-center text-sm text-[#575754] p-4 text-center">{item.title}</div>
                  )}
                </div>
                <div className="mt-4">
                  <p className="text-[10px] uppercase tracking-[0.2em] text-[#C5A059]">{item.label}</p>
                  <h3 className="qru-serif text-lg font-semibold leading-snug mt-1 group-hover:text-[#C5A059] transition-colors">{item.title}</h3>
                  <p className="text-sm text-[#575754] mt-0.5">{item.author}</p>
                </div>
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
