import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";
import Seo from "./Seo";

export default function QRUCatalog() {
  const [data, setData] = useState(null);
  const [imprint, setImprint] = useState(null);
  useEffect(() => {
    publicApi.get("/books", { params: imprint ? { imprint } : {} })
      .then((r) => setData(r.data)).catch(() => setData({ books: [], count: 0, imprints: [] }));
  }, [imprint]);

  if (!data) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;

  const books = data.books || [];
  const imprints = data.imprints || [];

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid="qru-catalog">
      <Seo title="Books · QRU Press™" description="Browse authorized titles from QRU Press™ — each book manufactured and verified to the Treasure Standard™." />
      <div className="border-b border-[#E5E5E0] pb-10 mb-14">
        <p className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-3">The Books Experience</p>
        <h1 className="qru-serif text-5xl md:text-6xl font-semibold tracking-tight leading-none">Books</h1>
        <p className="text-[#575754] mt-4 max-w-xl leading-relaxed">
          {data.count} authorized {data.count === 1 ? "title" : "titles"}, each manufactured and verified to the Treasure Standard™.
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
      </div>

      {books.length === 0 ? (
        <div className="border border-dashed border-[#E5E5E0] rounded-lg p-16 text-center" data-testid="catalog-empty">
          <p className="qru-serif text-2xl">No titles published yet.</p>
          <p className="text-sm text-[#575754] mt-2">Authorized releases will appear here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-8 gap-y-14">
          {books.map((book) => (
            <div key={book.id}>
              <Link to={`/book/${book.slug || book.id}`} data-testid={`catalog-book-${book.id}`} className="group block">
                <div className="relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-xl shadow-black/5 aspect-[2/3] transition-transform duration-500 group-hover:-translate-y-2 group-hover:shadow-2xl">
                  {book.cover_url ? (
                    <img src={assetUrl(book.thumb_url || book.cover_url)} alt={book.title} decoding="async"
                      className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full grid place-items-center text-sm text-[#575754] p-4 text-center">{book.title}</div>
                  )}
                </div>
                <div className="mt-4">
                  <p className="text-[10px] uppercase tracking-[0.2em] text-[#C5A059]">{book.genre || book.imprint}</p>
                  <h3 className="qru-serif text-lg font-semibold leading-snug mt-1 group-hover:text-[#C5A059] transition-colors">{book.title}</h3>
                  <p className="text-sm text-[#575754] mt-0.5">{book.author}</p>
                </div>
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
