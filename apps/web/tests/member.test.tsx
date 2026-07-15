import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

import MemberPage from "../app/member/page";
import type { SessionData } from "../lib/api";
import { saveSession } from "../lib/session";

const session: SessionData = {
  access_token: "member-token",
  token_type: "bearer",
  user: {
    id: "user-member",
    name: "협의체 위원",
    role: "MEMBER",
    organization_id: "org-council",
    organization_name: "선부3동 지역사회보장협의체",
  },
};

const base = {
  quantity: 5,
  remaining_quantity: 5,
  unit: "세트",
  status: "AVAILABLE",
  version: 2,
  organization_id: "org-donor",
  organization_name: "정담식당",
  available_until: "2099-12-31",
  delivery_method: "픽업",
  description: "제공 가능한 후원입니다.",
  review_reason: "확인 완료",
};

describe("위원 연결 가능 후원", () => {
  it("승인된 후원을 카테고리별로 탐색한다", async () => {
    saveSession(session);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [
          { ...base, id: "offer-2", category: "생필품", title: "새 생필품 꾸러미" },
          { ...base, id: "offer-1", category: "식사", title: "따뜻한 반찬 세트" },
        ],
      }),
    );

    render(<MemberPage />);
    expect(await screen.findByText("새 생필품 꾸러미")).toBeInTheDocument();
    expect(screen.getByText("따뜻한 반찬 세트")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "생필품" }));
    expect(screen.getByText("새 생필품 꾸러미")).toBeInTheDocument();
    expect(screen.queryByText("따뜻한 반찬 세트")).not.toBeInTheDocument();
    expect(screen.getByText("제공 가능 5세트")).toBeInTheDocument();
  });
});
