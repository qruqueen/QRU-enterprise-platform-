import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import {
  Loader2, Users, ArrowRight, ShieldCheck, Workflow, Palette, ChevronRight, Landmark,
} from "lucide-react";

export default function FactoryAgents() {
  const [agents, setAgents] = useState([]);
  const [overview, setOverview] = useState(null);
  const [design, setDesign] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/governance-binding/agents").then((r) => setAgents(r.data.agents)),
      api.get("/governance-binding/overview").then((r) => setOverview(r.data)),
      api.get("/governance-binding/design").then((r) => setDesign(r.data)),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div>
      <PageHeader
        overline="QRU Governance Binding Layer™ · Factory Agents™"
        title="Factory Agents"
        description="These are not tools — they are governed members of the operating system. Every agent is bound to a founding Institutional Standard™, and every manufacturing stage is governed end-to-end. This is a governed intelligence organization, not random AI automation."
        actions={<VerifiedBadge label="Governed Intelligence™" testid="agents-badge" />}
      />

      {/* Governance loop */}
      {overview && (
        <div className="qru-card qru-goldline p-5 mb-8" data-testid="governance-loop">
          <p className="overline text-royal mb-3 flex items-center gap-1.5"><Landmark className="w-3.5 h-3.5" /> The Governance Loop</p>
          <div className="flex items-center gap-2 flex-wrap">
            {overview.loop.map((s, i) => (
              <span key={s} className="flex items-center gap-2">
                <span className="text-sm font-heading font-bold text-navy px-3 py-1.5 rounded-md bg-muted/50 border border-border">{s}</span>
                {i < overview.loop.length - 1 && <ArrowRight className="w-4 h-4 text-gold" />}
              </span>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            {overview.agents} governed agents · {overview.manufacturing_stages} governed stages · Priority standards enforced: <b className="text-navy">{overview.priority_bound}/{overview.priority_total}</b>
          </p>
        </div>
      )}

      {/* Agent registry */}
      <Panel title="Agent Registry" icon={Users} accent="royal" testid="agent-registry" className="mb-8 overflow-hidden">
        <div className="overflow-x-auto -m-5">
          <table className="w-full text-sm">
            <thead className="bg-muted/40"><tr>{["Agent", "Role", "Mandate", "Governed By"].map((h) => <th key={h} className="text-left font-bold text-navy px-5 py-2.5 text-[11px] uppercase tracking-wide">{h}</th>)}</tr></thead>
            <tbody>
              {agents.map((a) => (
                <tr key={a.id} className="border-t border-border hover:bg-muted/30 transition-colors" data-testid={`agent-${a.id}`}>
                  <td className="px-5 py-3 font-heading font-bold text-navy whitespace-nowrap">{a.name}</td>
                  <td className="px-5 py-3 text-xs text-navy">{a.role}</td>
                  <td className="px-5 py-3 text-xs text-muted-foreground">{a.mandate}</td>
                  <td className="px-5 py-3">
                    <a href="/qiks" className="inline-flex items-center gap-1 text-xs font-semibold text-royal hover:underline">
                      {a.standard.standard_id ? `${a.standard.standard_id} · ` : ""}{a.standard.name}
                      {a.standard.adopted === false && <StatusChip status="Pending" tone="amber" />}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      {/* Manufacturing stage bindings (compliance chain) */}
      <Panel title="Manufacturing Governance Chain" icon={Workflow} accent="gold" testid="stage-bindings" className="mb-8">
        <p className="text-xs text-muted-foreground mb-4">Every Manufacturing Order flows through governed stages: Stage → Responsible Agent → Governing Standard → Verification. This is the QRU Manufacturing Compliance Record™.</p>
        <ManufacturingChain />
      </Panel>

      {/* Design governance */}
      {design && (
        <Panel title="Experience Design Governance" icon={Palette} accent="royal" testid="design-governance">
          <GovernedBy standards={[design.standard]} className="mb-4" testid="design-governed-by" />
          <p className="text-xs text-muted-foreground mb-3">Applies to: {design.applies_to.join(" · ")}. Every design decision answers "why does it look this way?"</p>
          <div className="space-y-2">
            {design.decisions.map((d, i) => (
              <div key={i} className="flex items-start gap-3 border rounded-sm p-3">
                <div className="w-1.5 h-full min-h-[2.5rem] rounded bg-gold shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-navy">{d.decision}</p>
                  <p className="text-xs text-muted-foreground">{d.purpose}</p>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

function ManufacturingChain() {
  const [orders, setOrders] = useState([]);
  const [selected, setSelected] = useState("");
  const [record, setRecord] = useState(null);

  useEffect(() => {
    api.get("/manufacturing-orders").then((r) => {
      const list = Array.isArray(r.data) ? r.data : (r.data.orders || []);
      setOrders(list);
      if (list[0]) { setSelected(list[0].id); }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (selected) api.get(`/governance-binding/manufacturing/${selected}/compliance`).then((r) => setRecord(r.data)).catch(() => setRecord(null));
  }, [selected]);

  return (
    <div>
      <select data-testid="chain-order" value={selected} onChange={(e) => setSelected(e.target.value)} className="border rounded-sm p-2 text-sm mb-4 max-w-md w-full">
        <option value="">— Select a Manufacturing Order —</option>
        {orders.map((o) => <option key={o.id} value={o.id}>{o.mo_code} — {o.topic}</option>)}
      </select>
      {record && (
        <div data-testid="compliance-record">
          <div className="flex items-center gap-2 mb-3 text-xs">
            <span className="font-mono text-navy font-semibold">{record.mo_code}</span>
            {record.kr_code && <span className="text-muted-foreground">· {record.kr_code}</span>}
            <GovernedBy standards={[record.pipeline_standard]} />
          </div>
          <div className="space-y-2">
            {record.stages.map((s, i) => (
              <div key={i} className="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center border rounded-sm p-3 text-xs">
                <div className="sm:col-span-3 font-heading font-bold text-navy">{s.stage}</div>
                <div className="sm:col-span-2 text-royal font-semibold">{s.agent}</div>
                <div className="sm:col-span-4">
                  <a href="/qiks" className="inline-flex items-center gap-1 text-navy font-semibold hover:underline">
                    <ShieldCheck className="w-3 h-3 text-gold" /> {s.governing_standard.standard_id || ""} {s.governing_standard.name}
                  </a>
                </div>
                <div className="sm:col-span-2 text-muted-foreground">Verify: {s.verification}</div>
                <div className="sm:col-span-1"><StatusChip status={s.status.includes("Pending") ? "Pending" : "Governed"} tone={s.status.includes("Pending") ? "amber" : "emerald"} /></div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
