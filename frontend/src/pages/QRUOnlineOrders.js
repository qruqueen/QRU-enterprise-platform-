import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import { Loader2, Mail, RefreshCw, CheckCircle2, AlertTriangle, MinusCircle, ShoppingBag } from "lucide-react";

const EMAIL_BADGE = {
  "sent-to-provider": { label: "Sent", cls: "bg-emerald-100 text-emerald-700", Icon: CheckCircle2 },
  failed: { label: "Failed", cls: "bg-red-100 text-red-700", Icon: AlertTriangle },
  skipped: { label: "Skipped", cls: "bg-amber-100 text-amber-700", Icon: MinusCircle },
};

function EmailBadge({ status }) {
  if (!status) return <span className="text-xs text-muted-foreground">—</span>;
  const b = EMAIL_BADGE[status] || { label: status, cls: "bg-muted text-foreground", Icon: Mail };
  const Icon = b.Icon;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${b.cls}`}>
      <Icon className="w-3 h-3" /> {b.label}
    </span>
  );
}

export default function QRUOnlineOrders() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(null);

  const load = () => api.get("/public/orders").then((r) => setData(r.data)).catch(() => setData(false));
  useEffect(() => { load(); }, []);

  const resend = async (sid) => {
    setBusy(sid);
    try {
      const { data: res } = await api.post(`/public/orders/${sid}/resend-confirmation`);
      const st = res?.confirmation_email?.status;
      if (st === "sent-to-provider") toast.success("Confirmation email re-sent to the customer.");
      else if (st === "skipped") toast.warning("Email provider not configured — nothing sent.");
      else toast.error(`Resend failed: ${res?.confirmation_email?.error || "unknown error"}`);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not resend confirmation.");
    }
    setBusy(null);
  };

  if (data === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>;
  if (data === false) return <div className="p-8 text-sm text-muted-foreground">Could not load QRU Online orders.</div>;

  const orders = data.orders || [];

  return (
    <div className="space-y-6" data-testid="qru-online-orders">
      <PageHeader
        overline="QRU Online™ · Fulfillment"
        title="QRU Online Orders"
        subtitle="Every real storefront purchase and its delivery email. Resend a customer's confirmation and a fresh secure link in one tap — no re-charge."
      />

      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="inline-flex items-center gap-1.5 rounded-lg border bg-card px-3 py-1.5" data-testid="orders-total">
          <ShoppingBag className="w-4 h-4 text-royal" /> {data.total} orders · {data.paid} paid
        </span>
        <span className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 ${data.provider_configured ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`} data-testid="orders-provider-status">
          <Mail className="w-4 h-4" /> {data.provider_configured ? "Email provider connected" : "Email provider NOT configured"}
        </span>
        <button onClick={load} data-testid="orders-refresh-btn" className="inline-flex items-center gap-1.5 rounded-lg border bg-card px-3 py-1.5 hover:bg-muted">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      <div className="rounded-xl border bg-card overflow-x-auto">
        <table className="w-full text-sm" data-testid="orders-table">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-muted-foreground border-b">
              <th className="px-4 py-3">Order</th>
              <th className="px-4 py-3">Amount</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Downloads</th>
              <th className="px-4 py-3">Delivery Email</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-10 text-center text-muted-foreground">No orders yet.</td></tr>
            )}
            {orders.map((o) => {
              const paid = o.payment_status === "paid";
              return (
                <tr key={o.session_id} className="border-b last:border-0 hover:bg-muted/30" data-testid={`order-row-${o.order_ref || o.session_id}`}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-foreground">{o.book_title || "—"}</div>
                    <div className="text-[11px] text-muted-foreground">{o.order_ref || o.session_id?.slice(0, 16)}</div>
                  </td>
                  <td className="px-4 py-3">${Number(o.amount || 0).toFixed(2)} {(o.currency || "usd").toUpperCase()}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${paid ? "bg-emerald-100 text-emerald-700" : "bg-muted text-muted-foreground"}`}>
                      {o.payment_status || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{o.customer_email || "—"}</td>
                  <td className="px-4 py-3 text-muted-foreground">{paid ? `${o.download_count}/${o.download_max}` : "—"}</td>
                  <td className="px-4 py-3">
                    <EmailBadge status={o.email_status} />
                    {o.email_attempts > 1 && <span className="ml-1 text-[10px] text-muted-foreground">×{o.email_attempts}</span>}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {paid ? (
                      <button
                        onClick={() => resend(o.session_id)}
                        disabled={busy === o.session_id}
                        data-testid={`resend-btn-${o.order_ref || o.session_id}`}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-navy text-white px-3 py-1.5 text-xs font-medium hover:opacity-90 disabled:opacity-50"
                      >
                        {busy === o.session_id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Mail className="w-3.5 h-3.5" />}
                        Resend
                      </button>
                    ) : <span className="text-xs text-muted-foreground">—</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
