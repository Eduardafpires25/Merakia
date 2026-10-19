import axios from "axios";
import { Image as ImageIcon, Loader2, Sparkles, Upload, X } from "lucide-react";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import type { Order, ProductListItem } from "../types/api";
import { ColorSwatchSelector, isColorOption, normalizeColorOptions } from "./ColorSwatchSelector";
import { Modal } from "./Modal";

interface Props {
  open: boolean;
  onClose: () => void;
  sellerId: string;
  sellerName: string;
  product?: ProductListItem;
}

export function CreateOrderModal({ open, onClose, sellerId, sellerName, product }: Props) {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Anexo de referência/logo
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [referencePreview, setReferencePreview] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        setError("O arquivo deve ter no máximo 10MB.");
        return;
      }
      setReferenceFile(file);
      setReferencePreview(URL.createObjectURL(file));
      setError(null);
    }
  };

  const removeFile = () => {
    setReferenceFile(null);
    if (referencePreview) {
      URL.revokeObjectURL(referencePreview);
      setReferencePreview(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const [loadingStep, setLoadingStep] = useState<string>("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    setLoadingStep("Criando pedido...");
    try {
      const { data } = await api.post<Order>("/orders/", {
        seller_id: sellerId,
        title,
        description,
        product_type: "customized",
        product_options: Object.keys(selectedOptions).length > 0 ? selectedOptions : undefined,
        quantity,
      });

      // Se houver anexo de logo/referência, faz o upload para o pedido criado
      if (referenceFile) {
        setLoadingStep("Enviando logo / imagem de referência...");
        const formData = new FormData();
        formData.append("file", referenceFile);
        formData.append("caption", "Logo / Referência do cliente");
        try {
          await api.post(`/orders/${data.id}/reference-images`, formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });
        } catch (uploadErr) {
          console.error("Falha ao enviar imagem de referência:", uploadErr);
        }
      }

      // Gera a 1ª versão automaticamente com a IA usando a descrição informada!
      setLoadingStep("Gerando 1ª versão com IA...");
      try {
        await api.post(`/orders/${data.id}/iterations`, { description });
      } catch (iterErr) {
        console.error("Falha ao gerar primeira versão imediatamente:", iterErr);
      }

      navigate(`/orders/${data.id}`);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          navigate("/login", { state: { from: `/sellers` } });
          return;
        }
        setError(err.response?.data?.detail || "Falha ao criar pedido.");
      } else {
        setError("Erro inesperado.");
      }
    } finally {
      setLoading(false);
      setLoadingStep("");
    }
  };

  const handleOptionChange = (optionKey: string, value: string) => {
    setSelectedOptions((prev) => ({ ...prev, [optionKey]: value }));
  };

  return (
    <Modal open={open} onClose={onClose} title={`Novo pedido - ${sellerName}`}>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label className="label">Título</label>
          <input
            required
            minLength={3}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
            placeholder="Ex.: Caneca personalizada com a logo da minha empresa"
          />
        </div>

        <div>
          <label className="label">
            Descrição do que você deseja{" "}
            <span className="text-slate-400 font-normal">(instruções para personalização e IA)</span>
          </label>
          <textarea
            required
            minLength={5}
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input resize-none"
            placeholder="Descreva sua ideia, elementos visuais e como gostaria que ficasse. Você poderá refinar com a IA."
          />
        </div>

        {/* Anexo de Foto / Logo da Empresa */}
        <div>
          <label className="label flex items-center justify-between">
            <span>Anexar foto ou logotipo <span className="text-slate-400 font-normal">(opcional)</span></span>
            <span className="text-xs text-slate-400">PNG, JPG até 10MB</span>
          </label>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            onChange={handleFileChange}
            className="hidden"
          />

          {!referencePreview ? (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full border-2 border-dashed border-slate-300 dark:border-ink-600 hover:border-brand-500 rounded-xl p-4 flex flex-col items-center justify-center gap-2 transition-colors bg-slate-50/50 dark:bg-ink-800/40 text-slate-600 dark:text-slate-300 group"
            >
              <div className="w-10 h-10 rounded-full bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center text-brand-500 group-hover:scale-105 transition-transform">
                <Upload className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium">Clique para enviar a logo ou foto de referência</span>
              <span className="text-xs text-slate-400">A logo será preservada e enviada para o vendedor</span>
            </button>
          ) : (
            <div className="relative border border-slate-200 dark:border-ink-700 rounded-xl p-3 flex items-center gap-3 bg-slate-50 dark:bg-ink-800/60">
              <div className="w-14 h-14 rounded-lg bg-white dark:bg-ink-900 border border-slate-200 dark:border-ink-700 flex items-center justify-center overflow-hidden shrink-0">
                <img
                  src={referencePreview}
                  alt="Pré-visualização do anexo"
                  className="w-full h-full object-contain p-1"
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                  {referenceFile?.name}
                </p>
                <p className="text-xs text-slate-400">
                  {referenceFile ? `${(referenceFile.size / 1024).toFixed(0)} KB` : ""}
                </p>
              </div>
              <button
                type="button"
                onClick={removeFile}
                className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-ink-700 text-slate-400 hover:text-red-500 transition-colors"
                title="Remover anexo"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Opções de Personalização (incluindo Cartela de Cores) */}
        {product?.is_customizable && product.customization_options && (
          <div className="space-y-4 p-4 bg-slate-50 dark:bg-ink-800/50 rounded-xl border border-slate-100 dark:border-ink-700/50">
            <h4 className="font-semibold text-sm text-slate-900 dark:text-white flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-brand-500" />
              Opções de personalização
            </h4>

            {Object.entries(product.customization_options).map(([key, values]) => {
              const isColor = isColorOption(key, values);

              if (isColor) {
                const colors = normalizeColorOptions(values);
                return (
                  <div key={key} className="space-y-1.5">
                    <label className="label text-xs capitalize mb-1">
                      {key}: Selecione a cor
                    </label>
                    <ColorSwatchSelector
                      colors={colors}
                      selected={selectedOptions[key]}
                      onChange={(colorName) => handleOptionChange(key, colorName)}
                    />
                  </div>
                );
              }

              return (
                <div key={key}>
                  <label className="label text-xs capitalize">{key}</label>
                  <select
                    required
                    value={selectedOptions[key] || ""}
                    onChange={(e) => handleOptionChange(key, e.target.value)}
                    className="input"
                  >
                    <option value="">Selecione...</option>
                    {Array.isArray(values)
                      ? values.map((v: unknown) => {
                          const valStr = typeof v === "object" && v !== null && "name" in v ? (v as { name: string }).name : String(v);
                          return (
                            <option key={valStr} value={valStr}>
                              {valStr}
                            </option>
                          );
                        })
                      : null}
                  </select>
                </div>
              );
            })}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="label">Quantidade</label>
            <input
              type="number"
              min={1}
              max={10000}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              className="input"
            />
          </div>
        </div>

        {error && (
          <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 px-3 py-2 rounded-lg">
            {error}
          </div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-60 flex items-center justify-center gap-2">
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{loadingStep || "Processando..."}</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Criar e gerar 1ª versão com IA</span>
            </>
          )}
        </button>
      </form>
    </Modal>
  );
}
