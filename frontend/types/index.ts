export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_entrepreneur: boolean;
  is_active?: boolean;
  businesses_count?: number;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  image: string | null;
  is_active: boolean;
  businesses_count?: number;
  created_at: string;
}

export type BusinessStatus = "pending" | "approved" | "rejected";

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
  logo?: File | null;
  cover_image?: File | null;
}

export interface Product {
  id: number;
  business: number;
  name: string;
  slug: string;
  description: string;
  image: string | null;
  price: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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
