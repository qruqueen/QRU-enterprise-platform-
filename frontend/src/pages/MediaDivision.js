import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { PageHeader } from "@/components/shared";
import { Panel, StatusChip, VerifiedBadge, MetricCard } from "@/components/qru";
import {
  Loader2, Layers, ShieldCheck, Download, CheckCircle2, XCircle, Sparkles,
  BookOpen, Pencil, GraduationCap, Users, Presentation, ClipboardList, Image as ImageIcon,
  LayoutTemplate, Clapperboard, Mic, Share2, RefreshCw,
} from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const ICON = { book: BookOpen, pencil: Pencil, graduation: GraduationCap, users: Users, presentation: Presentation, clipboard: ClipboardList, image: ImageIcon, layout: LayoutTemplate, clapperboard: Clapperboard, mic: Mic, share: Share2 };

export default function MediaDivision() {
  const [catalog, setCatalog] = useState(null);
  const [future, setFuture] = useState([]);
  const [pillars, setPillars] = useState([]);
  const [krs, setKrs] = useState([]);
  const [krId, setKrId] = useState("");
  const [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [refreshing, setRefreshing] = useState(null);

  useEffect(() => {
    api.get("/media-division/catalog").then((r) => { setCatalog(r.data.catalog); setFuture(r.data.future); setPillars(r.data.promise_pillars); setSelected(r.data.catalog.map((c) => c.id)); }).catch(() => {});
    api.get("/media-division/verified-krs").then((r) => { setKrs(r.data.records); if (r.data.records[0]) setKrId(r.data.records[0].id); }).catch(() => {});
    api.get("/media-division/stats").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const manufacture = async (formats) => {
    if (!krId) { toast.error("Select a verified Knowledge Record first."); return; }
    setBusy(true); setResult(null);
    toast.message("Manufacturing the media catalog from one verified Knowledge Record… this may take a minute.");
    try {
      const { data } = await api.post("/media-division/manufacture", { kr_id: krId, formats });
      setResult(data);
      toast.success(`Manufactured ${data.manufactured}/${data.total} formats.`);
      api.get("/media-division/stats").then((r) => setStats(r.data));
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const regenCover = async (pid) => {
    setRefreshing(pid);
    toast.message("Refreshing cover to the Gold Standard (new hero art)…");
    try {
      await api.post(`/products/${pid}/regenerate-cover`);
      toast.success("Cover refreshed to the new Gold Standard.");
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setRefreshing(null); }
  };

  if (!catalog) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;

  return (
    <div data-testid="media-division-page">
      <PageHeader
        overline="Media Manufacturing Division™ · Stone 2 · Inheritance-First™"
        title="One Knowledge Record™ → Many Products™"
        description="Manufacture the full media catalog from a single verified Knowledge Record. Every product inherits the same verified knowledge, citations, branding, governance and the Treasure Standard™ — no duplicated truth."
        actions={<VerifiedBadge label="Manufacturing Promise™" testid="md-badge" />}
      />

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6" data-testid="md-stats">
          <MetricCard icon={ShieldCheck} label="Verified KRs Available" value={stats.verified_krs} testid="stat-verified" />
          <MetricCard icon={Layers} accent="gold" label="Catalog Formats" value={stats.formats} testid="stat-formats" />
          <MetricCard icon={Sparkles} label="Products From Division" value={stats.products_from_division} testid="stat-from-division" />
          <MetricCard icon={Clapperboard} accent="royal" label="Studio Formats (Audio/Video)" value={stats.future_formats} testid="stat-future" />
        </div>
      )}

      {/* Manufacturing Promise */}
      <Panel accent="gold" className="mb-6" testid="md-promise">
        <div className="flex flex-wrap items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-gold" />
          <span className="text-sm font-bold text-navy">Every product inherits:</span>
          {pillars.map((p) => <StatusChip key={p} status={p} tone="gold" />)}
        </div>
      </Panel>

      {/* KR selector */}
      <Panel title="1 · Choose the verified Knowledge Record™" icon={ShieldCheck} testid="md-kr-select" className="mb-6">
        {krs.length === 0 ? (
          <p className="text-sm text-muted-foreground">No verified Knowledge Records yet. Approve one in Knowledge Record Manufacturing™ first — products may only inherit from verified knowledge.</p>
        ) : (
          <select data-testid="md-kr-dropdown" value={krId} onChange={(e) => setKrId(e.target.value)}
            className="w-full px-3 py-2.5 text-sm border border-border rounded-md bg-card outline-none focus:border-navy">
            {krs.map((k) => {
              const label = `${k.kr_code} — ${k.title} (${k.category})`;
              return <option key={k.id} value={k.id}>{label}</option>;
            })}
          </select>
        )}
      </Panel>

      {/* Catalog */}
      <Panel title="2 · Select the products to manufacture" icon={Layers} testid="md-catalog" className="mb-6"
        actions={<button data-testid="md-manufacture-all" onClick={() => { if (window.confirm(`Manufacture ALL ${catalog.length} formats from this Knowledge Record? Document formats use AI and can take a few minutes.`)) manufacture(catalog.map((c) => c.id)); }} disabled={busy || !krId}
          className="inline-flex items-center gap-2 bg-gold text-navy px-4 py-2 rounded-md text-sm font-bold disabled:opacity-60">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Manufacture Everything</button>}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 mb-4">
          {catalog.map((c) => {
            const Icon = ICON[c.icon] || Layers;
            const on = selected.includes(c.id);
            return (
              <button key={c.id} data-testid={`format-${c.id}`} onClick={() => toggle(c.id)}
                className={`flex items-center gap-2.5 p-3 rounded-md border text-left text-sm transition-colors ${on ? "border-navy bg-navy/[0.04]" : "border-border opacity-60 hover:opacity-100"}`}>
                <Icon className={`w-4 h-4 shrink-0 ${on ? "text-gold" : "text-muted-foreground"}`} />
                <span className="flex-1"><span className="font-semibold text-navy">{c.name}</span><span className="block text-[10px] text-muted-foreground">{c.division}</span></span>
                {on && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
              </button>
            );
          })}
        </div>
        <button data-testid="md-manufacture-selected" onClick={() => manufacture(selected)} disabled={busy || !krId || selected.length === 0}
          className="inline-flex items-center gap-2 bg-navy text-white px-4 py-2 rounded-md text-sm font-bold disabled:opacity-60">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Manufacture {selected.length} selected
        </button>
      </Panel>

      {/* Results */}
      {result && (
        <Panel title={`Manufactured from ${result.kr.kr_code} — ${result.kr.title}`} icon={CheckCircle2} accent="royal" testid="md-results" className="mb-6">
          <div className="space-y-2" data-testid="md-results-list">
            {result.results.map((r) => (
              <div key={r.format} data-testid={`result-${r.format}`} className="flex items-center justify-between gap-3 border border-border rounded-md p-3 flex-wrap">
                <div className="flex items-center gap-2 min-w-0">
                  {r.ok ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <XCircle className="w-4 h-4 text-red-500 shrink-0" />}
                  <span className="font-semibold text-navy text-sm">{r.name}</span>
                  {r.product_code && <span className="font-mono text-[10px] text-muted-foreground">{r.product_code}</span>}
                  {!r.ok && <span className="text-[11px] text-red-500">{r.error}</span>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {(r.files || []).map((f) => (
                    <a key={f.format} data-testid={`dl-${r.format}-${f.format}`} href={`${BACKEND}${f.url}`} target="_blank" rel="noreferrer"
                      className="inline-flex items-center gap-1 border border-navy/20 text-navy px-2.5 py-1 rounded-sm text-[11px] font-medium hover:bg-muted/40"><Download className="w-3 h-3" /> {f.label || f.format.toUpperCase()}</a>
                  ))}
                  {r.png_url && <a data-testid={`dl-${r.format}-png`} href={`${BACKEND}${r.png_url}`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 border border-navy/20 text-navy px-2.5 py-1 rounded-sm text-[11px] font-medium"><Download className="w-3 h-3" /> Poster PNG</a>}
                  {r.product_id && (
                    <button data-testid={`regen-${r.format}`} onClick={() => regenCover(r.product_id)} disabled={refreshing === r.product_id}
                      className="inline-flex items-center gap-1 border border-gold/40 text-navy px-2.5 py-1 rounded-sm text-[11px] font-medium hover:bg-gold/10">
                      {refreshing === r.product_id ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />} Refresh cover</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* Audio & video formats — live in the Studios */}
      <Panel title="Audio & Video — made in the Studios" icon={Clapperboard} testid="md-future">
        <p className="text-[12px] text-muted-foreground mb-3">
          These formats are manufactured in the <span className="font-semibold text-navy">Story &amp; Cinema Studio™</span> and{" "}
          <span className="font-semibold text-navy">Podcast Studio™</span> (audio &amp; video). Pick a verified Knowledge Record there and
          the Factory renders a real MP3/MP4 — same verified knowledge, branding and governance as everything above.
        </p>
        <div className="flex flex-wrap gap-2">
          {future.map((f) => (
            <Link key={f.id} to="/cinema-studio" data-testid={`future-${f.id}`}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-royal/30 bg-royal/[0.04] text-xs hover:border-royal hover:bg-royal/[0.08] transition-colors">
              {f.division === "Audio" ? <Mic className="w-3 h-3 text-royal" /> : <Clapperboard className="w-3 h-3 text-royal" />}
              <span className="font-semibold text-navy">{f.name}</span>
              <span className="text-[10px] text-muted-foreground">· {f.by}</span>
            </Link>
          ))}
        </div>
        <Link to="/cinema-studio" data-testid="md-open-studios"
          className="inline-flex items-center gap-1.5 mt-3 text-[12px] font-bold text-royal hover:underline">
          Open the Studios <Clapperboard className="w-3.5 h-3.5" />
        </Link>
      </Panel>
    </div>
  );
}
