import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, StatusBadge } from "@/components/shared";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, ChevronRight, Factory } from "lucide-react";

const STAGES = ["Queued", "Research", "Manufacturing", "Quality Review", "Approved", "Published"];
const PRODUCT_TYPES = ["Book", "Poster", "Infographic", "Presentation", "Teacher Guide", "Caregiver Guide", "Workbook", "Lesson Plan", "Video Script", "Quiz", "Flash Cards", "Course"];

function CreateOrderDialog({ onCreated }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ topic: "", audience: "General public", priority: "Medium", product_types: [] });
  const [saving, setSaving] = useState(false);

  const toggleType = (t) =>
    setForm((f) => ({ ...f, product_types: f.product_types.includes(t) ? f.product_types.filter((x) => x !== t) : [...f.product_types, t] }));

  const save = async () => {
    if (!form.topic) return toast.error("Topic is required");
    setSaving(true);
    try {
      const { data } = await api.post("/manufacturing-orders", form);
      toast.success(`Created ${data.mo_code}`);
      setOpen(false);
      setForm({ topic: "", audience: "General public", priority: "Medium", product_types: [] });
      onCreated?.();
    } catch { toast.error("Failed to create order"); } finally { setSaving(false); }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button data-testid="mo-new-btn" className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
          <Plus className="w-4 h-4" /> New Order
        </button>
      </DialogTrigger>
      <DialogContent className="rounded-md">
        <DialogHeader><DialogTitle className="font-heading">New Manufacturing Order™</DialogTitle></DialogHeader>
        <div className="space-y-4 py-2">
          <div>
            <label className="text-sm font-medium">Topic</label>
            <input data-testid="mo-topic-input" value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })}
              className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium">Audience</label>
              <input data-testid="mo-audience-input" value={form.audience} onChange={(e) => setForm({ ...form, audience: e.target.value })}
                className="mt-1 w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
            </div>
            <div>
              <label className="text-sm font-medium">Priority</label>
              <select data-testid="mo-priority-input" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="mt-1 w-full px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary">
                {["Low", "Medium", "High"].map((p) => <option key={p}>{p}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium">Product Types</label>
            <div className="mt-2 flex flex-wrap gap-2">
              {PRODUCT_TYPES.map((t) => (
                <button key={t} type="button" onClick={() => toggleType(t)}
                  className={`text-xs px-2.5 py-1 rounded-sm border transition-colors ${form.product_types.includes(t) ? "bg-primary text-primary-foreground border-primary" : "hover:border-primary"}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <button data-testid="mo-save-btn" onClick={save} disabled={saving}
            className="bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 disabled:opacity-60">
            {saving ? "Saving…" : "Create Order"}
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function ManufacturingOrders() {
  const [orders, setOrders] = useState([]);
  const load = () => api.get("/manufacturing-orders").then((r) => setOrders(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const advance = async (o) => {
    const idx = STAGES.indexOf(o.status);
    if (idx >= STAGES.length - 1) return;
    const next = STAGES[idx + 1];
    try {
      await api.patch(`/manufacturing-orders/${o.id}/status`, { status: next });
      toast.success(`${o.mo_code} → ${next}`);
      load();
    } catch { toast.error("Failed to advance"); }
  };

  return (
    <div>
      <PageHeader
        overline="Manufacturing Orders™"
        title="Production Floor"
        description="Track every order across the manufacturing pipeline. Advance stages toward publication — human approval required."
        actions={<CreateOrderDialog onCreated={load} />}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6 gap-4">
        {STAGES.map((stage) => {
          const items = orders.filter((o) => o.status === stage);
          return (
            <div key={stage} data-testid={`kanban-col-${stage.toLowerCase().replace(/\s/g, "-")}`} className="flex flex-col">
              <div className="flex items-center justify-between mb-3 px-1">
                <h3 className="text-sm font-medium">{stage}</h3>
                <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">{items.length}</span>
              </div>
              <div className="space-y-3 min-h-[80px]">
                {items.map((o) => (
                  <div key={o.id} data-testid={`mo-card-${o.id}`} className="bg-card border rounded-md p-3 hover:shadow-sm transition-all">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-[11px] text-muted-foreground">{o.mo_code}</span>
                      <StatusBadge status={o.priority} />
                    </div>
                    <p className="text-sm font-medium leading-snug">{o.topic}</p>
                    <p className="text-xs text-muted-foreground mt-1">{o.audience}</p>
                    {o.product_types?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {o.product_types.slice(0, 3).map((t) => (
                          <span key={t} className="text-[10px] bg-muted px-1.5 py-0.5 rounded-sm">{t}</span>
                        ))}
                      </div>
                    )}
                    {stage !== "Published" && (
                      <button data-testid={`mo-advance-${o.id}`} onClick={() => advance(o)}
                        className="mt-3 w-full flex items-center justify-center gap-1 text-xs text-primary font-medium border border-primary/30 rounded-sm py-1.5 hover:bg-primary/5 transition-colors">
                        Advance <ChevronRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                ))}
                {items.length === 0 && (
                  <div className="border border-dashed rounded-md py-6 flex items-center justify-center text-muted-foreground">
                    <Factory className="w-4 h-4" />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
