import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, StatusBadge } from "@/components/shared";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Bot, Target, ShieldCheck, Wrench, Activity, Power } from "lucide-react";
import { toast } from "sonner";

export default function DigitalWorkforce() {
  const [emps, setEmps] = useState([]);
  const [selected, setSelected] = useState(null);
  const load = () => api.get("/digital-employees").then((r) => setEmps(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const toggle = async (e, ev) => {
    ev.stopPropagation();
    try {
      await api.patch(`/digital-employees/${e.id}/toggle`);
      load();
      toast.success(`${e.name} ${e.status === "Active" ? "paused" : "activated"}`);
    } catch { toast.error("Failed"); }
  };

  return (
    <div>
      <PageHeader
        overline="QRU Digital Workforce™"
        title="AI Digital Employees"
        description="Every Digital Employee has a mission, permissions, tools, and approval authority. AI assists — humans remain responsible for truth and final approval."
      />

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {emps.map((e) => (
          <div key={e.id} data-testid={`de-card-${e.id}`} onClick={() => setSelected(e)}
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
              <div className="text-right">
                <p className="font-heading text-sm font-bold">{e.performance}%</p>
                <p className="text-[10px] text-muted-foreground">{e.tasks_completed} tasks</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="rounded-md max-w-lg">
          {selected && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <img src={selected.avatar} alt="" className="w-14 h-14 rounded-sm object-cover" />
                  <div>
                    <DialogTitle className="font-heading">{selected.title}</DialogTitle>
                    <p className="text-sm text-muted-foreground">{selected.name} · {selected.approval_authority} authority</p>
                  </div>
                </div>
              </DialogHeader>
              <div className="space-y-4 py-2 text-sm max-h-[60vh] overflow-y-auto">
                <div><p className="flex items-center gap-2 font-medium mb-1"><Target className="w-4 h-4 text-primary" />Mission</p><p className="text-muted-foreground">{selected.mission}</p></div>
                <div><p className="flex items-center gap-2 font-medium mb-1"><Activity className="w-4 h-4 text-primary" />Responsibilities</p>
                  <ul className="list-disc pl-5 text-muted-foreground">{selected.responsibilities.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
                <div><p className="flex items-center gap-2 font-medium mb-1"><ShieldCheck className="w-4 h-4 text-primary" />Permissions</p>
                  <div className="flex flex-wrap gap-1.5">{selected.permissions.map((p) => <span key={p} className="text-xs bg-muted px-2 py-0.5 rounded-sm">{p}</span>)}</div></div>
                <div><p className="flex items-center gap-2 font-medium mb-1"><Wrench className="w-4 h-4 text-primary" />Tools</p>
                  <div className="flex flex-wrap gap-1.5">{selected.tools.map((t) => <span key={t} className="text-xs bg-muted px-2 py-0.5 rounded-sm">{t}</span>)}</div></div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
