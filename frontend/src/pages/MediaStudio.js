import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import {
  Loader2, Clapperboard, Sparkles, ShieldCheck, Send, Film, Music2, FileText,
  Video, Waves, ChevronDown,
} from "lucide-react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { DestinationChips } from "@/components/DestinationPreview";

const STATUS = {
  manufactured: { bg: "hsl(var(--primary) / 0.12)", color: "hsl(var(--primary))", label: "Manufactured" },
  manufacturing: { bg: "hsl(var(--primary) / 0.12)", color: "hsl(var(--primary))", label: "Manufacturing…" },
  ready: { bg: "hsl(var(--success) / 0.12)", color: "hsl(var(--success))", label: "Ready to Publish" },
  failed: { bg: "hsl(var(--destructive) / 0.12)", color: "hsl(var(--destructive))", label: "Failed" },
};

function Field({ label, value }) {
  if (!value) return null;
  return <div className="mb-3"><p className="text-xs font-semibold text-primary mb-0.5">{label}</p><p className="text-sm whitespace-pre-wrap">{typeof value === "string" ? value : JSON.stringify(value)}</p></div>;
}

export default function MediaStudio() {
  const [records, setRecords] = useState([]);
  const [library, setLibrary] = useState([]);
  const [destinations, setDestinations] = useState([]);
  const [destMap, setDestMap] = useState([]);
  const [krId, setKrId] = useState("");
  const [mtype, setMtype] = useState("video");
  const [busy, setBusy] = useState(false);
  const [sel, setSel] = useState(null);
  const [showScores, setShowScores] = useState(false);

  const loadLibrary = useCallback(async () => {
    const { data } = await api.get("/media/library");
    setLibrary(data.media); setDestinations(data.destinations);
  }, []);

  useEffect(() => {
    api.get("/memory/records").then((r) => setRecords(r.data.records));
    api.get("/distribution-architecture/destinations-map").then((r) => setDestMap(r.data.map || [])).catch(() => {});
    loadLibrary();
  }, [loadLibrary]);

  const manufacture = async () => {
    if (!krId) { toast.error("Select a verified record."); return; }
    setBusy(true);
    await api.post("/media/manufacture", { knowledge_record_id: krId, media_type: mtype });
    toast.info(`Manufacturing ${mtype} media…`);
    setTimeout(loadLibrary, 1500);
    const poll = setInterval(async () => {
      const { data } = await api.get("/media/library");
      setLibrary(data.media);
      if (!data.media.some((m) => m.status === "manufacturing")) { clearInterval(poll); setBusy(false); }
    }, 4000);
  };

  const open = async (m) => {
    const { data } = await api.get(`/media/${m.id}`);
    setSel(data); setShowScores(false);
  };

  const runQC = async () => {
    await api.post(`/media/${sel.id}/quality-control`);
    toast.info("Treasure Standard™ QC started…");
    const poll = setInterval(async () => {
      const { data } = await api.get(`/media/${sel.id}`);
      setSel(data);
      if (["certified", "needs_improvement", "failed"].includes(data.qc?.status)) {
        clearInterval(poll); loadLibrary();
        toast[data.publishing_ready ? "success" : "warning"](data.publishing_ready ? "Media certified — ready to publish!" : "Media returned for improvement.");
      }
    }, 3000);
  };

  const a = sel?.assets || {};

  return (
    <div>
      <PageHeader overline="QRU Media Manufacturing Engine™ · Enterprise Mode" title="Media Studio"
        description="Turn one verified Knowledge Record™ into a complete multimedia package — scripts, memory assets, video metadata, or a QRU Frequency Collection™ meditation." />

      <div className="bg-card border rounded-2xl p-5 mb-6 grid sm:grid-cols-3 gap-3 items-end">
        <div className="sm:col-span-1">
          <label className="text-xs text-muted-foreground mb-1 block">Verified Knowledge Record™</label>
          <select data-testid="media-kr-select" value={krId} onChange={(e) => setKrId(e.target.value)} className="w-full px-3 py-2 text-sm bg-muted rounded-md border outline-none">
            <option value="">Select…</option>
            {records.map((r) => <option key={r.id} value={r.id}>{r.kr_code} · {r.title}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Media Type</label>
          <div className="flex gap-2">
            {[["video", Video, "Video"], ["meditation", Waves, "Meditation"]].map(([v, Icon, l]) => (
              <button key={v} data-testid={`media-type-${v}`} onClick={() => setMtype(v)}
                className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-sm border ${mtype === v ? "text-white border-transparent" : "text-muted-foreground"}`}
                style={mtype === v ? { background: "hsl(var(--navy))" } : {}}><Icon className="w-4 h-4" />{l}</button>
            ))}
          </div>
        </div>
        <button data-testid="media-manufacture" onClick={manufacture} disabled={busy}
          className="px-5 py-2 rounded-md text-white text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-60" style={{ background: "hsl(var(--royal))" }}>
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Clapperboard className="w-4 h-4" />} Manufacture Media
        </button>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Media Library */}
        <div>
          <p className="overline text-primary mb-3">Media Library</p>
          <div className="space-y-2" data-testid="media-library">
            {library.length === 0 && <p className="text-sm text-muted-foreground">No media yet.</p>}
            {library.map((m) => {
              const st = STATUS[m.status] || STATUS.manufactured;
              return (
                <button key={m.id} data-testid={`media-item-${m.id}`} onClick={() => open(m)}
                  className={`w-full text-left bg-card border rounded-xl p-3 hover:border-primary transition-colors ${sel?.id === m.id ? "border-primary" : ""}`}>
                  <div className="flex items-center gap-2">
                    {m.media_type === "meditation" ? <Waves className="w-4 h-4 text-primary" /> : <Film className="w-4 h-4 text-primary" />}
                    <p className="text-sm font-medium line-clamp-1 flex-1">{m.title}</p>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-[10px] text-muted-foreground">{m.media_code} · {m.media_type}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: st.bg, color: st.color }}>{st.label}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Detail */}
        <div className="lg:col-span-2">
          {!sel ? (
            <div className="bg-card border rounded-2xl p-12 text-center text-muted-foreground">
              <Clapperboard className="w-10 h-10 mx-auto mb-3" strokeWidth={1.5} />
              <p className="font-heading">Manufacture or select media to view the package.</p>
            </div>
          ) : (
            <div data-testid="media-detail">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                <div><p className="text-xs text-muted-foreground">{sel.media_code} · {sel.media_type}</p><h2 className="font-heading text-xl font-bold">{sel.title}</h2></div>
                <div className="flex gap-2">
                  {sel.qc?.status !== "certified" && sel.status !== "manufacturing" && (
                    <button data-testid="media-qc" onClick={runQC} className="px-4 py-2 rounded-md text-white text-sm font-medium flex items-center gap-1.5" style={{ background: "hsl(var(--navy))" }}><ShieldCheck className="w-4 h-4" /> Run Treasure Standard™ QC</button>
                  )}
                </div>
              </div>

              {sel.status === "manufacturing" && <div className="text-center py-16 text-muted-foreground"><Sparkles className="w-8 h-8 mx-auto mb-2 animate-pulse text-primary" /><p>Manufacturing the full media package…</p></div>}

              {sel.qc?.status === "certified" && (
                <div className="rounded-xl p-3 mb-4 flex items-center gap-2" style={{ background: "hsl(var(--success) / 0.1)" }} data-testid="media-certified">
                  <ShieldCheck className="w-4 h-4" style={{ color: "hsl(var(--success))" }} /><span className="text-sm font-medium">Treasure Standard™ Certified — ready to publish.</span>
                </div>
              )}
              {sel.qc?.status === "needs_improvement" && (
                <div className="rounded-xl p-3 mb-4 text-sm" style={{ background: "hsl(var(--warning) / 0.1)" }}>Returned for improvement. {(sel.qc.notes || []).join(" ")}</div>
              )}
              {sel.qc?.scores && Object.keys(sel.qc.scores).length > 0 && (
                <div className="mb-4">
                  <button onClick={() => setShowScores(!showScores)} className="text-xs text-primary flex items-center gap-1">Internal QC report <ChevronDown className={`w-3 h-3 transition-transform ${showScores ? "rotate-180" : ""}`} /></button>
                  {showScores && <div className="grid grid-cols-2 gap-2 mt-2">{Object.entries(sel.qc.scores).map(([k, v]) => <div key={k} className="text-xs flex justify-between border rounded px-2 py-1"><span>{k}</span><span className="font-semibold">{v}</span></div>)}</div>}
                </div>
              )}

              {a && sel.status !== "manufacturing" && (
                <div className="space-y-4">
                  {sel.media_type === "video" ? (
                    <>
                      <div className="bg-card border rounded-xl p-4"><p className="overline text-primary mb-2 flex items-center gap-1.5"><Video className="w-3.5 h-3.5" /> Video Package</p>
                        <Field label="Title" value={a.video?.title} /><Field label="SEO Title" value={a.video?.seo_title} />
                        <Field label="Description" value={a.video?.description} />
                        {a.video?.chapters?.length > 0 && <div className="mb-3"><p className="text-xs font-semibold text-primary mb-0.5">Chapters</p>{a.video.chapters.map((c, i) => <p key={i} className="text-sm">{c.time} — {c.title}</p>)}</div>}
                        <Field label="Thumbnail Text" value={a.video?.thumbnail_text} /><Field label="Thumbnail Brief" value={a.video?.thumbnail_brief} />
                        <Field label="Opening Hook" value={a.video?.opening_hook} /><Field label="Closing CTA" value={a.video?.closing_cta} />
                        {a.video?.hashtags && <p className="text-xs text-primary">{a.video.hashtags.join(" ")}</p>}
                      </div>
                      <div className="bg-card border rounded-xl p-4"><p className="overline text-primary mb-2 flex items-center gap-1.5"><FileText className="w-3.5 h-3.5" /> Scripts</p>
                        <Field label="Long-form Script" value={a.long_form_script} /><Field label="Short-form (30-60s)" value={a.short_form_script} /><Field label="Narration" value={a.narration_script} /><Field label="Voice-over" value={a.voice_over_script} />
                      </div>
                    </>
                  ) : (
                    <div className="bg-card border rounded-xl p-4"><p className="overline text-primary mb-2 flex items-center gap-1.5"><Waves className="w-3.5 h-3.5" /> Meditation Session</p>
                      <Field label="Session" value={a.meditation?.session_name} /><Field label="Guided Script" value={a.meditation?.script} />
                      {a.meditation?.reflection_prompts && <div className="mb-3"><p className="text-xs font-semibold text-primary mb-0.5">Reflection Prompts</p>{a.meditation.reflection_prompts.map((p, i) => <p key={i} className="text-sm">• {p}</p>)}</div>}
                      <Field label="Journal Page" value={a.meditation?.journal_page} /><Field label="Poster Brief" value={a.meditation?.poster_brief} />
                      <Field label="Workbook Page" value={a.meditation?.workbook_page} /><Field label="Character Intro" value={a.meditation?.character_intro} />
                      <Field label="Closing Reflection" value={a.meditation?.closing_reflection} /><Field label="Ambient Music Prompt" value={a.meditation?.ambient_music_prompt} />
                    </div>
                  )}

                  <div className="bg-card border rounded-xl p-4"><p className="overline text-primary mb-2 flex items-center gap-1.5"><Music2 className="w-3.5 h-3.5" /> Memory & Music</p>
                    <Field label="Memory Hook™" value={a.memory_hook} /><Field label="Memory Sentence™" value={a.memory_sentence} /><Field label="Memory Chant™" value={a.memory_chant} />
                    <Field label="Music Prompt" value={a.music_prompt} /><Field label="Instrumental Prompt" value={a.instrumental_prompt} />
                    {a.character_dialogue?.length > 0 && <div><p className="text-xs font-semibold text-primary mb-0.5">Character Dialogue</p>{a.character_dialogue.map((c, i) => <p key={i} className="text-sm"><b>{c.character}:</b> {c.line}</p>)}</div>}
                  </div>

                  {a.legacy_learners && (
                    <div className="bg-card border rounded-xl p-4"><p className="overline text-primary mb-2">Legacy Learners™ Versions</p>
                      <div className="grid sm:grid-cols-2 gap-2 text-sm">{Object.entries(a.legacy_learners).map(([k, v]) => <div key={k}><p className="text-xs font-semibold capitalize text-muted-foreground">{k}</p><p>{v}</p></div>)}</div>
                    </div>
                  )}

                  {/* Publishing */}
                  <div className="bg-card border rounded-xl p-4">
                    <p className="overline text-primary mb-2 flex items-center gap-1.5"><Send className="w-3.5 h-3.5" /> Publish destinations</p>
                    <div className="rounded-lg border border-navy/15 bg-navy/[0.03] p-2.5 mb-3 flex items-center gap-2 flex-wrap" data-testid="media-catalog-destination">
                      <span className="text-[11px] font-semibold text-navy">In the QRU catalog this publishes to</span>
                      <DestinationChips productType={sel.media_type === "video" ? "Video" : "Podcast"} destMap={destMap} />
                      <span className="text-[10px] text-muted-foreground">· auto-selected by Automatic Distribution™</span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2" data-testid="media-publish-note">
                      <b>YouTube publishing is live</b> — upload the finished MP4 in <a href="/youtube" className="text-royal font-semibold underline">YouTube Publisher™</a> and QRU uploads it to your channel with a real Video ID. Other destinations use automated upload that isn't wired yet (a planned milestone of the Universal Publishing Engine™). Manage connections in <b>Publishing Connectors™</b>.
                    </p>
                    <div className="flex flex-wrap gap-2" data-testid="publish-destinations">
                      <a href="/youtube" data-testid="publish-youtube"
                        className="text-xs px-3 py-1.5 rounded-full border border-navy bg-navy text-white font-semibold inline-flex items-center gap-1">
                        <Send className="w-3 h-3" /> Publish to YouTube →
                      </a>
                      {destinations.filter((d) => d.toLowerCase() !== "youtube").map((dst) => (
                        <button key={dst} data-testid={`publish-${dst}`} disabled
                          title={`Automated upload to ${dst} isn't wired yet — a planned milestone.`}
                          className="text-xs px-3 py-1.5 rounded-full border opacity-40 cursor-not-allowed">
                          {dst} · Coming Soon
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
