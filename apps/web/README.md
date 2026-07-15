# 이음 모바일웹

## 역할별 화면

- `/login` — 업무 계정 로그인 및 서버 확인 역할별 이동
- `/donor` — 내 후원, 신규 등록, 보완 후 같은 ID 재제출
- `/admin` — 검토 대기 후원 승인·보완 요청·반려
- `/member` — 승인되고 기한이 남은 연결 가능 후원 탐색

## 환경변수

```bash
export NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

운영 환경에서는 HTTPS API 주소를 빌드 시 주입합니다. 30분 Bearer 토큰과 사용자 정보는 브라우저 저장소에 쓰지 않고 현재 탭의 JavaScript 메모리에만 유지합니다. 로그아웃·새로고침·탭 종료 시 세션이 사라지며 다시 로그인해야 합니다. 동일 도메인 BFF가 마련되면 Secure·HttpOnly·SameSite 쿠키로 전환합니다.

## 실행과 검증

```bash
npm install
npm test
npm run typecheck
npm run build
npm run dev
```

GitHub Pages 정적 export:

```bash
GITHUB_PAGES=true npm run build
```

GitHub Pages는 UI 미리보기 용도입니다. 실제 로그인과 업무 처리를 위해서는 CORS·HTTPS가 설정된 FastAPI 운영 서버가 필요합니다. `NEXT_PUBLIC_API_URL`이 없으면 로그인 요청은 네트워크로 전송되지 않고 설정 오류를 표시합니다.
