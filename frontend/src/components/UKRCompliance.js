import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { ShieldCheck, AlertTriangle, XCircle, Loader2, Link2, Archive, BookMarked, RefreshCw } from "lucide-react";

const StatBox = ({ label, value, tone, testid }) => (
  <div data-testid={testid} className={`rounded-lg border p-3 ${tone}`}>
    <div className="text-2xl font-bold leading-none">{value}</div>
    <div className="text-[11px] uppercase tracking-wide mt-1 opacity-80">{label}</div>
  </div>
);

export const UKRCompliance = () => {
  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showRemediate, setShowRemediate] = useState(false);
  const [items, setItems] = useState([]);
  const [expanded, setExpanded] = useState(null);
  const [suggestions, setSuggestions] = useState({});
  const [working, setWorking] = useState(null);

  const loadAudit = () => api.get("/products/ukr-audit").then(({ data }) => setAudit(data)).catch(() => {});
  const loadDetails = () => api.get("/products/ukr-audit/details").then(({ data }) => setItems(data.items || [])).catch(() => {});

  useEffect(() => { loadAudit().finally(() => setLoading(false)); }, []);

  const openRemediate = async () => { setShowRemediate(true); await loadDetails(); };

  const expand = async (id) => {
    setExpanded(expanded === id ? null : id);
    if (!suggestions[id]) {
      const { data } = await api.get(`/products/${id}/ukr-suggestions`);
      setSuggestions((s) => ({ ...s, [id]: data.suggestions || [] }));
    }
  };

  const act = async (id, fn, msg) => {
    setWorking(id);
    try { await fn(); toast.success(msg); await Promise.all([loadAudit(), loadDetails()]); setExpanded(null); }
    catch (e) { toast.error(e?.response?.data?.detail || "Action failed"); }
    finally { setWorking(null); }
  };

  const bind = (id, krId, code) => act(id, () => api.post(`/products/${id}/ukr-bind`, { kr_id: krId }), `Bound to ${code} ✓`);
  const quarantine = (id) => act(id, () => api.post(`/products/${id}/ukr-quarantine`), "Quarantined ✓");
  const exception = (id) => act(id, () => api.post(`/products/${id}/ukr-exception`), "Classified as Founder-authored ✓");

  if (loading) return <div className="p-4 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading compliance…</div>;
  if (!audit) return null;

  return (
    <div data-testid="ukr-compliance-panel" className="rounded-xl border border-gold/40 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h2 className="font-heading text-lg font-bold text-navy flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-gold" /> Knowledge-First™ Compliance
        </h2>
        <div className="flex items-center gap-2">
          <span data-testid="ukr-compliance-pct" className="text-sm font-bold text-navy">{audit.compliant_pct}% compliant</span>
          <button data-testid="ukr-refresh" onClick={() => loadAudit()} className="text-muted-foreground hover:text-navy"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
        <StatBox testid="ukr-green" label="Verified UKR" value={audit.green} tone="border-emerald-200 bg-emerald-50 text-emerald-800" />
        <StatBox testid="ukr-amber" label="Unverified / dangling" value={audit.amber} tone="border-amber-200 bg-amber-50 text-amber-800" />
        <StatBox testid="ukr-red" label="No UKR" value={audit.red} tone="border-red-200 bg-red-50 text-red-800" />
        <StatBox testid="ukr-published-bad" label="Published non-compliant" value={audit.published_noncompliant_count} tone="border-red-300 bg-red-100 text-red-900" />
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button data-testid="ukr-open-remediation" onClick={openRemediate}
          className="text-sm font-semibold bg-navy text-white rounded-full px-4 py-2 hover:bg-navy/90">
          Open guided remediation ({audit.amber + audit.red})
        </button>
        <span className="text-[11px] text-muted-foreground">Total governed: {audit.total} · enforcement is live in preview (redeploy to activate production)</span>
      </div>

      {showRemediate && (
        <div data-testid="ukr-remediation-list" className="mt-5 border-t pt-4 space-y-2 max-h-[520px] overflow-y-auto">
          <p className="text-[12px] text-muted-foreground">Published-noncompliant shown first. Nothing is auto-bound — every decision is yours.</p>
          {items.length === 0 && <p className="text-sm text-emerald-700 font-semibold">🎉 Nothing to remediate — 100% compliant.</p>}
          {items.map((it) => (
            <div key={it.id} data-testid={`ukr-item-${it.id}`} className="border rounded-lg p-3">
              <div className="flex items-center justify-between gap-2 cursor-pointer" onClick={() => expand(it.id)}>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-navy truncate flex items-center gap-2">
                    {it.trace_status === "red" ? <XCircle className="w-4 h-4 text-red-500 shrink-0" /> : <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />}
                    {it.title || "(untitled)"} <span className="text-[11px] text-muted-foreground font-normal">· {it.product_type}</span>
                  </div>
                  <div className="text-[11px] text-muted-foreground">{it.reason}{it.published && <span className="ml-2 text-red-600 font-semibold">PUBLISHED</span>}</div>
                </div>
                <span className="text-[11px] text-royal shrink-0">{expanded === it.id ? "Hide" : "Fix"}</span>
              </div>

              {expanded === it.id && (
                <div className="mt-3 space-y-2" data-testid={`ukr-fix-${it.id}`}>
                  <div className="text-[11px] font-bold uppercase text-navy">Suggested Verified UKRs</div>
                  {(suggestions[it.id] || []).length === 0 && <div className="text-[12px] text-muted-foreground">No close match — create a new UKR or classify below.</div>}
                  {(suggestions[it.id] || []).map((s) => (
                    <div key={s.id} className="flex items-center justify-between gap-2 bg-muted/40 rounded p-2">
                      <div className="text-[12px] min-w-0"><span className="font-semibold">{s.kr_code}</span> · <span className="truncate">{s.title}</span> <span className="text-emerald-700">✓ Verified</span></div>
                      <button data-testid={`ukr-bind-${it.id}-${s.id}`} disabled={working === it.id} onClick={() => bind(it.id, s.id, s.kr_code)}
                        className="text-[11px] font-semibold text-white bg-emerald-600 rounded-full px-3 py-1 hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1">
                        <Link2 className="w-3 h-3" /> Bind
                      </button>
                    </div>
                  ))}
                  <div className="flex gap-2 pt-1">
                    <button data-testid={`ukr-exception-${it.id}`} disabled={working === it.id} onClick={() => exception(it.id)}
                      className="text-[11px] font-semibold text-navy border border-navy/30 rounded-full px-3 py-1 hover:bg-navy/5 flex items-center gap-1">
                      <BookMarked className="w-3 h-3" /> Founder-authored exception
                    </button>
                    <button data-testid={`ukr-quarantine-${it.id}`} disabled={working === it.id} onClick={() => quarantine(it.id)}
                      className="text-[11px] font-semibold text-red-700 border border-red-300 rounded-full px-3 py-1 hover:bg-red-50 flex items-center gap-1">
                      <Archive className="w-3 h-3" /> Quarantine
                    </button>
                    {working === it.id && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
