# Transistor

리서치 날짜: 2026-09-14

## 기본 정보

- **개발사**: Supergiant Games
- **출시**: 2014
- **플랫폼**: PC, PS4, iOS, Switch
- **장르**: Action RPG
- **공식 사이트**: https://www.supergiantgames.com/games/transistor/
- **Steam**: https://store.steampowered.com/app/237930/Transistor/
- **Wiki**: https://transistor.fandom.com/wiki/Transistor_Wiki

---

## 핵심 메카닉

### 1. 주인공 + AI 동반자 구조 (Red & Transistor)
- **Red**: 플레이어가 조작하는 주인공 (목소리를 잃은 가수)
- **Transistor**: 칼 형태의 무기 속에 갇힌 AI (남성 목소리 제공, 감정적 지원자)
- 두 캐릭터가 **물리적으로 하나의 존재** — Red가 Transistor를 들고 다님
- Transistor가 실시간으로 해설·조언·감정적 내러티브 제공
- "무기가 캐릭터다" — 무기와 주인공이 분리되지 않음

### 2. 전투 시스템: Turn() 메카닉
- 기본: 실시간 액션 (이동 + 스킬 사용)
- **Turn()** 활성화 시 시간 일시정지 → 액션 경로를 미리 계획
- 계획 실행 후 쿨다운 구간(재충전 시간) — 이동만 가능, 스킬 불가
- 실시간 + 전략적 계획의 하이브리드

### 3. Function(기능/스킬) 시스템
- 스킬을 "Function"이라 부름 (Crash, Purge, Jaunt 등 약 16개)
- **슬롯 3종 구분**:
  - **Active**: 주 사용 스킬 (버튼에 할당)
  - **Upgrade**: 기존 Active 스킬의 속성을 강화
  - **Passive**: 항상 발동되는 효과
- 같은 Function을 다른 슬롯에 넣으면 다른 효과 → 수십 가지 조합 가능
- 적 처치 시 적의 Function을 흡수해 새로운 스킬 획득

### 4. Process(적) 디자인
- 적 집단을 "The Process"라 부름
- 각 적 유형마다 고유한 행동 패턴과 취약점
- 특정 스킬 조합에만 반응하는 적 존재

### 5. Recursion(재도전) 시스템
- 죽으면 Limit(제한) 하나 해제되며 부활
- Limit = 특정 Function을 비활성화하는 핸디캡
- 더 어려워지지만 경험치 2배 → 도전과 보상의 균형

---

## 플레이어가 사랑하는 것

1. **분위기와 스토리텔링**: 두 캐릭터의 관계, Transistor의 목소리 연기, 음악
2. **스킬 조합의 깊이**: 같은 Function이 어디에 꽂히느냐에 따라 완전히 다름
3. **세계관**: 디지털 미래 도시 "Cloudbank"의 독창적인 미학
4. **음악**: Darren Korb의 재즈-일렉트로닉 사운드트랙, 전투 중 반응형 변화

---

## OnionCat 적용 포인트

### A. 하나의 몸 + 두 인격 개념
- Transistor: Red(몸)가 Transistor(무기/동반자)를 물리적으로 들고 다님
- OnionCat: Cat(몸)이 등에 Crop(화분)을 태우고 다님
- **두 존재가 독립적 인격을 가지되 하나의 유닛**으로 움직이는 디자인 철학 참고
- Transistor처럼 Crop이 전투 중 힌트나 반응을 주면 세계관 몰입↑

### B. 역할 분리 + 보완 구조
- Red = 이동·회피·근접 (메인 바디)
- Transistor = 전략 계획·스킬 (보조 AI)
- OnionCat: Cat=근접+이동, Crop=원거리+방어 — 역할 분리가 유사
- Turn() 메카닉처럼 **일시정지 후 전략 실행** 요소를 OnionCat에 선택적 추가 고려

### C. Function 조합 → 업그레이드 설계 참고
- Active/Upgrade/Passive 3단 슬롯 구조는 OnionCat 런 업그레이드에 응용 가능
- "같은 아이템이 다른 슬롯에서 다른 효과" → 소수 아이템으로 다양성 창출

### D. 핸디캡 + 보상(Limit) → 커스텀 도전 모드
- Recursion 시스템(핸디캡=2배 경험치)은 OnionCat의 재도전 동기 부여 구조로 참고

### E. 적 취약점 디자인
- Transistor의 일부 Process는 특정 스킬에만 약함 → OnionCat 근접/원거리 취약점 디자인과 정확히 일치

---

## 기술 메모

- Unity로 제작 아님 (자체 엔진), 그러나 턴/실시간 하이브리드 로직은 C# Coroutine으로 구현 가능
- Turn() 구현 아이디어: `Time.timeScale = 0f` + 경로 미리보기 → `Time.timeScale = 1f` 실행
- Function 슬롯 시스템: `ScriptableObject` 기반 스킬 + 슬롯 타입 Enum으로 구현

---

## 참고 링크

- [Game Overview - Supergiant Games](https://www.supergiantgames.com/games/transistor/)
- [Combat Design Analysis - YouTube/Design Doc](https://www.youtube.com/results?search_query=transistor+game+design+analysis)
- [Transistor Wiki - Functions](https://transistor.fandom.com/wiki/Functions)
- [GDC Talk: Music of Transistor](https://gdcvault.com/play/1021158/Music-Bootcamp-The-Music-of)
