import { ArrowRight, Loader2, Package, Store } from "lucide-react";
import { LogoIcon } from "../components/LogoIcon";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FeatureBar } from "../components/FeatureBar";
import { api } from "../lib/api";
import { formatCategory, ProductListItem, SellerListItem } from "../types/api";

export function HomePage() {
  const [sellers, setSellers] = useState<SellerListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSellers = async () => {
      try {
        const { data } = await api.get<{ items: SellerListItem[] }>("/sellers", {
          params: { limit: 6, active_only: true }
        });
        setSellers(data.items);
      } catch (e) {
        console.error("Failed to fetch sellers:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchSellers();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-ink-900 relative overflow-hidden">
      {/* Fumaça nos cantos */}
      <div className="fixed top-0 left-0 w-96 h-96 bg-gradient-to-br from-brand-500/8 via-accent-500/5 to-brand-300/8 dark:from-brand-500/10 dark:via-accent-500/5 dark:to-brand-300/10 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 animate-pulse" style={{ animationDuration: '6s' }} />
      <div className="fixed top-0 right-0 w-80 h-80 bg-gradient-to-bl from-accent-500/8 via-brand-500/5 to-brand-500/8 dark:from-accent-500/10 dark:via-brand-500/5 dark:to-brand-500/10 rounded-full blur-3xl translate-x-1/2 -translate-y-1/2 animate-pulse" style={{ animationDuration: '7s', animationDelay: '1s' }} />
      <div className="fixed bottom-0 left-0 w-72 h-72 bg-gradient-to-tr from-accent-500/8 via-brand-500/5 to-brand-300/8 dark:from-accent-500/10 dark:via-brand-500/5 dark:to-brand-300/10 rounded-full blur-3xl -translate-x-1/2 translate-y-1/2 animate-pulse" style={{ animationDuration: '8s', animationDelay: '2s' }} />
      <div className="fixed bottom-0 right-0 w-64 h-64 bg-gradient-to-tl from-brand-500/8 via-accent-500/5 to-brand-300/8 dark:from-brand-500/10 dark:via-accent-500/5 dark:to-brand-300/10 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 animate-pulse" style={{ animationDuration: '5s', animationDelay: '0.5s' }} />

      <main className="max-w-7xl mx-auto px-6 py-12 relative z-10">
        {/* Hero Section */}
        <section className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-4xl md:text-5xl font-extrabold leading-tight tracking-tight">
              Pedidos personalizáveis<br />com <span className="text-brand-500">IA</span>
            </h1>
            <p className="mt-4 text-slate-600 dark:text-slate-300 max-w-md leading-relaxed">
              Crie artes únicas, do seu jeito. Escolha uma loja e personalize como quiser.
            </p>
            <Link to="/sellers" className="btn-primary mt-8">
              <LogoIcon className="w-4 h-4" />
              Explorar lojas
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Mock visual da caneca */}
          <div className="relative h-[380px] flex items-center justify-center">
          <div className="relative flex flex-col items-center gap-2">
            {/* Fumaça animada */}
            <div className="absolute inset-0 -z-10">
              {/* Camadas principais */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-gradient-to-br from-brand-500/20 via-accent-500/15 to-brand-300/20 dark:from-brand-500/30 dark:via-accent-500/20 dark:to-brand-300/30 rounded-full blur-3xl animate-pulse" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-gradient-to-tr from-accent-500/25 via-brand-500/15 to-brand-500/20 dark:from-accent-500/40 dark:via-brand-500/20 dark:to-brand-500/30 rounded-full blur-2xl animate-pulse" style={{ animationDuration: '3s' }} />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-gradient-to-bl from-accent-500/20 via-brand-500/15 to-brand-300/20 dark:from-accent-500/30 dark:via-brand-500/20 dark:to-brand-300/30 rounded-full blur-xl animate-pulse" style={{ animationDuration: '5s' }} />
              {/* Camadas externas */}
              <div className="absolute top-1/3 left-1/3 w-40 h-40 bg-gradient-to-r from-brand-500/15 via-accent-500/10 to-brand-300/15 dark:from-brand-500/20 dark:via-accent-500/15 dark:to-brand-300/20 rounded-full blur-2xl animate-pulse" style={{ animationDuration: '4s', animationDelay: '1s' }} />
              <div className="absolute bottom-1/3 right-1/3 w-36 h-36 bg-gradient-to-l from-accent-500/15 via-brand-500/10 to-brand-300/15 dark:from-accent-500/20 dark:via-brand-500/15 dark:to-brand-300/20 rounded-full blur-2xl animate-pulse" style={{ animationDuration: '4.5s', animationDelay: '0.5s' }} />
              <div className="absolute top-1/4 right-1/4 w-24 h-24 bg-gradient-to-bl from-accent-500/12 via-brand-500/8 to-brand-500/12 dark:from-accent-500/15 dark:via-brand-500/10 dark:to-brand-500/15 rounded-full blur-xl animate-pulse" style={{ animationDuration: '3.5s', animationDelay: '1.5s' }} />
            </div>
            <LogoIcon className="w-16 h-16" />
            <div className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-slate-900 via-brand-500 to-accent-500 dark:from-white dark:via-brand-400 dark:to-accent-400 bg-clip-text text-transparent">
              MeraK<span className="text-accent-500 dark:text-accent-400">ia</span>
            </div>
          </div>
        </div>
      </section>

      {/* Lojas com produtos personalizáveis */}
      <section className="mt-12">
        <div className="text-center">
          <h2 className="text-2xl md:text-3xl font-bold">Lojas com personalização</h2>
          <p className="text-slate-500 dark:text-slate-400 mt-2">
            Descubra lojas que aceitam criar produtos personalizados com IA.
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
          </div>
        ) : sellers.length === 0 ? (
          <div className="card p-10 text-center text-slate-500 mt-8">
            <Store className="w-10 h-10 mx-auto mb-2 text-slate-300 dark:text-ink-600" />
            Nenhuma loja disponível no momento.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mt-8">
            {sellers
              .filter(s => s.accepts_custom_designs)
              .map((seller) => (
              <Link
                key={seller.id}
                to={`/sellers/${seller.slug}`}
                className="card p-5 flex flex-col gap-3 hover:shadow-lg transition-shadow"
              >
                <div className="aspect-square w-full rounded-xl bg-gradient-to-br from-brand-500/20 to-purple-600/20 flex items-center justify-center">
                  {seller.logo_url ? (
                    <img src={seller.logo_url} alt={seller.store_name} className="w-full h-full rounded-xl object-cover" />
                  ) : (
                    <Store className="w-16 h-16 text-brand-500" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold">{seller.store_name}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{formatCategory(seller.category)}</p>
                  {seller.city && (
                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{seller.city}</p>
                  )}
                </div>
                <div className="mt-auto pt-2">
                  <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-brand-100 dark:bg-brand-500/20 text-brand-600 dark:text-brand-400">
                    Aceita personalização
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Features */}
      <section className="mt-10">
        <FeatureBar />
      </section>
      </main>
    </div>
  );
}
