import { render, screen } from "@testing-library/react";

import HomePage from "../app/page";


describe("1차 모바일웹 홈", () => {
  it("첫 수직 기능과 세 역할을 안내한다", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: "이음 1차 모바일웹" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("후원 등록 → 운영 승인 → 연결 노출"),
    ).toBeInTheDocument();
    expect(screen.getByText("후원자")).toBeInTheDocument();
    expect(screen.getByText("협의체 위원")).toBeInTheDocument();
    expect(screen.getByText("운영자")).toBeInTheDocument();
  });
});
