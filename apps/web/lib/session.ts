import type { SessionData } from "./api";

let activeSession: SessionData | null = null;

export function saveSession(session: SessionData): void {
  activeSession = session;
}

export function loadSession(): SessionData | null {
  return activeSession;
}

export function clearSession(): void {
  activeSession = null;
}
