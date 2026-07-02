import { useEffect, useState } from "react";
import api from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/shared";
import { Bell, CheckCircle2, AlertTriangle, Info } from "lucide-react";

const ICONS = { success: CheckCircle2, warning: AlertTriangle, info: Info };
const COLORS = { success: "text-success", warning: "text-warning", info: "text-primary" };

export default function Notifications() {
  const [notifs, setNotifs] = useState([]);
  const load = () => api.get("/notifications").then((r) => setNotifs(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const markRead = async (id) => {
    await api.patch(`/notifications/${id}/read`);
    load();
  };

  return (
    <div>
      <PageHeader overline="Notifications" title="Enterprise Signals" description="Workflow events, approvals awaiting action, and continuous improvement signals." />
      {notifs.length === 0 ? (
        <EmptyState icon={Bell} title="All clear" description="No notifications right now." />
      ) : (
        <div className="space-y-2">
          {notifs.map((n) => {
            const Icon = ICONS[n.level] || Info;
            return (
              <div key={n.id} data-testid={`notif-${n.id}`} className={`bg-card border rounded-md p-4 flex items-start gap-3 ${n.read ? "opacity-60" : ""}`}>
                <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${COLORS[n.level]}`} />
                <p className="text-sm flex-1">{n.message}</p>
                {!n.read && (
                  <button data-testid={`notif-read-${n.id}`} onClick={() => markRead(n.id)} className="text-xs text-primary font-medium hover:underline shrink-0">
                    Mark read
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
