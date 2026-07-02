import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Users, Plus } from "lucide-react";

export default function Customers() {
  const [customers, setCustomers] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", organization: "", type: "Individual", license_tier: "Standard" });
  const load = () => api.get("/customers").then((r) => setCustomers(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const save = async () => {
    if (!form.name || !form.email) return toast.error("Name and email required");
    try {
      await api.post("/customers", form);
      toast.success("Customer added");
      setOpen(false);
      setForm({ name: "", email: "", organization: "", type: "Individual", license_tier: "Standard" });
      load();
    } catch { toast.error("Failed"); }
  };

  return (
    <div>
      <PageHeader
        overline="Customer Management & Licensing"
        title="Customers"
        description="Institutions and individuals licensing QRU understanding products."
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <button data-testid="customer-new-btn" className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
                <Plus className="w-4 h-4" /> New Customer
              </button>
            </DialogTrigger>
            <DialogContent className="rounded-md">
              <DialogHeader><DialogTitle className="font-heading">New Customer</DialogTitle></DialogHeader>
              <div className="space-y-3 py-2">
                <input data-testid="customer-name" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
                <input data-testid="customer-email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
                <input data-testid="customer-org" placeholder="Organization" value={form.organization} onChange={(e) => setForm({ ...form, organization: e.target.value })} className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
                <div className="grid grid-cols-2 gap-3">
                  <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className="px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary">
                    {["Individual", "Institution"].map((t) => <option key={t}>{t}</option>)}
                  </select>
                  <select value={form.license_tier} onChange={(e) => setForm({ ...form, license_tier: e.target.value })} className="px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary">
                    {["Standard", "Professional", "Enterprise"].map((t) => <option key={t}>{t}</option>)}
                  </select>
                </div>
              </div>
              <DialogFooter>
                <button data-testid="customer-save" onClick={save} className="bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90">Add Customer</button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {customers.length === 0 ? (
        <EmptyState icon={Users} title="No customers" description="Add your first customer to start licensing." />
      ) : (
        <div className="bg-card border rounded-md overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40 text-left">
                <th className="px-4 py-3 overline text-muted-foreground">Name</th>
                <th className="px-4 py-3 overline text-muted-foreground hidden md:table-cell">Organization</th>
                <th className="px-4 py-3 overline text-muted-foreground">Type</th>
                <th className="px-4 py-3 overline text-muted-foreground">License</th>
                <th className="px-4 py-3 overline text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.id} className="border-b last:border-0 hover:bg-muted/40 transition-colors">
                  <td className="px-4 py-3 font-medium">{c.name}<div className="text-xs text-muted-foreground">{c.email}</div></td>
                  <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">{c.organization || "—"}</td>
                  <td className="px-4 py-3">{c.type}</td>
                  <td className="px-4 py-3">{c.license_tier}</td>
                  <td className="px-4 py-3"><StatusBadge status={c.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
