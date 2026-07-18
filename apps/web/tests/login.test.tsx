import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

import LoginPage from "../app/login/page";
import { loadSession } from "../lib/session";


describe("간편 로그인 화면", () => {
  it("6자리 사용자 번호로 로그인하고 역할 화면으로 자동 이동한다", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
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
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<LoginPage />);

    const loginId = screen.getByLabelText(/사용자 번호/);
    expect(loginId).toHaveAttribute("inputmode", "numeric");
    expect(loginId).toHaveAttribute("maxlength", "6");
    fireEvent.change(loginId, { target: { value: "100001" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), {
      target: { value: "246810" },
    });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/donor"));
    expect(loadSession()?.access_token).toBe("test-token");
    expect(fetchMock.mock.calls[0]?.[1]?.body).toContain('"login_id":"100001"');
  });

  it("비밀번호를 쉽게 확인하고 다시 숨길 수 있다", () => {
    render(<LoginPage />);
    const password = screen.getByLabelText("비밀번호");

    expect(password).toHaveAttribute("type", "password");
    fireEvent.click(screen.getByRole("button", { name: "비밀번호 보이기" }));
    expect(password).toHaveAttribute("type", "text");
    fireEvent.click(screen.getByRole("button", { name: "비밀번호 숨기기" }));
    expect(password).toHaveAttribute("type", "password");
  });

  it("번호가 없는 기존 사용자는 이메일 입력으로 전환할 수 있다", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        access_token: "email-token",
        token_type: "bearer",
        user: {
          id: "user-member",
          name: "김이음",
          role: "MEMBER",
          organization_id: "org-council",
          organization_name: "협의체",
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<LoginPage />);

    fireEvent.click(screen.getByRole("button", { name: "기존 이메일로 로그인" }));
    fireEvent.change(screen.getByLabelText(/이메일/), { target: { value: "member@ieum.local" } });
    fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "test-password" } });
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/member"));
    expect(fetchMock.mock.calls[0]?.[1]?.body).toContain('"login_id":"member@ieum.local"');
  });

  it("로그인 실패 시 사용자 번호는 남기고 비밀번호만 지운다", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "사용자 번호 또는 비밀번호를 확인해 주세요." }),
    }));
    render(<LoginPage />);
    const loginId = screen.getByLabelText(/사용자 번호/);
    const password = screen.getByLabelText("비밀번호");

    fireEvent.change(loginId, { target: { value: "100001" } });
    fireEvent.change(password, { target: { value: "000000" } });
    fireEvent.click(screen.getByRole("button", { name: "비밀번호 보이기" }));
    fireEvent.click(screen.getByRole("button", { name: "로그인" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("사용자 번호 또는 비밀번호를 확인해 주세요.");
    expect(loginId).toHaveValue("100001");
    expect(password).toHaveValue("");
    expect(password).toHaveAttribute("type", "password");
    await waitFor(() => expect(password).toHaveFocus());
  });
});
