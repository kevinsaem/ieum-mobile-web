# 통합 상태 전이 계약

## 후원 자원 Offer

```text
DRAFT
→ PENDING_REVIEW
→ NEEDS_REVISION / REJECTED
→ AVAILABLE
→ MATCH_PENDING
→ RESERVED
→ PREPARING_PICKUP
→ IN_DELIVERY
→ PARTIALLY_AVAILABLE / EXHAUSTED
→ ARCHIVED
```

### 핵심 규칙
- 운영 승인 전 연결 목록에 노출하지 않는다.
- 보완 요청은 같은 후원 ID로 재제출한다.
- 최종 공동 승인 전 수량을 확정 차감하지 않는다.
- 취소·거절 시 예약 수량을 해제한다.

## 케이스 Case

```text
DRAFT
→ PENDING_REVIEW
→ NEEDS_REVISION / CLOSED
→ APPROVED
→ SEARCHING
→ MATCH_PENDING
→ APPROVAL_PENDING
→ DELIVERY_SCHEDULED
→ IN_DELIVERY
→ PARTIALLY_COMPLETED / COMPLETED / CANCELLED
```

### 핵심 규칙
- 운영 승인 전 추천·매칭할 수 없다.
- 대상자는 계정을 만들지 않는다.
- 실명·전화번호·상세 주소는 기본 케이스에 저장하지 않는다.
- 부분 완료 시 잔여 필요를 재매칭할 수 있다.

## 매칭 Match

```text
DRAFT
→ DONOR_CONFIRMATION_PENDING
→ DONOR_DECLINED / OPS_REVIEW_PENDING
→ NEEDS_REVISION / REJECTED
→ COUNCIL_APPROVAL_PENDING
→ RESERVED
→ PICKUP_READY
→ DELIVERY_SCHEDULED
→ IN_DELIVERY
→ PARTIALLY_COMPLETED / COMPLETED / FAILED / CANCELLED
```

### 핵심 규칙
- 후원자 제공 확약 없이 최종 예약할 수 없다.
- 운영 적정성 검토 후 공동 승인으로 이동한다.
- 서로 다른 로그인 사용자 2인이 승인해야 한다.
- 이해충돌 사용자는 승인할 수 없다.
- 재고 예약은 서버 트랜잭션으로 수행한다.
- 모든 전이는 처리자·사유·전후 상태·일시를 감사 로그에 남긴다.

## 배송 Delivery

```text
CREATED
→ PICKUP_SCHEDULED
→ PICKUP_READY
→ PICKED_UP
→ IN_DELIVERY
→ PARTIALLY_DELIVERED / DELIVERED / FAILED / CANCELLED
→ RESCHEDULED (실패 후 재일정)
```
