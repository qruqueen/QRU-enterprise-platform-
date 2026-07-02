import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/shared";
import { Search as SearchIcon, BookOpen, Factory, Library, Bot } from "lucide-react";

const GROUPS = [
  { key: "knowledge_records", label: "Knowledge Records", icon: BookOpen, to: (i) => `/knowledge/${i.id}`, title: (i) => i.title, sub: (i) => i.kr_code },
  { key: "manufacturing_orders", label: "Manufacturing Orders", icon: Factory, to: () => `/manufacturing`, title: (i) => i.topic, sub: (i) => i.mo_code },
  { key: "products", label: "Products", icon: Library, to: (i) => `/products/${i.id}`, title: (i) => i.title, sub: (i) => i.product_code },
  { key: "digital_employees", label: "Digital Workforce", icon: Bot, to: () => `/workforce`, title: (i) => i.title, sub: (i) => i.name },
];

export default function SearchResults() {
  const [params] = useSearchParams();
  const q = params.get("q") || "";
  const [results, setResults] = useState({});

  useEffect(() => {
    if (q) api.get("/search", { params: { q } }).then((r) => setResults(r.data)).catch(() => {});
  }, [q]);

  const total = GROUPS.reduce((n, g) => n + (results[g.key]?.length || 0), 0);

  return (
    <div>
      <PageHeader overline="Enterprise Search" title={`Results for "${q}"`} description={`${total} matches across the enterprise.`} />
      {total === 0 ? (
        <EmptyState icon={SearchIcon} title="No matches" description="Try a different search term." />
      ) : (
        <div className="space-y-8">
          {GROUPS.map((g) => {
            const items = results[g.key] || [];
            if (!items.length) return null;
            return (
              <div key={g.key}>
                <div className="flex items-center gap-2 mb-3">
                  <g.icon className="w-4 h-4 text-primary" />
                  <h3 className="font-heading font-semibold">{g.label} <span className="text-muted-foreground font-normal">({items.length})</span></h3>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {items.map((i) => (
                    <Link key={i.id} to={g.to(i)} className="bg-card border rounded-md p-4 hover:border-primary transition-colors">
                      <p className="font-mono text-[11px] text-muted-foreground">{g.sub(i)}</p>
                      <p className="font-medium mt-1 line-clamp-2">{g.title(i)}</p>
                    </Link>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
