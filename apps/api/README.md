# 이음 API

## 로컬 설치

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## 필수 환경변수

```bash
export DATABASE_URL
export IEUM_JWT_SECRET
export IEUM_THROTTLE_SECRET
export IEUM_DEMO_PASSWORD
# 선택: 쉼표로 구분한 웹 Origin
export IEUM_CORS_ORIGINS
```

각 값은 셸 세션 또는 서버 비밀 저장소에서 주입합니다. `IEUM_JWT_SECRET`과 `IEUM_THROTTLE_SECRET`은 각각 32자 이상인 서로 다른 값이어야 하며 실제 값을 문서·코드·Git 기록에 저장하지 않습니다. 리버스 프록시를 사용할 때만 `IEUM_TRUSTED_PROXY_CIDRS`에 신뢰하는 프록시 CIDR을 쉼표로 지정합니다. 미설정 상태에서는 전달 헤더를 무시합니다.

## DB 마이그레이션과 데모 데이터

```bash
.venv/bin/alembic upgrade head
.venv/bin/python scripts/seed_demo.py
```

스키마는 Alembic 마이그레이션으로만 생성·변경합니다. 데모 seed는 기존 스키마에 조직과 사용자를 추가합니다.

생성 사용자:

- `donor@ieum.local` — 후원자
- `member@ieum.local` — 협의체 위원
- `admin@ieum.local` — 운영자

비밀번호는 코드에 없으며 `IEUM_DEMO_PASSWORD` 값을 사용합니다.

## 로그인 방어

- 로그인 액세스 토큰은 30분 동안 유효하며, 현재 웹은 토큰을 브라우저 저장소에 영구 보관하지 않습니다.
- 정규화된 계정 이메일 기준 5회 또는 IP 기준 30회 요청이 5분 창에서 누적되면 HTTP 429와 `Retry-After`를 반환합니다.
- 이메일과 IP 원문은 저장하지 않고 별도 서버 비밀과 도메인 분리 HMAC-SHA-256으로 생성한 키만 `login_throttles` 테이블에 저장합니다.
- 5분이 지난 행은 다음 로그인 요청에서 `updated_at` 인덱스로 삭제하며, 운영 환경에서는 테이블 크기와 정리 건수를 모니터링합니다.
- HMAC 비밀을 회전하면 진행 중인 제한 창이 초기화되므로 저트래픽 시간에 교체하고 이전 키 행은 5분 후 정리합니다.
- SQLite/PostgreSQL 원자적 upsert 카운터를 사용하므로 다중 워커·다중 인스턴스가 같은 DB에서 제한 상태를 공유합니다.
- 직접 연결 IP를 기본으로 사용하고, `IEUM_TRUSTED_PROXY_CIDRS`에 포함된 프록시에서 온 경우에만 `X-Forwarded-For`를 오른쪽부터 검증합니다.
- 존재하지 않는 계정도 동일한 scrypt 검증 경로를 사용해 계정 존재 여부 추측을 어렵게 합니다.

## 실행

```bash
PYTHONPATH=. .venv/bin/uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- OpenAPI: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## 테스트

```bash
PYTHONPATH=. .venv/bin/pytest tests -q
```

## 첫 후원 실무 API

| Method | Path | 역할 | 기능 |
|---|---|---|---|
| POST | `/auth/login` | 전체 | 로그인·JWT 발급 |
| POST | `/offers` | 후원자 | 후원 검토 요청 |
| GET | `/offers/mine` | 후원자 | 자신의 조직 후원 목록 |
| GET | `/offers/reviews/pending` | 운영자 | 승인 대기 목록 |
| POST | `/offers/{id}/review` | 운영자 | 승인·보완·반려 |
| PUT | `/offers/{id}` | 후원자 | 보완 후 재제출 |
| GET | `/offers/available` | 위원·운영자 | 승인된 연결 가능 후원 |
| GET | `/offers/{id}/audit` | 운영자 | 상태 변경 감사 로그 |
