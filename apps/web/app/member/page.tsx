"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { apiRequest, type Offer, type SessionData } from "../../lib/api";
import { clearSession, loadSession } from "../../lib/session";

const categories = ["전체", "식사", "생필품", "서비스"];

export default function MemberPage() {
  const { push } = useRouter();
  const [session, setSession] = useState<SessionData | null>(null);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [category, setCategory] = useState("전체");
  const [error, setError] = useState("");

  useEffect(() => {
    const activeSession = loadSession();
    if (!activeSession || activeSession.user.role !== "MEMBER") {
      push("/login");
      return;
    }
    setSession(activeSession);
    apiRequest<Offer[]>("/offers/available", {}, activeSession.access_token)
      .then(setOffers)
      .catch((cause) => {
        setError(cause instanceof Error ? cause.message : "연결 가능 후원을 불러오지 못했습니다.");
      });
  }, [push]);

  const filtered = useMemo(
    () => category === "전체" ? offers : offers.filter((offer) => offer.category === category),
    [category, offers],
  );

  function logout() {
    clearSession();
    push("/login");
  }

  return (
    <main className="shell workShell">
      <header className="appbar workAppbar">
        <div>
          <div className="brand">IEUM <small>理音</small></div>
          <span className="accountLine">협의체 위원 · {session?.user.name ?? ""}</span>
        </div>
        <button className="textButton" onClick={logout} type="button">로그아웃</button>
      </header>
      <section className="workIntro memberIntro">
        <div>
          <p className="eyebrow">승인된 후원 · 신상 우선</p>
          <h1>연결 가능 후원</h1>
          <p className="supportText">운영 승인이 완료되고 제공 기한이 남은 후원만 표시됩니다.</p>
        </div>
      </section>
      <nav className="filterBar" aria-label="후원 카테고리">
        {categories.map((item) => (
          <button
            aria-pressed={category === item}
            className={category === item ? "filterChip active" : "filterChip"}
            key={item}
            onClick={() => setCategory(item)}
            type="button"
          >
            {item}
          </button>
        ))}
      </nav>
      {error && <p className="pageMessage errorMessage" role="alert">{error}</p>}
      <section className="feed" aria-live="polite">
        {filtered.length === 0 ? (
          <div className="emptyState"><strong>연결 가능한 후원이 없습니다.</strong><span>운영 승인 후 이 목록에 표시됩니다.</span></div>
        ) : filtered.map((offer) => (
          <article className="offerCard" key={offer.id}>
            <div className="offerThumb" aria-hidden="true">{offer.category.slice(0, 1)}</div>
            <div className="offerBody">
              <div className="offerMeta"><span>{offer.category} · {offer.organization_name}</span><span>신상</span></div>
              <h2>{offer.title}</h2>
              <p>제공 가능 {offer.remaining_quantity}{offer.unit}</p>
              <p>{offer.delivery_method} · ~{offer.available_until}</p>
              <span className="statusBadge status-available">연결 가능</span>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
