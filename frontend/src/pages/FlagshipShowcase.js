import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, Film, Search, CheckCircle2, X, ShieldAlert, Lock, Unlock, RefreshCw, ThumbsUp, Ban,
  Award, ShieldCheck, Clapperboard, Sparkles, Landmark, Palette, Brain, GraduationCap,
  BadgeCheck, ClipboardCheck, TrendingUp,
} from "lucide-react";

// MO-028 · Autonomous Improvement Loop™ — the specialized intelligences ("departments") of the civilization.
const DEPT_META = {
  creative_director: { icon: Clapperboard, color: "text-royal", bar: "bg-royal" },
  design_intelligence: { icon: Palette, color: "text-fuchsia-600", bar: "bg-fuchsia-500" },
  director_intelligence: { icon: Film, color: "text-indigo-600", bar: "bg-indigo-500" },
  learning_experience: { icon: GraduationCap, color: "text-emerald-600", bar: "bg-emerald-500" },
  knowledge_verification: { icon: BadgeCheck, color: "text-sky-600", bar: "bg-sky-500" },
  qa: { icon: ClipboardCheck, color: "text-gold", bar: "bg-gold" },
};

const API_BASE = (process.env.REACT_APP_BACKEND_URL || "") + "/api/media-library/asset";

const DEFAULT_NARRATION =
  "Forex means trading the world's currencies across global markets. Every trade carries real risk of loss that you must respect. Understanding how currency pairs move takes patient study and practice. Learning to trade responsibly builds lasting confidence over time. A calm and focused mind makes clearer decisions. Take a slow breath and reflect on your progress with gratitude.";

export default function FlagshipShowcase() {
  const [searchParams] = useSearchParams();
  const continuityProjectId = searchParams.get("project");
  const [gov, setGov] = useState([]);
  const [modes, setModes] = useState(null);
  const [mode, setMode] = useState("human_approval_required");
  const [narration, setNarration] = useState(DEFAULT_NARRATION);
  const [topic, setTopic] = useState("forex");
  const [aspect, setAspect] = useState("landscape");
  const [productTitle, setProductTitle] = useState("Forex Foundations");
  const [matchRes, setMatchRes] = useState(null);
  const [matching, setMatching] = useState(false);
  const [creative, setCreative] = useState(null);
  const [creativeApproved, setCreativeApproved] = useState(false);
  const [styleChoice, setStyleChoice] = useState(null);
  const [sceneState, setSceneState] = useState({}); // idx -> {selectedId, approved, rejected, locked}
  const [producing, setProducing] = useState(false);
  const [result, setResult] = useState(null);
  const [certifying, setCertifying] = useState(false);
  // MO-028 Autonomous Improvement Loop™ — the civilization improves before the Founder reviews.
  const [threshold, setThreshold] = useState(90);
  const [loop, setLoop] = useState(null);
  const [loopRunning, setLoopRunning] = useState(false);
  const [deptAnim, setDeptAnim] = useState({}); // dept -> animated progress %
  const [candidateDecision, setCandidateDecision] = useState(null);

  useEffect(() => {
    api.get("/media-library/showcase/modes").then((r) => setModes(r.data)).catch(() => {});
    api.get("/governance-binding/strip/media").then((r) => setGov(r.data.governed_by)).catch(() => {});
  }, []);

  const runMatch = async () => {
    if (!narration.trim()) return toast.error("Enter narration to match.");
    setMatching(true); setResult(null);
    try {
      const { data } = await api.post("/media-library/scene-match", { narration, topic, aspect });
      setMatchRes(data);
      setCreativeApproved(false);
      fetchCreative(data, null);
      // Initialise per-scene state, preserving any locked selections from a prior run.
      setSceneState((prev) => {
        const next = {};
        data.scenes.forEach((s) => {
          const old = prev[s.scene_index];
          if (old?.locked) { next[s.scene_index] = old; return; }
          next[s.scene_index] = {
            selectedId: s.selected_provider_asset_id || (s.candidates[0]?.provider_asset_id ?? null),
            approved: false, rejected: false, locked: false,
          };
        });
        return next;
      });
    } catch (e) { toast.error(e.response?.data?.detail || "Scene match failed."); }
    finally { setMatching(false); }
  };

  const fetchCreative = (mr, style) => {
    const src = mr || matchRes;
    if (!src) return;
    api.post("/media-library/creative-direction", {
      topic, narration, style,
      scenes: src.scenes.map((s) => {
        const sel = s.candidates.find((c) => c.provider_asset_id === s.selected_provider_asset_id) || s.candidates[0];
        return { scene_text: s.scene_text, learning_purpose: s.learning_purpose, match_score: sel?.match_score };
      }),
    }).then((r) => { setCreative(r.data); setStyleChoice(r.data.visual_mood); runLoop(src); }).catch(() => setCreative(null));
  };

  // MO-028 · Autonomous Improvement Loop™ — evaluate → auto-assign to departments → improve → re-evaluate → Gold Master Candidate.
  const runLoop = async (mr) => {
    const src = mr || matchRes;
    if (!src) return;
    setLoopRunning(true); setLoop(null); setDeptAnim({}); setCandidateDecision(null);
    try {
      const scenes = src.scenes.map((s) => {
        const sel = s.candidates.find((c) => c.provider_asset_id === s.selected_provider_asset_id) || s.candidates[0];
        return { scene_text: s.scene_text, learning_purpose: s.learning_purpose, match_score: sel?.match_score };
      });
      const { data } = await api.post("/media-library/improvement-loop", { scenes, narration, topic, threshold });
      setLoop(data);
      // Animate each department's progress bar from 0 → its honest final progress (live "civilization at work" feel).
      setTimeout(() => {
        const target = {};
        (data.civilization_status || []).forEach((d) => { target[d.department] = d.progress; });
        setDeptAnim(target);
      }, 120);
    } catch (e) { toast.error(e.response?.data?.detail || "Autonomous Improvement Loop failed."); }
    finally { setLoopRunning(false); }
  };

  const approveCandidate = () => {
    setCandidateDecision("approved");
    setCreativeApproved(true);
    toast.success("Gold Master Candidate approved. Ready to manufacture.");
    setTimeout(() => { const el = document.querySelector('[data-testid="fs-manufacture"]'); el && el.scrollIntoView({ behavior: "smooth" }); }, 100);
  };
  const requestCandidateChanges = () => {
    setCandidateDecision("changes");
    setCreativeApproved(false);
    toast.message("Sent back to the civilization. Adjust scenes, then the departments re-run.");
    const el = document.querySelector('[data-testid="fs-scenes"]'); el && el.scrollIntoView({ behavior: "smooth" });
  };

  const setScene = (idx, patch) => setSceneState((s) => ({ ...s, [idx]: { ...s[idx], ...patch } }));
  const selectCandidate = (idx, cid) => { if (sceneState[idx]?.locked) return toast.message("Scene locked — unlock to replace."); setScene(idx, { selectedId: cid }); };
  const approveScene = (idx) => setScene(idx, { approved: true, rejected: false });
  const rejectScene = (idx) => setScene(idx, { rejected: true, approved: false });
  const toggleLock = (idx) => setScene(idx, { locked: !sceneState[idx]?.locked });

  const scenesForProduction = () => {
    if (!matchRes) return [];
    return matchRes.scenes
      .filter((s) => !sceneState[s.scene_index]?.rejected && sceneState[s.scene_index]?.selectedId)
      .map((s) => {
        const sel = s.candidates.find((c) => c.provider_asset_id === sceneState[s.scene_index].selectedId);
        return sel && { scene_index: s.scene_index, scene_text: s.scene_text, learning_purpose: s.learning_purpose, approved: !!sceneState[s.scene_index]?.approved, selected: sel };
      })
      .filter(Boolean);
  };

  const allApproved = () => {
    const list = scenesForProduction();
    return list.length > 0 && list.every((s) => s.approved);
  };

  const produce = async () => {
    setProducing(true); setResult(null);
    try {
      const rejected = matchRes.scenes.filter((s) => sceneState[s.scene_index]?.rejected)
        .map((s) => s.candidates.find((c) => c.provider_asset_id === sceneState[s.scene_index]?.selectedId)?.provider_asset_id).filter(Boolean);
      const payload = { product_title: productTitle, topic, aspect, narration, approval_mode: mode, rejected_assets: rejected };
      if (continuityProjectId) payload.continuity_project_id = continuityProjectId;
      if (mode === "human_approval_required") payload.scenes = scenesForProduction();
      const { data } = await api.post("/media-library/showcase/produce", payload);
      setResult(data);
      if (data.ok) toast.success(data.is_draft_preview ? "Draft preview manufactured." : "Flagship Showcase manufactured.");
      else toast.error(data.error || "Manufacturing stopped — see the failed stage.");
    } catch (e) { toast.error(e.response?.data?.detail || "Could not reach the production engine."); }
    finally { setProducing(false); }
  };

  const certify = async () => {
    if (!result?.showcase_asset?.qru_asset_id) return;
    setCertifying(true);
    try {
      const { data } = await api.post(`/media-library/showcase/${result.showcase_asset.qru_asset_id}/certify-gold-master`);
      toast.success("Gold Master Certified™.");
      setResult((r) => ({ ...r, showcase_asset: { ...r.showcase_asset, gold_master_certified: true, production_status: "Gold Master Certified™" }, gold_master: data }));
    } catch (e) { toast.error(e.response?.data?.detail || "Certification blocked."); }
    finally { setCertifying(false); }
  };

  if (!modes) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  const sceneList = scenesForProduction();
  const canProduce = mode === "auto_select_draft" ? true : (allApproved() && creativeApproved);

  return (
    <div>
      <PageHeader
        overline="QRU Controlled Flagship Showcase™ Pilot · MO-012"
        title="Flagship Showcase Factory"
        description="One governed 30–60 second multi-scene video factory built on the verified Milestone 001 pipeline. Narration becomes scenes, each scene is human-approved with brand-safe licensed footage, then assembled into a single MP4 with full QA, checksums and a permanent Production Acceptance Record."
        actions={<VerifiedBadge label="Human Approval Gates · Treasure Standard™" testid="fs-badge" />}
      />
      <GovernedBy standards={gov} className="mb-4" testid="fs-governed-by" />

      {/* Approval mode */}
      <Panel title="Approval Mode" icon={ShieldCheck} accent="royal" testid="fs-modes" className="mb-6">
        <div className="grid md:grid-cols-3 gap-3">
          {Object.entries(modes.modes).map(([id, m]) => {
            const locked = !m.enabled;
            const active = mode === id;
            return (
              <button key={id} disabled={locked} onClick={() => !locked && setMode(id)} data-testid={`fs-mode-${id}`}
                className={`text-left border rounded-md p-3 transition-colors ${active ? "border-royal ring-2 ring-royal/30 bg-royal/[0.04]" : "border-navy/15"} ${locked ? "opacity-50 cursor-not-allowed" : "hover:border-royal/50"}`}>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-bold text-navy">{m.label}</p>
                  {m.default && <span className="text-[9px] px-1.5 py-0.5 rounded bg-gold/20 text-navy border border-gold/40">Default</span>}
                  {locked && <Lock className="w-3.5 h-3.5 text-muted-foreground" />}
                </div>
                <p className="text-[11px] text-muted-foreground">{m.note}</p>
                {id === "governed_auto_select" && <p className="text-[10px] text-amber-700 mt-1">{modes.approved_run_count}/5 approved runs · {modes.governed_auto_select_unlocked ? "authorized" : "not yet unlocked"}</p>}
              </button>
            );
          })}
        </div>
      </Panel>

      {/* Narration → scenes */}
      <Panel title="1 · Narration & Scene Segmentation" icon={Search} accent="gold" testid="fs-input" className="mb-6">
        <div className="grid md:grid-cols-4 gap-3 mb-3">
          <textarea data-testid="fs-narration" value={narration} onChange={(e) => setNarration(e.target.value)} rows={4}
            className="md:col-span-2 border rounded-sm p-2 text-sm" placeholder="Full narration / script…" />
          <div className="flex flex-col gap-2">
            <input data-testid="fs-title" value={productTitle} onChange={(e) => setProductTitle(e.target.value)} className="border rounded-sm p-2 text-sm" placeholder="Product title" />
            <input data-testid="fs-topic" value={topic} onChange={(e) => setTopic(e.target.value)} className="border rounded-sm p-2 text-sm" placeholder="Topic (e.g. forex)" />
            <select data-testid="fs-aspect" value={aspect} onChange={(e) => setAspect(e.target.value)} className="border rounded-sm p-2 text-sm">
              <option value="landscape">Landscape 16:9</option>
              <option value="portrait">Portrait 9:16</option>
              <option value="square">Square 1:1</option>
            </select>
          </div>
          <button onClick={runMatch} disabled={matching} data-testid="fs-match-run"
            className="inline-flex items-center justify-center gap-2 bg-navy text-white px-4 py-2 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors h-full">
            {matching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Segment & Match
          </button>
        </div>
        {matchRes && (
          <div className="flex flex-wrap items-center gap-3 text-[11px]" data-testid="fs-match-summary">
            <span className="px-2 py-0.5 rounded bg-navy/[0.06] text-navy">{matchRes.scene_count} scenes</span>
            <span className={`px-2 py-0.5 rounded ${matchRes.variety_ok ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-amber-50 text-amber-700 border border-amber-200"}`}>Variety score {matchRes.project_variety_score}</span>
            <span className="px-2 py-0.5 rounded bg-navy/[0.06] text-navy">{matchRes.unique_assets} unique assets · {matchRes.unique_creators} creators</span>
            {matchRes.scenes_needing_review?.length > 0 && <span className="px-2 py-0.5 rounded bg-red-50 text-red-700 border border-red-200">Scenes needing review: {matchRes.scenes_needing_review.map((i) => i + 1).join(", ")}</span>}
          </div>
        )}
      </Panel>

      {/* Scene approval interface */}
      {matchRes && (
        <Panel title="2 · Scene Approval Interface" icon={CheckCircle2} accent="royal" testid="fs-scenes" className="mb-6">
          <div className="flex flex-wrap gap-1 mb-4">
            <span className="text-[10px] text-muted-foreground mr-1">Excluded (brand-safe):</span>
            {matchRes.exclusions.map((x) => <span key={x} className="text-[10px] px-1.5 py-0.5 rounded bg-red-50 text-red-600 border border-red-200">{x}</span>)}
          </div>
          <div className="space-y-5">
            {matchRes.scenes.map((s) => {
              const st = sceneState[s.scene_index] || {};
              const sel = s.candidates.find((c) => c.provider_asset_id === st.selectedId);
              return (
                <div key={s.scene_index} className={`border rounded-md p-3 ${st.rejected ? "opacity-60 border-red-200" : st.approved ? "border-emerald-300 bg-emerald-50/30" : "border-navy/15"}`} data-testid={`fs-scene-${s.scene_index}`}>
                  <div className="flex items-center justify-between flex-wrap gap-2 mb-1">
                    <p className="text-sm font-bold text-navy">Scene {s.scene_index + 1} · <span className="text-royal">{s.learning_purpose}</span>{st.locked && <Lock className="inline w-3 h-3 ml-1 text-navy/60" />}</p>
                    <div className="flex items-center gap-2">
                      {st.approved && <StatusChip status="Approved" tone="emerald" />}
                      {st.rejected && <StatusChip status="Rejected" tone="rose" />}
                      {s.human_review_required && <span className="text-[10px] text-red-700">Unique candidate unavailable — human review required</span>}
                    </div>
                  </div>
                  <p className="text-[11px] text-muted-foreground italic mb-2">“{s.scene_text}”</p>

                  {/* Scene metadata */}
                  <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-x-4 gap-y-1 text-[10px] text-navy/80 mb-3">
                    <p><b>Proposed duration:</b> {sel?.recommendation?.suggested_duration ?? "—"}s</p>
                    <p><b>Speed:</b> {sel?.recommendation?.suggested_speed ?? "—"}</p>
                    <p><b>Crop:</b> {sel?.recommendation?.suggested_crop ?? "—"}</p>
                    <p><b>Text-safe:</b> {sel?.recommendation?.text_safe_zone ?? "—"}</p>
                    <p className="sm:col-span-2"><b>Search terms:</b> {[...(s.search_terms?.literal || []), ...(s.search_terms?.environmental || [])].slice(0, 5).join(", ")}</p>
                    <p className="sm:col-span-2"><b>Primary query:</b> “{s.primary_query}”</p>
                  </div>

                  {/* Candidate carousel */}
                  {s.candidates.length === 0 ? <p className="text-[11px] text-amber-700">{s.note}</p> : (
                    <div className="grid sm:grid-cols-3 lg:grid-cols-5 gap-2 mb-3">
                      {s.candidates.map((c, i) => {
                        const chosen = c.provider_asset_id === st.selectedId;
                        return (
                          <button key={i} onClick={() => selectCandidate(s.scene_index, c.provider_asset_id)} data-testid={`fs-cand-${s.scene_index}-${i}`}
                            className={`text-left border rounded-sm p-1.5 transition-colors ${chosen ? "border-royal ring-2 ring-royal/30" : "border-navy/15 hover:border-royal/40"} ${c.dedup_status === "hard_duplicate" ? "opacity-50" : ""}`}>
                            {c.preview_url && <img src={c.preview_url} alt="" className="w-full h-16 object-cover rounded-sm mb-1" />}
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] font-bold text-navy">{c.match_score}</span>
                              <StatusChip status={c.tier} tone={c.match_score >= 90 ? "gold" : c.match_score >= 80 ? "emerald" : "blue"} />
                            </div>
                            <p className="text-[9px] text-muted-foreground truncate">{c.creator_name}</p>
                            <div className="flex items-center gap-1 mt-0.5">
                              <span className={`text-[8px] px-1 rounded ${c.dedup_status === "unique" ? "bg-emerald-50 text-emerald-700" : c.dedup_status === "near_duplicate" ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"}`}>{c.dedup_status.replace("_", " ")}</span>
                              <span className="text-[8px] text-navy/50">var {c.variety_score}</span>
                            </div>
                            {chosen && <p className="text-[8px] text-royal font-bold mt-0.5">● Selected</p>}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {/* Selected candidate detail + scores */}
                  {sel && (
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-navy/80 mb-2 border-t pt-2" data-testid={`fs-scene-sel-${s.scene_index}`}>
                      <span><b>Provider:</b> {sel.provider}</span>
                      <span><b>Creator:</b> {sel.creator_name}</span>
                      <span><b>License:</b> {sel.license_type}{sel.commercial_use_allowed ? " · commercial OK" : ""}</span>
                      <span><b>Relevance:</b> {sel.score?.relevance}</span>
                      <span><b>Brand-safety:</b> {sel.score?.brand_fit}</span>
                      <span><b>Variety:</b> {sel.variety_score}</span>
                    </div>
                  )}

                  {/* Scene actions */}
                  {s.candidates.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      <button onClick={() => approveScene(s.scene_index)} disabled={st.rejected} data-testid={`fs-approve-${s.scene_index}`}
                        className="text-[11px] inline-flex items-center gap-1 bg-emerald-600 text-white px-2.5 py-1 rounded-sm font-medium disabled:opacity-40"><ThumbsUp className="w-3 h-3" /> Approve</button>
                      <button onClick={() => rejectScene(s.scene_index)} data-testid={`fs-reject-${s.scene_index}`}
                        className="text-[11px] inline-flex items-center gap-1 bg-white border border-red-300 text-red-600 px-2.5 py-1 rounded-sm font-medium"><Ban className="w-3 h-3" /> Reject</button>
                      <button onClick={() => toast.message("Pick a different candidate above to replace the selection.")} data-testid={`fs-replace-${s.scene_index}`}
                        className="text-[11px] inline-flex items-center gap-1 bg-white border border-navy/20 text-navy px-2.5 py-1 rounded-sm font-medium"><RefreshCw className="w-3 h-3" /> Replace</button>
                      <button onClick={runMatch} data-testid={`fs-search-again-${s.scene_index}`}
                        className="text-[11px] inline-flex items-center gap-1 bg-white border border-navy/20 text-navy px-2.5 py-1 rounded-sm font-medium"><Search className="w-3 h-3" /> Search again</button>
                      <button onClick={() => toggleLock(s.scene_index)} data-testid={`fs-lock-${s.scene_index}`}
                        className={`text-[11px] inline-flex items-center gap-1 px-2.5 py-1 rounded-sm font-medium ${st.locked ? "bg-navy text-white" : "bg-white border border-navy/20 text-navy"}`}>{st.locked ? <Unlock className="w-3 h-3" /> : <Lock className="w-3 h-3" />} {st.locked ? "Unlock" : "Lock scene"}</button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Panel>
      )}

      {/* Creative Direction Report (MO-027 · QRU Creative Director™) */}
      {matchRes && creative && (
        <Panel title="Creative Direction Report — QRU Creative Director™" icon={Clapperboard} accent="royal" testid="fs-creative" className="mb-6">
          <p className="text-[11px] text-muted-foreground mb-3">Prepared <b>before rendering</b>. The Factory makes intentional creative decisions, then you approve. Governed by the Treasure Standard™ + Art-Direction Standard™ (§5/§6).</p>

          {/* Scores */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-4" data-testid="fs-creative-scores">
            {[["Scene Quality", creative.scores.scene_quality], ["Brand", creative.scores.brand_score], ["Learning", creative.scores.learning_score], ["Thumbnail", creative.scores.thumbnail_score], ["Composite", creative.scores.composite]].map(([k, v]) => (
              <div key={k} className="border rounded-md p-2 text-center border-navy/10">
                <p className="text-lg font-black text-navy">{v}</p>
                <p className="text-[9px] uppercase tracking-wide text-muted-foreground">{k}</p>
              </div>
            ))}
            <div className="border rounded-md p-2 text-center border-gold/40 bg-gold/10">
              <p className="text-[11px] font-bold text-navy leading-tight mt-1">{creative.treasure_standard_prediction}</p>
              <p className="text-[9px] uppercase tracking-wide text-muted-foreground">Treasure Std</p>
            </div>
          </div>

          {/* Mood + pacing */}
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Visual Mood</span>
              <select data-testid="fs-creative-mood" value={styleChoice || creative.visual_mood} onChange={(e) => { setStyleChoice(e.target.value); fetchCreative(matchRes, e.target.value); setCreativeApproved(false); }} className="border rounded-sm px-2 py-1 text-xs">
                {creative.visual_mood_options.map((m) => <option key={m}>{m}</option>)}
              </select>
            </div>
            <span className="text-[11px] px-2 py-1 rounded bg-navy/[0.06] text-navy">Recommended pacing: <b>{creative.recommended_pacing}</b></span>
          </div>

          {/* Scene reviews */}
          <div className="mb-4" data-testid="fs-creative-reviews">
            <p className="text-[10px] font-bold uppercase tracking-wide text-royal mb-1">Scene Review</p>
            <div className="space-y-1.5">
              {creative.scene_reviews.map((r) => (
                <div key={r.scene_index} className={`flex items-start gap-2 text-[11px] border rounded-sm p-2 ${r.cd_approved ? "border-emerald-200 bg-emerald-50/30" : "border-amber-300 bg-amber-50/40"}`} data-testid={`fs-creative-scene-${r.scene_index}`}>
                  {r.cd_approved ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" /> : <ShieldAlert className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" />}
                  <div>
                    <p className="text-navy"><b>Scene {r.scene_index + 1} · {r.arc_role}</b> — <StatusChip status={r.quality_rating} tone={r.quality_rating === "Excellent" ? "emerald" : r.quality_rating === "Good" ? "blue" : "amber"} /></p>
                    {r.improvements.length > 0 && <p className="text-[10px] text-amber-700 mt-0.5">{r.improvements.join(" ")}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Thumbnail concepts */}
          <div className="mb-4" data-testid="fs-creative-thumbnails">
            <p className="text-[10px] font-bold uppercase tracking-wide text-royal mb-1">Thumbnail Concepts</p>
            <div className="grid sm:grid-cols-3 gap-2">
              {creative.thumbnail_concepts.map((t) => (
                <div key={t.name} className={`border rounded-md p-2.5 ${t.recommended ? "border-gold ring-2 ring-gold/30 bg-gold/[0.05]" : "border-navy/10"}`}>
                  <div className="flex items-center justify-between">
                    <p className="text-[11px] font-bold text-navy">{t.name}</p>
                    <span className="text-[11px] font-black text-navy">{t.total}</span>
                  </div>
                  <p className="text-[9px] text-muted-foreground">{t.composition}</p>
                  <p className="text-[9px] text-royal mt-0.5">“{t.overlay_text}” · Scene {t.hero_scene_index + 1}</p>
                  {t.recommended && <p className="text-[9px] text-gold font-bold mt-1">★ Recommended</p>}
                </div>
              ))}
            </div>
          </div>

          {/* Approval gate */}
          <div className="border-t pt-3 flex items-center justify-between flex-wrap gap-2">
            <p className="text-[11px] text-muted-foreground">Approve Creative Direction?</p>
            <div className="flex items-center gap-2">
              <button onClick={() => setCreativeApproved(true)} data-testid="fs-creative-approve" className={`text-[11px] inline-flex items-center gap-1 px-3 py-1.5 rounded-sm font-bold ${creativeApproved ? "bg-emerald-600 text-white" : "bg-navy text-white hover:bg-navy/90"}`}>{creativeApproved ? <><CheckCircle2 className="w-3 h-3" /> Approved</> : "Approve"}</button>
              <button onClick={() => { const el = document.querySelector('[data-testid="fs-scenes"]'); el && el.scrollIntoView({ behavior: "smooth" }); }} data-testid="fs-creative-modify" className="text-[11px] border border-navy/20 text-navy px-3 py-1.5 rounded-sm font-medium">Modify</button>
              <button onClick={() => { const opts = creative.visual_mood_options; const i = opts.indexOf(styleChoice || creative.visual_mood); const next = opts[(i + 1) % opts.length]; setStyleChoice(next); fetchCreative(matchRes, next); setCreativeApproved(false); }} data-testid="fs-creative-change-style" className="text-[11px] border border-royal/30 text-royal px-3 py-1.5 rounded-sm font-medium">Change Style</button>
            </div>
          </div>
        </Panel>
      )}

      {/* MO-028 · Civilization Status — Autonomous Improvement Loop™ */}
      {matchRes && (loopRunning || loop) && (
        <Panel title="Civilization Status — Autonomous Improvement Loop™ · MO-028" icon={Landmark} accent="royal" testid="fs-loop" className="mb-6">
          <p className="text-[11px] text-muted-foreground mb-3">
            The Founder approves. The civilization perfects. Specialized intelligences are auto-assigned every recommendation and improve the product until the Treasure Standard™ threshold is reached — you review one finished Gold Master Candidate, not a list of fixes. Governed by QRU-CON-0001 §5/§6/§9/§10.
          </p>

          {/* Threshold + re-run */}
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Treasure Standard threshold</span>
              <input type="range" min={70} max={98} value={threshold} data-testid="fs-loop-threshold"
                onChange={(e) => setThreshold(Number(e.target.value))} onMouseUp={() => runLoop()} onTouchEnd={() => runLoop()}
                className="w-40 accent-royal" />
              <span className="text-[12px] font-black text-navy">{threshold}</span>
            </div>
            <button onClick={() => runLoop()} disabled={loopRunning} data-testid="fs-loop-rerun"
              className="text-[11px] inline-flex items-center gap-1 bg-white border border-royal/30 text-royal px-3 py-1.5 rounded-sm font-medium disabled:opacity-50">
              {loopRunning ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />} Re-run civilization
            </button>
          </div>

          {loopRunning && !loop && (
            <div className="flex items-center gap-2 text-[12px] text-royal py-6" data-testid="fs-loop-working">
              <Loader2 className="w-4 h-4 animate-spin" /> The civilization is improving your product…
            </div>
          )}

          {loop && (
            <>
              {/* Department progress bars */}
              <div className="grid sm:grid-cols-2 gap-3 mb-5" data-testid="fs-loop-departments">
                {loop.civilization_status.map((d) => {
                  const meta = DEPT_META[d.department] || { icon: Brain, color: "text-navy", bar: "bg-navy" };
                  const Icon = meta.icon;
                  const pct = deptAnim[d.department] ?? 0;
                  const complete = d.progress >= 100 && !d.blocked;
                  return (
                    <div key={d.department} className={`border rounded-md p-3 ${d.blocked ? "border-amber-300 bg-amber-50/40" : complete ? "border-emerald-200 bg-emerald-50/20" : "border-navy/15"}`} data-testid={`fs-loop-dept-${d.department}`}>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-1.5">
                          <Icon className={`w-4 h-4 ${meta.color}`} />
                          <span className="text-[12px] font-bold text-navy">{d.department_name}</span>
                        </div>
                        <span className="text-[12px] font-black text-navy tabular-nums" data-testid={`fs-loop-pct-${d.department}`}>{d.blocked ? "Blocked" : `${d.progress}%`}</span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-navy/10 overflow-hidden">
                        <div className={`h-full rounded-full ${d.blocked ? "bg-amber-500" : meta.bar}`} style={{ width: `${d.blocked ? 100 : pct}%`, transition: "width 900ms ease-out" }} />
                      </div>
                      <p className={`text-[10px] mt-1.5 ${d.blocked ? "text-amber-700" : "text-muted-foreground"}`}>
                        {d.blocked ? "Needs your input — Knowledge-First governance (never fabricated)." : complete ? "Complete." : `${d.activity}…`}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* Treasure Standard climb (baseline → final) */}
              <div className="flex items-center gap-3 mb-5 text-[11px]" data-testid="fs-loop-climb">
                <TrendingUp className="w-4 h-4 text-royal" />
                <span className="text-muted-foreground">Baseline <b className="text-navy">{loop.baseline_composite}</b></span>
                <span className="text-navy/30">→</span>
                <span className="text-muted-foreground">After {loop.cycles.length - 1} cycle(s) <b className="text-navy">{loop.final_composite}</b></span>
                <span className="text-navy/30">·</span>
                <span className="text-muted-foreground">Threshold <b className="text-navy">{loop.threshold}</b></span>
              </div>

              {/* Gold Master Candidate Ready OR honest blocking / ceiling state */}
              {loop.gold_master_candidate_ready ? (
                <div className="border-2 border-gold/50 bg-gold/[0.07] rounded-md p-5 text-center" data-testid="fs-loop-candidate-ready">
                  <div className="inline-flex items-center gap-2 text-navy font-black text-lg mb-3"><Award className="w-5 h-5 text-gold" /> Gold Master Candidate Ready</div>
                  <div className="grid grid-cols-3 gap-3 max-w-md mx-auto mb-4">
                    <div className="border rounded-md p-2 bg-white/60 border-gold/30">
                      <p className="text-2xl font-black text-navy tabular-nums">{loop.final_composite}<span className="text-sm text-muted-foreground">/100</span></p>
                      <p className="text-[9px] uppercase tracking-wide text-muted-foreground">Treasure Standard</p>
                    </div>
                    <div className="border rounded-md p-2 bg-white/60 border-gold/30">
                      <p className="text-2xl font-black text-navy tabular-nums">{loop.civilization_status.filter((d) => d.progress >= 100 && !d.blocked).length}/{loop.civilization_status.length}</p>
                      <p className="text-[9px] uppercase tracking-wide text-muted-foreground">Departments Complete</p>
                    </div>
                    <div className="border rounded-md p-2 bg-white/60 border-gold/30 flex flex-col justify-center">
                      <p className="text-[11px] font-bold text-navy leading-tight">Awaiting Founder Approval</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-center gap-2 flex-wrap">
                    <button onClick={approveCandidate} data-testid="fs-loop-approve"
                      className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-sm font-bold text-[12px] ${candidateDecision === "approved" ? "bg-emerald-600 text-white" : "bg-navy text-white hover:bg-navy/90"}`}>
                      {candidateDecision === "approved" ? <><CheckCircle2 className="w-4 h-4" /> Approved</> : <><ThumbsUp className="w-4 h-4" /> Approve</>}
                    </button>
                    <button onClick={requestCandidateChanges} data-testid="fs-loop-request-changes"
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-sm font-medium text-[12px] border border-navy/20 text-navy bg-white"><RefreshCw className="w-4 h-4" /> Request Changes</button>
                    <button onClick={approveCandidate} data-testid="fs-loop-publish"
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-sm font-bold text-[12px] bg-gold text-navy hover:bg-gold/90"><Film className="w-4 h-4" /> Publish</button>
                  </div>
                </div>
              ) : (
                <div className={`border rounded-md p-4 ${loop.blocking_count > 0 ? "border-amber-300 bg-amber-50/50" : "border-navy/15 bg-navy/[0.03]"}`} data-testid="fs-loop-blocked">
                  <p className="text-[12px] font-bold text-navy flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-amber-500" /> {loop.blocking_count > 0 ? `${loop.blocking_count} item(s) need your input` : "Automated ceiling reached"}
                  </p>
                  <p className="text-[11px] text-muted-foreground mt-1">{loop.notification}</p>
                  {loop.work_orders.filter((w) => w.blocking).map((w) => (
                    <div key={w.id} className="mt-2 text-[11px] border-l-2 border-amber-400 pl-2" data-testid={`fs-loop-wo-${w.id}`}>
                      <b className="text-navy">{w.department_name}</b> — {w.recommendation}
                      <p className="text-[10px] text-amber-700">{w.resolution}</p>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-[10px] text-muted-foreground mt-3 border-t pt-2" data-testid="fs-loop-honest-note">{loop.honest_note}</p>
            </>
          )}
        </Panel>
      )}

      {/* Manufacture */}
      {matchRes && (
        <Panel title="3 · Manufacture Flagship Showcase" icon={Film} accent="gold" testid="fs-manufacture" className="mb-6">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <p className="text-[12px] text-muted-foreground max-w-2xl">
              {mode === "human_approval_required"
                ? `Approve every scene, then manufacture. ${sceneList.filter((s) => s.approved).length}/${sceneList.length} scene(s) approved.`
                : "Auto-Select renders a clearly-marked DRAFT PREVIEW only — never Gold Master, Final, Distribution Approved or Publication Ready."}
            </p>
            <button onClick={produce} disabled={producing || !canProduce} data-testid="fs-produce"
              className="inline-flex items-center justify-center gap-2 bg-navy text-white px-5 py-2.5 rounded-sm font-bold disabled:opacity-50 hover:bg-navy/90 transition-colors">
              {producing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Clapperboard className="w-4 h-4" />} {producing ? "Manufacturing… (~60s)" : mode === "auto_select_draft" ? "Render Draft Preview" : "Manufacture Showcase"}
            </button>
          </div>
          {mode === "human_approval_required" && !canProduce && (
            <p className="text-[11px] text-amber-700 mt-2" data-testid="fs-approve-hint">{!creativeApproved ? "Approve the Creative Direction Report, then approve every scene before manufacturing." : "Every included scene must be approved before manufacturing."}</p>
          )}
        </Panel>
      )}

      {/* Result */}
      {result && (
        <Panel title="Production Result" icon={result.ok ? CheckCircle2 : ShieldAlert} accent={result.ok ? "royal" : "gold"} testid="fs-result" className="mb-6">
          {!result.ok && <p className="text-[12px] text-red-700 bg-red-50 border border-red-200 rounded-sm p-2 mb-3" data-testid="fs-result-error">{result.error || "Manufacturing stopped — completed stages are preserved."}</p>}
          <div className="grid md:grid-cols-2 gap-5">
            <div className="space-y-1">
              {(result.steps || []).map((s, i) => (
                <div key={i} className="flex items-start gap-2 text-[11px]" data-testid={`fs-step-${s.step}`}>
                  {s.status === "ok" ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" /> : s.status === "pending" ? <Sparkles className="w-3.5 h-3.5 text-royal shrink-0 mt-0.5" /> : s.status === "degraded" ? <ShieldAlert className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" /> : <X className="w-3.5 h-3.5 text-red-500 shrink-0 mt-0.5" />}
                  <span><b className="text-navy capitalize">{s.step.replace(/_/g, " ")}</b> — <span className="text-muted-foreground">{s.detail}</span></span>
                </div>
              ))}
              {(result.warnings || []).map((w, i) => <p key={i} className="text-[10px] text-amber-700 mt-1">⚠ {w}</p>)}
            </div>
            <div>
              {result.showcase_asset && (
                <>
                  <video src={`${API_BASE}/${result.showcase_asset.qru_asset_id}/file`} controls className="w-full rounded-md border" data-testid="fs-video" />
                  <div className="flex items-center justify-between mt-2 flex-wrap gap-2">
                    <p className="text-[11px] text-navy font-mono">{result.showcase_asset.qru_asset_id}</p>
                    <StatusChip status={result.showcase_asset.gold_master_certified ? "Gold Master Certified™" : result.showcase_asset.production_status} tone={result.showcase_asset.gold_master_certified ? "gold" : result.showcase_asset.distribution_ready ? "emerald" : "amber"} />
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">
                    {result.showcase_asset.width}×{result.showcase_asset.height} · {result.showcase_asset.duration_seconds}s · {result.scene_count} scenes · narration {String(result.showcase_asset.has_narration)}
                  </p>
                  <p className="text-[10px] text-muted-foreground">Technical QA {result.technical_qa_score} · Brand/Content QA {result.brand_content_qa_score} · checksum {String(result.showcase_asset.checksum).slice(0, 18)}…</p>
                  <p className="text-[10px] text-navy/70 mt-1">Job {String(result.job_id).slice(0, 12)} · Acceptance record {String(result.acceptance_record_id).slice(0, 8)}</p>

                  {!result.is_draft_preview && result.showcase_asset.distribution_ready && !result.showcase_asset.gold_master_certified && (
                    <button onClick={certify} disabled={certifying} data-testid="fs-certify"
                      className="mt-3 inline-flex items-center gap-2 bg-gold text-navy px-4 py-2 rounded-sm font-bold disabled:opacity-50">
                      {certifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Award className="w-4 h-4" />} Certify Gold Master™
                    </button>
                  )}
                  {result.is_draft_preview && <p className="text-[11px] text-amber-700 mt-3 bg-amber-50 border border-amber-200 rounded-sm p-2" data-testid="fs-draft-note">DRAFT PREVIEW ONLY — this asset can never be Gold Master, Final, Distribution Approved or Publication Ready.</p>}
                  {result.showcase_asset.gold_master_certified && (
                    <div className="mt-3 border border-gold/40 bg-gold/10 rounded-sm p-2" data-testid="fs-gold-master">
                      <p className="text-[11px] font-bold text-navy flex items-center gap-1"><Award className="w-3.5 h-3.5 text-gold" /> Gold Master Certified™</p>
                      <p className="text-[10px] text-muted-foreground">All 11 production gates passed · permanently recorded in the Acceptance Record.</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </Panel>
      )}
    </div>
  );
}
