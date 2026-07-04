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
import ConsumerHome from "@/pages/consumer/ConsumerHome";
import ConsumerLearn from "@/pages/consumer/ConsumerLearn";
import ConsumerMyLearning from "@/pages/consumer/ConsumerMyLearning";
import ConsumerFavorites from "@/pages/consumer/ConsumerFavorites";
import ConsumerCertificates from "@/pages/consumer/ConsumerCertificates";
import ConsumerPathways from "@/pages/consumer/ConsumerPathways";
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
        <Route path="translation-engine" element={<TranslationEngine />} />
        <Route path="research" element={<ResearchCenter />} />
        <Route path="verification" element={<VerificationCenter />} />
        <Route path="verification-team" element={<VerificationTeam />} />
        <Route path="manufacturing" element={<ManufacturingOrders />} />
        <Route path="orchestrator" element={<Orchestrator />} />
        <Route path="manufacture" element={<ProductManufacturing />} />
        <Route path="manufacturing-studio" element={<ManufacturingStudio />} />
        <Route path="products" element={<ProductLibrary />} />
        <Route path="products/:id" element={<ProductDetail />} />
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
        <Route path="manufacturing-economics" element={<ManufacturingEconomics />} />
        <Route path="portability" element={<PortabilityCenter />} />
        <Route path="store" element={<Store />} />
        <Route path="checkout/success" element={<CheckoutSuccess />} />
        <Route path="command-center" element={<EnterpriseCommandCenter />} />
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

function ModeRouter() {
  const { user, loading } = useAuth();
  const { isConsumer } = useMode();
  if (loading)
    return <div className="min-h-screen flex items-center justify-center"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>;
  if (!user)
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
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
