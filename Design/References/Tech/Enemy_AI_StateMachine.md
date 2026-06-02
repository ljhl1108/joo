# 적 AI: 상태머신 (Idle / Chase / Attack)

## 개요

유한 상태 머신(Finite State Machine, FSM)은 적 AI를 구현하는 가장 범용적인 방법이다.
적의 행동을 명확한 "상태(State)"로 나누고, 조건에 따라 전환(Transition)시킨다.
OnionCat에서 모든 적(근접형·원거리형·혼합형)의 기반 구조로 사용된다.

---

## Unity 구현 방법

### 1. 상태 열거형 정의

```csharp
public enum EnemyState
{
    Idle,
    Chase,
    Attack,
    Dead
}
```

### 2. 기본 적 클래스

```csharp
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public class EnemyBase : MonoBehaviour
{
    [SerializeField] private float detectionRange = 5f;
    [SerializeField] private float attackRange    = 1.5f;
    [SerializeField] private float moveSpeed      = 2f;
    [SerializeField] private LayerMask obstacleLayer;

    protected EnemyState currentState = EnemyState.Idle;
    protected Transform  player;
    private   Rigidbody2D rb;

    protected virtual void Awake()
    {
        rb     = GetComponent<Rigidbody2D>();
        // Player 태그로 Cat(P1) 찾기 — Update()에서 Find 금지
        var go = GameObject.FindGameObjectWithTag("Player");
        if (go != null) player = go.transform;
    }

    protected virtual void Update()
    {
        if (player == null) return;

        switch (currentState)
        {
            case EnemyState.Idle:   UpdateIdle();   break;
            case EnemyState.Chase:  UpdateChase();  break;
            case EnemyState.Attack: UpdateAttack(); break;
        }
    }

    // ── 상태별 로직 ──────────────────────────────

    protected virtual void UpdateIdle()
    {
        if (IsPlayerInRange(detectionRange) && HasLineOfSight())
            ChangeState(EnemyState.Chase);
    }

    protected virtual void UpdateChase()
    {
        float dist = DistToPlayer();

        if (dist > detectionRange)          { ChangeState(EnemyState.Idle);   return; }
        if (dist <= attackRange)            { ChangeState(EnemyState.Attack); return; }

        Vector2 dir = ((Vector2)player.position - rb.position).normalized;
        rb.MovePosition(rb.position + dir * moveSpeed * Time.deltaTime);

        // 방향에 따라 스프라이트 뒤집기
        transform.localScale = new Vector3(dir.x > 0 ? 1 : -1, 1, 1);
    }

    protected virtual void UpdateAttack()
    {
        if (DistToPlayer() > attackRange)
        {
            ChangeState(EnemyState.Chase);
            return;
        }
        // 하위 클래스에서 오버라이드하여 실제 공격 구현
    }

    // ── 상태 전환 ─────────────────────────────────

    protected void ChangeState(EnemyState newState)
    {
        OnExitState(currentState);
        currentState = newState;
        OnEnterState(currentState);
    }

    protected virtual void OnEnterState(EnemyState state) { }
    protected virtual void OnExitState(EnemyState state)  { }

    // ── 유틸리티 ──────────────────────────────────

    protected float DistToPlayer()
        => Vector2.Distance(transform.position, player.position);

    protected bool IsPlayerInRange(float range)
        => DistToPlayer() <= range;

    protected bool HasLineOfSight()
    {
        Vector2 origin = transform.position;
        Vector2 dir    = (player.position - transform.position).normalized;
        float   dist   = DistToPlayer();

        RaycastHit2D hit = Physics2D.Raycast(origin, dir, dist, obstacleLayer);
        return hit.collider == null; // 장애물이 없으면 시야 확보
    }
}
```

### 3. 근접형 적 (Melee Enemy) — EnemyBase 상속

```csharp
using UnityEngine;

public class MeleeEnemy : EnemyBase
{
    [SerializeField] private float attackCooldown = 1.2f;
    [SerializeField] private int   attackDamage   = 10;

    private float lastAttackTime;

    protected override void OnEnterState(EnemyState state)
    {
        if (state == EnemyState.Attack) lastAttackTime = -attackCooldown; // 즉시 첫 공격
    }

    protected override void UpdateAttack()
    {
        base.UpdateAttack(); // 범위 벗어나면 Chase로 전환

        if (Time.time - lastAttackTime >= attackCooldown)
        {
            lastAttackTime = Time.time;
            PerformAttack();
        }
    }

    private void PerformAttack()
    {
        // 근접 범위 내 플레이어에게 데미지
        Collider2D hit = Physics2D.OverlapCircle(transform.position, 1.5f,
                             LayerMask.GetMask("Player"));
        if (hit != null)
            hit.GetComponent<PlayerHealth>()?.TakeDamage(attackDamage);
    }
}
```

### 4. 시야각(Cone Detection) 추가

```csharp
protected bool IsInFieldOfView(float angle)
{
    Vector2 toPlayer = (player.position - transform.position).normalized;
    Vector2 forward  = transform.right * Mathf.Sign(transform.localScale.x);
    float   dot      = Vector2.Dot(forward, toPlayer);
    return dot >= Mathf.Cos(angle * 0.5f * Mathf.Deg2Rad);
}
```

### 5. 상태머신 Gizmo 디버그 (에디터 확인용)

```csharp
private void OnDrawGizmos()
{
    Gizmos.color = Color.yellow;
    Gizmos.DrawWireSphere(transform.position, detectionRange);
    Gizmos.color = Color.red;
    Gizmos.DrawWireSphere(transform.position, attackRange);
}
```

---

## OnionCat 적용 포인트

### 약점 시스템 연동
```csharp
public enum WeaknessType { MeleeOnly, RangedOnly, Both }

public class EnemyBase : MonoBehaviour
{
    [SerializeField] public WeaknessType weakness;

    public void TakeDamage(int dmg, WeaknessType attackType)
    {
        if (weakness != WeaknessType.Both && attackType != weakness)
        {
            // 약점 아닌 공격 → 0 데미지 + "면역" 이펙트
            ShowImmuneEffect();
            return;
        }
        currentHp -= dmg;
    }
}
```

### 적 종류별 상태머신 분기
| 적 타입 | Idle | Chase 조건 | Attack |
|---------|------|-----------|--------|
| MeleeEnemy | 정지 대기 | 탐지 범위 진입 | 근접 공격 |
| RangedEnemy | 정지 대기 | 탐지 범위 진입 | 적정 거리 유지 + 투사체 발사 |
| ShieldEnemy | 순찰 | 시야각 감지 | 방패 전진 → 타이밍 공격 |

- **Awake에서 플레이어 참조**: Update 내 `Find` 금지 (CLAUDE.md 규칙)
- **상속 구조**: `EnemyBase` → `MeleeEnemy`, `RangedEnemy`, `BossEnemy` — 능력 교체 가능 추상 구조와 일치

---

## 참고 링크

- Code Monkey — Simple Enemy AI (State Machine): https://unitycodemonkey.com/video.php?v=db0KWYaWfeM
- Faramira — FSM with C# Delegates: https://faramira.com/enemy-behaviour-with-finite-state-machine-using-csharp-delegates-in-unity/
- Sharp Coder — Enemy AI in Unity: https://www.sharpcoderblog.com/blog/implementing-enemy-ai-in-unity
- Unity Learn — NavMesh 2D (참고): https://docs.unity3d.com/Manual/nav-NavigationOverview.html
