# Hades

리서치 날짜: 2026-08-01

## 기본 정보

- **개발사**: Supergiant Games
- **출시**: 2020년 9월 (얼리 액세스 2018년 12월)
- **장르**: 탑다운 액션 로그라이크
- **공식 사이트**: https://www.supergiantgames.com/games/hades/
- **Steam**: https://store.steampowered.com/app/1145360/Hades/
- **위키**: https://hades.fandom.com/wiki/Hades_Wiki

---

## 핵심 메카닉

### 전투 시스템
- **6가지 무기(Infernal Arms)**: 검, 창, 방패, 활, 권투 장갑, 레일건. 각 무기마다 고유한 공격 패턴과 특수 공격.
- **Basic / Special / Cast / Dash**: 4가지 행동 슬롯. 각 슬롯에 "Boon(신의 축복)"을 장착해 능력을 교체.
- **Dash (무적 구간)**: 모든 적 공격에 일정 프레임 무적. 타이밍 기반 회피가 핵심.
- **Death Defiance**: 최대 3회, 즉사 대신 HP 일정량 회복. 런 내 "목숨" 개념.

### Boon(업그레이드) 시스템
- 올림포스 신들(제우스·포세이돈·아테나 등)이 방 클리어 후 Boon 3개 제시.
- 각 신마다 테마(번개·물·방패 등)와 시너지 특성이 있어 런마다 다른 빌드 탄생.
- **Duo Boon**: 두 신의 Boon을 모두 가진 경우 특수 강화 Boon 등장. 빌드 심화.
- **Legendary Boon**: 각 신당 1개씩 매우 강력한 특수 능력.

### 메타 진행
- **Darkness**: 런 내 수집, 이후 "Mirror of Night"에서 영구 수동 능력 해금.
- **Gemstones / Keys / Nectar / Ambrosia**: 각각 집 업그레이드, 무기 해금, NPC 호감도, 최고 레벨 호감도에 사용.
- **Contractor**: 집(하우스 오브 하데스)을 인테리어하고 기능 확장.
- **Heat System(Pact of Punishment)**: 클리어 후 난이도 제약(적 HP 증가, 도망 불가 등) 자발적 선택. 리플레이 동기.

### 내러티브 통합
- **죽을 때마다 대화**: 귀환 시 NPC들이 다른 대사를 함. 런 결과(얼마나 진행했는지)에 따라 반응 다름.
- **관계 시스템**: Nectar 선물 → 호감도 증가 → 고유 스토리라인 해금. 모든 NPC에게 완결된 호감 이야기.
- **진행형 대화**: 같은 상황에서도 대화가 새로 갱신되어 수백 시간 플레이해도 새 대사 등장.

### 방 구조
- **방 유형**: 전투방, 엘리트 전투방, 보물방, 상점(Charon), 휴식방, 보스방.
- **비용 선택**: 일부 방 입장 전 Obols(런 내 화폐) 지불 여부 선택지 제시.
- **웰 오브 카론**: 런 내 일회성 아이템(HP 회복·능력 강화) 구매. 단기 vs 장기 투자 선택.

---

## 플레이어가 사랑하는 이유

1. **"한 번만 더" 루프**: 죽어도 스토리가 진행된다는 것이 리플레이 동기를 만든다.
2. **빌드 다양성**: 신 조합, 무기, 업그레이드 조합으로 매 런이 다른 플레이 경험.
3. **촉각적 피드백**: 히트스톱, 화면 진동, 선명한 사운드로 타격감이 업계 최고 수준.
4. **명확한 성장 곡선**: 처음엔 1층도 못 넘지만, 메타 업그레이드 쌓이면 자연스럽게 클리어.
5. **내러티브 밀도**: 로그라이크이면서 완결된 스토리를 가진 최초 사례 중 하나.

---

## OnionCat 적용 포인트

### 1. 죽음을 스토리 트리거로 활용
- **Hades**: 죽으면 집으로 돌아가고 NPC 대화.
- **OnionCat 적용**: 런 실패 시 Cat이 한마디, Onion도 별도 대사. 런 횟수에 따라 새 대사 풀 갱신.
  - 구현: `RunEndDialogueManager` — `runCount` 기반 대사 인덱스 선택. `DialogueEntry[]` ScriptableObject 배열.

### 2. Boon 시스템 → 2인 비대칭 업그레이드
- **Hades**: Boon은 단일 플레이어 전체 강화.
- **OnionCat 적용**: Boon을 "Cat 전용"과 "Onion 전용"으로 분리. 방 클리어 후 각자 1개씩 선택지 3개 제시 → 협의 후 선택.
  - 구현: `UpgradeOfferUI` — P1/P2 각자 UI 패널, `AbilityDatabase`에서 캐릭터 필터링 후 제시.

### 3. 엘리트 적 + 특수 보상 방 패턴
- **Hades**: 엘리트방은 어렵지만 더 좋은 Boon이나 Darkness 보상.
- **OnionCat 적용**: 특수 적(메카닉 적, 방패 유닛, 군집 적) 등장 방은 Legendary 아이템 드롭 확률 2배. 리스크/리워드 명확화.

### 4. Heat System → 어시스트/챌린지 모드
- **Hades**: 클리어 후 자발적 난이도 추가 제약으로 리플레이.
- **OnionCat 적용**: 클리어 후 "협동 제약 조건(예: 한 명만 공격 가능한 구간 추가)" 선택적 활성화. 싱글 플레이어 보조 모드도 검토.

### 5. Death Defiance → 2인 공유 목숨
- **Hades**: Death Defiance는 개인 목숨.
- **OnionCat 적용**: "공유 목숨 3개" — 한 명이 HP 0 도달 시 공유 목숨 1 소모 후 부활(Coop_Revival_System.md 참고). 둘 다 동시에 HP 0이 되면 런 종료.

---

## 참고 링크

- 공식 사이트: https://www.supergiantgames.com/games/hades/
- Steam 페이지: https://store.steampowered.com/app/1145360/Hades/
- Hades Wiki: https://hades.fandom.com/wiki/Hades_Wiki
- GDC 2019 — Supergiant Games 나레이티브 디자인 강연: https://www.gdcvault.com/play/1025821
- 하데스 로그라이크 디자인 분석 (Game Maker's Toolkit): https://www.youtube.com/watch?v=iSFIDSKWMvQ
