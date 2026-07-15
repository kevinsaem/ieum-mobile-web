export type UserRole = "DONOR" | "MEMBER" | "ADMIN";

export interface SessionUser {
  id: string;
  name: string;
  role: UserRole;
  organization_id: string | null;
  organization_name: string | null;
}

export interface SessionData {
  access_token: string;
  token_type: string;
  user: SessionUser;
}

export interface Offer {
  id: string;
  category: string;
  title: string;
  quantity: number;
  remaining_quantity: number;
  unit: string;
  status: string;
  version: number;
  organization_id: string;
  organization_name: string;
  available_until: string;
  delivery_method: string;
  description: string;
  review_reason: string | null;
}

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error("운영 API 주소가 설정되지 않았습니다.");
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body?.detail ?? "요청을 처리하지 못했습니다.";
    throw new Error(message);
  }
  return body as T;
}

export function login(email: string, password: string): Promise<SessionData> {
  return apiRequest<SessionData>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
