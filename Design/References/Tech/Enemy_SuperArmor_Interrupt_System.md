# Enemy Super Armor & Interrupt System (슈퍼아머 & 인터럽트 시스템)

리서치 날짜: 2026-09-17

## 개요

슈퍼아머(Super Armor)는 적이 피격 시에도 경직(Flinch/Stagger)되지 않고 행동을 유지하는 속성이다. 인터럽트 시스템은 일정 조건(누적 피해, 특정 공격 타입)이 충족될 때 슈퍼아머를 깨고 경직을 강제하는 메커닉이다.

OnionCat에서 특히 중요한 이유:
- "근접 전용 약점 적"은 슈퍼아머를 가지고 원거리 공격으로 경직이 불가능 → Cat이 반드시 근접해야 인터럽트 가능
- "원거리 전용 약점 적"은 Cat 슬래시로는 경직이 안 되고 Crop 투사체로만 슈퍼아머 파괴 가능
- 이 시스템이 역할 분업의 핵심 기계적 근거가 됨

---

## 핵심 개념

### Poise (포이즈)
- 슈퍼아머를 정량화한 수치
- 적의 최대 포이즈 = 슈퍼아머 내구력
- 공격을 받을 때마다 포이즈가 깎임
- 포이즈 = 0 → **포이즈 브레이크(Poise Break)** 발생 → 경직/스턴 상태로 전환
- 일정 시간 후 포이즈 회복 (또는 특정 HP 구간에서 재충전)

### 피격 반응 단계
```
포이즈 충분 → 슈퍼아머 (피격 이펙트만, 애니메이션 유지)
포이즈 절반 이하 → 작은 경직 (HitFlinch, 0.1~0.2초)
포이즈 = 0 → 포이즈 브레이크 (PoiseBreak, 0.5~1.5초 스턴)
```

### 공격 타입별 포이즈 데미지
| 공격 타입 | 포이즈 데미지 |
|-----------|--------------|
| Cat 슬래시 (근접) | 높음 (40~60) |
| Crop 투사체 (원거리) | 낮음 (5~10) |
| Crop 차지샷 (원거리) | 중간 (20~30) |
| Crop 패리 반사탄 | 매우 높음 (80~100, 즉시 브레이크 가능) |

→ "근접 전용 약점 적"은 원거리 포이즈 데미지가 0으로 설정 → Cat만 브레이크 가능

---

## Unity 구현 방법

### 1. 데이터 구조

```csharp
public enum DamageSource { Melee, Ranged, Parry, AoE }

[System.Serializable]
public class PoiseDamageConfig
{
    public DamageSource source;
    public float poiseDamageAmount;
}

[CreateAssetMenu(menuName = "OnionCat/EnemyPoiseData")]
public class EnemyPoiseData : ScriptableObject
{
    public float maxPoise = 100f;
    public float poiseRecoveryDelay = 2f;   // 브레이크 후 포이즈 회복 시작까지 대기
    public float poiseRecoveryRate = 30f;    // 초당 포이즈 회복량
    public float poiseBreakStunDuration = 0.8f;
    
    [SerializeField]
    public List<PoiseDamageConfig> poiseDamageTable = new List<PoiseDamageConfig>();
    
    public float GetPoiseDamage(DamageSource source)
    {
        var config = poiseDamageTable.Find(c => c.source == source);
        return config?.poiseDamageAmount ?? 0f;
    }
}
```

### 2. EnemyPoiseController 컴포넌트

```csharp
using UnityEngine;
using System.Collections;

public class EnemyPoiseController : MonoBehaviour
{
    [SerializeField] private EnemyPoiseData poiseData;
    [SerializeField] private Animator animator;
    [SerializeField] private SpriteRenderer spriteRenderer;

    private float currentPoise;
    private bool isBroken;
    private Coroutine recoveryCoroutine;

    // 포이즈 브레이크 시 외부에서 구독 가능한 이벤트
    public event System.Action OnPoiseBreak;
    public event System.Action OnPoiseRecover;

    private void Awake()
    {
        currentPoise = poiseData.maxPoise;
    }

    // DamageSystem에서 적에게 피해를 줄 때 이 메서드도 함께 호출
    public void TakePoiseDamage(DamageSource source)
    {
        if (isBroken) return;

        float damage = poiseData.GetPoiseDamage(source);
        if (damage <= 0f) return;  // 이 공격 타입으로는 포이즈 데미지 없음

        currentPoise -= damage;
        currentPoise = Mathf.Max(0f, currentPoise);

        if (currentPoise <= 0f)
        {
            TriggerPoiseBreak();
        }
        else if (currentPoise < poiseData.maxPoise * 0.5f)
        {
            // 포이즈 절반 이하: 작은 경직
            animator.SetTrigger("HitFlinch");
        }
        // 슈퍼아머 상태: 이펙트만, 애니메이션 유지
    }

    private void TriggerPoiseBreak()
    {
        isBroken = true;
        currentPoise = 0f;

        animator.SetTrigger("PoiseBreak");
        StartCoroutine(FlashPoiseBreakEffect());

        OnPoiseBreak?.Invoke();

        if (recoveryCoroutine != null) StopCoroutine(recoveryCoroutine);
        recoveryCoroutine = StartCoroutine(RecoverPoise());
    }

    private IEnumerator RecoverPoise()
    {
        // 스턴 지속
        yield return new WaitForSeconds(poiseData.poiseBreakStunDuration);

        // 회복 대기
        yield return new WaitForSeconds(poiseData.poiseRecoveryDelay);

        // 포이즈 서서히 회복
        while (currentPoise < poiseData.maxPoise)
        {
            currentPoise += poiseData.poiseRecoveryRate * Time.deltaTime;
            yield return null;
        }

        currentPoise = poiseData.maxPoise;
        isBroken = false;
        OnPoiseRecover?.Invoke();
    }

    private IEnumerator FlashPoiseBreakEffect()
    {
        // 포이즈 브레이크 시 노란색 플래시
        Color original = spriteRenderer.color;
        spriteRenderer.color = Color.yellow;
        yield return new WaitForSeconds(0.1f);
        spriteRenderer.color = original;
    }

    public bool HasSuperArmor() => !isBroken && currentPoise > 0f;
    public float PoisePercent => currentPoise / poiseData.maxPoise;
}
```

### 3. DamageSystem 연동

```csharp
// 기존 DamageSystem의 ApplyDamage에 추가
public void ApplyDamage(GameObject target, float damage, DamageSource source)
{
    var health = target.GetComponent<EnemyHealth>();
    if (health != null) health.TakeDamage(damage);

    // 포이즈 시스템 연동
    var poise = target.GetComponent<EnemyPoiseController>();
    if (poise != null) poise.TakePoiseDamage(source);
}
```

### 4. 슈퍼아머 시각 피드백

```csharp
// 슈퍼아머 활성 상태를 UI로 표시하는 경우
public class SuperArmorIndicator : MonoBehaviour
{
    [SerializeField] private SpriteRenderer armorGlowRenderer;  // 보라색 오라
    private EnemyPoiseController poiseCtrl;

    private void Awake()
    {
        poiseCtrl = GetComponentInParent<EnemyPoiseController>();
        poiseCtrl.OnPoiseBreak += () => armorGlowRenderer.enabled = false;
        poiseCtrl.OnPoiseRecover += () => armorGlowRenderer.enabled = true;
    }

    private void Update()
    {
        // 포이즈가 낮아질수록 글로우 투명도 감소
        if (armorGlowRenderer.enabled)
        {
            Color c = armorGlowRenderer.color;
            c.a = poiseCtrl.PoisePercent;
            armorGlowRenderer.color = c;
        }
    }
}
```

### 5. Animator 연동 파라미터
```
Parameters 추가:
- HitFlinch (Trigger): 작은 경직 애니메이션
- PoiseBreak (Trigger): 포이즈 브레이크 스턴 애니메이션
- IsStunned (Bool): EnemyAI에서 행동 잠금 여부 확인용
```

---

## OnionCat 적용 포인트

### 근접 전용 약점 적 (MeleeOnly 타입)
```csharp
// EnemyPoiseData ScriptableObject 설정 예시
poiseDamageTable = {
    { source: Melee,  poiseDamageAmount: 50 },   // Cat 슬래시 → 2번이면 브레이크
    { source: Ranged, poiseDamageAmount:  0 },   // Crop 투사체 → 포이즈 데미지 없음
    { source: Parry,  poiseDamageAmount:  0 },   // 패리 반사도 무효
}
```

### 원거리 전용 약점 적 (RangedOnly 타입)
```csharp
poiseDamageTable = {
    { source: Melee,  poiseDamageAmount:  0 },   // Cat 슬래시 → 포이즈 데미지 없음
    { source: Ranged, poiseDamageAmount: 25 },   // Crop 투사체 4번이면 브레이크
    { source: Parry,  poiseDamageAmount: 80 },   // 패리 반사탄은 즉시 브레이크
}
```

### 보스 슈퍼아머 구간
- 보스 HP 특정 구간(예: 60%, 30%)에서 슈퍼아머 발동
- 이 구간에서는 Cat+Crop이 동시에 집중 공격해야 빠르게 브레이크 가능
- 브레이크 성공 시 "Critical Exposed" 상태로 전환 → 2배 데미지 창문 3초

### 협력 콤보 연계
- Crop 패리 성공 시 반사탄이 적 포이즈를 크게 깎음
- 즉시 Cat이 슬래시로 마무리 → 포이즈 브레이크
- "패리 → 슬래시" 콤보로 강적 빠른 처리: 두 플레이어의 박자 맞추기 요구

---

## 참고 링크

- [Elden Ring Poise System Analysis (Fextralife)](https://eldenring.wiki.fextralife.com/Poise)
- [Unity Animator Trigger/Bool 공식 문서](https://docs.unity3d.com/Manual/AnimationParameters.html)
- [Game Feel: Super Armor in Action Games (GDC 2016 참고)](https://www.gdcvault.com/)
- [Dark Souls Poise System Deep Dive (YouTube)](https://www.youtube.com/results?search_query=dark+souls+poise+system)
- [Coroutine 패턴 공식 문서](https://docs.unity3d.com/Manual/Coroutines.html)
