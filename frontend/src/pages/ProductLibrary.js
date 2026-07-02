import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/api";
import { PageHeader, StatusBadge, EmptyState } from "@/components/shared";
import { Library, FileText } from "lucide-react";

export default function ProductLibrary() {
  const [products, setProducts] = useState([]);
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [types, setTypes] = useState([]);
  const navigate = useNavigate();

  useEffect(() => { api.get("/products/types").then((r) => setTypes(r.data.types)).catch(() => {}); }, []);

  const load = () => {
    const params = {};
    if (type) params.product_type = type;
    if (status) params.status = status;
    api.get("/products", { params }).then((r) => setProducts(r.data)).catch(() => {});
  };
  useEffect(() => { load(); }, [type, status]);

  return (
    <div>
      <PageHeader
        overline="Product Library"
        title="Manufactured Products"
        description="Every product manufactured from verified knowledge. Nothing publishes without human approval."
      />

      <div className="flex flex-wrap gap-3 mb-5">
        <select data-testid="pl-filter-type" value={type} onChange={(e) => setType(e.target.value)}
          className="px-3 py-2 text-sm border rounded-sm bg-card outline-none focus:border-primary">
          <option value="">All types</option>
          {types.map((t) => <option key={t}>{t}</option>)}
        </select>
        <select data-testid="pl-filter-status" value={status} onChange={(e) => setStatus(e.target.value)}
          className="px-3 py-2 text-sm border rounded-sm bg-card outline-none focus:border-primary">
          <option value="">All statuses</option>
          {["Draft", "In Review", "Approved", "Published", "Archived"].map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>

      {products.length === 0 ? (
        <EmptyState icon={Library} title="No products yet" description="Manufacture your first product in the Product Manufacturing Center." />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((p) => (
            <div key={p.id} data-testid={`product-card-${p.id}`} onClick={() => navigate(`/products/${p.id}`)}
              className="bg-card border rounded-md p-5 hover:-translate-y-1 hover:shadow-sm transition-all cursor-pointer">
              <div className="flex items-start justify-between mb-3">
                <div className="w-9 h-9 rounded-sm bg-primary/10 text-primary flex items-center justify-center">
                  <FileText className="w-5 h-5" />
                </div>
                <StatusBadge status={p.status} />
              </div>
              <p className="text-xs text-primary font-medium">{p.product_type}</p>
              <p className="font-heading font-semibold leading-snug mt-1 line-clamp-2">{p.title}</p>
              <p className="text-xs text-muted-foreground mt-2">{p.family} · {p.audience}</p>
              <p className="font-mono text-[11px] text-muted-foreground mt-3">{p.product_code}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
