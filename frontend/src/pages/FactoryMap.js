import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge } from "@/components/qru";
import {
  Loader2, ArrowRight, ShieldCheck, GitMerge, Archive, Sparkles, Layers,
  ChevronRight, Store, Youtube, Radio, GraduationCap, Building2, Compass, Star,
} from "lucide-react";

const STATUS_TONE = { active: "emerald", inherited: "royal", merged: "amber", deprecated: "slate", future: "navy" };
const STATUS_LABEL = { active: "Active", inherited: "Inherited", merged: "Merged", deprecated: "Deprecated", future: "Future" };
const DEST_ICON = { "QRU Store™": Store, YouTube: Youtube, Podcast: Radio, Classroom: GraduationCap, Enterprise: Building2, Future: Compass };

export default function FactoryMap() {
  const [map, setMap] = useState(null);
  const [summary, setSummary] = useState(null);
  const [caps, setCaps] = useState([]);
  const [meta, setMeta] = useState({ statuses: [], layers: [] });
  const [filter, setFilter] = useState("all");
  const [tab, setTab] = useState("map");
  const [loadError, setLoadError] = useState(false);
  const nav = useNavigate();

  const load = () => {
    setLoadError(false);
    Promise.all([
      api.get("/capability-registry/map").then((r) => setMap(r.data)),
      api.get("/capability-registry/summary").then((r) => setSummary(r.data)),
      api.get("/capability-registry").then((r) => { setCaps(r.data.capabilities); setMeta({ statuses: r.data.statuses, layers: r.data.layers }); }),
    ]).catch(() => setLoadError(true));
  };
  useEffect(load, []);

  const changeStatus = async (id, status) => {
    try {
      await api.patch(`/capability-registry/${id}/status`, { status });
      toast.success("Status updated");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  if (loadError) return (
    <div data-testid="factory-map-error" className="flex flex-col items-center justify-center py-32 text-center">
      <p className="text-navy font-semibold mb-2">Couldn't load the Manufacturing Map™.</p>
      <p className="text-sm text-muted-foreground mb-4">The Factory reported an error fetching the Capability Registry.</p>
      <button data-testid="factory-map-retry" onClick={load} className="px-4 py-2 rounded-md bg-navy text-white text-sm font-semibold hover:bg-navy/90">Retry</button>
    </div>
  );
  if (!map || !summary) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  const layerName = (k) => (meta.layers.find((l) => l.value === k) || {}).name || k;
  const shown = filter === "all" ? caps : caps.filter((c) => c.status === filter);

  return (
    <div data-testid="factory-map-page">
      <PageHeader
        overline="Capability Registry™ · Manufacturing Map™"
        title="The QRU Manufacturing Map™"
        description="One Knowledge Record™ → Many Products™. The canonical architecture: every verified record flows through the Understanding Engine™ into every creative division and out to every distribution channel."
        actions={<VerifiedBadge testid="map-treasure-badge" />}
      />

      {/* Manufacturing Promise */}
      <Panel accent="gold" className="mb-8" testid="manufacturing-promise">
        <div className="flex items-start gap-3 mb-4">
          <ShieldCheck className="w-6 h-6 text-gold shrink-0 mt-0.5" />
          <div>
            <p className="font-heading font-bold text-navy text-lg">{map.promise.title}</p>
            <p className="text-sm text-muted-foreground mt-0.5">{map.promise.statement}</p>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {map.promise.pillars.map((p) => (
            <div key={p.id} data-testid={`promise-${p.id}`} className="rounded-md border border-gold/30 bg-gold/[0.06] p-3">
              <p className="text-[13px] font-bold text-navy">{p.name}</p>
              <p className="text-[11px] text-muted-foreground mt-1 leading-snug">{p.description}</p>
            </div>
          ))}
        </div>
      </Panel>

      {/* Summary counts */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8" data-testid="registry-summary">
        <SummaryCard label="Capabilities" value={summary.total} icon={Layers} />
        {summary.by_status.map((s) => (
          <SummaryCard key={s.status} label={s.label} value={s.count} tone={STATUS_TONE[s.status]}
            onClick={() => { setTab("registry"); setFilter(s.status); }} />
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-border" data-testid="map-tabs">
        {[["map", "Manufacturing Map"], ["registry", "Capability Registry"]].map(([k, l]) => (
          <button key={k} data-testid={`tab-${k}`} onClick={() => setTab(k)}
            className={`px-4 py-2 text-sm font-semibold border-b-2 -mb-px transition-colors ${tab === k ? "border-gold text-navy" : "border-transparent text-muted-foreground hover:text-navy"}`}>
            {l}
          </button>
        ))}
      </div>

      {tab === "map" ? (
        <div data-testid="map-view" className="space-y-6">
          {/* Flow rail */}
          <div className="flex items-center gap-2 flex-wrap text-sm font-bold text-navy mb-2">
            {map.flow.map((f, i) => (
              <span key={f} className="flex items-center gap-2">
                <span className="px-3 py-1.5 rounded-full bg-navy text-white text-xs">{f}</span>
                {i < map.flow.length - 1 && <ArrowRight className="w-4 h-4 text-gold" />}
              </span>
            ))}
          </div>

          {map.nodes.filter((n) => n.capabilities.length > 0).map((node) => (
            <Panel key={node.layer} title={node.name} icon={Layers} testid={`map-node-${node.layer}`}>
              <p className="text-xs text-muted-foreground mb-3">{node.description}</p>
              <div className="flex flex-wrap gap-2">
                {node.capabilities.map((c) => (
                  <button key={c.id} data-testid={`map-cap-${c.id}`}
                    onClick={() => c.route && nav(c.route)}
                    disabled={!c.route}
                    className={`group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold transition-colors ${c.route ? "cursor-pointer hover:border-navy hover:bg-muted/40" : "opacity-70"} ${c.status === "active" ? "border-emerald-300 bg-emerald-50 text-emerald-800" : c.status === "merged" ? "border-amber-300 bg-amber-50 text-amber-800" : c.status === "deprecated" ? "border-slate-300 bg-slate-100 text-slate-500" : c.status === "future" ? "border-navy/25 bg-navy/[0.05] text-navy/70" : "border-royal/30 bg-royal/[0.06] text-royal"}`}>
                    {c.moat && <Star className="w-3 h-3 text-gold fill-gold" />}
                    {c.name}
                    {c.route && <ChevronRight className="w-3 h-3 opacity-40 group-hover:opacity-100" />}
                  </button>
                ))}
              </div>
            </Panel>
          ))}

          {/* Distribution destinations */}
          <Panel title="Universal Distribution Framework™ — Manufacture once, publish everywhere" icon={Radio} accent="gold" testid="map-destinations">
            <div className="flex flex-wrap gap-3">
              {map.destinations.map((d) => {
                const Icon = DEST_ICON[d] || Radio;
                return (
                  <div key={d} className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-border bg-muted/30 text-sm font-semibold text-navy">
                    <Icon className="w-4 h-4 text-gold" /> {d}
                  </div>
                );
              })}
            </div>
          </Panel>
        </div>
      ) : (
        <div data-testid="registry-view">
          {/* Filter chips */}
          <div className="flex flex-wrap gap-2 mb-4">
            {[{ value: "all", label: "All" }, ...meta.statuses].map((s) => (
              <button key={s.value} data-testid={`filter-${s.value}`} onClick={() => setFilter(s.value)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${filter === s.value ? "bg-navy text-white border-navy" : "border-border text-muted-foreground hover:border-navy"}`}>
                {s.label}
              </button>
            ))}
          </div>

          <Panel testid="registry-table" className="overflow-hidden">
            <div className="overflow-x-auto -m-5">
              <table className="w-full text-sm">
                <thead className="bg-muted/40"><tr>
                  {["Capability", "Division", "Current Purpose", "Status", "Set Status"].map((h) => (
                    <th key={h} className="text-left font-bold text-navy px-4 py-2.5 text-[11px] uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {shown.map((c) => (
                    <tr key={c.id} data-testid={`cap-row-${c.id}`} className="border-t border-border hover:bg-muted/20">
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5">
                          {c.moat && <Star className="w-3 h-3 text-gold fill-gold shrink-0" />}
                          <button onClick={() => c.route && nav(c.route)} disabled={!c.route}
                            className={`font-semibold text-navy text-left ${c.route ? "hover:underline" : "cursor-default"}`}>{c.name}</button>
                        </div>
                        {c.note && <p className="text-[11px] text-muted-foreground mt-0.5 flex items-center gap-1">{c.status === "merged" ? <GitMerge className="w-3 h-3" /> : c.status === "deprecated" ? <Archive className="w-3 h-3" /> : c.status === "future" ? <Sparkles className="w-3 h-3" /> : null}{c.note}</p>}
                      </td>
                      <td className="px-4 py-2.5 text-xs text-muted-foreground whitespace-nowrap">{layerName(c.layer)}</td>
                      <td className="px-4 py-2.5 text-xs text-muted-foreground max-w-xs">{c.current_purpose}</td>
                      <td className="px-4 py-2.5"><StatusChip status={STATUS_LABEL[c.status]} tone={STATUS_TONE[c.status]} testid={`cap-status-${c.id}`} /></td>
                      <td className="px-4 py-2.5">
                        <select data-testid={`cap-select-${c.id}`} value={c.status} onChange={(e) => changeStatus(c.id, e.target.value)}
                          className="text-xs border border-border rounded px-2 py-1 bg-card outline-none focus:border-navy">
                          {meta.statuses.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}

function SummaryCard({ label, value, icon: Icon, tone, onClick }) {
  const ring = tone === "emerald" ? "border-emerald-200" : tone === "amber" ? "border-amber-200" : tone === "slate" ? "border-slate-200" : tone === "royal" ? "border-royal/25" : "border-border";
  return (
    <button onClick={onClick} disabled={!onClick} data-testid={`summary-${label.toLowerCase().replace(/\s+/g, "-")}`}
      className={`text-left qru-card p-4 border ${ring} ${onClick ? "qru-interactive cursor-pointer" : ""}`}>
      <div className="flex items-center justify-between">
        <p className="font-heading text-2xl font-bold text-navy leading-none">{value}</p>
        {Icon && <Icon className="w-4 h-4 text-gold" />}
      </div>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground mt-2">{label}</p>
    </button>
  );
}
