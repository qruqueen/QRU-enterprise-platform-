import { ShieldCheck } from "lucide-react";

function Section({ title, children }) {
  return (
    <section className="mt-10">
      <h2 className="qru-serif text-2xl font-semibold" style={{ color: "#1C1C1A" }}>{title}</h2>
      <div className="mt-3 leading-relaxed" style={{ color: "#3A3A37" }}>{children}</div>
    </section>
  );
}

export default function QRUTerms() {
  return (
    <div className="max-w-3xl mx-auto px-6 md:px-10 py-16 md:py-24" data-testid="qru-terms">
      <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
        <ShieldCheck className="w-4 h-4" />
        <span className="text-xs uppercase tracking-[0.2em]">QRU Press™</span>
      </div>
      <h1 className="qru-serif text-4xl md:text-5xl font-semibold tracking-tight" style={{ color: "#1C1C1A" }}>
        Terms &amp; Conditions
      </h1>
      <p className="mt-4 leading-relaxed" style={{ color: "#575754" }}>
        These terms govern your use of QRU Online. By browsing or purchasing, you agree to them.
      </p>

      <Section title="Who we are">
        QRU Online is operated by <span style={{ color: "#1C1C1A" }}>Ascend Development Group LLC</span>{" "}
        ("QRU", "we", "us"), publishing under the imprint QRU Press™.
      </Section>

      <Section title="What we sell">
        QRU Online sells digital educational products — primarily ebooks delivered as downloadable
        EPUB files. Prices are shown in US dollars and set by QRU. We may add, change, or remove
        titles at any time.
      </Section>

      <Section title="Your purchase &amp; license">
        When you buy an ebook, we grant you a personal, non-transferable license to read it for your
        own use. You may not resell, redistribute, publicly post, or share the file, or remove any
        copyright or attribution. All intellectual property in our titles, brand, and site remains
        owned by Ascend Development Group LLC / QRU Press™.
      </Section>

      <Section title="Payment &amp; delivery">
        Payments are processed securely by Stripe; QRU never receives your card number. On successful
        payment you receive a download link that is valid for 72 hours and permits up to 5 downloads.
      </Section>

      <Section title="Refunds">
        We offer a 14-day satisfaction guarantee. See our{" "}
        <a href="/refunds" className="text-[#C5A059] hover:underline">Refund Policy</a>.
      </Section>

      <Section title="Acceptable use">
        You agree not to misuse the site, attempt to breach its security, or access content you have
        not purchased. We may suspend access for abuse of download links or fraudulent activity.
      </Section>

      <Section title="Disclaimers &amp; liability">
        Our products are provided for educational purposes "as is," without warranties of any kind.
        To the fullest extent permitted by law, Ascend Development Group LLC is not liable for
        indirect or consequential damages arising from use of the site or products.
      </Section>

      <Section title="Governing law">
        These terms are governed by the laws of [State/Country — to be confirmed by QRU]. Disputes
        will be handled in the courts of that jurisdiction.
      </Section>

      <Section title="Contact">
        Questions about these terms:{" "}
        <a href="mailto:support@qru-online.com" className="text-[#C5A059] hover:underline" data-testid="terms-contact">support@qru-online.com</a>.
      </Section>

      <p className="mt-12 text-xs" style={{ color: "#8A8A85" }}>
        These terms may be updated as the service grows; the current version always appears here.
      </p>
    </div>
  );
}
