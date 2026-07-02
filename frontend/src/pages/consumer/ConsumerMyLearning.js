import { useEffect, useState } from "react";
import { Loader2, GraduationCap } from "lucide-react";
import api from "@/lib/api";
import { ProductCard, toggleFavorite } from "@/components/consumer-shared";

export default function ConsumerMyLearning() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/consumer/my-learning").then((r) => setItems(r.data.items)).finally(() => setLoading(false));
  }, []);

  const onFav = async (p) => {
    await toggleFavorite(p.id);
    setItems((xs) => xs.map((x) => x.id === p.id ? { ...x, favorite: !x.favorite } : x));
  };

  const inProgress = items.filter((i) => (i.progress || 0) < 100);
  const completed = items.filter((i) => (i.progress || 0) >= 100);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <h1 className="font-heading text-3xl font-bold tracking-tight mb-1">My Learning</h1>
      <p className="text-muted-foreground mb-8">Pick up right where you left off.</p>
      {loading ? (
        <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-24 text-muted-foreground">
          <GraduationCap className="w-10 h-10 mx-auto mb-3" strokeWidth={1.5} />
          <p className="font-heading text-lg">You haven't started learning yet.</p>
          <p className="text-sm mt-1">Head to Discover to begin your first QRU lesson.</p>
        </div>
      ) : (
        <div className="space-y-10">
          {inProgress.length > 0 && (
            <div>
              <p className="overline text-primary mb-4">Continue Learning</p>
              <div data-testid="inprogress-grid" className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {inProgress.map((p) => <ProductCard key={p.id} p={p} onFav={onFav} />)}
              </div>
            </div>
          )}
          {completed.length > 0 && (
            <div>
              <p className="overline text-success mb-4">Completed</p>
              <div data-testid="completed-grid" className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {completed.map((p) => <ProductCard key={p.id} p={p} onFav={onFav} />)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
