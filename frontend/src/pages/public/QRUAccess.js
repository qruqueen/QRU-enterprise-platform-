import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CheckCircle2, Download, Loader2, ShieldCheck, XCircle, LifeBuoy } from "lucide-react";
import { publicApi } from "./publicApi";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

export default function QRUAccess() {
  const { token } = useParams();
  const [state, setState] = useState("checking"); // checking | ready | expired | invalid
  const [order, setOrder] = useState(null);
  const [support, setSupport] = useState("support@qru-online.com");

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const { data } = await publicApi.get(`/order/${token}`);
        if (!alive) return;
        setOrder(data);
        setSupport(data.support_email || support);
        setState("ready");
      } catch (e) {
        if (!alive) return;
        const code = e?.response?.status;
        if (code === 410) setState("expired");
        else setState("invalid");
        const em = e?.response?.data?.support_email;
        if (em) setSupport(em);
      }
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="max-w-2xl mx-auto px-6 py-24 text-center" data-testid="qru-access">
      {state === "checking" && (
        <div data-testid="access-checking">
          <Loader2 className="w-8 h-8 animate-spin text-[#C5A059] mx-auto" />
          <p className="qru-serif text-2xl mt-6" style={{ color: "#1C1C1A" }}>Verifying your secure link…</p>
        </div>
      )}

      {state === "ready" && (
        <div data-testid="access-ready">
          <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-xs uppercase tracking-[0.2em]">QRU Press™ · Secure Access</span>
          </div>
          <CheckCircle2 className="w-14 h-14 text-emerald-600 mx-auto" />
          <h1 className="qru-serif text-4xl font-semibold mt-6" style={{ color: "#1C1C1A" }}>
            Your book is ready.
          </h1>
          <p className="text-lg mt-3" style={{ color: "#3A3A37" }}>
            <span style={{ color: "#1C1C1A", fontWeight: 500 }}>{order?.book_title}</span>
          </p>
          <p className="text-sm mt-2" style={{ color: "#575754" }} data-testid="access-ref">
            Reference {order?.order_ref} · {order?.downloads_remaining} of {order?.download_max} downloads remaining
          </p>
          <a href={`${BACKEND}/api/public/order/${token}/download`} data-testid="access-download-btn"
            style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
            className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 text-sm font-medium mt-8 transition-opacity hover:opacity-90">
            <Download className="w-4 h-4" /> Download EPUB
          </a>
          <p className="mt-6 text-xs" style={{ color: "#8A8A85" }}>
            This secure link expires {order?.expires_at ? new Date(order.expires_at).toLocaleString() : "soon"}.
          </p>
          <div className="mt-8">
            <Link to="/catalog" className="text-sm text-[#C5A059] hover:underline">Continue browsing the catalog</Link>
          </div>
        </div>
      )}

      {(state === "expired" || state === "invalid") && (
        <div data-testid="access-failed">
          <XCircle className="w-12 h-12 text-[#575754] mx-auto" />
          <h1 className="qru-serif text-3xl font-semibold mt-6" style={{ color: "#1C1C1A" }}>
            {state === "expired" ? "This access link has expired." : "This access link is invalid."}
          </h1>
          <p className="text-sm mt-3 max-w-md mx-auto" style={{ color: "#575754" }} data-testid="access-recovery">
            Your purchase is safe. To restore access, contact QRU Press™ with your purchase
            reference and we'll send you a fresh secure link — no additional charge.
          </p>
          <a href={`mailto:${support}`} data-testid="access-support-link"
            style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
            className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 text-sm font-medium mt-8 transition-opacity hover:opacity-90">
            <LifeBuoy className="w-4 h-4" /> Contact {support}
          </a>
          <div className="mt-8">
            <Link to="/catalog" className="text-sm text-[#C5A059] hover:underline">Back to Catalog</Link>
          </div>
        </div>
      )}
    </div>
  );
}
