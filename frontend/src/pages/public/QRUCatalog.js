import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";

export default function QRUCatalog() {
  const [data, setData] = useState(null);
  useEffect(() => { publicApi.get("/books").then((r) => setData(r.data)).catch(() => setData({ books: [], count: 0 })); }, []);

  if (!data) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;

  const books = data.books || [];

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid="qru-catalog">
      <div className="border-b border-[#E5E5E0] pb-10 mb-14">
        <p className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-3">QRU Press™ Catalog</p>
        <h1 className="qru-serif text-5xl md:text-6xl font-semibold tracking-tight leading-none">Books</h1>
        <p className="text-[#575754] mt-4 max-w-xl leading-relaxed">
          {data.count} authorized {data.count === 1 ? "title" : "titles"}, each manufactured and verified to the Treasure Standard™.
        </p>
      </div>

      {books.length === 0 ? (
        <div className="border border-dashed border-[#E5E5E0] rounded-lg p-16 text-center" data-testid="catalog-empty">
          <p className="qru-serif text-2xl">No titles published yet.</p>
          <p className="text-sm text-[#575754] mt-2">Authorized releases will appear here.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-8 gap-y-14">
          {books.map((book, i) => (
            <motion.div key={book.id}
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, delay: (i % 8) * 0.05 }}>
              <Link to={`/book/${book.id}`} data-testid={`catalog-book-${book.id}`} className="group block">
                <div className="relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-xl shadow-black/5 aspect-[2/3] transition-transform duration-500 group-hover:-translate-y-2 group-hover:shadow-2xl">
                  {book.cover_url ? (
                    <img src={assetUrl(book.cover_url)} alt={book.title} decoding="async"
                      className="w-full h-full object-cover" loading="lazy" />
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
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
