import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { ShieldAlert, X, Loader2 } from "lucide-react";

export default function FounderSecurityBanner() {
  const [status, setStatus] = useState(null);
  const [open, setOpen] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [cur, setCur] = useState("");
  const [next, setNext] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get("/auth/setup-status").then((r) => setStatus(r.data)).catch(() => {});
  }, []);

  if (!status?.using_temporary_password || dismissed) return null;

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/auth/change-password", { current_password: cur, new_password: next });
      toast.success("Permanent password set. Use it next time you sign in.");
      setOpen(false); setDismissed(true);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  return (
    <div className="bg-gold/15 border border-gold/40 rounded-sm p-3 mb-6" data-testid="founder-security-banner">
      <div className="flex items-center gap-3">
        <ShieldAlert className="w-4 h-4 text-gold shrink-0" />
        <p className="text-sm flex-1">
          You're signed in with a <strong>temporary Founder password</strong>. Set your own permanent password to secure your account.
        </p>
        <button data-testid="set-password-toggle" onClick={() => setOpen((o) => !o)}
          className="text-xs px-3 py-1.5 rounded-sm bg-navy text-white font-medium">
          {open ? "Close" : "Set Permanent Password"}
        </button>
        <button onClick={() => setDismissed(true)} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
      </div>
      {open && (
        <form onSubmit={save} className="mt-3 flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs text-muted-foreground">Current (temporary) password</label>
            <input data-testid="cur-password" type="password" value={cur} onChange={(e) => setCur(e.target.value)} required
              placeholder="QruFounder2026!"
              className="mt-1 block px-3 py-2 rounded-sm border bg-background text-sm" />
            <button type="button" onClick={() => setCur("QruFounder2026!")}
              className="text-[11px] text-primary mt-1 underline">Use temporary password</button>
          </div>
          <div>
            <label className="text-xs text-muted-foreground">New password (≥10 chars, letters + numbers)</label>
            <input data-testid="new-password" type="password" value={next} onChange={(e) => setNext(e.target.value)} required
              className="mt-1 block px-3 py-2 rounded-sm border bg-background text-sm" />
          </div>
          <button data-testid="save-password-btn" type="submit" disabled={saving}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-sm text-sm font-medium disabled:opacity-60">
            {saving && <Loader2 className="w-4 h-4 animate-spin" />} Save Password
          </button>
        </form>
      )}
    </div>
  );
}
