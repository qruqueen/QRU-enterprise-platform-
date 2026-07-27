import { ShieldCheck, Lock, Download, RotateCcw } from "lucide-react";

const MARKS = [
  { icon: ShieldCheck, title: "Verified to the Treasure Standard™", body: "Every title is researched, written, and checked before release." },
  { icon: Lock, title: "Secure checkout by Stripe", body: "Payments are processed securely. We never see your card details." },
  { icon: Download, title: "Instant EPUB delivery", body: "Your book is available to download the moment payment clears." },
  { icon: RotateCcw, title: "14-day satisfaction guarantee", body: "Not satisfied? Request a full refund within 14 days." },
];

// Reassurance band for the storefront — real, honest promises only (Treasure Standard™).
export default function TrustMarks() {
  return (
    <section className="border-y border-[#E5E5E0] bg-[#F3F1EA]" data-testid="trust-marks">
      <div className="max-w-7xl mx-auto px-6 md:px-10 py-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        {MARKS.map((m) => {
          const Icon = m.icon;
          return (
            <div key={m.title} className="flex items-start gap-3">
              <span className="shrink-0 w-9 h-9 rounded-full bg-[#1C1C1A] text-[#C5A059] grid place-items-center">
                <Icon className="w-4 h-4" />
              </span>
              <div>
                <p className="qru-serif text-base font-semibold text-[#1C1C1A] leading-snug">{m.title}</p>
                <p className="text-xs text-[#575754] mt-1 leading-relaxed">{m.body}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
