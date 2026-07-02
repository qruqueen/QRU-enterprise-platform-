import { useNavigate } from "react-router-dom";
import { BookOpen, Star, ShieldCheck, Clock } from "lucide-react";
import api from "@/lib/api";

// Treasure Standard™ ribbon used across the consumer platform.
export function TreasureRibbon() {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border border-gold" style={{ background: "hsl(var(--gold) / 0.12)", color: "hsl(var(--navy))" }}>
      <svg width="10" height="10" viewBox="0 0 24 24" fill="hsl(var(--gold))"><path d="M12 2l2.9 6.1 6.6.9-4.8 4.6 1.2 6.6L12 18.6 6.1 21.8l1.2-6.6L2.5 9l6.6-.9z" /></svg>
      Treasure Standard™
    </span>
  );
}

export function VerifiedPill() {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold" style={{ background: "hsl(var(--success) / 0.12)", color: "hsl(var(--success))" }}>
      <ShieldCheck className="w-3 h-3" /> Kingdom Lion™ Verified
    </span>
  );
}

export function DemoBadge() {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-muted text-muted-foreground border border-border">
      Demo Data
    </span>
  );
}

const FAMILY_TINT = {
  "Heart Health": "244 63 63", "Brain Health": "139 92 246", "Metabolic Health": "16 185 129",
  "Lung Health": "6 182 212", "Kidney Health": "59 130 246", "Cancer Understanding": "245 158 11",
};

export function ProductCard({ p, onFav }) {
  const navigate = useNavigate();
  const tint = FAMILY_TINT[p.family] || "76 29 149";
  const BACKEND = process.env.REACT_APP_BACKEND_URL;
  const cover = p.cover_url ? `${BACKEND}${p.cover_url}` : null;
  return (
    <div data-testid={`product-card-${p.id}`} onClick={() => navigate(`/learn/${p.id}`)}
      className="group cursor-pointer bg-card border border-border rounded-2xl overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200">
      <div className="h-28 relative flex items-center justify-center overflow-hidden" style={{ background: `linear-gradient(135deg, rgb(${tint} / 0.14), rgb(${tint} / 0.04))` }}>
        {cover ? <img src={cover} alt={p.title} className="absolute inset-0 w-full h-full object-cover" />
          : <BookOpen className="w-9 h-9" style={{ color: `rgb(${tint})` }} strokeWidth={1.5} />}
        {onFav && (
          <button data-testid={`fav-btn-${p.id}`} onClick={(e) => { e.stopPropagation(); onFav(p); }}
            className="absolute top-2 right-2 p-1.5 rounded-full bg-white/80 hover:bg-white transition-colors">
            <Star className={`w-4 h-4 ${p.favorite ? "fill-gold text-gold" : "text-muted-foreground"}`} style={p.favorite ? { fill: "hsl(var(--gold))", color: "hsl(var(--gold))" } : {}} />
          </button>
        )}
        {typeof p.progress === "number" && p.progress > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-black/5">
            <div className="h-full" style={{ width: `${p.progress}%`, background: "hsl(var(--gold))" }} />
          </div>
        )}
      </div>
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full" style={{ background: `rgb(${tint} / 0.1)`, color: `rgb(${tint})` }}>{p.family}</span>
          {p.treasure_standard && <TreasureRibbon />}
        </div>
        <h3 className="font-heading font-semibold text-[15px] leading-snug text-foreground group-hover:text-primary transition-colors line-clamp-2">{p.title}</h3>
        <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> 15 min</span>
          <span>{p.product_type}</span>
          {p.is_demo && <DemoBadge />}
        </div>
      </div>
    </div>
  );
}

export async function toggleFavorite(productId) {
  const { data } = await api.post("/consumer/favorite", { product_id: productId });
  return data.favorite;
}
