import { Link, Outlet, useLocation } from "react-router-dom";
import { BookOpen, ShieldCheck } from "lucide-react";

export default function PublicLayout() {
  const { pathname } = useLocation();
  return (
    <div className="qru-paper qru-sans min-h-screen text-[#1C1C1A] flex flex-col" data-testid="qru-online-root">
      <header className="sticky top-0 z-40 bg-[#FAFAF8]/70 backdrop-blur-xl border-b border-[#E5E5E0]/70">
        <div className="max-w-7xl mx-auto px-6 md:px-10 h-20 flex items-center justify-between">
          <Link to="/" data-testid="qru-logo" className="group flex items-center gap-3">
            <span className="w-9 h-9 rounded-full bg-[#1C1C1A] text-[#FAFAF8] grid place-items-center transition-colors group-hover:bg-[#C5A059]">
              <BookOpen className="w-4 h-4" />
            </span>
            <span className="qru-serif text-2xl font-semibold tracking-tight leading-none">
              QRU <span className="text-[#C5A059]">Online</span>
            </span>
          </Link>
          <nav className="flex items-center gap-8 text-sm">
            <Link to="/" data-testid="nav-home"
              className={`transition-colors hover:text-[#C5A059] ${pathname === "/" ? "text-[#1C1C1A]" : "text-[#575754]"}`}>Home</Link>
            <Link to="/catalog" data-testid="nav-catalog"
              className={`transition-colors hover:text-[#C5A059] ${pathname.startsWith("/catalog") ? "text-[#1C1C1A]" : "text-[#575754]"}`}>Catalog</Link>
            <Link to="/login" data-testid="nav-founder-login"
              className="hidden sm:inline-flex items-center rounded-full border border-[#C5A059] text-[#C5A059] px-4 py-1.5 text-xs uppercase tracking-[0.15em] transition-colors hover:bg-[#C5A059] hover:text-[#FAFAF8]">
              Founder Login
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="bg-[#0A1128] text-[#FDFBF7] mt-24" data-testid="qru-footer">
        <div className="max-w-7xl mx-auto px-6 md:px-10 py-20 grid md:grid-cols-3 gap-12">
          <div className="md:col-span-2">
            <div className="inline-flex items-center gap-2 text-[#D4AF37] mb-4">
              <ShieldCheck className="w-5 h-5" />
              <span className="text-xs uppercase tracking-[0.2em]">The Treasure Standard™</span>
            </div>
            <p className="qru-serif text-3xl md:text-4xl leading-tight max-w-xl">
              Carefully researched, thoughtfully written, and verified.
            </p>
            <p className="text-[#9BA3B5] mt-4 max-w-lg text-sm leading-relaxed">
              QRU Online presents only what has been authorized for release by QRU Press™.
              Knowledge is governed at the source and published with evidence.
            </p>
          </div>
          <div className="flex flex-col gap-3 text-sm">
            <span className="text-xs uppercase tracking-[0.2em] text-[#9BA3B5] mb-1">Explore</span>
            <Link to="/" className="hover:text-[#D4AF37] transition-colors">Home</Link>
            <Link to="/catalog" className="hover:text-[#D4AF37] transition-colors">Books Catalog</Link>
            <Link to="/privacy" data-testid="footer-privacy" className="hover:text-[#D4AF37] transition-colors">Privacy</Link>
          </div>
        </div>
        <div className="border-t border-[#1E2943]">
          <div className="max-w-7xl mx-auto px-6 md:px-10 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[#9BA3B5]">
            <span>© {new Date().getFullYear()} QRU Press™ · Ascend Development Group LLC</span>
            <span className="qru-serif text-base text-[#FDFBF7]">QRU <span className="text-[#D4AF37]">Online</span></span>
          </div>
        </div>
      </footer>
    </div>
  );
}
