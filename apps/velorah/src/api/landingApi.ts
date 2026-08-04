const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
export const APP_URL = import.meta.env.VITE_APP_URL || "http://localhost:3000";

export type PlanTier = "free" | "hobbyist" | "professional" | "enterprise";

export interface PlanFeatures {
  projects_limit: number | null;
  storage_gb: number | null;
  ai_suggestions: boolean;
  collaboration_users: number | null;
  export_formats: string[] | string;
  cad_features: string[] | string;
  pcb_features: string[] | string;
  simulation: boolean | string;
}

export interface PlanPricing {
  tier: PlanTier;
  price_monthly: number | null;
  price_annual: number | null;
  is_custom: boolean;
  features: PlanFeatures;
}

export interface PricingResponse {
  plans: PlanPricing[];
}

export interface SignupPayload {
  email: string;
  password: string;
  name: string;
  plan_tier: PlanTier;
  company?: string;
  referral_source?: string;
}

export interface SignupResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: { id: string; email: string; name: string };
  organization_id: string;
  checkout_url: string | null;
  contact_sales: boolean;
  trial_ends: string | null;
}

export interface AgeVerificationResponse {
  verified: boolean;
  age: number;
  verified_at: string;
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body?.error?.message || body?.detail || `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const landingApi = {
  async getPricing(): Promise<PricingResponse> {
    return request<PricingResponse>("/landing/pricing");
  },

  async signup(payload: SignupPayload): Promise<SignupResponse> {
    return request<SignupResponse>("/landing/signup", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async verifyAge(accessToken: string, birthYear: number, country = "US"): Promise<AgeVerificationResponse> {
    return request<AgeVerificationResponse>("/age/verify", {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify({ birth_year: birthYear, country }),
    });
  },

  async trackEvent(event: string, properties: Record<string, unknown> = {}): Promise<void> {
    try {
      await request("/landing/analytics/event", {
        method: "POST",
        body: JSON.stringify({ event, properties, url: window.location.href }),
      });
    } catch {
      // Analytics failures should never break the page for a visitor.
    }
  },
};

export { ApiError };
