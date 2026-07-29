import { useEffect, useState, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, Download, Loader2, ShieldCheck, XCircle } from "lucide-react";
import { publicApi, assetUrl } from "./publicApi";

export default function QRUPurchaseSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const isBundle = params.get("kind") === "bundle";
  const [state, setState] = useState("checking"); // checking | paid | failed
  const [order, setOrder] = useState(null);
  const attempts = useRef(0);

  useEffect(() => {
    if (!sessionId) { setState("failed"); return; }
    let timer;
    const statusUrl = isBundle ? `/bundle-checkout/status/${sessionId}` : `/checkout/status/${sessionId}`;
    const poll = async () => {
      attempts.current += 1;
      try {
        const { data } = await publicApi.get(statusUrl);
        if (data.payment_status === "paid") { setOrder(data); setState("paid"); return; }
        if (["failed", "expired"].includes(data.payment_status)) { setState("failed"); return; }
      } catch { /* keep trying */ }
      if (attempts.current >= 12) { setState("failed"); return; }
      timer = setTimeout(poll, 2000);
    };
    poll();
    return () => clearTimeout(timer);
  }, [sessionId, isBundle]);

  return (
    <div className="max-w-2xl mx-auto px-6 py-24 text-center" data-testid="qru-purchase-success">
      {state === "checking" && (
        <div data-testid="purchase-checking">
          <Loader2 className="w-8 h-8 animate-spin text-[#C5A059] mx-auto" />
          <p className="qru-serif text-2xl mt-6" style={{ color: "#1C1C1A" }}>Confirming your purchase…</p>
          <p className="text-sm mt-2" style={{ color: "#575754" }}>One moment while Stripe confirms payment.</p>
        </div>
      )}

      {state === "paid" && (
        <div data-testid="purchase-paid">
          <div className="inline-flex items-center gap-2 text-[#C5A059] mb-4">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-xs uppercase tracking-[0.2em]">QRU Press™ · Treasure Standard™</span>
          </div>
          <CheckCircle2 className="w-14 h-14 text-emerald-600 mx-auto" />
          <h1 className="qru-serif text-4xl font-semibold mt-6" style={{ color: "#1C1C1A" }}>Thank you.</h1>
          {isBundle ? (
            <>
              <p className="text-lg mt-3" style={{ color: "#3A3A37" }}>
                Your bundle <span style={{ color: "#1C1C1A", fontWeight: 500 }}>{order?.bundle_title}</span> is ready — every item is waiting for you.
              </p>
              <Link to={`/bundle-access/${order?.access_token}`} data-testid="view-bundle-btn"
                style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
                className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 text-sm font-medium mt-8 transition-opacity hover:opacity-90">
                <Download className="w-4 h-4" /> Open my bundle
              </Link>
              <div className="mt-8"><Link to="/bundles" className="text-sm text-[#C5A059] hover:underline">Browse more bundles</Link></div>
            </>
          ) : (
            <>
              <p className="text-lg mt-3" style={{ color: "#3A3A37" }}>
                Your copy of <span style={{ color: "#1C1C1A", fontWeight: 500 }}>{order?.book_title}</span> is ready to download.
              </p>
              <a href={assetUrl(order?.download_url)} data-testid="download-ebook-btn"
                style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
                className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 text-sm font-medium mt-8 transition-opacity hover:opacity-90">
                <Download className="w-4 h-4" /> Download EPUB
              </a>
              <div className="mt-8"><Link to="/catalog" className="text-sm text-[#C5A059] hover:underline">Continue browsing the catalog</Link></div>
            </>
          )}
          <p className="mt-6 text-xs" style={{ color: "#8A8A85" }} data-testid="refund-guarantee-success">
            Not satisfied? Full refund within 14 days — just reply to your receipt.
          </p>
        </div>
      )}

      {state === "failed" && (
        <div data-testid="purchase-failed">
          <XCircle className="w-12 h-12 text-[#575754] mx-auto" />
          <h1 className="qru-serif text-3xl font-semibold mt-6" style={{ color: "#1C1C1A" }}>We couldn't confirm this purchase.</h1>
          <p className="text-sm mt-3" style={{ color: "#575754" }}>
            If you were charged, your download will still be available — please contact QRU Press™.
            Otherwise you can try again.
          </p>
          <Link to="/catalog" data-testid="back-to-catalog"
            style={{ backgroundColor: "#1C1C1A", color: "#FAFAF8" }}
            className="inline-flex items-center gap-2 rounded-full px-8 py-3.5 text-sm font-medium mt-8 transition-opacity hover:opacity-90">
            Back to Catalog
          </Link>
        </div>
      )}
    </div>
  );
}
