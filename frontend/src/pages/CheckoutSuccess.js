import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import api from "@/lib/api";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";

export default function CheckoutSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [state, setState] = useState("checking"); // checking | paid | pending | error
  const [info, setInfo] = useState(null);

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
          return;
        }
        if (data.status === "expired") {
          setState("error");
          return;
        }
      } catch (_) {}
      if (attempts >= 6) {
        setState("pending");
        return;
      }
      setTimeout(poll, 2000);
    };
    poll();
  }, [sessionId]);

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
          <p className="text-sm text-muted-foreground mt-2">Thank you — <b>{info?.title}</b> has been added to your library.</p>
          <Link to="/store" className="inline-block mt-6 bg-navy text-white px-4 py-2 rounded-sm text-sm font-semibold">Back to Store</Link>
        </>
      )}
      {state === "pending" && (
        <>
          <Loader2 className="w-10 h-10 text-amber-500 mx-auto" />
          <h1 className="font-heading text-xl font-bold text-navy mt-4">Payment is processing</h1>
          <p className="text-sm text-muted-foreground mt-2">This is taking a moment. Check your library shortly.</p>
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
