import { useEffect, useState } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { PageHeader } from "@/components/shared";
import {
  Loader2, RefreshCw, CheckCircle2, AlertTriangle, XCircle, Store,
  BookOpen, ShieldCheck, Mail, ShoppingCart, Sparkles,
} from "lucide-react";

const STATUS = {
  healthy: { cls: "bg-emerald-100 text-emerald-700 border-emerald-200", Icon: CheckCircle2, label: "Healthy" },
  warnings: { cls: "bg-amber-100 text-amber-700 border-amber-200", Icon: AlertTriangle, label: "Warnings" },
  attention: { cls: "bg-red-100 text-red-700 border-red-200", Icon: XCircle, label: "Needs attention" },
};

function Stat({ label, value, tone = "default" }) {
  const tones = { default: "bg-card", ok: "bg-emerald-50 text-emerald-700", warn: "bg-amber-50 text-amber-700", bad: "bg-red-50 text-red-700" };
  return (
    <div className={`rounded-lg border p-4 ${tones[tone]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-[11px] mt-1 opacity-80">{label}</div>
    </div>
  );
}

function Section({ icon: Icon, title, children }) {
  return (
    <section className="rounded-xl border bg-card p-5">
      <div className="flex items-center gap-2 mb-4">
        <Icon className="w-4 h-4 text-navy" />
        <span className="font-heading font-bold text-navy">{title}</span>
      </div>
      {children}
    </section>
  );
}

export default function StoreHealth() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    setBusy(true);
    api.get("/store/health")
      .then((r) => setData(r.data))
      .catch((e) => { setData(false); toast.error(e.response?.data?.detail || "Failed to load store health."); })
      .finally(() => setBusy(false));
  };
  useEffect(() => { load(); }, []);

  if (data === null) return <div className="flex justify-center py-32"><Loader2 className="w-6 h-6 animate-spin text-royal" /></div>;
  if (data === false) return <div className="text-sm text-muted-foreground py-16 text-center">Unable to load store health.</div>;

  const o = data.overall || {};
  const sf = data.storefront || {};
  const hy = data.hygiene || {};
  const cm = data.commerce || {};
  const or = data.orders || {};
  const st = STATUS[o.status] || STATUS.warnings;

  return (
    <div className="space-y-6" data-testid="store-health">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <PageHeader title="Store Health™" subtitle="A live, evidence-based view of your storefront's integrity. Every number is read straight from this environment's database — no fabricated metrics." />
        <button onClick={load} disabled={busy} data-testid="refresh-health" className="inline-flex items-center gap-2 rounded-lg border border-navy/30 text-navy px-4 py-2 text-sm font-medium hover:bg-navy/5 disabled:opacity-50">
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />} Refresh
        </button>
      </div>

      {/* Overall banner */}
      <div className={`rounded-xl border-2 p-5 flex items-center gap-4 ${st.cls}`} data-testid="overall-status">
        <st.Icon className="w-8 h-8 shrink-0" />
        <div className="flex-1">
          <div className="font-heading font-bold text-lg">{st.label}</div>
          <div className="text-sm opacity-90">{o.passed}/{o.total} integrity checks passing</div>
        </div>
        <Store className="w-10 h-10 opacity-30 shrink-0" />
      </div>

      {/* Checks */}
      <Section icon={ShieldCheck} title="Integrity Checks">
        <div className="space-y-2" data-testid="health-checks">
          {(o.checks || []).map((c) => (
            <div key={c.key} className="flex items-center gap-3 rounded-lg border p-3" data-testid={`check-${c.key}`}>
              {c.ok ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" /> : <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />}
              <div className="flex-1 text-sm text-foreground">{c.label}</div>
              <span className={`text-[11px] font-semibold rounded-full px-2.5 py-1 ${c.ok ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>{c.detail}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Storefront */}
      <Section icon={BookOpen} title="Public Storefront">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Stat label="Authorized books" value={sf.authorized_books} />
          <Stat label="Live on storefront" value={sf.live_on_storefront} tone="ok" />
          <Stat label="Hidden (missing cover)" value={sf.hidden_missing_cover} tone={sf.hidden_missing_cover ? "bad" : "ok"} />
          <Stat label={`Featured (${sf.featured_mode})`} value={sf.featured_selected} />
        </div>
        {sf.hidden_missing_cover > 0 && (
          <div className="mt-3 text-[11px] text-red-700">Hidden titles (no cover → not shown publicly): {(sf.missing_cover_titles || []).join(", ")}</div>
        )}
      </Section>

      {/* Hygiene */}
      <Section icon={Sparkles} title="Catalog Hygiene">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          <Stat label="Test products detected" value={hy.test_products_matched} />
          <Stat label="Test products visible in catalog" value={hy.test_products_visible_in_catalog} tone={hy.test_products_visible_in_catalog ? "warn" : "ok"} />
        </div>
        {hy.test_products_visible_in_catalog > 0 && (
          <div className="mt-3 text-[11px] text-amber-700">
            {hy.test_products_visible_in_catalog} internal test products are visible to learners. Run <span className="font-medium">Test Product Cleanup</span> in Production Operations™ to archive them.
          </div>
        )}
      </Section>

      {/* Commerce + Orders */}
      <div className="grid lg:grid-cols-2 gap-6">
        <Section icon={ShoppingCart} title="Commerce Configuration">
          <div className="space-y-2 text-sm">
            <Row label="Stripe mode" value={cm.stripe_mode} tone={cm.stripe_mode === "LIVE" ? "live" : cm.stripe_mode === "TEST" ? "test" : "bad"} />
            <Row label="Accepts real money" value={cm.accepts_real_money ? "Yes" : "No"} />
            <Row label="Webhook secret" value={cm.webhook_secret_set ? "Set" : "Missing"} tone={cm.webhook_secret_set ? "ok" : "warn"} />
            <Row label="Email provider connected" value={cm.email_provider_key_set ? "Yes" : "No"} tone={cm.email_provider_key_set ? "ok" : "warn"} />
            <Row label="Sender email" value={cm.sender_email_set ? "Set" : "Missing"} tone={cm.sender_email_set ? "ok" : "warn"} />
          </div>
        </Section>
        <Section icon={Mail} title="Orders & Delivery">
          <div className="grid grid-cols-2 gap-3">
            <Stat label="Orders total" value={or.orders_total} />
            <Stat label="Paid" value={or.orders_paid} tone="ok" />
            <Stat label="Pending" value={or.orders_pending} />
            <Stat label="Confirmations failed" value={or.confirmation_failed} tone={or.confirmation_failed ? "bad" : "ok"} />
            <Stat label="Confirmations sent" value={or.confirmation_sent} />
            <Stat label="Newsletter subscribers" value={or.newsletter_subscribers} />
          </div>
        </Section>
      </div>

      <p className="text-[11px] text-muted-foreground">Snapshot at {new Date(data.at).toLocaleString()} · reflects the database this environment is connected to (production when viewed on the live site).</p>
    </div>
  );
}

function Row({ label, value, tone }) {
  const tones = { ok: "text-emerald-700", warn: "text-amber-700", bad: "text-red-700", live: "text-emerald-700", test: "text-blue-700" };
  return (
    <div className="flex items-center justify-between rounded-lg border px-3 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className={`font-semibold ${tones[tone] || "text-foreground"}`}>{value}</span>
    </div>
  );
}
