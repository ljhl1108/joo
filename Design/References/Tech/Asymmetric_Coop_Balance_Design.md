# Asymmetric Co-op Balance Design

리서치 날짜: 2026-11-17

## 개요

두 플레이어가 **완전히 다른 조작 방식·행동 범위**를 가질 때, 둘 다 "내가 이 판에 기여했다"고 느끼게 만드는 설계 원칙. OnionCat의 고양이(조이스틱·근접) + 작물(마우스·원거리+스킬)이 대표적인 비대칭 협동이다. 역할이 다르면 "누가 더 중요한가" 논쟁이 생기기 쉽고, 한 역할이 쉬우면 짐처럼 느껴진다.

---

## 핵심 설계 원칙

### 1. 기여도 가시성 (Contribution Visibility)
플레이어가 자신이 한 일을 화면에서 직접 볼 수 있어야 한다.
- 고양이: 근접 타격음·히트스톱·적 넉백이 "내가 맞췄다"를 즉각 알림
- 작물: 씨앗 탄 명중 파티클·데미지 숫자가 "내 탄이 맞았다"를 알림
- 협동: 두 플레이어가 같이 맞췄을 때(협동 콤보) 별도 이펙트·사운드 → "합작"을 명시

### 2. 상호 의존성 (Mutual Dependency)
한 역할이 없어도 가능하지만, 없으면 확실히 더 힘들어야 한다.
- 작물 없이 고양이만: 원거리 위협에 취약, 마법서 스킬 없음
- 고양이 없이 작물만: 이동 불가, 근접 적에게 무방비 (하지만 1인 플레이 모드에서 AI Cat이 대신)
- "함께하면 쉬워진다"지, "혼자면 불가능하다"가 아닌 것이 접근성을 높임

### 3. 복잡도 조절 가능성 (Adjustable Complexity)
조작이 단순한 역할(작물 → 쏘기만 해도 기여)과 복잡한 역할(고양이 → 대쉬·할퀴기·특수 타이밍)이 공존 → **게임을 덜 아는 플레이어에게 작물을 맡기면 자연스럽게 쉬운 역할**이 됨.

### 4. 피해 기여 균형 (Damage Parity)
런 종료 화면에서 두 플레이어의 피해 기여도 차이가 너무 크면 한쪽이 "짐 역할"이었다는 느낌 → **목표 비율: Cat 50~60%, Onion 40~50%** (고양이가 근접이라 더 위험하므로 약간 더 높아도 OK).

---

## Unity 구현: 기여도 추적 시스템

### RunContribution 데이터 구조

```csharp
public class RunContribution {
    public float catDamageDealt;
    public float onionDamageDealt;
    public int catKills;
    public int onionKills;
    public int coBlow; // 협동 콤보 횟수

    public float CatPercent => catDamageDealt / (catDamageDealt + onionDamageDealt + 0.01f);

    public bool IsBalanced(float tolerance = 0.25f) =>
        Mathf.Abs(CatPercent - 0.5f) < tolerance; // 25~75%면 균형
}
```

### TakeDamage에서 집계

```csharp
// EnemyBase.TakeDamage 내부
public void TakeDamage(float amount, Attacker attacker) {
    // ...
    if (attacker == Attacker.Cat)
        GameManager.Instance.Run.Contribution.catDamageDealt += finalDamage;
    else
        GameManager.Instance.Run.Contribution.onionDamageDealt += finalDamage;
}
```

### 런 결과 화면 출력

```csharp
// RunResultScreen.cs
void ShowContribution(RunContribution c) {
    float catPct = c.CatPercent * 100f;
    catBar.fillAmount = c.CatPercent;
    catLabel.text = $"고양이 {catPct:F0}%";
    onionLabel.text = $"작물 {100f - catPct:F0}%";
    if (c.coBlow > 10)
        coBonus.text = $"협동 콤보 {c.coBlow}회! 👏";
}
```

---

## 비대칭 역할 균형 조정 도구

### 실시간 밸런스 조정 파라미터

```csharp
[CreateAssetMenu]
public class CoopBalanceSettings : ScriptableObject {
    [Header("작물 보정 (Onion too weak → 올리기)")]
    public float onionDamageMultiplier = 1.0f;    // 씨앗 탄 전체 배율
    public float onionSkillCooldownScale = 1.0f;  // 스킬 쿨다운 배율 (1.0 = 기본)

    [Header("고양이 보정 (Cat too strong → 낮추기)")]
    public float catDamageMultiplier = 1.0f;
    public float catSpecialGaugeScale = 1.0f;  // 야성 게이지 충전 속도

    [Header("협동 보너스")]
    public float coBlowBonusDamage = 0.3f;     // 협동 콤보 추가 피해
    public float jointUltimateDamageBonus = 0.5f;
}
```

### 플레이테스트 기반 조정 흐름

1. `RunContribution` 데이터를 10판 수집
2. Onion 평균 기여도가 35% 미만이면 `onionDamageMultiplier += 0.1`
3. Onion 기여도가 55% 초과이면 Cat 보정 or Onion 약화
4. 결과 화면에 항상 표시 → 플레이어 스스로 느낌 확인 가능

---

## 1인 플레이 시 균형 조정 (Solo Fallback)

한 명이 혼자 플레이할 경우:
- **Cat 단독**: 작물 AI가 자동 조준·발사. `onionAI.autoFire = true`. 스킬은 비활성
- **Onion 단독**: Cat AI가 가장 가까운 적을 추적·공격. 패링 없음
- 1인 플레이 시 적 HP를 15~20% 감소 (`SoloDifficultyMultiplier = 0.82f`)

```csharp
void AdjustForSoloPlay() {
    bool isSolo = !secondPlayerConnected;
    EnemyStats.hpMultiplier = isSolo ? 0.82f : 1f;
    if (isSolo && catPlayerActive)
        onionAI.enabled = true;   // 작물 AI 켜기
    else if (isSolo && onionPlayerActive)
        catAI.enabled = true;     // 고양이 AI 켜기
}
```

---

## 비대칭 협동의 흔한 실패 패턴

| 실패 패턴 | 증상 | 해결 |
|----------|------|------|
| **조수 증후군** | Onion이 쏘기만 해도 Cat이 혼자 처리 가능 | Onion 스킬이 필수 국면 추가 (보호막 적, 원거리 전용 적) |
| **기여도 비가시** | 둘 다 쏘는데 누가 더 했는지 모름 | 개인 피해 숫자 색 구분 (고양이=주황, 작물=초록) |
| **조작 복잡도 차이** | 초보가 항상 작물만 함 | 작물도 R 스킬 타이밍 등 중급 행동 추가 → 성장감 부여 |
| **단독 플레이 시 불균형** | 고양이만으로도 너무 쉬움 | 1인 플레이 AI는 기여도를 의도적으로 60%로 제한 |

---

## OnionCat 적용 포인트

### 단기 적용 (지금 바로 가능)
1. **기여도 집계 추가** — `RunContribution` 필드를 `RunData`에 추가, `TakeDamage`에서 집계
2. **런 결과 화면에 비율 표시** — "고양이 57% · 작물 43%" 한 줄 추가
3. **협동 콤보 카운터** — 현재 `Attacker` 로직 활용, `coBlow` 집계

### 중기 조정 과제
- 플레이테스트 10판 뒤 Onion 기여도 평균이 35% 미만이면 `onionDamageMultiplier` 올리기
- 작물 고유기(R) 쿨다운이 너무 길면 고양이만 싸우는 국면 길어짐 → 쿨다운 감소 검토

### 장기 설계 목표
- **보호막 적 도입**: 원거리 탄으로만 깨지는 보호막 → Onion의 필수 역할 국면
- **협동 퍼즐**: 고양이가 버튼을 누르고 있는 동안 작물이 적을 처치 → "합작이어야만 가능"한 순간

---

## 참고 링크

- Rayman Legends Murphy mechanic design: https://www.gamedeveloper.com/design/how-rayman-legends-wii-u-solves-the-asymmetric-co-op-problem
- Cooperative game balance theory (GDC): https://gdcvault.com/play/1021744/
- It Takes Two post-mortem: https://www.gamedeveloper.com/design/the-design-of-it-takes-two
- Unity Input System for multi-player: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html
