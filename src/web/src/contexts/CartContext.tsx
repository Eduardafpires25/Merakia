import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

export interface CartItem {
  id: string;
  user_id: string;
  seller_id: string;
  product_spec_id: string | null;
  order_id: string | null;
  selected_options: string | null;
  quantity: number;
  unit_price: number;
  total_price: number;
  name: string;
  description: string | null;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Cart {
  items: CartItem[];
  total: number;
  total_items: number;
  grouped_by_seller: Record<string, CartItem[]>;
}

export interface CheckoutResult {
  order_ids: string[];
  total_amount: number;
  message: string;
  payment_id?: string;
  pix_code?: string;
  pix_qr_code?: string;
  payment_status?: string;
}

export interface CartContextType {
  cart: Cart | null;
  loading: boolean;
  error: string | null;
  fetchCart: () => Promise<void>;
  addToCart: (data: {
    product_spec_id?: string;
    order_id?: string;
    quantity?: number;
    selected_options?: string;
  }) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  checkout: (
    sellerIds: string[],
    ignoreErrors?: boolean,
    shippingInfo?: {
      shipping_address: string;
      shipping_number?: string;
      shipping_complement?: string;
      shipping_neighborhood?: string;
      shipping_city: string;
      shipping_state: string;
      shipping_zip_code: string;
      shipping_phone: string;
      save_address_to_profile?: boolean;
    }
  ) => Promise<CheckoutResult>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const location = useLocation();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCart = useCallback(async () => {
    if (!user) {
      setCart(null);
      return;
    }
    try {
      const response = await api.get<Cart>("/cart/");
      setCart(response.data);
    } catch (err: any) {
      if (err.response?.status === 401) {
        setCart(null);
      } else {
        console.error("Erro ao carregar carrinho:", err);
      }
    }
  }, [user]);

  // Sincroniza carrinho no mount, ao trocar de usuário e a cada navegação entre rotas
  useEffect(() => {
    fetchCart();
  }, [fetchCart, location.pathname]);

  // Polling suave a cada 30s
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(fetchCart, 30000);
    return () => clearInterval(interval);
  }, [user, fetchCart]);

  const addToCart = async (data: {
    product_spec_id?: string;
    order_id?: string;
    quantity?: number;
    selected_options?: string;
  }) => {
    setLoading(true);
    setError(null);
    try {
      await api.post<CartItem>("/cart/items", data);
      await fetchCart();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erro ao adicionar ao carrinho");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId: string, quantity: number) => {
    setLoading(true);
    setError(null);
    try {
      await api.patch<CartItem>(`/cart/items/${itemId}`, { quantity });
      await fetchCart();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erro ao atualizar quantidade");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const removeItem = async (itemId: string) => {
    setLoading(true);
    setError(null);
    try {
      await api.delete(`/cart/items/${itemId}`);
      await fetchCart();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erro ao remover item");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const checkout = async (
    sellerIds: string[],
    ignoreErrors = false,
    shippingInfo?: {
      shipping_address: string;
      shipping_number?: string;
      shipping_complement?: string;
      shipping_neighborhood?: string;
      shipping_city: string;
      shipping_state: string;
      shipping_zip_code: string;
      shipping_phone: string;
      save_address_to_profile?: boolean;
    }
  ): Promise<CheckoutResult> => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post<CheckoutResult>("/cart/checkout", {
        seller_ids: sellerIds,
        ignore_errors: ignoreErrors,
        ...shippingInfo,
      });
      await fetchCart();
      return response.data;
    } catch (err: any) {
      console.error("Erro no checkout:", err);
      setError(err.response?.data?.detail || "Erro ao fazer checkout");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return (
    <CartContext.Provider
      value={{
        cart,
        loading,
        error,
        fetchCart,
        addToCart,
        updateQuantity,
        removeItem,
        checkout,
      }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}
