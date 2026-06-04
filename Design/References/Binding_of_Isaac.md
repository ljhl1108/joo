# The Binding of Isaac: Rebirth / Afterbirth+

## 기본 정보

- **장르**: 탑다운 트윈스틱 슈터 로그라이크
- **개발사**: Nicalis / Edmund McMillen
- **출시**: 2011(원작), 2014(Rebirth), 2017(Afterbirth+)
- **Steam**: https://store.steampowered.com/app/250900/The_Binding_of_Isaac_Rebirth/
- **Wiki**: https://bindingofisaacrebirth.fandom.com/wiki/Binding_of_Isaac:_Rebirth_Wiki
- **공식**: https://www.nicalis.com/games/thebindingofisaacrebirth

---

## 핵심 메카닉

### 아이템 시너지 시스템
- 게임의 핵심. 아이템 단독으로는 평범하지만 조합하면 폭발적인 효과
- 예: "눈물 속도 증가" + "눈물 관통" + "눈물 분열" → 광역 청소 빌드
- 수백 개 아이템이 서로 간섭 → 매 런마다 완전히 다른 캐릭터가 됨
- **OnionCat 적용**: 업그레이드 아이템이 Cat과 Crop 각각에 개별 적용되거나 시너지 발동하는 구조 설계 가능

### 방 기반 절차적 던전
- 층별로 방 타입이 정해져 있음: 일반방, 보스방, 상점, 보물방, 비밀방, 악마방
- 방 레이아웃은 사전 제작된 프리팹 중 랜덤 선택 + 적 조합만 랜덤
- 비밀방은 벽 폭발로 발견 → 탐험 보상 루프

### 트윈스틱 슈터 공격
- 이동: 좌측 스틱 / 사격: 우측 스틱 (또는 WASD + 화살표)
- 눈물(투사체)이 캐릭터의 스탯에 따라 변형: 크기, 속도, 관통, 독, 불 등
- Player 2(Crop)와 거의 동일한 조작 구조

### 코옵 모드 — "The Forgotten / The Soul" 구조
- 원래 코옵은 별도 캐릭터가 추가되는 방식
- **The Forgotten** 캐릭터: 영혼(The Soul)을 날려보내는 트릭 — 한 캐릭터가 두 개의 분리된 개체를 제어
- 이 메카닉이 OnionCat의 "한 몸에 두 플레이어" 컨셉과 가장 유사한 레퍼런스

### 적 타입 다양성
- 이동만 하는 기본 적, 투사체 발사 적, 근접 돌진 적, 폭탄 투척 적 등
- 일부 적은 특정 방법으로만 처치 가능: 불로만 죽는 적, 폭발 필요 적
- **OnionCat 핵심 메카닉과 직결**: "근접만 유효" / "원거리만 유효" 적 구분

---

## 플레이어가 좋아하는 요소

1. **발견의 재미** — 새 아이템 조합을 발견하는 순간의 쾌감
2. **높은 런 분산** — 망한 런도 교훈, 대박 런은 몇 시간도 진행 가능
3. **숨겨진 요소의 방대함** — 비밀방, 악마 거래, 은닉 캐릭터 등 수백 시간 분량의 메타게임
4. **빠른 탈락 후 재시작** — 한 런이 30분~2시간, 빠른 리트라이 루프

---

## OnionCat 적용 포인트

| 아이소크 요소 | OnionCat 적용 방법 |
|---|---|
| "근접/원거리만 유효" 적 | Cat(근접)과 Crop(원거리) 역할 분리의 핵심 근거 — 적 설계 시 이 구분을 명확하게 |
| 아이템 시너지 | Cat 업그레이드 + Crop 업그레이드가 서로 시너지 발동하는 패시브 아이템 시스템 |
| The Forgotten / The Soul | 한 몸-두 조작 구조의 선례 — "Crop이 일정 거리 이내에서만 효과 발동" 같은 제약 설계 아이디어 |
| 방 타입 시스템 | 보물방, 상점, 보스방 구분 → OnionCat 방 로테이션에 동일 구조 채용 가능 |
| 비밀 방 | 벽 파괴 or 특정 행동으로 발견하는 숨겨진 방 — 탐험 보상 루프 추가 |

---

## 개발자 참고 — 기술적 포인트

- 아이소크는 **데이터 기반 아이템 시스템**으로 유명: 아이템마다 플래그/스탯 수정자를 JSON처럼 정의하고 캐릭터 스탯에 누적 적용
- Unity에서 유사하게 구현하려면 `ScriptableObject`로 각 업그레이드를 정의하고 `CharacterStats` 클래스에서 modifier 리스트를 관리하는 패턴 권장
- 적의 "약점 타입" 구현은 enum 기반 `DamageType` + 적마다 `immuneTypes[]` 배열로 간단히 구현 가능

---

## 참고 링크

- [GDC - Edmund McMillen on the Design of Isaac](https://www.gdcvault.com/play/1017350) (설계 철학)
- [Isaac 아이템 데이터베이스](https://bindingofisaacrebirth.fandom.com/wiki/Items) (시너지 시스템 참고)
- [Steam 리뷰 분석](https://store.steampowered.com/app/250900/#app_reviews_hash) (플레이어 피드백)
