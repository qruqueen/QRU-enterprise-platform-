import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, BookOpen, Loader2, ShieldCheck } from "lucide-react";
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

export default function QRUBookPage() {
  const { slug } = useParams();
  const [book, setBook] = useState(null);
  const [error, setError] = useState(false);
  const [buying, setBuying] = useState(false);

  const load = useCallback(() => {
    setBook(null); setError(false);
    // publicApi never attaches auth by design (see publicApi.js), but the detail endpoint's
    // Founder-only bypass for a hidden book needs the token when one is present — otherwise a
    // signed-in Founder gets the same 404 an anonymous visitor gets and can never reach the
    // page to restore it. Scoped to this one call only; every other publicApi caller is unaffected.
    const token = localStorage.getItem("qru_token");
    publicApi.get(`/books/${slug}`, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined)
      .then((r) => setBook(r.data)).catch(() => setError(true));
  }, [slug]);

  useEffect(() => { load(); }, [load]);

  const buy = async () => {
    if (!book) return;
    setBuying(true);
    try {
      const { data } = await publicApi.post("/checkout", { book_id: book.id, origin_url: window.location.origin });
      window.location.href = data.checkout_url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start checkout. Please try again.");
      setBuying(false);
    }
  };

  if (error) return (
    <div className="min-h-[60vh] grid place-items-center text-center px-6" data-testid="book-not-found">
      <div>
        <p className="qru-serif text-3xl">This title is not available.</p>
        <Link to="/catalog" className="inline-flex items-center gap-2 mt-6 text-sm text-[#C5A059]"><ArrowLeft className="w-4 h-4" /> Back to Catalog</Link>
      </div>
    </div>
  );

  if (!book) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;

  const priceVal = book.ebook_price ?? book.list_price ?? book.paperback_price ?? null;
  const price = priceVal != null ? `${book.currency === "USD" ? "$" : ""}${priceVal.toFixed(2)}` : null;
  const seoDesc = (book.description || book.subtitle || `${book.title} by ${book.author} — published by QRU Press™.`).slice(0, 300);
  const coverAbs = book.cover_url ? assetUrl(book.thumb_url || book.cover_url) : null;

  return (
    <div className="max-w-7xl mx-auto px-6 md:px-10 py-12 md:py-20" data-testid="qru-book-page">
      <Seo title={`${book.title}${book.author ? ` — ${book.author}` : ""} · QRU Press™`} description={seoDesc} image={coverAbs} />
      <Link to="/catalog" data-testid="book-back" className="inline-flex items-center gap-2 text-sm text-[#575754] hover:text-[#C5A059] transition-colors mb-10">
        <ArrowLeft className="w-4 h-4" /> Catalog
      </Link>

      <FounderStorefrontControls kind="book" id={book.id} published={book.published} onChanged={load} />

      <div className="grid lg:grid-cols-12 gap-12 lg:gap-16">
        {/* Sticky cover */}
        <div className="lg:col-span-5">
          <div className="lg:sticky lg:top-28">
            <div className="relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-2xl shadow-black/10 aspect-[2/3] max-w-sm">
              {book.cover_url ? (
                <img src={assetUrl(book.thumb_url || book.cover_url)} alt={book.title} decoding="async" className="w-full h-full object-cover" data-testid="book-cover" />
              ) : (
                <div className="w-full h-full grid place-items-center text-[#575754]">{book.title}</div>
              )}
            </div>
            {price && (
              <div className="mt-6 max-w-sm">
                <div className="flex items-baseline gap-2">
                  <span className="qru-serif text-3xl" style={{ color: "#1C1C1A" }} data-testid="book-price">{price}</span>
                  <span className="text-sm" style={{ color: "#3A3A37" }}>· ebook (EPUB)</span>
                </div>
                <button onClick={buy} disabled={buying} data-testid="buy-ebook-btn"
                  style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
                  className="mt-4 w-full inline-flex items-center justify-center gap-2 rounded-full px-6 py-3.5 text-sm font-medium transition-opacity hover:opacity-90 disabled:opacity-60">
                  {buying ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />}
                  {buying ? "Redirecting to secure checkout…" : "Buy the ebook"}
                </button>
                <p className="text-xs mt-2 text-center" style={{ color: "#8A8A85" }}>Secure checkout by Stripe · instant download</p>
                <p className="text-xs mt-1 text-center" style={{ color: "#8A8A85" }} data-testid="refund-guarantee">14-day satisfaction guarantee · full refund on request</p>
              </div>
            )}
          </div>
        </div>

        {/* Details */}
        <div className="lg:col-span-7">
          <div>
            <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
              <BookOpen className="w-4 h-4" />
              <span className="text-xs uppercase tracking-[0.2em]">{book.imprint || "QRU Press™"}</span>
            </div>
            <h1 className="qru-serif text-4xl md:text-5xl font-semibold tracking-tight leading-tight" style={{ color: "#1C1C1A" }} data-testid="book-title">{book.title}</h1>
            {book.subtitle && <p className="text-xl mt-3 leading-relaxed" style={{ color: "#575754" }}>{book.subtitle}</p>}
            <p className="qru-serif text-2xl mt-6" style={{ color: "#1C1C1A" }}>by {book.author}</p>

            {book.description && (
              <div className="mt-10 pt-10 border-t border-[#E5E5E0]">
                <h2 className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-4">About this book</h2>
                <div className="max-w-none leading-relaxed whitespace-pre-line" style={{ color: "#1C1C1A" }} data-testid="book-description">
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

            <div className="mt-10 pt-8 border-t border-[#E5E5E0] flex items-start gap-3 text-sm" style={{ color: "#575754" }}>
              <ShieldCheck className="w-5 h-5 text-[#C5A059] shrink-0 mt-0.5" />
              <p>Manufactured and verified to the <span style={{ color: "#1C1C1A", fontWeight: 500 }}>Treasure Standard™</span> — authorized for release by QRU Press™.</p>
            </div>

            <CollectionTeaser family={book.family} excludeKind="book" excludeId={book.id} />
          </div>
        </div>
      </div>
    </div>
  );
}
