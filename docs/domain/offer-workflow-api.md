# 후원 등록·운영 승인 API 계약

## 정상 흐름

```text
DONOR 로그인
→ POST /offers
→ PENDING_REVIEW
→ ADMIN GET /offers/reviews/pending
→ ADMIN POST /offers/{id}/review {APPROVE}
→ AVAILABLE
→ MEMBER GET /offers/available에 노출
```

## 보완 흐름

```text
PENDING_REVIEW
→ ADMIN REQUEST_REVISION
→ NEEDS_REVISION
→ DONOR PUT /offers/{id}
→ PENDING_REVIEW
→ ADMIN APPROVE
→ AVAILABLE
```

## 반려 흐름

```text
PENDING_REVIEW
→ ADMIN REJECT
→ REJECTED
→ 연결 목록 미노출
```

## 감사 이벤트

| 행위 | from | to |
|---|---|---|
| `CREATED` | null | `PENDING_REVIEW` |
| `REVISION_REQUESTED` | `PENDING_REVIEW` | `NEEDS_REVISION` |
| `RESUBMITTED` | `NEEDS_REVISION` | `PENDING_REVIEW` |
| `APPROVED` | `PENDING_REVIEW` | `AVAILABLE` |
| `REJECTED` | `PENDING_REVIEW` | `REJECTED` |

모든 이벤트는 `actor_id`, `reason`, `created_at`을 저장한다.

## 서버 보장 규칙

- 후원자만 후원을 등록할 수 있다.
- 운영자만 검토할 수 있다.
- 다른 조직 후원자는 해당 후원을 수정할 수 없다.
- `NEEDS_REVISION` 후원만 재제출할 수 있다.
- 승인된 `AVAILABLE` 후원만 연결 목록에 나타난다.
- 과거 제공 기한은 요청 검증 단계에서 거절한다.
- 검토 대기 중 기한이 지나면 승인할 수 없고 만료된 후원은 연결 목록에서 제외한다.
- 검토와 재제출은 `expected_version`을 요구한다.
- 상태·버전 조건부 원자적 UPDATE의 반영 행이 1개일 때만 상태와 감사 이벤트를 같은 트랜잭션으로 커밋한다.
- 버전이 다르거나 동시 요청에 선점되면 HTTP 409로 거절해 상충하는 상태·감사 이벤트를 방지한다.
- JWT 역할 문자열만 신뢰하지 않고 매 요청에서 활성 사용자와 DB 역할을 다시 확인한다.
