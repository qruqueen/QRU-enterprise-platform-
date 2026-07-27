import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { Loader2, Star, Plus, X, ArrowUp, ArrowDown, Save, RotateCcw } from "lucide-react";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const thumb = (u) => (u ? `${BACKEND}${u}` : null);

function Cover({ book, className = "" }) {
  return (
    <div className={`shrink-0 w-10 h-14 rounded overflow-hidden bg-muted border ${className}`}>
      {book.thumb_url ? (
        <img src={thumb(book.thumb_url)} alt={book.title} className="w-full h-full object-cover" />
      ) : null}
    </div>
  );
}

export default function FeaturedTitlesManager() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [featured, setFeatured] = useState([]); // ordered book objects
  const [available, setAvailable] = useState([]); // the rest
  const [savedIds, setSavedIds] = useState([]);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/public/admin/featured");
      const books = data.books || [];
      const feat = (data.featured_ids || [])
        .map((id) => books.find((b) => b.id === id))
        .filter(Boolean);
      const featSet = new Set(feat.map((b) => b.id));
      setFeatured(feat);
      setAvailable(books.filter((b) => !featSet.has(b.id)));
      setSavedIds(data.featured_ids || []);
    } catch (e) {
      toast.error("Could not load titles.");
    }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const addFeatured = (book) => {
    setFeatured((f) => [...f, book]);
    setAvailable((a) => a.filter((b) => b.id !== book.id));
  };
  const removeFeatured = (book) => {
    setFeatured((f) => f.filter((b) => b.id !== book.id));
    setAvailable((a) => [...a, book].sort((x, y) => (x.title || "").localeCompare(y.title || "")));
  };
  const move = (idx, dir) => {
    setFeatured((f) => {
      const next = [...f];
      const j = idx + dir;
      if (j < 0 || j >= next.length) return f;
      [next[idx], next[j]] = [next[j], next[idx]];
      return next;
    });
  };

  const currentIds = featured.map((b) => b.id);
  const dirty = JSON.stringify(currentIds) !== JSON.stringify(savedIds);

  const save = async () => {
    setSaving(true);
    try {
      const { data } = await api.put("/public/admin/featured", { book_ids: currentIds });
      setSavedIds(data.featured_ids || []);
      toast.success(
        data.count === 0
          ? "Cleared — the home page will auto-feature your first titles."
          : `Saved — ${data.count} title${data.count === 1 ? "" : "s"} featured on the home page.`
      );
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not save featured titles.");
    }
    setSaving(false);
  };

  const reset = () => { load(); };

  return (
    <div className="rounded-xl border bg-card p-5" data-testid="featured-titles-manager">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <Star className="w-4 h-4 text-royal" /> Featured Titles
          </h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-xl">
            Choose which books appear in the “Featured Titles” row on the storefront home page — and the order they show in.
            Leave empty to auto-feature your first titles.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={reset}
            disabled={!dirty || saving}
            data-testid="featured-reset-btn"
            className="inline-flex items-center gap-1.5 rounded-lg border bg-card px-3 py-1.5 text-xs font-medium hover:bg-muted disabled:opacity-40"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset
          </button>
          <button
            onClick={save}
            disabled={!dirty || saving}
            data-testid="featured-save-btn"
            className="inline-flex items-center gap-1.5 rounded-lg bg-navy text-white px-4 py-1.5 text-xs font-medium hover:opacity-90 disabled:opacity-40"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            {dirty ? "Save changes" : "Saved"}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-5 h-5 animate-spin text-royal" /></div>
      ) : (
        <div className="grid md:grid-cols-2 gap-5">
          {/* Featured (ordered) */}
          <div>
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground mb-2">
              Featured on home ({featured.length})
            </p>
            <div className="space-y-2 min-h-[80px]" data-testid="featured-list">
              {featured.length === 0 && (
                <div className="text-xs text-muted-foreground border border-dashed rounded-lg p-4 text-center">
                  No titles selected — the home page will auto-feature your first titles.
                </div>
              )}
              {featured.map((b, i) => (
                <div key={b.id} className="flex items-center gap-3 rounded-lg border bg-background px-3 py-2" data-testid={`featured-item-${b.id}`}>
                  <span className="text-xs font-semibold text-muted-foreground w-4 text-center">{i + 1}</span>
                  <Cover book={b} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{b.title}</div>
                    <div className="text-[11px] text-muted-foreground truncate">{b.author}</div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => move(i, -1)} disabled={i === 0} data-testid={`featured-up-${b.id}`}
                      className="p-1 rounded hover:bg-muted disabled:opacity-30"><ArrowUp className="w-4 h-4" /></button>
                    <button onClick={() => move(i, 1)} disabled={i === featured.length - 1} data-testid={`featured-down-${b.id}`}
                      className="p-1 rounded hover:bg-muted disabled:opacity-30"><ArrowDown className="w-4 h-4" /></button>
                    <button onClick={() => removeFeatured(b)} data-testid={`featured-remove-${b.id}`}
                      className="p-1 rounded hover:bg-red-50 text-red-500"><X className="w-4 h-4" /></button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Available */}
          <div>
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground mb-2">
              Available titles ({available.length})
            </p>
            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1" data-testid="available-list">
              {available.length === 0 && (
                <div className="text-xs text-muted-foreground border border-dashed rounded-lg p-4 text-center">
                  All published titles are featured.
                </div>
              )}
              {available.map((b) => (
                <div key={b.id} className="flex items-center gap-3 rounded-lg border bg-background px-3 py-2" data-testid={`available-item-${b.id}`}>
                  <Cover book={b} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{b.title}</div>
                    <div className="text-[11px] text-muted-foreground truncate">{b.author}</div>
                  </div>
                  <button onClick={() => addFeatured(b)} data-testid={`available-add-${b.id}`}
                    className="inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-medium hover:bg-muted">
                    <Plus className="w-3.5 h-3.5" /> Feature
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
