export type UserRole = "user" | "admin" | "super_admin";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  whatsapp: string;
  is_staff: boolean;
  is_superuser: boolean;
  role: UserRole;
  is_entrepreneur: boolean;
  is_active?: boolean;
  businesses_count?: number;
  created_at: string;
}

export type NotificationType = "new_registration" | "password_reset_request";

export interface AppNotification {
  id: number;
  type: NotificationType;
  message: string;
  related_user: number | null;
  related_user_email: string | null;
  is_read: boolean;
  created_at: string;
}

export interface ActivityLogEntry {
  id: number;
  actor_email: string | null;
  actor_name: string | null;
  action: string;
  description: string;
  target_type: string | null;
  object_id: number | null;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  image: string | null;
  is_active: boolean;
  parent: number | null;
  parent_name?: string | null;
  subcategories?: Category[];
  businesses_count?: number;
  created_at: string;
}

export type BusinessStatus = "pending" | "approved" | "rejected";

export type BenefitType =
  | "descuento"
  | "envio_gratis"
  | "promocion"
  | "precio_especial"
  | "beneficio_exclusivo"
  | "otro"
  | "";

export interface BusinessImage {
  id: number;
  business: number;
  image: string;
  caption: string;
  order: number;
  created_at: string;
}

export interface Business {
  id: number;
  owner?: number;
  name: string;
  slug: string;
  logo: string | null;
  cover_image: string | null;
  description: string;
  category: Category;
  city: string;
  department: string;
  address: string;
  whatsapp: string;
  instagram: string;
  facebook: string;
  website: string;
  opening_hours: string;
  status: BusinessStatus;
  average_rating: string;
  home_delivery: boolean;
  tribe_benefit: boolean;
  benefit_type: BenefitType;
  benefit_detail: string;
  is_mama_tribu: boolean;
  responsible_name: string;
  tribe_recommended: boolean;
  images?: BusinessImage[];
  created_at: string;
  updated_at?: string;
}

export interface BusinessFormPayload {
  name: string;
  description: string;
  category: number;
  city: string;
  department: string;
  address: string;
  whatsapp: string;
  instagram: string;
  facebook: string;
  website: string;
  opening_hours: string;
  home_delivery: boolean;
  tribe_benefit: boolean;
  benefit_type: BenefitType;
  benefit_detail: string;
  is_mama_tribu: boolean;
  responsible_name: string;
  tribe_recommended: boolean;
  logo?: File | null;
  cover_image?: File | null;
}

export interface Answer {
  id: number;
  question: number;
  user: number;
  user_name: string;
  answer: string;
  is_active: boolean;
  created_at: string;
}

export interface Question {
  id: number;
  business: number;
  business_name: string;
  user: number;
  user_name: string;
  question: string;
  answer: Answer | null;
  is_active: boolean;
  created_at: string;
}

export interface Review {
  id: number;
  business: number;
  user: number;
  user_name: string;
  rating: number;
  comment: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Favorite {
  id: number;
  business: Business;
  created_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  [field: string]: unknown;
}

export interface AnalyticsSummary {
  total_pageviews: number;
  unique_sessions: number;
  unique_users: number;
  by_day: { day: string; count: number }[];
  by_hour: { hour: number; count: number }[];
  top_pages: { path: string; count: number }[];
  last_pages: { path: string; count: number }[];
}
