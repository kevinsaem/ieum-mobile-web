import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import DonorPage from "../app/donor/page";
import type { Offer, SessionData } from "../lib/api";
import { saveSession } from "../lib/session";

const session: SessionData = {
  access_token: "donor-token",
  token_type: "bearer",
  user: {
    id: "user-donor",
    name: "정담 담당자",
    role: "DONOR",
    organization_id: "org-donor",
    organization_name: "정담식당",
  },
};

const createdOffer: Offer = {
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

describe("후원자 업무 화면", () => {
  it("후원을 등록하고 내 목록에서 확인한다", async () => {
    saveSession(session);
    let offers: typeof createdOffer[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: string, options?: RequestInit) => {
        if (options?.method === "POST") {
          offers = [createdOffer];
          return { ok: true, json: async () => createdOffer };
        }
        return { ok: true, json: async () => offers };
      }),
    );

    render(<DonorPage />);
    await screen.findByRole("heading", { name: "내 후원" });
    fireEvent.click(screen.getByRole("button", { name: "새 후원 등록" }));
    fireEvent.change(screen.getByLabelText("카테고리"), { target: { value: "식사" } });
    fireEvent.change(screen.getByLabelText("후원명"), { target: { value: "따뜻한 반찬 세트" } });
    fireEvent.change(screen.getByLabelText("수량"), { target: { value: "5" } });
    fireEvent.change(screen.getByLabelText("단위"), { target: { value: "세트" } });
    fireEvent.change(screen.getByLabelText("제공 가능 기한"), { target: { value: "2099-12-31" } });
    fireEvent.change(screen.getByLabelText("전달 방식"), { target: { value: "픽업" } });
    fireEvent.change(screen.getByLabelText("상세 설명"), { target: { value: "당일 조리 반찬입니다." } });
    fireEvent.click(screen.getByRole("button", { name: "운영 검토 요청" }));

    await waitFor(() => expect(screen.getByText("따뜻한 반찬 세트")).toBeInTheDocument());
    expect(screen.getByText("운영 검토 대기")).toBeInTheDocument();
  });

  it("보완 요청 후 같은 후원 ID로 수정해 재제출한다", async () => {
    saveSession(session);
    const revision = {
      ...createdOffer,
      status: "NEEDS_REVISION",
      version: 2,
      review_reason: "제공 가능 시간을 설명해 주세요.",
    };
    let current: Offer = revision;
    const fetchMock = vi.fn(async (_url: string, options?: RequestInit) => {
      if (options?.method === "PUT") {
        current = { ...revision, status: "PENDING_REVIEW", version: 3, review_reason: null };
        return { ok: true, json: async () => current };
      }
      return { ok: true, json: async () => [current] };
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<DonorPage />);
    expect(await screen.findByText("보완 필요")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "보완하여 재제출" }));
    fireEvent.change(screen.getByLabelText("상세 설명"), {
      target: { value: "평일 오후 3시부터 픽업할 수 있습니다." },
    });
    fireEvent.click(screen.getByRole("button", { name: "수정 내용 재제출" }));

    await waitFor(() => expect(screen.getByText("운영 검토 대기")).toBeInTheDocument());
    const putCall = fetchMock.mock.calls.find(([, options]) => options?.method === "PUT");
    expect(putCall?.[0]).toContain("/offers/offer-1");
    expect(putCall?.[1]?.body).toContain('"expected_version":2');
  });

  it("재제출 성공 후 재조회가 실패해도 새 상태를 유지한다", async () => {
    saveSession(session);
    const revision: Offer = {
      ...createdOffer,
      status: "NEEDS_REVISION",
      version: 2,
      review_reason: "제공 시간을 보완해 주세요.",
    };
    let getCount = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_url: string, options?: RequestInit) => {
        if (options?.method === "PUT") {
          return { ok: true, json: async () => ({ ...revision, status: "PENDING_REVIEW", version: 3, review_reason: null }) };
        }
        getCount += 1;
        if (getCount === 1) return { ok: true, json: async () => [revision] };
        return { ok: false, json: async () => ({ detail: "목록 조회 실패" }) };
      }),
    );

    render(<DonorPage />);
    expect(await screen.findByText("보완 필요")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "보완하여 재제출" }));
    fireEvent.click(screen.getByRole("button", { name: "수정 내용 재제출" }));

    await waitFor(() => expect(screen.getByText("운영 검토 대기")).toBeInTheDocument());
    expect(screen.getByText("재제출은 완료됐지만 목록을 새로고침하지 못했습니다.")).toBeInTheDocument();
  });
});
