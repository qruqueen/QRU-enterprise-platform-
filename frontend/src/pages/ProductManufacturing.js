import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Markdown } from "@/components/shared";
import { toast } from "sonner";
import { Sparkles, Loader2, Factory, ArrowRight, Package, ShieldCheck, Star, Wand2, UserCog } from "lucide-react";

const PRODUCT_TYPES = ["Book", "Poster", "Infographic", "Presentation", "Teacher Guide", "Caregiver Guide", "Workbook", "Lesson Plan", "Video Script", "Podcast Script", "Short-form Content", "Interactive Lesson", "AI Tutor", "Course", "Certificate", "Flash Cards", "Quiz", "Printable PDF"];
const BACKEND = process.env.REACT_APP_BACKEND_URL;
const absU = (u) => (u ? (u.startsWith("http") ? u : `${BACKEND}${u}`) : null);
const TS_STATUSES = ["Treasure Standard™ Approved", "Founder Approved", "Brand Approved"];

export default function ProductManufacturing() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [krId, setKrId] = useState(params.get("kr") || "");
  const [topic, setTopic] = useState("");
  const [productType, setProductType] = useState("Poster");
  const [audience, setAudience] = useState("General public");
  const [level, setLevel] = useState("Introductory");
  const [loading, setLoading] = useState(false);
  const [assembling, setAssembling] = useState(false);
  const [result, setResult] = useState(null);
  const [recipes, setRecipes] = useState({});
  // MT-029 — Founder Asset Selection™
  const [assetMode, setAssetMode] = useState("director"); // director | use_imported | generate
  const [assets, setAssets] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [selectedAssetId, setSelectedAssetId] = useState(null);

  useEffect(() => {
    api.get("/knowledge-records").then((r) => setRecords(r.data)).catch(() => {});
    api.get("/products/recipes").then((r) => setRecipes(r.data.recipes || {})).catch(() => {});
    api.get("/vault/assets", { params: { selectable: true } }).then((r) => setAssets(r.data.assets)).catch(() => {});
  }, []);

  // Intelligent recommendations based on the selected record's family/topic.
  useEffect(() => {
    const rec = records.find((r) => r.id === krId);
    const fam = rec?.family || rec?.college;
    const tpc = rec?.title || topic;
    if (!fam && !tpc) { setRecommended([]); return; }
    api.get("/vault/recommend", { params: { product_family: fam, topic: tpc } })
      .then((r) => setRecommended(r.data.assets)).catch(() => setRecommended([]));
  }, [krId, topic, records]);

  const assetPayload = () => (assetMode === "use_imported" && selectedAssetId
    ? { asset_mode: "use_imported", asset_vault_id: selectedAssetId }
    : { asset_mode: assetMode });

  const generate = async () => {
    if (!krId && !topic) return toast.error("Select a Knowledge Record or enter a topic");
    if (assetMode === "use_imported" && !selectedAssetId) return toast.error("Select an imported asset, or change the asset option");
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post("/products/generate", {
        knowledge_record_id: krId || null,
        topic: topic || null,
        product_type: productType,
        audience,
        learning_level: level,
        ...assetPayload(),
      });
      setResult(data);
      toast.success(`Manufactured ${data.product_code}`);
    } catch { toast.error("Manufacturing failed"); } finally { setLoading(false); }
  };

  const assemble = async () => {
    if (!krId) return toast.error("Select a Knowledge Record to assemble from");
    if (assetMode === "use_imported" && !selectedAssetId) return toast.error("Select an imported asset, or change the asset option");
    setAssembling(true);
    setResult(null);
    try {
      const { data } = await api.post("/products/assemble", {
        knowledge_record_id: krId, product_type: productType, ...assetPayload(),
      });
      setResult(data);
      toast.success(`Assembled ${data.product_code} from existing fields`);
    } catch (e) { toast.error(e.response?.data?.detail || "Assembly failed"); } finally { setAssembling(false); }
  };

  const hasRecipe = !!recipes[productType];

  return (
    <div>
      <PageHeader
        overline="Product Manufacturing Center"
        title="Manufacture a Product"
        description="Turn verified knowledge into publication-ready products. The Manufacturing Director™ generates full content using GPT-5.5."
      />

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="bg-card border rounded-md p-6 space-y-4 lg:sticky lg:top-24 h-fit">
          <div>
            <label className="text-sm font-medium">Source Knowledge Record</label>
            <select data-testid="pm-kr-select" value={krId} onChange={(e) => setKrId(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary text-sm">
              <option value="">— None (use topic) —</option>
              {records.map((r) => <option key={r.id} value={r.id}>{r.kr_code} · {r.title}</option>)}
            </select>
          </div>

          {/* MT-029 — Founder Asset Selection™ */}
          <div data-testid="pm-asset-selection" className="border-t pt-4">
            <label className="text-sm font-medium flex items-center gap-1.5"><Package className="w-4 h-4 text-gold" /> Founder Asset Selection™</label>
            <p className="text-[11px] text-muted-foreground mb-2">Manufacture using an approved imported asset — or let the factory generate one.</p>
            <div className="space-y-1.5 mb-2">
              {[
                { v: "use_imported", label: "Use Imported Asset", icon: Package },
                { v: "generate", label: "Generate New Asset", icon: Wand2 },
                { v: "director", label: "Let Manufacturing Director™ Decide", icon: UserCog },
              ].map((o) => (
                <label key={o.v} data-testid={`pm-asset-mode-${o.v}`}
                  className={`flex items-center gap-2 text-sm px-2.5 py-1.5 rounded-sm border cursor-pointer ${assetMode === o.v ? "border-primary bg-primary/[0.04]" : "hover:border-primary/40"}`}>
                  <input type="radio" name="asset-mode" className="accent-primary" checked={assetMode === o.v} onChange={() => setAssetMode(o.v)} />
                  <o.icon className="w-3.5 h-3.5 text-muted-foreground" /> {o.label}
                </label>
              ))}
            </div>

            {assetMode === "use_imported" && (
              <div data-testid="pm-asset-picker" className="space-y-2">
                {recommended.length > 0 && (
                  <p className="text-[11px] text-gold flex items-center gap-1"><Star className="w-3 h-3 fill-gold" /> Recommended for this topic</p>
                )}
                {assets.length === 0 ? (
                  <p className="text-[11px] text-muted-foreground">No approved assets in the Vault yet. Import assets in the Asset Vault™ first.</p>
                ) : (
                  <div className="max-h-64 overflow-y-auto space-y-1.5 pr-1">
                    {[...recommended, ...assets.filter((a) => !recommended.some((r) => r.id === a.id))].map((a) => {
                      const isImg = a.file?.previewable && /png|jpg|jpeg|webp|gif|svg/i.test(a.file.ext);
                      const ts = TS_STATUSES.includes(a.approval_status);
                      return (
                        <button key={a.id} type="button" onClick={() => setSelectedAssetId(a.id)}
                          data-testid={`pm-asset-${a.asset_code}`}
                          className={`w-full flex items-center gap-2 p-2 rounded-md border text-left ${selectedAssetId === a.id ? "border-primary bg-primary/[0.05]" : "hover:border-primary/40"}`}>
                          <div className="w-12 h-12 rounded bg-navy/5 overflow-hidden flex items-center justify-center shrink-0">
                            {isImg ? <img src={absU(a.file.url)} alt={a.name} className="w-full h-full object-cover" /> : <Package className="w-5 h-5 text-navy/40" />}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-medium truncate">{a.name}</p>
                            <p className="text-[10px] text-muted-foreground">{a.asset_type} · v{a.version} · {a.approval_status}</p>
                            <div className="flex gap-1 mt-0.5">
                              {a.source === "Protected Master" && <span className="text-[9px] px-1 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 inline-flex items-center gap-0.5"><ShieldCheck className="w-2.5 h-2.5" />Protected Master</span>}
                              {ts && <span className="text-[9px] px-1 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">Treasure Standard™</span>}
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
                {selectedAssetId && <p className="text-[11px] text-emerald-700">Selected asset will be used exactly as imported — no regeneration.</p>}
              </div>
            )}
          </div>
          {!krId && (
            <div>
              <label className="text-sm font-medium">Topic</label>
              <input data-testid="pm-topic-input" value={topic} onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. How the immune system works"
                className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm" />
            </div>
          )}
          <div>
            <label className="text-sm font-medium">Product Type</label>
            <select data-testid="pm-type-select" value={productType} onChange={(e) => setProductType(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary text-sm">
              {PRODUCT_TYPES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Audience</label>
            <input data-testid="pm-audience-input" value={audience} onChange={(e) => setAudience(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary text-sm" />
          </div>
          <div>
            <label className="text-sm font-medium">Learning Level</label>
            <select data-testid="pm-level-select" value={level} onChange={(e) => setLevel(e.target.value)}
              className="mt-1 w-full px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary text-sm">
              {["Introductory", "Intermediate", "Advanced", "Expert"].map((l) => <option key={l}>{l}</option>)}
            </select>
          </div>
          <button data-testid="pm-generate-btn" onClick={generate} disabled={loading || assembling}
            className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground py-2.5 rounded-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Manufacturing…</> : <><Sparkles className="w-4 h-4" /> Manufacture with AI</>}
          </button>
          {krId && hasRecipe && (
            <button data-testid="pm-assemble-btn" onClick={assemble} disabled={loading || assembling}
              className="w-full flex items-center justify-center gap-2 border py-2.5 rounded-sm font-medium hover:border-primary hover:text-primary transition-colors disabled:opacity-60">
              {assembling ? <><Loader2 className="w-4 h-4 animate-spin" /> Assembling…</> : <><Factory className="w-4 h-4" /> Assemble from Record</>}
            </button>
          )}
          {krId && hasRecipe && (
            <p className="text-xs text-muted-foreground">Assembly reuses this record's already-manufactured fields — no regeneration. Recipe: {recipes[productType].map((f) => f.replace(/_/g, " ")).join(", ")}.</p>
          )}
        </div>

        <div className="lg:col-span-2">
          {loading && (
            <div className="bg-card border rounded-md p-12 flex flex-col items-center justify-center text-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
              <p className="font-heading font-semibold">Manufacturing understanding…</p>
              <p className="text-sm text-muted-foreground mt-1">The Manufacturing Director™ is generating your {productType}.</p>
            </div>
          )}
          {!loading && !result && (
            <div className="bg-card border border-dashed rounded-md p-12 flex flex-col items-center justify-center text-center">
              <Factory className="w-10 h-10 text-muted-foreground mb-4" strokeWidth={1.5} />
              <p className="font-heading font-semibold">No product yet</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm">Configure the order on the left and manufacture a full, publication-ready product.</p>
            </div>
          )}
          {result && (
            <div className="bg-card border rounded-md p-6 animate-fade-up" data-testid="pm-result">
              <div className="flex items-center justify-between mb-4 pb-4 border-b">
                <div>
                  <span className="font-mono text-xs text-muted-foreground">{result.product_code} · {result.product_type}</span>
                  <h2 className="font-heading text-xl font-bold mt-1">{result.title}</h2>
                </div>
                <button onClick={() => navigate(`/products/${result.id}`)} data-testid="pm-view-btn"
                  className="flex items-center gap-1.5 text-sm text-primary font-medium hover:underline shrink-0">
                  Open in Library <ArrowRight className="w-4 h-4" />
                </button>
              </div>
              <Markdown text={result.content} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
