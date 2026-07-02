import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Loader2, Search as SearchIcon } from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ProductCard, toggleFavorite } from "@/components/consumer-shared";

export default function ConsumerHome() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const [data, setData] = useState({ products: [], categories: [] });
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState("All");

  const load = useCallback(async () => {
    setLoading(true);
    const res = await api.get("/consumer/catalog", { params: q ? { q } : {} });
    setData(res.data);
    setLoading(false);
  }, [q]);

  useEffect(() => { load(); }, [load]);

  const onFav = async (p) => {
    await toggleFavorite(p.id);
    setData((d) => ({ ...d, products: d.products.map((x) => x.id === p.id ? { ...x, favorite: !x.favorite } : x) }));
  };

  const shown = active === "All" ? data.products : data.products.filter((p) => p.family === active);
  const firstName = (user?.name || "there").split(" ")[0];

  return (
    <div>
      <section className="relative overflow-hidden" style={{ background: "linear-gradient(135deg, hsl(var(--royal)), hsl(var(--navy)))" }}>
        <div className="max-w-6xl mx-auto px-6 py-16 sm:py-20 text-white relative z-10">
          <p className="overline mb-3" style={{ color: "hsl(var(--gold))" }}>Quest for Real Understanding</p>
          <h1 className="font-heading text-3xl sm:text-5xl font-bold tracking-tight max-w-2xl leading-[1.1]">
            Welcome back, {firstName}. Let's understand something real today.
          </h1>
          <p className="text-white/70 mt-4 max-w-xl text-base">
            Every QRU lesson turns verified knowledge into understanding you can actually use — clear, beautiful, and worthy of your trust.
          </p>
          <form onSubmit={(e) => { e.preventDefault(); }} className="mt-8 max-w-md relative">
            <SearchIcon className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-navy/40" />
            <input data-testid="hero-search" defaultValue={q}
              onChange={(e) => setParams(e.target.value ? { q: e.target.value } : {})}
              placeholder="Ask a question, e.g. How does the heart work?"
              className="w-full pl-12 pr-4 py-3.5 rounded-full text-navy bg-white outline-none shadow-lg text-sm" />
          </form>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="flex items-center gap-2 flex-wrap mb-8">
          {["All", ...data.categories].map((c) => (
            <button key={c} data-testid={`cat-filter-${c}`} onClick={() => setActive(c)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${active === c ? "text-white" : "bg-muted text-muted-foreground hover:text-foreground"}`}
              style={active === c ? { background: "hsl(var(--royal))" } : {}}>{c}</button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
        ) : shown.length === 0 ? (
          <div className="text-center py-24 text-muted-foreground">
            <p className="font-heading text-lg">No products found{q ? ` for "${q}"` : ""}.</p>
            <p className="text-sm mt-1">New understanding is being manufactured every day.</p>
          </div>
        ) : (
          <div data-testid="catalog-grid" className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {shown.map((p) => <ProductCard key={p.id} p={p} onFav={onFav} />)}
          </div>
        )}
      </div>
    </div>
  );
}
