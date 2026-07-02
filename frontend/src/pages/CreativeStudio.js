import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { toast } from "sonner";
import { Palette, Loader2, Wand2, Type, Layers, ShieldCheck, CheckCircle2 } from "lucide-react";

const PALETTE = [
  ["Royal Purple", "#35106A"], ["QRU Gold", "#F5B21A"], ["Deep Navy", "#1F1840"],
  ["White", "#FFFFFF"], ["Soft Gray", "#F3F2F7"],
];
const PRINCIPLES = [
  "Apple simplicity — clarity over decoration",
  "NASA Mission Control transparency",
  "Executive dashboard confidence",
  "Generous spacing & beautiful typography",
  "Consistent QRU Shield & brand voice",
];

export default function CreativeStudio() {
  const [queue, setQueue] = useState([]);
  const [busy, setBusy] = useState("");

  const load = () => api.get("/products/creative-queue").then((r) => setQueue(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const enhance = async (id) => {
    setBusy(id);
    try { await api.post(`/products/${id}/creative-brief`); toast.success("Product page enhanced by Creative Studio"); load(); }
    catch { toast.error("Enhancement failed"); } finally { setBusy(""); }
  };

  return (
    <div>
      <PageHeader
        overline="QRU Creative Studio™"
        title="Center of Excellence for Visual Communication"
        description="Every product passes through the Creative Studio before publication. We own QRU's design standards, master templates, and decision-ready product pages."
      />

      {/* Brand standards */}
      <div className="grid lg:grid-cols-3 gap-4 mb-8">
        <div className="bg-card border rounded-md p-5">
          <div className="flex items-center gap-2 mb-3"><Palette className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">Color System</h3></div>
          <div className="space-y-2">
            {PALETTE.map(([name, hex]) => (
              <div key={name} className="flex items-center gap-3 text-sm">
                <span className="w-6 h-6 rounded-sm border" style={{ backgroundColor: hex }} />
                <span className="font-medium">{name}</span><span className="ml-auto font-mono text-xs text-muted-foreground">{hex}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-card border rounded-md p-5">
          <div className="flex items-center gap-2 mb-3"><Type className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">Typography</h3></div>
          <p className="font-heading text-2xl font-bold">Outfit</p>
          <p className="text-xs text-muted-foreground mb-3">Headings & display</p>
          <p className="text-lg">IBM Plex Sans</p>
          <p className="text-xs text-muted-foreground">Body & UI</p>
        </div>
        <div className="bg-card border rounded-md p-5">
          <div className="flex items-center gap-2 mb-3"><Layers className="w-4 h-4 text-primary" /><h3 className="font-heading font-semibold">Design Principles</h3></div>
          <ul className="space-y-1.5 text-sm">
            {PRINCIPLES.map((p) => <li key={p} className="flex gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-success mt-0.5 shrink-0" />{p}</li>)}
          </ul>
        </div>
      </div>

      {/* Mascot / brand asset */}
      <div className="rounded-md p-6 mb-8 flex items-center gap-5 text-white" style={{ background: "hsl(var(--navy))" }}>
        <img src="/qru-shield-light.png" alt="QRU Shield" className="w-16 h-16 object-contain" />
        <div>
          <p className="overline text-gold mb-1">Master Brand Asset</p>
          <p className="font-heading text-xl font-bold">The QRU Shield</p>
          <p className="text-white/60 text-sm">The primary enterprise logo — applied consistently across every product and surface.</p>
        </div>
      </div>

      {/* Creative Quality Review queue */}
      <div className="flex items-center gap-2 mb-3"><ShieldCheck className="w-4 h-4 text-primary" /><h2 className="font-heading font-semibold text-lg">Creative Quality Review</h2></div>
      <p className="text-sm text-muted-foreground mb-4">Products awaiting a Creative Studio product-page enhancement before publication.</p>
      {queue.length === 0 ? (
        <EmptyState icon={Palette} title="All caught up" description="Every product has passed through the Creative Studio." />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {queue.map((p) => (
            <div key={p.id} data-testid={`creative-queue-${p.id}`} className="bg-card border rounded-md p-5">
              <p className="text-xs text-primary font-medium">{p.product_type}</p>
              <Link to={`/products/${p.id}`} className="font-heading font-semibold leading-snug mt-1 block hover:text-primary line-clamp-2">{p.title}</Link>
              <div className="flex items-center justify-between mt-4">
                <StatusBadge status={p.status} />
                <button data-testid={`enhance-${p.id}`} onClick={() => enhance(p.id)} disabled={busy === p.id}
                  className="flex items-center gap-1.5 text-sm text-primary font-medium hover:underline disabled:opacity-60">
                  {busy === p.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Wand2 className="w-3.5 h-3.5" />} Enhance Page
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
