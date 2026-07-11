import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { toast } from "sonner";
import {
  Loader2, Film, Search, CheckCircle2, X, ShieldAlert, Lock, Unlock, RefreshCw, ThumbsUp, Ban,
  Award, ShieldCheck, Clapperboard, Sparkles,
} from "lucide-react";

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
  const [directorPlan, setDirectorPlan] = useState(null);
  const [sceneState, setSceneState] = useState({}); // idx -> {selectedId, approved, rejected, locked}
  const [producing, setProducing] = useState(false);
  const [result, setResult] = useState(null);
  const [certifying, setCertifying] = useState(false);

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
      // Director Intelligence™ (MO-027): plan the cinematic direction for these scenes.
      api.post("/media-library/director-plan", {
        topic, aspect, scenes: data.scenes.map((s) => ({ scene_text: s.scene_text, learning_purpose: s.learning_purpose })),
      }).then((r) => setDirectorPlan(r.data)).catch(() => setDirectorPlan(null));
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
  const canProduce = mode === "auto_select_draft" ? true : allApproved();

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

      {/* Director's Plan (MO-027) */}
      {matchRes && directorPlan && (
        <Panel title="Director's Plan — Director Intelligence™" icon={Clapperboard} accent="royal" testid="fs-director" className="mb-6">
          <div className="flex flex-wrap items-center gap-3 mb-3 text-[11px]">
            <span className="px-2 py-0.5 rounded bg-navy/[0.06] text-navy">Target runtime ~{directorPlan.target_runtime_seconds}s</span>
            <span className="px-2 py-0.5 rounded bg-royal/10 text-royal border border-royal/20">Governed by §6 Art-Direction Standard™</span>
          </div>
          {/* Emotional arc timeline */}
          <div className="flex items-end gap-1.5 mb-3" data-testid="fs-director-arc">
            {directorPlan.scenes.map((s) => (
              <div key={s.scene_index} className="flex-1 text-center">
                <div className="w-full bg-gold/70 rounded-t" style={{ height: `${Math.max(12, s.energy * 0.5)}px` }} title={`energy ${s.energy}`} />
                <p className="text-[9px] text-navy font-semibold mt-1">{s.arc_role}</p>
                <p className="text-[8px] text-muted-foreground">{s.duration_seconds}s · {s.transition_label}</p>
              </div>
            ))}
          </div>
          <div className="grid sm:grid-cols-2 gap-3 text-[11px]">
            <div className="border rounded-md p-2.5 border-emerald-200 bg-emerald-50/40" data-testid="fs-director-applied">
              <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-700 mb-1">Applied by the render engine</p>
              {directorPlan.applied_by_engine.map((a) => <p key={a} className="text-navy flex items-start gap-1"><span className="text-emerald-500">✓</span> {a}</p>)}
            </div>
            <div className="border rounded-md p-2.5 border-amber-200 bg-amber-50/40" data-testid="fs-director-suggested">
              <p className="text-[10px] font-bold uppercase tracking-wide text-amber-700 mb-1">Directed & planned (honest — not yet rendered)</p>
              {directorPlan.suggested_for_review.map((a) => <p key={a} className="text-navy flex items-start gap-1"><span className="text-amber-500">○</span> {a}</p>)}
            </div>
          </div>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-navy">
            <p><b className="text-royal">Closing CTA:</b> {directorPlan.closing_cta}</p>
            <p><b className="text-royal">Reinforcement:</b> {directorPlan.learning_reinforcement}</p>
            <p><b className="text-royal">Thumbnail hero:</b> Scene {directorPlan.thumbnail_concept.hero_scene_index + 1}</p>
          </div>
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
          {mode === "human_approval_required" && !allApproved() && sceneList.length > 0 && (
            <p className="text-[11px] text-amber-700 mt-2" data-testid="fs-approve-hint">Every included scene must be approved before manufacturing.</p>
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
