import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Loader2, ArrowRight, Pencil, Check, RotateCcw, Send } from "lucide-react";

// Editable destination preview for the Publish screen.
// Shows where a product/book will go when published, and lets the Founder override.
export function DestinationPreview({ target, id, productType, className = "" }) {
  const [data, setData] = useState(null);
  const [editing, setEditing] = useState(false);
  const [sel, setSel] = useState([]);
  const [saving, setSaving] = useState(false);

  const load = () => {
    api.get("/distribution-architecture/destinations", { params: { target, id } })
      .then((r) => { setData(r.data); setSel(r.data.current || []); })
      .catch(() => setData({ error: true }));
  };
  useEffect(() => { if (target && id) load(); /* eslint-disable-next-line */ }, [target, id]);

  if (!data) return <div className={`flex items-center gap-2 text-xs text-muted-foreground ${className}`}><Loader2 className="w-3.5 h-3.5 animate-spin" /> Resolving destinations…</div>;
  if (data.error) return null;

  const all = data.experiences || [];
  const nameOf = (eid) => all.find((e) => e.id === eid)?.name || eid;

  const toggle = (eid) => setSel((s) => s.includes(eid) ? s.filter((x) => x !== eid) : [...s, eid]);

  const save = async () => {
    setSaving(true);
    try {
      await api.post("/distribution-architecture/destinations", { target, id, experiences: sel });
      toast.success("Destinations updated."); setEditing(false); load();
    } catch (e) { toast.error(e.response?.data?.detail || "Save failed."); }
    setSaving(false);
  };

  const revert = async () => {
    setSaving(true);
    try {
      await api.post("/distribution-architecture/destinations", { target, id, experiences: [] });
      toast.success("Reverted to automatic destinations."); setEditing(false); load();
    } catch (e) { toast.error("Revert failed."); }
    setSaving(false);
  };

  return (
    <div className={`rounded-lg border border-navy/15 bg-navy/[0.03] p-3 ${className}`} data-testid="destination-preview">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-navy">
          <Send className="w-3.5 h-3.5" /> Publishes to
          <span className={`text-[10px] font-medium rounded-full px-1.5 py-0.5 ${data.overridden ? "bg-gold/20 text-navy" : "bg-emerald-100 text-emerald-700"}`}>
            {data.overridden ? "Founder override" : "Automatic"}
          </span>
        </div>
        {!editing ? (
          <button onClick={() => setEditing(true)} data-testid="dest-edit" className="text-[11px] text-royal inline-flex items-center gap-1 hover:underline"><Pencil className="w-3 h-3" /> Change</button>
        ) : (
          <div className="flex items-center gap-2">
            <button onClick={save} disabled={saving} data-testid="dest-save" className="text-[11px] text-white bg-navy rounded-full px-2.5 py-1 inline-flex items-center gap-1 disabled:opacity-50">{saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />} Save</button>
            <button onClick={revert} disabled={saving} data-testid="dest-revert" className="text-[11px] text-royal inline-flex items-center gap-1 hover:underline"><RotateCcw className="w-3 h-3" /> Auto</button>
          </div>
        )}
      </div>
      {!editing ? (
        <div className="flex flex-wrap gap-1.5" data-testid="dest-current">
          {(data.current || []).map((eid) => (
            <span key={eid} className="inline-flex items-center gap-1 text-[11px] rounded-full bg-navy/10 text-navy px-2.5 py-1 font-medium"><ArrowRight className="w-3 h-3" />{nameOf(eid)}</span>
          ))}
        </div>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {all.map((e) => (
            <button key={e.id} onClick={() => toggle(e.id)} data-testid={`dest-toggle-${e.id}`}
              className={`inline-flex items-center gap-1 text-[11px] rounded-full px-2.5 py-1 font-medium border transition-colors ${sel.includes(e.id) ? "bg-navy text-white border-navy" : "border-navy/20 text-navy hover:bg-navy/5"}`}>
              {sel.includes(e.id) && <Check className="w-3 h-3" />}{e.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Compact read-only chips computed from a preloaded destinations map (no per-row network).
export function DestinationChips({ productType, destMap }) {
  const row = (destMap || []).find((r) => r.product_type === productType);
  const dests = row ? row.destinations : [{ id: "resources", name: "Resources" }];
  return (
    <span className="inline-flex flex-wrap items-center gap-1" data-testid="destination-chips">
      <span className="text-[9px] uppercase tracking-wide text-muted-foreground">→</span>
      {dests.map((d) => (
        <span key={d.id} className="text-[9px] font-semibold text-navy bg-navy/10 rounded-full px-1.5 py-0.5">{d.name}</span>
      ))}
    </span>
  );
}
