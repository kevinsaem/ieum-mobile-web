import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import AdminPage from "../app/admin/page";
import type { SessionData } from "../lib/api";
import { saveSession } from "../lib/session";

const session: SessionData = {
  access_token: "admin-token",
  token_type: "bearer",
  user: {
    id: "user-admin",
    name: "운영 담당자",
    role: "ADMIN",
    organization_id: "org-council",
    organization_name: "선부3동 지역사회보장협의체",
  },
};

const pendingOffer = {
  id: "offer-1",
  category: "식사",
  title: "따뜻한 반찬 세트",
  quantity: 5,
  remaining_quantity: 5,
  unit: "세트",
  status: "PENDING_REVIEW",
  version: 1,
  organization_id: "org-donor",
  organization_name: "정담식당",
  available_until: "2099-12-31",
  delivery_method: "픽업",
  description: "당일 조리 반찬입니다.",
  review_reason: null,
};

describe("운영자 검토함", () => {
  it("사유와 현재 버전으로 후원을 승인한다", async () => {
    saveSession(session);
    let pending = [pendingOffer];
    const fetchMock = vi.fn(async (_url: string, options?: RequestInit) => {
      if (options?.method === "POST") {
        pending = [];
        return { ok: true, json: async () => ({ ...pendingOffer, status: "AVAILABLE", version: 2 }) };
      }
      return { ok: true, json: async () => pending };
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminPage />);
    expect(await screen.findByText("따뜻한 반찬 세트")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "승인" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "보완 요청" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "반려" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("검토 사유 - 따뜻한 반찬 세트"), {
      target: { value: "수량과 제공 기한을 확인했습니다." },
    });
    fireEvent.click(screen.getByRole("button", { name: "승인" }));

    await waitFor(() => expect(screen.getByText("검토할 후원이 없습니다.")).toBeInTheDocument());
    const postCall = fetchMock.mock.calls.find(([, options]) => options?.method === "POST");
    expect(postCall?.[0]).toContain("/offers/offer-1/review");
    expect(postCall?.[1]?.body).toContain('"action":"APPROVE"');
    expect(postCall?.[1]?.body).toContain('"expected_version":1');
  });

  it("승인 성공 후 재조회가 실패해도 승인 결과를 유지한다", async () => {
    saveSession(session);
    let getCount = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: string, options?: RequestInit) => {
        if (options?.method === "POST") {
          return { ok: true, json: async () => ({ ...pendingOffer, status: "AVAILABLE", version: 2 }) };
        }
        getCount += 1;
        if (getCount === 1) return { ok: true, json: async () => [pendingOffer] };
        return { ok: false, json: async () => ({ detail: "목록 조회 실패" }) };
      }),
    );

    render(<AdminPage />);
    expect(await screen.findByText("따뜻한 반찬 세트")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("검토 사유 - 따뜻한 반찬 세트"), {
      target: { value: "승인 기준을 확인했습니다." },
    });
    fireEvent.click(screen.getByRole("button", { name: "승인" }));

    await waitFor(() => expect(screen.getByText("검토할 후원이 없습니다.")).toBeInTheDocument());
    expect(screen.getByText("승인은 완료됐지만 목록을 새로고침하지 못했습니다.")).toBeInTheDocument();
  });
});
