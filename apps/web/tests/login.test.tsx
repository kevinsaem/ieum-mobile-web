import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import LoginPage from "../app/login/page";
import { loadSession } from "../lib/session";


describe("로그인 화면", () => {
  it("로그인 성공 후 역할 화면으로 이동한다", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          access_token: "test-token",
          token_type: "bearer",
          user: {
            id: "user-donor",
            name: "정담 담당자",
            role: "DONOR",
            organization_id: "org-donor",
            organization_name: "정담식당",
          },
        }),
      }),
    );
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("이메일"), {
      target: { value: "donor@ieum.local" },
    });
    fireEvent.change(screen.getByLabelText("비밀번호"), {
      target: { value: "test-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/donor"));
    expect(loadSession()?.access_token).toBe("test-token");
  });
});
