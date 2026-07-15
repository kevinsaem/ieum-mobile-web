"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { login, type UserRole } from "../../lib/api";
import { saveSession } from "../../lib/session";

const rolePath: Record<UserRole, string> = {
  DONOR: "/donor",
  MEMBER: "/member",
  ADMIN: "/admin",
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const session = await login(email, password);
      saveSession(session);
      router.push(rolePath[session.user.role]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "로그인하지 못했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="shell authShell">
      <header className="appbar">
        <Link className="backLink" href="/" aria-label="홈으로 돌아가기">←</Link>
        <div className="brand">IEUM <small>理音</small></div>
        <span className="phase">로그인</span>
      </header>
      <section className="authPanel">
        <p className="eyebrow">선부3동 지역 나눔 연결 플랫폼</p>
        <h1>업무 계정으로 로그인</h1>
        <p className="supportText">승인된 후원자·협의체 위원·운영자 계정만 이용할 수 있습니다.</p>
        <form className="formStack" onSubmit={handleSubmit}>
          <label>
            이메일
            <input
              autoComplete="email"
              inputMode="email"
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            비밀번호
            <input
              autoComplete="current-password"
              minLength={8}
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && <p className="formError" role="alert">{error}</p>}
          <button className="primaryButton" disabled={submitting} type="submit">
            {submitting ? "확인 중…" : "로그인"}
          </button>
        </form>
      </section>
    </main>
  );
}
