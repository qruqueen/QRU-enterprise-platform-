import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, Factory, Database, Plus, ArrowDown, ArrowRight, Sparkles, Lock,
  BookOpen, GraduationCap, Wrench, Video, Gift, Boxes, Layers,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

const EXP_ICON = {
  book: BookOpen, "graduation-cap": GraduationCap, toolbox: Wrench, video: Video,
  gift: Gift, boxes: Boxes, layers: Layers,
};

const PRINCIPLES = [
  ["One Governed Catalog", "QRU Store™ is the single source of truth. The Factory publishes to the catalog; the catalog distributes to experiences."],
  ["Automatic Distribution", "Every product type has recommended destinations. Publishing auto-selects them — the Founder can override anytime."],
  ["Experiences are Plug-ins", "A customer experience registers itself and starts consuming the catalog. Adding one never changes the Factory."],
];

function ExperienceCard({ e }) {
  const Icon = EXP_ICON[e.icon] || Boxes;
  return (
    <div className="rounded-lg border bg-card p-4" data-testid={`exp-${e.id}`}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-navy" />
        <span className="font-heading font-bold text-navy text-sm">{e.name}</span>
        {e.protected && <span title="Preserved as-is"><Lock className="w-3 h-3 text-emerald-600" /></span>}
        {!e.builtin && <span className="text-[10px] rounded-full bg-gold/20 text-navy px-2 py-0.5 font-semibold">Registered</span>}
      </div>
      <div className="text-[11px] text-muted-foreground">{e.description}</div>
      <div className="text-[10px] text-royal mt-1">Audience: {e.audience || "—"}</div>
    </div>
  );
}

export default function DistributionArchitecture() {
  const [exps, setExps] = useState(null);
  const [map, setMap] = useState(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ id: "", name: "", description: "", audience: "" });
  const [saving, setSaving] = useState(false);

  const load = () => {
    Promise.all([
      api.get("/distribution-architecture/experiences"),
      api.get("/distribution-architecture/destinations-map"),
    ]).then(([a, b]) => { setExps(a.data.experiences); setMap(b.data); })
      .catch(() => { setExps(false); toast.error("Failed to load distribution architecture."); });
  };
  useEffect(() => { load(); }, []);

  const register = async () => {
    if (!form.id || !form.name) { toast.error("Give the experience an id and a name."); return; }
    setSaving(true);
    try {
      const { data } = await api.post("/distribution-architecture/experiences", { ...form });
      if (data.error) toast.error(data.error);
      else { toast.success(`Registered ${data.experience.name} — no Factory change needed.`); setOpen(false); setForm({ id: "", name: "", description: "", audience: "" }); load(); }
    } catch (e) { toast.error(e.response?.data?.detail || "Registration failed."); }
    setSaving(false);
  };

  if (exps === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>;
  if (exps === false) return <div className="text-sm text-muted-foreground py-16 text-center">Unable to load.</div>;

  return (
    <div className="space-y-6" data-testid="distribution-architecture">
      <PageHeader title="Distribution Architecture™" subtitle="One governed catalog, many customer experiences. The Factory publishes once; the catalog distributes everywhere." />

      {/* Principles */}
      <div className="grid md:grid-cols-3 gap-3">
        {PRINCIPLES.map(([t, d], i) => (
          <div key={i} className="rounded-xl border-2 border-gold/30 bg-gold/[0.05] p-4" data-testid={`principle-${i}`}>
            <div className="flex items-center gap-2 mb-1"><Sparkles className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy text-sm">{t}</span></div>
            <div className="text-[12px] text-muted-foreground">{d}</div>
          </div>
        ))}
      </div>

      {/* Three-layer flow */}
      <section className="rounded-xl border bg-card p-5" data-testid="layer-flow">
        <div className="flex flex-col items-center gap-3">
          <div className="w-full max-w-md rounded-lg border-2 border-navy/25 bg-navy/[0.04] p-3 text-center">
            <div className="flex items-center justify-center gap-2 text-navy font-heading font-bold text-sm"><Factory className="w-4 h-4" /> QRU Factory™</div>
            <div className="text-[11px] text-muted-foreground">Manufactures + governs · hidden from customers</div>
          </div>
          <ArrowDown className="w-4 h-4 text-muted-foreground" />
          <div className="w-full max-w-md rounded-lg border-2 border-gold/40 bg-gold/[0.08] p-3 text-center">
            <div className="flex items-center justify-center gap-2 text-navy font-heading font-bold text-sm"><Database className="w-4 h-4" /> QRU Store™ — governed catalog + distribution</div>
            <div className="text-[11px] text-muted-foreground">Single source of truth · fans out by destination</div>
          </div>
          <ArrowDown className="w-4 h-4 text-muted-foreground" />
          <div className="w-full grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
            {exps.map((e) => {
              const Icon = EXP_ICON[e.icon] || Boxes;
              return (
                <div key={e.id} className="rounded-lg border bg-card p-2 text-center" data-testid={`flow-exp-${e.id}`}>
                  <Icon className="w-4 h-4 text-royal mx-auto" />
                  <div className="text-[11px] font-semibold text-navy mt-1">{e.name}</div>
                </div>
              );
            })}
          </div>
          <div className="text-[11px] text-muted-foreground">↓ Customer</div>
        </div>
      </section>

      {/* Experiences (plug-ins) */}
      <section className="rounded-xl border bg-card p-5" data-testid="experiences-section">
        <div className="flex items-center justify-between gap-3 mb-4">
          <div>
            <div className="font-heading font-bold text-navy">Customer Experiences (plug-ins)</div>
            <div className="text-[12px] text-muted-foreground">Each consumes the same catalog. Register a new one and it works immediately — the Factory never changes.</div>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <button data-testid="register-experience-btn" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90">
                <Plus className="w-4 h-4" /> Register Experience
              </button>
            </DialogTrigger>
            <DialogContent data-testid="register-dialog">
              <DialogHeader><DialogTitle>Register a Customer Experience</DialogTitle></DialogHeader>
              <div className="space-y-3">
                <Input data-testid="exp-id-input" placeholder="id (e.g. qru-academy)" value={form.id} onChange={(e) => setForm({ ...form, id: e.target.value })} />
                <Input data-testid="exp-name-input" placeholder="Name (e.g. QRU Academy™)" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
                <Input data-testid="exp-desc-input" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                <Input data-testid="exp-audience-input" placeholder="Audience" value={form.audience} onChange={(e) => setForm({ ...form, audience: e.target.value })} />
                <p className="text-[11px] text-muted-foreground">This adds a new destination the whole Factory can publish to — with zero engine changes.</p>
              </div>
              <DialogFooter>
                <button onClick={register} disabled={saving} data-testid="exp-save-btn" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Register
                </button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {exps.map((e) => <ExperienceCard key={e.id} e={e} />)}
        </div>
      </section>

      {/* Automatic Distribution map */}
      <section className="rounded-xl border bg-card p-5" data-testid="distribution-map">
        <div className="font-heading font-bold text-navy mb-1">Automatic Distribution™ — default destinations</div>
        <div className="text-[12px] text-muted-foreground mb-4">When you publish, the Factory auto-selects these destinations by product type. You can override any product before or after publishing.</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-[11px] uppercase text-muted-foreground border-b">
              <th className="py-2 pr-4">Product Type</th><th className="py-2">Default Destinations</th>
            </tr></thead>
            <tbody>
              {(map?.map || []).map((r) => (
                <tr key={r.product_type} className="border-b last:border-0" data-testid={`map-row-${r.product_type}`}>
                  <td className="py-2 pr-4 font-medium text-foreground">{r.product_type}</td>
                  <td className="py-2">
                    <div className="flex flex-wrap gap-1.5">
                      {r.destinations.map((d) => (
                        <span key={d.id} className="inline-flex items-center gap-1 text-[11px] rounded-full bg-navy/10 text-navy px-2.5 py-1 font-medium">
                          <ArrowRight className="w-3 h-3" />{d.name}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
