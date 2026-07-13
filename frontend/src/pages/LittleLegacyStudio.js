import { useEffect, useState, useCallback } from "react";
import api, { formatApiError } from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, MetricCard, StatusChip, GovernedBy } from "@/components/qru";
import { KnowledgePicker } from "@/components/KnowledgePicker";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";
import {
  Sparkles, Users, BookOpen, Clapperboard, ShieldCheck, Lock, CheckCircle2,
  Globe, MapPin, GitBranch, Boxes, Baby, ClipboardCheck,
} from "lucide-react";

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
          <TabsTrigger value="stories" data-testid="ll-tab-stories">Stories</TabsTrigger>
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
              <p className="text-[11px] text-muted-foreground mb-3">Later phases. The Factory manufactures every applicable product from one verified source — nothing invented for children.</p>
              <div className="flex flex-wrap gap-1.5">
                {(ov.production_catalog || []).map((p) => (
                  <span key={p} className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gold/12 text-navy border border-gold/40">{p}</span>
                ))}
              </div>
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

        {/* STORIES — Knowledge-First Episode Blueprints */}
        <TabsContent value="stories" className="space-y-6">
          <EpisodeCreator chars={chars} onCreated={load} />
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
