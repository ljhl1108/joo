# Bastion

리서치 날짜: 2026-11-25

## 기본 정보

- **장르**: 액션 RPG (아이소메트릭 탑다운)
- **개발사/출시**: Supergiant Games (소규모 독립팀, Greg Kasavin 외 7명), 2011-07-20
- **플랫폼**: PC, Xbox, iOS, Switch 등 광범위
- **공식 링크**: https://www.supergiantgames.com/games/bastion/
- **Steam**: https://store.steampowered.com/app/107100/Bastion/
- **의의**: Hades를 만든 Supergiant Games의 첫 작품 — 소규모 팀 개발 성공 사례의 교과서

## 핵심 메카닉

### 세계관 & 연출
- 세계가 무너진 "재앙(Calamity)" 이후의 판타지 세계
- **반응하는 내레이터**: 플레이어의 모든 행동에 실시간으로 나레이션이 붙음
  - "Kid just rages for a while." (가만히 서 있을 때)
  - 처음 플레이할 때마다 다른 느낌 → 반복 플레이 의지 증가

### 무기 시스템 (장비 설계 참고 핵심)
- **2가지 주무기 + 특수기 1가지** 를 항상 장착
- 총 11종 무기 중 선택: 근접/원거리/폭발 등 다양
- 각 무기마다 완전히 다른 조작감과 전략:
  - Cael Hammer (대형 망치) — 느리지만 강력, 패링 가능
  - Dueling Pistols — 빠른 연사, 근거리 특화
  - Breaker's Bow — 차지 샷, 넉백
  - Brusher's Pike — 찌르기, 적 뚫고 지나감
- **무기 콤보**: 선택한 2개 무기가 서로 시너지를 만들도록 플레이어가 조합

### 성장 & 허브 구조
- 스테이지 완료 → **Bastion(기지)**으로 귀환 → 6가지 건물에서 성장:
  - Arsenal: 무기 교체
  - Forge: 무기 업그레이드 (재료 소모)
  - Distillery: 패시브 술(elixir) 선택 — 최대 5개까지
  - Shrine: 신(God) 위험 선택 (아래 참고)
  - Bastion 자체: 허브를 꾸미는 오브젝트들

### God Shrine — 셀프 핸디캡 + 보상 시스템
- 각 신(God)에게 기도하면 그 신의 "저주"가 활성화:
  - 예: Hera → 적이 더 강해짐
  - 예: Pyth → 적 명중률 상승
- **최대 10개 저주를 동시에 활성화 가능**
- 활성화한 저주 수에 비례해 획득 경험치·아이템 증가
- 결과: 플레이어 스스로 난이도를 조절하며 더 큰 보상 추구 → **Hades의 Pact of Punishment 원형**

### 패링/방어
- 근접 공격 타이밍에 맞춰 버튼 → 패링 성공 시 반격 대미지 + 짧은 무적
- Hades의 Deflect(Shield) 시스템의 직접적 전신

## 소규모 팀 개발 교훈

| 항목 | Bastion의 선택 | 이유 |
|------|--------------|------|
| 팀 규모 | 7명 | 더 적으면 범위 조절 불가, 더 많으면 소통 비용 급증 |
| 아트 스타일 | 손으로 그린 느낌의 2D + 3D 혼합 | 적은 에셋으로 고퀄리티처럼 보이게 |
| 내러티브 방식 | 나레이터(목소리) | 텍스트 박스·컷씬 없이 스토리 전달 — 개발 비용 최소화 |
| 범위 조절 | 스테이지 약 15개, 플레이 6~8시간 | 완성도 > 분량 |
| 재플레이성 | New Game+ "No Return" 모드 | 콘텐츠 재활용으로 추가 개발 없이 플레이 시간 확장 |

## 플레이어 반응

**좋아하는 점**
- 나레이터 — 단 하나의 보이스 액터가 게임 전체를 살려냄
- 무기 조합의 자유도와 각 무기의 완성도
- 짧지만 완성도 높은 스토리

**아쉬운 점**
- 반복적인 적 AI (대부분 직선 돌진)
- 전통적인 RPG 기대치에는 미흡 (깊이 있는 레벨업·스탯이 없음)

## OnionCat 적용 포인트

### 1. God Shrine → OnionCat 물음표 방 하이리스크 설계
- Bastion의 저주 시스템은 플레이어가 **자발적으로 난이도를 선택**하게 함
- OnionCat의 물음표 방 이벤트 설계에 직접 적용 가능:
  - "이 방에서 적이 2배지만 장비 보상 1개 추가" → 플레이어가 선택
  - 현재 "능력치 손해 금지" 규칙(CLAUDE.md)과 호환: 체력 손해나 매복은 OK

### 2. 허브 성장 → OnionCat 온실·마을 구조
- Bastion의 귀환 → 허브 업그레이드 흐름은 OnionCat의 마을 단계(온실·등불·가판대)와 동일 구조
- 건물마다 명확한 역할 → 플레이어가 허브에서 뭘 해야 할지 직관적으로 파악
- 온실에서 장비 해금, 샘물에서 체력 회복, 가판대에서 씨앗 구입 — 역할 분리 명확히

### 3. 2개 무기 선택 → OnionCat 장비 결정
- 고양이 무기 하나가 플레이스타일 전체를 결정 (Bastion과 동일)
- Bastion이 각 무기를 완전히 다른 조작감으로 만든 것처럼, OnionCat 무기도 단순 수치 차이가 아닌 **행동 패턴 자체가 바뀌어야** 재밌음

### 4. 나레이터 → 말하는 책 (낡은 책/그리모)
- Bastion은 행동 반응 나레이션으로 적은 비용에 큰 몰입감을 얻음
- OnionCat의 "낡은 책" NPC는 비슷한 역할 가능: 방에서 특정 행동(적을 불로 태움, 구덩이 낙사)에 짧게 반응하는 대사 추가

### 5. No Return 모드 → 하드 모드 해금
- New Game+ "No Return"은 보상 없는 추가 도전 모드
- OnionCat에서 "장비 보상 없음 / 체력 회복 없음" 하드 모드를 `MetaProgress` 해금 조건으로

## 참고 링크
- [공식 사이트](https://www.supergiantgames.com/games/bastion/)
- [Wikipedia 항목](https://en.wikipedia.org/wiki/Bastion_(video_game))
- [Game Informer 무기 가이드](https://www.gameinformer.com/games/bastion/b/xbox360/archive/2011/07/04/gaining-power-in-bastion.aspx)
- [Supergiant Games 개발 Q&A](https://www.supergiantgames.com/blog/bastion-faq/)
