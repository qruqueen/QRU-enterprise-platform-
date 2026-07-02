import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";
import { Boxes, ArrowRight } from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@qru.com");
  const [password, setPassword] = useState("qru-admin-2026");
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
      <div className="hidden lg:flex flex-col justify-between p-12 bg-[#0A0A0A] text-white relative overflow-hidden">
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "url('https://images.unsplash.com/photo-1707730318002-6fbd8ecd6b77?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div className="relative flex items-center gap-3">
          <div className="w-9 h-9 rounded-sm bg-primary flex items-center justify-center">
            <Boxes className="w-5 h-5" />
          </div>
          <span className="font-heading font-bold tracking-tight text-lg">QRU FACTORY™</span>
        </div>
        <div className="relative max-w-md">
          <p className="overline text-primary mb-4">Quest for Real Understanding</p>
          <h1 className="font-heading text-4xl font-bold leading-tight tracking-tight">
            We manufacture understanding from verified knowledge.
          </h1>
          <p className="text-white/60 mt-4 leading-relaxed">
            QRU does not simplify the truth. QRU simplifies the path to understanding the truth.
          </p>
        </div>
        <div className="relative text-white/40 text-xs tracking-wide">
          KNOWLEDGE ENTERS · UNDERSTANDING LEAVES
        </div>
      </div>

      {/* Right form */}
      <div className="flex items-center justify-center p-6 sm:p-12 bg-background">
        <div className="w-full max-w-sm animate-fade-up">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-sm bg-primary flex items-center justify-center">
              <Boxes className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading font-bold tracking-tight">QRU FACTORY™</span>
          </div>
          <p className="overline text-primary mb-2">Enterprise Access</p>
          <h2 className="font-heading text-2xl font-bold tracking-tight mb-1">Sign in to the OS</h2>
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
            <p className="font-medium text-foreground mb-1">Demo credentials</p>
            Admin · admin@qru.com / qru-admin-2026<br />
            Executive · executive@qru.com / qru-exec-2026
          </div>
        </div>
      </div>
    </div>
  );
}
