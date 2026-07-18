# Have a Nice Death

리서치 날짜: 2026-06-20

## 기본 정보

- **장르**: 2D 사이드스크롤 액션 로그라이크
- **개발사**: Magic Design Studios
- **퍼블리셔**: Focus Entertainment
- **출시**: 2023년 3월 22일 (PC/Switch)
- **공식 사이트**: https://www.haveanicedeathgame.com
- **Steam**: https://store.steampowered.com/app/1628320/Have_a_Nice_Death/
- **Steam 평가**: 매우 긍정적 (81%)

---

## 핵심 시스템 분석

### 전투 시스템 — 콤보 + 스펠 하이브리드

- **기본 공격**: 영혼낫(Soulscythe) 3타 콤보, 각 타격에 고유 판정
- **무기 다양성**: 런마다 추가 무기(검, 망치, 장갑 등) 최대 3개 슬롯
- **스펠(Anima)**: 원소 계열 원거리/범위 마법 — 무기와 별도 슬롯
- **에어 콤보**: 공중에서 이어지는 콤보, 적 공중 부양 후 추가 타격
- **대시 캔슬**: 대시 중 공격 입력으로 콤보 캔슬 가능 → 유체적 전투감
- **콤보 구조 예시**: 지상3타 → 대시 → 에어1타 → 스펠 → 착지공격

### 보스 디자인 — 다중 페이즈 + 페이즈별 패턴 변화

각 월드 보스(부서장)는 3페이즈 구성:
1. **페이즈 1**: 기본 패턴, 느리고 예측 가능
2. **페이즈 2**: HP 60% — 새 패턴 추가, 속도 상승
3. **페이즈 3**: HP 30% — 연속기 + 전장 전체 커버 패턴

보스별 고유 취약점 존재 (근접 전용 / 원거리 전용 페이즈 없음 — 하지만 패턴에 따라 접근/거리 유지 요구)

### 저주(Curse) 시스템 — 리스크 & 리워드

- 특정 방에서 **저주** 선택 가능: 부정적 효과를 수락하면 더 좋은 보상 획득
- 예: "공격력 -20% 대신 영구 HP +2", "이 방에서 피격 시 독 걸림 대신 황금 열쇠 획득"
- 플레이어 스킬 수준에 따라 저주를 감수할지 전략적 판단 필요

### 업그레이드 구조

- **임시(런 내)**: 방에서 획득, 런 종료 시 사라짐 — 스펠 강화, 무기 효과 등
- **영구(메타)**: 사무실 NPC 해금 → 시작 조건 강화, 스펠 해금
- **저주 → 특별 업그레이드 루트**: 저주를 쌓으면 희귀 보상 등장 확률 상승

---

## 플레이어가 사랑하는 요소

1. **전투 템포**: 빠르고 반응적인 콤보 — "공격하면서도 예쁜" 타격감
2. **보스 연출**: 보스 진입 애니메이션, 대사, 다중 페이즈 전환 연출이 화려
3. **유머 코드**: 기업 풍자 + 죽음의 신(Death)이 회사원으로 일한다는 세계관
4. **다양성**: 무기 × 스펠 × 저주 조합으로 런마다 다른 빌드 완성
5. **시각적 폴리시**: 2D 핸드드로운 픽셀 아트 + 부드러운 애니메이션

---

## 협동 관련 특이점

Have a Nice Death는 단독 플레이 게임이지만, **전투 구조에서 중요한 인사이트**:

- **근접 vs 원거리 역할 분리**: 납골함 적(방패 근접), 유령 궁수(원거리 우선) 등 적마다 최적 무기 타입이 다름
- **스펠 + 근접 연계**: 스펠로 적 경직 → 근접 콤보 → 에어리어 마무리 패턴이 OnionCat의 P1/P2 협동과 구조적으로 동일
- **히트스톱 + 카메라 흔들림**: 타격마다 0.05~0.1초 히트스톱 + 미세 카메라 흔들림으로 타격감 극대화

---

## OnionCat 적용 포인트

### 1. 보스 다중 페이즈 설계
```csharp
// BossController.cs 설계 패턴
public enum BossPhase { Phase1, Phase2, Phase3 }

private void OnHealthChanged(float currentHp, float maxHp)
{
    float ratio = currentHp / maxHp;
    if (ratio <= 0.3f && currentPhase != BossPhase.Phase3)
        TransitionToPhase(BossPhase.Phase3);
    else if (ratio <= 0.6f && currentPhase == BossPhase.Phase1)
        TransitionToPhase(BossPhase.Phase2);
}

private void TransitionToPhase(BossPhase phase)
{
    currentPhase = phase;
    // 일시 무적 + 연출 + 패턴 교체
    StartCoroutine(PhaseTransitionRoutine(phase));
}
```

### 2. 근접 전용 vs 원거리 전용 적 구현 (HaND 방식)
- 방패 적: 앞면 근접 무적(Collider 비활성화), P2 원거리가 뒤를 공격해야 패링 깨짐
- 유령 적: 원거리 반사(Reflect), P1 근접으로만 처치 가능
- **구현**: 각 적에 `WeaknessType` enum 필드 → `DamageReceiver.cs`에서 공격 타입 체크

### 3. 대시 캔슬 & 콤보 흐름 (P1 고양이)
- 대시 도중 공격 입력 시 즉시 콤보 이어가기
- 구현: `CatAttack.cs`에서 대시 상태 체크 → 대시 종료 없이 콤보 phase 진행

### 4. 저주 시스템 → OnionCat 리스크/리워드
- 특정 방 클리어 조건으로 "이 방에서 피격 0회" 달성 시 황금 업그레이드 출현
- 업그레이드 선택 화면에 "저주형 선택지" 추가 (강한 효과 + 불이익)

### 5. 보스 진입 연출
- 보스 방 진입 → BGM 전환 + 보스 등장 대사 + 카메라 줌인
- Cinemachine Priority 전환으로 구현, 연출 중 일시 조작 불능 처리

---

## 참고 링크

- [공식 게임 사이트](https://www.haveanicedeathgame.com)
- [Steam 페이지](https://store.steampowered.com/app/1628320/Have_a_Nice_Death/)
- [Have a Nice Death Wiki (Fandom)](https://have-a-nice-death.fandom.com/wiki/Have_a_Nice_Death_Wiki)
- [개발자 Magic Design Studios 인터뷰 (GDC 스타일 포스트모템)](https://www.magicdesignstudios.com)
- [Combat System 분석 (YouTube)](https://www.youtube.com/results?search_query=have+a+nice+death+combat+analysis)
