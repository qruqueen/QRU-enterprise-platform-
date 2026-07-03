import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Crown, ShieldCheck } from "lucide-react";

// Enterprise Director cards that render the APPROVED QRU visual identity from the
// Workforce Identity System™ (WIS). Any surface reuses this instead of generating art.
export function DirectorRoster() {
  const [chars, setChars] = useState([]);

  useEffect(() => {
    api.get("/wis/characters").then(({ data }) => setChars(data.characters || [])).catch(() => {});
  }, []);

  if (!chars.length) return null;

  return (
    <div data-testid="director-roster">
      <p className="overline text-primary mb-3 flex items-center gap-2"><Crown className="w-4 h-4" /> QRU AI Directors — Official Identity (Workforce Identity System™)</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {chars.map((c) => (
          <div key={c.id} data-testid={`director-card-${c.id}`}
            className="relative rounded-lg overflow-hidden border border-white/10 bg-gradient-to-b from-[#1a1147] to-[#0A1A3F] group">
            <div className="aspect-[3/4] flex items-end justify-center overflow-hidden">
              <img src={c.official_full_body || c.official_portrait} alt={c.name}
                className="h-full w-full object-contain object-bottom drop-shadow-[0_8px_24px_rgba(0,0,0,0.5)] group-hover:scale-[1.04] transition-transform"
                data-testid={`director-art-${c.id}`} />
            </div>
            <div className="absolute top-1.5 right-1.5 inline-flex items-center gap-0.5 text-[8px] text-gold bg-black/40 border border-gold/40 rounded-full px-1.5 py-0.5">
              <ShieldCheck className="w-2.5 h-2.5" /> Approved
            </div>
            <div className="p-2 bg-black/30 backdrop-blur-sm">
              <p className="font-heading font-semibold text-white text-[12px] leading-tight truncate">{c.name}</p>
              <p className="text-[10px] text-gold/90 truncate">{c.roles?.[0]}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
