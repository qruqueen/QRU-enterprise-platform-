import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, PackageOpen, Sparkles, CheckCircle2, Clock, Lock, Film, Music, Image as ImageIcon,
  FileText, Tag, Palette, Mic, Captions, Play,
} from "lucide-react";

const COMP_ICON = {
  hero_cover: ImageIcon, poster: ImageIcon, thumbnail: ImageIcon, narration_script: FileText,
  approved_voice: Mic, caption_file: Captions, transcript: FileText, keywords: Tag,
  music_profile: Music, emotional_target: Sparkles, visual_style: Palette,
  qrubrand_intro: Play, qrubrand_outro: Play,
};

export default function MediaStarterKit() {
  const [config, setConfig] = useState(null);
  const [gov, setGov] = useState([]);
  const [products, setProducts] = useState([]);
  const [pid, setPid] = useState("");
  const [kit, setKit] = useState(null);
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    api.get("/media-starter-kit/config").then((r) => setConfig(r.data)).catch(() => setConfig(false));
    api.get("/governance-binding/strip/media").then((r) => setGov(r.data.governed_by)).catch(() => {});
    api.get("/founder-inbox").then((r) => setProducts((r.data.products || []).slice(0, 200))).catch(() => {});
  }, []);

  const load = async (id) => {
    setPid(id); setKit(null);
    if (!id) return;
    setBusy(true);
    try { const { data } = await api.get(`/media-starter-kit/kit/${id}`); setKit(data); }
    catch { toast.error("Could not assemble the Media Starter Kit™."); }
    finally { setBusy(false); }
  };

  const generate = async () => {
    if (!pid) return;
    setGenerating(true);
    try {
      await api.post(`/media-starter-kit/generate/${pid}`);
      toast.success("Media Starter Kit™ generated and saved to the production package.");
    } catch (e) { toast.error(e.response?.data?.detail || "Generation blocked."); }
    finally { setGenerating(false); }
  };

  if (config === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (config === false) return <p className="text-sm text-muted-foreground p-8">Could not load the Media Starter Kit™.</p>;

  return (
    <div>
      <PageHeader
        overline="QRU Media Starter Kit™ · MO-011"
        title="Media Starter Kit"
        description="Every approved product becomes a standardized production package — the single source for audiobooks, narrated posters, MP4 showcases, podcasts, YouTube Shorts, social clips, and marketing video. Manufactured deterministically from verified knowledge — never faked."
        actions={<VerifiedBadge label="Treasure + Gold Standard™ Gated" testid="msk-badge" />}
      />
      <GovernedBy standards={gov} className="mb-6" testid="msk-governed-by" />

      <Panel title="Assemble a Product's Media Starter Kit™" icon={PackageOpen} accent="gold" testid="msk-assembler" className="mb-8">
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end">
          <div className="flex-1">
            <label className="text-xs font-bold text-navy uppercase tracking-wide">Product</label>
            <select data-testid="msk-product" value={pid} onChange={(e) => load(e.target.value)} className="w-full mt-1 border rounded-sm p-2 text-sm">
              <option value="">— Select an approved product —</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.product_code} — {p.title}</option>)}
            </select>
          </div>
          <button onClick={generate} disabled={generating || !kit || !kit.gate.passed} data-testid="msk-generate"
            title={kit && !kit.gate.passed ? (kit.gate.blocked_reason || "Blocked") : "Generate & save the kit"}
            className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Generate Kit
          </button>
        </div>
        {busy && <div className="flex items-center gap-2 text-sm text-muted-foreground mt-4"><Loader2 className="w-4 h-4 animate-spin" /> Assembling components…</div>}
      </Panel>

      {kit && (
        <>
          {/* Gate + completeness */}
          <div className="grid md:grid-cols-3 gap-4 mb-8" data-testid="msk-summary">
            <div className="qru-card p-4">
              <p className="overline text-muted-foreground mb-1">Standards Gate</p>
              <StatusChip status={kit.gate.passed ? "Cleared" : "Blocked"} tone={kit.gate.passed ? "emerald" : "red"} />
              <p className="text-[11px] text-muted-foreground mt-2">Treasure: {kit.gate.treasure_standard} · Gold: {kit.gate.gold_standard}</p>
              {!kit.gate.passed && <p className="text-[11px] text-red-600 mt-1">{kit.gate.blocked_reason}</p>}
            </div>
            <div className="qru-card p-4">
              <p className="overline text-muted-foreground mb-1">Kit Completeness</p>
              <p className="font-heading text-3xl font-bold text-navy">{kit.kit_completeness}<span className="text-sm text-muted-foreground">%</span></p>
              <p className="text-[11px] text-muted-foreground">{kit.ready_count}/{kit.component_total} components ready</p>
            </div>
            <div className="qru-card p-4">
              <p className="overline text-muted-foreground mb-1">Producible Outputs</p>
              <p className="font-heading text-3xl font-bold text-navy">{kit.outputs_ready}<span className="text-sm text-muted-foreground">/{kit.outputs_total}</span></p>
              <p className="text-[11px] text-muted-foreground">media formats ready to produce now</p>
            </div>
          </div>

          {/* Components */}
          <Panel title="Starter Kit Components" icon={PackageOpen} accent="royal" testid="msk-components" className="mb-8">
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {Object.entries(kit.components).map(([k, c]) => {
                const Icon = COMP_ICON[k] || FileText;
                const ready = c.status === "ready";
                return (
                  <div key={k} className="border rounded-md p-3" data-testid={`msk-comp-${k}`}>
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-semibold text-navy flex items-center gap-1.5"><Icon className="w-3.5 h-3.5 text-royal" /> {kit.component_labels[k]}</p>
                      {ready ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <Clock className="w-4 h-4 text-amber-500" />}
                    </div>
                    <p className="text-[11px] text-muted-foreground">{c.detail}</p>
                    <p className="text-[10px] text-navy/50 mt-1">Source: {c.source}</p>
                  </div>
                );
              })}
            </div>
          </Panel>

          {/* Outputs */}
          <Panel title="Media Outputs" icon={Film} accent="gold" testid="msk-outputs">
            <div className="grid sm:grid-cols-2 gap-2.5">
              {kit.outputs.map((o) => {
                const ready = o.status === "ready_to_produce";
                return (
                  <div key={o.id} className="border rounded-md p-3" data-testid={`msk-output-${o.id}`}>
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-semibold text-navy">{o.name}</p>
                      <StatusChip status={ready ? "Ready to Produce" : "Blocked"} tone={ready ? "emerald" : "amber"} />
                    </div>
                    <p className="text-[11px] text-muted-foreground">{o.detail}</p>
                    <p className="text-[10px] text-navy/50 mt-1 flex items-center gap-1"><Lock className="w-2.5 h-2.5" /> {o.channel}</p>
                  </div>
                );
              })}
            </div>
          </Panel>
        </>
      )}
    </div>
  );
}
