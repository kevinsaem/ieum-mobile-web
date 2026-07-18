"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useRef, useState } from "react";

import { login, type UserRole } from "../../lib/api";
import { saveSession } from "../../lib/session";

const rolePath: Record<UserRole, string> = {
  DONOR: "/donor",
  MEMBER: "/member",
  ADMIN: "/admin",
};

function easyLoginError(cause: unknown): string {
  const message = cause instanceof Error ? cause.message : "";
  if (message.includes("사용자 번호") || message.includes("로그인 시도가 너무 많습니다")) {
    return message;
  }
  if (message.includes("운영 API 주소")) {
    return "지금은 로그인할 수 없습니다. 담당자에게 문의해 주세요.";
  }
  return "인터넷 연결이 원활하지 않습니다. 잠시 후 다시 눌러 주세요.";
}

export default function LoginPage() {
  const router = useRouter();
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [useEmail, setUseEmail] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const passwordInputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const session = await login(loginId, password);
      saveSession(session);
      router.push(rolePath[session.user.role]);
    } catch (cause) {
      setPassword("");
      setShowPassword(false);
      setError(easyLoginError(cause));
      requestAnimationFrame(() => passwordInputRef.current?.focus());
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="shell authShell simpleAuthShell">
      <header className="appbar">
        <Link className="backLink" href="/" aria-label="홈으로 돌아가기">←</Link>
        <div className="brand">IEUM <small>理音</small></div>
        <span className="phase">로그인</span>
      </header>
      <section className="authPanel simpleAuthPanel">
        <p className="eyebrow">이음 업무 서비스</p>
        <h1>로그인</h1>
        <p className="simpleGuide" id="login-guide">
          {useEmail ? (
            <>기존에 사용하던 <strong>이메일</strong>과 비밀번호를 입력하세요.</>
          ) : (
            <>받으신 <strong>사용자 번호 6자리</strong>와 비밀번호를 입력하세요.</>
          )}
        </p>
        <form className="formStack simpleLoginForm" onSubmit={handleSubmit} aria-describedby="login-guide">
          <label className="simpleField">
            <span className="simpleFieldLabel"><b>1</b> {useEmail ? "이메일" : "사용자 번호"}</span>
            <input
              key={useEmail ? "email" : "number"}
              autoCapitalize="none"
              autoComplete="username"
              autoFocus
              inputMode={useEmail ? "email" : "numeric"}
              maxLength={useEmail ? 254 : 6}
              pattern={useEmail ? undefined : "[0-9]{6}"}
              placeholder={useEmail ? "예: name@example.com" : "예: 100001"}
              required
              type={useEmail ? "email" : "text"}
              value={loginId}
              onChange={(event) => setLoginId(
                useEmail
                  ? event.target.value
                  : event.target.value.replace(/\D/g, "").slice(0, 6),
              )}
            />
          </label>
          <label className="simpleField">
            <span className="simpleFieldLabel"><b>2</b> 비밀번호</span>
            <span className="passwordField">
              <input
                ref={passwordInputRef}
                aria-label="비밀번호"
                autoComplete="current-password"
                minLength={6}
                placeholder="비밀번호 입력"
                required
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              <button
                aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보이기"}
                className="passwordToggle"
                onClick={() => setShowPassword((current) => !current)}
                type="button"
              >
                {showPassword ? "숨기기" : "보기"}
              </button>
            </span>
          </label>
          {error && <p className="formError simpleLoginError" role="alert">{error}</p>}
          <button className="primaryButton simpleLoginButton" disabled={submitting} type="submit">
            {submitting ? "로그인 중…" : "로그인"}
          </button>
        </form>
        <div className="loginHelp" role="note">
          <strong>{useEmail ? "사용자 번호를 받으셨나요?" : "사용자 번호를 모르시나요?"}</strong>
          <span>{useEmail ? "더 쉬운 6자리 사용자 번호로 로그인할 수 있습니다." : "담당자에게 “사용자 번호를 알려 주세요”라고 말씀해 주세요."}</span>
          <button
            className="legacyLoginToggle"
            onClick={() => {
              setUseEmail((current) => !current);
              setLoginId("");
              setPassword("");
              setShowPassword(false);
              setError("");
            }}
            type="button"
          >
            {useEmail ? "사용자 번호로 로그인" : "기존 이메일로 로그인"}
          </button>
        </div>
      </section>
    </main>
  );
}
