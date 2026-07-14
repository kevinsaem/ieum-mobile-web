# 인프라 상태

현재 개발 환경에는 Docker가 설치되어 있지 않아 첫 기반 검증은 다음 조합으로 수행했습니다.

- Python venv + FastAPI/Uvicorn
- npm + Next.js production build/start

다음 작업에서 PostgreSQL·MinIO가 포함된 Docker Compose를 추가하고 Docker 사용이 가능한 Cafe24 테스트 서버에서 실제 기동을 검증합니다.
