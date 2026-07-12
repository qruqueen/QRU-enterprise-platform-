import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { toast } from "sonner";
import { Loader2, Cog, GitMerge, FlaskConical, TrendingUp, ShieldCheck, BookOpen, Boxes, Play, BadgeCheck, Plus, Trash2, ArrowUpRight } from "lucide-react";

export default function Refinement() {
  const [tab, setTab] = useState("engines");
  const [ov, setOv] = useState(null);
  const [learning, setLearning] = useState(null);
  const [bench, setBench] = useState(null);
  const [running, setRunning] = useState(false);

  // Verify & Promote state
  const [krList, setKrList] = useState([]);
  const [selKr, setSelKr] = useState(null);
  const [claims, setClaims] = useState(null);
  const [sources, setSources] = useState([]);
  const [humanApproved, setHumanApproved] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [promoteResult, setPromoteResult] = useState(null);
  const [lineage, setLineage] = useState([]);

  useEffect(() => {
    api.get("/refinement/overview").then((r) => setOv(r.data)).catch(() => setOv(false));
    api.get("/refinement/learning").then((r) => setLearning(r.data)).catch(() => {});
  }, []);

  const loadKrList = () => api.get("/refinement/knowledge").then((r) => setKrList(r.data.records || [])).catch(() => {});
  useEffect(() => { if (tab === "promote") loadKrList(); }, [tab]);

  const selectKr = async (kr) => {
    setSelKr(kr); setPromoteResult(null); setHumanApproved(false);
    try {
      const { data } = await api.get(`/refinement/kr/${kr.id}/claims`);
      setClaims(data);
      setSources(data.attached_sources?.length ? data.attached_sources
        : data.claims.map((c) => ({ claim_id: c.claim_id, title: "", url: "", publisher: "", approved: false })));
      api.get(`/refinement/kr/${kr.id}/lineage`).then((r) => setLineage(r.data.lineage || []));
    } catch { toast.error("Could not load claims."); }
  };

  const addSource = (claim_id) => setSources((s) => [...s, { claim_id, title: "", url: "", publisher: "", approved: false }]);
  const updateSource = (i, field, val) => setSources((s) => s.map((x, idx) => (idx === i ? { ...x, [field]: val } : x)));
  const removeSource = (i) => setSources((s) => s.filter((_, idx) => idx !== i));

  const verifyPromote = async () => {
    setPromoting(true);
    try {
      const { data } = await api.post("/refinement/verify-promote", {
        kr_id: selKr.id, sources, human_approved: humanApproved });
      setPromoteResult(data);
      if (data.promoted) toast.success(`Promoted to Gold Standard Knowledge Record™ · ${data.cascade.promoted_to_gold} product(s) → Gold.`);
      else toast.warning(data.message);
      api.get(`/refinement/kr/${selKr.id}/claims`).then((r) => setClaims(r.data));
      api.get(`/refinement/kr/${selKr.id}/lineage`).then((r) => setLineage(r.data.lineage || []));
      loadKrList();
      api.get("/refinement/learning").then((r) => setLearning(r.data));
    } catch { toast.error("Verify & Promote failed."); }
    finally { setPromoting(false); }
  };

  const runBenchmark = async () => {
    setRunning(true);
    try {
      const { data } = await api.post("/refinement/benchmark");
      setBench(data); setTab("benchmark");
      toast.success(`${data.knowledge_records_manufactured} Knowledge Records → ${data.products_manufactured} products manufactured.`);
      api.get("/refinement/learning").then((r) => setLearning(r.data));
    } catch { toast.error("Benchmark run failed."); }
    finally { setRunning(false); }
  };

  if (ov === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (ov === false) return <p className="p-8 text-sm text-muted-foreground">Could not load the Refinement Initiative.</p>;

  const TABS = [
    { id: "engines", label: "Three Engines", icon: Cog },
    { id: "matrix", label: "Capability Inheritance", icon: GitMerge },
    { id: "benchmark", label: "Benchmark Production", icon: FlaskConical },
    { id: "promote", label: "Verify & Promote", icon: BadgeCheck },
    { id: "learning", label: "Learning & Metrics", icon: TrendingUp },
  ];

  return (
    <div data-testid="refinement-page">
      <PageHeader
        overline="STD-RFN-0001 · Refinement Era™ · Production First™"
        title="Refinement Initiative™"
        description={ov.philosophy}
        actions={<button onClick={runBenchmark} disabled={running} data-testid="refinement-run-benchmark"
          className="inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm text-[12px] font-bold disabled:opacity-50 hover:bg-navy/90">
          {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Run Benchmark Production</button>}
      />
      <GovernedBy standards={["STD-RFN-0001", "QRU-CON-0001", "QRU-CON-0002"]} className="mb-4" testid="refinement-governed-by" />

      <div className="flex flex-wrap gap-1.5 mb-5" data-testid="refinement-tabs">
        {TABS.map((t) => { const Ic = t.icon; return (
          <button key={t.id} data-testid={`ref-tab-${t.id}`} onClick={() => setTab(t.id)}
            className={`text-[12px] inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-colors ${tab === t.id ? "bg-navy text-white" : "bg-white border border-navy/15 text-navy hover:border-royal"}`}>
            <Ic className="w-3.5 h-3.5" /> {t.label}
          </button>
        ); })}
      </div>

      {/* THREE ENGINES */}
      {tab === "engines" && (
        <div data-testid="refinement-engines">
          <Panel title="One Experience Layer™" icon={BookOpen} accent="gold" testid="ref-experience" className="mb-4">
            <p className="text-[12px] font-bold text-navy">{ov.experience_layer.name}</p>
            <p className="text-[11px] text-muted-foreground">{ov.experience_layer.purpose}</p>
          </Panel>
          <div className="grid md:grid-cols-3 gap-3 mb-4">
            {ov.engines.map((e) => (
              <Panel key={e.id} title={e.name} icon={Cog} accent="royal" testid={`ref-engine-${e.id}`}>
                <p className="text-[11px] text-navy/80">{e.purpose}</p>
                <p className="text-[10px] text-muted-foreground mt-2"><b>In:</b> {e.inputs.join(", ")}</p>
                <p className="text-[10px] text-muted-foreground"><b>Out:</b> {e.outputs.join(", ")}</p>
                <p className="text-[9px] text-emerald-700 mt-1.5">Internalizes: {e.internalizes.join(", ")}</p>
              </Panel>
            ))}
          </div>
          <Panel title="One Governed Foundation™ (permanent)" icon={ShieldCheck} accent="gold" testid="ref-foundation">
            <div className="flex flex-wrap gap-2">
              {ov.foundation.map((f) => <span key={f.id} className="text-[11px] px-2.5 py-1 rounded-full bg-navy/[0.05] border border-navy/10 text-navy">{f.name} <span className="text-muted-foreground">· {f.standard}</span></span>)}
            </div>
          </Panel>
        </div>
      )}

      {/* MATRIX */}
      {tab === "matrix" && (
        <Panel title="Capability Inheritance Matrix™ (nothing disappears without a successor)" icon={GitMerge} accent="royal" testid="refinement-matrix">
          <div className="space-y-2">
            {ov.inheritance_matrix.map((m, i) => (
              <div key={i} className="border rounded-md p-3 border-navy/10" data-testid={`ref-matrix-${i}`}>
                <p className="text-[12px] font-bold text-navy">{m.consolidated}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">Absorbs: {m.absorbs.join(", ")}</p>
                <div className="flex flex-wrap gap-2 mt-1.5 text-[10px]">
                  <StatusChip status={`Successor: ${m.successor}`} tone="blue" />
                  <span className="text-navy/70">{m.disposition}</span>
                  {m.governance_preserved && <span className="text-emerald-700">✓ Governance preserved</span>}
                  {m.memory_preserved && <span className="text-emerald-700">✓ Memory preserved</span>}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* BENCHMARK */}
      {tab === "benchmark" && (
        <div data-testid="refinement-benchmark">
          {!bench ? (
            <Panel title="Benchmark Production™" icon={FlaskConical} accent="gold">
              <p className="text-[12px] text-navy/80 mb-3">Prove the Factory: manufacture the 5 benchmark Knowledge Records ({ov.benchmark_topics.join(", ")}) and a full product family from each — with Treasure Standard + independent Verification recorded.</p>
              <button onClick={runBenchmark} disabled={running} data-testid="ref-benchmark-run"
                className="inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm text-[12px] font-bold disabled:opacity-50">
                {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Run Benchmark
              </button>
            </Panel>
          ) : (
            <>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
                {[["KRs", bench.knowledge_records_manufactured], ["KR Treasure Pass", `${bench.kr_success_rate}%`],
                  ["Products", bench.products_manufactured], ["Pre-Ship Clean", `${bench.product_success_rate}%`],
                  ["Gold Standard", bench.gold_standard_products]].map(([k, v]) => (
                  <div key={k} className="border rounded-md p-3 border-navy/10 bg-white" data-testid={`ref-metric-${k.replace(/\s/g, "-").toLowerCase()}`}>
                    <p className="text-2xl font-black text-navy tabular-nums">{v}</p>
                    <p className="text-[9px] uppercase tracking-wide text-muted-foreground">{k}</p>
                  </div>
                ))}
              </div>
              <div className="text-[10px] text-amber-700 bg-amber-50 border border-amber-200 rounded-md p-2 mb-4" data-testid="ref-honesty">{bench.honesty_note}</div>
              <Panel title="Manufactured Knowledge Records™" icon={BookOpen} accent="royal" testid="ref-krs" className="mb-4">
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {bench.knowledge_records.map((k) => (
                    <div key={k.id} className="border rounded-md p-2.5 border-navy/10" data-testid={`ref-kr-${k.id}`}>
                      <p className="text-[11px] font-bold text-navy">{k.topic}</p>
                      <p className="text-[9px] text-muted-foreground">{k.kr_code}</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        <StatusChip status={`Treasure: ${k.treasure.verdict === "PASSED" ? "Passed" : "Returned"}`} tone={k.treasure.verdict === "PASSED" ? "emerald" : "rose"} />
                        <StatusChip status={k.verification.verdict === "VERIFIED_EXTERNAL" ? "Verified" : "Internal · human review"} tone={k.verification.verdict === "VERIFIED_EXTERNAL" ? "emerald" : "amber"} />
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
              <Panel title="Manufactured Products™ (one KR → many products)" icon={Boxes} accent="gold" testid="ref-products">
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {bench.products.slice(0, 30).map((p) => (
                    <div key={p.id} className="border rounded-md p-2.5 border-navy/10 flex items-center justify-between" data-testid={`ref-product-${p.id}`}>
                      <div><p className="text-[11px] font-bold text-navy">{p.product_type}</p><p className="text-[9px] text-muted-foreground">{p.topic}</p></div>
                      <StatusChip status={p.gold_standard ? "Gold" : "Draft"} tone={p.gold_standard ? "gold" : "blue"} />
                    </div>
                  ))}
                </div>
              </Panel>
            </>
          )}
        </div>
      )}

      {/* VERIFY & PROMOTE */}
      {tab === "promote" && (
        <div data-testid="refinement-promote" className="grid lg:grid-cols-[300px_1fr] gap-4">
          <Panel title="Knowledge Records™" icon={BookOpen} accent="royal" testid="promote-kr-list">
            {krList.length === 0 ? (
              <p className="text-[11px] text-muted-foreground">No Knowledge Records yet. Run Benchmark Production first.</p>
            ) : (
              <div className="space-y-1.5 max-h-[560px] overflow-y-auto">
                {krList.map((k) => {
                  const ext = k.verification?.evidence_sufficient_for_external_publication;
                  return (
                    <button key={k.id} data-testid={`promote-kr-${k.id}`} onClick={() => selectKr(k)}
                      className={`w-full text-left border rounded-md p-2.5 transition-colors ${selKr?.id === k.id ? "border-royal bg-royal/[0.04]" : "border-navy/10 hover:border-royal/50"}`}>
                      <p className="text-[11px] font-bold text-navy">{k.topic}</p>
                      <p className="text-[9px] text-muted-foreground">{k.kr_code} · v{k.version || 1}</p>
                      <StatusChip status={ext ? "Verified External" : "Internal · needs sources"} tone={ext ? "emerald" : "amber"} />
                    </button>
                  );
                })}
              </div>
            )}
          </Panel>

          <div>
            {!selKr ? (
              <Panel title="Verify & Promote™" icon={BadgeCheck} accent="gold" testid="promote-empty">
                <p className="text-[12px] text-navy/80">Select a Knowledge Record to review its customer-facing claims, attach human-verified sources, and promote it from internal Draft to a <b>Gold Standard Knowledge Record™</b>. Promotion re-runs the Verification Lion™ + Treasure Standard™ and cascades revalidation to every derived product. No state is faked.</p>
              </Panel>
            ) : (
              <div className="space-y-4">
                <Panel title={`${claims?.topic || selKr.topic} — Claims & Sources`} icon={BadgeCheck} accent="gold" testid="promote-detail">
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <p className="text-[10px] text-muted-foreground">{claims?.kr_code} · v{claims?.version}</p>
                    <StatusChip status={claims?.externally_verified ? "Verified External™" : "Approved Internal · pending sources"} tone={claims?.externally_verified ? "emerald" : "amber"} />
                  </div>
                  {claims?.claims.map((c) => {
                    const claimSources = sources.map((s, i) => ({ ...s, _i: i })).filter((s) => s.claim_id === c.claim_id);
                    return (
                      <div key={c.claim_id} className="border rounded-md p-3 border-navy/10 mb-3" data-testid={`promote-claim-${c.claim_id}`}>
                        <p className="text-[11px] font-bold text-navy">{c.label}</p>
                        <p className="text-[10px] text-muted-foreground mb-2">{c.text}</p>
                        {claimSources.map((s) => (
                          <div key={s._i} className="flex flex-wrap items-center gap-1.5 mb-1.5" data-testid={`promote-source-${s._i}`}>
                            <input data-testid={`promote-source-title-${s._i}`} placeholder="Source title" value={s.title}
                              onChange={(e) => updateSource(s._i, "title", e.target.value)}
                              className="flex-1 min-w-[120px] text-[11px] border border-navy/15 rounded px-2 py-1" />
                            <input data-testid={`promote-source-url-${s._i}`} placeholder="URL" value={s.url}
                              onChange={(e) => updateSource(s._i, "url", e.target.value)}
                              className="flex-1 min-w-[120px] text-[11px] border border-navy/15 rounded px-2 py-1" />
                            <input placeholder="Publisher" value={s.publisher}
                              onChange={(e) => updateSource(s._i, "publisher", e.target.value)}
                              className="w-[110px] text-[11px] border border-navy/15 rounded px-2 py-1" />
                            <label className="flex items-center gap-1 text-[10px] text-navy">
                              <input type="checkbox" data-testid={`promote-source-approve-${s._i}`} checked={s.approved}
                                onChange={(e) => updateSource(s._i, "approved", e.target.checked)} /> Approve
                            </label>
                            <button onClick={() => removeSource(s._i)} data-testid={`promote-source-remove-${s._i}`} className="text-rose-600 hover:text-rose-800"><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        ))}
                        <button onClick={() => addSource(c.claim_id)} data-testid={`promote-add-source-${c.claim_id}`}
                          className="inline-flex items-center gap-1 text-[10px] text-royal hover:underline mt-1"><Plus className="w-3 h-3" /> Add source</button>
                      </div>
                    );
                  })}
                  <label className="flex items-center gap-2 text-[11px] text-navy mt-2 mb-3">
                    <input type="checkbox" data-testid="promote-human-approve" checked={humanApproved}
                      onChange={(e) => setHumanApproved(e.target.checked)} />
                    I have reviewed every claim against its approved source and confirm this is accurate for external publication (Treasure Standard™).
                  </label>
                  <button onClick={verifyPromote} disabled={promoting} data-testid="promote-submit"
                    className="inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-sm text-[12px] font-bold disabled:opacity-50 hover:bg-navy/90">
                    {promoting ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowUpRight className="w-4 h-4" />} Re-Verify & Promote
                  </button>
                </Panel>

                {promoteResult && (
                  <Panel title="Result" icon={ShieldCheck} accent={promoteResult.promoted ? "gold" : "royal"} testid="promote-result">
                    <div className={`text-[11px] rounded-md p-2.5 mb-3 ${promoteResult.promoted ? "bg-emerald-50 border border-emerald-200 text-emerald-800" : "bg-amber-50 border border-amber-200 text-amber-800"}`} data-testid="promote-result-message">
                      {promoteResult.promoted ? <VerifiedBadge /> : null} {promoteResult.message}
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      {[["Claims Sourced", `${promoteResult.verification.claims_sourced}/${promoteResult.verification.claims_total}`],
                        ["Products Revalidated", promoteResult.cascade.revalidated],
                        ["Promoted to Gold", promoteResult.cascade.promoted_to_gold]].map(([k, v]) => (
                        <div key={k} className="border rounded-md p-2 border-navy/10">
                          <p className="text-xl font-black text-navy tabular-nums">{v}</p>
                          <p className="text-[9px] uppercase tracking-wide text-muted-foreground">{k}</p>
                        </div>
                      ))}
                    </div>
                    {promoteResult.cascade.products?.length > 0 && (
                      <div className="grid sm:grid-cols-2 gap-2 mt-3">
                        {promoteResult.cascade.products.map((p) => (
                          <div key={p.id} className="border rounded-md p-2 border-navy/10 flex items-center justify-between" data-testid={`promote-cascade-${p.id}`}>
                            <span className="text-[11px] text-navy">{p.product_type}</span>
                            <StatusChip status={p.gold_standard ? "Gold" : "Draft"} tone={p.gold_standard ? "gold" : "blue"} />
                          </div>
                        ))}
                      </div>
                    )}
                  </Panel>
                )}

                {lineage.length > 0 && (
                  <Panel title="Enterprise Memory Lineage™ (immutable)" icon={GitMerge} accent="royal" testid="promote-lineage">
                    <div className="space-y-2">
                      {lineage.map((l) => (
                        <div key={l.id} className="border-l-2 border-royal pl-2.5" data-testid={`promote-lineage-${l.id}`}>
                          <p className="text-[11px] font-bold text-navy">{l.event === "VERIFY_AND_PROMOTE" ? "Promoted → Verified External™" : "Verify attempt"} · v{l.from_version}→v{l.to_version}</p>
                          <p className="text-[10px] text-muted-foreground">{l.claims_sourced}/{l.claims_total} claims sourced · {l.actor} · {new Date(l.at).toLocaleString()}</p>
                        </div>
                      ))}
                    </div>
                  </Panel>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* LEARNING */}
      {tab === "learning" && learning && (
        <div data-testid="refinement-learning">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {[["Knowledge Records", learning.knowledge_records], ["Products", learning.products],
              ["Knowledge Reuse", `${learning.knowledge_reuse_ratio}×`], ["Gold Standard", learning.gold_standard_products]].map(([k, v]) => (
              <div key={k} className="border rounded-md p-3 border-navy/10 bg-white">
                <p className="text-2xl font-black text-navy tabular-nums">{v}</p>
                <p className="text-[9px] uppercase tracking-wide text-muted-foreground">{k}</p>
              </div>
            ))}
          </div>
          <Panel title="Enterprise Learning Engine™ — recommendations (governed, human-approved)" icon={TrendingUp} accent="royal" testid="ref-recs">
            {learning.recommendations.map((r, i) => (
              <div key={i} className="border-l-2 border-royal pl-2.5 mb-2" data-testid={`ref-rec-${i}`}>
                <p className="text-[12px] font-bold text-navy">{r.recommendation}</p>
                <p className="text-[10px] text-muted-foreground">{r.evidence} · Authority: {r.authority}</p>
              </div>
            ))}
            <p className="text-[10px] text-muted-foreground mt-2">{learning.note}</p>
          </Panel>
        </div>
      )}
    </div>
  );
}
