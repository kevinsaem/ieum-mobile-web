"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { apiRequest, type Offer, type SessionData } from "../../lib/api";
import { clearSession, loadSession } from "../../lib/session";

const statusLabel: Record<string, string> = {
  PENDING_REVIEW: "운영 검토 대기",
  NEEDS_REVISION: "보완 필요",
  AVAILABLE: "연결 가능",
  REJECTED: "반려",
};

export default function DonorPage() {
  const { push } = useRouter();
  const [session, setSession] = useState<SessionData | null>(null);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingOffer, setEditingOffer] = useState<Offer | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadOffers(activeSession: SessionData) {
    const data = await apiRequest<Offer[]>(
      "/offers/mine",
      {},
      activeSession.access_token,
    );
    setOffers(data);
  }

  useEffect(() => {
    const activeSession = loadSession();
    if (!activeSession || activeSession.user.role !== "DONOR") {
      push("/login");
      return;
    }
    setSession(activeSession);
    loadOffers(activeSession).catch((cause) => {
      setError(cause instanceof Error ? cause.message : "후원을 불러오지 못했습니다.");
    });
  }, [push]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) return;
    setSubmitting(true);
    setError("");
    setNotice("");
    const form = new FormData(event.currentTarget);
    try {
      const payload = {
        category: form.get("category"),
        title: form.get("title"),
        quantity: Number(form.get("quantity")),
        unit: form.get("unit"),
        available_until: form.get("available_until"),
        delivery_method: form.get("delivery_method"),
        description: form.get("description"),
      };
      const updated = await apiRequest<Offer>(
        editingOffer ? `/offers/${editingOffer.id}` : "/offers",
        {
          method: editingOffer ? "PUT" : "POST",
          body: JSON.stringify(
            editingOffer
              ? { ...payload, expected_version: editingOffer.version }
              : payload,
          ),
        },
        session.access_token,
      );
      setOffers((current) => editingOffer
        ? current.map((item) => item.id === updated.id ? updated : item)
        : [updated, ...current]);
      setShowForm(false);
      setEditingOffer(null);
      try {
        await loadOffers(session);
      } catch {
        setNotice(`${editingOffer ? "재제출은" : "등록은"} 완료됐지만 목록을 새로고침하지 못했습니다.`);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "후원을 등록하지 못했습니다.");
    } finally {
      setSubmitting(false);
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
          <span className="accountLine">{session?.user.organization_name ?? "후원자"}</span>
        </div>
        <button className="textButton" onClick={logout} type="button">로그아웃</button>
      </header>

      <section className="workIntro">
        <div>
          <p className="eyebrow">후원자 업무</p>
          <h1>내 후원</h1>
        </div>
        <button className="primaryButton compactButton" onClick={() => { setEditingOffer(null); setShowForm(true); }} type="button">
          새 후원 등록
        </button>
      </section>

      {showForm && (
        <section className="formCard" aria-labelledby="offer-form-title">
          <div className="sectionTitle">
            <h2 id="offer-form-title">{editingOffer ? "후원 보완" : "후원 등록"}</h2>
            <button className="textButton" onClick={() => { setShowForm(false); setEditingOffer(null); }} type="button">닫기</button>
          </div>
          <form className="formStack" onSubmit={handleSubmit}>
            <label>카테고리<select name="category" defaultValue={editingOffer?.category ?? "식사"}><option>식사</option><option>생필품</option><option>서비스</option></select></label>
            <label>후원명<input name="title" required minLength={2} defaultValue={editingOffer?.title} /></label>
            <div className="formColumns">
              <label>수량<input name="quantity" required min={1} type="number" defaultValue={editingOffer?.quantity} /></label>
              <label>단위<input name="unit" required defaultValue={editingOffer?.unit} /></label>
            </div>
            <label>제공 가능 기한<input name="available_until" required type="date" defaultValue={editingOffer?.available_until} /></label>
            <label>전달 방식<select name="delivery_method" defaultValue={editingOffer?.delivery_method ?? "픽업"}><option>픽업</option><option>직접 전달</option><option>운영팀 배송</option></select></label>
            <label>상세 설명<textarea name="description" required defaultValue={editingOffer?.description} /></label>
            {error && <p className="formError" role="alert">{error}</p>}
            <button className="primaryButton" disabled={submitting} type="submit">
              {submitting ? "요청 중…" : editingOffer ? "수정 내용 재제출" : "운영 검토 요청"}
            </button>
          </form>
        </section>
      )}

      {!showForm && error && <p className="pageMessage errorMessage" role="alert">{error}</p>}
      {notice && <p className="pageMessage noticeMessage" role="status">{notice}</p>}
      <section className="feed" aria-live="polite">
        {offers.length === 0 ? (
          <div className="emptyState"><strong>등록한 후원이 없습니다.</strong><span>새 후원을 등록하면 운영 검토가 시작됩니다.</span></div>
        ) : offers.map((offer) => (
          <article className="offerCard" key={offer.id}>
            <div className="offerThumb" aria-hidden="true">{offer.category.slice(0, 1)}</div>
            <div className="offerBody">
              <div className="offerMeta"><span>{offer.category}</span><span>v{offer.version}</span></div>
              <h2>{offer.title}</h2>
              <p>{offer.quantity}{offer.unit} · {offer.delivery_method} · ~{offer.available_until}</p>
              <span className={`statusBadge status-${offer.status.toLowerCase()}`}>{statusLabel[offer.status] ?? offer.status}</span>
              {offer.review_reason && <p className="reviewReason">검토 의견: {offer.review_reason}</p>}
              {offer.status === "NEEDS_REVISION" && (
                <button
                  className="secondaryButton cardAction"
                  onClick={() => { setEditingOffer(offer); setShowForm(true); }}
                  type="button"
                >
                  보완하여 재제출
                </button>
              )}
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
