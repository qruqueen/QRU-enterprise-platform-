import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  Loader2, ArrowLeft, ShieldCheck, ChevronDown, Star, CheckCircle2, Award, Layers, Sparkles,
} from "lucide-react";
import api from "@/lib/api";
import { TreasureRibbon, VerifiedPill, DemoBadge, ProductCard, toggleFavorite } from "@/components/consumer-shared";
import { Markdown } from "@/components/shared";

function SectionBody({ s }) {
  const v = s.value;
  if (s.kind === "highlight") {
    return (
      <div className="rounded-2xl p-6 text-white" style={{ background: "linear-gradient(135deg, hsl(var(--royal)), hsl(var(--navy)))" }}>
        <p className="overline mb-2" style={{ color: "hsl(var(--gold))" }}>{s.label}</p>
        <p className="font-heading text-xl font-semibold leading-snug">{v}</p>
      </div>
    );
  }
  if (s.kind === "vocab" && Array.isArray(v)) {
    return (
      <dl className="grid sm:grid-cols-2 gap-3">
        {v.map((t, i) => (
          <div key={i} className="border border-border rounded-xl p-3">
            <dt className="font-semibold text-sm">{t.term}</dt>
            <dd className="text-sm text-muted-foreground mt-0.5">{t.definition}</dd>
          </div>
        ))}
      </dl>
    );
  }
  if (s.kind === "list" && Array.isArray(v)) {
    return (
      <ul className="space-y-2.5">
        {v.map((it, i) => (
          <li key={i} className="flex gap-3 text-[15px] leading-relaxed">
            <span className="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-heading font-bold" style={{ background: "hsl(var(--gold) / 0.15)", color: "hsl(var(--navy))" }}>{i + 1}</span>
            <span>{typeof it === "object" ? JSON.stringify(it) : it}</span>
          </li>
        ))}
      </ul>
    );
  }
  return <p className="text-[15px] leading-relaxed text-foreground whitespace-pre-wrap">{v}</p>;
}

const LAYER_ICONS = [Sparkles, Layers, ShieldCheck, Award];

export default function ConsumerLearn() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [layer, setLayer] = useState(0);
  const [mode, setMode] = useState(null);
  const [showRefs, setShowRefs] = useState(false);
  const [fav, setFav] = useState(false);
  const [progress, setProgress] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/consumer/products/${id}`);
      setD(data);
      setFav(data.enrollment?.favorite || false);
      setProgress(data.enrollment?.progress || 0);
      // auto-enroll on open
      await api.post("/consumer/enroll", { product_id: id });
    } catch {
      toast.error("This lesson isn't available.");
      navigate("/learn");
    }
    setLoading(false);
  }, [id, navigate]);

  useEffect(() => { load(); }, [load]);

  const onFav = async () => { setFav(await toggleFavorite(id)); };

  const complete = async () => {
    const { data } = await api.post("/consumer/progress", { product_id: id, progress: 100 });
    setProgress(100);
    if (data.certificate) toast.success("Lesson complete! Certificate earned 🎓");
    else toast.success("Lesson marked complete!");
  };

  if (loading) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (!d) return null;

  const { product: p, understanding: u, related } = d;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <button data-testid="learn-back" onClick={() => navigate("/learn")} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to Discover
      </button>

      {/* Hero */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <span className="text-[11px] uppercase tracking-wider font-semibold text-primary">{p.family}</span>
          {p.treasure_standard && <TreasureRibbon />}
          {u?.verification?.status === "Verified" && <VerifiedPill />}
          {p.is_demo && <DemoBadge />}
        </div>
        <div className="flex items-start justify-between gap-4">
          <h1 data-testid="learn-title" className="font-heading text-3xl sm:text-4xl font-bold tracking-tight text-foreground leading-tight">{p.title}</h1>
          <button data-testid="learn-fav" onClick={onFav} className="shrink-0 p-2 rounded-full border border-border hover:border-gold transition-colors">
            <Star className="w-5 h-5" style={fav ? { fill: "hsl(var(--gold))", color: "hsl(var(--gold))" } : { color: "hsl(var(--muted-foreground))" }} />
          </button>
        </div>
        {progress > 0 && (
          <div className="mt-4 h-2 rounded-full bg-muted overflow-hidden max-w-xs">
            <div className="h-full transition-all" style={{ width: `${progress}%`, background: "hsl(var(--gold))" }} />
          </div>
        )}
      </div>

      {!u ? (
        <div className="bg-card border rounded-2xl p-6"><Markdown text={p.content} /></div>
      ) : (
        <>
          {/* Kingdom Lion Verification */}
          <div className="bg-card border border-border rounded-2xl p-5 mb-8" data-testid="verification-card">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: "hsl(var(--success) / 0.12)" }}>
                  <ShieldCheck className="w-5 h-5" style={{ color: "hsl(var(--success))" }} />
                </div>
                <div>
                  <p className="font-heading font-semibold text-sm">Kingdom Lion™ Verification</p>
                  <p className="text-xs text-muted-foreground">Evidence level: {u.verification.evidence_level} · Confidence {u.verification.confidence_score}%{u.verification.reviewer ? ` · Reviewed by ${u.verification.reviewer}` : ""}</p>
                </div>
              </div>
              {(u.verification.references?.length > 0 || u.verification.sources?.length > 0) && (
                <button data-testid="toggle-refs" onClick={() => setShowRefs(!showRefs)} className="flex items-center gap-1 text-xs text-primary font-medium">
                  References <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showRefs ? "rotate-180" : ""}`} />
                </button>
              )}
            </div>
            {showRefs && (
              <div className="mt-4 pt-4 border-t border-border grid sm:grid-cols-2 gap-2 text-xs text-muted-foreground">
                {[...(u.verification.references || []), ...(u.verification.sources || [])].map((r, i) => (
                  <p key={i} className="flex gap-1.5"><span className="text-primary">•</span>{r}</p>
                ))}
              </div>
            )}
          </div>

          {/* Layered Understanding selector */}
          {u.layers.length > 0 && (
            <div className="mb-6">
              <p className="overline text-primary mb-3">Choose your depth</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {u.layers.map((L, i) => {
                  const Icon = LAYER_ICONS[i] || Layers;
                  return (
                    <button key={i} data-testid={`layer-btn-${i}`} onClick={() => setLayer(i)}
                      className={`text-left p-3 rounded-xl border transition-all ${layer === i ? "border-primary bg-secondary" : "border-border hover:border-primary/40"}`}>
                      <Icon className={`w-4 h-4 mb-1.5 ${layer === i ? "text-primary" : "text-muted-foreground"}`} />
                      <p className={`text-xs font-semibold leading-tight ${layer === i ? "text-primary" : "text-foreground"}`}>{L.title}</p>
                    </button>
                  );
                })}
              </div>
              <div className="mt-4 bg-card border border-border rounded-2xl p-5" data-testid="layer-content">
                <p className="text-xs text-muted-foreground mb-3 italic">{u.layers[layer].subtitle}</p>
                <div className="space-y-4">
                  {u.layers[layer].parts.map((part, i) => (
                    <div key={i}>
                      {Array.isArray(part.value)
                        ? <ul className="space-y-1.5 text-[15px]">{part.value.map((x, j) => <li key={j} className="flex gap-2"><span className="text-gold">•</span>{typeof x === "object" ? (x.term ? `${x.term}: ${x.definition}` : JSON.stringify(x)) : x}</li>)}</ul>
                        : <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{part.value}</p>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Learning modes */}
          {u.learning_modes.length > 0 && (
            <div className="mb-8">
              <p className="overline text-primary mb-3">Learning style</p>
              <div className="flex items-center gap-2 flex-wrap">
                {u.learning_modes.map((m) => (
                  <button key={m.key} data-testid={`mode-btn-${m.key}`} onClick={() => setMode(mode === m.key ? null : m.key)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${mode === m.key ? "text-white" : "bg-muted text-muted-foreground hover:text-foreground"}`}
                    style={mode === m.key ? { background: "hsl(var(--navy))" } : {}}>{m.label}</button>
                ))}
              </div>
              {mode && (
                <div className="mt-3 bg-secondary border border-border rounded-2xl p-5" data-testid="mode-content">
                  <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{u.learning_modes.find((m) => m.key === mode)?.content}</p>
                </div>
              )}
            </div>
          )}

          {/* Full QRU educational structure */}
          <p className="overline text-primary mb-4">The full lesson</p>
          <div className="space-y-5">
            {u.sections.map((s) => (
              <div key={s.id} data-testid={`section-${s.id}`}>
                {s.kind !== "highlight" && <p className="font-heading text-sm font-bold text-navy mb-2" style={{ color: "hsl(var(--navy))" }}>{s.label}</p>}
                <SectionBody s={s} />
              </div>
            ))}
          </div>

          {/* Completion */}
          <div className="mt-10 rounded-2xl border border-gold p-6 text-center" style={{ background: "hsl(var(--gold) / 0.06)" }}>
            {progress >= 100 ? (
              <div className="flex flex-col items-center gap-2">
                <CheckCircle2 className="w-8 h-8" style={{ color: "hsl(var(--success))" }} />
                <p className="font-heading font-semibold">You've completed this lesson.</p>
                <button data-testid="view-certificates" onClick={() => navigate("/learn/certificates")} className="text-sm text-primary font-medium mt-1">View your certificate →</button>
              </div>
            ) : (
              <div>
                <p className="font-heading font-semibold mb-1">Finished understanding this?</p>
                <p className="text-sm text-muted-foreground mb-4">Mark it complete to track your progress and earn a certificate.</p>
                <button data-testid="mark-complete" onClick={complete}
                  className="px-6 py-2.5 rounded-full text-white font-medium text-sm" style={{ background: "hsl(var(--royal))" }}>Mark Complete</button>
              </div>
            )}
          </div>
        </>
      )}

      {related?.length > 0 && (
        <div className="mt-14">
          <h2 className="font-heading text-lg font-bold mb-4">Related QRU Topics™</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((r) => <ProductCard key={r.id} p={r} />)}
          </div>
        </div>
      )}
    </div>
  );
}
