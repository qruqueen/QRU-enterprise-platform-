import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Loader2, Download, ShieldCheck, XCircle, LifeBuoy } from "lucide-react";
import { publicApi } from "./publicApi";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

export default function QRUBundleAccess() {
  const { token } = useParams();
  const [state, setState] = useState("checking"); // checking | ready | expired | invalid
  const [data, setData] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const { data } = await publicApi.get(`/bundle-access/${token}`);
        if (!alive) return;
        setData(data); setState("ready");
      } catch (e) {
        if (!alive) return;
        setState(e?.response?.status === 410 ? "expired" : "invalid");
      }
    })();
    return () => { alive = false; };
  }, [token]);

  return (
    <div className="max-w-2xl mx-auto px-6 py-24 text-center" data-testid="qru-bundle-access">
      {state === "checking" && (
        <div data-testid="bundle-access-checking">
          <Loader2 className="w-8 h-8 animate-spin text-[#C5A059] mx-auto" />
          <p className="qru-serif text-2xl mt-6" style={{ color: "#1C1C1A" }}>Verifying your secure link…</p>
        </div>
      )}

      {state === "ready" && (
        <div data-testid="bundle-access-ready">
          <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
            <ShieldCheck className="w-4 h-4" /><span className="text-xs uppercase tracking-[0.2em]">QRU Press™ · Secure Access</span>
          </div>
          <h1 className="qru-serif text-4xl font-semibold" style={{ color: "#1C1C1A" }}>{data?.bundle_title}</h1>
          <p className="text-sm mt-2" style={{ color: "#575754" }}>
            Reference {data?.order_ref} · {data?.items?.length} items · up to {data?.download_max} downloads each
          </p>
          <div className="mt-8 space-y-3 text-left" data-testid="bundle-access-items">
            {(data?.items || []).map((it) => (
              <div key={it.id} className="flex items-center gap-4 rounded-lg border border-[#E5E5E0] p-3 bg-white" data-testid={`bundle-dl-${it.id}`}>
                <img src={`${BACKEND}${it.cover_thumb}`} alt={it.title} className="w-12 h-16 object-cover rounded border border-[#E5E5E0]" />
                <div className="flex-1">
                  <p className="qru-serif font-semibold leading-snug" style={{ color: "#1C1C1A" }}>{it.title}</p>
                  <p className="text-xs" style={{ color: "#575754" }}>{it.author}</p>
                </div>
                <a href={`${BACKEND}${it.download_url}`} data-testid={`bundle-dl-btn-${it.id}`}
                  style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
                  className="inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-opacity hover:opacity-90">
                  <Download className="w-4 h-4" /> EPUB
                </a>
              </div>
            ))}
          </div>
          <p className="mt-6 text-xs" style={{ color: "#8A8A85" }}>
            This secure link expires {data?.expires_at ? new Date(data.expires_at).toLocaleString() : "soon"}.
          </p>
          <div className="mt-8"><Link to="/bundles" className="text-sm text-[#C5A059] hover:underline">Browse more bundles</Link></div>
        </div>
      )}

      {(state === "expired" || state === "invalid") && (
        <div data-testid="bundle-access-failed">
          <XCircle className="w-12 h-12 text-[#575754] mx-auto" />
          <h1 className="qru-serif text-3xl font-semibold mt-6" style={{ color: "#1C1C1A" }}>
            {state === "expired" ? "This access link has expired." : "This access link is invalid."}
          </h1>
          <p className="text-sm mt-3 max-w-md mx-auto" style={{ color: "#575754" }}>
            Your purchase is safe. Contact QRU Press™ with your reference and we'll send a fresh secure link — no additional charge.
          </p>
          <a href="mailto:support@qru-online.com" style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
            className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 text-sm font-medium mt-8 transition-opacity hover:opacity-90">
            <LifeBuoy className="w-4 h-4" /> Contact support
          </a>
        </div>
      )}
    </div>
  );
}
