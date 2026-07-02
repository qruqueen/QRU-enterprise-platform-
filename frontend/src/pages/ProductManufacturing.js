import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Markdown } from "@/components/shared";
import { toast } from "sonner";
import { Sparkles, Loader2, Factory, ArrowRight } from "lucide-react";

const PRODUCT_TYPES = ["Book", "Poster", "Infographic", "Presentation", "Teacher Guide", "Caregiver Guide", "Workbook", "Lesson Plan", "Video Script", "Podcast Script", "Short-form Content", "Interactive Lesson", "AI Tutor", "Course", "Certificate", "Flash Cards", "Quiz", "Printable PDF"];

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

  useEffect(() => {
    api.get("/knowledge-records").then((r) => setRecords(r.data)).catch(() => {});
    api.get("/products/recipes").then((r) => setRecipes(r.data.recipes || {})).catch(() => {});
  }, []);

  const generate = async () => {
    if (!krId && !topic) return toast.error("Select a Knowledge Record or enter a topic");
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post("/products/generate", {
        knowledge_record_id: krId || null,
        topic: topic || null,
        product_type: productType,
        audience,
        learning_level: level,
      });
      setResult(data);
      toast.success(`Manufactured ${data.product_code}`);
    } catch { toast.error("Manufacturing failed"); } finally { setLoading(false); }
  };

  const assemble = async () => {
    if (!krId) return toast.error("Select a Knowledge Record to assemble from");
    setAssembling(true);
    setResult(null);
    try {
      const { data } = await api.post("/products/assemble", { knowledge_record_id: krId, product_type: productType });
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
