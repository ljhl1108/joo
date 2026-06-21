# 근접전 시스템 (Melee Combat System)

리서치 날짜: 2026-06-21

## 개요

근접전 시스템은 플레이어가 적과 물리적으로 가까이서 공격하는 모든 메카닉을 포함한다. OnionCat에서 **고양이(Cat) 플레이어의 핵심 전투 도구**로, 180° 슬래시 + 무적 대시가 주력이다. 히트박스 타이밍, 애니메이션 연동, 콤보 판정, 무적 프레임 설계가 핵심이다.

## Unity 구현 방법

### 1. 기본 공격 구조 — 애니메이션 이벤트 방식

```csharp
public class CatAttack : MonoBehaviour
{
    [SerializeField] private Transform attackPoint;
    [SerializeField] private float attackRadius = 1.2f;
    [SerializeField] private LayerMask enemyLayers;
    [SerializeField] private float attackDamage = 10f;

    private Animator _animator;
    private bool _isAttacking;
    private static readonly int AttackHash = Animator.StringToHash("Attack");

    void Awake()
    {
        _animator = GetComponent<Animator>();
    }

    void Update()
    {
        // New Input System에서 버튼 입력 처리 (PlayerInput 컴포넌트 콜백에서 호출)
        // Attack() 호출은 OnAttack(InputAction.CallbackContext) 에서 처리
    }

    public void OnAttack(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed || _isAttacking) return;
        _isAttacking = true;
        _animator.SetTrigger(AttackHash);
    }

    // ★ AnimationEvent에서 호출 — 공격 판정 활성화 프레임에 삽입
    public void ActivateHitbox()
    {
        Collider2D[] hits = Physics2D.OverlapCircleAll(
            attackPoint.position, attackRadius, enemyLayers);

        foreach (var hit in hits)
        {
            if (hit.TryGetComponent<IDamageable>(out var target))
                target.TakeDamage(attackDamage);
        }
    }

    // ★ AnimationEvent에서 호출 — 공격 종료 프레임에 삽입
    public void EndAttack()
    {
        _isAttacking = false;
    }
}
```

### 2. 180° 슬래시 — 부채꼴 판정 (OverlapBoxAll + 각도 필터링)

```csharp
// 180° 앞쪽 부채꼴만 판정하는 방법
void SlashHitbox()
{
    Vector2 facingDir = transform.right; // 캐릭터가 바라보는 방향
    Collider2D[] hits = Physics2D.OverlapCircleAll(
        attackPoint.position, attackRadius, enemyLayers);

    foreach (var hit in hits)
    {
        Vector2 toEnemy = (hit.transform.position - transform.position).normalized;
        float angle = Vector2.Angle(facingDir, toEnemy);

        if (angle <= 90f) // 양쪽 90° = 총 180° 범위
        {
            if (hit.TryGetComponent<IDamageable>(out var target))
                target.TakeDamage(attackDamage);
        }
    }
}
```

### 3. IDamageable 인터페이스

```csharp
public interface IDamageable
{
    void TakeDamage(float damage);
}

public class EnemyHealth : MonoBehaviour, IDamageable
{
    [SerializeField] private float maxHealth = 30f;
    private float _currentHealth;

    void Awake() => _currentHealth = maxHealth;

    public void TakeDamage(float damage)
    {
        _currentHealth -= damage;
        if (_currentHealth <= 0f) Die();
    }

    void Die() { /* 드롭, 사망 애니메이션, 오브젝트 비활성화 */ }
}
```

### 4. 무적 대시 구현

```csharp
public class CatDash : MonoBehaviour
{
    [SerializeField] private float dashSpeed = 12f;
    [SerializeField] private float dashDuration = 0.2f;
    [SerializeField] private LayerMask enemyProjectileLayers;

    private Collider2D _bodyCollider;
    private Rigidbody2D _rb;
    private bool _isDashing;

    void Awake()
    {
        _bodyCollider = GetComponent<Collider2D>();
        _rb = GetComponent<Rigidbody2D>();
    }

    public void OnDash(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed || _isDashing) return;
        StartCoroutine(DashRoutine());
    }

    IEnumerator DashRoutine()
    {
        _isDashing = true;
        // 적 투사체 레이어와 충돌 비활성화 → 무적
        Physics2D.IgnoreLayerCollision(
            gameObject.layer,
            LayerMask.NameToLayer("EnemyProjectile"), true);

        Vector2 dashDir = GetMoveDirection();
        _rb.linearVelocity = dashDir * dashSpeed;

        yield return new WaitForSeconds(dashDuration);

        _rb.linearVelocity = Vector2.zero;
        Physics2D.IgnoreLayerCollision(
            gameObject.layer,
            LayerMask.NameToLayer("EnemyProjectile"), false);
        _isDashing = false;
    }

    Vector2 GetMoveDirection()
    {
        // New Input System에서 이동 방향 참조
        return Vector2.right; // 실제 구현에서는 입력값 사용
    }
}
```

### 5. 히트스톱 (타격감 강화)

```csharp
IEnumerator HitStop(float duration = 0.05f)
{
    Time.timeScale = 0f;
    yield return new WaitForSecondsRealtime(duration);
    Time.timeScale = 1f;
}
```

### 6. Animator 설정 요점

- `Idle → Attack`: Trigger "Attack" 발동 시 전환
- `Attack → Idle`: 공격 애니메이션 끝나면 자동 복귀 (Exit Time 1.0)
- 공격 애니메이션 구조: **선딜 1~2프레임 → 히트판정 1~2프레임 → 후딜 1~2프레임**
- AnimationEvent 2개 삽입: `ActivateHitbox` (히트판정 시작 프레임), `EndAttack` (마지막 프레임)

## OnionCat 적용 포인트

### 고양이 전투 구현 순서
1. `CatAttack.cs` — OverlapCircleAll + 각도 필터로 180° 슬래시 판정
2. `CatDash.cs` — 레이어 충돌 비활성화로 무적 구현
3. Animator에 Attack/Dash 파라미터 설정, AnimationEvent 삽입
4. IDamageable 인터페이스를 모든 적 구현 → 통일된 데미지 API
5. HitStop 코루틴 → 타격마다 0.05~0.08초 타임스케일 0

### 레이어 설계 권장
| 레이어 | 내용 |
|--------|------|
| Player | 고양이+양파 공유 몸체 |
| PlayerAttack | 고양이 근접 히트박스 |
| Enemy | 일반 적 |
| EnemyProjectile | 적 투사체 (대시 중 무시) |
| PlayerProjectile | 양파 원거리 씨앗 |

### 주의 사항
- `[SerializeField] private Transform attackPoint` → 유니티 에디터에서 드래그 앤 드롭 설정 필요
- `[SerializeField] private LayerMask enemyLayers` → 유니티 에디터에서 드래그 앤 드롭 설정 필요
- Update()에서 GetComponent 금지, Awake()에서 캐싱

## 참고 링크

- Sharp Coder Blog — 2D Melee Attack: https://www.sharpcoderblog.com/blog/2d-melee-attack-tutorial-for-unity
- Pav Creations — Melee AI: https://pavcreations.com/melee-attacks-and-ai-combat-mechanic-in-2d-unity-games/
- Medium — Hitbox Detection: https://medium.com/nerd-for-tech/implementing-hitbox-detection-for-melee-combat-unity-bc1912178e63
- YouTube Tutorial: https://www.youtube.com/watch?v=1QfxdUpVh5I
- Unity Docs Physics2D.OverlapCircleAll: https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircleAll.html
