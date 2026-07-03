import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { Library, Sparkles, Loader2, CheckCircle2, Layers } from "lucide-react";

export default function TopicRegistry() {
  const [stats, setStats] = useState(null);
  const [topics, setTopics] = useState([]);
  const [domain, setDomain] = useState("Health");
  const [count, setCount] = useState(100);
  const [generating, setGenerating] = useState(false);
  const [proposal, setProposal] = useState(null);
  const [importing, setImporting] = useState(false);
  const [filter, setFilter] = useState("");

  const load = async () => {
    const [s, t] = await Promise.all([
      api.get("/topic-registry/stats"),
      api.get("/topic-registry", { params: filter ? { division: filter } : {} }),
    ]);
    setStats(s.data);
    setTopics(t.data);
  };
  useEffect(() => { load(); }, [filter]);

  const generate = async () => {
    setGenerating(true); setProposal(null);
    try {
      const { data } = await api.post("/topic-registry/generate", { domain, count: Number(count) });
      setProposal(data);
      toast.success(`Generated ${data.count} proposed topics for review`);
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setGenerating(false); }
  };

  const importProposal = async () => {
    if (!proposal) return;
    setImporting(true);
    try {
      const { data } = await api.post("/topic-registry/bulk-import", {
        college: proposal.college, division: proposal.division,
        topics: proposal.topics, create_orders: true,
      });
      toast.success(`Seeded ${data.topics_created} topics + ${data.orders_created} manufacturing orders`);
      setProposal(null);
      load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setImporting(false); }
  };

  return (
    <div className="space-y-8" data-testid="topic-registry-page">
      <div>
        <p className="overline text-primary mb-1">Phase 2 · Governed Knowledge</p>
        <h1 className="font-heading text-3xl font-bold tracking-tight">QRU Topic Registry™</h1>
        <p className="text-muted-foreground text-sm mt-1">The authoritative source of every topic the factory manufactures.</p>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            ["Total Topics", stats.total],
            ["Queued", stats.by_status?.Queued || 0],
            ["Manufactured", stats.by_status?.Manufactured || 0],
            ["Verified", stats.verified],
            ["Treasure Certified", stats.certified],
          ].map(([label, val]) => (
            <div key={label} className="bg-card border rounded-sm p-4" data-testid={`registry-stat-${label}`}>
              <p className="text-2xl font-heading font-bold">{val}</p>
              <p className="text-xs text-muted-foreground mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Generate & Seed */}
      <div className="bg-card border rounded-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-gold" />
          <h2 className="font-heading font-semibold">Generate & Seed Colleges (Phase 4)</h2>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs text-muted-foreground">Domain</label>
            <select data-testid="registry-domain" value={domain} onChange={(e) => setDomain(e.target.value)}
              className="mt-1 block px-3 py-2 rounded-sm border bg-background text-sm">
              <option value="Health">Health University</option>
              <option value="Faith">College of Faith</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">Topics</label>
            <input data-testid="registry-count" type="number" value={count} min={10} max={120}
              onChange={(e) => setCount(e.target.value)}
              className="mt-1 block w-24 px-3 py-2 rounded-sm border bg-background text-sm" />
          </div>
          <button data-testid="registry-generate-btn" onClick={generate} disabled={generating}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium disabled:opacity-60">
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Generate Topic List
          </button>
        </div>

        {proposal && (
          <div className="mt-5 border rounded-sm" data-testid="registry-proposal">
            <div className="flex items-center justify-between p-3 bg-muted border-b">
              <p className="text-sm font-medium">{proposal.count} proposed topics · {proposal.college}</p>
              <button data-testid="registry-import-btn" onClick={importProposal} disabled={importing}
                className="flex items-center gap-2 bg-gold text-navy px-3 py-1.5 rounded-sm text-xs font-semibold disabled:opacity-60">
                {importing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                Approve & Seed to Registry
              </button>
            </div>
            <div className="max-h-64 overflow-y-auto divide-y">
              {proposal.topics.map((t, i) => (
                <div key={i} className="flex items-center justify-between px-3 py-2 text-sm">
                  <span>{t.topic_name}</span>
                  <span className="text-xs text-muted-foreground">{t.department} · P{t.priority_score}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Registry table */}
      <div className="bg-card border rounded-sm">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2"><Library className="w-4 h-4 text-primary" />
            <h2 className="font-heading font-semibold">Registry</h2></div>
          <select data-testid="registry-filter" value={filter} onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 rounded-sm border bg-background text-xs">
            <option value="">All divisions</option>
            <option value="Health">Health</option>
            <option value="Faith">Faith</option>
          </select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted text-xs text-muted-foreground">
              <tr>
                <th className="text-left px-4 py-2">Topic ID</th>
                <th className="text-left px-4 py-2">Topic</th>
                <th className="text-left px-4 py-2">Department</th>
                <th className="text-left px-4 py-2">Manufacturing</th>
                <th className="text-left px-4 py-2">Verification</th>
                <th className="text-left px-4 py-2">Treasure</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {topics.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  <Layers className="w-6 h-6 mx-auto mb-2 opacity-40" />No topics yet. Generate and seed a college above.
                </td></tr>
              )}
              {topics.map((t) => (
                <tr key={t.id} data-testid={`registry-row-${t.topic_id}`}>
                  <td className="px-4 py-2 font-mono text-xs">{t.topic_id}</td>
                  <td className="px-4 py-2">{t.topic_name}</td>
                  <td className="px-4 py-2 text-muted-foreground">{t.department}</td>
                  <td className="px-4 py-2"><Badge>{t.manufacturing_status}</Badge></td>
                  <td className="px-4 py-2"><Badge>{t.verification_status}</Badge></td>
                  <td className="px-4 py-2"><Badge>{t.treasure_standard_status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Badge({ children }) {
  const c = String(children);
  const tone = c.includes("Manufactured") || c.includes("Verified") || c.includes("Certified")
    ? "bg-emerald-100 text-emerald-700"
    : c.includes("Queued") || c.includes("Progress") ? "bg-amber-100 text-amber-700"
    : "bg-muted text-muted-foreground";
  return <span className={`text-[11px] px-2 py-0.5 rounded-full ${tone}`}>{c}</span>;
}
