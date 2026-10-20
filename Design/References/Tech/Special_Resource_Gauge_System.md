# Special Resource Gauge System (특수 게이지·리소스 미터)

리서치 날짜: 2026-10-20

## 개요

특수 게이지(Special Gauge)는 행동이나 이벤트를 통해 채워지고, 가득 차면 강력한 특수 행동을 해제하는 리소스 시스템이다. OnionCat은 2026-10-20 커밋 `5100706`에서 **야성 게이지(Wild Gauge)** + **CatSpecial** 시스템을 구현했다. 이 문서는 해당 시스템의 설계 패턴과 확장 방향을 정리한다.

**OnionCat 직접 관련**: `CatSpecial.cs` / `WildGauge (RunData)` / HUD 왼쪽 위 주황 막대

## 핵심 설계 패턴

### 1. 충전 방식 3가지

| 방식 | 예시 게임 | 특징 |
|------|-----------|------|
| 피해 딜링 | TMNT, Street Fighter | 공격적 플레이에 보상 |
| 피해 수령 | Hades (Cast), Doom (Glory Kill) | 위험 상황에서 역전 기회 |
| 시간 경과 | Smash Bros. (Final Smash 전통 방식) | 기다리기만 해도 채워짐, 단순 |
| 콤보/연속 | Devil May Cry | 스타일 높이면 강해지는 순환 |

OnionCat 현황: 할퀴기가 맞을 때 +8, 등 공격 시 ×2 → **딜링 방식 + 위치 보상** 조합

### 2. 소비 방식 3가지

| 방식 | 설명 | 장단점 |
|------|------|--------|
| 완전 소비 (Burst) | 게이지 전부 써서 큰 효과 1회 | 임팩트 강, 타이밍 중요 |
| 분할 소비 | 일부 써서 중간 효과 여러 번 | 유연하지만 복잡 |
| 수동 유지 | 게이지 유지 중 지속 효과 | Bloodborne Regain처럼 유지 비용 발생 |

OnionCat은 **완전 소비(Burst)** 방식 — 가득 차면 F 키로 발동

### 3. 감쇠(Decay) 처리
- **감쇠 없음**: 한번 모으면 영구 유지 → 적극적 축적 보상, 초보자 친화
- **시간 감쇠**: 전투 이탈 시 서서히 줄어듦 → 전투 집중 유도
- **즉시 감쇠**: 방 클리어 시 초기화 → 방마다 새로 전략

OnionCat 현황: 현재 감쇠 없음 → 방 사이에도 유지됨. 게임 흐름에 맞는지 확인 필요

## Unity 구현 방법

### 기본 구조 (ScriptableObject + RunData 패턴)

```csharp
// RunData.cs에 추가하는 방식 (OnionCat 아키텍처)
public class RunData
{
    public float wildGauge;          // 0~1 정규화
    public float wildGaugeMax = 100f; // 또는 고정

    public void AddWildGauge(float amount)
    {
        wildGauge = Mathf.Clamp(wildGauge + amount, 0, wildGaugeMax);
        OnWildGaugeChanged?.Invoke(wildGauge / wildGaugeMax);
    }

    public bool TryConsumeWildGauge()
    {
        if (wildGauge < wildGaugeMax) return false;
        wildGauge = 0;
        OnWildGaugeChanged?.Invoke(0);
        return true;
    }

    public event Action<float> OnWildGaugeChanged; // HUD 구독용
}
```

### HUD 막대 구현 (Unity UI)

```csharp
// WildGaugeBar.cs
public class WildGaugeBar : MonoBehaviour
{
    [SerializeField] Image fillImage;
    [SerializeField] Animator animator; // 가득 찼을 때 깜빡임 애니메이션

    void OnEnable() => GameManager.Instance.Run.OnWildGaugeChanged += UpdateBar;
    void OnDisable() => GameManager.Instance.Run.OnWildGaugeChanged -= UpdateBar;

    void UpdateBar(float normalized)
    {
        fillImage.fillAmount = normalized;
        animator.SetBool("IsFull", normalized >= 1f);
    }
}
```

### 특수 발동 흐름

```csharp
// CatSpecial.cs 발동 체크
void OnSpecialInput()
{
    if (!GameManager.Instance.Run.TryConsumeWildGauge()) return;
    if (!GameManager.IsGameplayActive) return;

    StartCoroutine(PerformSpecial());
}

IEnumerator PerformSpecial()
{
    // 1. 히트스톱 + 카메라 연출
    HitFeelManager.Instance.TriggerSpecialActivate();

    // 2. 무기 타입에 따른 분기
    switch (currentWeaponType)
    {
        case WeaponType.Default: yield return FrenzySlash(); break;
        case WeaponType.Whirlwind: yield return WhirlwindSpin(); break;
        // ...
    }
}
```

### 충전량 설계 가이드라인

```
목표 충전 시간: 전투방 1개 = 약 1~2번 발동 기회
방당 평균 적 처치 수 × 충전량 = 게이지 최대치

예:
- 방당 평균 처치 8마리
- 할퀴기 평균 3발씩 맞힌다고 가정 = 3 × 8 = 24회 명중
- 24 × 8 = 192 충전 → 게이지 최대치 100이면 약 1.9회 발동
- 적절한 밸런스: 한 방에 1~2번 쓸 수 있는 수준
```

### 게이지 시각 효과 (주황색 막대 → 가득 찼을 때 깜빡임)

```csharp
// DOTween 사용 예 (또는 Animator)
void OnGaugeFull()
{
    fillImage.DOColor(Color.yellow, 0.2f)
        .SetLoops(-1, LoopType.Yoyo)
        .SetId("gaugePulse");
}

void OnGaugeUsed()
{
    DOTween.Kill("gaugePulse");
    fillImage.color = originalColor;
}
```

### 장비에 의한 게이지 조정 (OnionCat v4 장비 시스템 연동)

```csharp
// PlayerStats.cs에서 게이지 관련 스탯 수식
float chargeMultiplier = 1f + PlayerStats.Current.Get(StatType.WildGaugeChargeRate);
float amount = baseAmount * chargeMultiplier;

// GearEffect 발동 조건 예: 게이지 가득 찼을 때 보너스
// trigger: "OnSpecialActivate"
// action: "AddBuff(AttackSpeed, 2f, 3f)" → 3초간 공속 2배
```

## OnionCat 적용 포인트

### 현재 구현 (2026-10-20 기준)
- 야성 게이지: 할퀴기 명중 +8, 등 공격 시 ×2
- 특수 발동: F 키 / 패드 LB
- 무기 타입별 5가지 특수 행동
- HUD 왼쪽 위 주황 막대

### 즉시 개선 가능한 항목

1. **발동 연출 강화**
   - 발동 순간 0.15초 히트스톱 전체 적용 (현재 히트스톱은 맞은 적만)
   - 카메라 살짝 zoom-out (Cinemachine Virtual Camera FOV +5, 0.1초) → 특수 공격 공간감 강조
   - HUD 막대 가득 찰 때 + 발동 시 각각 다른 SFX (`SfxId.WildGaugeFull`, `SfxId.WildGaugeActivate`)

2. **방 클리어 시 게이지 유지 vs. 초기화**
   - 유지(현재): 전략적으로 쌓아뒀다가 보스에서 씀 → 보스 전투 레버리지
   - 초기화: 매 방 독립적 전략 → 더 단순, 방 간 긴장감 없음
   - **권장**: 방 사이 이동 시 게이지 50% 감쇠 (보스 방 진입 시는 유지) — 모아두기 보상은 주되 무한 축적 방지

3. **합동 게이지와의 관계**
   - 지금 두 게이지가 완전히 독립적
   - "야성 게이지 가득 상태에서 합동기 발동 시 ONION STORM이 강화됨" 같은 교차 보상 가능
   - 구현: `coopGauge.Activate()` 전에 `if (RunData.wildGauge >= max) ApplyWildBonus()`

4. **장비 세트 연동**
   - Wind 세트 2단계: "야성 게이지 충전량 +25%" 
   - Sun 세트 4단계: "특수 발동 시 HP 15 회복"
   - 이런 연동이 있으면 특수 게이지가 장비 빌드 선택에 영향을 줌 → 깊이 증가

5. **StatType 추가 제안**
   ```
   WildGaugeChargeRate  — 충전량 배율
   WildGaugeCooldown    — 발동 후 재충전 속도 (감쇠 추가 시)
   WildSpecialDamage    — 특수 공격 데미지 배율
   ```

## 참고 링크
- [Unity 공식: UI Image Fill Amount](https://docs.unity3d.com/Manual/script-Image.html)
- [GDC 강연: Devil May Cry의 스타일 게이지 설계](https://www.gdcvault.com/)
- [Game Feel: Special Meter Design Patterns (Game Developer 매거진)](https://www.gamedeveloper.com/)
- [DOTween 공식 문서](http://dotween.demigiant.com/documentation.php)
