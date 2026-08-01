import { useEffect, useState, useCallback, useRef } from "react";
import api, { formatApiError } from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, MetricCard, StatusChip, GovernedBy } from "@/components/qru";
import { KnowledgePicker } from "@/components/KnowledgePicker";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";
import {
  Sparkles, Users, BookOpen, Clapperboard, ShieldCheck, Lock, CheckCircle2,
  Globe, MapPin, GitBranch, Boxes, Baby, ClipboardCheck, Wand2, Film, PlayCircle, Loader2, Mic, Workflow, Plug,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

const RESP_ICON = { universe: Globe, characters: Users, stories: BookOpen, production: Clapperboard, governance: ShieldCheck };
const AGE_BANDS = ["Early Learners", "Growing Learners", "Emerging Thinkers", "Future Leaders"];

export default function LittleLegacyStudio() {
  const [ov, setOv] = useState(null);
  const [chars, setChars] = useState([]);
  const [bible, setBible] = useState(null);
  const [locations, setLocations] = useState([]);
  const [episodes, setEpisodes] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [o, c, b, l, e] = await Promise.all([
        api.get("/little-legacy/overview"),
        api.get("/little-legacy/characters"),
        api.get("/little-legacy/universe-bible"),
        api.get("/little-legacy/locations"),
        api.get("/little-legacy/episodes"),
      ]);
      setOv(o.data); setChars(c.data.characters || []); setBible(b.data);
      setLocations(l.data.locations || []); setEpisodes(e.data.episodes || []);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail) || "Failed to load Studio."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const approveCharacter = async (id) => {
    try {
      const { data } = await api.post(`/little-legacy/characters/${id}/approve`);
      toast.success(data.message); load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const approveBible = async () => {
    try {
      const { data } = await api.post("/little-legacy/universe-bible/approve");
      toast.success(data.message); load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  if (loading) return <div className="p-8 text-muted-foreground">Loading Little Legacy Studio™…</div>;
  if (!ov) return <div className="p-8 text-muted-foreground">Studio not seeded yet.</div>;

  const fr = ov.franchise || {};
  const counts = ov.counts || {};

  return (
    <div className="max-w-6xl">
      <PageHeader
        overline="Governed Capability · QRU Factory™"
        title="Little Legacy Learners™"
        description={fr.promise || "Little Lessons Today. Big Impact Tomorrow.™ — a governed animation franchise manufactured inside the existing QRU Factory™."}
        actions={<StatusChip status={fr.status || "Draft"} testid="ll-franchise-status" />}
      />

      <GovernedBy className="mb-6" testid="ll-governed-by"
        standards={[{ name: "Treasure Standard™" }, { name: "Verification Lion™" }, { name: "QRU Publishing Standard™" }, { name: "Governance Binding Layer™" }]} />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard icon={Users} label="Character Bibles" value={counts.characters ?? 0} sub={`${counts.characters_approved ?? 0} Founder-approved`} accent="royal" testid="ll-metric-characters" />
        <MetricCard icon={MapPin} label="World Locations" value={counts.locations ?? 0} accent="navy" testid="ll-metric-locations" />
        <MetricCard icon={Clapperboard} label="Episode Blueprints" value={counts.episodes ?? 0} accent="gold" testid="ll-metric-episodes" />
        <MetricCard icon={Globe} label="Universe Bible" value={(ov.universe_bible_status || "Draft").split(" ")[0]} accent="navy" testid="ll-metric-bible" />
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="mb-6 flex-wrap h-auto">
          <TabsTrigger value="overview" data-testid="ll-tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="universe" data-testid="ll-tab-universe">Universe Bible</TabsTrigger>
          <TabsTrigger value="characters" data-testid="ll-tab-characters">Characters</TabsTrigger>
          <TabsTrigger value="mastering" data-testid="ll-tab-mastering">Character Mastering</TabsTrigger>
          <TabsTrigger value="stories" data-testid="ll-tab-stories">Stories</TabsTrigger>
          <TabsTrigger value="pilots" data-testid="ll-tab-pilots">Pilot Studio</TabsTrigger>
          <TabsTrigger value="kits" data-testid="ll-tab-kits">Product Kits</TabsTrigger>
          <TabsTrigger value="feedback" data-testid="ll-tab-feedback">Project Zero™</TabsTrigger>
          <TabsTrigger value="animation" data-testid="ll-tab-animation">Performance Engine™</TabsTrigger>
          <TabsTrigger value="governance" data-testid="ll-tab-governance">Governance</TabsTrigger>
        </TabsList>

        {/* OVERVIEW — Five Responsibilities + Knowledge Flow + Production catalog */}
        <TabsContent value="overview" className="space-y-6">
          <Panel title="The Five Responsibilities" icon={GitBranch} accent="royal" testid="ll-responsibilities">
            <div className="grid md:grid-cols-2 gap-4">
              {(ov.responsibilities || []).map((r) => {
                const Icon = RESP_ICON[r.key] || Boxes;
                return (
                  <div key={r.key} className="border border-navy/10 rounded-md p-4" data-testid={`ll-resp-${r.key}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4 text-royal" />
                      <p className="font-heading font-bold text-navy">{r.name}</p>
                    </div>
                    <p className="text-[11px] text-muted-foreground mb-2">Owner: {r.owner} · Source of truth: <span className="font-semibold text-navy/80">{r.source_of_truth}</span></p>
                    <div className="flex flex-wrap gap-1">
                      {r.owns.slice(0, 8).map((o) => (
                        <span key={o} className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-navy/[0.06] text-navy/70 border border-navy/10">{o}</span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </Panel>

          <div className="grid md:grid-cols-2 gap-6">
            <Panel title="Knowledge Flow — no stage is skipped" icon={GitBranch} testid="ll-knowledge-flow">
              <ol className="space-y-1.5">
                {(ov.knowledge_flow || []).map((s, i) => (
                  <li key={s} className="flex items-center gap-2 text-sm">
                    <span className="w-5 h-5 rounded-full bg-navy text-white text-[10px] font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                    <span className="text-navy font-medium">{s}</span>
                  </li>
                ))}
              </ol>
            </Panel>
            <Panel title="One Knowledge Record → many products" icon={Boxes} accent="gold" testid="ll-production-catalog">
              <p className="text-[11px] text-muted-foreground mb-3">The Factory manufactures every applicable product from one verified source — through inheritance, never duplication. Nothing invented for children.</p>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {(ov.production_catalog || []).map((p) => (
                  <span key={p} className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gold/12 text-navy border border-gold/40">{p}</span>
                ))}
              </div>
              <a href="/knowledge-manufacturing" className="text-[11px] font-bold text-royal underline" data-testid="ll-inheritance-link">Manufacture more from a verified topic → Manufacturing Dashboard™</a>
            </Panel>
          </div>

          <Panel title="Inherits from the existing QRU Factory™ (never recreated)" icon={CheckCircle2} testid="ll-inherits">
            <div className="flex flex-wrap gap-1.5">
              {(ov.inherits || []).map((c) => (
                <span key={c} className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">{c}</span>
              ))}
            </div>
          </Panel>
        </TabsContent>

        {/* UNIVERSE BIBLE */}
        <TabsContent value="universe" className="space-y-6">
          <Panel title="Little Legacy Learners™ Universe Bible" icon={Globe} accent="royal"
            right={bible?.status !== "Approved"
              ? <button onClick={approveBible} data-testid="ll-approve-bible-btn" className="text-xs font-bold px-3 py-1.5 rounded-md bg-navy text-white hover:bg-navy/90 transition-colors">Approve as v1.0</button>
              : <StatusChip status="Approved" />}
            testid="ll-universe-panel">
            {bible && (
              <div className="space-y-5">
                <p className="text-[11px] text-muted-foreground">Version {bible.version} · <StatusChip status={bible.status} /> · The permanent source of truth. Everything inherits from it.</p>
                {bible.sections?.franchise_foundation && (
                  <div className="grid sm:grid-cols-2 gap-3">
                    {Object.entries(bible.sections.franchise_foundation).map(([k, v]) => (
                      <div key={k} className="border border-navy/10 rounded-md p-3">
                        <p className="text-[10px] font-bold uppercase tracking-wide text-royal mb-1">{k.replace(/_/g, " ")}</p>
                        <p className="text-sm text-navy/85">{v}</p>
                      </div>
                    ))}
                  </div>
                )}
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-wide text-royal mb-1">World Origin</p>
                  <p className="text-sm text-navy/85">{bible.sections?.world_origin}</p>
                </div>
                <div className="grid sm:grid-cols-2 gap-5">
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wide text-royal mb-2">Rules of the World</p>
                    <ul className="space-y-1 text-sm text-navy/85 list-disc pl-4">
                      {(bible.sections?.rules_of_the_world || []).map((r) => <li key={r}>{r}</li>)}
                    </ul>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wide text-red-500 mb-2">Prohibited</p>
                    <div className="flex flex-wrap gap-1">
                      {(bible.sections?.prohibited || []).map((p) => <span key={p} className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-red-50 text-red-600 border border-red-200">{p}</span>)}
                    </div>
                    <p className="text-[10px] font-bold uppercase tracking-wide text-royal mb-2 mt-4">Tone</p>
                    <div className="flex flex-wrap gap-1">
                      {(bible.sections?.tone || []).map((t) => <span key={t} className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-royal/10 text-royal border border-royal/25">{t}</span>)}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </Panel>
          <Panel title={`World Locations (${locations.length})`} icon={MapPin} testid="ll-locations-panel">
            <div className="flex flex-wrap gap-1.5">
              {locations.map((l) => <span key={l.id} className="text-[11px] font-semibold px-2 py-1 rounded-md bg-navy/[0.06] text-navy border border-navy/10">{l.name}</span>)}
            </div>
          </Panel>
        </TabsContent>

        {/* CHARACTERS */}
        <TabsContent value="characters" className="space-y-4">
          <p className="text-sm text-muted-foreground">Six canonical Character Bibles™. Canon-locked fields (name, role, strengths, affirmation, identity, function) cannot change without explicit Founder approval. Approving locks the poster as Version 1.0.</p>
          <div className="grid md:grid-cols-2 gap-4">
            {chars.map((c) => (
              <div key={c.id} className="qru-card p-5" data-testid={`ll-character-${c.key}`}>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-9 h-9 rounded-full flex items-center justify-center shrink-0" style={{ background: `linear-gradient(135deg, ${c.palette?.[0] || "#8A5AD6"}, ${c.palette?.[1] || c.palette?.[0] || "#F5B21A"})` }}>
                      <Sparkles className="w-4 h-4 text-white" />
                    </span>
                    <div className="min-w-0">
                      <p className="font-heading font-bold text-navy truncate">{c.name}</p>
                      <p className="text-[11px] text-muted-foreground truncate">{c.role}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <StatusChip status={c.status === "Approved" ? "Approved" : "Draft"} />
                    {c.canon_locked && <span className="flex items-center gap-1 text-[9px] font-bold text-amber-600"><Lock className="w-3 h-3" /> Canon locked</span>}
                  </div>
                </div>
                <p className="text-[13px] italic text-royal mb-2">“{c.affirmation}”</p>
                <p className="text-[12px] text-navy/80 mb-3">{c.identity}</p>
                <div className="flex flex-wrap gap-1 mb-3">
                  {(c.strengths || []).map((s) => <span key={s} className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-navy/[0.06] text-navy/70 border border-navy/10">{s}</span>)}
                </div>
                <p className="text-[11px] text-muted-foreground mb-3"><span className="font-semibold text-navy/70">Prop:</span> {c.signature_prop} · <span className="font-semibold text-navy/70">v{c.version}</span></p>
                {c.founder_approved
                  ? <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700"><CheckCircle2 className="w-4 h-4" /> Founder-approved · Character Bible v1.0</span>
                  : <button onClick={() => approveCharacter(c.id)} data-testid={`ll-approve-character-${c.key}`} className="text-xs font-bold px-3 py-1.5 rounded-md bg-navy text-white hover:bg-navy/90 transition-colors">Approve Character Bible (Founder)</button>}
              </div>
            ))}
          </div>
        </TabsContent>

        {/* PHASE 2 — CHARACTER MASTERING */}
        <TabsContent value="mastering" className="space-y-4">
          <MasteringTab chars={chars} />
        </TabsContent>

        {/* STORIES — Knowledge-First Episode Blueprints */}
        <TabsContent value="stories" className="space-y-6">
          <EpisodeCreator chars={chars} onCreated={load} />
          <WholeFamily episodes={episodes} />
          <Panel title={`Episode Blueprints (${episodes.length})`} icon={Clapperboard} testid="ll-episodes-panel">
            {episodes.length === 0 ? (
              <p className="text-sm text-muted-foreground py-6 text-center">No episode blueprints yet. Every episode begins with a verified Knowledge Record™ — create one above.</p>
            ) : (
              <div className="space-y-2">
                {episodes.map((e) => (
                  <div key={e.id} className="border border-navy/10 rounded-md p-3 flex items-start justify-between gap-3" data-testid={`ll-episode-${e.id}`}>
                    <div className="min-w-0">
                      <p className="font-semibold text-navy text-sm truncate">{e.title}</p>
                      <p className="text-[11px] text-muted-foreground truncate">{e.kr_topic} · {e.age_band}</p>
                      <p className="text-[11px] text-navy/70 mt-1"><span className="font-semibold">Treasure Takeaway™:</span> {e.treasure_takeaway}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <StatusChip status={e.verification_status === "Verified" ? "Verified" : "Knowledge Required"} tone={e.verification_status === "Verified" ? "emerald" : "amber"} />
                      <StatusChip status={e.status} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </TabsContent>

        {/* PHASE 3 — PILOT STUDIO */}
        <TabsContent value="pilots" className="space-y-6">
          <PilotTab episodes={episodes} />
        </TabsContent>

        {/* PHASE 4 — PRODUCT KITS (kid-format inheriting recipes) */}
        <TabsContent value="kits" className="space-y-6">
          <KitTab episodes={episodes} />
        </TabsContent>

        {/* PHASE 4 — PROJECT ZERO */}
        <TabsContent value="feedback" className="space-y-6">
          <FeedbackTab episodes={episodes} />
        </TabsContent>

        {/* QRU ANIMATION MANUFACTURING PLATFORM */}
        <TabsContent value="animation" className="space-y-6">
          <PerformanceEngineTab episodes={episodes} chars={chars} />
        </TabsContent>

        {/* GOVERNANCE */}
        <TabsContent value="governance" className="space-y-6">
          <Panel title="Production Statuses (governed lifecycle)" icon={ClipboardCheck} accent="navy" testid="ll-statuses">
            <div className="flex flex-wrap gap-1.5">
              {(ov.governance?.statuses || []).map((s) => <StatusChip key={s} status={s} />)}
            </div>
          </Panel>
          <div className="grid md:grid-cols-2 gap-4">
            {Object.entries(ov.governance?.checklists || {}).map(([name, items]) => (
              <Panel key={name} title={name.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase())} icon={ShieldCheck} testid={`ll-checklist-${name}`}>
                <ul className="space-y-1 text-sm text-navy/85">
                  {items.map((it) => (
                    <li key={it} className="flex items-start gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" /> {it}</li>
                  ))}
                </ul>
              </Panel>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function EpisodeCreator({ chars, onCreated }) {
  const [kr, setKr] = useState(null);
  const [title, setTitle] = useState("");
  const [ageBand, setAgeBand] = useState("Early Learners");
  const [character, setCharacter] = useState("");
  const [busy, setBusy] = useState(false);

  const create = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/little-legacy/episodes", {
        kr_id: kr?.id || null, title: title || null, age_band: ageBand,
        featured_character_key: character || null,
      });
      if (!data.ok) { toast.warning(data.message); }
      else if (data.verification_status === "Verified") { toast.success("Episode blueprint drafted from verified Knowledge."); }
      else { toast.warning(data.message || "Held at Knowledge Required — source not verified."); }
      onCreated();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  return (
    <Panel title="Create an Episode Blueprint" icon={Baby} accent="gold" testid="ll-episode-creator">
      <p className="text-[11px] text-muted-foreground mb-4">Knowledge-First: every episode begins with a verified Knowledge Record™. The Factory never invents facts for children.</p>
      <div className="space-y-3">
        <div>
          <label className="text-[11px] font-bold uppercase tracking-wide text-navy/70 block mb-1.5">Knowledge Record (source of truth)</label>
          <KnowledgePicker value={kr?.id} onSelect={setKr} verifiedOnly testid="ll-episode-kr" label="Browse Verified Knowledge" />
        </div>
        <div className="grid sm:grid-cols-3 gap-3">
          <div className="sm:col-span-1">
            <label className="text-[11px] font-bold uppercase tracking-wide text-navy/70 block mb-1.5">Title (optional)</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} data-testid="ll-episode-title"
              placeholder="Auto from topic" className="w-full border border-navy/15 rounded-md px-3 py-2 text-sm focus:border-royal outline-none" />
          </div>
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wide text-navy/70 block mb-1.5">Age Band</label>
            <select value={ageBand} onChange={(e) => setAgeBand(e.target.value)} data-testid="ll-episode-ageband"
              className="w-full border border-navy/15 rounded-md px-3 py-2 text-sm focus:border-royal outline-none bg-white">
              {AGE_BANDS.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wide text-navy/70 block mb-1.5">Featured Character</label>
            <select value={character} onChange={(e) => setCharacter(e.target.value)} data-testid="ll-episode-character"
              className="w-full border border-navy/15 rounded-md px-3 py-2 text-sm focus:border-royal outline-none bg-white">
              <option value="">Any / ensemble</option>
              {chars.map((c) => <option key={c.key} value={c.key}>{c.name}</option>)}
            </select>
          </div>
        </div>
        <button onClick={create} disabled={busy} data-testid="ll-episode-create-btn"
          className="text-xs font-bold px-4 py-2 rounded-md bg-navy text-white hover:bg-navy/90 transition-colors disabled:opacity-50">
          {busy ? "Drafting…" : "Draft Episode Blueprint"}
        </button>
      </div>
    </Panel>
  );
}


function MasteringTab({ chars }) {
  const [masters, setMasters] = useState({});
  const timers = useRef({});

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/little-legacy/masters");
      const map = {};
      (data.masters || []).forEach((m) => { map[m.key] = m; });
      setMasters(map);
    } catch { /* ignore */ }
  }, []);
  useEffect(() => { load(); return () => Object.values(timers.current).forEach(clearInterval); }, [load]);

  const poll = (key) => {
    if (timers.current[key]) clearInterval(timers.current[key]);
    timers.current[key] = setInterval(async () => {
      try {
        const { data } = await api.get(`/little-legacy/characters/${key}/master`);
        setMasters((prev) => ({ ...prev, [key]: data }));
        if (["READY", "Approved", "FAILED"].includes(data.status)) { clearInterval(timers.current[key]); }
      } catch { /* ignore */ }
    }, 5000);
  };

  const startMaster = async (key) => {
    try {
      const { data } = await api.post(`/little-legacy/characters/${key}/master`);
      toast.success(data.message);
      setMasters((prev) => ({ ...prev, [key]: { key, status: "RENDERING" } }));
      poll(key);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const approveMaster = async (key) => {
    try {
      const { data } = await api.post(`/little-legacy/masters/${key}/approve`, { consistency_confirmed: true });
      if (!data.ok) { toast.warning(data.message); return; }
      toast.success(data.message); load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const [consist, setConsist] = useState({});

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Phase 2 — Character Mastering. Generate a model sheet, expression sheet and voice profile for each character (AI-assisted concept art via Gemini Nano Banana — governed reference, not final licensed art). The expression sheet inherits from the model-sheet identity anchor, and Founder approval requires a Character Consistency Check™ before locking the Character Bible™ at v1.0.</p>
      <div className="qru-card p-3 bg-royal/[0.04] border-royal/20 text-[12px] text-navy/85 italic" data-testid="ll-identity-standard">🌟 Identity Standard™: "If a child instantly recognizes the character without reading the name, the identity standard has been achieved."</div>
      <div className="grid md:grid-cols-2 gap-4">
        {chars.map((c) => {
          const m = masters[c.key];
          const st = m?.status;
          return (
            <div key={c.key} className="qru-card p-5" data-testid={`ll-master-${c.key}`}>
              <div className="flex items-center justify-between mb-3">
                <p className="font-heading font-bold text-navy">{c.name}</p>
                {st && <StatusChip status={st === "RENDERING" ? "Generating" : st === "READY" ? "Ready" : st} />}
              </div>
              {st === "RENDERING" && <p className="text-sm text-royal flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Generating master art & voice… (a minute or two)</p>}
              {st === "FAILED" && <p className="text-sm text-red-600">Mastering failed: {m.error}</p>}
              {(st === "READY" || st === "Approved") && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <img src={`${BACKEND}${m.model_sheet_url}`} alt="Model sheet" className="rounded-md border border-navy/10 w-full" data-testid={`ll-master-model-${c.key}`} />
                    <img src={`${BACKEND}${m.expression_sheet_url}`} alt="Expression sheet" className="rounded-md border border-navy/10 w-full" data-testid={`ll-master-expr-${c.key}`} />
                  </div>
                  <p className="text-[11px] text-navy/70 flex items-center gap-1.5"><Mic className="w-3.5 h-3.5 text-royal" /> Voice: <span className="font-semibold">{m.voice_profile?.voice}</span> — {m.voice_profile?.tone}</p>
                  {m.color_palette?.length > 0 && (
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wide text-navy/60">Palette</span>
                      {m.color_palette.map((col) => <span key={col} className="w-4 h-4 rounded-full border border-navy/20" style={{ background: col }} title={col} />)}
                    </div>
                  )}
                  {m.canon_notes?.length > 0 && (
                    <ul className="text-[10px] text-navy/70 space-y-0.5 list-disc pl-4">
                      {m.canon_notes.map((n) => <li key={n}>{n}</li>)}
                    </ul>
                  )}
                  {m.founder_approved
                    ? <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700"><CheckCircle2 className="w-4 h-4" /> Approved · Character Bible v1.0 (Canon locked · anchor set)</span>
                    : (
                      <div className="space-y-2">
                        <label className="flex items-start gap-2 text-[11px] text-navy/80 cursor-pointer" data-testid={`ll-consistency-check-${c.key}`}>
                          <input type="checkbox" checked={!!consist[c.key]} onChange={(e) => setConsist((p) => ({ ...p, [c.key]: e.target.checked }))} className="mt-0.5" data-testid={`ll-consistency-checkbox-${c.key}`} />
                          <span><span className="font-bold">Character Consistency Check™:</span> I confirm the turnaround and expression sheet show the SAME canonical character — skin tone, hair, facial proportions, eyes, smile, clothing, crown, palette.</span>
                        </label>
                        <button onClick={() => approveMaster(c.key)} disabled={!consist[c.key]} data-testid={`ll-approve-master-${c.key}`} className="text-xs font-bold px-3 py-1.5 rounded-md bg-navy text-white hover:bg-navy/90 transition-colors disabled:opacity-50">Approve & Lock as Canon v1.0</button>
                      </div>
                    )}
                </div>
              )}
              {!st && (
                <button onClick={() => startMaster(c.key)} data-testid={`ll-master-btn-${c.key}`} className="text-xs font-bold px-3 py-1.5 rounded-md bg-royal text-white hover:bg-royal/90 transition-colors flex items-center gap-1.5"><Wand2 className="w-3.5 h-3.5" /> Master this character</button>
              )}
              {st === "READY" && !m.founder_approved && <button onClick={() => startMaster(c.key)} className="text-[10px] text-muted-foreground underline mt-2 block">Regenerate</button>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PilotTab({ episodes }) {
  const [pilots, setPilots] = useState({});
  const timers = useRef({});

  const loadOne = useCallback(async (id) => {
    try {
      const { data } = await api.get(`/little-legacy/episodes/${id}/pilot`);
      setPilots((prev) => ({ ...prev, [id]: data }));
      return data.status;
    } catch { return null; }
  }, []);

  useEffect(() => {
    episodes.forEach((e) => loadOne(e.id));
    return () => Object.values(timers.current).forEach(clearInterval);
  }, [episodes, loadOne]);

  const poll = (id) => {
    if (timers.current[id]) clearInterval(timers.current[id]);
    timers.current[id] = setInterval(async () => {
      const st = await loadOne(id);
      if (["READY", "APPROVED", "FAILED", "NONE"].includes(st)) clearInterval(timers.current[id]);
    }, 6000);
  };

  const manufacture = async (id, teaser = false) => {
    try {
      const { data } = await api.post(`/little-legacy/episodes/${id}/pilot`, { teaser });
      if (!data.ok) { toast.warning(data.message); return; }
      toast.success(data.message);
      setPilots((prev) => ({ ...prev, [id]: { status: "RENDERING", teaser } }));
      poll(id);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const approve = async (id) => {
    try {
      const { data } = await api.post(`/little-legacy/pilots/${id}/approve`);
      if (!data.ok) { toast.warning(data.message); return; }
      toast.success(data.message); loadOne(id);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const [publishing, setPublishing] = useState({});
  const publishYouTube = async (id) => {
    setPublishing((p) => ({ ...p, [id]: true }));
    try {
      const { data } = await api.post(`/little-legacy/pilots/${id}/publish-youtube`, { privacy: "private" });
      if (!data.ok) { toast.warning(data.message); return; }
      toast.success(data.message);
      if (data.url) window.open(data.studio_url || data.url, "_blank");
      loadOne(id);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setPublishing((p) => ({ ...p, [id]: false })); }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Phase 3 — Pilot Episode Manufacturing. From a Verified episode blueprint, the Factory manufactures a <span className="font-semibold text-navy">QRU Animated Storybook Pilot™</span> — AI-generated key art with cinematic motion, warm narration and burned captions (image-based motion animation, honestly stated — not frame-by-frame cel animation). Pilots are reviewable DRAFT previews; nothing is auto-published.</p>
      {episodes.length === 0 && <p className="text-sm text-muted-foreground py-6 text-center">No episode blueprints yet. Create one in the Stories tab first.</p>}
      {episodes.map((e) => {
        const p = pilots[e.id] || {};
        const verified = e.verification_status === "Verified";
        return (
          <Panel key={e.id} title={e.title} icon={Film} accent="gold" testid={`ll-pilot-${e.id}`}
            right={<StatusChip status={verified ? "Verified" : "Knowledge Required"} tone={verified ? "emerald" : "amber"} />}>
            <p className="text-[11px] text-muted-foreground mb-3">{e.kr_topic} · {e.age_band}</p>
            {!verified && <p className="text-sm text-amber-700">Knowledge-First: this episode's Knowledge Record is not externally Verified. Verify it before manufacturing a children's pilot.</p>}
            {verified && p.status === "RENDERING" && <p className="text-sm text-royal flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> {p.teaser ? "Rendering a quick 2-scene teaser… (about a minute)" : "Manufacturing pilot — generating scenes, narration & rendering MP4… (a few minutes)"}</p>}
            {verified && p.status === "FAILED" && <p className="text-sm text-red-600">Render failed: {p.error} <button onClick={() => manufacture(e.id, !!p.teaser)} className="underline ml-2">Retry</button></p>}
            {verified && (p.status === "READY" || p.status === "APPROVED") && (
              <div className="space-y-3">
                {p.teaser && <p className="text-[12px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2" data-testid={`ll-teaser-note-${e.id}`}>⚡ Teaser preview (2 scenes) — this is a cheap end-to-end test, not a publishable pilot. Manufacture the full pilot to approve & publish.</p>}
                <video src={`${BACKEND}${p.video_url}`} controls className="w-full rounded-md border border-navy/10 bg-black" data-testid={`ll-pilot-video-${e.id}`} />
                <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                  <span>{p.duration_seconds}s · {p.scenes?.length} scenes · voice {p.voice}</span>
                  <a href={`${BACKEND}${p.captions_url}`} target="_blank" rel="noreferrer" className="text-royal font-semibold underline">Captions (.srt)</a>
                </div>
                {!p.teaser && (
                <div className="grid sm:grid-cols-2 gap-2">
                  {Object.entries(p.gates || {}).map(([g, v]) => (
                    <div key={g} className="flex items-start gap-2 text-[11px]">
                      {v.pass ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" /> : <ShieldCheck className="w-3.5 h-3.5 text-red-500 mt-0.5 shrink-0" />}
                      <span><span className="font-semibold text-navy">{g.replace(/_/g, " ")}:</span> {v.detail}</span>
                    </div>
                  ))}
                </div>
                )}
                {p.teaser ? (
                  <button onClick={() => manufacture(e.id, false)} data-testid={`ll-teaser-fullpilot-${e.id}`} className="text-xs font-bold px-4 py-2 rounded-md bg-royal text-white hover:bg-royal/90 transition-colors flex items-center gap-1.5"><PlayCircle className="w-4 h-4" /> Manufacture Full Pilot (all scenes)</button>
                ) : (
                <>
                {p.publishing_package && <PublishingPackage pkg={p.publishing_package} approved={p.package_approved} />}
                {p.youtube_url && <p className="text-[12px] font-semibold text-emerald-700 flex items-center gap-1.5" data-testid={`ll-youtube-live-${e.id}`}><CheckCircle2 className="w-4 h-4" /> On YouTube ({p.youtube_privacy || "private"}): <a href={p.youtube_url} target="_blank" rel="noreferrer" className="underline">watch</a></p>}
                <div className="flex items-center gap-2 flex-wrap">
                  {p.status === "APPROVED" && <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700"><CheckCircle2 className="w-4 h-4" /> Approved · Publishing Package™ locked</span>}
                  {p.status !== "APPROVED" && <button onClick={() => approve(e.id)} disabled={!p.governance_passed} data-testid={`ll-approve-pilot-${e.id}`} className="text-xs font-bold px-4 py-2 rounded-md bg-navy text-white hover:bg-navy/90 transition-colors disabled:opacity-50">Approve Pilot + Publishing Package™</button>}
                  {!p.youtube_url && <button onClick={() => publishYouTube(e.id)} disabled={!p.governance_passed || publishing[e.id]} data-testid={`ll-publish-youtube-${e.id}`} className="text-xs font-bold px-4 py-2 rounded-md bg-gold text-navy hover:bg-gold/90 transition-colors disabled:opacity-50 flex items-center gap-1.5">{publishing[e.id] ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlayCircle className="w-4 h-4" />} Approve & Publish to YouTube (Private)</button>}
                  <a href="/youtube" className="text-xs font-bold px-3 py-1.5 rounded-md border border-royal/30 text-royal hover:bg-royal/5 transition-colors" data-testid={`ll-open-youtube-${e.id}`}>YouTube Publisher™ →</a>
                </div>
                </>
                )}
              </div>
            )}
            {verified && !["RENDERING", "READY", "APPROVED"].includes(p.status) && (
              <div className="flex items-center gap-2 flex-wrap">
                <button onClick={() => manufacture(e.id, false)} data-testid={`ll-manufacture-pilot-${e.id}`} className="text-xs font-bold px-4 py-2 rounded-md bg-royal text-white hover:bg-royal/90 transition-colors flex items-center gap-1.5"><PlayCircle className="w-4 h-4" /> Manufacture Animated Pilot</button>
                <button onClick={() => manufacture(e.id, true)} data-testid={`ll-teaser-pilot-${e.id}`} className="text-xs font-bold px-4 py-2 rounded-md border border-royal/40 text-royal hover:bg-royal/5 transition-colors flex items-center gap-1.5"><PlayCircle className="w-4 h-4" /> Quick 2-Scene Teaser (cheap test)</button>
              </div>
            )}
          </Panel>
        );
      })}
    </div>
  );
}

function PublishingPackage({ pkg, approved }) {
  const [open, setOpen] = useState(false);
  const Row = ({ label, children }) => (
    <div className="py-1.5 border-b border-navy/5 last:border-0">
      <p className="text-[10px] font-bold uppercase tracking-wide text-royal">{label}</p>
      <div className="text-[12px] text-navy/85 mt-0.5">{children}</div>
    </div>
  );
  return (
    <div className="border border-gold/40 rounded-md bg-gold/[0.04]" data-testid="ll-publishing-package">
      <button onClick={() => setOpen((o) => !o)} className="w-full flex items-center justify-between px-4 py-2.5 text-left" data-testid="ll-package-toggle">
        <span className="font-heading font-bold text-navy text-sm flex items-center gap-2"><Boxes className="w-4 h-4 text-royal" /> Publishing Package™ {approved && <span className="text-[10px] font-bold text-emerald-700">· Approved</span>}</span>
        <span className="text-[11px] text-royal font-semibold">{open ? "Hide" : "Review"}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-0.5">
          <Row label="YouTube Title">{pkg.youtube_title}</Row>
          <Row label="Episode #">{pkg.episode_number}</Row>
          <Row label="SEO Description"><p className="whitespace-pre-wrap text-[11px]">{pkg.seo_description}</p></Row>
          <Row label="Made for Kids">{pkg.made_for_kids ? "Yes (COPPA — Made for Kids)" : "No"}</Row>
          <Row label="Keywords"><div className="flex flex-wrap gap-1">{(pkg.keywords || []).map((k) => <span key={k} className="text-[10px] px-1.5 py-0.5 rounded bg-navy/[0.06] border border-navy/10">{k}</span>)}</div></Row>
          <Row label="Playlist">{pkg.playlist_recommendation}</Row>
          <Row label="Learning Objective">{pkg.learning_objective}</Row>
          <Row label="Thumbnail Recommendation">{pkg.thumbnail_recommendation}</Row>
          <Row label="Parent Discussion Questions"><ul className="list-disc pl-4">{(pkg.parent_discussion_questions || []).map((q) => <li key={q}>{q}</li>)}</ul></Row>
          <Row label="Teacher Discussion Questions"><ul className="list-disc pl-4">{(pkg.teacher_discussion_questions || []).map((q) => <li key={q}>{q}</li>)}</ul></Row>
          <Row label="Call to Action">{pkg.call_to_action}</Row>
          <Row label="Suggested End Screen">{pkg.suggested_end_screen}</Row>
          <Row label="Suggested Next Episode">{pkg.suggested_next_episode}</Row>
          <Row label="Copyright / Footer">{pkg.copyright_footer}</Row>
          <Row label="QRU Brand Verification Checklist">
            <ul className="space-y-0.5">
              {(pkg.brand_verification_checklist || []).map((c) => (
                <li key={c.item} className="flex items-center gap-1.5">
                  {c.ok ? <CheckCircle2 className="w-3 h-3 text-emerald-600" /> : <ShieldCheck className="w-3 h-3 text-amber-500" />} {c.item}
                </li>
              ))}
            </ul>
          </Row>
        </div>
      )}
    </div>
  );
}


function KitAtom({ value }) {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) {
    return (
      <div className="space-y-1">
        {value.map((item, i) => {
          if (item && typeof item === "object" && "front" in item) {
            return <div key={i} className="text-[11px] border-l-2 border-gold/60 pl-2"><span className="font-semibold text-navy">{item.front}</span> — <span className="text-navy/75">{item.back}</span></div>;
          }
          if (item && typeof item === "object" && "prompt" in item) {
            return <div key={i} className="text-[11px] text-navy/80">{item.prompt} → <span className="font-semibold">{item.answer}</span></div>;
          }
          return <div key={i} className="text-[11px] text-navy/80 flex gap-1.5"><span className="text-gold">•</span> {String(item)}</div>;
        })}
      </div>
    );
  }
  return <span className="text-[11px] text-navy/80">{String(value)}</span>;
}

function KitValue({ value }) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return (
      <div className="space-y-1">
        {Object.entries(value).map(([k, v]) => (
          <div key={k} className="text-[11px]">
            <span className="font-semibold text-navy/60 uppercase tracking-wide text-[9px]">{k.replace(/_/g, " ")}: </span>
            <KitAtom value={v} />
          </div>
        ))}
      </div>
    );
  }
  return <KitAtom value={value} />;
}


function KitTab({ episodes }) {
  const [kits, setKits] = useState({});
  const timers = useRef({});
  const verified = episodes.filter((e) => e.verification_status === "Verified");

  const loadOne = useCallback(async (id) => {
    try {
      const { data } = await api.get(`/little-legacy/episodes/${id}/kit`);
      setKits((prev) => ({ ...prev, [id]: data }));
      return data.status;
    } catch { return null; }
  }, []);
  useEffect(() => {
    verified.forEach((e) => loadOne(e.id));
    return () => Object.values(timers.current).forEach(clearInterval);
  }, [episodes]); // eslint-disable-line

  const poll = (id) => {
    if (timers.current[id]) clearInterval(timers.current[id]);
    timers.current[id] = setInterval(async () => {
      const st = await loadOne(id);
      if (["READY", "APPROVED", "FAILED", "NONE"].includes(st)) clearInterval(timers.current[id]);
    }, 6000);
  };
  const make = async (id) => {
    try {
      const { data } = await api.post(`/little-legacy/episodes/${id}/kit`);
      if (!data.ok) { toast.warning(data.message); return; }
      toast.success(data.message);
      setKits((prev) => ({ ...prev, [id]: { status: "RENDERING" } })); poll(id);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const approve = async (id) => {
    try {
      const { data } = await api.post(`/little-legacy/kits/${id}/approve`);
      if (!data.ok) { toast.warning(data.message); return; }
      toast.success(data.message); loadOne(id);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Phase 4 — Product Inheritance. One verified Knowledge Record™ manufactures the full kid catalog through inheritance (no duplication): coloring page, social/marketing asset, storybook cover, Knowledge Cards™, workbook/activity pack, and parent + teacher guides. Artwork inherits the approved Character Bible v1.0 identity anchor.</p>
      {verified.length === 0 && <p className="text-sm text-muted-foreground py-6 text-center">No verified episode blueprints yet. Create one in the Stories tab.</p>}
      {verified.map((e) => {
        const k = kits[e.id] || {};
        return (
          <Panel key={e.id} title={e.title} icon={Boxes} accent="gold" testid={`ll-kit-${e.id}`}
            right={k.status === "APPROVED" ? <StatusChip status="Approved" /> : k.consistency_inherited === false ? <StatusChip status="Consistency Flagged" tone="amber" /> : null}>
            <p className="text-[11px] text-muted-foreground mb-3">{e.kr_topic} · {e.age_band}</p>
            {k.status === "RENDERING" && <p className="text-sm text-royal flex items-center gap-2"><Loader2 className="w-4 h-4 animate-spin" /> Manufacturing the full product family…</p>}
            {k.status === "FAILED" && <p className="text-sm text-red-600">Failed: {k.error} <button onClick={() => make(e.id)} className="underline ml-2">Retry</button></p>}
            {(k.status === "READY" || k.status === "APPROVED") && (
              <div className="space-y-4">
                {k.consistency_inherited === false && <p className="text-[11px] text-amber-700">⚠ {k.consistency_note}</p>}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {(k.products || []).filter((p) => p.kind === "image").map((p) => (
                    <div key={p.format} className="text-center" data-testid={`ll-kit-img-${e.id}-${p.format.split(' ')[0]}`}>
                      <img src={`${BACKEND}${p.url}`} alt={p.format} className="rounded-md border border-navy/10 w-full mb-1" />
                      <p className="text-[10px] font-semibold text-navy/70">{p.format}</p>
                    </div>
                  ))}
                </div>
                <div className="grid sm:grid-cols-2 gap-2">
                  {(k.products || []).filter((p) => p.kind === "text").map((p) => (
                    <div key={p.format} className="border border-navy/10 rounded-md p-3" data-testid={`ll-kit-text-${e.id}-${p.format.split(' ')[0]}`}>
                      <p className="text-[11px] font-bold text-royal mb-1.5">{p.format}</p>
                      <div className="max-h-48 overflow-auto"><KitValue value={p.data} /></div>
                    </div>
                  ))}
                </div>
                {k.status === "APPROVED"
                  ? <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700"><CheckCircle2 className="w-4 h-4" /> Product Kit approved · full family ready</span>
                  : <button onClick={() => approve(e.id)} data-testid={`ll-approve-kit-${e.id}`} className="text-xs font-bold px-4 py-2 rounded-md bg-navy text-white hover:bg-navy/90 transition-colors">Approve Product Kit</button>}
              </div>
            )}
            {!["RENDERING", "READY", "APPROVED"].includes(k.status) && (
              <button onClick={() => make(e.id)} data-testid={`ll-make-kit-${e.id}`} className="text-xs font-bold px-4 py-2 rounded-md bg-royal text-white hover:bg-royal/90 transition-colors flex items-center gap-1.5"><Boxes className="w-4 h-4" /> Manufacture Product Kit</button>
            )}
          </Panel>
        );
      })}
    </div>
  );
}

function FeedbackTab({ episodes }) {
  const [ep, setEp] = useState(episodes[0]?.id || "");
  const [role, setRole] = useState("parent");
  const [rating, setRating] = useState(5);
  const [before, setBefore] = useState(2);
  const [after, setAfter] = useState(5);
  const [comment, setComment] = useState("");
  const [improve, setImprove] = useState("");
  const [loop, setLoop] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (id) => {
    if (!id) return;
    try { const { data } = await api.get(`/little-legacy/feedback?episode_id=${id}`); setLoop(data); } catch { /* ignore */ }
  }, []);
  useEffect(() => { load(ep); }, [ep, load]);

  const submit = async () => {
    if (!ep) { toast.warning("Choose an episode."); return; }
    setBusy(true);
    try {
      const { data } = await api.post("/little-legacy/feedback", {
        episode_id: ep, role, rating: Number(rating),
        understanding_before: Number(before), understanding_after: Number(after),
        comment, suggested_improvement: improve,
      });
      if (!data.ok) { toast.warning(data.message); } else { toast.success(data.message); }
      setComment(""); setImprove(""); load(ep);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Phase 4 — Little Legacy Project Zero™. Real parent, teacher and child feedback + learning outcomes flow back into the originating Knowledge Record™, so every future product improves through inheritance. Deterministic — no fabricated metrics (Treasure Standard™).</p>
      <Panel title="Share Feedback" icon={ClipboardCheck} accent="royal" testid="ll-feedback-form">
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wide text-navy/70 block mb-1.5">Episode</label>
            <select value={ep} onChange={(e) => setEp(e.target.value)} data-testid="ll-feedback-episode" className="w-full border border-navy/15 rounded-md px-3 py-2 text-sm bg-white">
              {episodes.map((e) => <option key={e.id} value={e.id}>{e.title}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wide text-navy/70 block mb-1.5">I am a…</label>
            <select value={role} onChange={(e) => setRole(e.target.value)} data-testid="ll-feedback-role" className="w-full border border-navy/15 rounded-md px-3 py-2 text-sm bg-white">
              <option value="parent">Parent</option><option value="teacher">Teacher</option><option value="child">Child</option>
            </select>
          </div>
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wide text-navy/70 block mb-1.5">Rating (1–5)</label>
            <input type="number" min="1" max="5" value={rating} onChange={(e) => setRating(e.target.value)} data-testid="ll-feedback-rating" className="w-full border border-navy/15 rounded-md px-3 py-2 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div><label className="text-[10px] font-bold uppercase text-navy/70 block mb-1">Understood before</label><input type="number" min="1" max="5" value={before} onChange={(e) => setBefore(e.target.value)} data-testid="ll-feedback-before" className="w-full border border-navy/15 rounded-md px-2 py-2 text-sm" /></div>
            <div><label className="text-[10px] font-bold uppercase text-navy/70 block mb-1">Understood after</label><input type="number" min="1" max="5" value={after} onChange={(e) => setAfter(e.target.value)} data-testid="ll-feedback-after" className="w-full border border-navy/15 rounded-md px-2 py-2 text-sm" /></div>
          </div>
        </div>
        <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="What did the child learn / enjoy?" data-testid="ll-feedback-comment" className="w-full border border-navy/15 rounded-md px-3 py-2 text-sm mt-3" rows={2} />
        <textarea value={improve} onChange={(e) => setImprove(e.target.value)} placeholder="Suggested improvement (feeds the Knowledge Record)" data-testid="ll-feedback-improve" className="w-full border border-navy/15 rounded-md px-3 py-2 text-sm mt-2" rows={2} />
        <button onClick={submit} disabled={busy} data-testid="ll-feedback-submit" className="text-xs font-bold px-4 py-2 rounded-md bg-navy text-white hover:bg-navy/90 transition-colors disabled:opacity-50 mt-3">{busy ? "Submitting…" : "Submit Feedback → Knowledge Record"}</button>
      </Panel>
      {loop && (
        <Panel title="Enterprise Learning — feeds the originating Knowledge Record" icon={GitBranch} testid="ll-feedback-loop">
          <p className="text-sm text-navy/80 mb-2">Feedback count: <span className="font-bold">{loop.aggregate?.feedback_count ?? 0}</span></p>
          {loop.aggregate?.improvement_signals?.length > 0 && (
            <div className="mb-2"><p className="text-[10px] font-bold uppercase text-royal mb-1">Improvement signals</p>
              <div className="flex flex-wrap gap-1">{loop.aggregate.improvement_signals.map((s) => <span key={s.signal} className="text-[10px] px-1.5 py-0.5 rounded bg-navy/[0.06] border border-navy/10">{s.signal} ({s.mentions})</span>)}</div>
            </div>
          )}
          <div className="space-y-1.5 max-h-60 overflow-auto">
            {(loop.episode_feedback || loop.feedback || []).map((f) => (
              <div key={f.id} className="text-[11px] border border-navy/10 rounded p-2" data-testid={`ll-feedback-item-${f.id}`}>
                <span className="font-semibold text-navy">{f.source}</span> · ★{f.rating ?? "—"} · {f.comment || f.summary}
                {f.suggested_improvement && <span className="text-royal"> · 💡 {f.suggested_improvement}</span>}
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

function WholeFamily({ episodes }) {
  const [ep, setEp] = useState("");
  const [fam, setFam] = useState(null);
  const timer = useRef(null);
  const verified = episodes.filter((e) => e.verification_status === "Verified");
  useEffect(() => { if (!ep && verified[0]) setEp(verified[0].id); }, [episodes]); // eslint-disable-line
  useEffect(() => () => timer.current && clearInterval(timer.current), []);

  const poll = (id) => {
    timer.current && clearInterval(timer.current);
    timer.current = setInterval(async () => {
      try { const { data } = await api.get(`/little-legacy/episodes/${id}/family`); setFam(data); if (data.ready || (data.pilot.status === "FAILED" && data.kit.status !== "RENDERING")) clearInterval(timer.current); } catch { /* ignore */ }
    }, 6000);
  };
  const go = async () => {
    if (!ep) return;
    try {
      const { data } = await api.post(`/little-legacy/episodes/${ep}/family`);
      if (!data.ok) { toast.warning(data.message); return; }
      toast.success(data.message); setFam({ pilot: { status: "RENDERING" }, kit: { status: "RENDERING" }, ready: false }); poll(ep);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  return (
    <Panel title="Manufacture the Whole Family™ — one click, one verified Knowledge Record" icon={Boxes} accent="royal" testid="ll-whole-family">
      <p className="text-[11px] text-muted-foreground mb-3">Fires the animated pilot AND the full Product Kit (coloring page, social asset, storybook cover, Knowledge Cards, workbook, parent & teacher guides, song & mini-course) together. Review the video in Pilot Studio and the kit in Product Kits.</p>
      <div className="flex items-center gap-2 mb-3">
        <select value={ep} onChange={(e) => setEp(e.target.value)} data-testid="ll-family-episode" className="border border-navy/15 rounded-md px-3 py-2 text-sm bg-white">
          {verified.map((e) => <option key={e.id} value={e.id}>{e.title}</option>)}
        </select>
        <button onClick={go} disabled={!ep} data-testid="ll-family-go" className="text-xs font-bold px-4 py-2 rounded-md bg-royal text-white hover:bg-royal/90 transition-colors disabled:opacity-50 flex items-center gap-1.5"><Sparkles className="w-4 h-4" /> Manufacture the Whole Family</button>
      </div>
      {fam && (
        <div className="flex gap-4 text-[12px]">
          <span className="flex items-center gap-1.5"><Film className="w-4 h-4 text-royal" /> Pilot: <b>{fam.pilot.status}</b>{fam.pilot.status === "RENDERING" && <Loader2 className="w-3.5 h-3.5 animate-spin" />}</span>
          <span className="flex items-center gap-1.5"><Boxes className="w-4 h-4 text-royal" /> Kit: <b>{fam.kit.status}</b>{fam.kit.status === "RENDERING" && <Loader2 className="w-3.5 h-3.5 animate-spin" />}</span>
          {fam.ready && <span className="text-emerald-700 font-bold flex items-center gap-1"><CheckCircle2 className="w-4 h-4" /> Family ready — review & approve</span>}
        </div>
      )}
    </Panel>
  );
}



function PerformanceEngineTab({ episodes, chars }) {
  const [status, setStatus] = useState(null);
  const [lib, setLib] = useState(null);
  const [identities, setIdentities] = useState([]);
  const [ep, setEp] = useState("");
  const [plan, setPlan] = useState(null);
  const [openId, setOpenId] = useState(null);
  const verified = episodes.filter((e) => e.verification_status === "Verified");

  useEffect(() => {
    (async () => {
      try {
        const [s, l, id] = await Promise.all([
          api.get("/little-legacy/animation/status"),
          api.get("/little-legacy/animation/performance-library"),
          api.get("/little-legacy/animation/identities"),
        ]);
        setStatus(s.data); setLib(l.data); setIdentities(id.data.identities || []);
      } catch { /* ignore */ }
    })();
  }, []);
  useEffect(() => { if (!ep && verified[0]) setEp(verified[0].id); }, [episodes]); // eslint-disable-line
  useEffect(() => {
    if (!ep) return;
    api.get(`/little-legacy/animation/performance-plan/${ep}`).then((r) => setPlan(r.data)).catch(() => {});
  }, [ep]);

  const activate = async (pid) => {
    try { const { data } = await api.post(`/little-legacy/animation/providers/${pid}/activate`); if (!data.ok) toast.warning(data.message); else { toast.success(data.message); const s = await api.get("/little-legacy/animation/status"); setStatus(s.data); } }
    catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const buildPlan = async () => {
    try { const { data } = await api.post(`/little-legacy/animation/performance-plan/${ep}`); setPlan(data); toast.success("Performance Plan built."); }
    catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  if (!status || !lib) return <p className="text-muted-foreground">Loading Performance Engine™…</p>;

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground">QRU Animation Manufacturing Platform™ — a vendor-agnostic engine that separates <span className="font-semibold text-navy">identity</span> from <span className="font-semibold text-navy">motion</span>. Any current or future AI animation model plugs into the Provider Layer without changing the rest of the Factory.</p>

      {/* Pipeline */}
      <Panel title="QRU Character Performance Engine™ — Pipeline" icon={Workflow} accent="royal" testid="ll-anim-pipeline">
        <div className="flex flex-wrap items-center gap-2">
          {status.pipeline.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${s === "Performance Plan" ? "bg-gold/15 border-gold/50 text-navy" : "bg-navy/[0.06] border-navy/10 text-navy/80"}`}>{s}{s === "Performance Plan" && " ✨"}</span>
              {i < status.pipeline.length - 1 && <span className="text-navy/30">→</span>}
            </div>
          ))}
        </div>
        <p className="text-[11px] text-muted-foreground mt-3">{status.render_note}</p>
      </Panel>

      {/* Provider Layer */}
      <Panel title="Animation Provider Layer (pluggable · no vendor lock-in)" icon={Plug} testid="ll-anim-providers">
        <div className="space-y-2">
          {status.provider_layer.map((p) => (
            <div key={p.id} className="flex items-center justify-between border border-navy/10 rounded-md p-3" data-testid={`ll-provider-${p.id}`}>
              <div>
                <p className="text-sm font-semibold text-navy">{p.name} {p.active && <span className="text-[10px] font-bold text-emerald-700">· ACTIVE</span>}</p>
                <p className="text-[11px] text-muted-foreground">{p.produces_character_motion ? "Produces true character motion" : "Cinematic camera motion"} · {p.available ? "Available" : p.reason}</p>
              </div>
              {!p.active && p.available && <button onClick={() => activate(p.id)} data-testid={`ll-activate-${p.id}`} className="text-xs font-bold px-3 py-1.5 rounded-md bg-navy text-white hover:bg-navy/90 transition-colors">Activate</button>}
              {!p.available && <span className="text-[10px] font-bold text-amber-600 px-2 py-1 rounded bg-amber-50 border border-amber-200">Provider slot — connect a model</span>}
            </div>
          ))}
        </div>
      </Panel>

      {/* Character Identity System */}
      <Panel title="Canonical Character Identity System™ (stored once · handed to every provider)" icon={Users} accent="navy" testid="ll-anim-identities">
        <div className="grid md:grid-cols-2 gap-3">
          {identities.map((idp) => (
            <div key={idp.key} className="border border-navy/10 rounded-md" data-testid={`ll-identity-${idp.key}`}>
              <button onClick={() => setOpenId(openId === idp.key ? null : idp.key)} className="w-full flex items-center justify-between px-3 py-2.5 text-left">
                <span className="font-semibold text-navy text-sm">{idp.character} {idp.canon_locked && <Lock className="w-3 h-3 inline text-amber-600" />}</span>
                <span className="text-[11px] text-royal">{openId === idp.key ? "Hide" : "Identity Package"}</span>
              </button>
              {openId === idp.key && (
                <div className="px-3 pb-3 space-y-1.5 text-[11px] text-navy/80">
                  {idp.canonical_appearance?.anchor_url && <img src={`${BACKEND}${idp.canonical_appearance.anchor_url}`} alt="anchor" className="rounded border border-navy/10 w-full mb-2" />}
                  <div><b>Palette:</b> {(idp.color_palette || []).map((c) => <span key={c} className="inline-block w-3 h-3 rounded-full border border-navy/20 ml-1 align-middle" style={{ background: c }} />)}</div>
                  <div><b>Facial proportions:</b> {idp.facial_proportions}</div>
                  <div><b>Voice:</b> {idp.voice?.voice} — {idp.voice?.tone}</div>
                  <div><b>Movement style:</b> {idp.movement_style}</div>
                  <div><b>Emotional style:</b> {idp.emotional_style}</div>
                  <div><b>Vocabulary:</b> {(idp.vocabulary || []).join(" · ")}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </Panel>

      {/* Performance Library */}
      <Panel title={`Character Performance Library™ — ${lib.total_shipped} shipped / ${lib.total_target} target`} icon={Boxes} accent="gold" testid="ll-anim-library">
        <p className="text-[11px] text-muted-foreground mb-3">{lib.note}</p>
        <div className="grid sm:grid-cols-2 gap-3">
          {lib.categories.map((c) => (
            <div key={c.category} className="border border-navy/10 rounded-md p-3" data-testid={`ll-lib-${c.category}`}>
              <p className="text-[11px] font-bold text-navy mb-1">{c.label} <span className="text-muted-foreground font-normal">({c.shipped}/{c.target_capacity})</span></p>
              <div className="flex flex-wrap gap-1">{c.primitives.map((p) => <span key={p} className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-navy/[0.06] text-navy/70 border border-navy/10">{p}</span>)}</div>
            </div>
          ))}
        </div>
      </Panel>

      {/* Performance Plan */}
      <Panel title="Performance Plan (data-driven direction per beat)" icon={GitBranch} testid="ll-anim-plan">
        <div className="flex items-center gap-2 mb-3">
          <select value={ep} onChange={(e) => setEp(e.target.value)} data-testid="ll-plan-episode" className="border border-navy/15 rounded-md px-3 py-2 text-sm bg-white">
            {verified.map((e) => <option key={e.id} value={e.id}>{e.title}</option>)}
          </select>
          <button onClick={buildPlan} disabled={!ep} data-testid="ll-build-plan" className="text-xs font-bold px-3 py-2 rounded-md bg-royal text-white hover:bg-royal/90 transition-colors disabled:opacity-50">Build / Rebuild Plan</button>
        </div>
        {plan?.beats?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-[11px]">
              <thead><tr className="text-left text-navy/60 border-b border-navy/10">
                <th className="py-1 pr-2">#</th><th className="pr-2">Scene</th><th className="pr-2">Expression</th><th className="pr-2">Gesture</th><th className="pr-2">Walk</th><th className="pr-2">Emotion</th><th className="pr-2">Camera</th><th className="pr-2">Pose</th>
              </tr></thead>
              <tbody>
                {plan.beats.map((b) => (
                  <tr key={b.beat} className="border-b border-navy/5" data-testid={`ll-beat-${b.beat}`}>
                    <td className="py-1 pr-2">{b.beat}</td><td className="pr-2 font-semibold text-navy">{b.scene}</td>
                    <td className="pr-2">{b.expression}</td><td className="pr-2">{b.gesture}</td><td className="pr-2">{b.walk}</td>
                    <td className="pr-2">{b.emotion}</td><td className="pr-2">{b.camera}</td><td className="pr-2">{b.educational_pose}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <p className="text-sm text-muted-foreground py-4 text-center">No plan yet — build one for the selected episode.</p>}
      </Panel>
    </div>
  );
}

