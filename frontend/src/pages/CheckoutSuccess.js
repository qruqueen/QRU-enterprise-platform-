import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import api from "@/lib/api";
import { downloadByFid } from "@/lib/deliverable";
import { CheckCircle2, Loader2, XCircle, Download, AlertTriangle } from "lucide-react";

export default function CheckoutSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [state, setState] = useState("checking"); // checking | paid | pending | error
  const [info, setInfo] = useState(null);
  const [delivery, setDelivery] = useState(null); // {files:[...]} | null
  const [deliveryErr, setDeliveryErr] = useState(null);
  const [loadingDl, setLoadingDl] = useState(false);

  const fetchDelivery = async () => {
    setLoadingDl(true); setDeliveryErr(null);
    try {
      const { data } = await api.get(`/commerce/download/${sessionId}`);
      setDelivery(data);
    } catch (e) {
      setDeliveryErr(e.response?.data?.detail || "Your download isn't ready yet — please refresh shortly.");
    } finally { setLoadingDl(false); }
  };

  useEffect(() => {
    if (!sessionId) {
      setState("error");
      return;
    }
    let attempts = 0;
    const poll = async () => {
      attempts += 1;
      try {
        const { data } = await api.get(`/commerce/checkout/status/${sessionId}`);
        setInfo(data);
        if (data.payment_status === "paid") {
          setState("paid");
          fetchDelivery();
          return;
        }
        if (data.status === "expired") {
          setState("error");
          return;
        }
      } catch (e) {
        if (e.response?.status === 404) { setState("error"); return; }
      }
      if (attempts >= 6) {
        setState("pending");
        return;
      }
      setTimeout(poll, 2000);
    };
    poll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const BACKEND = process.env.REACT_APP_BACKEND_URL;

  return (
    <div className="max-w-lg mx-auto py-16 text-center" data-testid="checkout-success-page">
      {state === "checking" && (
        <>
          <Loader2 className="w-10 h-10 animate-spin text-gold mx-auto" />
          <p className="mt-4 text-sm text-muted-foreground" data-testid="checkout-checking">Confirming your payment…</p>
        </>
      )}
      {state === "paid" && (
        <>
          <CheckCircle2 className="w-14 h-14 text-emerald-600 mx-auto" />
          <h1 className="font-heading text-2xl font-bold text-navy mt-4" data-testid="checkout-success-message">Payment successful</h1>
          <p className="text-sm text-muted-foreground mt-2">Thank you — <b>{info?.title}</b> is ready to download.</p>

          <div className="mt-6 bg-card border rounded-md p-4 text-left" data-testid="delivery-panel">
            <p className="font-heading font-semibold text-navy mb-2 flex items-center gap-2"><Download className="w-4 h-4 text-gold" /> Your Download</p>
            {loadingDl && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="w-4 h-4 animate-spin" /> Preparing your files…</div>}
            {deliveryErr && (
              <div className="text-sm" data-testid="delivery-error">
                <p className="flex items-start gap-2 text-amber-700"><AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" /> {deliveryErr}</p>
                <button onClick={fetchDelivery} className="mt-2 text-xs border px-3 py-1.5 rounded-sm hover:border-primary" data-testid="delivery-retry">Refresh download</button>
              </div>
            )}
            {delivery?.files?.length > 0 && (
              <div className="space-y-2" data-testid="delivery-files">
                {delivery.files.map((f, i) => (
                  <button key={i} onClick={() => downloadByFid(f.download_url || f.url)}
                    data-testid={`download-file-${f.format || i}`}
                    className="w-full text-left flex items-center gap-2 border rounded-sm p-2.5 hover:bg-muted transition-colors">
                    <Download className="w-4 h-4 text-gold shrink-0" />
                    <span className="text-sm font-medium text-navy flex-1">{f.label}</span>
                    <span className="text-xs text-royal">Download</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <Link to="/store" className="inline-block mt-6 bg-navy text-white px-4 py-2 rounded-sm text-sm font-semibold">Back to Store</Link>
        </>
      )}
      {state === "pending" && (
        <>
          <Loader2 className="w-10 h-10 text-amber-500 mx-auto" />
          <h1 className="font-heading text-xl font-bold text-navy mt-4">Payment is processing</h1>
          <p className="text-sm text-muted-foreground mt-2">This is taking a moment. Your download will appear here once it clears.</p>
          <Link to="/store" className="inline-block mt-6 bg-navy text-white px-4 py-2 rounded-sm text-sm font-semibold">Back to Store</Link>
        </>
      )}
      {state === "error" && (
        <>
          <XCircle className="w-14 h-14 text-red-500 mx-auto" />
          <h1 className="font-heading text-xl font-bold text-navy mt-4">We couldn't confirm the payment</h1>
          <Link to="/store" className="inline-block mt-6 bg-navy text-white px-4 py-2 rounded-sm text-sm font-semibold">Back to Store</Link>
        </>
      )}
    </div>
  );
}
