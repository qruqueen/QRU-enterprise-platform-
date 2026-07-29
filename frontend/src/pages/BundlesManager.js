import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, Plus, Gift, Trash2, Check, Rocket, RotateCcw, X, Image as ImageIcon,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

function StatusPill({ status }) {
  const cls = status === "Published" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700";
  return <span className={`text-[11px] font-semibold rounded-full px-2.5 py-1 ${cls}`}>{status}</span>;
}

export default function BundlesManager() {
  const [bundles, setBundles] = useState(null);
  const [eligible, setEligible] = useState([]);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState("");
  const [form, setForm] = useState({ title: "", subtitle: "", description: "", price: "", item_ids: [] });

  const load = () => {
    Promise.all([api.get("/bundles"), api.get("/bundles/eligible-items")])
      .then(([a, b]) => { setBundles(a.data.bundles); setEligible(b.data.items); })
      .catch(() => { setBundles([]); toast.error("Failed to load bundles."); });
  };
  useEffect(() => { load(); }, []);

  const sumSelected = form.item_ids.reduce((s, id) => s + (eligible.find((e) => e.id === id)?.price || 0), 0);

  const toggleItem = (id) => setForm((f) => ({
    ...f, item_ids: f.item_ids.includes(id) ? f.item_ids.filter((x) => x !== id) : [...f.item_ids, id],
  }));

  const create = async () => {
    if (!form.title || form.item_ids.length < 2 || !form.price) {
      toast.error("A bundle needs a title, a price, and at least 2 items."); return;
    }
    setBusy("create");
    try {
      await api.post("/bundles", { ...form, price: parseFloat(form.price) });
      toast.success("Bundle created as a draft."); setOpen(false);
      setForm({ title: "", subtitle: "", description: "", price: "", item_ids: [] }); load();
    } catch (e) { toast.error(e.response?.data?.detail || "Create failed."); }
    setBusy("");
  };

  const act = async (id, action) => {
    setBusy(id + action);
    try {
      if (action === "delete") { await api.delete(`/bundles/${id}`); toast.success("Bundle deleted."); }
      else { await api.post(`/bundles/${id}/${action}`); toast.success(action === "publish" ? "Bundle published to the Bundles experience." : action === "cover" ? "Bundle cover regenerated ($0 AI)." : "Bundle moved back to draft."); }
      load();
    } catch (e) { toast.error(e.response?.data?.detail || "Action failed."); }
    setBusy("");
  };

  if (bundles === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>;

  return (
    <div className="space-y-6" data-testid="bundles-manager">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <PageHeader title="Bundles™" subtitle="First-class bundle products. Fill a bundle with any deliverable items, price it as one, and publish it to the Bundles experience on qru-online.com." />
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <button data-testid="new-bundle-btn" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90">
              <Plus className="w-4 h-4" /> New Bundle
            </button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl" data-testid="new-bundle-dialog">
            <DialogHeader>
              <DialogTitle>Create a Bundle</DialogTitle>
              <DialogDescription>Pick the titles, set one price, and we'll show the savings vs. buying separately.</DialogDescription>
            </DialogHeader>
            <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
              <Input data-testid="bundle-title-input" placeholder="Bundle title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              <Input data-testid="bundle-subtitle-input" placeholder="Subtitle (optional)" value={form.subtitle} onChange={(e) => setForm({ ...form, subtitle: e.target.value })} />
              <Textarea data-testid="bundle-desc-input" placeholder="Description (optional)" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              <div>
                <div className="text-xs font-medium text-muted-foreground mb-2">Select items (books) — choose at least 2</div>
                <div className="space-y-1.5 border rounded-lg p-2">
                  {eligible.map((it) => (
                    <button key={it.id} onClick={() => toggleItem(it.id)} data-testid={`select-item-${it.id}`}
                      className={`w-full flex items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition-colors ${form.item_ids.includes(it.id) ? "bg-navy/10" : "hover:bg-muted"}`}>
                      <span className={`w-4 h-4 rounded border grid place-items-center ${form.item_ids.includes(it.id) ? "bg-navy border-navy" : "border-muted-foreground/40"}`}>
                        {form.item_ids.includes(it.id) && <Check className="w-3 h-3 text-white" />}
                      </span>
                      <span className="flex-1 truncate">{it.title}</span>
                      <span className="text-xs text-muted-foreground">${it.price.toFixed(2)}</span>
                    </button>
                  ))}
                  {eligible.length === 0 && <p className="text-xs text-muted-foreground p-2">No eligible books yet (need authorized books with a price + EPUB).</p>}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Input data-testid="bundle-price-input" type="number" step="0.01" placeholder="Bundle price (USD)" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} className="max-w-[200px]" />
                <span className="text-xs text-muted-foreground">
                  Items total ${sumSelected.toFixed(2)}
                  {form.price && sumSelected > parseFloat(form.price) && <span className="text-emerald-600 font-medium"> · saves ${(sumSelected - parseFloat(form.price)).toFixed(2)}</span>}
                </span>
              </div>
            </div>
            <DialogFooter>
              <button onClick={create} disabled={busy === "create"} data-testid="bundle-create-btn" className="inline-flex items-center gap-2 rounded-lg bg-navy text-white px-4 py-2 text-sm font-medium hover:opacity-90 disabled:opacity-50">
                {busy === "create" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />} Create draft
              </button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {bundles.length === 0 ? (
        <div className="border border-dashed rounded-xl p-16 text-center" data-testid="no-bundles">
          <Gift className="w-8 h-8 text-royal mx-auto mb-3" />
          <p className="font-heading font-bold text-navy">No bundles yet</p>
          <p className="text-sm text-muted-foreground mt-1">Create your first bundle to sell multiple titles as one.</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {bundles.map((b) => (
            <div key={b.id} className="rounded-xl border bg-card overflow-hidden" data-testid={`bundle-${b.id}`}>
              {b.cover_url && (
                <img src={`${BACKEND}${b.cover_url.startsWith("/") ? b.cover_url : "/" + b.cover_url}`} alt={b.title}
                  className="w-full h-40 object-cover border-b" data-testid={`bundle-cover-${b.id}`} />
              )}
              <div className="p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2"><Gift className="w-4 h-4 text-navy" /><span className="font-heading font-bold text-navy">{b.title}</span></div>
                  {b.subtitle && <p className="text-xs text-muted-foreground mt-0.5">{b.subtitle}</p>}
                </div>
                <StatusPill status={b.status} />
              </div>
              <div className="flex items-baseline gap-2 mt-3">
                <span className="text-xl font-bold text-navy">${(b.price || 0).toFixed(2)}</span>
                {b.savings > 0 && <span className="text-xs text-muted-foreground line-through">${b.sum_price.toFixed(2)}</span>}
                {b.savings > 0 && <span className="text-xs text-emerald-600 font-medium">save ${b.savings.toFixed(2)}</span>}
              </div>
              <div className="mt-3 space-y-1">
                {(b.item_detail || []).map((it) => (
                  <div key={it.id} className="text-[12px] text-muted-foreground flex items-center gap-2">
                    <Check className={`w-3 h-3 ${it.deliverable ? "text-emerald-600" : "text-amber-500"}`} /> {it.title}
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-2 mt-4">
                {b.status !== "Published" ? (
                  <button onClick={() => act(b.id, "publish")} disabled={!!busy} data-testid={`publish-${b.id}`} className="inline-flex items-center gap-1.5 rounded-lg bg-navy text-white px-3 py-1.5 text-xs font-medium hover:opacity-90 disabled:opacity-50">
                    {busy === b.id + "publish" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Rocket className="w-3.5 h-3.5" />} Publish
                  </button>
                ) : (
                  <button onClick={() => act(b.id, "unpublish")} disabled={!!busy} data-testid={`unpublish-${b.id}`} className="inline-flex items-center gap-1.5 rounded-lg border border-navy/30 text-navy px-3 py-1.5 text-xs font-medium hover:bg-navy/5 disabled:opacity-50">
                    <RotateCcw className="w-3.5 h-3.5" /> Unpublish
                  </button>
                )}
                <button onClick={() => act(b.id, "delete")} disabled={!!busy} data-testid={`delete-${b.id}`} className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 text-red-700 px-3 py-1.5 text-xs font-medium hover:bg-red-50 disabled:opacity-50">
                  <Trash2 className="w-3.5 h-3.5" /> Delete
                </button>
                <button onClick={() => act(b.id, "cover")} disabled={!!busy} data-testid={`cover-${b.id}`} className="inline-flex items-center gap-1.5 rounded-lg border border-navy/30 text-navy px-3 py-1.5 text-xs font-medium hover:bg-navy/5 disabled:opacity-50">
                  {busy === b.id + "cover" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ImageIcon className="w-3.5 h-3.5" />} Regenerate cover
                </button>
              </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
