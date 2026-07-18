import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, BookOpen, Loader2, ShieldCheck } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";

function Meta({ label, value }) {
  if (!value) return null;
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-[0.2em] text-[#575754]">{label}</dt>
      <dd className="qru-serif text-lg text-[#1C1C1A] mt-0.5">{value}</dd>
    </div>
  );
}

export default function QRUBookPage() {
  const { id } = useParams();
  const [book, setBook] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setBook(null); setError(false);
    publicApi.get(`/books/${id}`).then((r) => setBook(r.data)).catch(() => setError(true));
  }, [id]);

  if (error) return (
    <div className="min-h-[60vh] grid place-items-center text-center px-6" data-testid="book-not-found">
      <div>
        <p className="qru-serif text-3xl">This title is not available.</p>
        <Link to="/catalog" className="inline-flex items-center gap-2 mt-6 text-sm text-[#C5A059]"><ArrowLeft className="w-4 h-4" /> Back to Catalog</Link>
      </div>
    </div>
  );

  if (!book) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;

  const priceVal = book.list_price ?? book.paperback_price ?? book.ebook_price ?? null;
  const price = priceVal != null ? `${book.currency === "USD" ? "$" : ""}${priceVal.toFixed(2)}` : null;

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-12 md:py-20" data-testid="qru-book-page">
      <Link to="/catalog" data-testid="book-back" className="inline-flex items-center gap-2 text-sm text-[#575754] hover:text-[#C5A059] transition-colors mb-10">
        <ArrowLeft className="w-4 h-4" /> Catalog
      </Link>

      <div className="grid lg:grid-cols-12 gap-12 lg:gap-16">
        {/* Sticky cover */}
        <div className="lg:col-span-5">
          <div className="lg:sticky lg:top-28">
            <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }}
              className="relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-2xl shadow-black/10 aspect-[2/3] max-w-sm">
              {book.cover_url ? (
                <img src={assetUrl(book.cover_url)} alt={book.title} decoding="async" className="w-full h-full object-cover" data-testid="book-cover" />
              ) : (
                <div className="w-full h-full grid place-items-center text-[#575754]">{book.title}</div>
              )}
            </motion.div>
            {price && (
              <div className="mt-6 flex items-center gap-4 max-w-sm">
                <span className="qru-serif text-3xl text-[#1C1C1A]" data-testid="book-price">{price}</span>
                <button disabled data-testid="book-availability"
                  className="flex-1 rounded-full border border-[#E5E5E0] text-[#575754] px-6 py-3 text-sm cursor-not-allowed">
                  Available soon
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Details */}
        <div className="lg:col-span-7">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
            <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
              <BookOpen className="w-4 h-4" />
              <span className="text-xs uppercase tracking-[0.2em]">{book.imprint || "QRU Press™"}</span>
            </div>
            <h1 className="qru-serif text-4xl md:text-5xl font-semibold tracking-tight leading-tight" data-testid="book-title">{book.title}</h1>
            {book.subtitle && <p className="text-xl text-[#575754] mt-3 leading-relaxed">{book.subtitle}</p>}
            <p className="qru-serif text-2xl text-[#1C1C1A] mt-6">by {book.author}</p>

            {book.description && (
              <div className="mt-10 pt-10 border-t border-[#E5E5E0]">
                <h2 className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-4">About this book</h2>
                <div className="prose max-w-none text-[#1C1C1A] leading-relaxed whitespace-pre-line" data-testid="book-description">
                  {book.description}
                </div>
              </div>
            )}

            <dl className="mt-10 pt-10 border-t border-[#E5E5E0] grid grid-cols-2 sm:grid-cols-3 gap-6">
              <Meta label="Genre" value={book.genre} />
              <Meta label="Edition" value={book.edition} />
              <Meta label="Language" value={book.language} />
              <Meta label="Audience" value={book.audience} />
              <Meta label="Publisher" value={book.publisher} />
              <Meta label="Series" value={book.series} />
            </dl>

            <div className="mt-10 pt-8 border-t border-[#E5E5E0] flex items-start gap-3 text-sm text-[#575754]">
              <ShieldCheck className="w-5 h-5 text-[#C5A059] shrink-0 mt-0.5" />
              <p>Manufactured and verified to the <span className="text-[#1C1C1A] font-medium">Treasure Standard™</span> — authorized for release by QRU Press™.</p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
