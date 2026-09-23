# Enemy Pattern Composition System

리서치 날짜: 2026-09-23

## 개요

"패턴 조합 시스템"은 **원자적 공격 패턴(Atomic Pattern)을 작은 블록으로 만들어두고, 이들을 조합해 다양한 적을 빠르게 설계**하는 접근법이다.

기존의 Enemy_AI_StateMachine이 상태 전환(Idle→Chase→Attack)을 다룬다면, 이 시스템은 **Attack 상태 내부**에서 어떤 행동 시퀀스를 실행할지를 데이터 주도(ScriptableObject)로 정의한다.

OnionCat에서는 근접 전용/원거리 전용/혼합형 적들이 모두 필요하므로, 패턴 구성 블록을 재사용하면 개발 속도가 크게 향상된다.

---

## Unity 구현 방법

### 1. 패턴 블록 기반 구조

```csharp
// 원자적 행동 블록 — ScriptableObject로 정의
public abstract class EnemyActionSO : ScriptableObject
{
    public abstract IEnumerator Execute(EnemyController enemy);
}
```

기본 블록 예시:
```csharp
// WaitAction.cs
[CreateAssetMenu(menuName = "Enemy/Action/Wait")]
public class WaitAction : EnemyActionSO
{
    public float duration = 0.5f;
    public override IEnumerator Execute(EnemyController enemy)
    {
        yield return new WaitForSeconds(duration);
    }
}

// MoveTowardPlayerAction.cs
[CreateAssetMenu(menuName = "Enemy/Action/MoveTowardPlayer")]
public class MoveTowardPlayerAction : EnemyActionSO
{
    public float duration = 1f;
    public float speed = 3f;
    public override IEnumerator Execute(EnemyController enemy)
    {
        float t = 0;
        while (t < duration)
        {
            t += Time.deltaTime;
            Vector2 dir = (enemy.Target.position - enemy.transform.position).normalized;
            enemy.Rigidbody.linearVelocity = dir * speed;
            yield return null;
        }
        enemy.Rigidbody.linearVelocity = Vector2.zero;
    }
}

// ShootProjectileAction.cs
[CreateAssetMenu(menuName = "Enemy/Action/ShootProjectile")]
public class ShootProjectileAction : EnemyActionSO
{
    public GameObject projectilePrefab;
    public int count = 1;
    public float spreadAngle = 0f;
    public override IEnumerator Execute(EnemyController enemy)
    {
        Vector2 dir = (enemy.Target.position - enemy.transform.position).normalized;
        float startAngle = -spreadAngle * 0.5f * (count - 1);
        for (int i = 0; i < count; i++)
        {
            float angle = startAngle + spreadAngle * i;
            Vector2 shotDir = Quaternion.Euler(0, 0, angle) * dir;
            var proj = PoolManager.Spawn(projectilePrefab, enemy.transform.position, Quaternion.identity);
            proj.GetComponent<Projectile>().Launch(shotDir);
        }
        yield return null;
    }
}
```

### 2. 패턴 시퀀스 (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "Enemy/Pattern/Sequence")]
public class AttackPatternSO : ScriptableObject
{
    [Header("패턴 블록 목록 (순서대로 실행)")]
    public EnemyActionSO[] actions;

    [Header("전체 반복 횟수 (0 = 무한)")]
    public int repeatCount = 1;

    public IEnumerator Execute(EnemyController enemy)
    {
        int loops = repeatCount == 0 ? int.MaxValue : repeatCount;
        for (int i = 0; i < loops; i++)
        {
            foreach (var action in actions)
                yield return enemy.StartCoroutine(action.Execute(enemy));
        }
    }
}
```

### 3. 적 컨트롤러에서 패턴 실행

```csharp
public class EnemyController : MonoBehaviour
{
    [SerializeField] private AttackPatternSO[] patterns;
    public Transform Target { get; private set; }
    public Rigidbody2D Rigidbody { get; private set; }

    private Coroutine _activePattern;

    private void Awake() => Rigidbody = GetComponent<Rigidbody2D>();

    public void SetTarget(Transform t) => Target = t;

    public void ExecutePattern(int index)
    {
        if (_activePattern != null) StopCoroutine(_activePattern);
        _activePattern = StartCoroutine(patterns[index].Execute(this));
    }

    // AI 상태머신에서 Attack 상태 진입 시 호출
    public void OnEnterAttack() => ExecutePattern(0);
}
```

### 4. 복합 패턴 예시 (Inspector에서 조합)

**슬라임 돌진 패턴** (MeleeOnly 적):
```
AttackPattern_SlimeCharge:
  actions:
    [0] TelegraphAction (duration: 0.4, showIndicator: true)
    [1] MoveTowardPlayerAction (duration: 0.3, speed: 8)
    [2] MeleeHitCheckAction (radius: 0.5, damage: 10)
    [3] WaitAction (duration: 0.5)
  repeatCount: 3
```

**꽃잎 세례 패턴** (RangedOnly 적):
```
AttackPattern_FlowerSpread:
  actions:
    [0] WaitAction (duration: 0.3)
    [1] ShootProjectileAction (count: 5, spreadAngle: 60)
    [2] WaitAction (duration: 1.0)
  repeatCount: 0  // 무한
```

**1페이즈 보스** (HP 50% 이상, 근접 전용):
```
AttackPattern_BossPhase1:
  actions:
    [0] MoveTowardPlayerAction (duration: 1.0)
    [1] MeleeHitCheckAction (radius: 1.0)
    [2] WaitAction (duration: 1.5)
```

**2페이즈 보스** (HP 50% 미만, 근거리+원거리 혼합):
패턴 전환은 EnemyController의 OnHealthChanged에서 `ExecutePattern(1)` 호출

---

## OnionCat 적용 포인트

### 핵심: 피아 구분과 약점 시스템

OnionCat의 **"근접으로만 처치 가능한 적"**, **"원거리로만 처치 가능한 적"** 설계에 맞게 패턴 블록에 면역 정보를 같이 설정:

```csharp
// EnemyController에 추가
public enum AttackTypeResistance { None, ImmuneToMelee, ImmuneToRanged }

[SerializeField] private AttackTypeResistance resistance;

public bool IsImmuneTo(DamageType type)
{
    return resistance switch {
        AttackTypeResistance.ImmuneToMelee  => type == DamageType.Melee,
        AttackTypeResistance.ImmuneToRanged => type == DamageType.Ranged,
        _ => false
    };
}
```

면역일 때 데미지 처리 (DamageSystem에서):
```csharp
if (enemy.IsImmuneTo(dmgType))
{
    // 데미지 0, "IMMUNE" 팝업 표시
    FloatingTextManager.Show("IMMUNE", hitPos, Color.gray);
    return;
}
```

### 패턴 블록 재사용 예시

| 블록 | 슬라임 | 거미 | 꽃 | 보스1 | 보스2 |
|------|--------|------|-----|-------|-------|
| Wait | ✓ | ✓ | ✓ | ✓ | ✓ |
| MoveToward | ✓ | ✓ | | ✓ | ✓ |
| MeleeHit | ✓ | ✓ | | ✓ | |
| ShootProjectile | | | ✓ | | ✓ |
| TelegraphAction | | ✓ | | ✓ | ✓ |

→ 블록 7개로 5종 적의 다양한 패턴 구성 가능

### 단계적 도입 순서

1. `WaitAction`, `MoveTowardPlayerAction` 먼저 구현 → 기본 추적적 완성
2. `MeleeHitCheckAction` → 근접 공격 적 완성
3. `ShootProjectileAction` → 원거리 적 완성
4. `TelegraphAction` → 전조 연출 추가
5. 보스용 `MultiPhaseEnemy` 컴포넌트 → HP 임계값에서 패턴 인덱스 전환

---

## 참고 링크

- [Unity Manual: Coroutines](https://docs.unity3d.com/Manual/Coroutines.html)
- [GDC: Spelunky's Enemy AI](https://www.gdcvault.com/play/1015317/The-Spelunky-Spelunkython-Making-a)
- [Game Programming Patterns: Command Pattern](https://gameprogrammingpatterns.com/command.html)
- [ScriptableObject Architecture in Unity (Ryan Hipple, Unite 2017)](https://www.youtube.com/watch?v=raQ3iHhE_Kk)
