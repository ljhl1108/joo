# Despot's Game: Dystopian Army Builder

리서치 날짜: 2026-11-23

## 기본 정보

- **개발사**: Konfa Games
- **출시**: 2022년 10월 (얼리 액세스 졸업)
- **플랫폼**: PC, iOS, Android
- **장르**: 로그라이크 + 오토배틀러
- **Steam**: https://store.steampowered.com/app/1227280/Despots_Game_Dystopian_Battle_Simulator/
- **Wikipedia**: https://en.wikipedia.org/wiki/Despot%27s_Game
- **PCGamer 평**: "Teamfight Tactics + 로그라이크 던전 크롤러"

## 핵심 메커니즘

### 오토배틀러 + 로그라이크 융합
- 플레이어가 인간 유닛으로 군대를 조립하고, 절차적으로 생성된 던전에 보낸다
- 전투는 자동으로 진행 — 플레이어는 편성과 준비만 담당
- 층마다 난이도 상승, 보스 층 존재, 메타 진행으로 새 유닛 타입 해금

### 클래스 시너지 시스템
- 유닛은 각자 클래스 타입을 가짐
- 같은 클래스 유닛을 여러 명 편성하면 패시브 보너스 활성화 (시너지 효과)
- 시너지 단계: 보통 2개 이상이면 작은 보너스, 4개 이상이면 강한 보너스 구조

### 자원 관리 — 식량과 군대 규모
- 유닛 수가 많을수록 층당 식량 소비가 증가
- "군대 규모 vs 품질" 긴장: 많은 유닛 = 식량 압박, 소수 정예 = 위험 최소화
- 이 선택지가 런마다 전략의 핵심이 됨

### 보상 및 업그레이드
- 무작위 변이(Mutation)/퍽: 전투 중 발견, 군대 보드에 추가
- 상점 조우: 제한된 선택지에서 무작위 옵션 구매
- 비판: 운 의존도가 너무 높아 시너지 계획이 무너지는 경우가 많다는 평

## 플레이어 반응

| 호평 | 비판 |
|---|---|
| 접근하기 쉬운 오토배틀러 | 운이 시너지 전략을 압도하는 경우 |
| 로그라이크 층 구조와의 조화 | 반복감 (후반 런이 비슷하게 느껴짐) |
| 유닛 조합의 다양성 | 선택지가 너무 무작위여서 목표 빌드 불가 |

## OnionCat 적용 포인트

### 1. 세트 시너지 임계점 설계
Despot's Game의 클래스 시너지(2개=소, 4개=대)는 OnionCat의 장비 세트 보너스(`CombatModifiers.Has(세트, 단계)`)와 구조가 같다. 핵심 교훈:

- **단계 1 보너스가 "조금 좋다"가 아니라 "체감된다" 수준이어야** 플레이어가 세트를 의식하고 목표로 삼는다
- `sets.csv`에서 단계 1·2 보너스 차이를 확인하고, 단계 1이 충분히 가시적인지 점검
- 예시 기준: 태양 세트 1단계 = 공격력 +15%, 2단계 = 공격력 +35% + 불꽃 효과

### 2. 보상 화면 필터링의 중요성
Despot's Game의 비판 1위는 "무작위가 너무 강해서 빌드 방향을 잡을 수 없다"는 것. OnionCat의 3개 장비 보상 화면도 같은 위험이 있다.

**실용 힌트**: 현재 세트 진행도를 기반으로 보상 풀을 약하게 필터링 (`RewardTable.RollFor` 조정)하면 "세트를 완성할 수 있다는 희망"이 생긴다. 완전 필터가 아니라 가중치 조정으로 충분.

### 3. 중복 장비 레벨업 UX 명확화
Despot's Game에서 같은 유닛 중복 = 시너지 카운트 증가. OnionCat에서 같은 장비 중복 = 레벨업. 최대 레벨 도달 후 "완전 중복"을 씨앗으로 환전하는 UX가 명확하지 않으면 플레이어가 혼란스럽다. `Dismantle` 로직이 충분히 가시적인지 체크.

### 4. 양파의 자율 씨앗 발사 ↔ 오토배틀러 유닛
직접 적용은 아니지만, Despot's Game이 "알아서 싸우는 유닛 + 편성자로서의 플레이어"를 재미있게 만든다는 점은 참고할 만하다. 양파가 발사하는 씨앗은 목표 추적·자율 동작을 하므로, 편성(어떤 씨앗/스킬을 고를지)과 실시간 조작(타이밍, 각도)의 균형을 의식적으로 설계해야 한다.

### 5. 세트 보너스 가시성
세트 단계가 올라갈 때 명확한 피드백이 없으면 플레이어가 세트 의식을 못 한다. `PassiveHost.Recalculate` 후 단계가 오르면 `CoreHUD`에서 세트 아이콘 강조 + `Sfx.Play(SfxId.SetUnlock)` 추가를 고려.

## 참고 링크

- [Steam 페이지](https://store.steampowered.com/app/1227280/Despots_Game_Dystopian_Battle_Simulator/)
- [Wikipedia](https://en.wikipedia.org/wiki/Despot%27s_Game)
- [PCGamer 소개](https://pcgamer.com/this-game-is-like-teamfight-tactics-except-its-also-a-roguelike-dungeon-crawler)
- [Cogconnected 리뷰](https://cogconnected.com/review/despots-game-dystopian-army-builder-review/)
- [Indiecator 첫인상](https://indiecator.org/2021/11/07/indietail-despots-game-dystopian-army-builder/)
