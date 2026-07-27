import { useState } from "react";
import { toast } from "sonner";
import { Loader2, Mail, Check } from "lucide-react";
import { publicApi } from "./publicApi";

// Storefront email capture — wired to the QRU newsletter (Resend welcome email).
export default function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setBusy(true);
    try {
      const { data } = await publicApi.post("/subscribe", { email: email.trim() });
      setDone(true);
      toast.success(data.message || "You're on the list.");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not subscribe. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="bg-[#0A1128] text-[#FDFBF7]" data-testid="newsletter-section">
      <div className="max-w-4xl mx-auto px-6 md:px-10 py-20 md:py-24 text-center">
        <div className="inline-flex items-center gap-2 text-[#D4AF37] mb-5">
          <Mail className="w-4 h-4" />
          <span className="text-xs uppercase tracking-[0.25em]">The QRU Reading List</span>
        </div>
        <h2 className="qru-serif text-3xl md:text-4xl font-semibold tracking-tight leading-tight">
          Be first to know when a new title is released.
        </h2>
        <p className="text-[#9BA3B5] mt-4 max-w-xl mx-auto leading-relaxed text-sm">
          Occasional letters from QRU Press™ — new books, no noise. Unsubscribe anytime.
        </p>

        {done ? (
          <div className="mt-8 inline-flex items-center gap-2 rounded-full bg-[#D4AF37]/15 border border-[#D4AF37]/40 px-6 py-3 text-sm text-[#D4AF37]" data-testid="newsletter-success">
            <Check className="w-4 h-4" /> You're on the list — thank you.
          </div>
        ) : (
          <form onSubmit={submit} className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 max-w-lg mx-auto" data-testid="newsletter-form">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              data-testid="newsletter-email-input"
              className="w-full sm:flex-1 rounded-full bg-[#12193200] border border-[#2A3654] px-6 py-3.5 text-sm text-[#FDFBF7] placeholder:text-[#5C6784] outline-none focus:border-[#D4AF37] transition-colors"
            />
            <button
              type="submit"
              disabled={busy}
              data-testid="newsletter-submit-btn"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-full bg-[#D4AF37] text-[#0A1128] px-7 py-3.5 text-sm font-medium transition-opacity hover:opacity-90 disabled:opacity-60 whitespace-nowrap">
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {busy ? "Subscribing…" : "Subscribe"}
            </button>
          </form>
        )}
      </div>
    </section>
  );
}
