# Katana ZERO

리서치 날짜: 2026-06-25

## 게임 개요

**Katana ZERO** (2019)는 인디 스튜디오 Askiisoft가 개발하고 Devolver Digital이 퍼블리싱한 2D 픽셀아트 액션 플랫포머. 기억상실증 검객 Subject Zero가 주인공이며, 시간을 조작하여 미래를 예측하는 능력을 사용한다.

- **장르**: 2D 액션, 네오-노아르, 신서웨이브 미학
- **엔진**: GameMaker Studio 2
- **아트 도구**: Aseprite
- **플레이타임**: 약 3~4시간
- **평가**: Steam 97% 긍정 (22,000+ 리뷰), Metacritic 89점

## 공식/관련 링크

- [Steam 스토어](https://store.steampowered.com/app/460950/Katana_ZERO/)
- [Wikipedia](https://en.wikipedia.org/wiki/Katana_Zero)
- [Katana Zero Wiki (Enemies)](https://katana-zero.fandom.com/wiki/Enemies)
- [개발자 인터뷰 - Shacknews (일격 필살 철학)](https://www.shacknews.com/article/110713/katana-zero-interview-one-hit-kills-make-you-feel-badass)
- [Katana ZERO and the metalanguage of violence - Game Developer](https://www.gamedeveloper.com/business/katana-zero-and-the-metalanguage-of-violence)
- [디자인 분석 영상 - YouTube](https://www.youtube.com/watch?v=Pw9r1-Ho-08)

## 핵심 메커니즘

### 1. 일격 필살 (One-Hit Kill)

플레이어도 적도 단 한 번의 공격으로 죽는 완전 대칭 구조. 개발자 Justin Stander 인용: *"일격 필살이 플레이어를 'badass'하게 느끼게 한다."* 모든 행동이 의미를 가지고, 높은 스테이크가 높은 만족감을 만든다.

### 2. 시간 감속 (Time Slow)

리소스가 제한된 시간 감속 미터. 서사적으로는 "Zero가 미래를 예측하는 행위"로 프레이밍 — 각 죽음은 실패가 아니라 "잘못된 계획을 포기하는 것"으로 표현된다.

### 3. 즉시 재시도 (Instant Retry)

11개 레벨이 개별 "장면"으로 분리, 죽으면 즉시 해당 장면 재시작. 마찰을 완전히 제거하면서 긴장감 유지.

### 4. 방향성 대시 회피

적 공격을 타이밍 기반 대시로 회피. 무적 프레임 존재.

### 5. 분기 대사 시스템

NPC가 말하는 동안 타이머 바가 채워지고, 플레이어는 시간 내에 선택하거나 상대방 말을 인터럽트할 수 있다. "누군가의 말을 끊는 것 자체가 폭력 행위"로 게임의 테마 강화.

### 6. 적 다양성

- Skinny Rickies: 기본 근접
- Greasers: 곡괭이 패리 (반사 가능)
- Shotgun 적: 산탄 패턴 회피 필수
- 각 적 타입마다 대응 전술이 다름

## 플레이어가 사랑하는 것

1. **검 베기 만족감** — 프레임별 애니메이션 + 즉각적 시각/음향 피드백의 조합
2. **신서웨이브 사운드트랙** — 34곡, Bill Kiley & LudoWic 작곡. Gary Numan, Vangelis 영향
3. **짧고 집약적인 경험** — 3~4시간이지만 매우 밀도 높음
4. **내러티브와 게임플레이의 통합** — 시간 조작이 서사적 장치이자 메커니즘
5. **픽셀아트 폴리시** — "2D 픽셀아트임을 잊을 정도"(Steam 리뷰)

## OnionCat 적용 포인트

### 검 베기 만족감 (Player 1 - Cat)

Katana ZERO에서 가장 직접적으로 배울 수 있는 영역.

- **히트스탑**: 베기 명중 시 2~4프레임 일시 정지 → 타격감의 핵심
- **트레일 이펙트**: 180도 슬래시 궤적을 따라가는 잔상 (색상 변화 + 투명도 감소)
- **히트 플래시**: 적 피격 시 흰색 섬광 1~2프레임
- **음향 레이어링**: 슬래시 음 + 피격음 + 적별 사망음 분리 설계
- **프레임 정확도**: 히트박스를 "애니메이션이 정점에 달하는 프레임"에만 활성화

### 무적 대시 (Player 1 - Cat)

- 무적 프레임이 활성화된 구간을 시각적으로 표시 (잔상 이펙트, 색상 변화)
- 대시 이후 짧은 쿨다운으로 남용 방지
- 대시 방향과 작물 냄비 흔들림 물리 연동 (공유 신체 feel)

### 공유 신체 메커니즘 적용

- Katana ZERO는 "단일 캐릭터 우아함"을 보여줌 → OnionCat은 이를 2인 협력 복잡성으로 변환
- 고양이 이동 방향이 작물의 조준 각도에 제약을 줄 수 있음 (협동 강제)
- 냄비가 고양이 등 위에서 흔들리는 물리 시뮬레이션 → 공유 신체의 시각적 표현

### 즉시 재시도 문화

- 방 단위 체크포인트 → 방을 클리어하면 다음 방으로, 죽으면 현재 방 재시작
- 재시작 애니메이션 0.3초 이내 완료 목표

### 사운드 디자인 방향

- 신서웨이브 기반이지만 자연/정원 앰비언스 혼합 (도시 네오-노아르 → 식물 판타지)
- 긴장 구간: 빠른 신스 드럼 / 이동 구간: 차분한 리프
- 각 아이템 획득, 방 클리어마다 독립적인 "스팅거" 사운드

### 내러티브 통합 (선택적)

- "고양이와 작물이 최고의 팀워크를 찾기 위해 시간을 되감는다"는 설정으로 런 실패를 서사적으로 정당화
- 하드 모드: 이전 시도의 "유령 플레이어" 잔상 출현 (Katana의 "예측 실패" 개념)

## 참고 자료

- [개발자 인터뷰 - Red Bull](https://www.redbull.com/us-en/katana-zero-developer-justin-stander-interview)
- [PC Gamer Review](https://www.pcgamer.com/katana-zero-review/)
- [Defined Design: Katana Zero - VGChartz](https://www.vgchartz.com/article/444421/defined-design-katana-zeros-surprising-story/)
