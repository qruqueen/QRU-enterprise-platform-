import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, GovernedBy } from "@/components/qru";
import { ManufacturingGPS } from "@/components/ManufacturingGPS";
import {
  Loader2, Layers as LayersIcon, Boxes, Compass, Map, ArrowRight, X, Building2, Navigation,
} from "lucide-react";

const VIEW_LABEL = { simple: "Simple View™", std: "Standard View™", ent: "Enterprise View™" };

export default function EnterpriseArchitecture() {
  const [tab, setTab] = useState("domains");
  const [domains, setDomains] = useState([]);
  const [layers, setLayers] = useState([]);
  const [intentions, setIntentions] = useState([]);
  const [view, setView] = useState("std");
  const [detail, setDetail] = useState(null);
  const [firstProject, setFirstProject] = useState(null);

  useEffect(() => {
    api.get("/architecture/domains").then((r) => setDomains(r.data.domains)).catch(() => {});
    api.get("/architecture/layers").then((r) => setLayers(r.data.layers)).catch(() => {});
    api.get("/factory-os/projects").then((r) => { const p = Array.isArray(r.data) ? r.data[0] : (r.data.projects || [])[0]; setFirstProject(p?.id); }).catch(() => {});
  }, []);
  useEffect(() => { api.get(`/architecture/intentions?view=${view}`).then((r) => setIntentions(r.data.intentions)).catch(() => {}); }, [view]);

  const openModule = (route) => api.get(`/architecture/explorer?route=${encodeURIComponent(route)}`).then((r) => setDetail(r.data)).catch(() => {});

  const TABS = [
    { id: "domains", label: "Domains", icon: Building2 },
    { id: "layers", label: "Enterprise Layers", icon: LayersIcon },
    { id: "intentions", label: "Intention Navigation", icon: Navigation },
    { id: "gps", label: "Manufacturing GPS™", icon: Compass },
  ];

  return (
    <div data-testid="architecture-page">
      <PageHeader
        overline="STD-EIP-0002 · Enterprise Foundation Sprint A™"
        title="Architecture Explorer™"
        description="Google Maps™ for the QRU Enterprise. Every module belongs to exactly one Domain and one Enterprise Layer, and is reachable by what you're trying to do — so the Factory feels like working with an organization, not operating software."
        actions={<VerifiedBadge label="Every module governed · Every page explains itself" testid="architecture-badge" />}
      />
      <GovernedBy standards={["STD-EIP-0002", "STD-EIP-0001", "STD-MFG-0001"]} className="mb-4" testid="architecture-governed-by" />

      <div className="flex flex-wrap gap-1.5 mb-5" data-testid="architecture-tabs">
        {TABS.map((t) => { const Ic = t.icon; return (
          <button key={t.id} data-testid={`arch-tab-${t.id}`} onClick={() => setTab(t.id)}
            className={`text-[12px] inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-colors ${tab === t.id ? "bg-navy text-white" : "bg-white border border-navy/15 text-navy hover:border-royal"}`}>
            <Ic className="w-3.5 h-3.5" /> {t.label}
          </button>
        ); })}
      </div>

      {/* DOMAINS */}
      {tab === "domains" && (
        <div className="grid sm:grid-cols-2 gap-3" data-testid="architecture-domains">
          {domains.map((d) => (
            <Panel key={d.id} title={d.name} icon={Building2} accent="royal" testid={`arch-domain-${d.id}`}
              right={<span className="text-[10px] text-muted-foreground">{d.module_count} modules</span>}>
              <p className="text-[11px] text-navy/80">{d.purpose}</p>
              <p className="text-[10px] text-emerald-700 mt-1.5"><b>Output:</b> {d.output}</p>
            </Panel>
          ))}
        </div>
      )}

      {/* LAYERS */}
      {tab === "layers" && (
        <Panel title="Enterprise Layer Registry™ (7 layers)" icon={LayersIcon} accent="gold" testid="architecture-layers">
          <div className="space-y-2">
            {layers.map((l) => (
              <div key={l.id} className="flex items-center gap-3 border rounded-md p-3 border-navy/10" data-testid={`arch-layer-${l.id}`}>
                <span className="w-7 h-7 rounded-full bg-gold/20 text-navy grid place-items-center text-[11px] font-black shrink-0">{l.n}</span>
                <p className="text-[12px] font-bold text-navy flex-1">{l.name}</p>
                <span className="text-[10px] text-muted-foreground">{l.module_count} modules</span>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* INTENTIONS */}
      {tab === "intentions" && (
        <div data-testid="architecture-intentions">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">Navigation mode</span>
            {["simple", "std", "ent"].map((v) => (
              <button key={v} data-testid={`arch-view-${v}`} onClick={() => setView(v)}
                className={`text-[11px] px-2.5 py-1 rounded-full ${view === v ? "bg-royal text-white" : "bg-white border border-navy/15 text-navy"}`}>{VIEW_LABEL[v]}</button>
            ))}
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {intentions.map((it) => (
              <Panel key={it.id} title={it.name} icon={Navigation} accent="royal" testid={`arch-intention-${it.id}`}>
                <p className="text-[10px] text-muted-foreground mb-2">{it.desc}</p>
                <div className="flex flex-wrap gap-1">
                  {it.modules.length === 0 ? <span className="text-[10px] text-navy/30">No modules in this view</span> :
                    it.modules.map((m) => (
                      <button key={m.route} onClick={() => openModule(m.route)} data-testid={`arch-mod-${m.route}`}
                        className="text-[10px] px-2 py-0.5 rounded-full border border-navy/15 text-navy hover:border-royal hover:text-royal transition-colors">{m.name}</button>
                    ))}
                </div>
              </Panel>
            ))}
          </div>
        </div>
      )}

      {/* GPS DEMO */}
      {tab === "gps" && (
        <Panel title="Manufacturing GPS™ + Why-Am-I-Here™ (live)" icon={Compass} accent="gold" testid="architecture-gps">
          <p className="text-[11px] text-muted-foreground mb-3">Persistent production awareness — this component appears on production pages (e.g. My Projects) so you always know where a project is, what's next, who owns it, and what's blocking it. Live example for your most recent project:</p>
          <ManufacturingGPS projectId={firstProject} route="/projects" />
        </Panel>
      )}

      {/* MODULE DETAIL DRAWER */}
      {detail && (
        <div className="fixed inset-0 bg-navy/40 z-50 flex items-end sm:items-center justify-center p-4" onClick={() => setDetail(null)} data-testid="arch-detail">
          <div className="bg-white rounded-lg max-w-lg w-full p-5 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-2">
              <div>
                <h3 className="text-lg font-black text-navy">{detail.name}</h3>
                <div className="flex gap-2 mt-1"><StatusChip status={detail.domain_name} tone="blue" /><StatusChip status={detail.layer_name} tone="gold" /></div>
              </div>
              <button onClick={() => setDetail(null)} data-testid="arch-detail-close" className="text-navy/40 hover:text-navy"><X className="w-5 h-5" /></button>
            </div>
            <div className="text-[11px] text-navy/80 space-y-1.5 mt-3">
              <p><b>Why:</b> {detail.why.why}</p>
              <p><b>Objective:</b> {detail.why.objective}</p>
              <p><b>Next:</b> {detail.why.next}</p>
              <p><b>Governing standards:</b> {detail.standards.join(", ")}</p>
              <p><b>Mission contribution:</b> {detail.mission_contribution}</p>
              <p><b>Human capability:</b> {detail.human_capability_contribution}</p>
              {detail.related_in_domain?.length > 0 && <p><b>Related in domain:</b> {detail.related_in_domain.map((r) => r.name).join(", ")}</p>}
            </div>
            <a href={detail.route} className="mt-4 inline-flex items-center gap-1.5 bg-navy text-white px-4 py-2 rounded-sm text-[12px] font-bold hover:bg-navy/90"><ArrowRight className="w-4 h-4" /> Open module</a>
          </div>
        </div>
      )}
    </div>
  );
}
