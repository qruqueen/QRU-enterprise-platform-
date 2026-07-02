import { useEffect, useState } from "react";
import { Loader2, Award } from "lucide-react";
import api from "@/lib/api";

export default function ConsumerCertificates() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/consumer/certificates").then((r) => setItems(r.data.items)).finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="font-heading text-3xl font-bold tracking-tight mb-1">Certificates</h1>
      <p className="text-muted-foreground mb-8">Proof of the understanding you've earned.</p>
      {loading ? (
        <div className="flex justify-center py-24"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-24 text-muted-foreground">
          <Award className="w-10 h-10 mx-auto mb-3" strokeWidth={1.5} />
          <p className="font-heading text-lg">No certificates yet.</p>
          <p className="text-sm mt-1">Complete a lesson to earn your first QRU certificate.</p>
        </div>
      ) : (
        <div className="space-y-5" data-testid="certificates-list">
          {items.map((c) => (
            <div key={c.id} data-testid={`certificate-${c.id}`} className="rounded-2xl border-2 border-gold p-8 relative overflow-hidden" style={{ background: "linear-gradient(135deg, hsl(var(--gold) / 0.06), hsl(var(--background)))" }}>
              <div className="flex items-center gap-2 mb-4">
                <img src="/qru-shield-light.png" alt="QRU" className="w-8 h-8 object-contain" />
                <div>
                  <p className="font-heading font-bold text-sm" style={{ color: "hsl(var(--royal))" }}>QRU CERTIFICATE OF UNDERSTANDING</p>
                  <p className="text-[10px] tracking-widest text-muted-foreground">TREASURE STANDARD™</p>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">This certifies that</p>
              <p className="font-heading text-2xl font-bold mt-1">{c.learner_name}</p>
              <p className="text-xs text-muted-foreground mt-3">has completed</p>
              <p className="font-heading text-lg font-semibold" style={{ color: "hsl(var(--royal))" }}>{c.product_title}</p>
              <div className="flex items-center justify-between mt-5 pt-4 border-t border-gold/30 text-xs text-muted-foreground">
                <span>Certificate No. {c.code}</span>
                <span>{new Date(c.issued_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
