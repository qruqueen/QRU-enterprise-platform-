import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Loader2, ShieldCheck } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";

const HERO_IMG =
  "https://images.unsplash.com/photo-1779703056727-3c8b2bd919bc?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwxfHxlbGVnYW50JTIwbGlicmFyeSUyMGFyY2hpdGVjdHVyZSUyMG1vZGVybnxlbnwwfHx8fDE3ODQyNDIwNzB8MA&ixlib=rb-4.1.0&q=85";

function CoverCard({ book, index, large }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.08 }}
    >
      <Link to={`/book/${book.id}`} data-testid={`featured-book-${book.id}`} className="group block">
        <div className={`relative overflow-hidden rounded-md border border-[#E5E5E0] bg-white shadow-xl shadow-black/5 transition-transform duration-500 group-hover:-translate-y-2 group-hover:shadow-2xl ${large ? "aspect-[3/4]" : "aspect-[2/3]"}`}>
          {book.cover_url ? (
            <img src={assetUrl(book.cover_url)} alt={book.title}
              className="w-full h-full object-cover" loading="lazy" />
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
    </motion.div>
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
      {/* Hero */}
      <section className="relative">
        <div className="absolute inset-0">
          <img src={HERO_IMG} alt="" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#FAFAF8] via-[#FAFAF8]/85 to-[#FAFAF8]/30" />
        </div>
        <div className="relative max-w-7xl mx-auto px-6 md:px-10 py-28 md:py-40">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="max-w-2xl">
            <div className="inline-flex items-center gap-2 text-[#C5A059] mb-6">
              <ShieldCheck className="w-4 h-4" />
              <span className="text-xs uppercase tracking-[0.25em]">The Treasure Standard™</span>
            </div>
            <h1 className="qru-serif text-5xl md:text-7xl leading-[0.95] tracking-tight font-semibold text-[#1C1C1A]">
              A premium educational<br />publishing house.
            </h1>
            <p className="text-lg text-[#575754] mt-8 leading-relaxed max-w-xl">
              {data.brand?.promise || "Only what has been authorized for release. Every title verified, every page governed at the source."}
            </p>
            <Link to="/catalog" data-testid="hero-browse-catalog"
              className="inline-flex items-center gap-2 mt-10 rounded-full bg-[#1C1C1A] text-[#FAFAF8] px-8 py-3.5 text-sm font-medium transition-colors hover:bg-[#C5A059]">
              Browse the Catalog <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </div>
      </section>

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
                <CoverCard book={hero} index={0} large />
              </div>
            )}
            <div className="lg:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-8">
              {rest.map((b, i) => <CoverCard key={b.id} book={b} index={i + 1} />)}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
