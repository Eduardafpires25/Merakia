export type UserRole = "client" | "seller" | "admin";

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string | null;
  avatar_url?: string | null;
  zip_code?: string | null;
  address?: string | null;
  number?: string | null;
  complement?: string | null;
  neighborhood?: string | null;
  city?: string | null;
  state?: string | null;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  email_verified: boolean;
  created_at: string;
}


export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  phone?: string;
  role: UserRole;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export type SellerCategory =
  | "mug"
  | "shirt"
  | "poster"
  | "sticker"
  | "keychain"
  | "tote_bag"
  | "ceramic"
  | "woodwork"
  | "jewelry"
  | "other";

export function formatCategory(category: SellerCategory): string {
  const categoryMap: Record<SellerCategory, string> = {
    mug: "Canecas",
    shirt: "Camisetas",
    poster: "Posters",
    sticker: "Adesivos",
    keychain: "Chaveiros",
    tote_bag: "Ecobags",
    ceramic: "Cerâmica",
    woodwork: "Madeira",
    jewelry: "Bijuterias",
    other: "Outros",
  };
  return categoryMap[category] || category;
}

export interface SellerListItem {
  id: string;
  store_name: string;
  slug: string;
  description?: string | null;
  category: SellerCategory;
  whatsapp?: string | null;
  instagram?: string | null;
  city?: string | null;
  state?: string | null;
  min_order_quantity: number;
  estimated_days?: number | null;
  accepts_custom_designs?: boolean;
  user_name?: string | null;
  logo_url?: string | null;
  average_rating?: number | null;
  total_reviews?: number;
}

export interface SellerListResponse {
  items: SellerListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface ProductImage {
  id: string;
  product_spec_id: string;
  url: string;
  alt_text?: string | null;
  position: number;
  is_cover: boolean;
  created_at: string;
}

export interface ProductListItem {
  id: string;
  name: string;
  description?: string | null;
  is_customizable: boolean;
  customization_options: Record<string, any>;
  base_price?: string | null;
  is_active: boolean;
  cover_url?: string | null;
}

export interface SellerDetail extends SellerListItem {
  user_id: string;
  accepts_custom_designs: boolean;
  is_open: boolean;
  banner_url?: string | null;
  user_email?: string | null;
  user_avatar_url?: string | null;
  email_verified?: boolean | null;
  created_at: string;
  updated_at: string;
  products: ProductListItem[];
}

export type OrderStatus =
  | "draft"
  | "in_analysis"
  | "approved"
  | "paid"
  | "in_production"
  | "sent"
  | "delivered"
  | "completed"
  | "cancelled";

export type IterationStatus = "pending" | "generating" | "ready" | "failed" | "approved";

export interface Iteration {
  id: string;
  order_id: string;
  version: number;
  description: string;
  prompt?: string | null;
  image_url?: string | null;
  image_key?: string | null;
  ai_model?: string | null;
  status: IterationStatus;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderReferenceImage {
  id: string;
  order_id: string;
  image_key: string;
  image_url?: string | null;
  caption?: string | null;
  position: number;
  created_at: string;
}

export interface Order {
  id: string;
  title: string;
  description: string;
  product_type?: string | null;
  product_options?: Record<string, any>;
  quantity: number;
  estimated_price?: string | null;
  status: OrderStatus;
  client_id: string;
  seller_id?: string | null;
  approved_iteration_id?: string | null;
  submitted_at?: string | null;
  approved_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at: string;
  iterations: Iteration[];
  approved_iteration?: Iteration | null;
  reference_images?: OrderReferenceImage[];
  image_url?: string | null;
  shipping_address?: string | null;
  shipping_number?: string | null;
  shipping_complement?: string | null;
  shipping_neighborhood?: string | null;
  shipping_city?: string | null;
  shipping_state?: string | null;
  shipping_zip_code?: string | null;
  shipping_phone?: string | null;
}

export interface OrderListItem {
  id: string;
  title: string;
  product_type?: string | null;
  quantity: number;
  estimated_price?: string | number | null;
  status: OrderStatus;
  seller_id?: string | null;
  client_id: string;
  cover_url?: string | null;
  submitted_at?: string | null;
  created_at: string;
}

export interface OrderListResponse {
  items: OrderListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface ApiErrorBody {
  detail?: string | { field: string; message: string }[];
  errors?: { field: string; message: string }[];
}

export interface OrderReview {
  id: string;
  order_id?: string | null;
  seller_id: string;
  client_id?: string | null;
  client_name: string;
  product_title?: string | null;
  rating: number;
  comment?: string | null;
  is_edited: boolean;
  created_at: string;
  updated_at: string;
}

export interface SellerReviewsListResponse {
  items: OrderReview[];
  total: number;
  average_rating: number;
  rating_distribution: Record<number, number>;
}
