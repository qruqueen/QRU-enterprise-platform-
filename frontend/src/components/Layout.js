import { useState } from "react";
import { NavLink, useNavigate, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useMode } from "@/context/ModeContext";
import MusicControl from "@/components/MusicControl";
import FounderSecurityBanner from "@/components/FounderSecurityBanner";
import {
  LayoutDashboard, MessageSquareText, BookOpen, FlaskConical, ShieldCheck,
  Factory, Sparkles, Library, Bot, GraduationCap, BarChart3, Users, UserCog,
  Bell, Settings, Search, LogOut, Menu, Wand2, Building2, Palette, Activity, Eye, PackageCheck, Brain, Clapperboard,
  ClipboardList, Boxes, ShieldHalf, Plug, Rocket, Cpu, Workflow, Radio, Store, Brain as BrainIcon, BookOpenCheck, UsersRound, Coins, HardDriveDownload, Gauge, Archive, Wallet, Sprout, ShieldAlert,
} from "lucide-react";

const NAV = [
  { section: "The QRU Experience" },
  { to: "/first-dollar", label: "First Dollar Mode™", icon: Coins, testid: "nav-first-dollar", q: "Will a real customer pay for it?" },
  { to: "/factory-readiness", label: "Factory Readiness™", icon: Gauge, testid: "nav-factory-readiness", q: "Which product should we manufacture first?" },
  { to: "/manufacturing-economics", label: "Manufacturing Economics™", icon: Wallet, testid: "nav-economics", q: "What does each product cost — and what's the profit?" },
  { to: "/teach", label: "What to Teach Today", icon: Rocket, testid: "nav-teach", q: "What do we want to teach today?" },
  { to: "/workflows", label: "Workflow Engine™", icon: Workflow, testid: "nav-workflows", q: "What should happen next?" },
  { to: "/factory-monitor", label: "Factory Monitor™", icon: Radio, testid: "nav-factory-monitor", q: "What is happening right now?" },
  { to: "/failure-intelligence", label: "Failure Intelligence™", icon: ShieldAlert, testid: "nav-failure-intelligence", q: "Why did a run fail — and what do I do next?" },
  { to: "/autonomy", label: "Autonomy Center™", icon: BrainIcon, testid: "nav-autonomy", q: "How do we get better and run ourselves?" },
  { to: "/enterprise-autonomy", label: "Continuous Improvement™", icon: Cpu, testid: "nav-enterprise-autonomy", q: "How does every run make the factory better?" },
  { to: "/command-center", label: "Enterprise Command Center™", icon: LayoutDashboard, testid: "nav-command-center", q: "How is the whole enterprise doing?" },
  { to: "/governance", label: "Governance Center™", icon: BrainIcon, testid: "nav-governance", q: "What rules govern everything we make?" },
  { to: "/blueprint", label: "Enterprise Blueprint™", icon: BookOpenCheck, testid: "nav-blueprint", q: "What does every department do and why?" },
  { to: "/wis", label: "Character Library™", icon: UsersRound, testid: "nav-wis", q: "Who are our official characters?" },
  { to: "/qiks", label: "Institutional Knowledge™", icon: BookOpenCheck, testid: "nav-qiks", q: "What has QRU already learned?" },
  { section: "Mission Control" },
  { to: "/", label: "Founder Console", icon: LayoutDashboard, end: true, testid: "nav-dashboard", q: "Where should the Founder focus today?" },
  { to: "/command", label: "Command Console", icon: MessageSquareText, testid: "nav-command", q: "What do you want done — in your own words?" },
  { to: "/enterprise-health", label: "Enterprise Health", icon: Activity, testid: "nav-health-dash", q: "Is the enterprise healthy — and if not, why?" },
  { to: "/organization", label: "Organization", icon: Building2, testid: "nav-organization", q: "Who is doing the work?" },
  { section: "Knowledge" },
  { to: "/knowledge", label: "Knowledge Records", icon: BookOpen, testid: "nav-knowledge", q: "What do we know?" },
  { to: "/topic-registry", label: "Topic Registry™", icon: ClipboardList, testid: "nav-topic-registry", q: "What should we teach — and in what order?" },
  { to: "/promotion-pipeline", label: "Promotion Pipeline™", icon: Sprout, testid: "nav-promotion", q: "How do we turn a Topic Seed into Verified Knowledge?" },
  { to: "/translation-engine", label: "Translation Engine™", icon: Wand2, testid: "nav-translation", q: "How do we make this truly understandable?" },
  { to: "/research", label: "Research Center", icon: FlaskConical, testid: "nav-research", q: "What is the evidence?" },
  { to: "/verification", label: "Verification Center", icon: ShieldCheck, testid: "nav-verification", q: "Can we trust it?" },
  { to: "/verification-team", label: "Verification Team™", icon: ShieldCheck, testid: "nav-verification-team", q: "Can we trust it — automatically, at scale?" },
  { to: "/memory-engineering", label: "Memory Engineering™", icon: Brain, testid: "nav-memory", q: "Will they remember it?" },
  { section: "Manufacturing" },
  { to: "/manufacturing", label: "Manufacturing Orders", icon: Factory, testid: "nav-manufacturing", q: "What are we building right now, and at what stage?" },
  { to: "/orchestrator", label: "Bulk Orchestrator™", icon: Boxes, testid: "nav-orchestrator", q: "How do we scale production without breaking?" },
  { to: "/manufacture", label: "Product Manufacturing", icon: Sparkles, testid: "nav-manufacture", q: "How do we make the actual product?" },
  { to: "/manufacturing-studio", label: "Manufacturing Studio", icon: PackageCheck, testid: "nav-mfg-studio", q: "Is this product ready to ship?" },
  { to: "/products", label: "Product Library", icon: Library, testid: "nav-products", q: "What have we made?" },
  { to: "/product-protection", label: "Product Protection™", icon: ShieldHalf, testid: "nav-protection", q: "Is it protected and properly licensed?" },
  { to: "/creative-studio", label: "Creative Studio™", icon: Palette, testid: "nav-creative", q: "Is it beautiful, engaging, and easy to understand?" },
  { to: "/asset-vault", label: "Asset Vault™", icon: Archive, testid: "nav-asset-vault", q: "Which approved assets can we reuse instead of regenerating?" },
  { to: "/media-studio", label: "Media Studio™", icon: Clapperboard, testid: "nav-media", q: "How do we bring it to life in sound and motion?" },
  { to: "/design-intelligence", label: "Design Intelligence™", icon: Sparkles, testid: "nav-design-intel", q: "What does great QRU design look like — and how do we repeat it?" },
  { to: "/design-director", label: "Design Director™", icon: Gauge, testid: "nav-design-director", q: "Is every product polished before the Founder sees it?" },
  { to: "/experience-lab", label: "Experience Lab™", icon: Eye, testid: "nav-experience", q: "How does this feel to learn?" },
  { section: "Enterprise" },
  { to: "/workforce", label: "Digital Workforce", icon: Bot, testid: "nav-workforce", q: "Who (which AI) does each job?" },
  { to: "/colleges", label: "Understanding Colleges", icon: GraduationCap, testid: "nav-health", q: "What subjects do we teach, and how deep?" },
  { to: "/analytics", label: "Analytics", icon: BarChart3, testid: "nav-analytics", q: "What do the numbers tell us?" },
  { to: "/customers", label: "Customers", icon: Users, testid: "nav-customers", q: "Who are we serving?" },
  { to: "/store", label: "QRU Store™", icon: Store, testid: "nav-store", q: "How do people buy what we make?" },
  { section: "Administration" },
  { to: "/integration-hub", label: "Integration Hub™", icon: Plug, testid: "nav-integration-hub", q: "What are we connected to?" },
  { to: "/ai-services", label: "AI Services™", icon: Cpu, testid: "nav-ai-services", q: "What AI powers can we use right now?" },
  { to: "/users", label: "User Management", icon: UserCog, testid: "nav-users", q: "Who has access, and to what?" },
  { to: "/portability", label: "Portability Center™", icon: HardDriveDownload, testid: "nav-portability", q: "How do we back up and redeploy QRU?" },
  { to: "/settings", label: "Settings", icon: Settings, testid: "nav-settings", q: "How is the factory configured?" },
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
                title={item.q ? `${item.label} — "${item.q}"` : item.label}
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
          <FounderSecurityBanner />
          <Outlet />
        </main>
      </div>
    </div>
  );
}
