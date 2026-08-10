import { useState } from "react";
import { toast } from "sonner";
import { Eye, EyeOff, Loader2, ShieldCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import api, { formatApiError } from "@/lib/api";

// Mirrors backend auth.require_super_admin's exact role check — the same rule gates the
// API endpoints this component calls, so "who sees the controls" and "who the API accepts"
// can never drift apart into two different rules.
const SUPER_ADMIN_ROLES = ["Founder & CEO", "Administrator"];

/**
 * Renders nothing for anonymous visitors and ordinary customers — only a signed-in
 * Founder/Administrator sees this, on the real public storefront page they're viewing.
 * Hide/restore is non-destructive: it flips a visibility flag only, never deletes the
 * underlying book/product, its manufacturing assets, source material, or history.
 */
export default function FounderStorefrontControls({ kind, id, published, onChanged }) {
  const { user } = useAuth();
  const [busy, setBusy] = useState(false);

  if (!user || !SUPER_ADMIN_ROLES.includes(user.role)) return null;

  const toggle = async () => {
    setBusy(true);
    try {
      const path =
        kind === "book"
          ? `/book-mfg/books/${id}/${published ? "remove-from-store" : "relist-to-store"}`
          : `/public/products/${id}/${published ? "unpublish" : "publish"}`;
      await api.post(path, kind === "book" && published ? { reason: "Hidden from Founder storefront view" } : undefined);
      toast.success(published ? "Hidden from the public storefront." : "Restored to the public storefront.");
      onChanged?.();
    } catch (e) {
      toast.error(formatApiError(e?.response?.data?.detail));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      data-testid="founder-storefront-controls"
      className="mb-6 flex items-center justify-between gap-4 rounded-xl border border-dashed px-4 py-3 text-sm"
      style={{ borderColor: "#C5A059", background: "rgba(197,160,89,0.08)" }}
    >
      <div className="flex items-center gap-2" style={{ color: "#8A6A1F" }}>
        <ShieldCheck className="w-4 h-4 shrink-0" />
        <span>
          Founder view — {published ? "visible on the public storefront" : "hidden from the public storefront"}.
          Nothing is deleted either way.
        </span>
      </div>
      <button
        onClick={toggle}
        disabled={busy}
        data-testid="founder-toggle-visibility"
        className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-xs uppercase tracking-[0.1em] shrink-0 disabled:opacity-60"
        style={{ borderColor: "#C5A059", color: "#8A6A1F" }}
      >
        {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : published ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
        {published ? "Hide" : "Restore"}
      </button>
    </div>
  );
}
