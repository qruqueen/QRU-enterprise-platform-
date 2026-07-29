import { useState } from "react";
import { PageHeader } from "@/components/shared";
import {
  BookOpen, Rocket, Network, Printer, ShieldCheck, ArrowRight,
  CheckCircle2, Info, GitBranch,
} from "lucide-react";
import {
  MANUAL_META, MANUFACTURING_PROMISE, CORE_CAPABILITIES, CAPABILITY_CATALOG,
  QUICK_START, RELATIONSHIP_LANES, STORE_VS_ONLINE, OBSERVATIONS,
} from "@/data/founderManual";

const TABS = [
  { id: "manual", label: "Operator's Manual", Icon: BookOpen },
  { id: "quickstart", label: "Quick Start", Icon: Rocket },
  { id: "map", label: "Relationship Map", Icon: Network },
];

const LANE_TONE = {
  internal: "border-navy/20 bg-navy/[0.03]",
  external: "border-gold/40 bg-gold/[0.06]",
  support: "border-emerald-200 bg-emerald-50/50",
};

function Field({ label, value }) {
  if (!value || value === "—") return null;
  return (
    <div className="flex gap-2 text-[13px]">
      <span className="shrink-0 w-40 text-muted-foreground">{label}</span>
      <span className="text-foreground">{value}</span>
    </div>
  );
}

export default function FounderManual() {
  const [tab, setTab] = useState("manual");

  return (
    <div className="space-y-6" data-testid="founder-manual">
      <div className="flex items-start justify-between gap-3 flex-wrap print:hidden">
        <PageHeader title={`${MANUAL_META.title} ${MANUAL_META.version}`} subtitle={MANUAL_META.purpose} />
        <button onClick={() => window.print()} data-testid="print-manual" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90">
          <Printer className="w-4 h-4" /> Print / Save PDF
        </button>
      </div>

      <div className="flex flex-wrap gap-2 print:hidden" data-testid="manual-tabs">
        {TABS.map(({ id, label, Icon }) => (
          <button key={id} onClick={() => setTab(id)} data-testid={`tab-${id}`}
            className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium border transition-colors ${tab === id ? "bg-navy text-white border-navy" : "border-navy/25 text-navy hover:bg-navy/5"}`}>
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {/* The Manufacturing Promise — always visible header */}
      <div className="rounded-xl border-2 border-gold/40 bg-gold/[0.06] p-5" data-testid="promise-band">
        <div className="flex items-center gap-2 mb-2"><ShieldCheck className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">The QRU Manufacturing Promise™</span></div>
        <p className="text-sm text-muted-foreground mb-3">Every product manufactured by the QRU Factory™ inherits from a verified source — never invented, never faked.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {MANUFACTURING_PROMISE.map(([n, d]) => (
            <div key={n} className="rounded-lg border bg-card p-3">
              <div className="text-[13px] font-semibold text-navy">{n}</div>
              <div className="text-[11px] text-muted-foreground mt-1">{d}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── DELIVERABLE 1 — Operator's Manual ── */}
      {(tab === "manual") && (
        <div className="space-y-6" data-testid="deliverable-manual">
          <p className="text-xs text-muted-foreground">Audience: {MANUAL_META.audience}</p>
          <h2 className="font-heading font-bold text-navy text-lg">Core Launch Capabilities — full detail</h2>
          <div className="space-y-4">
            {CORE_CAPABILITIES.map((c) => (
              <section key={c.id} className="rounded-xl border bg-card p-5 break-inside-avoid" data-testid={`cap-${c.id}`}>
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div>
                    <span className="text-[10px] uppercase tracking-wide text-royal font-semibold">{c.dept}</span>
                    <h3 className="font-heading font-bold text-navy">{c.name}</h3>
                  </div>
                  <span className="text-[11px] font-semibold rounded-full px-2.5 py-1 bg-emerald-100 text-emerald-700">{c.status}</span>
                </div>
                <p className="text-sm text-foreground mb-3">{c.purpose}</p>
                <div className="grid md:grid-cols-2 gap-x-6 gap-y-1.5">
                  <Field label="Why it exists" value={c.why} />
                  <Field label="Founder interaction" value={c.founderRequired} />
                  <Field label="Inputs" value={c.inputs} />
                  <Field label="Outputs" value={c.outputs} />
                  <Field label="Records created" value={c.created} />
                  <Field label="Records modified" value={c.modified} />
                  <Field label="Records consumed" value={c.consumed} />
                  <Field label="Automatic or manual" value={c.mode} />
                  <Field label="Comes after" value={c.predecessor} />
                  <Field label="Comes next" value={c.successor} />
                  <Field label="Common use cases" value={c.useCases} />
                  <Field label="Example workflow" value={c.example} />
                </div>
                <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50/60 p-3 text-[12px] text-amber-800 flex gap-2">
                  <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span><span className="font-semibold">Common misunderstanding: </span>{c.misunderstandings}</span>
                </div>
              </section>
            ))}
          </div>

          <h2 className="font-heading font-bold text-navy text-lg pt-2">Full Capability Catalog — by department</h2>
          <p className="text-xs text-muted-foreground">Every other implemented capability, in business language. Use these alongside the core lines above.</p>
          <div className="grid md:grid-cols-2 gap-4">
            {Object.entries(CAPABILITY_CATALOG).map(([dept, items]) => (
              <section key={dept} className="rounded-xl border bg-card p-4 break-inside-avoid" data-testid={`dept-${dept}`}>
                <div className="font-heading font-bold text-navy text-sm mb-2">{dept}</div>
                <ul className="space-y-1.5">
                  {items.map(([n, d]) => (
                    <li key={n} className="text-[12px]"><span className="font-semibold text-foreground">{n}</span> — <span className="text-muted-foreground">{d}</span></li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        </div>
      )}

      {/* ── DELIVERABLE 2 — Quick Start ── */}
      {(tab === "quickstart") && (
        <div className="space-y-4" data-testid="deliverable-quickstart">
          <h2 className="font-heading font-bold text-navy text-lg">"I have a product. What do I do next?"</h2>
          {QUICK_START.map((w, i) => (
            <section key={i} className="rounded-xl border bg-card p-5 break-inside-avoid" data-testid={`qs-${i}`}>
              <div className="flex items-center gap-2 mb-3">
                <span className="shrink-0 w-7 h-7 rounded-full bg-navy text-white text-sm font-bold grid place-items-center">{i + 1}</span>
                <h3 className="font-heading font-bold text-navy">{w.scenario}</h3>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-[12px] mb-3">
                <span className="rounded-md bg-navy/10 text-navy px-2 py-1 font-medium">Start: {w.start}</span>
                <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="rounded-md bg-gold/15 text-navy px-2 py-1 font-medium">Next: {w.next}</span>
                <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="rounded-md bg-emerald-100 text-emerald-700 px-2 py-1 font-medium">Done: {w.done}</span>
              </div>
              <ol className="space-y-1 mb-3">
                {w.steps.map((s, j) => (
                  <li key={j} className="text-[13px] text-foreground flex gap-2"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />{s}</li>
                ))}
              </ol>
              <div className="text-[12px] text-muted-foreground"><span className="font-semibold text-foreground">Decision point: </span>{w.decision}</div>
              <div className="text-[12px] text-muted-foreground mt-1"><span className="font-semibold text-foreground">Expected output: </span>{w.output}</div>
            </section>
          ))}
        </div>
      )}

      {/* ── DELIVERABLE 3 — Relationship Map ── */}
      {(tab === "map") && (
        <div className="space-y-5" data-testid="deliverable-map">
          <h2 className="font-heading font-bold text-navy text-lg">How products move through the Factory</h2>

          {/* Store vs online conceptual flow */}
          <div className="rounded-xl border-2 border-navy/20 p-5" data-testid="store-vs-online">
            <div className="flex items-center gap-2 mb-3"><GitBranch className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">QRU Store™ vs qru-online.com — the important distinction</span></div>
            <div className="flex flex-wrap items-center gap-2 text-[13px] font-medium mb-4">
              {STORE_VS_ONLINE.flow.map((n, i) => (
                <span key={i} className="flex items-center gap-2">
                  <span className={`rounded-md px-3 py-1.5 ${i === 3 ? "bg-emerald-100 text-emerald-700" : i === 2 ? "bg-gold/15 text-navy" : "bg-navy/10 text-navy"}`}>{n}</span>
                  {i < STORE_VS_ONLINE.flow.length - 1 && <ArrowRight className="w-4 h-4 text-muted-foreground" />}
                </span>
              ))}
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="rounded-lg border bg-navy/[0.03] p-3">
                <div className="text-sm font-semibold text-navy mb-1">QRU Store™ — internal capability</div>
                <ul className="list-disc pl-4 space-y-1 text-[12px] text-muted-foreground">{STORE_VS_ONLINE.qruStore.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
              <div className="rounded-lg border bg-gold/[0.06] p-3">
                <div className="text-sm font-semibold text-navy mb-1">qru-online.com — customer website</div>
                <ul className="list-disc pl-4 space-y-1 text-[12px] text-muted-foreground">{STORE_VS_ONLINE.qruOnline.map((s, i) => <li key={i}>{s}</li>)}</ul>
              </div>
            </div>
            <div className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50/60 p-3 text-[12px] text-emerald-800 flex gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5" />
              <span><span className="font-semibold">Confirmed — this reflects the intended architecture. </span>{STORE_VS_ONLINE.honestNote}</span>
            </div>
          </div>

          {/* Lanes */}
          {RELATIONSHIP_LANES.map((lane, i) => (
            <section key={i} className={`rounded-xl border-2 p-4 break-inside-avoid ${LANE_TONE[lane.tone]}`} data-testid={`lane-${i}`}>
              <div className="font-heading font-bold text-navy text-sm mb-3">{lane.lane}{lane.tone === "external" && <span className="ml-2 text-[10px] uppercase tracking-wide text-gold">Customer-facing</span>}{lane.tone === "support" && <span className="ml-2 text-[10px] uppercase tracking-wide text-emerald-600">Always-on</span>}</div>
              <div className="grid md:grid-cols-3 gap-3">
                {lane.nodes.map((n, j) => (
                  <div key={j} className="rounded-lg border bg-card p-3">
                    <div className="text-[13px] font-semibold text-navy mb-1.5">{n.name}</div>
                    <div className="text-[11px] text-muted-foreground"><span className="font-medium text-foreground">In: </span>{n.enters}</div>
                    <div className="text-[11px] text-muted-foreground"><span className="font-medium text-foreground">Out: </span>{n.leaves}</div>
                    <div className="text-[11px] text-royal mt-1 flex items-center gap-1"><ArrowRight className="w-3 h-3" />{n.next}</div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {/* Observations — shown on all tabs at the end */}
      <section className="rounded-xl border border-dashed p-5" data-testid="observations">
        <div className="font-heading font-bold text-navy text-sm mb-2">Observations (documented gaps — not a redesign)</div>
        <ul className="list-disc pl-5 space-y-1.5 text-[12px] text-muted-foreground">
          {OBSERVATIONS.map((o, i) => <li key={i}>{o}</li>)}
        </ul>
      </section>
    </div>
  );
}
