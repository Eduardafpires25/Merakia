import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  ExternalLink,
  Loader2,
  Minus,
  Package,
  Plus,
  QrCode,
  ShieldCheck,
  ShoppingBag,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useCart } from "../hooks/useCart";
import { PhoneInput } from "../components/PhoneInput";

import { ProtectedRoute } from "../components/ProtectedRoute";
import { Toast } from "../components/Toast";

function CartItem({
  item,
  updateQuantity,
  removeItem,
  loading,
}: {
  item: any;
  updateQuantity: (id: string, quantity: number) => Promise<void>;
  removeItem: (id: string) => Promise<void>;
  loading: boolean;
}) {
  const handleQuantityChange = async (newQuantity: number) => {
    if (newQuantity < 1) return;
    try {
      await updateQuantity(item.id, newQuantity);
    } catch (error) {
      console.error("Erro ao atualizar quantidade:", error);
    }
  };

  const handleRemove = async () => {
    try {
      await removeItem(item.id);
    } catch (error) {
      console.error("Erro ao remover item:", error);
    }
  };

  return (
    <div className="flex gap-4 p-4 bg-white dark:bg-ink-800 rounded-lg border border-slate-200 dark:border-ink-700">
      <div className="w-24 h-24 rounded-md overflow-hidden flex-shrink-0 bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center">
        {item.image_url ? (
          <img
            src={item.image_url}
            alt={item.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <Package className="w-10 h-10 text-slate-300 dark:text-ink-600" />
        )}
      </div>
      <div className="flex-1">
        <h3 className="font-semibold text-slate-900 dark:text-white">{item.name}</h3>
        {item.description && (
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{item.description}</p>
        )}
        <p className="text-lg font-bold text-brand-500 mt-2">
          R$ {Number(item.unit_price).toFixed(2)}
        </p>
      </div>
      <div className="flex flex-col items-end gap-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleQuantityChange(item.quantity - 1)}
            disabled={loading || item.quantity <= 1}
            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-ink-700 disabled:opacity-50"
          >
            <Minus className="w-4 h-4" />
          </button>
          <span className="w-8 text-center font-medium">{item.quantity}</span>
          <button
            onClick={() => handleQuantityChange(item.quantity + 1)}
            disabled={loading}
            className="p-1 rounded hover:bg-slate-100 dark:hover:bg-ink-700 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <button
          onClick={handleRemove}
          disabled={loading}
          className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 disabled:opacity-50"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

const BRAZILIAN_STATES = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
  "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
];

interface PaymentModalData {
  open: boolean;
  paymentId: string;
  pixCode: string;
  pixQrCode: string;
  amount: number;
  status: string;
}

export default function CartPage() {
  const navigate = useNavigate();
  const { user, refresh } = useAuth();
  const { cart, loading, checkout, updateQuantity, removeItem } = useCart();
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({
    show: false,
    message: "",
    type: "success",
  });
  const [shippingAddress, setShippingAddress] = useState("");
  const [shippingNumber, setShippingNumber] = useState("");
  const [shippingComplement, setShippingComplement] = useState("");
  const [shippingNeighborhood, setShippingNeighborhood] = useState("");
  const [shippingCity, setShippingCity] = useState("");
  const [shippingState, setShippingState] = useState("");
  const [shippingZipCode, setShippingZipCode] = useState("");
  const [shippingPhone, setShippingPhone] = useState("");
  const [noNumber, setNoNumber] = useState(false);
  const [saveAddressToProfile, setSaveAddressToProfile] = useState(true);
  const [loadingCep, setLoadingCep] = useState(false);
  const [copiedPix, setCopiedPix] = useState(false);
  const [simulating, setSimulating] = useState(false);

  // Auto-preenche os dados com o endereço salvo no perfil do usuário
  useEffect(() => {
    if (user) {
      if (user.zip_code) setShippingZipCode(user.zip_code);
      if (user.address) setShippingAddress(user.address);
      if (user.number) {
        if (user.number === "S/N") {
          setNoNumber(true);
          setShippingNumber("S/N");
        } else {
          setShippingNumber(user.number);
        }
      }
      if (user.complement) setShippingComplement(user.complement);
      if (user.neighborhood) setShippingNeighborhood(user.neighborhood);
      if (user.city) setShippingCity(user.city);
      if (user.state) setShippingState(user.state);
      if (user.phone) setShippingPhone(user.phone);
    }
  }, [user]);

  // Modal de pagamento PIX
  const [paymentModal, setPaymentModal] = useState<PaymentModalData | null>(null);


  const numberInputRef = useRef<HTMLInputElement>(null);

  const fetchAddressByCep = async (cep: string) => {
    const cleanCep = cep.replace(/\D/g, "");
    if (cleanCep.length !== 8) return;

    setLoadingCep(true);
    try {
      const response = await fetch(`https://viacep.com.br/ws/${cleanCep}/json/`);
      const data = await response.json();

      if (data.erro) {
        setToast({ show: true, message: "CEP não encontrado.", type: "error" });
        return;
      }

      setShippingAddress(data.logradouro || "");
      setShippingNeighborhood(data.bairro || "");
      setShippingCity(data.localidade || "");
      setShippingState(data.uf || "");

      // Foco automático no número após auto-preenchimento
      setTimeout(() => {
        numberInputRef.current?.focus();
      }, 100);
    } catch (error) {
      console.error("Erro ao buscar CEP:", error);
      setToast({ show: true, message: "Erro ao buscar CEP. Verifique sua conexão.", type: "error" });
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

    setShippingZipCode(formatted);

    // Auto busca imediata ao completar 8 dígitos
    if (cleanValue.length === 8) {
      fetchAddressByCep(cleanValue);
    }
  };

  const handleCepKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (
      !/[0-9]/.test(e.key) &&
      !e.key.startsWith("Backspace") &&
      !e.key.startsWith("Delete") &&
      !e.key.startsWith("Arrow") &&
      !e.key.startsWith("Tab")
    ) {
      e.preventDefault();
    }
  };

  const handleCopyPix = () => {
    if (!paymentModal?.pixCode) return;
    navigator.clipboard.writeText(paymentModal.pixCode);
    setCopiedPix(true);
    setTimeout(() => setCopiedPix(false), 2500);
    setToast({ show: true, message: "Código PIX copiado para a área de transferência!", type: "success" });
  };

  const handleSimulatePayment = async (action: "approve" | "fail") => {
    if (!paymentModal) return;
    setSimulating(true);
    try {
      const res = await api.post(`/payments/${paymentModal.paymentId}/simulate`, { action });
      const newStatus = res.data.payment.status;
      setPaymentModal((prev) => (prev ? { ...prev, status: newStatus } : null));

      if (action === "approve") {
        setToast({
          show: true,
          message: "Pagamento aprovado com sucesso! Valor retido com segurança em custódia na MeraKia.",
          type: "success",
        });
      } else {
        setToast({
          show: true,
          message: "O pagamento foi marcado como falho ou cancelado.",
          type: "error",
        });
      }
    } catch (err: any) {
      console.error("Erro na simulação:", err);
      setToast({
        show: true,
        message: err.response?.data?.detail || "Erro ao simular transação.",
        type: "error",
      });
    } finally {
      setSimulating(false);
    }
  };

  const handleCheckout = async () => {
    if (!cart || cart.items.length === 0) return;

    if (!shippingZipCode || !shippingAddress || !shippingCity || !shippingState || !shippingPhone) {
      setToast({ show: true, message: "Preencha todos os campos de endereço para entrega.", type: "error" });
      return;
    }

    const cleanPhone = shippingPhone.replace(/\D/g, "");
    if (cleanPhone.length < 10) {
      setToast({
        show: true,
        message: "Informe um telefone válido com DDD (mínimo 10 dígitos).",
        type: "error",
      });
      return;
    }

    if (!noNumber && !shippingNumber) {
      setToast({ show: true, message: "Informe o número ou marque 'Sem número'.", type: "error" });
      return;
    }

    const sellerIds = [...new Set(cart.items.map((item) => item.seller_id))];
    try {
      const result = await checkout(sellerIds, false, {
        shipping_address: shippingAddress,
        shipping_number: noNumber ? "S/N" : shippingNumber,
        shipping_complement: shippingComplement,
        shipping_neighborhood: shippingNeighborhood,
        shipping_city: shippingCity,
        shipping_state: shippingState,
        shipping_zip_code: shippingZipCode,
        shipping_phone: shippingPhone,
        save_address_to_profile: saveAddressToProfile,
      });


      if (saveAddressToProfile) {
        refresh();
      }

      if (result.payment_id && result.pix_code) {

        setPaymentModal({
          open: true,
          paymentId: result.payment_id,
          pixCode: result.pix_code,
          pixQrCode: result.pix_qr_code || "",
          amount: Number(result.total_amount),
          status: result.payment_status || "pending",
        });
      } else {
        setToast({
          show: true,
          message: `Checkout realizado! Total: R$ ${Number(result.total_amount).toFixed(2)}`,
          type: "success",
        });
      }
    } catch (error: any) {
      console.error("Erro ao fazer checkout:", error);
      const detail = error.response?.data?.detail;
      let errorMsg = "Erro ao fazer checkout. Tente novamente.";
      if (typeof detail === "string") {
        errorMsg = detail;
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        errorMsg = detail[0].msg;
      }
      setToast({ show: true, message: errorMsg, type: "error" });
    }
  };

  if (loading && !cart) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 dark:bg-ink-700 rounded mb-4"></div>
          <div className="h-32 bg-slate-200 dark:bg-ink-700 rounded mb-4"></div>
          <div className="h-32 bg-slate-200 dark:bg-ink-700 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto p-6">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-6">Meu Carrinho</h1>

        {!cart || cart.items.length === 0 ? (
          <div className="text-center py-12">
            <ShoppingBag className="w-16 h-16 mx-auto text-slate-400 mb-4" />
            <h2 className="text-xl font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Seu carrinho está vazio
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              Adicione produtos para começar suas compras
            </p>
            <a href="/sellers" className="btn-primary inline-block">
              Ver Produtos
            </a>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {cart.items.map((item) => (
                <CartItem
                  key={item.id}
                  item={item}
                  updateQuantity={updateQuantity}
                  removeItem={removeItem}
                  loading={loading}
                />
              ))}
            </div>

            <div className="card p-6">
              <h3 className="font-semibold mb-4 text-lg text-slate-900 dark:text-white">
                Endereço de Entrega
              </h3>

              <div className="space-y-4 mb-6">
                {/* CEP no TOPO com auto-preenchimento rápido */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="label">CEP (digite para autocompletar)</label>
                    <div className="relative">
                      <input
                        type="text"
                        value={shippingZipCode}
                        onChange={handleCepChange}
                        onKeyPress={handleCepKeyPress}
                        onBlur={() => fetchAddressByCep(shippingZipCode)}
                        className="input pr-10"
                        placeholder="00000-000"
                        maxLength={9}
                        required
                      />
                      {loadingCep && (
                        <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-brand-500" />
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="label">Telefone para Contato</label>
                    <PhoneInput
                      value={shippingPhone}
                      onChange={setShippingPhone}
                      required
                      className="w-full"
                    />
                  </div>
                </div>

                <div>
                  <label className="label">Logradouro / Endereço</label>
                  <input
                    type="text"
                    value={shippingAddress}
                    onChange={(e) => setShippingAddress(e.target.value)}
                    className="input"
                    placeholder="Rua, Avenida, etc."
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Número</label>
                    <input
                      ref={numberInputRef}
                      type="text"
                      value={shippingNumber}
                      onChange={(e) => setShippingNumber(e.target.value)}
                      className="input"
                      placeholder="123"
                      disabled={noNumber}
                    />
                  </div>
                  <div>
                    <label className="label">Complemento (opcional)</label>
                    <input
                      type="text"
                      value={shippingComplement}
                      onChange={(e) => setShippingComplement(e.target.value)}
                      className="input"
                      placeholder="Apto, Bloco, etc."
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="noNumber"
                    checked={noNumber}
                    onChange={(e) => {
                      setNoNumber(e.target.checked);
                      if (e.target.checked) {
                        setShippingNumber("S/N");
                      } else {
                        setShippingNumber("");
                      }
                    }}
                    className="w-4 h-4 accent-brand-500 cursor-pointer"
                  />
                  <label htmlFor="noNumber" className="text-sm cursor-pointer text-slate-600 dark:text-slate-400">
                    Sem número
                  </label>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="label">Bairro</label>
                    <input
                      type="text"
                      value={shippingNeighborhood}
                      onChange={(e) => setShippingNeighborhood(e.target.value)}
                      className="input"
                      placeholder="Bairro"
                    />
                  </div>
                  <div>
                    <label className="label">Cidade</label>
                    <input
                      type="text"
                      value={shippingCity}
                      onChange={(e) => setShippingCity(e.target.value)}
                      className="input"
                      placeholder="Cidade"
                      required
                    />
                  </div>
                  <div>
                    <label className="label">UF</label>
                    <select
                      value={shippingState}
                      onChange={(e) => setShippingState(e.target.value)}
                      className="input"
                      required
                    >
                      <option value="">Selecione</option>
                      {BRAZILIAN_STATES.map((state) => (
                        <option key={state} value={state}>
                          {state}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="pt-2">
                  <label className="flex items-center gap-2 cursor-pointer bg-slate-50 dark:bg-ink-800/60 p-3 rounded-xl border border-slate-200/80 dark:border-ink-700/80">
                    <input
                      type="checkbox"
                      checked={saveAddressToProfile}
                      onChange={(e) => setSaveAddressToProfile(e.target.checked)}
                      className="w-4 h-4 accent-brand-500 rounded border-slate-300 text-brand-500 focus:ring-brand-500 cursor-pointer"
                    />
                    <span className="text-xs sm:text-sm font-medium text-slate-700 dark:text-slate-300">
                      Salvar este endereço no meu perfil para compras futuras
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex justify-between items-center mb-4 pt-4 border-t border-slate-200 dark:border-ink-700">

                <span className="text-lg text-slate-700 dark:text-slate-300">
                  Total ({cart.total_items} {cart.total_items === 1 ? "item" : "itens"})
                </span>
                <span className="text-2xl font-bold text-brand-500">
                  R$ {Number(cart.total).toFixed(2)}
                </span>
              </div>

              <button

                onClick={handleCheckout}
                disabled={loading}
                className="w-full btn-primary !py-3 flex items-center justify-center gap-2 text-base font-semibold"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" /> Processando...
                  </>
                ) : (
                  <>
                    <QrCode className="w-5 h-5" /> Pagar com PIX Intermediado
                  </>
                )}
              </button>
            </div>
          </>
        )}

        {/* Modal didático de Pagamento PIX com Custódia */}
        {paymentModal && paymentModal.open && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
            <div className="bg-white dark:bg-ink-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 dark:border-ink-700 relative animate-in fade-in zoom-in-95 duration-200">
              <button
                onClick={() => setPaymentModal(null)}
                className="absolute top-4 right-4 p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full hover:bg-slate-100 dark:hover:bg-ink-700"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-brand-500/10 dark:bg-brand-500/20 text-brand-500 rounded-xl">
                  <QrCode className="w-7 h-7" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                    Pagamento via PIX
                  </h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Intermediado pela plataforma MeraKia
                  </p>
                </div>
              </div>

              {/* Banner Didático de Custódia */}
              <div className="p-3.5 mb-5 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/60 flex items-start gap-3">
                <ShieldCheck className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-blue-900 dark:text-blue-200 leading-relaxed">
                  <strong className="block font-semibold mb-0.5 text-blue-950 dark:text-blue-100">
                    Garantia de Custódia Segura MeraKia
                  </strong>
                  O valor pago fica retido em conta intermediária da plataforma. O vendedor
                  só receberá a liberação do repasse para sua chave PIX quando você confirmar o
                  recebimento do produto.
                </div>
              </div>

              <div className="text-center my-4">
                <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Valor Total</p>
                <p className="text-3xl font-extrabold text-brand-500">
                  R$ {paymentModal.amount.toFixed(2)}
                </p>
              </div>

              {/* Status Atual do Pagamento */}
              <div className="flex justify-center mb-4">
                {paymentModal.status === "paid" && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700">
                    <CheckCircle2 className="w-4 h-4" /> Pagamento Aprovado (Em Custódia)
                  </span>
                )}
                {paymentModal.status === "pending" && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-700">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" /> Aguardando Pagamento
                  </span>
                )}
                {paymentModal.status === "failed" && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-300 border border-red-300 dark:border-red-700">
                    <AlertCircle className="w-4 h-4" /> Pagamento Falhou ou Expirou
                  </span>
                )}
                {paymentModal.status === "released" && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-700">
                    <CheckCircle2 className="w-4 h-4" /> Valor Liberado ao Vendedor
                  </span>
                )}
              </div>

              {/* QR Code */}
              {paymentModal.pixQrCode && (
                <div className="flex justify-center my-3">
                  <div className="p-3 bg-white rounded-xl shadow-inner border border-slate-200 inline-block">
                    <img
                      src={paymentModal.pixQrCode}
                      alt="QR Code Pix"
                      className="w-48 h-48 mx-auto"
                    />
                  </div>
                </div>
              )}

              {/* Copia e Cola */}
              <div className="space-y-1.5 mb-5">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Pix Copia e Cola
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    readOnly
                    value={paymentModal.pixCode}
                    className="input text-xs font-mono select-all bg-slate-50 dark:bg-ink-900 truncate"
                  />
                  <button
                    onClick={handleCopyPix}
                    className="btn-secondary flex-shrink-0 flex items-center gap-1.5 text-xs py-2 px-3"
                    title="Copiar Código Pix"
                  >
                    {copiedPix ? (
                      <>
                        <Check className="w-4 h-4 text-emerald-500" /> Copiado!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" /> Copiar
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Painel Didático de Simulação */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-ink-700/50 border border-slate-200 dark:border-ink-600 mb-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                  Ambiente de Testes Didáticos
                </p>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleSimulatePayment("approve")}
                    disabled={simulating || paymentModal.status === "paid"}
                    className="btn-primary !bg-emerald-600 hover:!bg-emerald-700 !py-2 text-xs font-semibold flex items-center justify-center gap-1.5"
                  >
                    {simulating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                    Simular Sucesso
                  </button>
                  <button
                    onClick={() => handleSimulatePayment("fail")}
                    disabled={simulating || paymentModal.status === "paid"}
                    className="btn-secondary !text-red-600 dark:!text-red-400 hover:!bg-red-50 dark:hover:!bg-red-950/30 !py-2 text-xs font-semibold flex items-center justify-center gap-1.5"
                  >
                    {simulating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <AlertCircle className="w-3.5 h-3.5" />}
                    Simular Falha
                  </button>
                </div>
              </div>

              {/* Botões de Ação */}
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setPaymentModal(null)}
                  className="btn-secondary text-sm py-2 px-4"
                >
                  Fechar
                </button>
                <button
                  onClick={() => {
                    setPaymentModal(null);
                    navigate("/orders");
                  }}
                  className="btn-primary text-sm py-2 px-4 flex items-center gap-1.5"
                >
                  <ExternalLink className="w-4 h-4" /> Ver Meus Pedidos
                </button>
              </div>
            </div>
          </div>
        )}

        <Toast
          show={toast.show}
          message={toast.message}
          type={toast.type}
          onClose={() => setToast({ show: false, message: "", type: "success" })}
        />
      </div>
    </ProtectedRoute>
  );
}
