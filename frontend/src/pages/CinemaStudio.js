import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, MetricCard } from "@/components/qru";
import {
  Loader2, ShieldCheck, Film, Mic, Radio, Clapperboard, Play, Sparkles,
  Volume2, Video, Clock, Info,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const FMT_ICON = { audiobook: Volume2, podcast: Mic, motion_storybook: Film, animated_episode: Clapperboard, youtube_short: Video, promo_video: Play };

export default function CinemaStudio() {
  const [formats, setFormats] = useState(null);
  const [krs, setKrs] = useState([]);
  const [krId, setKrId] = useState("");
  const [stats, setStats] = useState(null);
  const [productions, setProductions] = useState([]);
  const [busy, setBusy] = useState(null);

  const loadProds = () => api.get("/cinema-studio/productions").then((r) => setProductions(r.data.productions)).catch(() => {});
  useEffect(() => {
    api.get("/cinema-studio/formats").then((r) => setFormats(r.data.formats)).catch(() => {});
    api.get("/cinema-studio/verified-krs").then((r) => { setKrs(r.data.records); if (r.data.records[0]) setKrId(r.data.records[0].id); }).catch(() => {});
    api.get("/cinema-studio/stats").then((r) => setStats(r.data)).catch(() => {});
    loadProds();
  }, []);

  const manufacture = async (fmt) => {
    if (!krId) { toast.error("Select a verified Knowledge Record first."); return; }
    setBusy(fmt.id);
    toast.message(fmt.kind === "video"
      ? "Manufacturing narrated motion video — generating scenes, narration & assembling. This can take a minute or two."
      : "Manufacturing narrated audio from the verified Knowledge Record…");
    try {
      const { data } = await api.post("/cinema-studio/manufacture", { kr_id: krId, format: fmt.id });
      toast.success(`${data.production.name} manufactured (${data.production.duration}s).`);
      loadProds();
      api.get("/cinema-studio/stats").then((r) => setStats(r.data));
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(null); }
  };

  if (!formats) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  const audio = formats.filter((f) => f.kind === "audio");
  const video = formats.filter((f) => f.kind === "video");

  const Card = (f) => {
    const Icon = FMT_ICON[f.id] || Sparkles;
    return (
      <div key={f.id} data-testid={`studio-format-${f.id}`} className="border border-border rounded-md p-4 flex flex-col">
        <div className="flex items-center gap-2 mb-1"><Icon className="w-5 h-5 text-gold" /><span className="font-bold text-navy">{f.name}</span></div>
        <p className="text-[11px] text-muted-foreground flex items-center gap-1 mb-3"><Info className="w-3 h-3" />{f.technique}</p>
        <button data-testid={`studio-make-${f.id}`} onClick={() => manufacture(f)} disabled={busy || !krId}
          className="mt-auto inline-flex items-center justify-center gap-2 bg-navy text-white px-3 py-2 rounded-md text-sm font-bold disabled:opacity-60">
          {busy === f.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Manufacture
        </button>
      </div>
    );
  };

  return (
    <div data-testid="cinema-studio-page">
      <PageHeader
        overline="Story & Cinema Studio™ · Podcast Studio™ · Stone 3"
        title="Bring verified knowledge to life — in sound & motion"
        description="Governed audio & video manufacturing departments. Every production inherits from a verified Knowledge Record™. Truthful by design: video is image-based motion (Ken Burns) with narration — not frame-by-frame animation."
        actions={<VerifiedBadge label="Inheritance-First™" testid="cs-badge" />}
      />

      {stats && (
        <div className="grid grid-cols-3 gap-3 mb-6" data-testid="cs-stats">
          <MetricCard icon={Volume2} accent="gold" label="Audio Productions" value={stats.audio_productions} testid="stat-audio" />
          <MetricCard icon={Video} accent="royal" label="Video Productions" value={stats.video_productions} testid="stat-video" />
          <MetricCard icon={Clapperboard} label="Formats" value={stats.formats} testid="stat-formats" />
        </div>
      )}

      <Panel title="Choose the verified Knowledge Record™" icon={ShieldCheck} testid="cs-kr-select" className="mb-6">
        {krs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No verified Knowledge Records yet. Approve one in Knowledge Record Manufacturing™ first.</p>
        ) : (
          <select data-testid="cs-kr-dropdown" value={krId} onChange={(e) => setKrId(e.target.value)}
            className="w-full px-3 py-2.5 text-sm border border-border rounded-md bg-card outline-none focus:border-navy">
            {krs.map((k) => { const label = `${k.kr_code} — ${k.title} (${k.category})`; return <option key={k.id} value={k.id}>{label}</option>; })}
          </select>
        )}
      </Panel>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        <Panel title="Podcast Studio™ — Audio" icon={Mic} accent="gold" testid="cs-audio">
          <div className="grid sm:grid-cols-2 gap-3">{audio.map(Card)}</div>
        </Panel>
        <Panel title="Story & Cinema Studio™ — Video" icon={Film} accent="royal" testid="cs-video">
          <div className="grid sm:grid-cols-2 gap-3">{video.map(Card)}</div>
        </Panel>
      </div>

      <Panel title="Manufactured Productions" icon={Radio} testid="cs-productions">
        {productions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No productions yet. Pick a verified KR above and manufacture your first audio or video.</p>
        ) : (
          <div className="space-y-3" data-testid="cs-productions-list">
            {productions.map((p) => (
              <div key={p.id} data-testid={`production-${p.id}`} className="border border-border rounded-md p-3">
                <div className="flex items-center gap-2 flex-wrap mb-2">
                  {p.kind === "video" ? <Video className="w-4 h-4 text-royal" /> : <Volume2 className="w-4 h-4 text-gold" />}
                  <span className="font-bold text-navy text-sm">{p.name}</span>
                  <span className="font-mono text-[10px] text-muted-foreground">{p.kr_code}</span>
                  <StatusChip status={p.department} tone="navy" />
                  <StatusChip status={`${p.duration}s`} tone="royal" />
                </div>
                {p.kind === "video"
                  ? <video data-testid={`player-${p.id}`} controls className="w-full max-w-lg rounded-md" src={`${BACKEND}${p.url}`} />
                  : <audio data-testid={`player-${p.id}`} controls className="w-full max-w-lg" src={`${BACKEND}${p.url}`} />}
                <p className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1"><Info className="w-3 h-3" />{p.technique} · inherits from {p.kr_title}</p>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
