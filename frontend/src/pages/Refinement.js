import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { toast } from "sonner";
import { Loader2, Cog, GitMerge, FlaskConical, TrendingUp, ShieldCheck, BookOpen, Boxes, Play } from "lucide-react";

export default function Refinement() {
  const [tab, setTab] = useState("engines");
  const [ov, setOv] = useState(null);
  const [learning, setLearning] = useState(null);
  const [bench, setBench] = useState(null);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    api.get("/refinement/overview").then((r) => setOv(r.data)).catch(() => setOv(false));
    api.get("/refinement/learning").then((r) => setLearning(r.data)).catch(() => {});
  }, []);

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
