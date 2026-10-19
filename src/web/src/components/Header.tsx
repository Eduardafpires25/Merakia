import { AlertCircle, ChevronDown, LogOut, ShoppingCart, User as UserIcon, X, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { useIterations } from "../contexts/IterationsContext";
import { ThemeToggle } from "./ThemeToggle";
import { Logo } from "./Logo";
import { NavLink, useNavigate } from "react-router-dom";
import { useCart } from "../hooks/useCart";

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `relative px-2 py-1 text-sm font-medium transition-colors
         ${isActive
           ? "text-brand-500 after:absolute after:left-0 after:right-0 after:-bottom-1 after:h-[2px] after:bg-brand-500 after:rounded-full"
           : "text-slate-700 hover:text-brand-500 dark:text-slate-300 dark:hover:text-brand-400"
         }`
      }
    >
      {children}
    </NavLink>
  );
}

export function Header() {
  const { user, logout } = useAuth();
  const { cart } = useCart();
  const { iterationsLimit } = useIterations();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [showEmailBanner, setShowEmailBanner] = useState(true);

  const initials = user
    ? user.name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((p) => p[0]?.toUpperCase())
        .join("")
    : "";

  const handleLogout = async () => {
    await logout();
    setMenuOpen(false);
    navigate("/");
  };

  const shouldShowEmailBanner = user && !user.email_verified && showEmailBanner;

  return (
    <>
      {shouldShowEmailBanner && (
        <div className="bg-amber-500 text-white text-sm px-4 py-2 flex items-center justify-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>Verifique seu email para acessar todas as funcionalidades.</span>
          <Link to="/verify-email" className="font-semibold underline hover:no-underline">
            Verificar agora
          </Link>
          <button
            onClick={() => setShowEmailBanner(false)}
            className="ml-2 hover:bg-amber-600 rounded p-0.5"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      <header className="sticky top-0 z-30 backdrop-blur-md bg-white/80 dark:bg-ink-900/80 border-b border-slate-200 dark:border-ink-700">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Logo />

        <nav className="hidden md:flex items-center gap-8">
          <NavItem to="/sellers">Produtos</NavItem>
          <NavItem to="/chat">Chat com IA</NavItem>
          {user && <NavItem to="/orders">Meus pedidos</NavItem>}
          {user && user.role === "seller" && <NavItem to="/seller-dashboard">Meu painel</NavItem>}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />

          {user && (
            <Link to="/cart" className="relative p-2 rounded-full hover:bg-slate-100 dark:hover:bg-ink-700/60 transition-colors">
              <ShoppingCart className="w-5 h-5 text-slate-700 dark:text-slate-200" />
              {cart && cart.total_items > 0 && (
                <span className="absolute -top-1 -right-1 bg-brand-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {cart.total_items > 9 ? "9+" : cart.total_items}
                </span>
              )}
            </Link>
          )}

          {user ? (
            <>
              <div className="relative">
                <button
                  onClick={() => setMenuOpen((o) => !o)}
                  className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-full
                             hover:bg-slate-100 dark:hover:bg-ink-700/60 transition-colors"
                >
                  <div className="w-9 h-9 rounded-full bg-brand-500 text-white flex items-center justify-center font-semibold text-sm overflow-hidden">
                    {user.avatar_url ? (
                      <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                      initials
                    )}
                  </div>
                  <span className="hidden sm:inline text-sm text-slate-700 dark:text-slate-200">
                    Minha conta
                  </span>
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                </button>

                {menuOpen && (
                  <div
                    className="absolute right-0 top-full mt-2 w-56 card p-2 shadow-xl"
                    onMouseLeave={() => setMenuOpen(false)}
                  >
                    <div className="px-3 py-2 text-xs text-slate-500 dark:text-slate-400 truncate overflow-hidden">
                      {user.email}
                    </div>
                    {iterationsLimit && iterationsLimit.enabled && (
                      <div className="px-3 py-2 mb-2 bg-brand-50 dark:bg-brand-500/10 rounded-lg">
                        <div className="flex items-center gap-2 text-xs font-medium text-brand-600 dark:text-brand-400">
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>{iterationsLimit.remaining} iterações restantes hoje</span>
                        </div>
                      </div>
                    )}
                    <Link
                      to="/profile"
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm
                                 hover:bg-slate-100 dark:hover:bg-ink-700/60"
                      onClick={() => setMenuOpen(false)}
                    >
                      <UserIcon className="w-4 h-4" /> Perfil
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm
                                 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10"
                    >
                      <LogOut className="w-4 h-4" /> Sair
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login" className="btn-ghost">Entrar</Link>
              <Link to="/register" className="btn-primary !py-2 !px-4">Cadastrar</Link>
            </div>
          )}
        </div>
      </div>
    </header>
    </>
  );
}
