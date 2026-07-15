"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiRequest, type Offer, type SessionData } from "../../lib/api";
import { clearSession, loadSession } from "../../lib/session";

type ReviewAction = "APPROVE" | "REQUEST_REVISION" | "REJECT";

export default function AdminPage() {
  const { push } = useRouter();
  const [session, setSession] = useState<SessionData | null>(null);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [processing, setProcessing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadPending(activeSession: SessionData) {
    const data = await apiRequest<Offer[]>(
      "/offers/reviews/pending",
      {},
      activeSession.access_token,
    );
    setOffers(data);
  }

  useEffect(() => {
    const activeSession = loadSession();
    if (!activeSession || activeSession.user.role !== "ADMIN") {
      push("/login");
      return;
    }
    setSession(activeSession);
    loadPending(activeSession).catch((cause) => {
      setError(cause instanceof Error ? cause.message : "검토함을 불러오지 못했습니다.");
    });
  }, [push]);

  async function review(offer: Offer, action: ReviewAction) {
    if (!session) return;
    const reason = reasons[offer.id]?.trim() ?? "";
    if (reason.length < 2) {
      setError("검토 사유를 2자 이상 입력해 주세요.");
      return;
    }
    setProcessing(offer.id);
    setError("");
    setNotice("");
    try {
      await apiRequest<Offer>(
        `/offers/${offer.id}/review`,
        {
          method: "POST",
          body: JSON.stringify({
            action,
            reason,
            expected_version: offer.version,
          }),
        },
        session.access_token,
      );
      setOffers((current) => current.filter((item) => item.id !== offer.id));
      setReasons((current) => {
        const next = { ...current };
        delete next[offer.id];
        return next;
      });
      try {
        await loadPending(session);
      } catch {
        const completed = action === "APPROVE" ? "승인은" : action === "REQUEST_REVISION" ? "보완 요청은" : "반려는";
        setNotice(`${completed} 완료됐지만 목록을 새로고침하지 못했습니다.`);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "검토를 처리하지 못했습니다.");
    } finally {
      setProcessing(null);
    }
  }

  function logout() {
    clearSession();
    push("/login");
  }

  return (
    <main className="shell workShell">
      <header className="appbar workAppbar">
        <div>
          <div className="brand">IEUM <small>理音</small></div>
          <span className="accountLine">운영자 · {session?.user.name ?? ""}</span>
        </div>
        <button className="textButton" onClick={logout} type="button">로그아웃</button>
      </header>
      <section className="workIntro">
        <div>
          <p className="eyebrow">운영 검토</p>
          <h1>후원 검토함</h1>
        </div>
        <span className="countBadge">{offers.length}건</span>
      </section>
      {error && <p className="pageMessage errorMessage" role="alert">{error}</p>}
      {notice && <p className="pageMessage noticeMessage" role="status">{notice}</p>}
      <section className="reviewFeed" aria-live="polite">
        {offers.length === 0 ? (
          <div className="emptyState"><strong>검토할 후원이 없습니다.</strong><span>새 요청이 접수되면 여기에 표시됩니다.</span></div>
        ) : offers.map((offer) => (
          <article className="reviewCard" key={offer.id}>
            <div className="offerMeta"><span>{offer.organization_name} · {offer.category}</span><span>v{offer.version}</span></div>
            <h2>{offer.title}</h2>
            <dl className="detailGrid">
              <div><dt>수량</dt><dd>{offer.quantity}{offer.unit}</dd></div>
              <div><dt>기한</dt><dd>{offer.available_until}</dd></div>
              <div><dt>전달</dt><dd>{offer.delivery_method}</dd></div>
            </dl>
            <p className="descriptionText">{offer.description}</p>
            <label className="reviewLabel">
              검토 사유 - {offer.title}
              <textarea
                value={reasons[offer.id] ?? ""}
                onChange={(event) => setReasons((current) => ({ ...current, [offer.id]: event.target.value }))}
                placeholder="승인 근거 또는 보완·반려 사유를 입력하세요."
              />
            </label>
            <div className="reviewActions">
              <button className="primaryButton" disabled={processing === offer.id} onClick={() => review(offer, "APPROVE")} type="button">승인</button>
              <button className="secondaryButton" disabled={processing === offer.id} onClick={() => review(offer, "REQUEST_REVISION")} type="button">보완 요청</button>
              <button className="dangerButton" disabled={processing === offer.id} onClick={() => review(offer, "REJECT")} type="button">반려</button>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
