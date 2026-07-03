import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { ShieldCheck, Lock, Loader2, Copyright, Droplets, KeyRound } from "lucide-react";

const LICENSE_OPTIONS = ["Personal Use", "Classroom/Teacher", "School/Organization", "Commercial"];

export default function ProductProtection() {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(null);
  const [license, setLicense] = useState({});

  const load = async () => {
    const { data } = await api.get("/protection/dashboard");
    setData(data);
  };
  useEffect(() => { load(); }, []);

  const verify = async (pid) => {
    setBusy(pid + "-verify");
    try {
      const { data } = await api.post(`/protection/${pid}/verify`);
      toast[data.verified ? "success" : "warning"](
        data.verified ? "Product verified by the AI Verification Team" : "Product flagged — needs revision/escalation");
      load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(null); }
  };

  const applyProtection = async (pid) => {
    setBusy(pid + "-protect");
    try {
      await api.post(`/protection/${pid}/apply-protection`, {
        license_type: license[pid] || "Personal Use", watermark: true, access_control: "account_required",
      });
      toast.success("Protection applied (copyright, watermark, license, secure access)");
      load();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setBusy(null); }
  };

  const secureLink = async (pid) => {
    try {
      const { data } = await api.post(`/protection/${pid}/secure-link`, { minutes: 60 });
      await navigator.clipboard?.writeText(`${process.env.REACT_APP_BACKEND_URL}${data.path}`).catch(() => {});
      toast.success("Expiring secure download link created (copied)");
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  const s = data?.summary;

  return (
    <div className="space-y-8" data-testid="protection-page">
      <div>
        <p className="overline text-primary mb-1">IP & Access Security</p>
        <h1 className="font-heading text-3xl font-bold tracking-tight">Product Protection & Verification Agent™</h1>
        <p className="text-muted-foreground text-sm mt-1">Balanced protection — secure for QRU, simple for buyers, teachers & families.</p>
      </div>

      {s && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[["Products", s.total], ["Verified", s.verified], ["Protected", s.protected],
            ["Published", s.published], ["At Risk", s.at_risk]].map(([l, v]) => (
            <div key={l} className="bg-card border rounded-sm p-4">
              <p className="text-2xl font-heading font-bold">{v}</p>
              <p className="text-xs text-muted-foreground mt-1">{l}</p>
            </div>
          ))}
        </div>
      )}

      <div className="bg-card border rounded-sm overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted text-xs text-muted-foreground">
            <tr>
              <th className="text-left px-4 py-2">Product</th>
              <th className="text-left px-4 py-2">Verification</th>
              <th className="text-left px-4 py-2">License</th>
              <th className="text-left px-4 py-2">Protection</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.rows?.map((r) => (
              <tr key={r.id} data-testid={`protection-row-${r.id}`}>
                <td className="px-4 py-3">
                  <p className="font-medium">{r.title}</p>
                  <p className="text-[11px] text-muted-foreground font-mono">{r.product_code} · {r.product_type}</p>
                  {r.risk_flags?.length > 0 && (
                    <p className="text-[11px] text-amber-600 mt-0.5">⚠ {r.risk_flags.join(", ")}</p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-[11px] px-2 py-0.5 rounded-full ${r.verified ? "bg-emerald-100 text-emerald-700" : "bg-muted text-muted-foreground"}`}>
                    {r.verified ? `Verified ${r.confidence_score ? `(${r.confidence_score}%)` : ""}` : (r.verification_status || "Unverified")}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs">{r.license_type}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-1.5 text-muted-foreground">
                    <Copyright className={`w-3.5 h-3.5 ${r.copyright_applied ? "text-emerald-600" : "opacity-30"}`} />
                    <Droplets className={`w-3.5 h-3.5 ${r.watermark_applied ? "text-blue-600" : "opacity-30"}`} />
                    <Lock className={`w-3.5 h-3.5 ${r.access_control === "account_required" ? "text-primary" : "opacity-30"}`} />
                  </div>
                </td>
                <td className="px-4 py-3 text-xs">{r.publication_status}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <button data-testid={`verify-btn-${r.id}`} onClick={() => verify(r.id)} disabled={busy === r.id + "-verify"}
                      className="flex items-center gap-1 text-[11px] px-2 py-1 rounded-sm border hover:bg-muted">
                      {busy === r.id + "-verify" ? <Loader2 className="w-3 h-3 animate-spin" /> : <ShieldCheck className="w-3 h-3" />} Verify
                    </button>
                    <select data-testid={`license-select-${r.id}`} value={license[r.id] || "Personal Use"}
                      onChange={(e) => setLicense({ ...license, [r.id]: e.target.value })}
                      className="text-[11px] px-1.5 py-1 rounded-sm border bg-background">
                      {LICENSE_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
                    </select>
                    <button data-testid={`protect-btn-${r.id}`} onClick={() => applyProtection(r.id)} disabled={busy === r.id + "-protect"}
                      className="flex items-center gap-1 text-[11px] px-2 py-1 rounded-sm border hover:bg-muted">
                      {busy === r.id + "-protect" ? <Loader2 className="w-3 h-3 animate-spin" /> : <Lock className="w-3 h-3" />} Protect
                    </button>
                    <button data-testid={`link-btn-${r.id}`} onClick={() => secureLink(r.id)}
                      className="flex items-center gap-1 text-[11px] px-2 py-1 rounded-sm border hover:bg-muted">
                      <KeyRound className="w-3 h-3" /> Link
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
