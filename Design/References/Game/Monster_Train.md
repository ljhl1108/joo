# Monster Train

리서치 날짜: 2026-09-23

## 기본 정보

- **개발사**: Shiny Shoe (시애틀 인디팀, ~15명)
- **출시**: 2020년 5월 (Steam)
- **장르**: 덱빌딩 로그라이트 (타워 디펜스 요소 혼합)
- **공식 사이트**: https://www.monsterstrain.com/
- **Steam**: https://store.steampowered.com/app/1102190/Monster_Train/
- **플랫폼**: PC, Nintendo Switch

---

## 핵심 메커니즘

### 코어 루프
- **기차 방어**: 3층 구조의 기차를 타고 이동 → 매 구간마다 적 침입 → 맨 아래 "Pyre"(심장)를 지켜야 함
- **덱빌딩**: Slay the Spire와 유사. 카드 드래프트로 덱 구성
- **유닛 배치**: 카드 사용 → 유닛이 해당 층에 배치 → 공격/방어 자동 수행
  - 플레이어는 "어느 층에 배치할지"를 전략적으로 결정

### 클랜 시스템
- **5개 클랜** × **5개 클랜** = **25가지 조합** (주 클랜 1 + 부 클랜 1)
  - Hellhorned: 공격형, 피 상처 활용
  - Awoken: 식물형, 재생/회복
  - Stygian Guard: 마법형, 스펠 시너지
  - Umbra: 소환형, 식인 메커니즘
  - Melting Remnant: 변형형, 죽으면서 강해지는 유닛
- 클랜 조합에 따라 빌드 전략이 완전히 달라짐

### 진행 구조
- **총 9개 구간** + 최종 보스 → 약 40~50분 / 런
- 각 구간 사이 노드 분기 (상점, 이벤트, 전투, 보스)
- **Covenant(언약)**: 난이도 시스템 (1~25 단계). 높을수록 적 강화 + 제약 추가

### 카드/챔피언 강화
- **챔피언(Champion)**: 플레이어 직접 조작 가능한 강력한 카드
  - 런 진행에 따라 3번 업그레이드 분기 선택 → 플레이어마다 다른 챔피언
- **카드 업그레이드**: 불꽃(Ember) 소비 → 카드 강화. 동일 카드 2장 합성 가능

---

## 협동 시스템

- **코옵 없음** (싱글플레이만)
- 단, Multiplayer Draft(멀티 드래프트 모드)는 존재: 각자 덱 드래프트 후 점수 비교
- 리플레이 공유 기능 있음

---

## 플레이어들이 좋아하는 것

1. **빠른 런 사이클**: 40~50분의 적절한 런 길이 → "딱 한 판만" 중독성
2. **클랜 조합의 폭발적 다양성**: 25가지 클랜 조합 × Covenant 단계 × 드래프트 운 → 사실상 무한 변주
3. **강력한 시너지 발견**: "이게 이렇게 조합되는구나!" 순간의 쾌감
4. **Slay the Spire에 비해 더 적극적인 방어 기제**: 유닛 배치라는 공간 전략 레이어 추가

---

## 단점 / 비판

- 비주얼이 어두운 악마 테마라 진입 장벽이 높은 편
- 복잡도가 높아 초보에게 첫 5~6런은 혼란스러움
- 코옵/멀티 미지원
- 일부 클랜(Umbra, Melting Remnant) 학습 곡선 가파름

---

## OnionCat 적용 포인트

### 1. 런 길이 설계 벤치마크
Monster Train의 **40~50분 런** 구조는 OnionCat의 목표 런 타임과 비슷:
- 방 수: 10~15개 정도가 "너무 짧지도, 너무 길지도 않은" 체감
- 각 방 소요시간: 1~3분 (전투 + 이동) → 전체 20~30분 런 목표 시 방 12~16개

### 2. 분기 노드 구조
Monster Train의 **선택 구조 노드**는 OnionCat의 방 배치 설계에 직접 적용 가능:
```
전투 → 전투 → [분기: 상점 / 이벤트 / 선택적 강화방] → 엘리트 → 보스
```
- 코드 힌트: `RoomGraph`의 노드에 `RoomType` enum (Combat, Shop, Event, Elite, Boss) 할당
- 분기 선택 UI: 방 아이콘 3개 중 1개 선택 → `InRun_Branch_Map_System` 참고

### 3. 챔피언 업그레이드 분기 → Cat/Crop 캐릭터 업그레이드 적용
Monster Train은 **런 중 챔피언이 3번 분기 선택**으로 성장:
- OnionCat 적용: 층(층=Floor 구간) 클리어 시 "Cat 특성" 또는 "Crop 특성" 분기 선택
  - Cat: 대쉬 쿨다운 감소 / 슬래시 범위 증가 / 슬래시 후 무적 연장 중 택 1
  - Crop: 투사체 속도 증가 / 실드 지속시간 증가 / 패리 피해 2배 중 택 1

### 4. 25가지 시너지 조합 → OnionCat의 빌드 다양성 설계
25가지 클랜 조합처럼, **OnionCat의 런 다양성**을 높이려면:
- "Cat 특화 런" / "Crop 특화 런" / "균형 런" 세 방향으로 업그레이드 풀 분류
- 특화 방향 3개 이상 선택 시 "클래스 보너스" 발동 (예: Cat 특화 4개 → 슬래시 추가 타격)

### 5. Covenant 난이도 시스템 참고
첫 번째 엔딩 이후 **점진적 난이도 해금 구조**:
- OnionCat: 클리어 후 "저주 선택" 추가 (언약 1단계), 다음 런부터 특수 변형 적 등장 등
- 초보가 기본 엔딩만 즐기고, 하드코어 플레이어는 Covenant 올리며 장기 플레이

---

## 참고 링크

- [Monster Train Wiki (Fandom)](https://monster-train.fandom.com/wiki/Monster_Train_Wiki)
- [Official Monster Train Blog](https://www.monsterstrain.com/blog)
- [Monster Train Guide - Kotaku](https://kotaku.com/monster-train-beginners-guide-tips-1843855498)
- [GDC 2021: Monster Train Post-Mortem](https://www.gdcvault.com/play/1027030/Monster-Train) (공식 포스트모템, 개발 결정 과정 공개)
