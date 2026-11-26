# Towerborne

리서치 날짜: 2026-11-26

## 기본 정보

| 항목 | 내용 |
|------|------|
| 개발 | Stoic Studio (Banner Saga 제작사) |
| 유통 | Xbox Game Studios |
| 플랫폼 | PC(Steam), Xbox Series X\|S, Windows(Game Pass) |
| 출시 | Early Access 2024-09-10 / Xbox Preview 2025-04-29 / 1.0 2026-02-26 |
| 장르 | 협동 액션 RPG / 루터 브롤러 |
| 공식 | https://www.xbox.com/en-US/games/towerborne |
| Steam | https://store.steampowered.com/app/2458830/Towerborne/ |

## 핵심 메카닉

### 협동 전투 (1~4인)
- **로컬 또는 온라인** 최대 4인 협동, 단독 플레이도 가능
- **클래스 4종**: Sentinel(탱), Shadowstriker(암살), Pyroclast(마법), Rockbreaker(전사)
- 클래스마다 메인 무기가 다르지만 **장비는 클래스 공용** — 고른 클래스와 무관하게 같은 장비를 쓸 수 있음
- "All buttons lead to awesome" 철학 — 어떤 버튼을 눌러도 흥미로운 액션이 나와야 한다는 설계 원칙

### 장비 시스템 (Gear System)
- 미션 클리어 후 장비를 보상으로 획득 (상자 + 미션 중 드롭)
- 장비에 **세트 보너스(Set Bonus)** + **특성(Aspect)** 슬롯이 붙음
- 세트 보너스: 같은 세트 아이템을 여러 개 갖추면 추가 효과 발동
- Aspect 슬롯 예시:
  - 적시 회피 시 추가 방어력
  - 공중에 뜬 적에게 추가 피해
  - 불이 붙은 적에게 추가 피해
- 쓸모없는 장비는 **분해 → 영혼 가루(Spirit Dust)** → 원하는 장비 강화에 사용
- 장비 레벨(Equipment Level)이 권장 수치 이상이어야 고난도 미션에 도전 가능

### 클래스 마스터리 (Class Mastery, 2025-04 업데이트)
- 각 클래스에 **스킬 트리** 추가
- 성장 경로 선택: 공격적 / 방어적 / 지원형 등
- 미션을 반복하며 클래스 레벨을 올려 스킬 포인트 획득

### 미션 구조
- 로그라이크식 무작위 맵이 아닌 **핸드크래프트 구역(Belfry 세계)** 에서 미션 선택
- 미션마다 적 조합·보상 풀이 다름
- 스테이지마다 권장 장비 레벨이 있어 성장 방향을 안내

## 플레이어들이 좋아하는 것

- **전투 타격감**: 버튼을 누르면 뭔가 "시원하게" 터지는 콤보 감각
- **장비 조합의 깊이**: 세트 보너스 + Aspect 조합으로 나만의 빌드 구성
- **협동 시너지**: 클래스마다 역할이 달라 파티에 기여하는 방식이 다름
- **한 세션 분량 미션**: 10~20분짜리 미션 단위라 부담 없이 즐길 수 있음

## 비판 / 한계

- **반복 피로**: 같은 장비를 노리면 같은 미션을 수십 번 반복해야 함
- **RNG 의존**: 원하는 세트·Aspect 조합이 나올 때까지 운에 맡겨야 함
- **장기 멀티 의문**: 플레이어 기반 유지가 쉽지 않은 구조
- 로그라이크가 아님 — 미션이 끝나면 진행이 저장되고 사망 패널티가 없음

## OnionCat 적용 포인트

### 1. "조작이 항상 재밌어야" 원칙
Towerborne의 "All buttons lead to awesome" 철학을 OnionCat에 적용:
- 고양이의 모든 행동(이동·할퀴기·대쉬·특수)이 각각 독립적으로 재미있어야 함
- 양파의 조준·발사·방패 패리도 그 자체로 보람 있는 조작이어야 함
- 어느 한 행동이 "안 쓰고 싶은 버튼"이 되면 안 됨

### 2. Aspect 슬롯 → OnionCat의 GearEffect 조합
Towerborne의 Aspect 슬롯(조건부 효과: "공중에 뜬 적에게 +피해")은 OnionCat의 `GearEffect` 구조와 일치:
```
발동 조건 (EffectTrigger) → 행동 (Effect) → 대상 (Target)
```
- "패리 성공 시 → 적 주변 범위 피해" 같은 형식이 Aspect 슬롯의 직접 번역
- Towerborne처럼 Aspect들이 서로 연계되도록 설계하면 조합 가치 증가

### 3. 클래스 고유성 ≠ 장비 차별 → 공유 장비 풀
Towerborne은 장비를 클래스 비차별로 운영:
- 모든 장비가 클래스 무관하게 사용 가능 → 협동 중 장비 공유·교환 가능
- OnionCat: 고양이 장비 / 양파 장비 풀이 분리돼 있지만 "세트 보너스는 양쪽 합산"
  → 양쪽 플레이어가 세트를 함께 모아야 최고 시너지 → 협동 필요성 강화

### 4. 장비 분해 → 자원화 루프
- Towerborne: 불필요한 장비 → Spirit Dust → 원하는 장비 강화
- OnionCat: 같은 슬롯의 장비 → 씨앗(seeds) 환원 → 다음 보상 선택에 영향
  → 중복 획득을 "쓸모없는 드롭"이 아니라 **강화 연료**로 느끼게 하면 불만 감소

### 5. 세트 보너스 가시성
Towerborne은 플레이어가 현재 세트 진행도를 쉽게 볼 수 있게 UI 제공:
- OnionCat의 `CombatModifiers.Has(세트, 단계)` 상태를 HUD에서 작게 표시하면
  "아직 2개 더 필요해" 하는 목표감이 생겨 보상 선택 시 판단 근거가 됨

## 참고 링크
- [RPGSite 리뷰 (1.0)](https://rpgsite.net/review/19720-towerborne-review)
- [GamesRadar 리뷰](https://www.gamesradar.com/games/action/towerborne-review)
- [Xbox Dev Diary: Co-op & Progression](https://gamingbolt.com/towerborne-dev-diary-details-co-op-progression-and-more/)
- [Class Mastery 업데이트 노트](https://news.xbox.com/en-us/2025/04/24/towerbornes-class-mastery-update/)
- [TechRadar 미리보기: "All buttons lead to awesome"](https://techradar.com/gaming/all-buttons-lead-to-awesome-towerbornes-developers-discuss-the-games-intricate-co-op-melee-combat)
