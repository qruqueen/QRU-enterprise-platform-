import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Loader2, ShieldCheck } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";
import Seo from "./Seo";
import TrustMarks from "./TrustMarks";
import NewsletterSignup from "./NewsletterSignup";

const HERO_IMG = "/qru-hero.png";

function CoverCard({ book, large }) {
  return (
    <div>
      <Link to={`/book/${book.slug || book.id}`} data-testid={`featured-book-${book.id}`} className="group block">
        <div className={`relative overflow-hidden rounded-md border border-[#E5E5E0] bg-[#EDEBE4] shadow-xl shadow-black/5 transition-transform duration-500 group-hover:-translate-y-2 group-hover:shadow-2xl ${large ? "aspect-[3/4]" : "aspect-[2/3]"}`}>
          {book.cover_url ? (
            <img src={assetUrl(book.thumb_url || book.cover_url)} alt={book.title} decoding="async"
              className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full grid place-items-center text-[#575754]">{book.title}</div>
          )}
        </div>
        <div className="mt-4">
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#C5A059]">{book.genre || book.imprint}</p>
          <h3 className={`qru-serif ${large ? "text-2xl" : "text-lg"} font-semibold leading-snug mt-1 group-hover:text-[#C5A059] transition-colors`}>
            {book.title}
          </h3>
          <p className="text-sm text-[#575754] mt-0.5">{book.author}</p>
        </div>
      </Link>
    </div>
  );
}

export default function QRUHome() {
  const [data, setData] = useState(null);
  useEffect(() => { publicApi.get("/home").then((r) => setData(r.data)).catch(() => setData({ featured: [], brand: {} })); }, []);

  if (!data) return <div className="min-h-[60vh] grid place-items-center"><Loader2 className="w-6 h-6 animate-spin text-[#C5A059]" /></div>;

  const featured = data.featured || [];
  const [hero, ...rest] = featured;

  return (
    <div data-testid="qru-home">
      <Seo title="QRU Press™ — Books that make hard ideas easy" />
      {/* Hero — split layout: text on solid bone, image beside it (no overlays) */}
      <section className="grid lg:grid-cols-2 items-stretch" style={{ backgroundColor: "#FAFAF8" }}>
        <div className="flex items-center px-6 md:px-12 lg:pl-16 xl:pl-24 py-20 md:py-28 lg:py-36">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 mb-6" style={{ color: "#C5A059" }}>
              <ShieldCheck className="w-4 h-4" />
              <span className="text-xs uppercase tracking-[0.25em]">QRU Press™ · The Treasure Standard™</span>
            </div>
            <h1 className="qru-serif text-5xl md:text-7xl leading-[0.95] tracking-tight font-semibold" style={{ color: "#1C1C1A" }}>
              Books that make<br />hard ideas easy.
            </h1>
            <p className="text-lg mt-8 leading-relaxed" style={{ color: "#3A3A37" }}>
              QRU Press is a premium educational publishing house. Every title is carefully
              researched, thoughtfully written, and verified to the QRU Treasure Standard™.
            </p>
            <div className="flex flex-wrap items-center gap-4 mt-10">
              <Link to="/catalog" data-testid="hero-browse-catalog"
                style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
                className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 text-sm font-medium transition-opacity hover:opacity-90">
                Browse the Books <ArrowRight className="w-4 h-4" />
              </Link>
              <span className="text-sm" style={{ color: "#3A3A37" }}>
                {data.counts?.books ?? ""} {data.counts?.books === 1 ? "title" : "titles"} available now
              </span>
            </div>
          </div>
        </div>
        <div className="relative" style={{ minHeight: 300 }}>
          <img src={HERO_IMG} alt="QRU Press reading room"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
        </div>
      </section>

      <TrustMarks />

      {/* Featured */}
      <section className="max-w-7xl mx-auto px-6 md:px-10 py-20 md:py-28">
        <div className="flex items-end justify-between mb-12">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-[#C5A059] mb-2">Published by QRU Press™</p>
            <h2 className="qru-serif text-3xl md:text-4xl font-semibold tracking-tight">Featured Titles</h2>
          </div>
          <Link to="/catalog" className="hidden sm:inline-flex items-center gap-2 text-sm text-[#575754] hover:text-[#C5A059] transition-colors" data-testid="see-all-books">
            See all {data.counts?.books ?? ""} titles <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {featured.length === 0 ? (
          <div className="border border-dashed border-[#E5E5E0] rounded-lg p-16 text-center" data-testid="home-empty">
            <p className="qru-serif text-2xl text-[#1C1C1A]">The first titles are being prepared.</p>
            <p className="text-sm text-[#575754] mt-2">Authorized releases from the QRU Press™ will appear here.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            {hero && (
              <div className="lg:col-span-5">
                <CoverCard book={hero} large />
              </div>
            )}
            <div className="lg:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-8">
              {rest.map((b) => <CoverCard key={b.id} book={b} />)}
            </div>
          </div>
        )}
      </section>

      <NewsletterSignup />
    </div>
  );
}
