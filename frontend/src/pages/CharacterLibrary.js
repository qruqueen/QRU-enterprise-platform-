import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Users, Loader2, ShieldCheck, Quote } from "lucide-react";

function Field({ label, value }) {
  if (!value || (Array.isArray(value) && !value.length)) return null;
  return (
    <div className="mb-3">
      <p className="text-[11px] font-semibold tracking-wide text-gold uppercase mb-1">{label}</p>
      {Array.isArray(value) ? (
        <ul className="list-disc pl-4 space-y-0.5 text-sm text-foreground/80">
          {value.map((v, i) => <li key={i}>{typeof v === "string" ? v : v.description || JSON.stringify(v)}</li>)}
        </ul>
      ) : (
        <p className="text-sm text-foreground/80">{value}</p>
      )}
    </div>
  );
}

export default function CharacterLibrary() {
  const [chars, setChars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(null);

  useEffect(() => {
    api.get("/wis/characters").then(({ data }) => setChars(data.characters || [])).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading Character Library…</div>;

  return (
    <div className="space-y-8" data-testid="wis-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <Users className="w-7 h-7 text-gold" /> QRU Workforce Identity System™
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          The permanent Character Library™ — the enterprise source of truth for every QRU Director, mascot, reviewer, and guide.
          Applications <span className="font-semibold text-navy">retrieve</span> these approved characters; they are never replaced with generic AI portraits.
        </p>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {chars.map((c) => (
          <button
            key={c.id}
            data-testid={`character-card-${c.id}`}
            onClick={() => setOpen(c)}
            className="text-left rounded-lg border border-border bg-card overflow-hidden hover:border-gold hover:shadow-lg transition-all group"
          >
            <div className="aspect-square bg-navy overflow-hidden">
              <img src={c.official_portrait} alt={c.name} className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform" />
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between">
                <p className="font-heading font-semibold text-navy text-[15px]">{c.name}</p>
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-1.5 py-0.5">
                  <ShieldCheck className="w-3 h-3" /> {c.treasure_standard_status}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">{c.roles?.[0]} · {c.department}</p>
              <p className="text-xs text-foreground/70 mt-2 line-clamp-2">{c.biography}</p>
              <p className="text-[10px] text-muted-foreground mt-2 font-mono">{c.character_id} · v{c.version}</p>
            </div>
          </button>
        ))}
      </div>

      <Dialog open={!!open} onOpenChange={(v) => !v && setOpen(null)}>
        <DialogContent className="max-w-4xl max-h-[88vh] overflow-y-auto" data-testid="character-dialog">
          {open && (
            <>
              <DialogHeader>
                <p className="overline text-gold text-[10px] font-semibold tracking-widest uppercase">{open.character_id} · Character Record · v{open.version}</p>
                <DialogTitle className="font-heading text-2xl text-navy">{open.name}</DialogTitle>
                <p className="text-sm text-muted-foreground">{open.roles?.join(" · ")} — {open.department}</p>
              </DialogHeader>
              <div className="grid sm:grid-cols-[240px_1fr] gap-6 mt-2">
                <div>
                  <div className="rounded-lg overflow-hidden border border-border bg-navy">
                    <img src={open.official_portrait} alt={open.name} className="w-full object-cover" data-testid="character-portrait" />
                  </div>
                  {open.official_full_body && (
                    <div className="mt-3 rounded-lg overflow-hidden border border-border bg-gradient-to-b from-[#1a1147] to-[#0A1A3F]">
                      <img src={open.official_full_body} alt={`${open.name} full body`} className="w-full object-contain" data-testid="character-full-body" />
                      <p className="text-[10px] text-white/60 text-center pb-1.5">Official Full-Body · Transparent PNG</p>
                    </div>
                  )}
                  <div className="mt-3">
                    <p className="text-[11px] font-semibold tracking-wide text-gold uppercase mb-1">Approved Palette</p>
                    <div className="flex flex-wrap gap-1.5">
                      {open.approved_color_palette?.map((p, i) => {
                        const hex = p.split(" ")[0];
                        return <span key={i} title={p} className="w-6 h-6 rounded-sm border border-border" style={{ background: hex }} />;
                      })}
                    </div>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-3">{open.copyright_status}</p>
                </div>
                <div>
                  {open.catchphrases?.length ? (
                    <div className="mb-3 rounded-sm bg-navy/5 p-2.5 flex items-start gap-2">
                      <Quote className="w-4 h-4 text-gold shrink-0 mt-0.5" />
                      <p className="text-sm italic text-foreground/80">{open.catchphrases.join("  ·  ")}</p>
                    </div>
                  ) : null}
                  <div className="grid sm:grid-cols-2 gap-x-6">
                    <div>
                      <Field label="Biography" value={open.biography} />
                      <Field label="Personality Profile" value={open.personality_profile} />
                      <Field label="Teaching Style" value={open.teaching_style} />
                      <Field label="Voice Style" value={open.voice_style} />
                      <Field label="Responsibilities" value={open.responsibilities} />
                    </div>
                    <div>
                      <Field label="Clothing / Uniform" value={open.clothing_uniform} />
                      <Field label="Facial Expressions" value={open.facial_expressions} />
                      <Field label="Standard Poses" value={open.standard_poses} />
                      <Field label="Iconography" value={open.iconography} />
                      <Field label="Brand Guidelines" value={open.brand_guidelines} />
                      <Field label="Variations Created" value={open.variations?.map(v => `${v.kind}: ${v.description}`)} />
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
