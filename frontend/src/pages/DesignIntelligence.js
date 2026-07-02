import { useEffect, useState } from "react";
import { Loader2, Palette, Library, Layers, Search, Sparkles, CheckCircle2, Type, Grid3x3 } from "lucide-react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";

const TABS = [
  { key: "brand", label: "Brand Library™", icon: Palette },
  { key: "design", label: "Design Library™", icon: Library },
  { key: "assets", label: "Master Assets™", icon: Grid3x3 },
  { key: "language", label: "Design Language™", icon: Type },
  { key: "autonomy", label: "Studio Autonomy", icon: Sparkles },
];

export default function DesignIntelligence() {
  const [tab, setTab] = useState("brand");
  const [stats, setStats] = useState(null);
  const [brand, setBrand] = useState(null);
  const [refs, setRefs] = useState([]);
  const [assets, setAssets] = useState([]);
  const [principles, setPrinciples] = useState([]);
  const [q, setQ] = useState("");
  const [rec, setRec] = useState(null);
  const [recType, setRecType] = useState("Poster");
  const [recAud, setRecAud] = useState("Children");

  useEffect(() => {
    api.get("/design/stats").then((r) => setStats(r.data));
    api.get("/design/brand-library").then((r) => setBrand(r.data));
    api.get("/design/design-library").then((r) => setRefs(r.data.references));
    api.get("/design/master-assets").then((r) => setAssets(r.data.assets));
    api.get("/design/design-language").then((r) => setPrinciples(r.data.principles));
  }, []);

  const searchAssets = async (val) => {
    setQ(val);
    const { data } = await api.get("/design/master-assets", { params: val ? { q: val } : {} });
    setAssets(data.assets);
  };

  const recommend = async () => {
    const { data } = await api.get("/design/recommend-templates", { params: { product_type: recType, audience: recAud } });
    setRec(data);
  };

  if (!brand) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div>
      <PageHeader overline="Creative Studio™ · Enterprise Mode" title="QRU Design Intelligence™"
        description="Creative Studio learns the QRU Design Language™ so every future product feels unmistakably QRU — original, never copied." />

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[["Design References", stats.design_references], ["Master Assets", stats.master_assets], ["Design Principles", stats.design_principles], ["Brand Standards", stats.brand_standards]].map(([l, v]) => (
            <div key={l} className="bg-card border rounded-xl p-4"><p className="font-heading text-2xl font-bold">{v}</p><p className="text-[11px] text-muted-foreground">{l}</p></div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-1.5 flex-wrap mb-6 border-b border-border">
        {TABS.map((t) => (
          <button key={t.key} data-testid={`di-tab-${t.key}`} onClick={() => setTab(t.key)}
            className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${tab === t.key ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>

      {tab === "brand" && (
        <div className="space-y-8" data-testid="di-brand">
          <div>
            <p className="overline text-primary mb-3">Color System</p>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {brand.colors?.map((c) => (
                <div key={c.name} className="rounded-xl overflow-hidden border">
                  <div className="h-16" style={{ background: `hsl(${c.hsl})` }} />
                  <div className="p-2"><p className="text-xs font-semibold">{c.name}</p><p className="text-[10px] text-muted-foreground">{c.role} · {c.hex}</p></div>
                </div>
              ))}
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-6">
            <div>
              <p className="overline text-primary mb-3">Typography</p>
              {brand.typography?.map((t) => (
                <div key={t.name} className="bg-card border rounded-xl p-4 mb-2">
                  <p className="font-heading text-lg font-bold">{t.name}</p>
                  <p className="text-xs text-muted-foreground">{t.role} · weights {t.weights?.join(", ")}</p>
                </div>
              ))}
            </div>
            <div>
              <p className="overline text-primary mb-3">Design Principles</p>
              <ul className="space-y-1.5 text-sm">{brand.principles?.map((p, i) => <li key={i} className="flex gap-2"><CheckCircle2 className="w-4 h-4 shrink-0" style={{ color: "hsl(var(--success))" }} />{p}</li>)}</ul>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-6">
            <div>
              <p className="overline text-primary mb-3">Components</p>
              <div className="space-y-1.5">{brand.components?.map((c) => <div key={c.name} className="bg-card border rounded-lg p-3"><p className="text-sm font-semibold">{c.name}</p><p className="text-xs text-muted-foreground">{c.use}</p></div>)}</div>
            </div>
            <div>
              <p className="overline text-primary mb-3">Templates</p>
              <div className="space-y-1.5">{brand.templates?.map((t) => <div key={t.name} className="bg-card border rounded-lg p-3"><p className="text-sm font-semibold">{t.name}</p><p className="text-xs text-muted-foreground">For: {t.for?.join(", ")}</p></div>)}</div>
            </div>
          </div>
        </div>
      )}

      {tab === "design" && (
        <div data-testid="di-design">
          <p className="text-sm text-muted-foreground mb-4">Every Treasure Standard™ product becomes a reusable design reference. The more QRU creates, the smarter Creative Studio becomes.</p>
          {refs.length === 0 ? <p className="text-muted-foreground py-12 text-center">No references yet — certify products to grow the library.</p> : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {refs.map((r) => (
                <div key={r.id} className="bg-card border rounded-xl overflow-hidden" data-testid={`di-ref-${r.id}`}>
                  <div className="h-24 flex items-center justify-center" style={{ background: "hsl(var(--secondary))" }}><img src={r.preview} alt="" className="w-10 h-10 object-contain" /></div>
                  <div className="p-3">
                    <p className="text-sm font-semibold line-clamp-1">{r.title}</p>
                    <p className="text-[11px] text-muted-foreground">{r.product_type} · {r.template || "QRU Template"}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "assets" && (
        <div data-testid="di-assets">
          <div className="relative max-w-md mb-4">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input data-testid="di-asset-search" value={q} onChange={(e) => searchAssets(e.target.value)} placeholder="Search assets, keywords, IDs…"
              className="w-full pl-9 pr-3 py-2 text-sm bg-muted rounded-md border border-transparent focus:border-primary outline-none" />
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {assets.map((a) => (
              <div key={a.id} className="bg-card border rounded-xl p-3 flex gap-3" data-testid={`di-asset-${a.id}`}>
                <img src={a.preview} alt="" className="w-10 h-10 object-contain shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-semibold line-clamp-1">{a.title}</p>
                  <p className="text-[10px] text-muted-foreground">{a.asset_id}</p>
                  <p className="text-[11px] text-muted-foreground">{a.category} · {a.product_family} · {a.license_status}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "language" && (
        <div data-testid="di-language">
          <p className="text-sm text-muted-foreground mb-4">The evolving QRU Design Language™ — baseline standards plus principles learned from approved products.</p>
          <div className="space-y-2">
            {principles.map((p) => (
              <div key={p.id} className="bg-card border rounded-xl p-4 flex items-start gap-3">
                <span className={`text-[10px] px-2 py-0.5 rounded-full shrink-0 mt-0.5 ${p.category === "Learned" ? "bg-gold/15" : "bg-secondary text-primary"}`} style={p.category === "Learned" ? { color: "hsl(var(--navy))" } : {}}>{p.category}</span>
                <div><p className="text-sm">{p.principle}</p><p className="text-[11px] text-muted-foreground mt-0.5">Source: {p.source}</p></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "autonomy" && (
        <div data-testid="di-autonomy">
          <p className="text-sm text-muted-foreground mb-4">Creative Studio automatically selects the right template, palette, typography, and illustration style — no manual selection needed.</p>
          <div className="bg-card border rounded-2xl p-5 max-w-2xl">
            <div className="grid sm:grid-cols-2 gap-3 mb-4">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Product Type</label>
                <select data-testid="di-rec-type" value={recType} onChange={(e) => setRecType(e.target.value)} className="w-full px-3 py-2 text-sm bg-muted rounded-md border outline-none">
                  {["Book", "Workbook", "Poster", "Infographic", "Presentation", "Teacher Guide", "Caregiver Guide", "Course", "Interactive Lesson", "Quiz", "Flash Cards", "Video Script"].map((t) => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Audience</label>
                <select data-testid="di-rec-aud" value={recAud} onChange={(e) => setRecAud(e.target.value)} className="w-full px-3 py-2 text-sm bg-muted rounded-md border outline-none">
                  {["Children", "Teens", "General public", "Professionals", "Caregivers", "Teachers"].map((a) => <option key={a}>{a}</option>)}
                </select>
              </div>
            </div>
            <button data-testid="di-recommend" onClick={recommend} className="px-5 py-2 rounded-md text-white text-sm font-medium" style={{ background: "hsl(var(--royal))" }}>Auto-Select Design</button>
            {rec && (
              <div className="mt-5 grid sm:grid-cols-2 gap-3 text-sm" data-testid="di-rec-result">
                {[["Cover Template", rec.cover_template], ["Layout", rec.layout], ["Illustration", rec.illustration_style], ["Palette", rec.palette], ["Typography", rec.typography], ["Tone", rec.tone], ["Icon Set", rec.icon_set], ["Brand Elements", rec.brand_elements?.join(", ")]].map(([l, v]) => (
                  <div key={l} className="border rounded-lg p-3"><p className="text-[11px] text-muted-foreground">{l}</p><p className="font-medium">{v}</p></div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
