import axios from "axios";
import {
  Image as ImageIcon, Loader2, Package, Palette, Pencil, Plus, Save, Store, Trash2, Upload, X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { Modal } from "../components/Modal";
import { PhoneInput } from "../components/PhoneInput";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { formatCategory, type OrderListResponse, ProductListItem, SellerCategory } from "../types/api";
import {
  isColorOption,
  parseColorValue,
  toPickerHex,
} from "../components/ColorSwatchSelector";

interface SellerProfile {
  id: string;
  store_name: string;
  slug: string;
  description?: string | null;
  category: SellerCategory;
  whatsapp?: string | null;
  instagram?: string | null;
  city?: string | null;
  state?: string | null;
  accepts_custom_designs: boolean;
  min_order_quantity: number;
  estimated_days?: number | null;
  is_open: boolean;
  logo_url?: string | null;
  banner_url?: string | null;
  pix_key?: string | null;
  pix_key_type?: string | null;
}

const categories: SellerCategory[] = [
  "mug", "shirt", "poster", "sticker", "keychain",
  "tote_bag", "ceramic", "woodwork", "jewelry", "other",
];

const BRAZILIAN_STATES = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
  "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

export function SellerDashboardPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<SellerProfile | null>(null);
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [orders, setOrders] = useState<OrderListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasProfile, setHasProfile] = useState<boolean | null>(null);
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<ProductListItem | undefined>();
  const [orderFilter, setOrderFilter] = useState<string>("analysis");
  const [showEditProfileModal, setShowEditProfileModal] = useState(false);

  const filteredOrders = orders?.items.filter((o) => {
    if (orderFilter === "all") return true;
    if (orderFilter === "customized") return o.product_type === "customized";
    if (orderFilter === "production") return o.status === "in_production";
    if (orderFilter === "analysis") return o.status === "in_analysis";
    if (orderFilter === "approved") return o.status === "approved";
    if (orderFilter === "paid") return o.status === "paid";
    if (orderFilter === "sent") return o.status === "sent";
    return true;
  }) || [];

  const handleOpenProductModal = (product?: ProductListItem) => {
    setEditingProduct(product);
    setShowProductModal(true);
  };

  const handleCloseProductModal = () => {
    setShowProductModal(false);
    setEditingProduct(undefined);
  };

  const refresh = async () => {
    try {
      const { data } = await api.get<SellerProfile>("/sellers/me/profile");
      setProfile(data);
      setHasProfile(true);
      const [pres, ores] = await Promise.all([
        api.get<{ items: ProductListItem[] }>("/sellers/me/products"),
        api.get<OrderListResponse>("/sellers/me/orders/"),
      ]);
      setProducts(pres.data.items);
      setOrders(ores.data);
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.status === 404) {
        setHasProfile(false);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  if (user && user.role !== "seller") {
    return <Navigate to="/" replace />;
  }

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-brand-500" /></div>;
  }

  if (hasProfile === false) {
    return <CreateProfileForm onCreated={refresh} />;
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-bold mb-1">Painel do Vendedor</h1>
      <p className="text-slate-500 dark:text-slate-400 mb-8">Gerencie loja, produtos e pedidos.</p>

      {profile && <ProfileCard profile={profile} onSaved={refresh} onEdit={() => setShowEditProfileModal(true)} />}

      <div className="grid md:grid-cols-2 gap-6 mt-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <Package className="w-5 h-5 text-brand-500" /> Produtos ({products.length})
            </h2>
            <button onClick={() => handleOpenProductModal()} className="btn-primary !py-2 !px-3 text-sm">
              <Plus className="w-4 h-4" /> Novo
            </button>
          </div>
          {products.length === 0 ? (
            <p className="text-sm text-slate-500">Nenhum produto cadastrado.</p>
          ) : (
            <div className="space-y-2">
              {products.map((p) => (
                <ProductRow key={p.id} product={p} onChanged={refresh} onEdit={handleOpenProductModal} />
              ))}
            </div>
          )}
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <Store className="w-5 h-5 text-brand-500" /> Pedidos recebidos ({filteredOrders.length})
            </h2>
          </div>
          
          <div className="flex flex-wrap gap-2 mb-4">
            {[
              { value: "all", label: "Todos" },
              { value: "analysis", label: "Em análise" },
              { value: "approved", label: "Aprovados" },
              { value: "paid", label: "Pagos" },
              { value: "production", label: "Em produção" },
              { value: "sent", label: "Enviados" },
            ].map((filter) => (
              <button
                key={filter.value}
                onClick={() => setOrderFilter(filter.value)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  orderFilter === filter.value
                    ? "bg-brand-500 text-white"
                    : "bg-slate-100 dark:bg-ink-700/60 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-ink-700"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>

          {!filteredOrders.length ? (
            <p className="text-sm text-slate-500 py-4">Nenhum pedido encontrado com este filtro.</p>
          ) : (
            <div className="space-y-2">
              {filteredOrders.slice(0, 10).map((o) => (
                <Link key={o.id} to={`/orders/${o.id}`}
                  className={`block p-4 rounded-lg border ${
                    o.status === "in_analysis" 
                      ? "bg-amber-50 dark:bg-amber-500/10 border-amber-300 dark:border-amber-500/50 hover:bg-amber-100 dark:hover:bg-amber-500/20" 
                      : "bg-white dark:bg-ink-800 border-slate-200 dark:border-ink-700 hover:bg-slate-50 dark:hover:bg-ink-700/40"
                  }`}>
                  <div className="flex justify-between items-start gap-2 mb-2">
                    <span className="font-medium truncate">{o.title}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      o.status === "in_analysis"
                        ? "bg-amber-200 dark:bg-amber-500/30 text-amber-800 dark:text-amber-300"
                        : "bg-slate-100 dark:bg-ink-700/60 text-slate-600 dark:text-slate-300"
                    } capitalize`}>
                      {o.status.replace("_", " ")}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                    <span>Qtd: {o.quantity}</span>
                    {o.estimated_price && <span>R$ {o.estimated_price}</span>}
                    {o.product_type && <span className="text-xs capitalize">{o.product_type}</span>}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      <ProductModal
        open={showProductModal}
        onClose={handleCloseProductModal}
        onCreated={refresh}
        product={editingProduct}
      />

      {profile && (
        <EditProfileModal
          open={showEditProfileModal}
          onClose={() => setShowEditProfileModal(false)}
          profile={profile}
          onSaved={refresh}
        />
      )}
    </div>
  );
}

// ============================================================================
// Create profile (quando seller ainda nao tem)
// ============================================================================

function CreateProfileForm({ onCreated }: { onCreated: () => void }) {
  const [storeName, setStoreName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<SellerCategory>("mug");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [estimated, setEstimated] = useState(7);
  const [pixKey, setPixKey] = useState("");
  const [pixKeyType, setPixKeyType] = useState("cpf");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      await api.post("/sellers/me/profile", {
        store_name: storeName,
        description: description || null,
        category,
        city: city || null,
        state: state || null,
        whatsapp: whatsapp || null,
        estimated_days: estimated,
        accepts_custom_designs: true,
        min_order_quantity: 1,
        pix_key: pixKey || null,
        pix_key_type: pixKeyType || null,
      });
      onCreated();
    } catch (err) {
      if (axios.isAxiosError(err)) setError(err.response?.data?.detail || "Falha ao criar.");
      else setError("Erro inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <h1 className="text-2xl font-bold mb-2">Configurar sua loja</h1>
      <p className="text-slate-500 dark:text-slate-400 mb-6">
        Preencha os dados da sua loja para começar a receber pedidos.
      </p>

      <form onSubmit={submit} className="card p-6 space-y-4">
        <div><label className="label">Nome da loja</label>
          <input required minLength={2} value={storeName} onChange={(e) => setStoreName(e.target.value)} className="input" />
        </div>
        <div><label className="label">Descrição</label>
          <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} className="input resize-none" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Categoria</label>
            <select value={category} onChange={(e) => setCategory(e.target.value as SellerCategory)} className="input">
              {categories.map((c) => <option key={c} value={c}>{formatCategory(c)}</option>)}
            </select>
          </div>
          <div><label className="label">Prazo (dias)</label>
            <input type="number" min={1} value={estimated} onChange={(e) => setEstimated(Number(e.target.value))} className="input" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Cidade</label><input value={city} onChange={(e) => setCity(e.target.value)} className="input" /></div>
          <div><label className="label">UF</label>
            <select value={state} onChange={(e) => setState(e.target.value)} className="input">
              <option value="">Selecione</option>
              {BRAZILIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
        <div><label className="label">WhatsApp</label><PhoneInput value={whatsapp} onChange={setWhatsapp} className="w-full" /></div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-ink-700/50 border border-slate-200 dark:border-ink-600">
          <div>
            <label className="label">Tipo de Chave PIX</label>
            <select value={pixKeyType} onChange={(e) => setPixKeyType(e.target.value)} className="input">
              <option value="cpf">CPF</option>
              <option value="cnpj">CNPJ</option>
              <option value="email">E-mail</option>
              <option value="phone">Telefone</option>
              <option value="random">Chave Aleatória</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="label">Chave PIX para Recebimento</label>
            <input
              value={pixKey}
              onChange={(e) => setPixKey(e.target.value)}
              placeholder="Digite sua chave PIX para repasse"
              className="input"
            />
          </div>
        </div>

        {error && <div className="text-sm text-red-500">{error}</div>}

        <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Criar loja
        </button>
      </form>
    </div>
  );
}

// ============================================================================
// Profile card com upload de logo/banner
// ============================================================================

function ProfileCard({ profile, onSaved, onEdit }: { profile: SellerProfile; onSaved: () => void; onEdit: () => void }) {
  const logoRef = useRef<HTMLInputElement>(null);
  const bannerRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState<"logo" | "banner" | null>(null);

  const upload = async (kind: "logo" | "banner", file: File) => {
    setUploading(kind);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await api.post(`/sellers/me/profile/${kind}`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      onSaved();
    } catch {
      alert("Falha no upload.");
    } finally {
      setUploading(null);
    }
  };

  return (
    <div className="card p-6">
      <div className="flex items-start gap-5 flex-wrap">
        <div className="relative">
          <div className="w-24 h-24 rounded-2xl bg-slate-100 dark:bg-ink-700/50 overflow-hidden flex items-center justify-center">
            {profile.logo_url ? (
              <img src={profile.logo_url} alt="logo" className="w-full h-full object-cover" />
            ) : (
              <Store className="w-10 h-10 text-slate-400" />
            )}
          </div>
          <button
            onClick={() => logoRef.current?.click()}
            disabled={uploading === "logo"}
            className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-brand-500 text-white flex items-center justify-center hover:bg-brand-600"
            aria-label="Trocar logo"
          >
            {uploading === "logo" ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
          </button>
          <input ref={logoRef} type="file" accept="image/*" hidden
            onChange={(e) => e.target.files?.[0] && upload("logo", e.target.files[0])} />
        </div>

        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-bold">{profile.store_name}</h2>
          <p className="text-brand-500 capitalize text-sm">{formatCategory(profile.category)}</p>
          {profile.description && <p className="text-sm text-slate-500 mt-1">{profile.description}</p>}

          {profile.pix_key ? (
            <div className="mt-2 text-xs flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
              <span>Chave PIX de Recebimento ({profile.pix_key_type?.toUpperCase() || "GERAL"}):</span>
              <span className="font-mono bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                {profile.pix_key}
              </span>
            </div>
          ) : (
            <div className="mt-2 text-xs text-amber-600 dark:text-amber-400 font-medium flex items-center gap-1">
              <span>⚠️ Nenhuma chave PIX configurada. Clique em "Editar infos" para cadastrar sua chave e receber repasses.</span>
            </div>
          )}

          <div className="flex gap-2 mt-3">
            <button onClick={() => bannerRef.current?.click()} disabled={uploading === "banner"}
              className="btn-outline !py-2 !px-3 text-sm disabled:opacity-60">
              {uploading === "banner" ? <Loader2 className="w-4 h-4 animate-spin" /> : <ImageIcon className="w-4 h-4" />}
              {profile.banner_url ? "Trocar banner" : "Adicionar banner"}
            </button>
            <button onClick={onEdit} className="btn-outline !py-2 !px-3 text-sm">
              <Pencil className="w-4 h-4" /> Editar infos
            </button>
            <input ref={bannerRef} type="file" accept="image/*" hidden
              onChange={(e) => e.target.files?.[0] && upload("banner", e.target.files[0])} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Edit profile modal
// ============================================================================

interface EditProfileModalProps {
  open: boolean;
  onClose: () => void;
  profile: SellerProfile;
  onSaved: () => void;
}

function EditProfileModal({ open, onClose, profile, onSaved }: EditProfileModalProps) {
  const [storeName, setStoreName] = useState(profile.store_name);
  const [description, setDescription] = useState(profile.description || "");
  const [category, setCategory] = useState(profile.category);
  const [city, setCity] = useState(profile.city || "");
  const [state, setState] = useState(profile.state || "");
  const [whatsapp, setWhatsapp] = useState(profile.whatsapp || "");
  const [instagram, setInstagram] = useState(profile.instagram || "");
  const [estimated, setEstimated] = useState(profile.estimated_days || 7);
  const [pixKey, setPixKey] = useState(profile.pix_key || "");
  const [pixKeyType, setPixKeyType] = useState(profile.pix_key_type || "cpf");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setStoreName(profile.store_name);
      setDescription(profile.description || "");
      setCategory(profile.category);
      setCity(profile.city || "");
      setState(profile.state || "");
      setWhatsapp(profile.whatsapp || "");
      setInstagram(profile.instagram || "");
      setEstimated(profile.estimated_days || 7);
      setPixKey(profile.pix_key || "");
      setPixKeyType(profile.pix_key_type || "cpf");
    }
  }, [open, profile]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.patch("/sellers/me/profile", {
        store_name: storeName,
        description: description || null,
        category,
        city: city || null,
        state: state || null,
        whatsapp: whatsapp || null,
        instagram: instagram || null,
        estimated_days: estimated,
        pix_key: pixKey || null,
        pix_key_type: pixKeyType || null,
      });
      onSaved();
      onClose();
    } catch (err) {
      if (axios.isAxiosError(err)) setError(err.response?.data?.detail || "Falha ao atualizar.");
      else setError("Erro inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Editar informações da loja">
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">Nome da loja</label>
          <input value={storeName} onChange={(e) => setStoreName(e.target.value)} className="input" required />
        </div>
        <div>
          <label className="label">Descrição</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="input" rows={3} />
        </div>
        <div>
          <label className="label">Categoria</label>
          <select value={category} onChange={(e) => setCategory(e.target.value as SellerCategory)} className="input">
            {categories.map((c) => <option key={c} value={c}>{formatCategory(c)}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Prazo (dias)</label>
          <input type="number" min={1} value={estimated} onChange={(e) => setEstimated(Number(e.target.value))} className="input" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div><label className="label">Cidade</label><input value={city} onChange={(e) => setCity(e.target.value)} className="input" /></div>
          <div><label className="label">UF</label>
            <select value={state} onChange={(e) => setState(e.target.value)} className="input">
              <option value="">Selecione</option>
              {BRAZILIAN_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
        <div><label className="label">WhatsApp</label><PhoneInput value={whatsapp} onChange={setWhatsapp} className="w-full" /></div>
        <div><label className="label">Instagram</label><input value={instagram} onChange={(e) => setInstagram(e.target.value)} className="input" /></div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-50 dark:bg-ink-700/50 border border-slate-200 dark:border-ink-600">
          <div>
            <label className="label">Tipo de Chave PIX</label>
            <select value={pixKeyType} onChange={(e) => setPixKeyType(e.target.value)} className="input">
              <option value="cpf">CPF</option>
              <option value="cnpj">CNPJ</option>
              <option value="email">E-mail</option>
              <option value="phone">Telefone</option>
              <option value="random">Chave Aleatória</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="label">Chave PIX para Recebimento</label>
            <input
              value={pixKey}
              onChange={(e) => setPixKey(e.target.value)}
              placeholder="Digite sua chave PIX para repasses"
              className="input"
            />
          </div>
        </div>

        {error && <div className="text-sm text-red-500">{error}</div>}

        <div className="flex gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-outline flex-1">Cancelar</button>
          <button type="submit" disabled={loading} className="btn-primary flex-1 disabled:opacity-60">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Salvar
          </button>
        </div>
      </form>
    </Modal>
  );
}

// ============================================================================
// Product row + create modal
// ============================================================================

interface ProductRowProps {
  product: ProductListItem;
  onChanged: () => void;
  onEdit: (product: ProductListItem) => void;
}

function ProductRow({ product, onChanged, onEdit }: ProductRowProps) {
  const [busy, setBusy] = useState(false);

  const remove = async () => {
    if (!confirm(`Remover "${product.name}"?`)) return;
    setBusy(true);
    try {
      await api.delete(`/sellers/me/products/${product.id}`);
      onChanged();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 dark:border-ink-700">
      <div className="w-12 h-12 rounded-lg bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center overflow-hidden shrink-0">
        {product.cover_url ? (
          <img src={product.cover_url} alt={product.name} className="w-full h-full object-cover" />
        ) : (
          <Package className="w-5 h-5 text-slate-400" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{product.name}</p>
        {product.base_price && <p className="text-xs text-brand-500">R$ {product.base_price}</p>}
      </div>
      <div className="flex gap-1">
        <button onClick={() => onEdit(product)} disabled={busy}
          className="p-2 text-brand-500 hover:bg-brand-50 dark:hover:bg-brand-500/10 rounded-lg disabled:opacity-50">
          <Pencil className="w-4 h-4" />
        </button>
        <button onClick={remove} disabled={busy}
          className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg disabled:opacity-50">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

interface ColorItem {
  id: string;
  name: string;
  hex: string;
}

interface CustomizationOption {
  id: string;
  name: string;
  isColor: boolean;
  values: string[];
  colors: ColorItem[];
}

const createColorItem = (name = "", hex = "#3B82F6"): ColorItem => ({
  id: `c_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
  name,
  hex,
});

const createOption = (name = "", isColor = false, values: string[] = [""], colors: ColorItem[] = []): CustomizationOption => ({
  id: `opt_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`,
  name,
  isColor,
  values,
  colors,
});

interface ProductModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  product?: ProductListItem;
}

function ProductModal({ open, onClose, onCreated, product }: ProductModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [basePrice, setBasePrice] = useState("");
  const [isCustomizable, setIsCustomizable] = useState(false);
  const [customizationOptions, setCustomizationOptions] = useState<CustomizationOption[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const imageRef = useRef<HTMLInputElement>(null);

  // Reset form when modal opens/closes or product changes
  useEffect(() => {
    if (open) {
      if (product) {
        // Edit mode
        setName(product.name);
        setDescription(product.description || "");
        setBasePrice(product.base_price ? String(product.base_price) : "");
        setIsCustomizable(product.is_customizable);
        if (product.customization_options && Object.keys(product.customization_options).length > 0) {
          const opts: CustomizationOption[] = Object.entries(product.customization_options).map(([optName, rawValues], idx) => {
            const valuesArr = Array.isArray(rawValues) ? rawValues : [rawValues];
            const isColor = isColorOption(optName, valuesArr);
            if (isColor) {
              const colorList = valuesArr.map((v, cIdx) => {
                const parsed = parseColorValue(v);
                return {
                  id: `c_${idx}_${cIdx}_${Math.random().toString(36).substring(2, 8)}`,
                  name: parsed.name === parsed.hex ? "" : parsed.name,
                  hex: parsed.hex || "#3B82F6",
                };
              });
              return {
                id: `opt_${idx}_${Math.random().toString(36).substring(2, 8)}`,
                name: optName,
                isColor: true,
                values: [],
                colors: colorList.length > 0 ? colorList : [createColorItem("", "#3B82F6")],
              };
            }
            return {
              id: `opt_${idx}_${Math.random().toString(36).substring(2, 8)}`,
              name: optName,
              isColor: false,
              values: valuesArr.length > 0 ? valuesArr : [""],
              colors: [],
            };
          });
          setCustomizationOptions(opts);
        } else {
          setCustomizationOptions([createOption("", false, [""])]);
        }
        setImagePreview(product.cover_url || null);
      } else {
        // Create mode
        setName("");
        setDescription("");
        setBasePrice("");
        setIsCustomizable(false);
        setCustomizationOptions([]);
        setImageFile(null);
        setImagePreview(null);
      }
    }
  }, [open, product]);

  const addOption = () => {
    setCustomizationOptions([...customizationOptions, createOption("", false, [""])]);
  };

  const addColorOption = () => {
    setCustomizationOptions([
      ...customizationOptions,
      createOption("Cores disponíveis", true, [], [
        createColorItem("Branco", "#FFFFFF"),
        createColorItem("Preto", "#1F2937"),
        createColorItem("Vermelho", "#EF4444"),
      ]),
    ]);
  };

  const toggleOptionType = (optId: string) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        if (opt.isColor) {
          // Switch from color to simple text values
          const textValues = opt.colors
            .map((c) => {
              let h = c.hex.trim();
              if (h && !h.startsWith("#")) h = `#${h}`;
              if (c.name.trim() && h) return `${c.name.trim()} (${h.toUpperCase()})`;
              return c.name.trim() || h || "";
            })
            .filter(Boolean);
          return {
            ...opt,
            isColor: false,
            values: textValues.length > 0 ? textValues : [""],
            colors: [],
          };
        } else {
          // Switch from text to color palette
          const colorItems = opt.values.map((v) => {
            const parsed = parseColorValue(v);
            return createColorItem(parsed.name === parsed.hex ? "" : parsed.name, parsed.hex);
          });
          return {
            ...opt,
            isColor: true,
            values: [],
            colors: colorItems.length > 0 ? colorItems : [createColorItem("", "#3B82F6")],
          };
        }
      })
    );
  };

  const removeOption = (optId: string) => {
    setCustomizationOptions(customizationOptions.filter((opt) => opt.id !== optId));
  };

  const updateOptionName = (optId: string, value: string) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        return { ...opt, name: value };
      })
    );
  };

  const addColorItem = (optId: string) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        return {
          ...opt,
          colors: [...opt.colors, createColorItem("", "#3B82F6")],
        };
      })
    );
  };

  const updateColorName = (optId: string, colorId: string, name: string) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        return {
          ...opt,
          colors: opt.colors.map((c) => (c.id === colorId ? { ...c, name } : c)),
        };
      })
    );
  };

  const updateColorHex = (optId: string, colorId: string, hex: string) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        return {
          ...opt,
          colors: opt.colors.map((c) => (c.id === colorId ? { ...c, hex } : c)),
        };
      })
    );
  };

  const removeColorItem = (optId: string, colorId: string) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        return {
          ...opt,
          colors: opt.colors.filter((c) => c.id !== colorId),
        };
      })
    );
  };

  const addValue = (optId: string) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        return { ...opt, values: [...opt.values, ""] };
      })
    );
  };

  const updateValue = (optId: string, valueIndex: number, value: string) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        const newValues = [...opt.values];
        newValues[valueIndex] = value;
        return { ...opt, values: newValues };
      })
    );
  };

  const removeValue = (optId: string, valueIndex: number) => {
    setCustomizationOptions((prev) =>
      prev.map((opt) => {
        if (opt.id !== optId) return opt;
        return { ...opt, values: opt.values.filter((_, i) => i !== valueIndex) };
      })
    );
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError(null);
    try {
      let options: Record<string, string[]> = {};
      if (isCustomizable) {
        for (const opt of customizationOptions) {
          const trimmedName = opt.name.trim();
          if (!trimmedName) continue;

          if (opt.isColor) {
            const validColors = opt.colors
              .filter((c) => c.name.trim() || c.hex.trim())
              .map((c) => {
                let cleanHex = c.hex.trim();
                if (cleanHex && !cleanHex.startsWith("#")) cleanHex = `#${cleanHex}`;
                cleanHex = cleanHex.toUpperCase();
                const cleanName = c.name.trim();

                if (cleanName && cleanHex && cleanName.toUpperCase() !== cleanHex) {
                  return `${cleanName} (${cleanHex})`;
                }
                return cleanName || cleanHex || "#000000";
              });

            if (validColors.length > 0) {
              options[trimmedName] = validColors;
            }
          } else {
            const validValues = opt.values.map((v) => v.trim()).filter(Boolean);
            if (validValues.length > 0) {
              options[trimmedName] = validValues;
            }
          }
        }
      }

      if (product) {
        // Edit mode
        await api.patch(`/sellers/me/products/${product.id}`, {
          name,
          description: description || null,
          attributes: {},
          is_customizable: isCustomizable,
          customization_options: isCustomizable ? options : {},
          base_price: basePrice ? Number(basePrice) : null,
        });
        
        // Upload image if provided
        if (imageFile) {
          const formData = new FormData();
          formData.append("file", imageFile);
          await api.post(`/sellers/me/products/${product.id}/images`, formData, {
            headers: { "Content-Type": "multipart/form-data" }
          });
        }
      } else {
        // Create mode
        const { data } = await api.post("/sellers/me/products", {
          name,
          description: description || null,
          attributes: {},
          is_customizable: isCustomizable,
          customization_options: isCustomizable ? options : {},
          base_price: basePrice ? Number(basePrice) : null,
        });
        
        // Upload image if provided
        if (imageFile) {
          const formData = new FormData();
          formData.append("file", imageFile);
          await api.post(`/sellers/me/products/${data.id}/images`, formData, {
            headers: { "Content-Type": "multipart/form-data" }
          });
        }
      }

      setName(""); setDescription(""); setBasePrice(""); setIsCustomizable(false); setCustomizationOptions([]);
      setImageFile(null); setImagePreview(null);
      onCreated();
      onClose();
    } catch (err) {
      if (axios.isAxiosError(err)) setError(err.response?.data?.detail || "Falha.");
      else setError("Erro inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title={product ? "Editar produto" : "Novo produto"}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">Imagem do produto</label>
          <div className="flex items-center gap-4">
            {imagePreview ? (
              <div className="relative w-24 h-24 rounded-lg overflow-hidden border border-slate-200 dark:border-ink-700">
                <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => { setImageFile(null); setImagePreview(null); }}
                  className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <div className="w-24 h-24 rounded-lg border-2 border-dashed border-slate-300 dark:border-ink-700 flex items-center justify-center">
                <ImageIcon className="w-8 h-8 text-slate-400" />
              </div>
            )}
            <div>
              <input
                ref={imageRef}
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => imageRef.current?.click()}
                className="btn-outline !py-2 !px-3 text-sm"
              >
                {imagePreview ? "Trocar imagem" : "Adicionar imagem"}
              </button>
            </div>
          </div>
        </div>
        <div><label className="label">Nome</label>
          <input required minLength={2} value={name} onChange={(e) => setName(e.target.value)} className="input" placeholder="Ex.: Caneca 350ml branca" />
        </div>
        <div><label className="label">Descrição</label>
          <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} className="input resize-none" />
        </div>
        <div><label className="label">Preço base (R$)</label>
          <input type="number" step="0.01" min="0" value={basePrice} onChange={(e) => setBasePrice(e.target.value)} className="input" placeholder="29.90" />
        </div>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="isCustomizable"
            checked={isCustomizable}
            onChange={(e) => setIsCustomizable(e.target.checked)}
            className="w-4 h-4 rounded border-slate-300 text-brand-500 focus:ring-brand-500"
          />
          <label htmlFor="isCustomizable" className="label !mb-0">Produto personalizável</label>
        </div>
        {isCustomizable && (
          <div className="space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <label className="label !mb-0">Opções de personalização</label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={addColorOption}
                  className="text-xs text-brand-500 hover:text-brand-600 font-medium inline-flex items-center gap-1 bg-brand-50 dark:bg-brand-500/10 px-2.5 py-1 rounded-lg border border-brand-200 dark:border-brand-500/30"
                >
                  <Palette className="w-3.5 h-3.5" /> + Cartela de cores
                </button>
                <button
                  type="button"
                  onClick={addOption}
                  className="text-xs text-brand-500 hover:text-brand-600 font-medium py-1 px-2"
                >
                  + Outra opção
                </button>
              </div>
            </div>
            {customizationOptions.map((option) => (
              <div key={option.id} className="p-3.5 rounded-xl border border-slate-200 dark:border-ink-700 space-y-3 bg-white dark:bg-ink-800">
                <div className="flex items-center gap-2">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={option.name}
                      onChange={(e) => updateOptionName(option.id, e.target.value)}
                      className="input w-full !py-1.5"
                      placeholder="Nome da opção (ex: Cor da caneca, Tamanho)"
                    />
                  </div>

                  {/* Botão de alternar entre paleta de cores e texto simples */}
                  <button
                    type="button"
                    onClick={() => toggleOptionType(option.id)}
                    className={`text-[11px] font-medium px-2.5 py-1 rounded-md border shrink-0 flex items-center gap-1.5 transition-colors ${
                      option.isColor
                        ? "bg-brand-50 dark:bg-brand-500/15 text-brand-600 dark:text-brand-400 border-brand-200 dark:border-brand-500/30 hover:bg-brand-100"
                        : "bg-slate-100 dark:bg-ink-700 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-ink-600 hover:bg-slate-200"
                    }`}
                    title={option.isColor ? "Clique para converter em lista de texto" : "Clique para converter em paleta de cores"}
                  >
                    <Palette className="w-3.5 h-3.5" />
                    {option.isColor ? "Paleta de Cores" : "Converter p/ Cor"}
                  </button>

                  <button
                    type="button"
                    onClick={() => removeOption(option.id)}
                    className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg shrink-0"
                    title="Remover opção"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {option.isColor ? (
                  <div className="space-y-2 pt-1 border-t border-slate-100 dark:border-ink-700/60">
                    <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 flex items-center justify-between">
                      <span>Cores configuradas (Seletor + Nome + Hex)</span>
                      <span>{option.colors.length} {option.colors.length === 1 ? "cor" : "cores"}</span>
                    </div>

                    <div className="space-y-2">
                      {option.colors.map((color) => (
                        <div
                          key={color.id}
                          className="flex items-center gap-2 bg-slate-50 dark:bg-ink-700/40 p-2 rounded-xl border border-slate-200/80 dark:border-ink-600"
                        >
                          {/* Seletor nativo de cor */}
                          <div className="relative shrink-0 flex items-center">
                            <input
                              type="color"
                              value={toPickerHex(color.hex)}
                              onChange={(e) => {
                                updateColorHex(option.id, color.id, e.target.value.toUpperCase());
                              }}
                              className="w-9 h-9 rounded-lg cursor-pointer border border-slate-300 dark:border-ink-600 bg-transparent p-0.5"
                              title="Clique para escolher a cor na paleta visual"
                            />
                          </div>

                          {/* Nome comercial da cor */}
                          <input
                            type="text"
                            value={color.name}
                            onChange={(e) => updateColorName(option.id, color.id, e.target.value)}
                            placeholder="Nome da cor (ex: Azul Petróleo)"
                            className="input flex-1 !py-1.5 text-sm"
                          />

                          {/* Código Hexadecimal */}
                          <input
                            type="text"
                            value={color.hex}
                            maxLength={7}
                            onChange={(e) => {
                              let val = e.target.value;
                              if (val && !val.startsWith("#")) val = "#" + val;
                              updateColorHex(option.id, color.id, val.toUpperCase());
                            }}
                            placeholder="#000000"
                            className="input w-24 !py-1.5 text-xs font-mono uppercase text-center shrink-0"
                            title="Código hexadecimal (#RRGGBB)"
                          />

                          {/* Botão de exclusão */}
                          <button
                            type="button"
                            onClick={() => removeColorItem(option.id, color.id)}
                            className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg shrink-0 transition-colors"
                            title="Remover cor"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>

                    <button
                      type="button"
                      onClick={() => addColorItem(option.id)}
                      className="text-xs text-brand-500 hover:text-brand-600 font-medium py-1.5 px-3 inline-flex items-center gap-1.5 border border-dashed border-brand-300 dark:border-brand-500/40 rounded-lg hover:bg-brand-50/50 dark:hover:bg-brand-500/10 transition-colors"
                    >
                      <Plus className="w-3.5 h-3.5" /> Adicionar nova cor à cartela
                    </button>
                  </div>
                ) : (
                  <div className="space-y-1.5 pt-1 border-t border-slate-100 dark:border-ink-700/60">
                    {option.values.map((value, valueIndex) => (
                      <div key={valueIndex} className="flex items-center gap-2">
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => updateValue(option.id, valueIndex, e.target.value)}
                          className="input flex-1 !py-1.5"
                          placeholder="Valor (ex: 250ml, Cerâmica)"
                        />
                        <button
                          type="button"
                          onClick={() => removeValue(option.id, valueIndex)}
                          className="p-1 text-slate-400 hover:text-red-500 rounded"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => addValue(option.id)}
                      className="text-sm text-slate-500 hover:text-brand-500"
                    >
                      + Adicionar valor
                    </button>
                  </div>
                )}
              </div>
            ))}
            {customizationOptions.length === 0 && (
              <p className="text-sm text-slate-500 italic">Nenhuma opção adicionada</p>
            )}
          </div>
        )}
        {error && <div className="text-sm text-red-500">{error}</div>}
        <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          {product ? "Salvar produto" : "Criar produto"}
        </button>
      </form>
    </Modal>
  );
}
