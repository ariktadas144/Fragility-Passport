// Thin client for the Fragility Passport backend (FastAPI, see
// docs/ml-backend-contract.md and backend/app/schemas/*). Base URL comes from
// NEXT_PUBLIC_API_BASE_URL (see .env.local / .env.example) so it is not
// hardcoded to localhost.

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`POST ${path} failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

// ---- Response shapes (mirror backend/app/schemas) ----

export interface DashboardSummary {
  total_events: number;
  events_by_risk_level: Record<string, number>;
  events_by_dock: Record<string, number>;
  events_by_behavior: Record<string, number>;
  active_alerts: number;
  escalated_alerts: number;
  total_estimated_exposure_inr: number;
}

export interface EventListItem {
  id: number;
  public_id: string;
  dock: string | null;
  start_time_seconds: number;
  risk_level: string;
  risk_score: number;
  status: string;
  behaviors: string[];
}

export interface ProductRead {
  id: number;
  sku: string;
  name: string;
  category: string;
  declared_value_inr: number;
}

export interface EventRead {
  id: number;
  public_id: string;
  video_id: number | null;
  dock: string | null;
  start_time_seconds: number;
  end_time_seconds: number;
  risk_level: string;
  risk_score: number;
  confidence: number;
  status: string;
  evidence_description: string | null;
  recommended_action: string | null;
  contract_clause_violated: string | null;
  estimated_exposure_inr: number | null;
  created_at: string;
  behaviors: string[];
  potential_consequence: string[];
  product: ProductRead | null;
  evidence_paths: string[];
}

export interface FragilityPassportRead {
  id: number;
  product_id: number;
  max_tilt_deg: number;
  max_drop_height_cm: number;
  required_orientation: string;
  max_stack_weight_kg: number;
  drag_allowed: boolean;
  throw_allowed: boolean;
  notes: string | null;
}

export interface AssistantAnswer {
  answer: string;
  source: "local" | "llm" | "unavailable";
  data?: unknown;
}

export const api = {
  dashboardSummary: () => getJSON<DashboardSummary>("/dashboard/summary"),
  events: () => getJSON<EventListItem[]>("/events"),
  event: (id: number) => getJSON<EventRead>(`/events/${id}`),
  /** GET /events, then hydrate each with its full detail (contract clause,
   *  INR exposure, product) — the list endpoint only returns a slim shape. */
  eventsDetailed: async (): Promise<EventRead[]> => {
    const list = await getJSON<EventListItem[]>("/events");
    return Promise.all(list.map((e) => getJSON<EventRead>(`/events/${e.id}`)));
  },
  products: () => getJSON<ProductRead[]>("/products"),
  passportForProduct: (productId: number) =>
    getJSON<FragilityPassportRead>(`/passports/${productId}`),
  askAssistant: (question: string) =>
    postJSON<AssistantAnswer>("/assistant/query", { question }),
};

// ---- Small display helpers ----

export type BadgeVariant =
  | "default" | "secondary" | "destructive" | "outline"
  | "critical" | "high" | "medium" | "low";

export function riskBadgeVariant(riskLevel: string): BadgeVariant {
  const v = riskLevel.toLowerCase();
  if (v === "critical" || v === "high" || v === "medium" || v === "low") return v;
  return "default";
}

export function formatInr(amount: number | null | undefined): string {
  if (amount == null) return "—";
  return `₹${Math.round(amount).toLocaleString("en-IN")}`;
}

/** "product_dragged" -> "Product Dragged" */
export function humanizeBehavior(code: string): string {
  return code
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
