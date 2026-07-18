import { ShieldCheck } from "lucide-react";

const SUPPORT_EMAIL = "privacy@qru-online.com";

function Section({ title, children }) {
  return (
    <section className="mt-10">
      <h2 className="qru-serif text-2xl font-semibold" style={{ color: "#1C1C1A" }}>{title}</h2>
      <div className="mt-3 leading-relaxed" style={{ color: "#3A3A37" }}>{children}</div>
    </section>
  );
}

export default function QRUPrivacy() {
  return (
    <div className="max-w-3xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid="qru-privacy">
      <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
        <ShieldCheck className="w-4 h-4" />
        <span className="text-xs uppercase tracking-[0.2em]">QRU Press™</span>
      </div>
      <h1 className="qru-serif text-4xl md:text-5xl font-semibold tracking-tight" style={{ color: "#1C1C1A" }}>
        Privacy
      </h1>
      <p className="mt-4 leading-relaxed" style={{ color: "#575754" }}>
        We keep this simple and honest — the same standard we hold for our books.
      </p>

      <Section title="What QRU collects">
        Browsing QRU Online requires no account and no sign-in. We do not sell your data or use
        advertising trackers. When you buy an ebook, we store only an order record — the title
        purchased, the amount, the Stripe transaction reference, timestamps, and how many times
        the download link has been used. <span style={{ color: "#1C1C1A" }}>We never see or store your card number.</span>
      </Section>

      <Section title="What Stripe processes">
        Payments are handled by Stripe, our PCI-compliant payment processor. To complete your
        purchase, Stripe collects and processes your name, email, and payment/billing details.
        Stripe's handling of that information is governed by Stripe's own privacy policy.
      </Section>

      <Section title="Why we use it">
        Only to complete your purchase, deliver your ebook, provide support, and prevent fraud or
        abuse of download links. That's it.
      </Section>

      <Section title="How long we keep it">
        Order records are retained for accounting and legal obligations. Your ebook download link
        is time-limited: it expires 72 hours after purchase and permits up to five downloads.
      </Section>

      <Section title="Support &amp; deletion">
        You can request a copy of your order information, ask a question, or request deletion of
        your order record (subject to legal retention requirements) by emailing{" "}
        <a href={`mailto:${SUPPORT_EMAIL}`} className="text-[#C5A059] hover:underline" data-testid="privacy-contact">{SUPPORT_EMAIL}</a>.
      </Section>

      <p className="mt-12 text-xs" style={{ color: "#8A8A85" }}>
        This page describes current practices for QRU Online and may be updated as the service grows.
      </p>
    </div>
  );
}
