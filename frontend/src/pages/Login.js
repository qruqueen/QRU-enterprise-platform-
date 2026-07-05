import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";
import { QRUShield } from "@/components/qru";
import { ArrowRight } from "lucide-react";
export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("22j2rsdzb8@privaterelay.appleid.com");
  const [password, setPassword] = useState("QruFounder2026!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left brand panel */}
      <div className="hidden lg:flex flex-col justify-between p-12 text-white relative overflow-hidden" style={{ backgroundColor: "hsl(var(--navy))" }}>
        <div
          className="absolute inset-0 opacity-25"
          style={{
            backgroundImage:
              "radial-gradient(circle at 22% 18%, hsl(var(--royal) / 0.55) 0%, transparent 42%), radial-gradient(circle at 85% 88%, hsl(var(--gold) / 0.22) 0%, transparent 42%)",
          }}
        />
        <div
          className="absolute inset-0 opacity-[0.06]"
          style={{ backgroundImage: "linear-gradient(hsl(0 0% 100%) 1px, transparent 1px), linear-gradient(90deg, hsl(0 0% 100%) 1px, transparent 1px)", backgroundSize: "44px 44px" }}
        />
        <div className="relative flex items-center gap-3">
          <QRUShield className="w-11 h-11" />
          <span className="font-heading font-bold tracking-tight text-xl">QRU FACTORY™</span>
        </div>
        <div className="relative max-w-md">
          <p className="overline text-gold mb-4">Quest for Real Understanding</p>
          <h1 className="font-heading text-5xl font-bold leading-[1.08] tracking-tight">
            We manufacture understanding from verified knowledge.
          </h1>
          <p className="text-white/60 mt-5 leading-relaxed text-[15px]">
            QRU does not simplify the truth. QRU simplifies the path to understanding the truth.
          </p>
        </div>
        <div className="relative text-gold/70 text-xs tracking-[0.2em] font-semibold">
          KNOWLEDGE ENTERS · UNDERSTANDING LEAVES
        </div>
      </div>

      {/* Right form */}
      <div className="flex items-center justify-center p-6 sm:p-12 bg-background">
        <div className="w-full max-w-sm animate-fade-up">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <QRUShield className="w-9 h-9" />
            <span className="font-heading font-bold tracking-tight">QRU FACTORY™</span>
          </div>
          <p className="overline text-royal mb-2">Enterprise Access</p>
          <h2 className="font-heading text-3xl font-bold tracking-tight mb-1 text-navy">Sign in to the OS</h2>
          <p className="text-muted-foreground text-sm mb-8">Operate the knowledge manufacturing enterprise.</p>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-sm font-medium">Email</label>
              <input
                data-testid="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium">Password</label>
              <input
                data-testid="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full px-3 py-2 rounded-sm border bg-card outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
                required
              />
            </div>
            {error && (
              <p data-testid="login-error" className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-sm px-3 py-2">
                {error}
              </p>
            )}
            <button
              data-testid="login-submit"
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground py-2.5 rounded-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60"
            >
              {loading ? "Signing in…" : "Enter Command Center"}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </form>
          <div className="mt-6 text-xs text-muted-foreground bg-muted rounded-sm p-3 border">
            <p className="font-medium text-foreground mb-1">Founder access (temporary — set your own after login)</p>
            Founder · 22j2rsdzb8@privaterelay.appleid.com / QruFounder2026!<br />
            <span className="text-muted-foreground/70">Demo Admin · demo.admin@qru.com / qru-demo-admin-2026</span>
          </div>
        </div>
      </div>
    </div>
  );
}
