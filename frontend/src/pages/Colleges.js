import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { GraduationCap, Play, Loader2, BookOpen, Video, DollarSign, Users, Activity } from "lucide-react";

const STATUS_COLOR = {
  "Not Started": "bg-slate-100 text-slate-600", "Planning": "bg-sky-100 text-sky-700",
  "Verification": "bg-indigo-100 text-indigo-700", "Manufacturing": "bg-blue-100 text-blue-700",
  "Publishing": "bg-violet-100 text-violet-700", "Live": "bg-emerald-100 text-emerald-700",
  "Growing": "bg-emerald-100 text-emerald-800", "Treasure Standard™": "bg-gold/20 text-navy",
};

function healthColor(h) {
  if (h >= 85) return "bg-emerald-500";
  if (h >= 60) return "bg-gold";
  if (h >= 30) return "bg-amber-500";
  return "bg-slate-300";
}

export default function Colleges() {
  const [colleges, setColleges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/colleges").then(({ data }) => setColleges(data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const startManufacturing = async (c) => {
    setStarting(c.id);
    try {
      const { data } = await api.get(`/colleges/${c.id}/factory-defaults`);
      const topic = data.suggested_topics[0];
      const template = data.workflow_template || "Full Treasure Package™";
      navigate(`/workflows?topic=${encodeURIComponent(topic)}&template=${encodeURIComponent(template)}&college=${encodeURIComponent(c.name)}`);
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setStarting(null);
    }
  };

  if (loading) return <div className="p-8 flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Loading Colleges…</div>;

  return (
    <div className="space-y-6" data-testid="colleges-page">
      <div>
        <h1 className="font-heading text-3xl font-bold text-navy flex items-center gap-2">
          <GraduationCap className="w-7 h-7 text-gold" /> QRU Colleges
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Every College is a live manufacturing division powered by the one shared QRU Factory™.
        </p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {colleges.map((c) => (
          <div key={c.id} data-testid={`college-card-${c.id}`} className="bg-card border rounded-sm p-5 flex flex-col"
               style={{ borderTop: `3px solid ${c.color || "#F5B21A"}` }}>
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-heading font-semibold text-navy">{c.name}</h3>
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${STATUS_COLOR[c.status_badge] || STATUS_COLOR[c.status] || "bg-slate-100"}`}>{c.status_badge || c.status}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2 flex-1">{c.description}</p>

            <div className="flex items-center gap-2 mt-3">
              <Activity className="w-3.5 h-3.5 text-gold" />
              <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                <div className={`h-full ${healthColor(c.health)}`} style={{ width: `${c.health}%` }} />
              </div>
              <span className="text-xs font-medium text-navy">{c.health}%</span>
            </div>

            <div className="grid grid-cols-4 gap-1 mt-3 text-center">
              <div><BookOpen className="w-3.5 h-3.5 mx-auto text-muted-foreground" /><p className="text-xs font-semibold text-navy mt-0.5">{c.metrics.published}</p><p className="text-[9px] text-muted-foreground">Published</p></div>
              <div><Video className="w-3.5 h-3.5 mx-auto text-muted-foreground" /><p className="text-xs font-semibold text-navy mt-0.5">{c.metrics.videos}</p><p className="text-[9px] text-muted-foreground">Videos</p></div>
              <div><Users className="w-3.5 h-3.5 mx-auto text-muted-foreground" /><p className="text-xs font-semibold text-navy mt-0.5">{c.metrics.students}</p><p className="text-[9px] text-muted-foreground">Students</p></div>
              <div><DollarSign className="w-3.5 h-3.5 mx-auto text-muted-foreground" /><p className="text-xs font-semibold text-navy mt-0.5">{c.metrics.revenue_usd}</p><p className="text-[9px] text-muted-foreground">Revenue</p></div>
            </div>
            <p className="text-[10px] text-muted-foreground mt-2">Understanding Impact™: <span className="font-semibold text-navy">{c.metrics.understanding_impact}</span></p>

            <button
              data-testid={`start-manufacturing-${c.id}`}
              onClick={() => startManufacturing(c)}
              disabled={starting === c.id}
              className="mt-3 flex items-center justify-center gap-2 bg-navy text-white px-3 py-2 rounded-sm text-sm font-semibold hover:bg-navy/90 disabled:opacity-60"
            >
              {starting === c.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Start Manufacturing
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
