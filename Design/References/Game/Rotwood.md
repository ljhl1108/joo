# Rotwood

리서치 날짜: 2026-11-19

## 기본 정보

- **개발사**: Klei Entertainment (Don't Starve, Oxygen Not Included 개발사)
- **장르**: Co-op 액션 로그라이크 브롤러
- **플레이어 수**: 1~4인 협동
- **플랫폼**: Steam (Early Access 2024-04-24 출시, 2026년 정식 출시), Nintendo Switch 2
- **공식 사이트**: https://www.klei.com/games/rotwood
- **Steam**: https://store.steampowered.com/app/2015270/Rotwood/
- **위키**: https://rotwood.fandom.com/

---

## 핵심 메커니즘

### 무기 시스템
- **5가지 무기 타입**: 해머(Hammer), 활(Bow), 창(Spear), 타격기(Strikers), 캐논(Cannon)
- 각 무기마다 완전히 다른 콤보 패턴, 차지 공격, 특수기
- 무기를 선택하면 그 무기의 고유한 "리듬"을 익혀야 함
- 훈련 구역(Training Area)에서 각 무기의 콤보·차지·특수기 연습 가능

### 전투 시스템
- **2.5D 브롤러 감각**: 공격에 약간의 AoE가 있어 여러 적을 동시에 타격 가능
- 정밀한(Precise) 타이밍 중심 — 단순 버튼 연타보다 적절한 타이밍의 콤보가 중요
- 각 무기의 고유한 공격 리듬을 익히는 것이 핵심 성장 곡선

### 장비·성장 시스템
- 런 시작 전 **무기 + 아머 + 부적(Talisman) + 유틸리티 아이템** 선택
- 각 아이템은 뚜렷한 효과/능력치/스킬 제공
- **보스 처치 → 큰 보석(Gemstone)** 획득 → 마을에서 소비하여 능력치 강화
- **무기 연구(Weapon Research)**: 같은 무기를 반복 사용하면 그 무기의 추가 능력 해금
- **강화 무기(Imbued Weapon)**: 프로토 무기(Proto-Weapon)를 통해 제작하는 강력한 최종 단계

### 협동 시스템
- 1~4인이 함께 같은 화면에서 플레이
- 협동 콤보·부활 등 멀티플레이 특화 메커니즘 (동료를 부활시킬 수 있음)
- 솔로도 가능하지만 멀티일 때 더 풍부한 경험 설계

### 적 설계
- 모든 적 공격이 명확하게 **예고(Telegraph)** 됨
- 반응해서 회피하거나 맞받아치는 방어 메커니즘 존재
- 보스는 단계별로 패턴이 바뀌며 여러 번의 판을 걸쳐 완전히 익히게 설계

---

## 플레이어들이 좋아하는 점

1. **무기별 완전히 다른 플레이스타일** — 무기 하나가 다른 게임처럼 느껴짐
2. **Klei 특유의 아트 스타일** — 카툰 같은 선명하고 귀여운 비주얼
3. **정밀한 전투 피드백** — 타격감과 타이밍 판정이 명확
4. **코옵 협력의 자연스러움** — 혼자도 재미있고 같이 하면 더 재미있는 설계
5. **조용한 성장감** — 보석·무기 연구로 티 안 나게 강해짐

---

## OnionCat 적용 포인트

### 1. 무기별 플레이스타일 → 고양이 무기 장비
Rotwood처럼 고양이 무기 장비 하나가 콤보 패턴 전체를 바꾸면 좋음.
지금 고양이 무기는 할퀴기 형태(회전·도약·3타·연타)가 달라지는데,
각 형태가 완전히 다른 "리듬"을 가지도록 차별화하면 재플레이 가치 상승.

### 2. 훈련 구역 → OnionCat 튜토리얼 방 설계
런 시작 전 훈련 구역에서 무기 연습하는 구조가 좋은 참고.
OnionCat 농장 시작 방에서 고양이+작물이 함께 기본 공격·협동 콤보·대쉬를 연습할 수 있는 짧은 샌드박스 추가 고려.

### 3. 보스 보석 → 런 간 성장과 판 간 성장의 분리
Rotwood는 보스 보석은 판 간(메타) 성장에, 런 중 선택은 그 판만 적용됨.
OnionCat도 런 중 장비(그 판)와 온실 파편(메타 해금)을 명확히 분리한 구조가 이미 있어 방향이 맞음. 보스마다 메타 성장 재료를 주는 구조(지금은 파편이 고정)로 발전 가능.

### 4. 2.5D 브롤러 AoE 감각 → 할퀴기 판정 조정
Rotwood가 모든 공격에 약간의 AoE를 주어 여러 적을 동시 처리 가능하게 한 것처럼,
OnionCat 고양이 할퀴기도 부채꼴 판정이지만 "1마리만" 맞는 경우가 없는지 확인 필요.
특히 적이 밀집했을 때 자연스럽게 여럿을 타격하는 감각이 중요.

### 5. 무기 연구(반복 사용 보상) → 장비 세트 본
같은 무기를 반복 사용하면 추가 능력이 해금되는 시스템은 OnionCat의 세트 본(같은 세트 2개/3개)과 유사한 보상 구조. 세트 완성 감각을 더 명확히 UX로 보여주는 힌트가 됨.

---

## 참고 링크

- [Rotwood Early Access Review – PCGamer](https://www.pcgamer.com/games/action/rotwood-early-access-launch)
- [Rotwood Early Access Review – GameLuster](https://gameluster.com/rotwood-early-access-review-far-from-rotten/)
- [Rotwood – Gematsu](https://gematsu.com/games/rotwood)
- [Rotwood – Wikipedia](https://en.wikipedia.org/wiki/Rotwood)
- [Rotwood Guides – games.gg](https://games.gg/rotwood/guides/)
