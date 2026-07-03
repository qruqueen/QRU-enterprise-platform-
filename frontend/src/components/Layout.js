import { useState } from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useMode } from "@/context/ModeContext";
import MusicControl from "@/components/MusicControl";
import {
  LayoutDashboard, MessageSquareText, BookOpen, FlaskConical, ShieldCheck,
  Factory, Sparkles, Library, Bot, GraduationCap, BarChart3, Users, UserCog,
  Bell, Settings, Search, LogOut, Menu, Wand2, Building2, Palette, Activity, Eye, PackageCheck, Brain, Clapperboard,
} from "lucide-react";

const NAV = [
  { section: "Mission Control" },
  { to: "/", label: "Command Center", icon: LayoutDashboard, end: true, testid: "nav-dashboard" },
  { to: "/command", label: "Command Console", icon: MessageSquareText, testid: "nav-command" },
  { to: "/enterprise-health", label: "Enterprise Health", icon: Activity, testid: "nav-health-dash" },
  { to: "/organization", label: "Organization", icon: Building2, testid: "nav-organization" },
  { section: "Knowledge" },
  { to: "/knowledge", label: "Knowledge Records", icon: BookOpen, testid: "nav-knowledge" },
  { to: "/translation-engine", label: "Translation Engine™", icon: Wand2, testid: "nav-translation" },
  { to: "/research", label: "Research Center", icon: FlaskConical, testid: "nav-research" },
  { to: "/verification", label: "Verification Center", icon: ShieldCheck, testid: "nav-verification" },
  { to: "/memory-engineering", label: "Memory Engineering™", icon: Brain, testid: "nav-memory" },
  { section: "Manufacturing" },
  { to: "/manufacturing", label: "Manufacturing Orders", icon: Factory, testid: "nav-manufacturing" },
  { to: "/manufacture", label: "Product Manufacturing", icon: Sparkles, testid: "nav-manufacture" },
  { to: "/manufacturing-studio", label: "Manufacturing Studio", icon: PackageCheck, testid: "nav-mfg-studio" },
  { to: "/products", label: "Product Library", icon: Library, testid: "nav-products" },
  { to: "/creative-studio", label: "Creative Studio™", icon: Palette, testid: "nav-creative" },
  { to: "/media-studio", label: "Media Studio™", icon: Clapperboard, testid: "nav-media" },
  { to: "/design-intelligence", label: "Design Intelligence™", icon: Sparkles, testid: "nav-design-intel" },
  { to: "/experience-lab", label: "Experience Lab™", icon: Eye, testid: "nav-experience" },
  { section: "Enterprise" },
  { to: "/workforce", label: "Digital Workforce", icon: Bot, testid: "nav-workforce" },
  { to: "/colleges", label: "Understanding Colleges", icon: GraduationCap, testid: "nav-health" },
  { to: "/analytics", label: "Analytics", icon: BarChart3, testid: "nav-analytics" },
  { to: "/customers", label: "Customers", icon: Users, testid: "nav-customers" },
  { section: "Administration" },
  { to: "/users", label: "User Management", icon: UserCog, testid: "nav-users" },
  { to: "/settings", label: "Settings", icon: Settings, testid: "nav-settings" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const { canToggle, switchMode } = useMode();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [q, setQ] = useState("");

  const doSearch = (e) => {
    e.preventDefault();
    if (q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  };

  const initials = (user?.name || "U").split(" ").map((n) => n[0]).slice(0, 2).join("");

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside
        className={`fixed lg:static z-40 w-64 h-screen bg-navy text-white/90 border-r border-white/10 flex flex-col transition-transform ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-white/10 shrink-0">
          <img src="/qru-shield-light.png" alt="QRU" className="w-8 h-8 object-contain" />
          <div className="leading-none">
            <p className="font-heading font-bold text-[15px] tracking-tight text-white">QRU FACTORY™</p>
            <p className="text-[9px] text-gold tracking-[0.18em]">UNDERSTANDING OS</p>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
          {NAV.map((item, i) =>
            item.section ? (
              <p key={i} className="overline text-white/40 px-3 pt-4 pb-1">{item.section}</p>
            ) : (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                data-testid={item.testid}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-sm text-sm transition-colors ${
                    isActive
                      ? "bg-gold text-navy font-semibold"
                      : "text-white/70 hover:bg-white/10 hover:text-white"
                  }`
                }
              >
                <item.icon className="w-4 h-4 shrink-0" />
                {item.label}
              </NavLink>
            )
          )}
        </nav>
        <div className="p-3 border-t border-white/10">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-9 h-9 rounded-sm bg-gold text-navy flex items-center justify-center font-heading font-semibold text-sm">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate text-white">{user?.name}</p>
              <p className="text-xs text-white/50 truncate">{user?.role}</p>
            </div>
            <button data-testid="logout-btn" onClick={logout} className="text-white/50 hover:text-destructive p-1">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {mobileOpen && <div className="fixed inset-0 bg-black/30 z-30 lg:hidden" onClick={() => setMobileOpen(false)} />}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 lg:ml-0">
        <header className="h-16 border-b bg-card/80 backdrop-blur sticky top-0 z-20 flex items-center gap-4 px-4 sm:px-6">
          <button className="lg:hidden" data-testid="mobile-menu-btn" onClick={() => setMobileOpen(true)}>
            <Menu className="w-5 h-5" />
          </button>
          <form onSubmit={doSearch} className="flex-1 max-w-md relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              data-testid="global-search-input"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search knowledge, orders, products, workforce…"
              className="w-full pl-9 pr-3 py-2 text-sm bg-muted rounded-sm border border-transparent focus:border-primary focus:bg-card outline-none transition-colors"
            />
          </form>
          <div className="flex items-center gap-1 ml-auto">
            <span className="hidden xl:block text-xs text-muted-foreground italic mr-2">
              QRU simplifies the path to understanding the truth.
            </span>
            {canToggle && (
              <button onClick={() => switchMode("consumer")} data-testid="switch-to-consumer"
                className="hidden sm:flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border border-border text-muted-foreground hover:text-foreground hover:border-primary transition-colors mr-1">
                <Eye className="w-3.5 h-3.5" /> Preview Consumer Mode
              </button>
            )}
            <MusicControl />
            <NavLink to="/notifications" data-testid="nav-notifications" className="p-2 rounded-sm hover:bg-muted text-muted-foreground hover:text-foreground">
              <Bell className="w-5 h-5" />
            </NavLink>
          </div>
        </header>
        <main className="flex-1 p-4 sm:p-8 max-w-[1600px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
