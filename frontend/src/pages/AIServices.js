import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Link } from "react-router-dom";
import { Cpu, CheckCircle2, PlugZap, Image, Video, Mic, Music, FileText } from "lucide-react";

const CAP_ICONS = { image: Image, video: Video, animation: Video, voice: Mic, music: Music, audio: Music };

export default function AIServices() {
  const [status, setStatus] = useState(null);
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    const load = async () => {
      const [s, j] = await Promise.all([api.get("/ai-services/status"), api.get("/ai-services/jobs", { params: { limit: 40 } })]);
      setStatus(s.data); setJobs(j.data);
    };
    load();
    const iv = setInterval(load, 12000);
    return () => clearInterval(iv);
  }, []);

  if (!status) return <div className="p-8 text-sm text-muted-foreground">Loading AI Services Division™…</div>;

  return (
    <div className="space-y-8" data-testid="ai-services-page">
      <div>
        <p className="overline text-primary mb-1">AI Services Division™</p>
        <h1 className="font-heading text-3xl font-bold tracking-tight">AI Services Manager™</h1>
        <p className="text-muted-foreground text-sm mt-1">Coordinates every AI specialist automatically. The Founder never picks a tool.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[["Capabilities", status.capabilities.length], ["Jobs Run", status.jobs_total], ["Real (native)", status.jobs_real], ["Failed", status.jobs_failed]].map(([l, v]) => (
          <div key={l} className="bg-card border rounded-sm p-4"><p className="text-2xl font-heading font-bold">{v}</p><p className="text-xs text-muted-foreground mt-1">{l}</p></div>
        ))}
      </div>

      <div className="bg-card border rounded-sm">
        <div className="flex items-center gap-2 p-4 border-b"><Cpu className="w-4 h-4 text-primary" /><h2 className="font-heading font-semibold">Capability Matrix</h2></div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-border">
          {status.capabilities.map((c) => {
            const Icon = CAP_ICONS[c.capability] || FileText;
            return (
              <div key={c.capability} className="bg-card p-4" data-testid={`cap-${c.capability}`}>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-sm font-medium capitalize"><Icon className="w-4 h-4 text-muted-foreground" />{c.capability}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ${c.mode === "real" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>{c.mode}</span>
                </div>
                <p className="text-[11px] text-muted-foreground mt-2">
                  {c.connected_provider ? `via ${c.connected_provider}` : c.requires_connector ? "needs connector" : "native (Emergent)"}
                </p>
              </div>
            );
          })}
        </div>
        <div className="p-3 border-t text-xs text-muted-foreground">
          Media capabilities upgrade from <strong>simulated</strong> to <strong>real</strong> once you connect a provider in the
          <Link to="/integration-hub" className="text-primary underline ml-1"><PlugZap className="w-3 h-3 inline" /> Integration Hub</Link>.
        </div>
      </div>

      <div className="bg-card border rounded-sm">
        <div className="p-4 border-b"><h2 className="font-heading font-semibold">Production Job History</h2></div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground"><tr>
              <th className="text-left px-4 py-2">Capability</th><th className="text-left px-4 py-2">Provider</th>
              <th className="text-left px-4 py-2">Mode</th><th className="text-left px-4 py-2">Status</th>
            </tr></thead>
            <tbody className="divide-y">
              {jobs.length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">No AI production jobs yet.</td></tr>}
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td className="px-4 py-2 capitalize">{j.capability}</td>
                  <td className="px-4 py-2 text-muted-foreground text-xs">{j.provider}</td>
                  <td className="px-4 py-2"><span className={`text-[10px] px-2 py-0.5 rounded-full ${j.mode === "real" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>{j.mode}</span></td>
                  <td className="px-4 py-2">{j.status === "success" ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <span className="text-red-600 text-xs">{j.status}</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
