import axios from "axios";
import {
  AlertCircle, ArrowLeft, Check, CheckCircle2, Copy, Download, Edit3, Image as ImageIcon, Loader2, Package, QrCode, RefreshCw, Send, ShieldCheck, Sparkles, ShoppingCart, Star, Trash2, Upload, X, XCircle,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useIterations } from "../contexts/IterationsContext";
import { Modal } from "../components/Modal";
import { Toast } from "../components/Toast";
import { useCart } from "../hooks/useCart";
import type { Iteration, Order, OrderReview, OrderStatus } from "../types/api";
import { isColorOption, parseColorValue } from "../components/ColorSwatchSelector";

interface PaymentModalData {
  open: boolean;
  paymentId: string;
  pixCode: string;
  pixQrCode: string;
  amount: number;
  status: string;
}

const RATING_LABELS: Record<number, string> = {
  1: "Muito ruim",
  2: "Ruim",
  3: "Bom",
  4: "Muito bom!",
  5: "Excelente! Adorei",
};

const formatReviewDate = (isoStr: string) => {
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoStr;
  }
};


const statusLabels: Record<OrderStatus, string> = {
  draft: "Rascunho",
  in_analysis: "Em análise pelo seller",
  approved: "Aceito - aguardando pagamento",
  paid: "Pago - aguardando produção",
  in_production: "Em produção",
  sent: "Enviado",
  delivered: "Entregue",
  completed: "Concluído",
  cancelled: "Cancelado",
};

const statusBadge: Record<OrderStatus, string> = {
  draft: "bg-slate-100 text-slate-700 dark:bg-ink-700/60 dark:text-slate-300",
  in_analysis: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300",
  approved: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300",
  paid: "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300",
  in_production: "bg-purple-100 text-purple-700 dark:bg-brand-500/20 dark:text-brand-300",
  sent: "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300",
  delivered: "bg-teal-100 text-teal-700 dark:bg-teal-500/20 dark:text-teal-300",
  completed: "bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300",
  cancelled: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300",
};

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { iterationsLimit, fetchIterationsLimit } = useIterations();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const [order, setOrder] = useState<Order | null>(null);
  const [paymentInfo, setPaymentInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [description, setDescription] = useState("");
  const [generating, setGenerating] = useState(false);
  const [acting, setActing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [acceptPrice, setAcceptPrice] = useState("");
  const [showAcceptModal, setShowAcceptModal] = useState(false);
  const [showLimitModal, setShowLimitModal] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string; type: "success" | "error" }>({ show: false, message: "", type: "success" });
  const [paymentModal, setPaymentModal] = useState<PaymentModalData | null>(null);
  const [copiedPix, setCopiedPix] = useState(false);
  const [simulatingPayment, setSimulatingPayment] = useState(false);
  const [actingPayment, setActingPayment] = useState(false);
  const [review, setReview] = useState<OrderReview | null>(null);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [isEditingReview, setIsEditingReview] = useState(false);
  const [ratingInput, setRatingInput] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [commentInput, setCommentInput] = useState("");
  const refFileInputRef = useRef<HTMLInputElement>(null);

  const handleUploadReferenceFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    setActing(true);
    setActionError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("caption", "Logo / Referência do cliente");
      await api.post(`/orders/${id}/reference-images`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setToast({ show: true, message: "Foto de referência anexada com sucesso!", type: "success" });
      await fetchOrder();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setActionError(err.response?.data?.detail || "Falha ao anexar imagem.");
      } else {
        setActionError("Erro inesperado ao enviar anexo.");
      }
    } finally {
      setActing(false);
      if (refFileInputRef.current) refFileInputRef.current.value = "";
    }
  };

  const handleDeleteReferenceImage = async (refId: string) => {
    if (!id || !confirm("Remover esta imagem de referência?")) return;
    setActing(true);
    setActionError(null);
    try {
      await api.delete(`/orders/${id}/reference-images/${refId}`);
      setToast({ show: true, message: "Imagem removida com sucesso.", type: "success" });
      await fetchOrder();
    } catch {
      setActionError("Falha ao remover imagem.");
    } finally {
      setActing(false);
    }
  };

  const fetchOrder = async () => {
    if (!id) return;
    try {
      const { data } = await api.get<Order>(`/orders/${id}`);
      setOrder(data);
      try {
        const payRes = await api.get(`/payments/by-order/${id}`);
        setPaymentInfo(payRes.data);
      } catch {
        setPaymentInfo(null);
      }

      if (data.status === "delivered" || data.status === "completed") {
        try {
          const revRes = await api.get<OrderReview>(`/orders/${id}/reviews`);
          setReview(revRes.data);
          setRatingInput(revRes.data.rating);
          setCommentInput(revRes.data.comment || "");
        } catch {
          setReview(null);
        }
      }
    } catch {
      setError("Pedido não encontrado.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitReview = async () => {
    if (!id) return;
    if (ratingInput < 1 || ratingInput > 5) {
      setToast({ show: true, message: "Por favor, selecione de 1 a 5 estrelas.", type: "error" });
      return;
    }
    setSubmittingReview(true);
    try {
      if (review) {
        const res = await api.put<OrderReview>(`/orders/${id}/reviews`, {
          rating: ratingInput,
          comment: commentInput.trim() || null,
        });
        setReview(res.data);
        setIsEditingReview(false);
        setToast({ show: true, message: "Avaliação atualizada com sucesso!", type: "success" });
      } else {
        const res = await api.post<OrderReview>(`/orders/${id}/reviews`, {
          rating: ratingInput,
          comment: commentInput.trim() || null,
        });
        setReview(res.data);
        setIsEditingReview(false);
        setToast({ show: true, message: "Obrigado! Sua avaliação foi registrada com sucesso.", type: "success" });
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Erro ao salvar avaliação.";
      setToast({ show: true, message: msg, type: "error" });
    } finally {
      setSubmittingReview(false);
    }
  };

  useEffect(() => { fetchOrder(); /* eslint-disable-next-line */ }, [id]);

  const isClient = user?.id === order?.client_id;
  const isSeller = user?.id === order?.seller_id;
  const canIterate = isClient && order?.status === "draft";
  const canSubmit = isClient && order?.status === "draft" && order?.approved_iteration_id;
  const canCancelClient = isClient && (order?.status === "draft" || order?.status === "in_analysis");
  const canSellerDecide = isSeller && order?.status === "in_analysis";
  const isPaymentConfirmed = paymentInfo?.status === "paid" || paymentInfo?.status === "released";
  const canSellerProgress = isSeller && (
    (order?.status === "paid" && isPaymentConfirmed) ||
    order?.status === "in_production" ||
    order?.status === "sent"
  );

  const handleCopyPix = async () => {
    if (!paymentModal?.pixCode) return;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(paymentModal.pixCode);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = paymentModal.pixCode;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }
      setCopiedPix(true);
      setTimeout(() => setCopiedPix(false), 3000);
    } catch {
      alert("Não foi possível copiar automaticamente.");
    }
  };

  const handleOpenExistingPaymentModal = (pay: any) => {
    if (!pay) return;
    setPaymentModal({
      open: true,
      paymentId: pay.id,
      pixCode: pay.pix_code,
      pixQrCode: pay.pix_qr_code,
      amount: Number(pay.amount || order?.estimated_price || 0),
      status: pay.status,
    });
  };

  const handlePayWithPixDirect = async () => {
    if (!id) return;
    setActingPayment(true);
    setActionError(null);
    try {
      const { data } = await api.post(`/payments/for-order/${id}`);
      setPaymentInfo(data);
      setPaymentModal({
        open: true,
        paymentId: data.id,
        pixCode: data.pix_code,
        pixQrCode: data.pix_qr_code,
        amount: Number(data.amount),
        status: data.status,
      });
      await fetchOrder();
    } catch (e) {
      if (axios.isAxiosError(e)) {
        setActionError(e.response?.data?.detail || "Erro ao gerar cobrança PIX.");
      } else {
        setActionError("Erro inesperado ao gerar pagamento.");
      }
    } finally {
      setActingPayment(false);
    }
  };

  const handleSimulatePayment = async (action: "approve" | "fail") => {
    if (!paymentModal) return;
    setSimulatingPayment(true);
    try {
      const { data } = await api.post(`/payments/${paymentModal.paymentId}/simulate`, { action });
      setPaymentModal((prev) => (prev ? { ...prev, status: action === "approve" ? "paid" : "failed" } : null));
      setToast({
        show: true,
        message: data.message || (action === "approve" ? "Pagamento aprovado com sucesso!" : "Pagamento falhou."),
        type: action === "approve" ? "success" : "error",
      });
      await fetchOrder();
    } catch (e) {
      console.error("Erro ao simular pagamento:", e);
      setToast({
        show: true,
        message: "Erro ao processar simulação.",
        type: "error",
      });
    } finally {
      setSimulatingPayment(false);
    }
  };

  const handleAction = async (fn: () => Promise<unknown>) => {
    setActing(true);
    setActionError(null);
    try {
      await fn();
      await fetchOrder();
    } catch (e) {
      if (axios.isAxiosError(e)) setActionError(e.response?.data?.detail || "Falha na operação.");
      else setActionError("Erro inesperado.");
    } finally {
      setActing(false);
    }
  };

  const generateIteration = async (customPrompt?: string) => {
    const textToUse = (typeof customPrompt === "string" ? customPrompt : description).trim() || order?.description || "";
    if (!textToUse || generating) return;
    setGenerating(true);
    setActionError(null);
    try {
      await api.post(`/orders/${id}/iterations`, { description: textToUse });
      setDescription("");
      await fetchOrder();
      // Atualizar iterações restantes
      await fetchIterationsLimit();
    } catch (e) {
      if (axios.isAxiosError(e)) {
        const status = e.response?.status;
        // Tratar especificamente o erro de limite excedido (429)
        if (status === 429) {
          setShowLimitModal(true);
        } else {
          const detail = e.response?.data?.detail;
          setActionError(detail || "Falha na geração da imagem. Tente novamente mais tarde.");
        }
      } else {
        setActionError("Erro inesperado. Tente novamente.");
      }
    } finally {
      setGenerating(false);
    }
  };

  const approveIteration = (iterId: string) =>
    handleAction(() => api.post(`/orders/${id}/approve-iteration/${iterId}`));

  const submitOrder = () => handleAction(() => api.post(`/orders/${id}/submit`));

  const cancelOrder = () =>
    handleAction(() => api.post(`/orders/${id}/cancel`, { note: "Cancelado pelo cliente" }));

  const sellerAccept = () => setShowAcceptModal(true);
  const sellerReject = () =>
    handleAction(() => api.post(`/orders/${id}/seller-decision`, { accept: false, note: "Rejeitado" }));
  const updateStatus = (status: OrderStatus) =>
    handleAction(() => api.patch(`/orders/${id}/status`, { status }));

  const confirmDelivery = () =>
    handleAction(() => api.patch(`/orders/${id}/confirm-delivery`));

  const completeOrder = () =>
    handleAction(() => api.patch(`/orders/${id}/complete`));

  const confirmAcceptWithPrice = async () => {
    const price = parseFloat(acceptPrice);
    if (isNaN(price) || price <= 0) {
      setActionError("Digite um preço válido.");
      return;
    }
    await handleAction(() => api.post(`/orders/${id}/seller-decision`, { accept: true, estimated_price: price }));
    setShowAcceptModal(false);
    setAcceptPrice("");
  };

  const handleAddOrderToCart = async () => {
    if (!order) return;
    try {
      await addToCart({
        order_id: order.id,
        quantity: order.quantity,
      });
      setToast({ show: true, message: "Pedido adicionado ao carrinho! Vá para o carrinho para finalizar o pagamento.", type: "success" });
    } catch (error) {
      console.error("Erro ao adicionar pedido ao carrinho:", error);
      setToast({ show: true, message: "Erro ao adicionar pedido ao carrinho. Tente novamente.", type: "error" });
    }
  };

  if (loading) {
    return <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-brand-500" /></div>;
  }

  if (error || !order) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center">
        <p className="text-slate-500">{error}</p>
        <button onClick={() => {
          if (user?.role === "seller") {
            navigate("/seller-dashboard");
          } else {
            navigate("/orders");
          }
        }} className="btn-outline mt-6">Voltar</button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <Link to={isSeller ? "/seller-dashboard" : "/orders"} className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-brand-500 mb-4">
        <ArrowLeft className="w-4 h-4" /> Voltar
      </Link>

      {/* Header do pedido */}
      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold">{order.title}</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              {order.product_type ?? "—"} • Qtd: {order.quantity}
              {order.estimated_price && <> • <span className="text-brand-500 font-semibold">R$ {order.estimated_price}</span></>}
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-300 mt-3 max-w-2xl">{order.description}</p>
            {order.product_options && Object.keys(order.product_options).length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {Object.entries(order.product_options).map(([k, v]) => {
                  const valStr = String(v);
                  const isColor = isColorOption(k, [valStr]) || valStr.includes("#");
                  const colorData = isColor ? parseColorValue(valStr) : null;

                  return (
                    <span
                      key={k}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-ink-700/60 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-ink-600"
                    >
                      <span className="capitalize text-slate-500 dark:text-slate-400">{k}:</span>
                      {colorData && (
                        <span
                          className="w-3.5 h-3.5 rounded-full border border-slate-300 dark:border-ink-500 shadow-sm shrink-0"
                          style={{ backgroundColor: colorData.hex }}
                          title={`${colorData.name} (${colorData.hex})`}
                        />
                      )}
                      <span className="font-semibold text-slate-900 dark:text-white">{valStr}</span>
                    </span>
                  );
                })}
              </div>
            )}
          </div>
          <span className={`px-3 py-1.5 rounded-full text-xs font-medium ${statusBadge[order.status]}`}>
            {statusLabels[order.status]}
          </span>
        </div>

        {/* Card Didático de Custódia e Pagamento PIX */}
        {paymentInfo && (
          <div className="mt-4">
            {paymentInfo.status === "paid" && (
              <div className="bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/60 p-4 rounded-xl flex items-start gap-3">
                <ShieldCheck className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-sm text-blue-950 dark:text-blue-100 flex items-center gap-2">
                    Pagamento em Custódia Protegida MeraKia
                    <span className="text-xs bg-blue-200/70 dark:bg-blue-800 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded-full font-mono">
                      R$ {Number(paymentInfo.amount).toFixed(2)}
                    </span>
                  </h4>
                  <p className="text-xs text-blue-800/90 dark:text-blue-300/90 mt-1 leading-relaxed">
                    {isClient
                      ? "O seu pagamento já foi confirmado e está retido com segurança pela plataforma. O valor só será repassado para a chave PIX do vendedor quando você confirmar o recebimento do pedido."
                      : "O cliente já efetuou o pagamento e o valor está garantido em custódia na plataforma. Assim que o cliente confirmar a entrega, o repasse será liberado automaticamente para sua chave PIX."}
                  </p>
                </div>
              </div>
            )}

            {paymentInfo.status === "released" && (
              <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 p-4 rounded-xl flex items-start gap-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <h4 className="font-semibold text-sm text-emerald-950 dark:text-emerald-100 flex items-center gap-2">
                      Repasse PIX Liberado ao Vendedor!
                      <span className="text-xs bg-emerald-200/70 dark:bg-emerald-800 text-emerald-900 dark:text-emerald-200 px-2 py-0.5 rounded-full font-mono">
                        R$ {Number(paymentInfo.amount).toFixed(2)}
                      </span>
                    </h4>
                    {paymentInfo.released_at && (
                      <span className="text-xs text-emerald-700 dark:text-emerald-300">
                        {new Date(paymentInfo.released_at).toLocaleString("pt-BR")}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-emerald-800/90 dark:text-emerald-300/90 mt-1 leading-relaxed">
                    {isClient ? (
                      "Você confirmou o recebimento e o valor em custódia foi liberado com sucesso para o vendedor."
                    ) : (
                      <>
                        Recebimento confirmado pelo cliente! O repasse foi enviado para sua chave PIX:{" "}
                        <strong className="font-mono bg-emerald-100 dark:bg-emerald-900/60 px-1.5 py-0.5 rounded text-emerald-900 dark:text-emerald-200 ml-1">
                          {paymentInfo.seller_pix_key || "Chave cadastrada"} ({paymentInfo.seller_pix_key_type?.toUpperCase() || "PIX"})
                        </strong>
                      </>
                    )}
                  </p>
                </div>
              </div>
            )}

            {paymentInfo.status === "pending" && (
              <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 p-4 rounded-xl flex items-start justify-between flex-wrap gap-3">
                <div className="flex items-start gap-3">
                  <Loader2 className="w-6 h-6 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5 animate-spin" />
                  <div>
                    <h4 className="font-semibold text-sm text-amber-950 dark:text-amber-100">
                      Aguardando Confirmação do PIX (R$ {Number(paymentInfo.amount).toFixed(2)})
                    </h4>
                    <p className="text-xs text-amber-800/90 dark:text-amber-300/90 mt-1">
                      Cobrança PIX gerada pela plataforma. Efetue o pagamento para dar início à produção.
                    </p>
                  </div>
                </div>
                {isClient && (
                  <button
                    type="button"
                    onClick={() => handleOpenExistingPaymentModal(paymentInfo)}
                    className="btn-primary !py-2 !px-3.5 text-xs font-semibold flex items-center gap-1.5 shrink-0 self-center"
                  >
                    <QrCode className="w-4 h-4" /> Ver QR Code / Pagar
                  </button>
                )}
              </div>
            )}

            {paymentInfo.status === "failed" && (
              <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/60 p-4 rounded-xl flex items-start justify-between flex-wrap gap-3">
                <div className="flex items-start gap-3">
                  <XCircle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-sm text-red-950 dark:text-red-100">
                      Pagamento Não Confirmado / Falhou (R$ {Number(paymentInfo.amount).toFixed(2)})
                    </h4>
                    <p className="text-xs text-red-800/90 dark:text-red-300/90 mt-1">
                      A transação PIX foi cancelada ou falhou. O pedido permanece aguardando pagamento para você tentar novamente quando desejar.
                    </p>
                  </div>
                </div>
                {isClient && (
                  <button
                    type="button"
                    onClick={handlePayWithPixDirect}
                    disabled={actingPayment}
                    className="btn-primary !bg-red-600 hover:!bg-red-700 !py-2 !px-3.5 text-xs font-semibold flex items-center gap-1.5 shrink-0 self-center"
                  >
                    {actingPayment ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                    Tentar Novamente com PIX
                  </button>
                )}
              </div>
            )}
          </div>
        )}


        {/* Logotipos e Imagens de Referencia */}
        <div className="mt-5 pt-5 border-t border-slate-100 dark:border-ink-700">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <h3 className="font-semibold text-sm flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-brand-500" />
              Logotipos e Fotos de Referência
              {order.reference_images && order.reference_images.length > 0 && (
                <span className="text-xs text-slate-400">({order.reference_images.length})</span>
              )}
            </h3>

            {canIterate && (
              <div>
                <input
                  ref={refFileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  onChange={handleUploadReferenceFile}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => refFileInputRef.current?.click()}
                  disabled={acting}
                  className="btn-outline text-xs py-1.5 px-3 inline-flex items-center gap-1.5"
                >
                  <Upload className="w-3.5 h-3.5" />
                  Anexar foto/logo
                </button>
              </div>
            )}
          </div>

          {!order.reference_images || order.reference_images.length === 0 ? (
            <p className="text-xs text-slate-400 italic">
              Nenhum logotipo ou imagem de referência anexado a este pedido.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {order.reference_images.map((img) => (
                <div
                  key={img.id}
                  className="border border-slate-200 dark:border-ink-700 rounded-xl p-3 flex items-center gap-3 bg-slate-50/50 dark:bg-ink-800/40 hover:bg-slate-50 dark:hover:bg-ink-800 transition-colors"
                >
                  <div className="w-14 h-14 rounded-lg bg-white dark:bg-ink-900 border border-slate-200 dark:border-ink-700 flex items-center justify-center overflow-hidden shrink-0">
                    <img
                      src={img.image_url || ""}
                      alt={img.caption || "Referência"}
                      className="w-full h-full object-contain p-1"
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                      {img.caption || "Logo do Cliente"}
                    </p>
                    <a
                      href={img.image_url || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] text-brand-600 dark:text-brand-400 hover:underline mt-1"
                    >
                      <Download className="w-3 h-3" /> Baixar original
                    </a>
                  </div>
                  {canIterate && (
                    <button
                      type="button"
                      onClick={() => handleDeleteReferenceImage(img.id)}
                      disabled={acting}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                      title="Excluir anexo"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {actionError && (
          <div className="mt-4 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
            {actionError}
          </div>
        )}

        {/* Informações de envio */}
        {(order.shipping_address || order.shipping_city || order.shipping_state || order.shipping_zip_code || order.shipping_phone) && (
          <div className="mt-4 p-4 bg-slate-50 dark:bg-ink-700/30 rounded-lg">
            <h3 className="font-semibold text-sm mb-2 flex items-center gap-2">
              <Package className="w-4 h-4" /> Informações de envio
            </h3>
            <div className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
              {order.shipping_address && (
                <p>
                  {order.shipping_address}
                  {order.shipping_number && order.shipping_address && !order.shipping_address.includes(order.shipping_number) && `, ${order.shipping_number}`}
                  {order.shipping_complement && `, ${order.shipping_complement}`}
                  {order.shipping_neighborhood && ` - ${order.shipping_neighborhood}`}
                </p>
              )}
              {(order.shipping_city || order.shipping_state || order.shipping_zip_code) && (
                <p>
                  {order.shipping_city && order.shipping_city}
                  {order.shipping_city && (order.shipping_state || order.shipping_zip_code) && ", "}
                  {order.shipping_state && order.shipping_state}
                  {order.shipping_state && order.shipping_zip_code && " - "}
                  {order.shipping_zip_code && order.shipping_zip_code}
                </p>
              )}
              {order.shipping_phone && <p>Telefone: {order.shipping_phone}</p>}
            </div>
          </div>
        )}

        {/* Acoes */}
        <div className="flex flex-wrap gap-2 mt-5">
          {canSubmit && (
            <button onClick={submitOrder} disabled={acting} className="btn-primary disabled:opacity-60">
              {acting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Enviar ao seller
            </button>
          )}
          {canCancelClient && (
            <button onClick={cancelOrder} disabled={acting}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 disabled:opacity-60">
              <XCircle className="w-4 h-4" /> Cancelar pedido
            </button>
          )}
          {isClient && order.status === "approved" && order.estimated_price && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handlePayWithPixDirect}
                disabled={acting || actingPayment}
                className="btn-primary flex items-center gap-2"
              >
                {actingPayment ? <Loader2 className="w-4 h-4 animate-spin" /> : <QrCode className="w-4 h-4" />}
                Pagar com PIX
              </button>
              <button
                type="button"
                onClick={handleAddOrderToCart}
                disabled={acting || actingPayment}
                className="btn-outline flex items-center gap-2"
              >
                <ShoppingCart className="w-4 h-4" /> Adicionar ao carrinho
              </button>
            </div>
          )}
          {canSellerDecide && (
            <>
              <button onClick={sellerAccept} disabled={acting} className="btn-primary disabled:opacity-60">
                <Check className="w-4 h-4" /> Aceitar pedido
              </button>
              <button onClick={sellerReject} disabled={acting}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 disabled:opacity-60">
                <X className="w-4 h-4" /> Rejeitar
              </button>
            </>
          )}
          {isSeller && order.status === "approved" && (
            <div className="flex items-center gap-2 text-xs font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-3.5 py-2.5 rounded-xl border border-amber-200 dark:border-amber-800">
              <Loader2 className="w-4 h-4 animate-spin text-amber-500 shrink-0" />
              <span>Aguardando confirmação do pagamento pelo cliente para iniciar a produção.</span>
            </div>
          )}
          {isSeller && order.status === "paid" && !isPaymentConfirmed && (
            <div className="flex items-center gap-2 text-xs font-medium text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/40 px-3.5 py-2.5 rounded-xl border border-red-200 dark:border-red-800">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span>O pagamento PIX ainda não foi confirmado em custódia. Produção bloqueada.</span>
            </div>
          )}
          {canSellerProgress && order.status === "paid" && (
            <button onClick={() => updateStatus("in_production")} disabled={acting} className="btn-primary disabled:opacity-60">
              <Package className="w-4 h-4" /> Iniciar produção
            </button>
          )}
          {canSellerProgress && order.status === "in_production" && (
            <button onClick={() => updateStatus("sent")} disabled={acting} className="btn-primary disabled:opacity-60">
              <Package className="w-4 h-4" /> Marcar como enviado
            </button>
          )}
          {isClient && order.status === "sent" && (
            <button onClick={confirmDelivery} disabled={acting} className="btn-primary disabled:opacity-60">
              <Check className="w-4 h-4" /> Confirmar recebimento
            </button>
          )}
          {isClient && order.status === "delivered" && (
            <button onClick={completeOrder} disabled={acting} className="btn-primary disabled:opacity-60">
              <CheckCircle2 className="w-4 h-4" /> Marcar como concluído
            </button>
          )}
        </div>
      </div>

      {/* Bloco de Avaliação do Pedido (Disponível após Entrega / Conclusão) */}
      {(order.status === "delivered" || order.status === "completed") && (
        <div className="card p-6 mb-6 border-2 border-amber-200/60 dark:border-amber-500/20 bg-gradient-to-br from-white via-amber-50/20 to-white dark:from-ink-800 dark:via-ink-800/80 dark:to-ink-800">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                <Star className="w-5 h-5 fill-amber-500 text-amber-500" />
              </div>
              <div>
                <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                  {review ? "Avaliação do Pedido" : "Avalie sua Experiência"}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {review
                    ? "Sua opinião registrada para o vendedor e outros compradores"
                    : "Compartilhe o que achou da peça, do acabamento e do atendimento"}
                </p>
              </div>
            </div>

            {/* Se o cliente já avaliou e não está editando, botão para editar */}
            {isClient && review && !isEditingReview && (
              <button
                type="button"
                onClick={() => {
                  setRatingInput(review.rating);
                  setCommentInput(review.comment || "");
                  setIsEditingReview(true);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-ink-700 border border-slate-200 dark:border-ink-600 hover:bg-slate-50 dark:hover:bg-ink-600 transition shadow-sm"
              >
                <Edit3 className="w-3.5 h-3.5 text-brand-500" />
                Editar Avaliação
              </button>
            )}
          </div>

          {/* CASO 1: Cliente já avaliou e não está no modo de edição (ou é o vendedor visualizando a review) */}
          {review && !isEditingReview ? (
            <div className="bg-white dark:bg-ink-900/60 rounded-xl p-5 border border-slate-200/80 dark:border-ink-700/80">
              <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`w-5 h-5 ${
                          star <= review.rating
                            ? "fill-amber-400 text-amber-400"
                            : "text-slate-300 dark:text-slate-600"
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-200 ml-1">
                    {review.rating}.0
                  </span>
                  <span className="text-xs text-amber-600 dark:text-amber-400 font-medium bg-amber-50 dark:bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-200/50 dark:border-amber-500/20">
                    {RATING_LABELS[review.rating]}
                  </span>
                </div>

                <div className="text-xs text-slate-400 flex items-center gap-2">
                  <span>Avaliado em {formatReviewDate(review.created_at)}</span>
                  {review.is_edited && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 dark:bg-ink-700 text-slate-600 dark:text-slate-300 font-medium">
                      (Editada em {formatReviewDate(review.updated_at)})
                    </span>
                  )}
                </div>
              </div>

              {review.comment ? (
                <p className="text-sm text-slate-700 dark:text-slate-200 italic bg-slate-50/70 dark:bg-ink-800/50 p-3.5 rounded-lg border border-slate-100 dark:border-ink-700/50">
                  "{review.comment}"
                </p>
              ) : (
                <p className="text-xs text-slate-400 italic">Nenhum comentário por escrito.</p>
              )}
            </div>
          ) : isClient ? (
            /* CASO 2: Cliente avaliando pela primeira vez ou editando a avaliação existente */
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                  Sua Nota
                </label>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5">
                    {[1, 2, 3, 4, 5].map((star) => {
                      const active = (hoverRating || ratingInput) >= star;
                      return (
                        <button
                          key={star}
                          type="button"
                          onClick={() => setRatingInput(star)}
                          onMouseEnter={() => setHoverRating(star)}
                          onMouseLeave={() => setHoverRating(0)}
                          className="p-1 rounded-lg hover:scale-110 transition-transform focus:outline-none focus:ring-2 focus:ring-amber-400"
                        >
                          <Star
                            className={`w-7 h-7 transition-colors ${
                              active
                                ? "fill-amber-400 text-amber-400"
                                : "text-slate-300 dark:text-slate-600 hover:text-amber-300"
                            }`}
                          />
                        </button>
                      );
                    })}
                  </div>
                  <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 ml-2">
                    {RATING_LABELS[hoverRating || ratingInput] || "Selecione uma nota"}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                  Comentário (opcional)
                </label>
                <textarea
                  value={commentInput}
                  onChange={(e) => setCommentInput(e.target.value)}
                  placeholder="Conte o que achou da qualidade do produto, acabamento, fidelidade à personalização e atendimento do vendedor..."
                  rows={3}
                  maxLength={1000}
                  className="input text-sm resize-none"
                />
                <div className="flex justify-between items-center text-xs text-slate-400 mt-1">
                  <span>Você pode editar sua avaliação a qualquer momento depois de salvar.</span>
                  <span>{commentInput.length}/1000</span>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={handleSubmitReview}
                  disabled={submittingReview || ratingInput === 0}
                  className="btn-primary py-2 px-5 text-sm font-medium flex items-center gap-2 disabled:opacity-50"
                >
                  {submittingReview ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Star className="w-4 h-4 fill-current" />
                  )}
                  {review ? "Atualizar Avaliação" : "Publicar Avaliação"}
                </button>

                {isEditingReview && (
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingReview(false);
                      setRatingInput(review?.rating || 5);
                      setCommentInput(review?.comment || "");
                    }}
                    disabled={submittingReview}
                    className="btn-outline py-2 px-4 text-sm"
                  >
                    Cancelar
                  </button>
                )}
              </div>
            </div>
          ) : (
            /* CASO 3: O vendedor está visualizando e o cliente ainda não avaliou */
            <div className="text-sm text-slate-500 dark:text-slate-400 bg-white dark:bg-ink-900/60 p-4 rounded-xl border border-slate-200/80 dark:border-ink-700/80 text-center">
              O comprador ainda não avaliou este pedido. Assim que ele enviar a avaliação, a nota e o comentário ficarão visíveis aqui e na página da sua loja.
            </div>
          )}
        </div>
      )}


      {/* Iteracoes - apenas para pedidos personalizados */}
      {/* Iteracoes */}
      {order.product_type === "customized" || order.iterations.length > 0 || canIterate ? (
        <div className="mb-6">
          <div className="flex items-baseline justify-between mb-4">
            <h2 className="text-xl font-bold">Iterações</h2>
            <span className="text-sm text-slate-500">
              {order.iterations.length} {order.iterations.length === 1 ? "versão" : "versões"}
            </span>
          </div>

          {order.iterations.length === 0 ? (
            <div className="card p-10 text-center text-slate-500 space-y-3">
              <Sparkles className="w-10 h-10 mx-auto text-brand-500/50" />
              <p className="font-medium text-slate-700 dark:text-slate-300">Nenhuma iteração gerada ainda.</p>
              <p className="text-sm text-slate-400 max-w-md mx-auto">
                Gere a primeira versão agora usando a descrição do pedido ou adicione mais detalhes no campo abaixo.
              </p>
              {canIterate && (
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => generateIteration(order.description)}
                    disabled={generating}
                    className="btn-primary inline-flex items-center gap-2"
                  >
                    {generating ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Gerando 1ª versão com IA...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        <span>Gerar 1ª versão com IA agora</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {order.iterations.map((it) => (
                <IterationCard
                  key={it.id}
                  iteration={it}
                  isApproved={order.approved_iteration_id === it.id}
                  canApprove={canIterate || false}
                  onApprove={() => approveIteration(it.id)}
                  disabled={acting}
                />
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Imagem do produto para pedidos regulares */
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-4">Imagem do Produto</h2>
          <div className="card p-4">
            {order.image_url ? (
              <img
                src={order.image_url}
                alt={order.title}
                className="w-full max-w-md mx-auto rounded-lg object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                  (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                }}
              />
            ) : null}
            {(!order.image_url || order.image_url === '/placeholder-product.png') && (
              <div className="w-full max-w-md mx-auto rounded-lg bg-slate-100 dark:bg-ink-700/60 flex items-center justify-center aspect-square">
                <Package className="w-24 h-24 text-slate-300 dark:text-slate-600" />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Form de nova iteracao */}
      {canIterate && (
        <div className="card p-6">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-brand-500" />
            {order.iterations.length === 0 ? "Gerar 1ª versão com IA" : "Nova iteração com IA"}
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
            {order.iterations.length === 0
              ? "Refine sua ideia abaixo ou clique no botão para gerar a 1ª versão usando a descrição inicial do pedido."
              : "Refine sua ideia. A cada nova descrição, a IA gera uma nova versão."}
          </p>
          {iterationsLimit && iterationsLimit.enabled && (
            <div className="mb-4 flex items-center gap-2 text-sm font-medium text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-500/10 px-3 py-2 rounded-lg">
              <Sparkles className="w-4 h-4" />
              <span>{iterationsLimit.remaining} iterações restantes hoje</span>
            </div>
          )}
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input resize-none"
            placeholder={
              order.iterations.length === 0
                ? (order.description || "Descreva sua ideia para gerar a 1ª versão...")
                : "Ex.: Estilo aquarela, cores pasteis, fundo branco..."
            }
          />
          <button
            onClick={() => generateIteration()}
            disabled={generating || (order.iterations.length > 0 && description.trim().length < 5 && !order.description)}
            className="btn-primary mt-3 disabled:opacity-60 flex items-center gap-2"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Gerando com IA...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>{order.iterations.length === 0 ? "Gerar 1ª versão com IA" : "Gerar nova versão"}</span>
              </>
            )}
          </button>
        </div>
      )}

      <Modal open={showAcceptModal} onClose={() => { setShowAcceptModal(false); setAcceptPrice(""); }} title="Definir preço do pedido">
        <div className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Defina o preço para este pedido. O cliente será notificado e poderá prosseguir com o pagamento.
          </p>
          <div>
            <label className="label">Preço (R$)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={acceptPrice}
              onChange={(e) => setAcceptPrice(e.target.value)}
              className="input"
              placeholder="29.90"
            />
          </div>
          {actionError && (
            <div className="text-sm text-red-600 dark:text-red-400">{actionError}</div>
          )}
          <button
            onClick={confirmAcceptWithPrice}
            disabled={acting || !acceptPrice}
            className="btn-primary w-full disabled:opacity-60"
          >
            {acting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            Aceitar e definir preço
          </button>
        </div>
      </Modal>
      <Toast
        show={toast.show}
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ show: false, message: "", type: "success" })}
      />

      <Modal
        open={showLimitModal}
        onClose={() => setShowLimitModal(false)}
        title="Limite de iterações atingido"
        maxWidth="max-w-md"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-amber-600 dark:text-amber-400">
            <Sparkles className="w-6 h-6" />
            <p className="font-semibold">Você atingiu o limite diário</p>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Você atingiu o limite de iterações com IA por dia. O limite é reiniciado diariamente às 00:00 UTC.
          </p>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Tente novamente amanhã para criar novas iterações.
          </p>
          <button
            onClick={() => setShowLimitModal(false)}
            className="btn-primary w-full"
          >
            Entendi
          </button>
        </div>
      </Modal>
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
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Valor do Pedido</p>
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
                  <AlertCircle className="w-4 h-4" /> Pagamento Falhou ou Cancelado
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
            {paymentModal.pixCode && (
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
            )}

            {/* Painel Didático de Simulação */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-ink-700/50 border border-slate-200 dark:border-ink-600 mb-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2">
                Ambiente de Testes Didáticos (TCC)
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => handleSimulatePayment("approve")}
                  disabled={simulatingPayment || paymentModal.status === "paid"}
                  className="btn-primary !bg-emerald-600 hover:!bg-emerald-700 !py-2 text-xs font-semibold flex items-center justify-center gap-1.5"
                >
                  {simulatingPayment ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                  Simular Sucesso
                </button>
                <button
                  onClick={() => handleSimulatePayment("fail")}
                  disabled={simulatingPayment || paymentModal.status === "paid"}
                  className="btn-secondary !text-red-600 dark:!text-red-400 hover:!bg-red-50 dark:hover:!bg-red-950/30 !py-2 text-xs font-semibold flex items-center justify-center gap-1.5"
                >
                  {simulatingPayment ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <AlertCircle className="w-3.5 h-3.5" />}
                  Simular Falha
                </button>
              </div>
            </div>

            {/* Botões de Ação */}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setPaymentModal(null)}
                className="btn-primary text-sm py-2 px-5"
              >
                Concluir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function IterationCard({
  iteration, isApproved, canApprove, onApprove, disabled,
}: {
  iteration: Iteration;
  isApproved: boolean;
  canApprove: boolean;
  onApprove: () => void;
  disabled: boolean;
}) {
  return (
    <div className={`card p-4 flex flex-col gap-3 transition-all ${isApproved ? "ring-2 ring-brand-500" : ""}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold text-slate-500 dark:text-slate-400">v{iteration.version}</span>
        {isApproved && (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-brand-500">
            <CheckCircle2 className="w-3.5 h-3.5" /> Aprovada
          </span>
        )}
      </div>

      <div className="aspect-square w-full rounded-xl overflow-hidden bg-slate-100 dark:bg-ink-700/50 flex items-center justify-center">
        {iteration.status === "ready" || iteration.status === "approved" ? (
          iteration.image_url ? (
            <img src={iteration.image_url} alt={`v${iteration.version}`} className="w-full h-full object-cover" />
          ) : (
            <Sparkles className="w-10 h-10 text-slate-300" />
          )
        ) : iteration.status === "generating" || iteration.status === "pending" ? (
          <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
        ) : (
          <XCircle className="w-10 h-10 text-red-400" />
        )}
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-300 line-clamp-3">{iteration.description}</p>

      {canApprove && !isApproved && (iteration.status === "ready" || iteration.status === "approved") && (
        <button
          onClick={onApprove}
          disabled={disabled}
          className="btn-outline w-full text-sm disabled:opacity-60"
        >
          <Check className="w-4 h-4" /> Escolher esta
        </button>
      )}
      {iteration.status === "failed" && (
        <p className="text-xs text-red-500">Falha na geração da imagem</p>
      )}
    </div>
  );
}
