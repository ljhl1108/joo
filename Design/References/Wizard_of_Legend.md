# Wizard of Legend

리서치 날짜: 2026-06-21

## 기본 정보

- **개발사**: Contingent99
- **출시**: 2018년 5월 (Steam, Switch, PS4, Xbox)
- **장르**: 탑다운 액션 로그라이크
- **Steam**: https://store.steampowered.com/app/445980/Wizard_of_Legend/
- **Wiki**: https://wizardoflegend.fandom.com/wiki/Wizard_of_Legend_Wiki

## 핵심 메카닉

### 아르카나(Arcana) 스펠 시스템
- **6개 원소**: Fire, Water, Earth, Air, Lightning, Chaos
- **4가지 아르카나 타입**:
  - **Basic**: 빠르고 낮은 데미지, 다른 스펠 쿨다운 중 사용
  - **Dash**: 회피 이동 + 공격 결합 (이동기 겸 공격기)
  - **Standard**: 중간 스킬 (쿨다운 존재)
  - **Signature**: 강력한 궁극기 (긴 쿨다운)
- **원소 상성**: Fire > Air > Earth > Lightning > Water > Fire (약점 순환)
- **Chaos 원소**: 특별히 강력하지만 런 중 드롭되지 않음, 보스 격파 시 획득

### 전투 철학
- **스펠 콤보**: 4개 슬롯(Basic/Dash/Standard/Signature)을 상황에 맞게 연계
- **빠른 페이스**: 한 스펠이 쿨다운이면 다음 스펠로 흐름 유지
- **원소 상성 강요**: 일부 보스/적이 특정 원소에 저항 → 다양한 덱 구성 유도
- **유물(Relic)**: 패시브 아이템으로 캐릭터 빌드 방향성 결정

### 로그라이크 구조
- **절차적 방 생성**: 각 층마다 랜덤 방 구성
- **골드 경제**: 런 중 상점에서 아르카나/유물 구매
- **영구 해금**: 런 실패해도 새 아르카나/유물 해금 가능 (로그라이트 요소)
- **보스**: 층마다 마법사 협회 멤버 격파 (패턴 기반 보스전)

### 로컬 코-op
- **2인 협동**: 각자 독립적인 스펠 덱으로 협동
- **부활 시스템**: 파트너가 죽으면 다른 플레이어가 부활 가능
- **공유 체력 없음**: 개별 HP 바로 각자 생존
- **난이도 스케일**: 플레이어 수에 따라 적 HP/수 조정

## 플레이어가 좋아하는 것

- 스펠 조합 자유도가 매우 높아 매 런마다 다른 빌드
- 대시+공격 결합으로 유동적인 이동 전투
- 원소 속성 시스템이 전략적 깊이 추가
- 픽셀아트인데도 스펠 이펙트가 화려함
- 2인 코-op에서 서로 다른 원소 특화로 시너지 가능

## OnionCat 적용 포인트

### 1. 비대칭 능력 협동 강화
WoL의 원소 상성처럼, **고양이(근접)와 양파(원거리)** 역할 분리를 더 명확히:
- "근접으로만 약한 적" vs "원거리로만 약한 적" 디자인 → 두 플레이어 협동 필수
- 고양이 대시 + 양파 원거리가 WoL의 Dash+Standard 연계와 유사한 역할

### 2. 스펠 슬롯 → 업그레이드 슬롯 시스템
WoL의 4슬롯(Basic/Dash/Standard/Signature) 구조를 참고:
- OnionCat 런 업그레이드도 슬롯별 카테고리(공격/방어/이동/패시브)로 분류

### 3. 대시 + 공격 연계 패턴
WoL Dash 아르카나처럼 대시 자체가 공격 판정을 가질 수 있음:
- 고양이 대시 중 무적 + 근접 히트판정 추가 업그레이드 가능

### 4. 원소 저항 적 디자인
특정 공격 타입에 저항하는 적 → 협력 필수 구조:
- 원소 저항이 아닌 **공격 방식 저항**으로 구현 (방패적 → 근접만, 유령적 → 원거리만)

## 참고 링크

- Steam: https://store.steampowered.com/app/445980/Wizard_of_Legend/
- Wiki: https://wizardoflegend.fandom.com/wiki/Arcana
- Arcana Guide: https://www.magicgameworld.com/wizard-of-legend-arcana-guide/
- Chaos Trials: https://wizardoflegend.fandom.com/wiki/Chaos_Trials
