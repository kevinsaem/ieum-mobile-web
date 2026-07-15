import { vi } from "vitest";


describe("API 기본 주소", () => {
  it("API 주소가 없으면 자격증명을 네트워크로 보내지 않는다", async () => {
    const configured = process.env.NEXT_PUBLIC_API_URL;
    delete process.env.NEXT_PUBLIC_API_URL;
    vi.resetModules();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    try {
      const { login } = await import("../lib/api");
      await expect(login("user@example.com", "password123")).rejects.toThrow(
        "운영 API 주소가 설정되지 않았습니다.",
      );
      expect(fetchMock).not.toHaveBeenCalled();
    } finally {
      process.env.NEXT_PUBLIC_API_URL = configured;
      vi.resetModules();
    }
  });
});
