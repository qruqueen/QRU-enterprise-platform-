import { ShieldCheck } from "lucide-react";

function Section({ title, children }) {
  return (
    <section className="mt-10">
      <h2 className="qru-serif text-2xl font-semibold" style={{ color: "#1C1C1A" }}>{title}</h2>
      <div className="mt-3 leading-relaxed" style={{ color: "#3A3A37" }}>{children}</div>
    </section>
  );
}

export default function QRURefunds() {
  return (
    <div className="max-w-3xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid="qru-refunds">
      <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
        <ShieldCheck className="w-4 h-4" />
        <span className="text-xs uppercase tracking-[0.2em]">QRU Press™</span>
      </div>
      <h1 className="qru-serif text-4xl md:text-5xl font-semibold tracking-tight" style={{ color: "#1C1C1A" }}>
        Refund Policy
      </h1>
      <p className="mt-4 leading-relaxed" style={{ color: "#575754" }}>
        We stand behind every title we publish.
      </p>

      <Section title="14-day satisfaction guarantee">
        If you're not satisfied with your purchase, we'll issue a full refund within{" "}
        <span style={{ color: "#1C1C1A" }}>14 days</span> of purchase — no complicated conditions.
        Simply email us and we'll take care of it.
      </Section>

      <Section title="How to request a refund">
        Email{" "}
        <a href="mailto:support@qru-online.com" className="text-[#C5A059] hover:underline" data-testid="refunds-contact">support@qru-online.com</a>{" "}
        with the email address you used at checkout (and your order reference from the receipt if you
        have it). Refunds are returned to your original payment method via Stripe, typically within a
        few business days.
      </Section>

      <Section title="After a refund">
        Once refunded, your download link is deactivated and the ebook license ends. Please delete any
        downloaded copies.
      </Section>

      <Section title="Questions">
        We're happy to help before or after purchase — reach us any time at{" "}
        <a href="mailto:support@qru-online.com" className="text-[#C5A059] hover:underline">support@qru-online.com</a>.
      </Section>

      <p className="mt-12 text-xs" style={{ color: "#8A8A85" }}>
        QRU Online is operated by Ascend Development Group LLC (QRU Press™).
      </p>
    </div>
  );
}
