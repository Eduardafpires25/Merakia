import axios from "axios";
import { Camera, Loader2, MapPin, Save, Sparkles, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useIterations } from "../contexts/IterationsContext";
import { PhoneInput } from "../components/PhoneInput";

const BRAZILIAN_STATES = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
  "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

export function UserProfilePage() {
  const { user, refresh } = useAuth();
  const { iterationsLimit } = useIterations();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [zipCode, setZipCode] = useState(user?.zip_code ?? "");
  const [address, setAddress] = useState(user?.address ?? "");
  const [number, setNumber] = useState(user?.number ?? "");
  const [complement, setComplement] = useState(user?.complement ?? "");
  const [neighborhood, setNeighborhood] = useState(user?.neighborhood ?? "");
  const [city, setCity] = useState(user?.city ?? "");
  const [state, setState] = useState(user?.state ?? "");
  const [noNumber, setNoNumber] = useState(user?.number === "S/N");

  const [loadingCep, setLoadingCep] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user) {
      setName(user.name ?? "");
      setEmail(user.email ?? "");
      setPhone(user.phone ?? "");
      setZipCode(user.zip_code ?? "");
      setAddress(user.address ?? "");
      setNumber(user.number ?? "");
      setComplement(user.complement ?? "");
      setNeighborhood(user.neighborhood ?? "");
      setCity(user.city ?? "");
      setState(user.state ?? "");
      setNoNumber(user.number === "S/N");
    }
  }, [user]);

  const fetchAddressByCep = async (cep: string) => {
    const cleanCep = cep.replace(/\D/g, "");
    if (cleanCep.length !== 8) return;

    setLoadingCep(true);
    try {
      const response = await fetch(`https://viacep.com.br/ws/${cleanCep}/json/`);
      const data = await response.json();

      if (!data.erro) {
        setAddress(data.logradouro || "");
        setNeighborhood(data.bairro || "");
        setCity(data.localidade || "");
        setState(data.uf || "");
      }
    } catch (err) {
      console.error("Erro ao buscar CEP:", err);
    } finally {
      setLoadingCep(false);
    }
  };

  const handleCepChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const cleanValue = value.replace(/\D/g, "");
    let formatted = "";

    if (cleanValue.length > 0) {
      formatted = cleanValue.substring(0, 5);
      if (cleanValue.length > 5) {
        formatted += "-" + cleanValue.substring(5, 8);
      }
    }

    setZipCode(formatted);

    if (cleanValue.length === 8) {
      fetchAddressByCep(cleanValue);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await api.patch("/users/me", {
        name,
        email,
        phone: phone || null,
        zip_code: zipCode || null,
        address: address || null,
        number: noNumber ? "S/N" : (number || null),
        complement: complement || null,
        neighborhood: neighborhood || null,
        city: city || null,
        state: state || null,
      });
      await refresh();
      setEditing(false);
      setSuccessMsg("Perfil e endereço atualizados com sucesso!");
      setTimeout(() => setSuccessMsg(null), 3500);
    } catch (e) {
      if (axios.isAxiosError(e)) setError(e.response?.data?.detail || "Falha ao salvar.");
      else setError("Erro inesperado.");
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await api.post("/users/me/avatar", fd, { headers: { "Content-Type": "multipart/form-data" } });
      await refresh();
    } catch {
      setError("Falha no upload do avatar.");
    } finally {
      setUploading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold mb-6">Meu perfil</h1>

      <div className="card p-6 mb-6">
        {/* Avatar */}
        <div className="flex items-start gap-6 mb-6">
          <div className="relative">
            <div className="w-24 h-24 rounded-2xl bg-slate-100 dark:bg-ink-700/50 overflow-hidden flex items-center justify-center">
              {user.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <User className="w-10 h-10 text-slate-400" />
              )}
            </div>
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-brand-500 text-white flex items-center justify-center hover:bg-brand-600 disabled:opacity-60"
              aria-label="Trocar avatar"
            >
              {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Camera className="w-3.5 h-3.5" />}
            </button>
            <input ref={fileRef} type="file" accept="image/*" hidden
              onChange={(e) => e.target.files?.[0] && handleAvatarUpload(e.target.files[0])} />
          </div>

          <div className="flex-1">
            <h2 className="text-xl font-semibold">{user.name || "Sem nome"}</h2>
            <p className="text-slate-500 dark:text-slate-400">{user.email}</p>
            <span className="inline-block mt-2 px-2 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-ink-700/60 text-slate-600 dark:text-slate-300 capitalize">
              {user.role === "client" ? "Cliente" : "Vendedor"}
            </span>
            {iterationsLimit && iterationsLimit.enabled && (
              <div className="mt-3 flex items-center gap-2 text-sm font-medium text-brand-600 dark:text-brand-400">
                <Sparkles className="w-4 h-4" />
                <span>{iterationsLimit.remaining} iterações restantes hoje</span>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
            {error}
          </div>
        )}

        {successMsg && (
          <div className="mb-4 text-sm text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 px-3 py-2 rounded-lg">
            {successMsg}
          </div>
        )}

        {/* Dados Básicos */}
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Nome completo</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={!editing}
                className="input"
              />
            </div>

            <div>
              <label className="label">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={!editing}
                className="input"
              />
            </div>
          </div>

          <div>
            <label className="label">Telefone para Contato</label>
            {editing ? (
              <PhoneInput
                value={phone}
                onChange={setPhone}
                className="w-full"
              />
            ) : (
              <input
                value={phone || "Não informado"}
                disabled
                className="input"
              />
            )}
          </div>
        </div>

        {/* Seção Endereço de Entrega */}
        <div className="mt-8 pt-6 border-t border-slate-200 dark:border-ink-700">
          <div className="flex items-center gap-2 mb-2">
            <MapPin className="w-5 h-5 text-brand-500" />
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              Endereço de Entrega Padrão
            </h3>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-5">
            Salvo aqui, seu endereço será preenchido automaticamente ao realizar compras no carrinho.
          </p>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">CEP</label>
                <div className="relative">
                  <input
                    value={zipCode}
                    onChange={handleCepChange}
                    onBlur={() => fetchAddressByCep(zipCode)}
                    disabled={!editing}
                    placeholder="00000-000"
                    maxLength={9}
                    className="input pr-10"
                  />
                  {loadingCep && (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-brand-500" />
                  )}
                </div>
              </div>

              <div>
                <label className="label">Logradouro / Rua / Avenida</label>
                <input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  disabled={!editing}
                  placeholder="Nome da rua ou avenida"
                  className="input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="label">Número</label>
                <input
                  value={noNumber ? "S/N" : number}
                  onChange={(e) => setNumber(e.target.value)}
                  disabled={!editing || noNumber}
                  placeholder="123"
                  className="input"
                />
                {editing && (
                  <label className="flex items-center gap-1.5 mt-1.5 text-xs text-slate-500 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={noNumber}
                      onChange={(e) => {
                        setNoNumber(e.target.checked);
                        if (e.target.checked) setNumber("S/N");
                        else setNumber("");
                      }}
                      className="w-3.5 h-3.5 accent-brand-500"
                    />
                    Sem número
                  </label>
                )}
              </div>

              <div>
                <label className="label">Complemento (opcional)</label>
                <input
                  value={complement}
                  onChange={(e) => setComplement(e.target.value)}
                  disabled={!editing}
                  placeholder="Apto, Bloco, etc."
                  className="input"
                />
              </div>

              <div>
                <label className="label">Bairro</label>
                <input
                  value={neighborhood}
                  onChange={(e) => setNeighborhood(e.target.value)}
                  disabled={!editing}
                  placeholder="Bairro"
                  className="input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Cidade</label>
                <input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  disabled={!editing}
                  placeholder="Cidade"
                  className="input"
                />
              </div>

              <div>
                <label className="label">UF / Estado</label>
                {editing ? (
                  <select
                    value={state}
                    onChange={(e) => setState(e.target.value)}
                    className="input"
                  >
                    <option value="">Selecione a UF</option>
                    {BRAZILIAN_STATES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    value={state || "Não informado"}
                    disabled
                    className="input"
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="flex gap-2 pt-6 mt-6 border-t border-slate-200 dark:border-ink-700">
          {editing ? (
            <>
              <button onClick={handleSave} disabled={saving} className="btn-primary disabled:opacity-60 flex items-center gap-2">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Salvar alterações
              </button>
              <button
                onClick={() => {
                  setEditing(false);
                  if (user) {
                    setName(user.name ?? "");
                    setEmail(user.email);
                    setPhone(user.phone ?? "");
                    setZipCode(user.zip_code ?? "");
                    setAddress(user.address ?? "");
                    setNumber(user.number ?? "");
                    setComplement(user.complement ?? "");
                    setNeighborhood(user.neighborhood ?? "");
                    setCity(user.city ?? "");
                    setState(user.state ?? "");
                    setNoNumber(user.number === "S/N");
                  }
                }}
                className="btn-outline"
              >
                Cancelar
              </button>
            </>
          ) : (
            <button onClick={() => setEditing(true)} className="btn-primary">
              Editar dados e endereço
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
