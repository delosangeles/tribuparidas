/** Tipos del Portal de emprendimientos y de "Mi tarjeta". */

export type PortalRole = "owner" | "seller";

export interface PortalBusinessRef {
  business_id: number;
  name: string;
  slug: string;
  role: PortalRole;
  logo: string | null;
}

export interface PortalBusiness {
  id: number;
  name: string;
  slug: string;
  logo: string | null;
  description: string;
  category: number;
  category_name: string;
  city: string;
  department: string;
  address: string;
  whatsapp: string;
  instagram: string;
  facebook: string;
  website: string;
  opening_hours: string;
  home_delivery: boolean;
  responsible_name: string;
  status: "pending" | "approved" | "rejected";
  average_rating: string;
  public_path: string;
}

export interface PortalImage {
  id: number;
  image: string;
  caption: string;
  order: number;
  is_main: boolean;
}

export interface PortalReview {
  id: number;
  user_name: string;
  rating: number;
  comment: string;
  reply: { text: string; updated_at: string } | null;
  created_at: string;
}

export interface PortalFAQ {
  id: number;
  question: string;
  answer: string;
  order: number;
}

export type BenefitStatus = "pending" | "approved" | "rejected";

export interface PortalBenefit {
  id: number;
  percentage: number;
  conditions: string;
  valid_from: string | null;
  valid_until: string | null;
  status: BenefitStatus;
}

export interface PublicBenefit {
  percentage: number;
  conditions: string;
  valid_from: string | null;
  valid_until: string | null;
}

export interface PortalChange {
  id: number;
  entity: string;
  action: string;
  changes: Record<string, { from: string | null; to: string | null }>;
  actor_name: string;
  created_at: string;
}

export interface PeriodCounts {
  today: number;
  last_7_days: number;
  last_30_days: number;
  total: number;
}

export interface PortalStats {
  visits: PeriodCounts;
  redemptions: PeriodCounts;
}

export interface PortalMember {
  id: number;
  first_name: string;
  last_name: string;
  whatsapp: string;
  email: string;
  last_activity: string | null;
  redemption_count: number;
}

export interface RedeemPreview {
  member: { name: string; status: string };
  benefit: { percentage: number; conditions: string };
  ticket: string;
}

export interface RedeemError {
  code: string;
  detail: string;
  member?: { name: string };
}

export type CardBlocker = "not_member" | "inactive" | "membership_inactive" | "missing_document" | "consent_required";

export interface CardBenefit {
  business_id: number;
  name: string;
  slug: string;
  logo: string | null;
  percentage: number;
  conditions: string;
  valid_until: string | null;
}

export interface MyCard {
  eligible: boolean;
  blockers: CardBlocker[];
  name: string;
  membership_active: boolean;
  consent_version: string;
  benefits: CardBenefit[];
  token?: string;
  code?: string;
  expires_in?: number;
}

export interface MemberNotice {
  id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface BusinessOwnerRow {
  id: number;
  user: number;
  user_name: string;
  user_email: string;
  account_type: "member" | "portal";
  business: number;
  business_name: string;
  role: PortalRole;
  created_at: string;
}

export interface AdminBenefit extends PortalBenefit {
  business_id: number;
  business_name: string;
}

export interface MembershipRow {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  whatsapp: string;
  membership_active: boolean;
  has_document: boolean;
}
