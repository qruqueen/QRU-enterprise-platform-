import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, StatusBadge } from "@/components/shared";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Target, ShieldCheck, Wrench, Power, Loader2, Factory, BookOpen, FileText, Activity } from "lucide-react";

export default function DigitalWorkforce() {
  const [emps, setEmps] = useState([]);
  const [dept, setDept] = useState(null);
  const [loadingDept, setLoadingDept] = useState(false);

  const load = () => api.get("/digital-employees").then((r) => setEmps(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const openDept = async (e) => {
    setLoadingDept(true);
    setDept({ employee: e });
    try {
      const { data } = await api.get(`/digital-employees/${e.id}/department`);
      setDept(data);
    } catch { toast.error("Failed to load department"); } finally { setLoadingDept(false); }
  };

  const toggle = async (e, ev) => {
    ev.stopPropagation();
    try { await api.patch(`/digital-employees/${e.id}/toggle`); load(); toast.success(`${e.name} ${e.status === "Active" ? "paused" : "activated"}`); }
    catch { toast.error("Failed"); }
  };

  return (
    <div>
      <PageHeader
        overline="QRU Digital Workforce™"
        title="AI Director Departments"
        description="Each AI Director runs an operational department — with live manufacturing orders, assigned knowledge records, product output, and quality metrics. AI assists; humans own truth and final approval."
      />

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {emps.map((e) => (
          <div key={e.id} data-testid={`de-card-${e.id}`} onClick={() => openDept(e)}
            className="bg-card border rounded-md p-5 hover:-translate-y-1 hover:shadow-sm transition-all cursor-pointer">
            <div className="flex items-start gap-3">
              <img src={e.avatar} alt={e.name} className="w-12 h-12 rounded-sm object-cover bg-muted" />
              <div className="flex-1 min-w-0">
                <p className="font-heading font-semibold leading-tight">{e.title}</p>
                <p className="text-xs text-muted-foreground">{e.name}</p>
              </div>
              <button data-testid={`de-toggle-${e.id}`} onClick={(ev) => toggle(e, ev)}
                className={`p-1.5 rounded-sm ${e.status === "Active" ? "text-success" : "text-muted-foreground"}`}>
                <Power className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-muted-foreground mt-3 line-clamp-2 leading-relaxed">{e.mission}</p>
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <StatusBadge status={e.status} />
              <div className="text-right"><p className="font-heading text-sm font-bold text-gold">{e.performance}%</p><p className="text-[10px] text-muted-foreground">{e.tasks_completed} tasks</p></div>
            </div>
          </div>
        ))}
      </div>

      <Dialog open={!!dept} onOpenChange={(o) => !o && setDept(null)}>
        <DialogContent className="rounded-md max-w-3xl max-h-[88vh] overflow-y-auto">
          {dept && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <img src={dept.employee.avatar} alt="" className="w-14 h-14 rounded-sm object-cover" />
                  <div>
                    <DialogTitle className="font-heading">{dept.employee.title} — Department</DialogTitle>
                    <p className="text-sm text-muted-foreground">{dept.employee.name} · {dept.employee.approval_authority} authority</p>
                  </div>
                </div>
                <DialogDescription className="sr-only">Operational department overview for this AI Director.</DialogDescription>
              </DialogHeader>

              {loadingDept ? (
                <div className="py-16 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
              ) : (
                <div className="space-y-5 py-2">
                  <div className="flex items-start gap-2 text-sm"><Target className="w-4 h-4 text-primary mt-0.5" /><p className="text-muted-foreground">{dept.employee.mission}</p></div>

                  {dept.metrics && (
                    <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                      {[["Active Orders", dept.metrics.active_orders], ["Records", dept.metrics.assigned_records], ["Products", dept.metrics.products_output], ["Performance", `${dept.metrics.performance}%`], ["Quality", `${dept.metrics.quality_score}%`]].map(([l, v]) => (
                        <div key={l} className="border rounded-sm p-3 text-center"><p className="font-heading text-lg font-bold">{v}</p><p className="text-[10px] text-muted-foreground">{l}</p></div>
                      ))}
                    </div>
                  )}

                  <div className="grid sm:grid-cols-2 gap-3 text-sm">
                    <div><p className="flex items-center gap-2 font-medium mb-1"><ShieldCheck className="w-4 h-4 text-primary" />Permissions</p>
                      <div className="flex flex-wrap gap-1.5">{dept.employee.permissions?.map((p) => <span key={p} className="text-xs bg-muted px-2 py-0.5 rounded-sm">{p}</span>)}</div></div>
                    <div><p className="flex items-center gap-2 font-medium mb-1"><Wrench className="w-4 h-4 text-primary" />Tools</p>
                      <div className="flex flex-wrap gap-1.5">{dept.employee.tools?.map((t) => <span key={t} className="text-xs bg-muted px-2 py-0.5 rounded-sm">{t}</span>)}</div></div>
                  </div>

                  <DeptList title="Current Manufacturing Orders" icon={Factory} items={dept.current_orders}
                    render={(o) => <Link key={o.id} to="/manufacturing" className="flex justify-between border rounded-sm px-3 py-2 text-sm hover:border-primary"><span>{o.mo_code} · {o.topic}</span><StatusBadge status={o.status} /></Link>} />
                  <DeptList title="Assigned Knowledge Records" icon={BookOpen} items={dept.assigned_records}
                    render={(r) => <Link key={r.id} to={`/knowledge/${r.id}`} className="flex justify-between border rounded-sm px-3 py-2 text-sm hover:border-primary"><span>{r.kr_code} · {r.title}</span><StatusBadge status={r.verification_status} /></Link>} />
                  <DeptList title="Product Output" icon={FileText} items={dept.product_output}
                    render={(p) => <Link key={p.id} to={`/products/${p.id}`} className="flex justify-between border rounded-sm px-3 py-2 text-sm hover:border-primary"><span>{p.product_code} · {p.title}</span><StatusBadge status={p.status} /></Link>} />

                  {dept.team_activity?.length > 0 && (
                    <div>
                      <p className="flex items-center gap-2 font-medium mb-2 text-sm"><Activity className="w-4 h-4 text-primary" />Team Activity</p>
                      <div className="space-y-1.5">
                        {dept.team_activity.map((a) => <p key={a.id} className="text-xs text-muted-foreground"><span className="font-medium text-foreground">{a.actor}</span> {a.action} {a.detail}</p>)}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function DeptList({ title, icon: Icon, items, render }) {
  return (
    <div>
      <p className="flex items-center gap-2 font-medium mb-2 text-sm"><Icon className="w-4 h-4 text-primary" />{title}</p>
      {(!items || items.length === 0) ? <p className="text-xs text-muted-foreground">None currently.</p>
        : <div className="space-y-1.5">{items.map(render)}</div>}
    </div>
  );
}
