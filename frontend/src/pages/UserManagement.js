import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { PageHeader } from "@/components/shared";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { formatApiError } from "@/lib/api";
import { UserCog, Plus, Trash2, ShieldAlert } from "lucide-react";

export default function UserManagement() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "Researcher" });
  const [forbidden, setForbidden] = useState(false);

  const load = () => api.get("/users").then((r) => setUsers(r.data)).catch((e) => { if (e.response?.status === 403) setForbidden(true); });
  useEffect(() => { load(); api.get("/users/roles").then((r) => setRoles(r.data.roles)).catch(() => {}); }, []);

  const save = async () => {
    if (!form.name || !form.email || !form.password) return toast.error("All fields required");
    try {
      await api.post("/users", form);
      toast.success("User created");
      setOpen(false);
      setForm({ name: "", email: "", password: "", role: "Researcher" });
      load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  const del = async (id) => {
    try { await api.delete(`/users/${id}`); toast.success("User removed"); load(); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  if (forbidden) {
    return (
      <div>
        <PageHeader overline="Administration" title="User Management" />
        <div className="bg-card border rounded-md p-10 flex flex-col items-center text-center">
          <ShieldAlert className="w-10 h-10 text-warning mb-3" />
          <p className="font-heading font-semibold">Restricted</p>
          <p className="text-sm text-muted-foreground">User management requires Administrator or Executive access.</p>
        </div>
      </div>
    );
  }

  const isAdmin = user?.role === "Administrator";

  return (
    <div>
      <PageHeader
        overline="Administration"
        title="User Management"
        description="Manage human team members and their role-based permissions across the enterprise."
        actions={isAdmin && (
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <button data-testid="user-new-btn" className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90 transition-colors">
                <Plus className="w-4 h-4" /> New User
              </button>
            </DialogTrigger>
            <DialogContent className="rounded-md">
              <DialogHeader><DialogTitle className="font-heading">New User</DialogTitle></DialogHeader>
              <div className="space-y-3 py-2">
                <input data-testid="user-name" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
                <input data-testid="user-email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
                <input data-testid="user-password" type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="w-full px-3 py-2 rounded-sm border outline-none focus:border-primary" />
                <select data-testid="user-role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="w-full px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary">
                  {roles.map((r) => <option key={r}>{r}</option>)}
                </select>
              </div>
              <DialogFooter>
                <button data-testid="user-save" onClick={save} className="bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium hover:bg-primary/90">Create User</button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      />

      <div className="bg-card border rounded-md overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/40 text-left">
              <th className="px-4 py-3 overline text-muted-foreground">Name</th>
              <th className="px-4 py-3 overline text-muted-foreground hidden sm:table-cell">Email</th>
              <th className="px-4 py-3 overline text-muted-foreground">Role</th>
              {isAdmin && <th className="px-4 py-3 overline text-muted-foreground text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} data-testid={`user-row-${u.id}`} className="border-b last:border-0 hover:bg-muted/40 transition-colors">
                <td className="px-4 py-3 font-medium">{u.name}</td>
                <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">{u.email}</td>
                <td className="px-4 py-3"><span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-sm font-medium">{u.role}</span></td>
                {isAdmin && (
                  <td className="px-4 py-3 text-right">
                    {u.role !== "Administrator" && (
                      <button data-testid={`user-delete-${u.id}`} onClick={() => del(u.id)} className="text-muted-foreground hover:text-destructive p-1">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
