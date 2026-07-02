import { useState } from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useMode } from "@/context/ModeContext";
import { Compass, GraduationCap, Route, Heart, Award, Search, LogOut, Menu, ArrowLeftRight } from "lucide-react";

const NAV = [
  { to: "/learn", label: "Discover", icon: Compass, end: true, testid: "cnav-discover" },
  { to: "/learn/my-learning", label: "My Learning", icon: GraduationCap, testid: "cnav-mylearning" },
  { to: "/learn/pathways", label: "Learning Paths", icon: Route, testid: "cnav-pathways" },
  { to: "/learn/favorites", label: "Favorites", icon: Heart, testid: "cnav-favorites" },
  { to: "/learn/certificates", label: "Certificates", icon: Award, testid: "cnav-certificates" },
];

export default function ConsumerLayout() {
  const { user, logout } = useAuth();
  const { canToggle, switchMode } = useMode();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);

  const doSearch = (e) => {
    e.preventDefault();
    navigate(`/learn?q=${encodeURIComponent(q.trim())}`);
  };
  const initials = (user?.name || "L").split(" ").map((n) => n[0]).slice(0, 2).join("");

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="sticky top-0 z-30 border-b border-border bg-white/85 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center gap-4">
          <NavLink to="/learn" className="flex items-center gap-2.5 shrink-0" data-testid="consumer-logo">
            <img src="/qru-shield-light.png" alt="QRU" className="w-8 h-8 object-contain" style={{ filter: "none" }} />
            <div className="leading-none hidden sm:block">
              <p className="font-heading font-bold text-[15px] tracking-tight" style={{ color: "hsl(var(--royal))" }}>QRU</p>
              <p className="text-[9px] tracking-[0.18em]" style={{ color: "hsl(var(--gold))" }}>LEARNING</p>
            </div>
          </NavLink>

          <nav className="hidden lg:flex items-center gap-1 ml-2">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} data-testid={item.testid}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2 rounded-full text-sm font-medium transition-colors ${
                    isActive ? "bg-secondary text-primary" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}>
                <item.icon className="w-4 h-4" />{item.label}
              </NavLink>
            ))}
          </nav>

          <form onSubmit={doSearch} className="ml-auto relative hidden md:block w-56">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input data-testid="consumer-search" value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Ask a question…"
              className="w-full pl-9 pr-3 py-2 text-sm bg-muted rounded-full border border-transparent focus:border-primary focus:bg-card outline-none transition-colors" />
          </form>

          {canToggle && (
            <button onClick={() => switchMode("enterprise")} data-testid="switch-to-enterprise"
              className="hidden sm:flex items-center gap-1.5 text-xs px-3 py-2 rounded-full border border-border text-muted-foreground hover:text-foreground hover:border-primary transition-colors">
              <ArrowLeftRight className="w-3.5 h-3.5" /> Enterprise
            </button>
          )}

          <div className="flex items-center gap-2 shrink-0">
            <div className="w-9 h-9 rounded-full flex items-center justify-center font-heading font-semibold text-sm text-white" style={{ background: "hsl(var(--royal))" }}>
              {initials}
            </div>
            <button data-testid="consumer-logout" onClick={logout} className="text-muted-foreground hover:text-destructive p-1">
              <LogOut className="w-4 h-4" />
            </button>
          </div>

          <button className="lg:hidden" data-testid="consumer-menu" onClick={() => setOpen(!open)}><Menu className="w-5 h-5" /></button>
        </div>
        {open && (
          <nav className="lg:hidden border-t border-border px-4 py-2 space-y-1 bg-white">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} onClick={() => setOpen(false)}
                className={({ isActive }) => `flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${isActive ? "bg-secondary text-primary" : "text-muted-foreground"}`}>
                <item.icon className="w-4 h-4" />{item.label}
              </NavLink>
            ))}
          </nav>
        )}
      </header>

      <main className="flex-1 w-full">
        <Outlet />
      </main>

      <footer className="border-t border-border py-8 mt-16">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="font-heading text-sm font-semibold" style={{ color: "hsl(var(--royal))" }}>QRU · Quest for Real Understanding</p>
          <p className="text-xs text-muted-foreground mt-1 italic">Verified knowledge enters. Understanding grows. Lives improve.</p>
        </div>
      </footer>
    </div>
  );
}
