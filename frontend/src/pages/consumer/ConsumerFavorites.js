import { useEffect, useState } from "react";
import { Loader2, Heart } from "lucide-react";
import api from "@/lib/api";
import { ProductCard, toggleFavorite } from "@/components/consumer-shared";

export default function ConsumerFavorites() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/consumer/favorites").then((r) => setItems(r.data.items)).finally(() => setLoading(false));
  }, []);

  const onFav = async (p) => {
    await toggleFavorite(p.id);
    setItems((xs) => xs.filter((x) => x.id !== p.id));
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <h1 className="font-heading text-3xl font-bold tracking-tight mb-1">Favorites</h1>
      <p className="text-muted-foreground mb-8">Lessons you've saved to revisit.</p>
      {loading ? (
        <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-24 text-muted-foreground">
          <Heart className="w-10 h-10 mx-auto mb-3" strokeWidth={1.5} />
          <p className="font-heading text-lg">No favorites yet.</p>
          <p className="text-sm mt-1">Tap the star on any lesson to save it here.</p>
        </div>
      ) : (
        <div data-testid="favorites-grid" className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((p) => <ProductCard key={p.id} p={{ ...p, favorite: true }} onFav={onFav} />)}
        </div>
      )}
    </div>
  );
}
