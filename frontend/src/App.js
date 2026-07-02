import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { MusicProvider } from "@/context/MusicContext";
import { Toaster } from "@/components/ui/sonner";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import CommandCenter from "@/pages/CommandCenter";
import KnowledgeRecords from "@/pages/KnowledgeRecords";
import KnowledgeRecordDetail from "@/pages/KnowledgeRecordDetail";
import TranslationEngine from "@/pages/TranslationEngine";
import ResearchCenter from "@/pages/ResearchCenter";
import VerificationCenter from "@/pages/VerificationCenter";
import ManufacturingOrders from "@/pages/ManufacturingOrders";
import ProductManufacturing from "@/pages/ProductManufacturing";
import ProductLibrary from "@/pages/ProductLibrary";
import ProductDetail from "@/pages/ProductDetail";
import DigitalWorkforce from "@/pages/DigitalWorkforce";
import Colleges from "@/pages/Colleges";
import CollegeWorkspace from "@/pages/CollegeWorkspace";
import Analytics from "@/pages/Analytics";
import Customers from "@/pages/Customers";
import UserManagement from "@/pages/UserManagement";
import Notifications from "@/pages/Notifications";
import Settings from "@/pages/Settings";
import SearchResults from "@/pages/SearchResults";
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

function App() {
  return (
    <AuthProvider>
      <MusicProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="command" element={<CommandCenter />} />
              <Route path="knowledge" element={<KnowledgeRecords />} />
              <Route path="knowledge/:id" element={<KnowledgeRecordDetail />} />
              <Route path="translation-engine" element={<TranslationEngine />} />
              <Route path="research" element={<ResearchCenter />} />
              <Route path="verification" element={<VerificationCenter />} />
              <Route path="manufacturing" element={<ManufacturingOrders />} />
              <Route path="manufacture" element={<ProductManufacturing />} />
              <Route path="products" element={<ProductLibrary />} />
              <Route path="products/:id" element={<ProductDetail />} />
              <Route path="workforce" element={<DigitalWorkforce />} />
              <Route path="colleges" element={<Colleges />} />
              <Route path="colleges/:id" element={<CollegeWorkspace />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="customers" element={<Customers />} />
              <Route path="users" element={<UserManagement />} />
              <Route path="notifications" element={<Notifications />} />
              <Route path="settings" element={<Settings />} />
              <Route path="search" element={<SearchResults />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Toaster position="top-right" />
        </BrowserRouter>
      </MusicProvider>
    </AuthProvider>
  );
}

export default App;
