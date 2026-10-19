import { Loader2, Search, Star, Store } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { formatCategory } from "../types/api";
import type { SellerListResponse } from "../types/api";

export function SellersPage() {
  const [data, setData] = useState<SellerListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    const params = search ? { search } : {};
    api.get<SellerListResponse>("/sellers/", { params })
      .then(({ data }) => active && setData(data))
      .catch(() => active && setError("Erro ao carregar lojas."))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [search]);

  const items = useMemo(() => data?.items ?? [], [data]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold">Lojas</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Encontre vendedores artesanais para seu pedido personalizado.
          </p>
        </div>

        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nome ou cidade"
            className="input pl-9 w-72"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        </div>
      ) : error ? (
        <div className="text-center text-red-500 py-10">{error}</div>
      ) : items.length === 0 ? (
        <div className="text-center text-slate-500 py-10">Nenhuma loja encontrada.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {items.map((s) => (
            <Link
              key={s.id}
              to={`/sellers/${s.slug}`}
              className="card p-5 flex gap-4 hover:-translate-y-0.5 transition-transform"
            >
              <div className="w-16 h-16 rounded-xl bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center overflow-hidden shrink-0">
                {s.logo_url ? (
                  <img src={s.logo_url} alt={s.store_name} className="w-full h-full object-cover" />
                ) : (
                  <Store className="w-7 h-7 text-slate-400" />
                )}
              </div>
              <div className="min-w-0">
                <h3 className="font-semibold truncate">{s.store_name}</h3>
                <div className="flex items-center gap-2 mt-0.5">
                  <p className="text-xs text-brand-500">{formatCategory(s.category)}</p>
                  <span className="text-slate-300 dark:text-ink-600">•</span>
                  <div className="flex items-center gap-1 text-xs text-amber-500 font-semibold">
                    <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                    <span>{s.average_rating ? s.average_rating.toFixed(1) : "Novo"}</span>
                    <span className="text-slate-400 font-normal">
                      ({s.total_reviews ?? 0})
                    </span>
                  </div>
                </div>

                {s.description && (
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                    {s.description}
                  </p>
                )}
                {s.city && (
                  <p className="text-xs text-slate-400 mt-1">
                    {s.city}{s.state ? ` - ${s.state}` : ""}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
