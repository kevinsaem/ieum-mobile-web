import Link from "next/link";

const roles = [
  {
    symbol: "心",
    name: "후원자",
    description: "나눔을 등록하고 제공 가능 여부를 확인합니다.",
  },
  {
    symbol: "結",
    name: "협의체 위원",
    description: "비식별 케이스를 등록하고 적합한 후원을 연결합니다.",
  },
  {
    symbol: "保",
    name: "운영자",
    description: "후원·케이스·매칭을 검토하고 안전한 전달을 관리합니다.",
  },
];

export default function HomePage() {
  return (
    <main className="shell">
      <header className="appbar">
        <div className="brand">
          IEUM <small>理音</small>
        </div>
        <span className="phase">1차 모바일웹</span>
      </header>

      <section className="hero">
        <p className="eyebrow">선부3동 지역 나눔 연결 플랫폼</p>
        <h1>이음 1차 모바일웹</h1>
        <p>
          세 역할이 하나의 업무를 처음부터 끝까지 안전하게 처리하는 운영용
          모바일웹을 개발합니다.
        </p>
        <Link className="primaryLink" href="/login">
          로그인하고 시작하기
        </Link>
      </section>

      <section className="milestone" aria-labelledby="first-milestone">
        <span>FIRST VERTICAL SLICE</span>
        <h2 id="first-milestone">후원 등록 → 운영 승인 → 연결 노출</h2>
        <ol>
          <li>후원자가 나눔과 사진을 등록합니다.</li>
          <li>운영자가 승인·보완·반려를 처리합니다.</li>
          <li>승인된 후원만 위원의 연결 목록에 나타납니다.</li>
        </ol>
      </section>

      <section className="roles" aria-labelledby="role-heading">
        <div className="sectionTitle">
          <h2 id="role-heading">함께 연결되는 역할</h2>
          <span>3개 역할</span>
        </div>
        <div className="roleList">
          {roles.map((role) => (
            <article className="roleCard" key={role.name}>
              <div className="roleSymbol" aria-hidden="true">
                {role.symbol}
              </div>
              <div>
                <h3>{role.name}</h3>
                <p>{role.description}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="foundation" aria-labelledby="foundation-heading">
        <h2 id="foundation-heading">이번 기반 작업</h2>
        <ul>
          <li><strong>API</strong><span>등록·보완·승인 API</span></li>
          <li><strong>상태</strong><span>감사 로그·연결 노출 규칙</span></li>
          <li><strong>다음</strong><span>PostgreSQL·사진 업로드</span></li>
        </ul>
      </section>
    </main>
  );
}
