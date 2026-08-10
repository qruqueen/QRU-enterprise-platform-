import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { MusicProvider } from "@/context/MusicContext";
import { ModeProvider, useMode } from "@/context/ModeContext";
import { Toaster } from "@/components/ui/sonner";
import Layout from "@/components/Layout";
import ConsumerLayout from "@/components/ConsumerLayout";
import Login from "@/pages/Login";
import MissionControl from "@/pages/MissionControl";
import CommandCenter from "@/pages/CommandCenter";
import EnterpriseHealth from "@/pages/EnterpriseHealth";
import ExperienceLab from "@/pages/ExperienceLab";
import KnowledgeRecords from "@/pages/KnowledgeRecords";
import KnowledgeRecordDetail from "@/pages/KnowledgeRecordDetail";
import TranslationEngine from "@/pages/TranslationEngine";
import ResearchCenter from "@/pages/ResearchCenter";
import VerificationCenter from "@/pages/VerificationCenter";
import ManufacturingOrders from "@/pages/ManufacturingOrders";
import ProductManufacturing from "@/pages/ProductManufacturing";
import ManufacturingStudio from "@/pages/ManufacturingStudio";
import ProductLibrary from "@/pages/ProductLibrary";
import ProductDetail from "@/pages/ProductDetail";
import DigitalWorkforce from "@/pages/DigitalWorkforce";
import Organization from "@/pages/Organization";
import CreativeStudio from "@/pages/CreativeStudio";
import DesignIntelligence from "@/pages/DesignIntelligence";
import DesignDirector from "@/pages/DesignDirector";
import FactoryHealth from "@/pages/FactoryHealth";
import FounderInbox from "@/pages/FounderInbox";
import MemoryEngineering from "@/pages/MemoryEngineering";
import MediaStudio from "@/pages/MediaStudio";
import TopicRegistry from "@/pages/TopicRegistry";
import PromotionPipeline from "@/pages/PromotionPipeline";
import LibraryImport from "@/pages/LibraryImport";
import EngineeringConsole from "@/pages/EngineeringConsole";
import Orchestrator from "@/pages/Orchestrator";
import VerificationTeam from "@/pages/VerificationTeam";
import ProductProtection from "@/pages/ProductProtection";
import IntegrationHub from "@/pages/IntegrationHub";
import ProductionLine from "@/pages/ProductionLine";
import EnterpriseCommandCenter from "@/pages/EnterpriseCommandCenter";
import AIServices from "@/pages/AIServices";
import Workflows from "@/pages/Workflows";
import FactoryMonitor from "@/pages/FactoryMonitor";
import FailureIntelligence from "@/pages/FailureIntelligence";
import Store from "@/pages/Store";
import CheckoutSuccess from "@/pages/CheckoutSuccess";
import AutonomyCenter from "@/pages/AutonomyCenter";
import GovernanceCenter from "@/pages/GovernanceCenter";
import EnterpriseBlueprint from "@/pages/EnterpriseBlueprint";
import CharacterLibrary from "@/pages/CharacterLibrary";
import InstitutionalKnowledge from "@/pages/InstitutionalKnowledge";
import EnterpriseAutonomy from "@/pages/EnterpriseAutonomy";
import FirstDollarMode from "@/pages/FirstDollarMode";
import FactoryReadiness from "@/pages/FactoryReadiness";
import AssetVault from "@/pages/AssetVault";
import CreativeAssets from "@/pages/CreativeAssets";
import PrintableStudio from "@/pages/PrintableStudio";
import PublicationGovernance from "@/pages/PublicationGovernance";
import ManufacturingEconomics from "@/pages/ManufacturingEconomics";
import PortabilityCenter from "@/pages/PortabilityCenter";
import Colleges from "@/pages/Colleges";
import CollegeWorkspace from "@/pages/CollegeWorkspace";
import Analytics from "@/pages/Analytics";
import Customers from "@/pages/Customers";
import UserManagement from "@/pages/UserManagement";
import Notifications from "@/pages/Notifications";
import Settings from "@/pages/Settings";
import SearchResults from "@/pages/SearchResults";
import Connectors from "@/pages/Connectors";
import EtsyIntegration from "@/pages/EtsyIntegration";
import EvidenceDashboard from "@/pages/EvidenceDashboard";
import ManufacturingInspection from "@/pages/ManufacturingInspection";
import ManufacturingDashboard from "@/pages/ManufacturingDashboard";
import KnowledgeRecord2 from "@/pages/KnowledgeRecord2";
import ManufacturingDirector from "@/pages/ManufacturingDirector";
import YouTubePublisher from "@/pages/YouTubePublisher";
import DistributionCenter from "@/pages/DistributionCenter";
import ShippingDashboard from "@/pages/ShippingDashboard";
import FactoryAgents from "@/pages/FactoryAgents";
import VisualStudio from "@/pages/VisualStudio";
import MediaStarterKit from "@/pages/MediaStarterKit";
import TrustRegistry from "@/pages/TrustRegistry";
import CompanionSystem from "@/pages/CompanionSystem";
import MediaLibrary from "@/pages/MediaLibrary";
import FlagshipShowcase from "@/pages/FlagshipShowcase";
import CreateExperience from "@/pages/CreateExperience";
import FactoryConcierge from "@/pages/FactoryConcierge";
import PublishingStandard from "@/pages/PublishingStandard";
import FoundationMap from "@/pages/FoundationMap";
import CoverStudio from "@/pages/CoverStudio";
import PosterStudio from "@/pages/PosterStudio";
import StoryboardStudio from "@/pages/StoryboardStudio";
import KnowledgeManufacturing from "@/pages/KnowledgeManufacturing";
import ProductShelf from "@/pages/ProductShelf";
import LittleLegacyStudio from "@/pages/LittleLegacyStudio";
import ManufacturingFlow from "@/pages/ManufacturingFlow";
import EnterpriseArchitecture from "@/pages/EnterpriseArchitecture";
import Refinement from "@/pages/Refinement";
import Constitution from "@/pages/Constitution";
import ProjectsContinuity from "@/pages/ProjectsContinuity";
import FactoryMap from "@/pages/FactoryMap";
import KRManufacturing from "@/pages/KRManufacturing";
import MediaDivision from "@/pages/MediaDivision";
import CinemaStudio from "@/pages/CinemaStudio";
import DecoderEngine from "@/pages/DecoderEngine";
import BookManufacturing from "@/pages/BookManufacturing";
import FactoryJobs from "@/pages/FactoryJobs";
import ProductFamily from "@/pages/ProductFamily";
import ConsumerHome from "@/pages/consumer/ConsumerHome";
import ConsumerLearn from "@/pages/consumer/ConsumerLearn";
import ConsumerMyLearning from "@/pages/consumer/ConsumerMyLearning";
import ConsumerFavorites from "@/pages/consumer/ConsumerFavorites";
import ConsumerCertificates from "@/pages/consumer/ConsumerCertificates";
import ConsumerPathways from "@/pages/consumer/ConsumerPathways";
import PublicLayout from "@/pages/public/PublicLayout";
import QRUHome from "@/pages/public/QRUHome";
import QRUCatalog from "@/pages/public/QRUCatalog";
import QRUBundles from "@/pages/public/QRUBundles";
import QRUBundlePage from "@/pages/public/QRUBundlePage";
import QRUBundleAccess from "@/pages/public/QRUBundleAccess";
import QRUBookPage from "@/pages/public/QRUBookPage";
import QRUPurchaseSuccess from "@/pages/public/QRUPurchaseSuccess";
import QRUAccess from "@/pages/public/QRUAccess";
import QRUPrivacy from "@/pages/public/QRUPrivacy";
import QRUTerms from "@/pages/public/QRUTerms";
import QRURefunds from "@/pages/public/QRURefunds";
import QRUPathway from "@/pages/public/QRUPathway";
import QRUCollection from "@/pages/public/QRUCollection";
import QRUProductPage from "@/pages/public/QRUProductPage";
import QRUOnlineOrders from "@/pages/QRUOnlineOrders";
import PilotCoordinator from "@/pages/PilotCoordinator";
import ProductionOperations from "@/pages/ProductionOperations";
import StoreHealth from "@/pages/StoreHealth";
import FounderManual from "@/pages/FounderManual";
import DistributionArchitecture from "@/pages/DistributionArchitecture";
import BundlesManager from "@/pages/BundlesManager";
import { Loader2 } from "lucide-react";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    );
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}

function EnterpriseRoutes() {
  return (
    <Routes>
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<MissionControl />} />
        <Route path="command" element={<CommandCenter />} />
        <Route path="enterprise-health" element={<EnterpriseHealth />} />
        <Route path="experience-lab" element={<ExperienceLab />} />
        <Route path="organization" element={<Organization />} />
        <Route path="creative-studio" element={<CreativeStudio />} />
        <Route path="design-intelligence" element={<DesignIntelligence />} />
        <Route path="design-director" element={<DesignDirector />} />
        <Route path="factory-health" element={<FactoryHealth />} />
        <Route path="founder-inbox" element={<FounderInbox />} />
        <Route path="memory-engineering" element={<MemoryEngineering />} />
        <Route path="media-studio" element={<MediaStudio />} />
        <Route path="knowledge" element={<KnowledgeRecords />} />
        <Route path="knowledge/:id" element={<KnowledgeRecordDetail />} />
        <Route path="topic-registry" element={<TopicRegistry />} />
        <Route path="promotion-pipeline" element={<PromotionPipeline />} />
        <Route path="library-import" element={<LibraryImport />} />
        <Route path="engineering-console" element={<EngineeringConsole />} />
        <Route path="translation-engine" element={<TranslationEngine />} />
        <Route path="research" element={<ResearchCenter />} />
        <Route path="verification" element={<VerificationCenter />} />
        <Route path="verification-team" element={<VerificationTeam />} />
        <Route path="manufacturing" element={<ManufacturingOrders />} />
        <Route path="orchestrator" element={<Orchestrator />} />
        <Route path="manufacture" element={<ProductManufacturing />} />
        <Route path="manufacturing-studio" element={<ManufacturingStudio />} />
        <Route path="products/:id" element={<ProductDetail />} />
        <Route path="product-library" element={<ProductLibrary />} />
        <Route path="product-protection" element={<ProductProtection />} />
        <Route path="workforce" element={<DigitalWorkforce />} />
        <Route path="colleges" element={<Colleges />} />
        <Route path="colleges/:id" element={<CollegeWorkspace />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="customers" element={<Customers />} />
        <Route path="users" element={<UserManagement />} />
        <Route path="integration-hub" element={<IntegrationHub />} />
        <Route path="teach" element={<ProductionLine />} />
        <Route path="workflows" element={<Workflows />} />
        <Route path="factory-monitor" element={<FactoryMonitor />} />
        <Route path="failure-intelligence" element={<FailureIntelligence />} />
        <Route path="autonomy" element={<AutonomyCenter />} />
        <Route path="governance" element={<GovernanceCenter />} />
        <Route path="blueprint" element={<EnterpriseBlueprint />} />
        <Route path="wis" element={<CharacterLibrary />} />
        <Route path="qiks" element={<InstitutionalKnowledge />} />
        <Route path="enterprise-autonomy" element={<EnterpriseAutonomy />} />
        <Route path="first-dollar" element={<FirstDollarMode />} />
        <Route path="factory-readiness" element={<FactoryReadiness />} />
        <Route path="asset-vault" element={<AssetVault />} />
        <Route path="creative-assets" element={<CreativeAssets />} />
        <Route path="printable-studio" element={<PrintableStudio />} />
        <Route path="publication-governance" element={<PublicationGovernance />} />
        <Route path="manufacturing-economics" element={<ManufacturingEconomics />} />
        <Route path="portability" element={<PortabilityCenter />} />
        <Route path="store" element={<Store />} />
        <Route path="qru-online-orders" element={<QRUOnlineOrders />} />
        <Route path="pilot-coordinator" element={<PilotCoordinator />} />
        <Route path="production-operations" element={<ProductionOperations />} />
        <Route path="store-health" element={<StoreHealth />} />
        <Route path="founder-manual" element={<FounderManual />} />
        <Route path="distribution-architecture" element={<DistributionArchitecture />} />
        <Route path="bundles" element={<BundlesManager />} />
        <Route path="checkout/success" element={<CheckoutSuccess />} />
        <Route path="command-center" element={<EnterpriseCommandCenter />} />
        <Route path="evidence" element={<EvidenceDashboard />} />
        <Route path="inspection" element={<ManufacturingInspection />} />
        <Route path="mfg-command" element={<ManufacturingDashboard />} />
        <Route path="kr2" element={<KnowledgeRecord2 />} />
        <Route path="director" element={<ManufacturingDirector />} />
        <Route path="youtube" element={<YouTubePublisher />} />
        <Route path="distribution" element={<DistributionCenter />} />
        <Route path="shipping-status" element={<ShippingDashboard />} />
        <Route path="agents" element={<FactoryAgents />} />
        <Route path="visual-studio" element={<VisualStudio />} />
        <Route path="media-starter-kit" element={<MediaStarterKit />} />
        <Route path="trust" element={<TrustRegistry />} />
        <Route path="companion" element={<CompanionSystem />} />
        <Route path="media-library" element={<MediaLibrary />} />
        <Route path="flagship-showcase" element={<FlagshipShowcase />} />
        <Route path="create" element={<CreateExperience />} />
        <Route path="concierge" element={<FactoryConcierge />} />
        <Route path="publishing" element={<PublishingStandard />} />
        <Route path="manufacturing-foundation" element={<FoundationMap />} />
        <Route path="cover-studio" element={<CoverStudio />} />
        <Route path="poster-studio" element={<PosterStudio />} />
        <Route path="storyboard-studio" element={<StoryboardStudio />} />
        <Route path="knowledge-manufacturing" element={<KnowledgeManufacturing />} />
        <Route path="products" element={<ProductShelf />} />
        <Route path="little-legacy" element={<LittleLegacyStudio />} />
        <Route path="flow" element={<ManufacturingFlow />} />
        <Route path="architecture" element={<EnterpriseArchitecture />} />
        <Route path="refinement" element={<Refinement />} />
        <Route path="constitution" element={<Constitution />} />
        <Route path="projects" element={<ProjectsContinuity />} />
        <Route path="factory-map" element={<FactoryMap />} />
        <Route path="kr-manufacturing" element={<KRManufacturing />} />
        <Route path="media-division" element={<MediaDivision />} />
        <Route path="cinema-studio" element={<CinemaStudio />} />
        <Route path="decoder-engine" element={<DecoderEngine />} />
        <Route path="book-manufacturing" element={<BookManufacturing />} />
        <Route path="factory-jobs" element={<FactoryJobs />} />
        <Route path="product-family" element={<ProductFamily />} />
        <Route path="connectors" element={<Connectors />} />
        <Route path="etsy" element={<EtsyIntegration />} />
        <Route path="ai-services" element={<AIServices />} />
        <Route path="notifications" element={<Notifications />} />
        <Route path="settings" element={<Settings />} />
        <Route path="search" element={<SearchResults />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function ConsumerRoutes() {
  return (
    <Routes>
      <Route path="/learn" element={<ProtectedRoute><ConsumerLayout /></ProtectedRoute>}>
        <Route index element={<ConsumerHome />} />
        <Route path="my-learning" element={<ConsumerMyLearning />} />
        <Route path="pathways" element={<ConsumerPathways />} />
        <Route path="favorites" element={<ConsumerFavorites />} />
        <Route path="certificates" element={<ConsumerCertificates />} />
        <Route path=":id" element={<ConsumerLearn />} />
      </Route>
      <Route path="*" element={<Navigate to="/learn" replace />} />
    </Routes>
  );
}

// Only the bare root is decided by auth state (Mission Control for a signed-in Founder,
// the storefront home for everyone else — unchanged from today). Every other public page
// is hoisted to App()'s top-level router below, reachable regardless of auth state, so a
// signed-in Founder can view the actual storefront experience (with FounderStorefrontControls
// layered in by each page) rather than always being routed into the Enterprise console.
function PublicRoutes() {
  return (
    <Routes>
      <Route path="/" element={<PublicLayout />}>
        <Route index element={<QRUHome />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function ModeRouter() {
  const { user, loading } = useAuth();
  const { isConsumer } = useMode();
  if (loading)
    return <div className="min-h-screen flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (!user) return <PublicRoutes />;
  return isConsumer ? <ConsumerRoutes /> : <EnterpriseRoutes />;
}

function App() {
  return (
    <AuthProvider>
      <ModeProvider>
        <MusicProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              {/* Path-less layout route: no path here means none of these match bare "/",
                  which stays owned by ModeRouter below. Each child's own absolute path
                  wins over ModeRouter's "/*" catch-all regardless of auth state, per
                  React Router's route ranking (explicit paths outrank a splat). */}
              <Route element={<PublicLayout />}>
                <Route path="/catalog" element={<QRUCatalog />} />
                <Route path="/bundles" element={<QRUBundles />} />
                <Route path="/bundle/:slug" element={<QRUBundlePage />} />
                <Route path="/bundle-access/:token" element={<QRUBundleAccess />} />
                <Route path="/book/:slug" element={<QRUBookPage />} />
                <Route path="/product/:slug" element={<QRUProductPage />} />
                <Route path="/for/:slug" element={<QRUPathway />} />
                <Route path="/collections/:subject" element={<QRUCollection />} />
                <Route path="/purchase/success" element={<QRUPurchaseSuccess />} />
                <Route path="/access/:token" element={<QRUAccess />} />
                <Route path="/privacy" element={<QRUPrivacy />} />
                <Route path="/terms" element={<QRUTerms />} />
                <Route path="/refunds" element={<QRURefunds />} />
              </Route>
              <Route path="/*" element={<ModeRouter />} />
            </Routes>
            <Toaster position="top-right" />
          </BrowserRouter>
        </MusicProvider>
      </ModeProvider>
    </AuthProvider>
  );
}

export default App;
