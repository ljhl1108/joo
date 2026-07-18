# Soulstone Survivors

리서치 날짜: 2026-06-12

## 기본 정보
- **장르**: 로그라이트 호드 서바이벌 / 액션 RPG (Survivors-like + Bullet Hell)
- **개발사**: Game Smithing Limited (소규모 독립 스튜디오)
- **출시**: 2022년 11월 7일 (Steam 얼리 액세스) → 2025년 6월 17일 (정식 출시 1.0)
- **플랫폼**: PC (Steam, Epic Games Store, GOG), PlayStation 5, Xbox Series X|S
- **가격**: $14.99 (정식 출시 시 35% 할인 이벤트)
- **판매량**: 얼리 액세스 기간 Steam 누적 100만 장 돌파
- **Steam 평가**: "매우 긍정적" — 25,917건 기준 91% 긍정 (2026년 6월 기준)
- **공식 사이트**: https://www.gsmithingltd.com/
- **Steam**: https://store.steampowered.com/app/2066020/Soulstone_Survivors/
- **위키/참고**: https://soulstone-survivors.fandom.com/wiki/Soulstone_Survivors

---

## 핵심 메카닉

### 기본 전투 구조
- **이동 + 자동 공격의 혼합**: Vampire Survivors처럼 기본 공격은 일부 자동화, 그러나 **액티브 스킬은 플레이어가 직접 발동** — 단순 서바이버류보다 입력이 많고 액티브한 게임플레이
- **닷지 롤**: 무적 프레임 있는 구르기. 포지셔닝과 생존의 핵심 — 적 공격을 읽고 회피하는 스킬 기반 생존
- **Body-Mass Physics**: 적과 충돌해도 즉시 피해 없음. 몸으로 군중을 밀치며 이동 가능 — 혼잡한 전투에서 답답함 감소
- **No-Contact Damage**: 적을 몸으로 밀어도 피해 없음. 군중 속 다이빙이 전술적 선택지가 됨

### 스케일링과 강도
- **웨이브 기반 강도 상승**: 시간이 지날수록 적 밀도·속도·변종 증가. 런 초반 여유 → 후반 화면을 덮는 군중
- **저주(Curses) 시스템**: 선택적 난이도 상승 모디파이어. 엘리트 적 스폰 증가, 힐링 감소, "Void Presence"(맞으면 즉사하는 추적자 생성) 등 — 클리어 후에도 반복 도전 욕구를 자극
- **루프(Looping)**: 런을 완주 후 재시작 시 적이 강해지는 NG+ 개념. 루프 1회 이후엔 시각 효과가 극단적으로 증가

### 게임 모드 (3종)
| 모드 | 특징 |
|------|------|
| **Void Fields** | 5개 맵에서 구조화된 임무 클리어. 맵마다 독립적 지형·자원 배치 |
| **Unholy Cathedral** | 가오틱 가운틀렛 스타일. 끊임없는 웨이브 압박 |
| **Titan Hunt** | 거대 적 추적·격파 중심. 오픈 구조 |
- **런 길이**: 13분 이내 클리어 시 레드 포탈(오버로드 모드), 15분 이내 옐로 포탈(엔들리스 모드) 개방

---

## 빌드 / 스킬 시스템

### 스킬 구성
- **액티브 스킬**: 플레이어가 직접 발동하는 전투 기술. 런 중 최대 6개 슬롯에 장착. 쿨다운 기반. 150개 가까운 고유 스킬
- **패시브 파워(Powers)**: 런 중 레벨업·픽업으로 획득하는 영구 버프. 데미지·이속·크리티컬 확률 등 수치 향상 + 새로운 메카닉 해금
- **총 스킬 수**: 350개 이상의 스킬·파워·룬 조합

### 스킬 타입 태그 시스템
- 모든 스킬은 **27가지 스킬 타입**에 해당하는 태그를 보유
- 태그 분류:
  - **Primary Types**: 속성/테마 (화염, 빙결, 번개, 독, 공허 등) — 데미지 보너스·룬 호환성 결정
  - **Extra Types**: 행동 방식 (범위, 투사체, 근접, 召唤 등) — 시너지 적용 방식 결정
- **중요**: 태그는 파워·룬과의 시너지 계산에 직접 사용. 예) "화염" 태그 스킬에 "화염 강화" 파워가 적용

### 룬(Runes)
- 캐릭터에 장착하는 커스터마이즈 모디파이어
- 스킬 동작 변경, 상태 이상 상호작용 수정, 완전히 새로운 메카닉 해금
- 예) **"Synergetic" 룬**: 일반 시너지 스킬 발동 확률 50% → 75%로 상향

### 상태 이상(Status Effects) 시스템
| 상태 이상 | 효과 |
|-----------|------|
| **Burn** | 4초간 DoT. 1초마다 총 데미지의 12.5% 적용. 데미지 모디파이어에 비례 |
| **Poison** | DoT 계열. 스택 가능 |
| **Doom** | 가장 높은 베이스 데미지의 폭발형 DoT |
| **Slow** | 이동 속도 감소. Burn→Slow 콤보 (Thermal Shock) |
| **Fragility** | 받는 데미지 증가 디버프 — 최고 수준 디버프 |
| **Dazed** | 스택당 크리티컬 피격 확률 +1% (8초). 크리 시너지 빌드와 궁합 좋음 |
- **스택 메카닉**: 같은 상태 이상 업그레이드 2개 = 데미지 2배. 발동 확률은 올라가지 않음

### 빌드 예시
- **화염 마법사**: 화염 태그 스킬 집중 + Burn 강화 파워 + Thermal Shock 룬
- **召唤사**: 미니언·구조물 召唤 스킬 + Cunning(우선 타겟팅)·Taunt(적 어그로 집중) 특수 효과
- **근접 야만전사**: 근접 태그 스킬 + Fragility 디버프 + 크리티컬 스택
- **미니건 난사**: 투사체 태그 스킬 + 쿨다운 감소 집중 + Dazed 스택

### 메타 진행 (캐릭터 외부 성장)
- **스킬 트리 (Citadel)**: 런 중 획득한 Soulstone을 소비해 영구 업그레이드. 기본 스탯 향상·새 스킬 트리 티어 해금
- **두 트랙 진행**:
  1. **런 내 성장**: XP, 골드, 임시 버프
  2. **영구 해금**: Citadel 메뉴에서 영혼석·토큰 소비 → 글로벌 스탯·새 스킬 티어·아틀라스 업그레이드
- **캐릭터 레벨**: 각 캐릭터는 레벨 1~100+. 레벨업 시 무기 해금. 프레스티지 레벨 100에서 전설 무기

### 캐릭터 (Void Hunters)
- **총 23명** (정식 출시 기준, 2명 신규 추가: Machinist, Samurai)
- 각 캐릭터는 고유 시작 스킬 + 5가지 무기 등급 (Common→Legendary)
- 대표 캐릭터: Engineer, Cursed Captain, Arcane Weaver, Death Knight, Monkey King, Necromancer, Beastmaster, Sentinel 등
- **100개 이상의 고유 무기** 보유

---

## 적 / 보스 디자인

### 일반 적 (호드)
- **웨이브 기반 스폰**: 시간·진행도에 따라 적 수·종류 자동 증가
- **Bestiary 시스템**: 도감 형태로 적 유형 기록. 전투 경험이 쌓일수록 적 패턴 파악
- **엘리트 변종**: 기본 적과 외형·행동이 다른 강화판 포함. 예) 자폭 돌진형 엘리트 (접근 시 폭발)

### 보스 계층 구조 (3단계)
| 등급 | 설명 |
|------|------|
| **Lords of the Void** | 런 중 주기적으로 등장하는 강력 보스. 고유 스킬·속성 친화성 보유 |
| **Titans** | 더 대형의 강화 보스. 더 큰 체력풀과 위험한 공격 패턴 |
| **Final Bosses** | Void King, Mh'thaeus the Heretic 등 — 다단계 전투 |

### 보스 디자인 철학
- 각 보스는 **고유 속성 친화성** 보유 → 해당 속성 빌드에 추가 대응 또는 저항
- **다단계 전투(Phase System)**: 체력 특정 구간 돌파 시 행동 패턴 전환
- 보스 전용 **아레나 환경 변형** (지형 붕괴, 포탈, 인력 구체 등)

### Void King (최종 보스) — 상세
- **Phase 1**: 왕좌에 앉은 채 플레이어 현재 위치에 딜레이 후 공허 기둥 발사
- **Phase 2**: "Safe Lane" 메카닉 — 안전 통로가 아레나를 가로질러 이동. 위치 파악이 생존 핵심
- **Phase 3**: 아레나 면적 축소 + 회전하는 원형 공격 패턴 + DPS 레이스 + 회전 방어막 (타이밍 + 스킬 시너지 필요)

### Void Fields 보스 메카닉
- 적 제거 미션 완료 시 Lords of the Void 1~4마리 동시 스폰
- 페이즈가 진행될수록 더 강한 Lords 조합 등장

### 저주(Curse) 적용 시 엘리트 변화
- 엘리트 적 스폰 빈도 증가
- 동시 등장하는 Lords of the Void 수 증가
- **Void Presence**: 플레이어를 추적하며 접촉 시 즉사하는 특수 적 생성 (최상위 저주 효과)

---

## 피드백 시스템

### 시각 피드백
- **타격감 효과**: 모든 공격·폭발·상태 이상에 고유 시각 효과. "공격에 무게와 의도가 느껴진다"는 리뷰 다수
- **상태 이상 시각화**: 캐릭터 체력바 위, 보스 체력바 아래에 상태 이상 아이콘 표시
- **레벨업 / 픽업 피드백**: 아이템 획득·레벨업 시 화면 내 명확한 시각·사운드 피드백
- **무기 변경 피드백**: 무기 교체 시 전용 시각 효과로 변경 인지 강화

### 시각적 과부하 문제와 해결책
- **문제**: 후반 루프 시 자신의 스킬 이펙트로 화면이 완전히 뒤덮임 — 적 위치·공격 인지 불가 수준
  - 특히 엔들리스/오버로드 모드에서 심각
  - 일부 스킬(예: Demolish 충격파)은 화면 전체를 덮어버림
- **개발사 해결책**:
  - **시각 효과 슬라이더**: 0으로 설정 시 이펙트가 최소 외곽선만 남음 → 적과 데미지 숫자만 표시되는 "울트라 클리어" 모드
  - 데미지 숫자·적 체력바 개별 ON/OFF
  - FX 불투명도 조절 가능

### 사운드 피드백
- 각 스킬 타입별 고유 음향 효과
- 보스 등장 시 별도 BGM 전환으로 긴장감 고조

### UI / 정보 표시
- 스킬 타입 태그 명확히 UI에 표시 → 시너지 파악 용이
- 진행 중 빌드 상태 실시간 확인 가능

---

## 플레이어가 사랑하는 것

### 압도적 긍정 평가 핵심 포인트

1. **파워 판타지 곡선의 설계**: "초반 아슬아슬 → 후반 화면 쓸기"의 만족도 곡선이 탁월. 리뷰어들이 "역대 최고의 로그라이크 서바이버" "중독성 있는 파워 판타지"로 표현
2. **빌드 깊이**: 350개+ 스킬, 100개+ 무기, 23명 캐릭터의 조합. "패시브를 쌓고 쌓는 행위 자체가 재미있다"는 반응
3. **비교 우위**: Vampire Survivors + Path of Exile의 깊이 + Returnal의 총격 디자인을 합친 것으로 평가됨. 같은 장르 내에서 가장 깊은 커스터마이징 시스템
4. **개발사 신뢰도**: 얼리 액세스 기간(2022~2025) 동안 플레이어 피드백 기반 지속 업데이트. "얼리 액세스를 올바르게 한 게임"으로 평가
5. **가성비**: $14.99에 수백 시간 콘텐츠 제공. "가격 대비 최고"라는 평 다수
6. **재방문 욕구**: 매 런 다른 빌드 방향 + 저주 조합 → 반복 플레이 동기 풍부
7. **난이도 커브**: 저주 시스템으로 초보~하드코어 모두 자신에 맞는 도전 수위 선택 가능

### 주요 비판 포인트
- 후반 시각 이펙트 과부하 (단, 슬라이더로 어느 정도 해결 가능)
- 진행 시스템 초반 설명 부족 — "진행이 헷갈린다"는 신규 플레이어 의견
- 멀티플레이 없음 (현재 완전 싱글플레이어; 코옵은 개발사가 검토 중이나 미정)

---

## OnionCat 적용 포인트

- **적 속성 취약점 시스템 도입**: Soulstone Survivors의 보스 속성 친화성처럼, OnionCat에서 일부 적은 **근접(Cat의 슬래시)에만 취약**, 다른 적은 **원거리(Onion의 투사체)에만 취약**하게 설정. 예) 갑옷 적 → 원거리 튕김, 유령 적 → 근접 패스스루, 폭발형 적 → Cat이 슬래시로 방향 전환. 구현 힌트: 적에 `DamageTag` enum (Melee/Ranged/Both)을 붙이고, 히트박스에서 태그 불일치 시 데미지 0 + "NO EFFECT" 텍스트 팝업

- **다단계 보스 페이즈 + 협동 필수 메카닉**: Soulstone Survivors의 Void King처럼 보스 각 페이즈에 협동 조건 부여. 예) Phase 1: Onion이 방패를 깨야(패링) Cat이 근접 공격 가능 → Phase 2: Cat이 근접 제압하는 동안 Onion이 특정 장치 조준 사격. 구현 힌트: 보스 `BossPhaseManager`에 `PhaseCondition` (요구 플레이어 태그)을 정의해 페이즈 전환 조건으로 사용

- **시각 이펙트 클리어리티 설계**: Soulstone Survivors의 교훈(후반 이펙트 과부하)을 사전 방지. OnionCat은 초기부터 Cat 이펙트(냉·따뜻한 색 계열: 주황/빨강)와 Onion 이펙트(차가운 색 계열: 청/녹)를 완전히 다른 색상으로 분리. 구현 힌트: 피격 이펙트 Material에 팀 컬러 파라미터를 노출해 에디터에서 일괄 관리. 적의 공격은 노란색으로 통일해 구별

- **상태 이상 + 태그 시너지 시스템의 경량화 적용**: Soulstone Survivors의 27가지 스킬 타입 태그 시스템을 OnionCat에 축소 적용. Cat의 슬래시에 "Slash" 태그, Onion의 투사체에 "Projectile" 태그 → 파워업 카드에 "Slash 공격 피격 적에 다음 Projectile 데미지 +30%" 같은 시너지 카드 도입. 구현 힌트: `SkillTag` ScriptableObject 기반으로 각 스킬에 태그 리스트 보유, 파워업 카드도 태그 조건 필드 보유

- **저주형 난이도 모디파이어로 리플레이성 강화**: 런 시작 전 선택적 저주 1~3개 선택. 예) "분신 저주": 모든 적이 처치 시 2마리로 분열 / "속도 저주": 적 이동 속도 +40% 대신 Cat 대시 쿨다운 -30% 보상 / "Void Presence 오마주": 처치 불가 추적 유령이 등장해 Onion의 방향 패링으로만 막을 수 있음. 구현 힌트: `CurseManager` SO(ScriptableObject)에 CurseEffect 리스트를 정의, 런 시작 씬에서 선택 UI 제공

---

## 참고 링크

- Steam 페이지: https://store.steampowered.com/app/2066020/Soulstone_Survivors/
- 공식 Wiki: https://soulstone-survivors.fandom.com/wiki/Soulstone_Survivors
- 보스 위키: https://soulstone-survivors.fandom.com/wiki/Bosses
- Void King 위키: https://soulstone-survivors.fandom.com/wiki/The_Void_King
- 스킬 타입 위키: https://soulstone-survivors.fandom.com/wiki/Skill_Types
- FinalBoss.io 리뷰: https://finalboss.io/soulstone-survivors-1-0-launch-brings-power-fantasy
- Rogueliker.com 인터뷰: https://rogueliker.com/soulstone-survivors-interview/
- Rogueliker.com 콘솔 발표: https://rogueliker.com/soulstone-survivors-console-announcement/
- PCGamesN 출시 평가: https://www.pcgamesn.com/soulstone-survivors/steam-user-ratings-full-launch
- Xbox Wire 빌드 가이드: https://news.xbox.com/en-us/2025/04/23/soulstone-survivors-demo-xbox/
- Pro Game Guides 기본 정보: https://progameguides.com/soulstone-survivors/what-is-soulstone-survivors-release-date-platforms-bullet-hell-and-more/
- NotebookCheck 출시 기사: https://www.notebookcheck.net/New-hack-and-slash-roguelite-RPG-hits-Steam-with-21-000-Very-Positive-reviews-massive-skill-trees-and-35-launch-discount.1038942.0.html
