import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Route, ChevronRight } from "lucide-react";
import api from "@/lib/api";

export default function ConsumerPathways() {
  const [pathways, setPathways] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/consumer/pathways").then((r) => setPathways(r.data.pathways)).finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="font-heading text-3xl font-bold tracking-tight mb-1">Learning Paths</h1>
      <p className="text-muted-foreground mb-8">Guided journeys that build understanding step by step.</p>
      {loading ? (
        <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
      ) : (
        <div className="space-y-6" data-testid="pathways-list">
          {pathways.map((path) => (
            <div key={path.name} data-testid={`pathway-${path.name}`} className="bg-card border border-border rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: "hsl(var(--royal) / 0.1)" }}>
                  <Route className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h2 className="font-heading font-bold">{path.name}</h2>
                  <p className="text-xs text-muted-foreground">{path.topic_count} topic{path.topic_count !== 1 ? "s" : ""}</p>
                </div>
              </div>
              <div className="space-y-2">
                {path.products.map((p, i) => (
                  <button key={p.id} onClick={() => navigate(`/learn/${p.id}`)} data-testid={`pathway-item-${p.id}`}
                    className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-muted transition-colors text-left">
                    <span className="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-heading font-bold" style={{ background: "hsl(var(--gold) / 0.15)", color: "hsl(var(--navy))" }}>{i + 1}</span>
                    <span className="flex-1 text-sm font-medium">{p.title}</span>
                    <span className="text-xs text-muted-foreground">{p.product_type}</span>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
