import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import { Loader2, Scale, Link2, Search } from "lucide-react";

export default function Constitution() {
  const [doc, setDoc] = useState(null);
  const [bindings, setBindings] = useState(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    api.get("/governance/factory-constitution").then((r) => setDoc(r.data)).catch(() => setDoc(false));
    api.get("/governance/factory-constitution/bindings").then((r) => setBindings(r.data)).catch(() => {});
  }, []);

  if (doc === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (doc === false || !doc?.doc_id) return <p className="text-sm text-muted-foreground p-8">Constitution not adopted.</p>;

  const sections = (doc.sections || []).filter((s) => !q || `${s.n} ${s.title} ${s.summary}`.toLowerCase().includes(q.toLowerCase()));

  return (
    <div data-testid="constitution-page">
      <PageHeader
        overline={`${doc.doc_id} · Version ${doc.version} · ${doc.authority_level}`}
        title="QRU Factory™ Constitution"
        description="The supreme, version-controlled foundational governing standard. It actively binds agents, pipelines, quality gates and the operating experience — not merely as labels."
        actions={<VerifiedBadge label={doc.status} testid="const-status" />}
      />

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-2.5 top-2.5 text-muted-foreground" />
            <input data-testid="const-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search the Constitution…" className="w-full border rounded-sm pl-8 pr-2 py-2 text-sm" />
          </div>
          {sections.map((s) => (
            <div key={s.n} className="qru-card p-4 border-l-4 border-royal" data-testid={`const-section-${s.n}`}>
              <p className="overline text-royal mb-1">§{s.n}</p>
              <p className="text-sm font-bold text-navy font-heading">{s.title}</p>
              <p className="text-[12px] text-muted-foreground mt-1 leading-relaxed">{s.summary}</p>
            </div>
          ))}
        </div>

        <div className="space-y-4">
          <Panel title="Governance Bindings" icon={Link2} accent="gold" testid="const-bindings">
            {!bindings ? <Loader2 className="w-4 h-4 animate-spin" /> : (
              <div className="space-y-2">
                {bindings.bindings.map((b, i) => (
                  <div key={i} className="border rounded-md p-2.5 border-navy/10" data-testid={`const-binding-${i}`}>
                    <p className="text-[12px] font-semibold text-navy">{b.system}</p>
                    <div className="flex flex-wrap gap-1 my-1">{b.section_titles.map((t) => <span key={t} className="text-[9px] px-1.5 py-0.5 rounded bg-royal/10 text-royal border border-royal/20">{t}</span>)}</div>
                    <p className="text-[10px] text-muted-foreground">{b.why}</p>
                  </div>
                ))}
                <p className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-sm p-2 mt-2">{bindings.acceptance_note}</p>
              </div>
            )}
          </Panel>
          <Panel title="Quality Gates (§10)" icon={Scale} accent="royal" testid="const-gates">
            <div className="space-y-1.5">
              {(doc.quality_gates || []).map((g) => (
                <div key={g.gate} className="text-[11px]"><StatusChip status={g.gate} tone="blue" /><p className="text-[10px] text-muted-foreground mt-0.5">{g.verifies.slice(0, 4).join(" · ")}…</p></div>
              ))}
            </div>
          </Panel>
          <Panel title="Product Statuses (§10)" icon={Scale} accent="gold" testid="const-statuses">
            <div className="flex flex-wrap gap-1">{(doc.product_statuses || []).map((s) => <span key={s} className="text-[10px] px-1.5 py-0.5 rounded border bg-navy/[0.05] text-navy border-navy/15">{s}</span>)}</div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
