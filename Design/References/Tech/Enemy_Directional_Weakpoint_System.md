# Enemy Directional Weak Point System

리서치 날짜: 2026-08-27

## 개요

적의 특정 방향(등, 측면, 정면)을 공격했을 때 추가 데미지를 주는 시스템. 기존 `Enemy_Weakness_Resistance_System.md`가 속성/무기 타입 약점을 다루는 것과 달리, 이 시스템은 **공간적·방향적 취약점**을 처리한다.

OnionCat에서는 Cat의 근접 슬래시와 Onion의 원거리 투사체가 서로 다른 각도에서 적을 타격할 수 있어, "방향 약점" 구조가 협력 필수 메커니즘의 핵심 도구가 된다.

## Unity 구현 방법

### 방법 1: 방향 벡터 기반 (가장 단순, 권장)

```csharp
public enum AttackDirection { Front, Back, Side, Any }

public class DirectionalWeakPoint : MonoBehaviour
{
    [SerializeField] private float backstabMultiplier = 2f;
    [SerializeField] private float flankMultiplier = 1.5f;

    // attackerPosition: 공격자의 월드 위치
    public float GetDamageMultiplier(Vector2 attackerPosition)
    {
        Vector2 toAttacker = (attackerPosition - (Vector2)transform.position).normalized;
        // transform.right = 적이 바라보는 방향 (facing direction)
        float dot = Vector2.Dot(transform.right, toAttacker);

        if (dot < -0.7f) return backstabMultiplier;       // 등 공격 (등 뒤에서 옴)
        if (Mathf.Abs(dot) < 0.5f) return flankMultiplier; // 측면 공격
        return 1f;                                         // 정면 공격
    }
}
```

**DamageSystem에서 호출:**
```csharp
public void TakeDamage(int baseDamage, Vector2 attackerPosition)
{
    var weakPoint = GetComponent<DirectionalWeakPoint>();
    float multiplier = weakPoint != null
        ? weakPoint.GetDamageMultiplier(attackerPosition)
        : 1f;

    int finalDamage = Mathf.RoundToInt(baseDamage * multiplier);

    if (multiplier > 1f)
        SpawnWeakPointVFX(multiplier); // 크리티컬 이펙트

    ApplyDamage(finalDamage);
}
```

---

### 방법 2: 분리된 히트박스 콜라이더 (Body Part 방식)

```csharp
public class EnemyBodyPart : MonoBehaviour
{
    public enum PartType { Head, Body, Back, Shield }

    [SerializeField] public PartType partType;
    [SerializeField] public float damageMultiplier = 1f;
    [SerializeField] public bool isImmune = false; // 방패 등

    private EnemyBase _parentEnemy;

    private void Awake()
    {
        _parentEnemy = GetComponentInParent<EnemyBase>();
    }

    public void ReceiveHit(int damage, Vector2 hitDirection)
    {
        if (isImmune)
        {
            SpawnBlockVFX();
            return;
        }

        int finalDamage = Mathf.RoundToInt(damage * damageMultiplier);
        _parentEnemy.TakeDamage(finalDamage);

        if (damageMultiplier >= 2f)
            SpawnCriticalVFX(); // "WEAK!" 팝업
    }

    private void SpawnBlockVFX()
    {
        // 방어 이펙트 생성 (스파크 등)
    }

    private void SpawnCriticalVFX()
    {
        FloatingTextManager.Instance.Spawn("WEAK!", transform.position, Color.yellow);
    }
}
```

**히트박스 레이아웃 (Sprite 자식 오브젝트):**
```
EnemyObject
  ├── Sprite
  ├── BodyPart_Head (PartType.Head, multiplier = 2.0)
  ├── BodyPart_Body (PartType.Body, multiplier = 1.0)  ← 메인 콜라이더
  ├── BodyPart_Back (PartType.Back, multiplier = 2.0)
  └── BodyPart_Shield (PartType.Shield, isImmune = true)
```

---

### 방법 3: ScriptableObject로 약점 정의 (데이터 주도, 최적)

```csharp
[CreateAssetMenu(fileName = "EnemyWeakPointData", menuName = "OnionCat/EnemyWeakPointData")]
public class EnemyWeakPointData : ScriptableObject
{
    [System.Serializable]
    public class WeakPointRule
    {
        public AttackType requiredAttackType; // Melee, Ranged, Any
        public AttackDirection requiredDirection;
        public float multiplier;
        public GameObject criticalVFXPrefab;
    }

    public List<WeakPointRule> rules;

    public float Evaluate(AttackType attackType, AttackDirection direction)
    {
        foreach (var rule in rules)
        {
            bool typeMatch = rule.requiredAttackType == AttackType.Any
                             || rule.requiredAttackType == attackType;
            bool dirMatch = rule.requiredDirection == AttackDirection.Any
                            || rule.requiredDirection == direction;
            if (typeMatch && dirMatch) return rule.multiplier;
        }
        return 1f;
    }
}
```

---

### 피격 방향 계산 유틸리티

```csharp
public static class DirectionUtils
{
    public static AttackDirection GetAttackDirection(Transform enemy, Vector2 attackerPos)
    {
        Vector2 toAttacker = (attackerPos - (Vector2)enemy.position).normalized;
        float dot = Vector2.Dot(enemy.right, toAttacker);

        if (dot < -0.6f) return AttackDirection.Back;
        if (dot > 0.6f)  return AttackDirection.Front;
        return AttackDirection.Side;
    }
}
```

---

### 크리티컬 피드백 VFX

```csharp
private void SpawnWeakPointVFX(float multiplier)
{
    // 약점 공격 시 "WEAK!" 텍스트 팝업
    FloatingTextManager.Instance.Spawn("WEAK!", transform.position, Color.yellow);

    // 화면 진동 강화 (CinemachineImpulse)
    _impulseSource.GenerateImpulse(multiplier * 0.3f);

    // 히트스톱 강화
    TimeScaleManager.Instance.DoHitStop(0.08f);
}
```

---

### 약점 인디케이터 (플레이어 힌트 UI)

```csharp
// 적의 등이 플레이어에게 노출될 때 등에 약점 표시 아이콘 활성화
public class WeakPointIndicator : MonoBehaviour
{
    [SerializeField] private GameObject backIndicatorIcon; // 등 위 빨간 점

    private Transform _catTransform;

    private void Update()
    {
        if (_catTransform == null) return;

        AttackDirection dir = DirectionUtils.GetAttackDirection(transform, _catTransform.position);
        backIndicatorIcon.SetActive(dir == AttackDirection.Back);
    }
}
```

## OnionCat 적용 포인트

### 협력 필수 적 설계 테이블

| 적 유형 | 약점 방향 | 필요 공격 | 협력 방식 |
|--------|---------|---------|---------|
| 갑옷 기사 | 등 (Back) | 근접(Cat) | Onion이 정면 견제 → Cat이 뒤로 돌아가 슬래시 |
| 등껍질 괴물 | 정면 (Front) | 원거리(Onion) | Cat 근접 공격 반격당함 → Onion만 정면 공격 가능 |
| 방패 기사 | 측면 (Side) | 양쪽 | Cat이 측면 육박, Onion이 반대쪽 측면 조준 |
| 고속 돌격 적 | 이동 중 | 근접(Cat) | 너무 빨라 Onion 조준 불가, Cat 대시로 따라가 슬래시 |

### 적 프리팹 Inspector 설정

```
EnemyObject
  ├── EnemyBase (스크립트)
  ├── DirectionalWeakPoint (스크립트)
  │     ├── backstabMultiplier: 2.0
  │     └── flankMultiplier: 1.5
  └── WeakPointIndicator (스크립트)
        └── backIndicatorIcon: [빨간 점 오브젝트 드래그]
```

유니티 에디터에서 **드래그 앤 드롭 설정 필요**:
- 각 적 프리팹의 Inspector에서 `EnemyWeakPointData` ScriptableObject 할당
- `WeakPointIndicator`의 `backIndicatorIcon` 오브젝트 연결
- Cat 오브젝트 레퍼런스 할당 (또는 GameManager에서 런타임에 주입)

## 참고 링크

- Unity Vector2.Dot: https://docs.unity3d.com/ScriptReference/Vector2.Dot.html
- 히트박스 레이어 설정: `Design/References/Tech/Hitbox_Design.md`
- 속성 약점 시스템: `Design/References/Tech/Enemy_Weakness_Resistance_System.md`
- 데미지 시스템: `Design/References/Tech/Damage_System.md`
- 부유 텍스트: `Design/References/Tech/Floating_Damage_Numbers.md`
