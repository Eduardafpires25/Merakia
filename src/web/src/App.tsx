import { Outlet, Route, Routes, useLocation } from "react-router-dom";
import { FloatingChatButton } from "./components/FloatingChatButton";
import { Header } from "./components/Header";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { IterationsProvider } from "./contexts/IterationsContext";
import { CartProvider } from "./contexts/CartContext";
import CartPage from "./pages/Cart";
import { ChatAIPage } from "./pages/ChatAI";
import { EmailVerificationPage } from "./pages/EmailVerification";
import { HomePage } from "./pages/Home";
import { LoginPage } from "./pages/Login";
import { MyOrdersPage } from "./pages/MyOrders";
import { OrderDetailPage } from "./pages/OrderDetail";
import { RegisterPage } from "./pages/Register";
import { SellerDashboardPage } from "./pages/SellerDashboard";
import { SellerDetailPage } from "./pages/SellerDetail";
import { SellersPage } from "./pages/Sellers";
import { UserProfilePage } from "./pages/UserProfile";

function MainLayout() {
  const location = useLocation();
  const hideChat = location.pathname.startsWith("/chat") || location.pathname.startsWith("/orders/");
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      {!hideChat && <FloatingChatButton />}
    </div>
  );
}

export default function App() {
  return (
    <CartProvider>
      <IterationsProvider>
        <Routes>

        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify-email" element={<EmailVerificationPage />} />

        <Route element={<MainLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/sellers" element={<SellersPage />} />
          <Route path="/sellers/:slug" element={<SellerDetailPage />} />
          <Route path="/chat" element={<ChatAIPage />} />

          <Route
            path="/cart"
            element={<ProtectedRoute><CartPage /></ProtectedRoute>}
          />

          <Route
            path="/orders"
            element={<ProtectedRoute><MyOrdersPage /></ProtectedRoute>}
          />
          <Route
            path="/orders/:id"
            element={<ProtectedRoute><OrderDetailPage /></ProtectedRoute>}
          />

          <Route
            path="/profile"
            element={<ProtectedRoute><UserProfilePage /></ProtectedRoute>}
          />

          <Route
            path="/seller-dashboard"
            element={<ProtectedRoute><SellerDashboardPage /></ProtectedRoute>}
          />

          <Route path="*" element={<HomePage />} />
        </Route>
      </Routes>
    </IterationsProvider>
    </CartProvider>
  );
}

