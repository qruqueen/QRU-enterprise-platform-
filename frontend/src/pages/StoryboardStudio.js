import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { toast } from "sonner";
import { Loader2, Clapperboard, Film, Wand2, Download, FileText, Presentation, Volume2 } from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL || "";

const FORMAT_META = {
  youtube_video: { label: "YouTube Video", icon: Film },
  promo_short: { label: "Promo Short (9:16)", icon: Film },
  audio_lesson: { label: "Narrated Audio Lesson", icon: Volume2 },
  teacher_presentation: { label: "Teacher Presentation", icon: Presentation },
  student_presentation: { label: "Student Presentation", icon: Presentation },
};
const STATUS_TONE = { DRAFT: "slate", VERIFICATION_REQUIRED: "amber", REVISION_REQUIRED: "rose", MEDIA_APPROVED: "emerald", QRU_GOLD_STANDARD: "gold" };

export default function StoryboardStudio() {
  const [krs, setKrs] = useState([]);
  const [krId, setKrId] = useState("");
  const [formats, setFormats] = useState(["youtube_video", "audio_lesson", "teacher_presentation"]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/refinement/knowledge").then((r) => {
      const list = r.data.records || [];
      setKrs(list);
      const v = list.find((k) => k.verification?.evidence_sufficient_for_external_publication);
      setKrId((v || list[0])?.id || "");
    }).catch(() => {});
  }, []);

  const toggleFmt = (f) => setFormats((s) => s.includes(f) ? s.filter((x) => x !== f) : [...s, f]);

  const run = async (mode) => {
    if (!krId) return toast.error("Select a Knowledge Record.");
    setBusy(true); setResult(null);
    try {
      const { data } = mode === "pilot"
        ? await api.post(`/media-studio/pilot?kr_id=${krId}`)
        : mode === "kit"
        ? await api.post(`/media-studio/media-kit?kr_id=${krId}`)
        : await api.post("/media-studio/order", { kr_id: krId, formats });
      setResult(data);
      if (!data.source_verified_external) toast.warning("Held at INTERNAL DRAFT — source KR is not externally verified.");
      else toast.success(`Storyboard ${data.storyboard.sb_code} → ${data.products.length} media output(s).`);
    } catch (e) { toast.error(e.response?.data?.detail || "Media order failed."); }
    finally { setBusy(false); }
  };

  const patchProduct = (updated) => setResult((r) => ({ ...r, products: r.products.map((p) => p.id === updated.id ? updated : p) }));

  const renderAudio = async (product) => {
    patchProduct({ ...product, render_status: "RENDERING" });
    try {
      const { data } = await api.post(`/media-studio/product/${product.id}/render-audio`);
      patchProduct(data); toast.success("Narration MP3 rendered.");
    } catch (e) { patchProduct({ ...product, render_status: "RENDER_FAILED" }); toast.error(e.response?.data?.detail || "TTS failed."); }
  };

  const renderVideo = async (product) => {
    try {
      await api.post(`/media-studio/product/${product.id}/render-video`);
      patchProduct({ ...product, render_status: "RENDERING" });
      toast.info("Assembling draft MP4 via Flagship Showcase™ — this runs in the background.");
      const poll = setInterval(async () => {
        try {
          const { data } = await api.get(`/media-studio/product/${product.id}`);
          if (data.render_status !== "RENDERING") { clearInterval(poll); patchProduct(data);
            toast[data.render_status === "RENDERED" ? "success" : "warning"](data.render_status === "RENDERED" ? "Draft MP4 ready." : "Video render needs review."); }
        } catch { clearInterval(poll); }
      }, 6000);
      setTimeout(() => clearInterval(poll), 180000);
    } catch (e) { toast.error(e.response?.data?.detail || "Video render failed to start."); }
  };

  const selKr = krs.find((k) => k.id === krId);

  return (
    <div data-testid="storyboard-studio-page">
      <PageHeader
        overline="QRU Media Manufacturing™ · Storyboard Master™ · inside Product Manufacturing Engine™"
        title="Storyboard Studio"
        description="One approved Knowledge Record → one Storyboard Master™ → many governed media formats. Factual content is inherited verbatim from the verified KR — never rewritten. A successful render is not Gold Standard."
        actions={<VerifiedBadge label="Knowledge-First · One blueprint, many formats" testid="storyboard-badge" />}
      />

      <div className="grid lg:grid-cols-[380px_1fr] gap-5">
        <Panel title="Media Manufacturing Order™" icon={Clapperboard} accent="royal" testid="storyboard-order">
          <div className="space-y-3">
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Approved Knowledge Record</label>
              <select data-testid="storyboard-kr" value={krId} onChange={(e) => setKrId(e.target.value)} className="w-full mt-0.5 border rounded-sm p-2 text-sm">
                {krs.map((k) => {
                  const v = k.verification?.evidence_sufficient_for_external_publication;
                  return <option key={k.id} value={k.id}>{v ? "\u2713 " : "\u2022 "}{k.topic} ({k.kr_code})</option>;
                })}
              </select>
              {selKr && (
                <p className={`text-[10px] mt-1 ${selKr.verification?.evidence_sufficient_for_external_publication ? "text-emerald-700" : "text-amber-700"}`}>
                  {selKr.verification?.evidence_sufficient_for_external_publication ? "Externally verified — eligible for Gold Standard media." : "Not externally verified — media stays INTERNAL DRAFT (Verify & Promote first)."}
                </p>
              )}
            </div>
            <div>
              <label className="text-[10px] font-bold uppercase tracking-wide text-navy">Formats to manufacture</label>
              <div className="mt-1 space-y-1">
                {Object.entries(FORMAT_META).map(([f, m]) => {
                  const Ic = m.icon;
                  return (
                    <label key={f} data-testid={`storyboard-fmt-${f}`} className={`flex items-center gap-2 border rounded-sm px-2.5 py-1.5 text-[12px] cursor-pointer transition-colors ${formats.includes(f) ? "border-royal bg-royal/[0.04] text-navy" : "border-navy/15 text-navy/70"}`}>
                      <input type="checkbox" checked={formats.includes(f)} onChange={() => toggleFmt(f)} />
                      <Ic className="w-3.5 h-3.5" /> {m.label}
                    </label>
                  );
                })}
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <button onClick={() => run("order")} disabled={busy || formats.length === 0} data-testid="storyboard-manufacture" className="flex-1 inline-flex items-center justify-center gap-2 bg-navy text-white px-4 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90">
                {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wand2 className="w-4 h-4" />} Manufacture
              </button>
              <button onClick={() => run("pilot")} disabled={busy} data-testid="storyboard-pilot" className="inline-flex items-center justify-center gap-1.5 border border-navy/20 text-navy px-3 py-2.5 rounded-sm font-bold text-[12px] disabled:opacity-50">
                5-output Pilot
              </button>
            </div>
            <button onClick={() => run("kit")} disabled={busy} data-testid="storyboard-media-kit" className="w-full inline-flex items-center justify-center gap-2 border-2 border-gold text-navy bg-gold/10 px-4 py-2.5 rounded-sm font-bold text-[13px] disabled:opacity-50 hover:bg-gold/20 transition-colors">
              <Wand2 className="w-4 h-4" /> Manufacture Full Media Kit
            </button>
          </div>
        </Panel>

        <div className="space-y-4">
          {!result ? (
            <Panel title="Storyboard Master™" icon={Film} accent="gold" testid="storyboard-empty">
              <p className="text-[12px] text-navy/80">Select a verified Knowledge Record and the formats you want. The Factory builds one governed Storyboard Master™ (scene-by-scene: objective, narration, visual direction, on-screen text, motion, audio, duration, accessibility, citations) and renders each selected format from it — no repeated content rewriting.</p>
            </Panel>
          ) : (
            <>
              <Panel title={`Storyboard Master™ · ${result.storyboard.sb_code}`} icon={Film} accent="gold" testid="storyboard-master">
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <span className="text-[11px] font-bold text-navy">{result.storyboard.topic}</span>
                  <StatusChip status={`${result.storyboard.scene_count} scenes · ~${result.storyboard.estimated_seconds}s`} tone="blue" />
                  <StatusChip status={result.source_verified_external ? "Verified External" : "Internal Draft"} tone={result.source_verified_external ? "emerald" : "amber"} />
                  <span className="text-[10px] text-muted-foreground">from {result.storyboard.kr_code} v{result.storyboard.kr_version}</span>
                </div>
                <p className="text-[11px] text-navy/70 mb-3">{result.note}</p>
                <div className="space-y-1.5 max-h-[240px] overflow-y-auto">
                  {result.storyboard.scenes.map((s) => (
                    <div key={s.scene} className="border-l-2 border-royal pl-2.5 py-0.5" data-testid={`storyboard-scene-${s.scene}`}>
                      <p className="text-[11px] font-bold text-navy">Scene {s.scene} · {s.kr_section} <span className="text-muted-foreground font-normal">({s.duration_sec}s)</span></p>
                      <p className="text-[10px] text-navy/80">{s.narration}</p>
                      <p className="text-[9px] text-muted-foreground italic">Visual: {s.visual_direction} · Motion: {s.animation}</p>
                    </div>
                  ))}
                </div>
              </Panel>

              <Panel title="Rendered Media Products" icon={Clapperboard} accent="royal" testid="storyboard-products">
                <div className="grid sm:grid-cols-2 gap-3">
                  {result.products.map((p) => {
                    const Ic = (FORMAT_META[p.format] || {}).icon || FileText;
                    return (
                      <div key={p.id} className="border rounded-md p-3 border-navy/10" data-testid={`storyboard-product-${p.format}`}>
                        <div className="flex items-center gap-2 mb-1.5">
                          <Ic className="w-4 h-4 text-royal" />
                          <span className="text-[12px] font-bold text-navy">{p.label}</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          <StatusChip status={p.status.replace(/_/g, " ")} tone={STATUS_TONE[p.status] || "slate"} />
                          <StatusChip status={p.render_status.replace(/_/g, " ")} tone="blue" />
                          <StatusChip status={p.treasure_status === "TREASURE_STANDARD_PASSED" ? "Treasure \u2713" : "Return"} tone={p.treasure_status === "TREASURE_STANDARD_PASSED" ? "emerald" : "rose"} />
                        </div>
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {p.files.map((f, i) => (
                            <a key={i} href={`${BACKEND}${f.url}`} target="_blank" rel="noreferrer" data-testid={`storyboard-file-${p.format}-${f.format}`} className="inline-flex items-center gap-1 text-[10px] border border-navy/15 rounded-sm px-2 py-1 text-navy hover:border-royal">
                              <Download className="w-3 h-3" /> {f.label || f.format.toUpperCase()}
                            </a>
                          ))}
                        </div>
                        {p.notes?.map((n, i) => <p key={i} className="text-[9px] text-muted-foreground">{n}</p>)}
                        {(p.format === "audio_lesson" || p.recipe?.render === "video") && (
                          <div className="mt-1.5 flex gap-1.5">
                            {p.format === "audio_lesson" && (
                              <button onClick={() => renderAudio(p)} disabled={p.render_status === "RENDERING"} data-testid={`storyboard-render-audio-${p.format}`} className="inline-flex items-center gap-1 text-[10px] border border-royal/40 text-royal rounded-sm px-2 py-1 font-bold disabled:opacity-50 hover:bg-royal/5">
                                {p.render_status === "RENDERING" ? <Loader2 className="w-3 h-3 animate-spin" /> : <Volume2 className="w-3 h-3" />} Render MP3
                              </button>
                            )}
                            {p.recipe?.render === "video" && (
                              <button onClick={() => renderVideo(p)} disabled={p.render_status === "RENDERING" || p.verification_status !== "VERIFIED_EXTERNAL"} data-testid={`storyboard-render-video-${p.format}`} className="inline-flex items-center gap-1 text-[10px] border border-royal/40 text-royal rounded-sm px-2 py-1 font-bold disabled:opacity-50 hover:bg-royal/5" title={p.verification_status !== "VERIFIED_EXTERNAL" ? "Requires an externally-verified KR" : ""}>
                                {p.render_status === "RENDERING" ? <Loader2 className="w-3 h-3 animate-spin" /> : <Film className="w-3 h-3" />} Render MP4
                              </button>
                            )}
                          </div>
                        )}
                        <p className="text-[9px] text-muted-foreground mt-1">Quality Gate: {p.quality_gate.counts.passed}/{p.quality_gate.counts.total} passed · {p.quality_gate.counts.blocking} blocking</p>
                      </div>
                    );
                  })}
                </div>
              </Panel>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
