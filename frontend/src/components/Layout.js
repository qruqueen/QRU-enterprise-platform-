import { useState, useEffect } from "react";
import { NavLink, useNavigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useMode } from "@/context/ModeContext";
import api from "@/lib/api";
import MusicControl from "@/components/MusicControl";
import FounderSecurityBanner from "@/components/FounderSecurityBanner";
import ErrorBoundary from "@/components/ErrorBoundary";
import { QRUShield } from "@/components/qru";
import {
  LayoutDashboard, MessageSquareText, BookOpen, FlaskConical, ShieldCheck,
  Factory, Sparkles, Library, Bot, GraduationCap, BarChart3, Users, UserCog,
  Bell, Settings, Search, LogOut, Menu, Wand2, Building2, Palette, Activity, Eye, PackageCheck, Brain, Clapperboard, Film,
  ClipboardList, Boxes, PackageOpen, ShieldHalf, Plug, Rocket, Cpu, Workflow, Radio, Store, Brain as BrainIcon, BookOpenCheck, UsersRound, Coins, HardDriveDownload, Gauge, Archive, Wallet, Sprout, ShieldAlert, Stethoscope, Inbox, FolderUp, Database, UploadCloud, Gavel, Youtube, QrCode, Scale, Compass, Cog, LayoutTemplate, Baby, Map, ChevronDown, ChevronRight, History, Layers, FileText,
} from "lucide-react";

// Icon per capability route — keeps the established visual language.
const ICON = {
  "/factory-map": Map, "/": LayoutDashboard, "/create": Sparkles, "/concierge": MessageSquareText, "/projects": Workflow,
  "/knowledge": BookOpen, "/kr2": BookOpenCheck, "/kr-manufacturing": FlaskConical, "/topic-registry": ClipboardList, "/promotion-pipeline": Sprout,
  "/library-import": FolderUp, "/translation-engine": Wand2, "/research": FlaskConical, "/verification": ShieldCheck,
  "/verification-team": ShieldCheck, "/memory-engineering": Brain, "/qiks": BookOpenCheck,
  "/refinement": Cog, "/flow": Workflow, "/architecture": Compass, "/workflows": Workflow, "/orchestrator": Boxes,
  "/director": Gavel, "/manufacturing": Factory, "/manufacture": Sparkles, "/knowledge-manufacturing": Boxes,
  "/manufacturing-studio": PackageCheck, "/mfg-command": Gauge,
  "/publishing": BookOpenCheck, "/media-division": Boxes, "/cover-studio": Palette, "/products": PackageOpen, "/product-library": Library, "/companion": QrCode,
  "/colleges": GraduationCap, "/teach": Rocket,
  "/storyboard-studio": Clapperboard, "/cinema-studio": Film, "/little-legacy": Baby, "/flagship-showcase": Film, "/media-studio": Clapperboard,
  "/wis": UsersRound, "/media-library": Clapperboard, "/creative-studio": Palette, "/visual-studio": Eye, "/media-starter-kit": PackageCheck,
  "/poster-studio": LayoutTemplate, "/inspection": ShieldHalf,
  "/store": Store, "/youtube": Youtube, "/connectors": UploadCloud, "/distribution": Radio, "/shipping-status": PackageCheck,
  "/constitution": Scale, "/governance": BrainIcon, "/trust": ShieldCheck, "/agents": UsersRound,
  "/product-protection": ShieldHalf, "/design-director": Gauge, "/design-intelligence": Sparkles,
  "/founder-inbox": Inbox, "/command-center": LayoutDashboard, "/evidence": Database, "/factory-health": Stethoscope,
  "/factory-monitor": Radio, "/failure-intelligence": ShieldAlert, "/autonomy": BrainIcon, "/enterprise-autonomy": Cpu,
  "/analytics": BarChart3, "/manufacturing-economics": Wallet, "/first-dollar": Coins, "/factory-readiness": Gauge,
  "/customers": Users, "/workforce": Bot, "/organization": Building2, "/asset-vault": Archive, "/command": MessageSquareText,
  "/creative-assets": Layers, "/publication-governance": Gavel, "/printable-studio": FileText,
  "/enterprise-health": Activity, "/blueprint": BookOpenCheck, "/experience-lab": Eye,
  "/integration-hub": Plug, "/ai-services": Cpu, "/users": UserCog, "/portability": HardDriveDownload,
  "/engineering-console": Cpu, "/settings": Settings, "/production-operations": Database,
  "/store-health": Stethoscope, "/founder-manual": BookOpenCheck, "/distribution-architecture": Workflow, "/bundles": Boxes, "/etsy": Store,
};
const iconFor = (route) => ICON[route] || Boxes;

// Minimal fallback if the Registry is briefly unavailable.
const FALLBACK = {
  core: [
    { id: "dashboard", label: "Founder Console", route: "/" },
    { id: "create", label: "Create", route: "/create" },
    { id: "knowledge-records", label: "Knowledge & Decoder™", route: "/knowledge" },
    { id: "book-mfg", label: "Book Manufacturing™", route: "/book-manufacturing" },
    { id: "media-division", label: "Media & Design Studio", route: "/media-division" },
    { id: "distribution", label: "Publishing & Distribution", route: "/distribution" },
    { id: "governance", label: "Governance & Trust", route: "/governance" },
    { id: "factory-map", label: "All Capabilities", route: "/factory-map" },
  ],
  pinned: [],
  sections: [],
  legacy: [],
};

function NavItem({ item, onNavigate }) {
  const Icon = iconFor(item.route);
  return (
    <NavLink
      to={item.route}
      end={item.route === "/"}
      data-testid={`nav-${item.id}`}
      title={item.hint ? `${item.label} — ${item.hint}` : item.label}
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 lg:py-2 rounded-sm text-sm transition-colors duration-150 active:bg-white/15 ${
          isActive ? "bg-gold text-navy font-bold shadow-sm" : "text-white/65 hover:bg-white/10 hover:text-white"
        }`
      }
    >
      <Icon className="w-4 h-4 shrink-0" />
      <span className="flex-1 truncate">{item.label}</span>
    </NavLink>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  const { canToggle, switchMode } = useMode();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [q, setQ] = useState("");
  const [nav, setNav] = useState(null);
  const [legacyOpen, setLegacyOpen] = useState(false);
  const [allOpen, setAllOpen] = useState(false);

  useEffect(() => {
    api.get("/capability-registry/navigation")
      .then((r) => setNav(r.data))
      .catch(() => setNav(FALLBACK));
  }, [location.pathname === "/factory-map"]); // refresh when returning from the Registry

  const model = nav || FALLBACK;
  const doSearch = (e) => {
    e.preventDefault();
    if (q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
  };
  const close = () => setMobileOpen(false);
  const initials = (user?.name || "U").split(" ").map((n) => n[0]).slice(0, 2).join("");

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside
        className={`fixed lg:static z-40 w-[85vw] max-w-xs lg:w-64 h-screen bg-navy text-white/90 border-r border-white/10 flex flex-col transition-transform duration-300 ease-out ${
          mobileOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-white/10 shrink-0" style={{ paddingTop: "env(safe-area-inset-top)", height: "calc(4rem + env(safe-area-inset-top))" }}>
          <QRUShield className="w-8 h-8 shrink-0" />
          <div className="leading-none">
            <p className="font-heading font-bold text-[16px] tracking-tight text-white">QRU FACTORY™</p>
            <p className="text-[8.5px] text-gold tracking-[0.2em] font-semibold mt-0.5">KNOWLEDGE MANUFACTURING OS</p>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5" data-testid="sidebar-nav">
          {/* Core capabilities — the Founder Cockpit (8 items) */}
          <p className="overline text-white/40 px-3 pt-2 pb-1">Core Capabilities</p>
          {(model.core || []).map((item) => <NavItem key={item.id} item={item} onNavigate={close} />)}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "production-operations", label: "Production Operations™", route: "/production-operations" }} onNavigate={close} />
          )}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "store-health", label: "Store Health™", route: "/store-health" }} onNavigate={close} />
          )}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "founder-manual", label: "Operator's Manual™", route: "/founder-manual" }} onNavigate={close} />
          )}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "distribution-architecture", label: "Distribution Architecture™", route: "/distribution-architecture" }} onNavigate={close} />
          )}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "bundles", label: "Bundles™", route: "/bundles" }} onNavigate={close} />
          )}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "etsy", label: "Etsy Integration™", route: "/etsy" }} onNavigate={close} />
          )}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "creative-assets", label: "Creative Assets™", route: "/creative-assets" }} onNavigate={close} />
          )}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "printable-studio", label: "Printable Studio™", route: "/printable-studio" }} onNavigate={close} />
          )}
          {["Founder & CEO", "Administrator"].includes(user?.role) && (
            <NavItem item={{ id: "publication-governance", label: "Publication Governance™", route: "/publication-governance" }} onNavigate={close} />
          )}

          {/* All Capabilities — every other working page, one click away (collapsed) */}
          {model.sections && model.sections.length > 0 && (
            <div className="pt-4">
              <button
                data-testid="all-capabilities-toggle"
                onClick={() => setAllOpen((v) => !v)}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-sm text-xs font-semibold text-white/50 hover:bg-white/5 hover:text-white/80 transition-colors"
              >
                <Boxes className="w-3.5 h-3.5 shrink-0" />
                <span className="flex-1 text-left tracking-wide uppercase">All Capabilities</span>
                <span className="text-[10px] bg-white/10 rounded-full px-1.5 py-0.5">
                  {model.sections.reduce((n, s) => n + s.items.length, 0)}
                </span>
                {allOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>
              {allOpen && (
                <div data-testid="all-capabilities-drawer" className="mt-1 pl-1 border-l border-white/10 ml-3">
                  {model.sections.map((s) => (
                    <div key={s.label}>
                      <p className="overline text-white/35 px-3 pt-3 pb-1">{s.label}</p>
                      {s.items.map((item) => <NavItem key={item.id} item={item} onNavigate={close} />)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Legacy — Under Review (Merged/Deprecated), collapsed */}
          {model.legacy && model.legacy.length > 0 && (
            <div className="pt-4">
              <button
                data-testid="legacy-drawer-toggle"
                onClick={() => setLegacyOpen((v) => !v)}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-sm text-xs font-semibold text-white/45 hover:bg-white/5 hover:text-white/70 transition-colors"
              >
                <History className="w-3.5 h-3.5 shrink-0" />
                <span className="flex-1 text-left tracking-wide uppercase">Legacy — Under Review</span>
                <span className="text-[10px] bg-white/10 rounded-full px-1.5 py-0.5">{model.legacy.length}</span>
                {legacyOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>
              {legacyOpen && (
                <div data-testid="legacy-drawer" className="mt-1 pl-1 border-l border-white/10 ml-3 space-y-0.5">
                  {model.legacy.map((item) => (
                    <NavLink
                      key={item.id}
                      to={item.route}
                      data-testid={`nav-${item.id}`}
                      title={item.duplicate_of ? `Recommend merging into ${item.duplicate_of}` : item.hint}
                      onClick={close}
                      className={({ isActive }) =>
                        `flex items-center gap-2.5 px-3 py-1.5 rounded-sm text-[13px] transition-colors ${
                          isActive ? "bg-white/15 text-white" : "text-white/40 hover:bg-white/5 hover:text-white/60"
                        }`
                      }
                    >
                      {(() => { const I = iconFor(item.route); return <I className="w-3.5 h-3.5 shrink-0 opacity-70" />; })()}
                      <span className="flex-1 truncate">{item.label}</span>
                      <span className="text-[8px] uppercase tracking-wide text-amber-300/70">{item.status}</span>
                    </NavLink>
                  ))}
                  <button
                    data-testid="legacy-review-link"
                    onClick={() => { navigate("/factory-map"); close(); }}
                    className="w-full text-left px-3 py-1.5 text-[11px] text-gold/70 hover:text-gold"
                  >
                    Review & consolidate on the Factory Map™ →
                  </button>
                </div>
              )}
            </div>
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

      {mobileOpen && <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={() => setMobileOpen(false)} />}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 lg:ml-0">
        <header
          className="border-b bg-card/80 backdrop-blur sticky top-0 z-20 flex items-center gap-4 px-4 sm:px-6 h-16"
          style={{ paddingTop: "env(safe-area-inset-top)", height: "calc(4rem + env(safe-area-inset-top))" }}
        >
          <button className="lg:hidden -ml-1 p-2.5 rounded-sm active:bg-muted transition-colors" data-testid="mobile-menu-btn" onClick={() => setMobileOpen(true)} aria-label="Open menu">
            <Menu className="w-6 h-6" />
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
        <main className="flex-1 p-4 sm:p-8 pb-24 lg:pb-8 max-w-[1600px] w-full mx-auto">
          <FounderSecurityBanner />
          <ErrorBoundary routeKey={location.pathname}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      {/* Mobile bottom tab bar — native app feel */}
      <MobileTabBar onOpenMenu={() => setMobileOpen(true)} />
    </div>
  );
}

const TABS = [
  { id: "dashboard", label: "Console", route: "/", icon: LayoutDashboard, end: true },
  { id: "create", label: "Create", route: "/create", icon: Sparkles },
  { id: "knowledge", label: "Knowledge", route: "/knowledge", icon: BookOpen },
  { id: "concierge", label: "Concierge", route: "/concierge", icon: MessageSquareText },
];

function MobileTabBar({ onOpenMenu }) {
  return (
    <nav
      data-testid="mobile-tab-bar"
      className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-navy/95 backdrop-blur border-t border-white/10 flex items-stretch"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      {TABS.map((t) => {
        const Icon = t.icon;
        return (
          <NavLink
            key={t.id}
            to={t.route}
            end={t.end}
            data-testid={`tab-${t.id}`}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center justify-center gap-0.5 min-h-[56px] py-1.5 text-[10px] font-medium transition-colors active:bg-white/10 ${
                isActive ? "text-gold" : "text-white/60"
              }`
            }
          >
            <Icon className="w-5 h-5" />
            <span className="tracking-wide">{t.label}</span>
          </NavLink>
        );
      })}
      <button
        data-testid="tab-menu"
        onClick={onOpenMenu}
        className="flex-1 flex flex-col items-center justify-center gap-0.5 min-h-[56px] py-1.5 text-[10px] font-medium text-white/60 active:bg-white/10 transition-colors"
      >
        <Menu className="w-5 h-5" />
        <span className="tracking-wide">Menu</span>
      </button>
    </nav>
  );
}
