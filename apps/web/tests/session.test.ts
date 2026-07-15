import { clearSession, loadSession, saveSession } from "../lib/session";
import type { SessionData } from "../lib/api";

const session: SessionData = {
  access_token: "memory-only-token",
  token_type: "bearer",
  user: {
    id: "user-donor",
    name: "후원자",
    role: "DONOR",
    organization_id: "org-donor",
    organization_name: "정담식당",
  },
};

describe("메모리 세션", () => {
  it("토큰을 브라우저 저장소에 기록하지 않는다", () => {
    saveSession(session);

    expect(loadSession()).toEqual(session);
    expect(sessionStorage.length).toBe(0);
    expect(localStorage.length).toBe(0);

    clearSession();
    expect(loadSession()).toBeNull();
  });
});
