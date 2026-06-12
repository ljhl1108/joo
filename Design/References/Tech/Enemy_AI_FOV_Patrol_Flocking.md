# 적 AI 심화 — 시야각(FOV) & 패트롤 & 군집 행동

리서치 날짜: 2026-06-12

---

## 개요

OnionCat은 2인 협동 탑다운 픽셀아트 로그라이크다. 적 AI가 단순히 플레이어를 감지하고 돌진하는 수준을 넘어, 다음 세 가지를 갖춰야 전략적 재미가 생긴다.

| 기술 | 역할 |
|------|------|
| **FOV(시야각)** | 적이 "볼 수 있을 때만" 반응 → 은신·기습 플레이 가능 |
| **패트롤** | 탐지 전 자연스러운 배회 → 룸 진입 긴장감 상승 |
| **군집 행동** | 여러 적이 함께 에워싸기 → 역할 분담(근접/원거리) 강제 |

기존 `Enemy_AI_StateMachine.md`의 `EnemyBase` 클래스를 기반으로 Patrol 상태와 고급 FOV 감지를 확장한다.

---

## Unity 구현 방법

### 1. 시야각(FOV) 감지

#### 1-1. 개념

탑다운 2D에서 FOV는 세 단계로 구현된다.

```
[1단계] 반경 검사   Physics2D.OverlapCircleAll  → 근처 콜라이더 목록
[2단계] 각도 검사   Vector2.Angle               → 시야각 내부인지 확인
[3단계] 직선 검사   Physics2D.Raycast           → 벽/장애물 관통 방지
```

세 조건을 **모두** 통과해야 "플레이어를 발견"으로 처리한다.

#### 1-2. Approach A — OverlapCircle + 각도 체크 + Raycast (권장)

```csharp
using UnityEngine;

public class EnemyFOV : MonoBehaviour
{
    [SerializeField] private float viewRadius    = 6f;   // 시야 반경 (미터)
    [SerializeField] private float viewAngle     = 90f;  // 시야각 (도, 전체 원뿔 폭)
    [SerializeField] private LayerMask playerMask;       // "Player" 레이어
    [SerializeField] private LayerMask obstacleMask;     // "Wall", "Obstacle" 레이어

    // 캐시: Awake에서 초기화
    private Transform _playerTransform;

    private void Awake()
    {
        // Update() 안에서 FindGameObjectWithTag 금지 — 여기서만 호출
        var playerGO = GameObject.FindGameObjectWithTag("Player");
        if (playerGO != null) _playerTransform = playerGO.transform;
    }

    /// <summary>
    /// 플레이어가 FOV 안에 있으면 true 반환.
    /// EnemyAI의 Update()에서 매 프레임 또는 InvokeRepeating으로 호출.
    /// </summary>
    public bool CanSeePlayer()
    {
        if (_playerTransform == null) return false;

        // ─── 1단계: 반경 검사 ──────────────────────────────────────
        float dist = Vector2.Distance(transform.position, _playerTransform.position);
        if (dist > viewRadius) return false;

        // ─── 2단계: 각도 검사 ──────────────────────────────────────
        // 적의 "전방" = transform.right (스프라이트가 오른쪽을 향한다고 가정)
        Vector2 dirToPlayer = (_playerTransform.position - transform.position).normalized;
        float   angle       = Vector2.Angle(transform.right, dirToPlayer);
        if (angle > viewAngle * 0.5f) return false;    // 반각과 비교

        // ─── 3단계: 직선 시야 검사 ─────────────────────────────────
        RaycastHit2D hit = Physics2D.Raycast(
            transform.position,
            dirToPlayer,
            dist,
            obstacleMask
        );
        // 장애물에 맞으면 시야 차단
        return hit.collider == null;
    }

    // 에디터에서 시야각 시각화
    private void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(transform.position, viewRadius);

        // 시야각 경계선 두 개
        Vector3 leftBound  = Quaternion.Euler(0, 0,  viewAngle * 0.5f) * transform.right;
        Vector3 rightBound = Quaternion.Euler(0, 0, -viewAngle * 0.5f) * transform.right;
        Gizmos.color = Color.cyan;
        Gizmos.DrawRay(transform.position, leftBound  * viewRadius);
        Gizmos.DrawRay(transform.position, rightBound * viewRadius);
    }
}
```

> **Inspector 설정 필요**: `playerMask`에 "Player" 레이어, `obstacleMask`에 "Wall"/"Obstacle" 레이어를 드래그 앤 드롭.

#### 1-3. Approach B — OverlapCircleAll (다수 타겟 처리)

적 하나가 P1(Cat)과 P2(OnionCat) 둘 다 탐지해야 할 때.

```csharp
/// <summary>
/// viewRadius 안의 모든 플레이어를 검사하여 FOV + LOS 통과한 첫 타겟 반환.
/// </summary>
public Transform FindVisibleTarget()
{
    Collider2D[] hits = Physics2D.OverlapCircleAll(transform.position,
                                                    viewRadius,
                                                    playerMask);
    foreach (Collider2D col in hits)
    {
        Vector2 dirToTarget = (col.transform.position - transform.position).normalized;
        float   angle       = Vector2.Angle(transform.right, dirToTarget);

        if (angle > viewAngle * 0.5f) continue;   // 각도 밖

        float dist = Vector2.Distance(transform.position, col.transform.position);
        RaycastHit2D hit = Physics2D.Raycast(transform.position, dirToTarget,
                                              dist, obstacleMask);
        if (hit.collider == null)
            return col.transform;   // 시야 확보 — 타겟 반환
    }
    return null;
}
```

#### 1-4. 적의 "전방" 방향 관리 팁

탑다운에서 적이 이동 방향을 향하도록 `transform.right`를 갱신한다.

```csharp
// 이동 시 전방 방향 동기화 (Rigidbody2D 이동 후 호출)
private void FaceDirection(Vector2 moveDir)
{
    if (moveDir.sqrMagnitude < 0.01f) return;
    float angle = Mathf.Atan2(moveDir.y, moveDir.x) * Mathf.Rad2Deg;
    transform.rotation = Quaternion.Euler(0f, 0f, angle);
}
```

#### 1-5. 성능 최적화 — InvokeRepeating

FOV 검사를 매 프레임 하지 않아도 된다. 0.2초마다 실행하면 CPU 부담 60~80% 감소.

```csharp
private void Start()
{
    InvokeRepeating(nameof(CheckFOV), 0f, 0.2f);
}

private void CheckFOV()
{
    _canSeePlayer = CanSeePlayer();
}
```

---

### 2. 패트롤 AI

#### 2-1. 웨이포인트 패트롤 (구조화된 룸)

복도나 정해진 경로에 적합. Inspector에서 배열로 포인트를 드래그 앤 드롭.

```csharp
using UnityEngine;

public class EnemyPatrol : MonoBehaviour
{
    [SerializeField] private Transform[]   waypoints;        // 순찰 지점 배열
    [SerializeField] private float         moveSpeed    = 2f;
    [SerializeField] private float         waypointTolerance = 0.15f; // 도달 판정 거리
    [SerializeField] private bool          loop         = true;       // 순환 or 왕복

    private int         _currentIndex = 0;
    private bool        _goingForward = true;
    private Rigidbody2D _rb;

    private void Awake()
    {
        _rb = GetComponent<Rigidbody2D>();
    }

    public void UpdatePatrol()
    {
        if (waypoints == null || waypoints.Length == 0) return;

        Transform target = waypoints[_currentIndex];
        Vector2   dir    = ((Vector2)target.position - _rb.position).normalized;

        _rb.MovePosition(_rb.position + dir * moveSpeed * Time.deltaTime);
        FaceDirection(dir);

        // 웨이포인트 도달 판정
        if (Vector2.Distance(_rb.position, target.position) <= waypointTolerance)
            AdvanceWaypoint();
    }

    private void AdvanceWaypoint()
    {
        if (loop)
        {
            _currentIndex = (_currentIndex + 1) % waypoints.Length;
        }
        else
        {
            // 왕복 (A→B→A)
            if (_goingForward)
            {
                if (_currentIndex < waypoints.Length - 1) _currentIndex++;
                else { _goingForward = false; _currentIndex--; }
            }
            else
            {
                if (_currentIndex > 0) _currentIndex--;
                else { _goingForward = true; _currentIndex++; }
            }
        }
    }

    private void FaceDirection(Vector2 dir)
    {
        if (dir.sqrMagnitude < 0.01f) return;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
        transform.rotation = Quaternion.Euler(0f, 0f, angle);
    }

    private void OnDrawGizmos()
    {
        if (waypoints == null) return;
        Gizmos.color = Color.green;
        for (int i = 0; i < waypoints.Length; i++)
        {
            if (waypoints[i] == null) continue;
            Gizmos.DrawSphere(waypoints[i].position, 0.1f);
            int next = loop ? (i + 1) % waypoints.Length : Mathf.Min(i + 1, waypoints.Length - 1);
            if (waypoints[next] != null)
                Gizmos.DrawLine(waypoints[i].position, waypoints[next].position);
        }
    }
}
```

> **Inspector 설정 필요**: `waypoints` 배열 크기 설정 후 씬의 빈 GameObject(웨이포인트 마커)를 드래그 앤 드롭.

#### 2-2. 랜덤 배회 패트롤 (로그라이크 랜덤 룸)

절차적으로 생성된 룸에서 미리 웨이포인트를 배치하기 어렵다. 랜덤 지점을 선택해 이동.

```csharp
using System.Collections;
using UnityEngine;

public class EnemyWander : MonoBehaviour
{
    [SerializeField] private float wanderRadius  = 4f;    // 현재 위치 기준 이동 반경
    [SerializeField] private float moveSpeed     = 1.5f;
    [SerializeField] private float idleTime      = 1.5f;  // 목적지 도달 후 대기 시간
    [SerializeField] private LayerMask wallMask;          // 벽 레이어

    private Vector2     _startPos;     // 룸 진입 시 시작 위치
    private Vector2     _targetPos;
    private bool        _isWaiting;
    private Rigidbody2D _rb;

    private void Awake()
    {
        _rb       = GetComponent<Rigidbody2D>();
        _startPos = transform.position;
        _targetPos = transform.position;
    }

    public void UpdateWander()
    {
        if (_isWaiting) return;

        Vector2 dir = (_targetPos - _rb.position);
        if (dir.magnitude <= 0.2f)
        {
            StartCoroutine(WaitThenPickTarget());
            return;
        }

        _rb.MovePosition(_rb.position + dir.normalized * moveSpeed * Time.deltaTime);
    }

    private IEnumerator WaitThenPickTarget()
    {
        _isWaiting = true;
        yield return new WaitForSeconds(idleTime);
        _targetPos = PickRandomTarget();
        _isWaiting = false;
    }

    private Vector2 PickRandomTarget()
    {
        // 최대 10번 시도: 벽 안 지점 걸러내기
        for (int i = 0; i < 10; i++)
        {
            Vector2 candidate = _startPos + Random.insideUnitCircle * wanderRadius;
            // 후보 지점에 벽이 없으면 채택
            if (Physics2D.OverlapCircle(candidate, 0.3f, wallMask) == null)
                return candidate;
        }
        return _startPos;  // 10번 실패 시 원점 복귀
    }
}
```

---

### 3. 군집 행동 (Flocking / Boids)

Craig Reynolds의 Boids 알고리즘(1986)을 2D Unity에 적용. 세 가지 단순 규칙에서 자연스러운 군집 행동이 창발한다.

| 규칙 | 설명 |
|------|------|
| **분리(Separation)** | 너무 가까운 이웃을 피한다 |
| **정렬(Alignment)** | 이웃의 평균 이동 방향을 따른다 |
| **응집(Cohesion)** | 이웃의 중심 쪽으로 이동한다 |

#### 3-1. FlockAgent 컴포넌트 (각 적에게 부착)

```csharp
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public class FlockAgent : MonoBehaviour
{
    // FlockManager가 할당
    [HideInInspector] public FlockManager flock;

    public Rigidbody2D Rb { get; private set; }

    private void Awake()
    {
        Rb = GetComponent<Rigidbody2D>();
    }

    public void Move(Vector2 velocity)
    {
        if (velocity.sqrMagnitude < 0.01f) return;
        Rb.velocity = velocity;

        // 이동 방향으로 스프라이트 회전
        float angle = Mathf.Atan2(velocity.y, velocity.x) * Mathf.Rad2Deg;
        transform.rotation = Quaternion.Euler(0f, 0f, angle);
    }
}
```

#### 3-2. FlockManager (군집 전체 제어)

```csharp
using System.Collections.Generic;
using UnityEngine;

public class FlockManager : MonoBehaviour
{
    [Header("군집 설정")]
    [SerializeField] private FlockAgent agentPrefab;
    [SerializeField] private int        agentCount       = 8;
    [SerializeField] private float      spawnRadius      = 3f;

    [Header("이동")]
    [SerializeField] private float      maxSpeed         = 3f;
    [SerializeField] private float      maxSteerForce    = 2f;

    [Header("규칙 반경")]
    [SerializeField] private float      perceptionRadius = 2.5f;  // 이웃 감지 반경
    [SerializeField] private float      separationRadius = 1.0f;  // 분리 작동 반경

    [Header("규칙 가중치")]
    [SerializeField] private float      separationWeight = 2.0f;
    [SerializeField] private float      alignmentWeight  = 1.0f;
    [SerializeField] private float      cohesionWeight   = 1.0f;

    private List<FlockAgent> _agents = new List<FlockAgent>();

    private void Start()
    {
        // 초기 스폰
        for (int i = 0; i < agentCount; i++)
        {
            Vector2     pos   = (Vector2)transform.position + Random.insideUnitCircle * spawnRadius;
            FlockAgent  agent = Instantiate(agentPrefab, pos, Quaternion.identity, transform);
            agent.flock = this;
            // 랜덤 초기 속도
            agent.Rb.velocity = Random.insideUnitCircle.normalized * maxSpeed * 0.5f;
            _agents.Add(agent);
        }
    }

    private void FixedUpdate()
    {
        foreach (FlockAgent agent in _agents)
            UpdateAgent(agent);
    }

    private void UpdateAgent(FlockAgent agent)
    {
        List<FlockAgent> neighbors    = GetNeighbors(agent, perceptionRadius);
        List<FlockAgent> closeNeighbors = GetNeighbors(agent, separationRadius);

        Vector2 separation = CalculateSeparation(agent, closeNeighbors) * separationWeight;
        Vector2 alignment  = CalculateAlignment(agent, neighbors)        * alignmentWeight;
        Vector2 cohesion   = CalculateCohesion(agent, neighbors)         * cohesionWeight;

        Vector2 steering = separation + alignment + cohesion;
        steering = Vector2.ClampMagnitude(steering, maxSteerForce);

        Vector2 newVelocity = agent.Rb.velocity + steering * Time.fixedDeltaTime;
        newVelocity = Vector2.ClampMagnitude(newVelocity, maxSpeed);

        agent.Move(newVelocity);
    }

    // ─── 규칙 1: 분리 ─────────────────────────────────────────────
    private Vector2 CalculateSeparation(FlockAgent agent, List<FlockAgent> close)
    {
        if (close.Count == 0) return Vector2.zero;

        Vector2 force = Vector2.zero;
        foreach (FlockAgent neighbor in close)
        {
            Vector2 diff = (Vector2)agent.transform.position - (Vector2)neighbor.transform.position;
            float   dist = diff.magnitude;
            if (dist > 0f)
                force += diff.normalized / dist;   // 거리에 반비례
        }
        return force / close.Count;
    }

    // ─── 규칙 2: 정렬 ─────────────────────────────────────────────
    private Vector2 CalculateAlignment(FlockAgent agent, List<FlockAgent> neighbors)
    {
        if (neighbors.Count == 0) return agent.Rb.velocity.normalized;

        Vector2 avgVelocity = Vector2.zero;
        foreach (FlockAgent neighbor in neighbors)
            avgVelocity += neighbor.Rb.velocity;

        avgVelocity /= neighbors.Count;
        return avgVelocity.normalized;
    }

    // ─── 규칙 3: 응집 ─────────────────────────────────────────────
    private Vector2 CalculateCohesion(FlockAgent agent, List<FlockAgent> neighbors)
    {
        if (neighbors.Count == 0) return Vector2.zero;

        Vector2 center = Vector2.zero;
        foreach (FlockAgent neighbor in neighbors)
            center += (Vector2)neighbor.transform.position;

        center /= neighbors.Count;
        Vector2 dirToCenter = center - (Vector2)agent.transform.position;
        return dirToCenter.normalized;
    }

    // ─── 이웃 탐색 (반경 기준) ────────────────────────────────────
    private List<FlockAgent> GetNeighbors(FlockAgent agent, float radius)
    {
        List<FlockAgent> result = new List<FlockAgent>();
        foreach (FlockAgent other in _agents)
        {
            if (other == agent) continue;
            if (Vector2.Distance(agent.transform.position, other.transform.position) <= radius)
                result.Add(other);
        }
        return result;
    }
}
```

> **성능 팁**: 에이전트 수가 20개 이상이면 `GetNeighbors`의 전체 순회(O(n²))가 부담. 공간 분할(Grid Spatial Partitioning)이나 `Physics2D.OverlapCircleAll`로 대체 가능.

#### 3-3. Boids를 플레이어 방향으로 유도하기

순수 Boids는 방향이 없다. 플레이어 추적과 결합:

```csharp
[Header("추적 가중치")]
[SerializeField] private float seekWeight = 1.5f;
[SerializeField] private Transform playerTarget;

private Vector2 CalculateSeek(FlockAgent agent)
{
    if (playerTarget == null) return Vector2.zero;
    Vector2 desired = ((Vector2)playerTarget.position - (Vector2)agent.transform.position).normalized;
    return desired * maxSpeed - agent.Rb.velocity;
}

// UpdateAgent 내에서 아래 추가:
// Vector2 seek = CalculateSeek(agent) * seekWeight;
// Vector2 steering = separation + alignment + cohesion + seek;
```

---

### 4. 상태머신 통합

`Enemy_AI_StateMachine.md`의 `EnemyBase`에 **Patrol 상태**를 추가하고 FOV로 Chase 전환을 처리한다.

#### 4-1. 상태 enum에 Patrol 추가

```csharp
public enum EnemyState
{
    Idle,
    Patrol,   // ← 추가
    Chase,
    Attack,
    Dead
}
```

#### 4-2. EnemyBase 확장 (Patrol + FOV 연결)

```csharp
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public class EnemyBase : MonoBehaviour
{
    // ── Inspector 설정 ───────────────────────────────────────────
    [SerializeField] protected float detectionRange   = 5f;
    [SerializeField] protected float attackRange      = 1.5f;
    [SerializeField] protected float moveSpeed        = 2f;
    [SerializeField] protected float viewAngle        = 90f;   // FOV 시야각
    [SerializeField] protected LayerMask playerMask;
    [SerializeField] protected LayerMask obstacleMask;

    // ── 내부 참조 ────────────────────────────────────────────────
    protected EnemyState    currentState = EnemyState.Patrol;
    protected Transform     player;
    protected Rigidbody2D   rb;
    protected EnemyFOV      fovSensor;
    protected EnemyPatrol   patrolBehavior;
    protected EnemyWander   wanderBehavior;

    protected virtual void Awake()
    {
        rb             = GetComponent<Rigidbody2D>();
        fovSensor      = GetComponent<EnemyFOV>();
        patrolBehavior = GetComponent<EnemyPatrol>();
        wanderBehavior = GetComponent<EnemyWander>();

        var go = GameObject.FindGameObjectWithTag("Player");
        if (go != null) player = go.transform;

        // FOV 검사를 0.15초마다 실행 (매 프레임 불필요)
        InvokeRepeating(nameof(CheckVision), 0f, 0.15f);
    }

    protected virtual void Update()
    {
        if (player == null) return;

        switch (currentState)
        {
            case EnemyState.Idle:    UpdateIdle();    break;
            case EnemyState.Patrol:  UpdatePatrol();  break;
            case EnemyState.Chase:   UpdateChase();   break;
            case EnemyState.Attack:  UpdateAttack();  break;
        }
    }

    // ── FOV 체크 (InvokeRepeating으로 호출) ──────────────────────
    private void CheckVision()
    {
        if (currentState == EnemyState.Dead) return;

        bool sees = fovSensor != null ? fovSensor.CanSeePlayer() : FallbackRangeCheck();

        if (sees && (currentState == EnemyState.Idle || currentState == EnemyState.Patrol))
            ChangeState(EnemyState.Chase);
    }

    // FOV 컴포넌트 없을 때 단순 거리 체크로 대체
    private bool FallbackRangeCheck()
        => Vector2.Distance(transform.position, player.position) <= detectionRange;

    // ── 상태별 Update ────────────────────────────────────────────

    protected virtual void UpdateIdle()
    {
        // 아무것도 하지 않음 — CheckVision이 Chase 전환 담당
    }

    protected virtual void UpdatePatrol()
    {
        // 웨이포인트 있으면 웨이포인트, 없으면 랜덤 배회
        if (patrolBehavior != null)
            patrolBehavior.UpdatePatrol();
        else if (wanderBehavior != null)
            wanderBehavior.UpdateWander();
    }

    protected virtual void UpdateChase()
    {
        float dist = Vector2.Distance(transform.position, player.position);

        if (dist > detectionRange * 1.3f)   // 1.3배 여유 → 히스테리시스(깜빡임 방지)
        {
            ChangeState(EnemyState.Patrol);
            return;
        }
        if (dist <= attackRange)
        {
            ChangeState(EnemyState.Attack);
            return;
        }

        Vector2 dir = ((Vector2)player.position - rb.position).normalized;
        rb.MovePosition(rb.position + dir * moveSpeed * Time.deltaTime);
        FaceDirection(dir);
    }

    protected virtual void UpdateAttack()
    {
        if (Vector2.Distance(transform.position, player.position) > attackRange)
            ChangeState(EnemyState.Chase);
        // 실제 공격 로직은 하위 클래스에서 override
    }

    // ── 상태 전환 ────────────────────────────────────────────────

    protected void ChangeState(EnemyState newState)
    {
        OnExitState(currentState);
        currentState = newState;
        OnEnterState(currentState);
    }

    protected virtual void OnEnterState(EnemyState state) { }
    protected virtual void OnExitState(EnemyState state)  { }

    // ── 유틸리티 ─────────────────────────────────────────────────

    protected void FaceDirection(Vector2 dir)
    {
        if (dir.sqrMagnitude < 0.01f) return;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
        transform.rotation = Quaternion.Euler(0f, 0f, angle);
    }

    // ── 디버그 Gizmos ────────────────────────────────────────────

    private void OnDrawGizmos()
    {
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(transform.position, detectionRange);
        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(transform.position, attackRange);
    }
}
```

#### 4-3. 상태 전환 흐름 요약

```
[Patrol / Idle]
    │   FOV 감지 성공 (CanSeePlayer == true)
    ▼
 [Chase]
    │   공격 범위 진입                   │   탐지 범위 벗어남(×1.3배)
    ▼                                    ▼
 [Attack]                           [Patrol]
    │   범위 벗어남
    ▼
 [Chase]
```

히스테리시스(감지 범위 × 1.3) 적용으로 Chase↔Patrol 경계에서 상태가 떨리는 현상(flickering)을 방지한다.

---

## OnionCat 적용 포인트

### 4-1. 약점 시스템 × FOV 조합

- **근접 전용 적(MeleeOnlyEnemy)**: 시야각 넓게(120°), 탐지 거리 짧게(4m) → 가까이 와야 반응, Player 1(Cat)이 유인 역할
- **원거리 전용 적(RangedOnlyEnemy)**: 시야각 좁게(60°), 탐지 거리 길게(8m) → Player 2(OnionCat)가 먼저 인지해서 대응

```
FOV 60° × 8m        FOV 120° × 4m
원거리 전용 적        근접 전용 적
[P2만 유효 데미지]   [P1만 유효 데미지]
```

### 4-2. 협동 강제 메커니즘

**군집 행동 활용 예시 — 협동 필수 상황 설계:**

| 씬 | 적 구성 | 요구 협동 |
|----|---------|-----------|
| 방 A | 근접 전용 4마리 Boids 군집 | P1이 근접, P2는 후방 커버 |
| 방 B | 원거리 전용 2마리 + 근접 전용 3마리 패트롤 | P1은 근접군 처리, P2는 원거리군 먼저 제거 |
| 보스방 | 원거리 전용 잡몹 군집이 보스 주위 플로킹 | P2가 군집 무력화, P1이 보스 근접 공격 |

### 4-3. 패트롤 적용 가이드

| 적 타입 | 패트롤 방식 | 이유 |
|---------|------------|------|
| 복도 경비병 | 웨이포인트 왕복 | 예측 가능한 패턴 → 기습 타이밍 학습 가능 |
| 룸 배회 잡몹 | EnemyWander (랜덤) | 절차 생성 룸에서 웨이포인트 배치 불필요 |
| 보스 잡몹 | FlockManager 연동 | 보스가 FlockManager.playerTarget을 공유 |

### 4-4. 구현 순서 권장 (초보자용 로드맵)

```
1단계  EnemyWander 만 구현   → 랜덤 배회 동작 확인
2단계  EnemyFOV 추가         → 시야각 감지 → Chase 전환
3단계  EnemyPatrol 추가      → 웨이포인트 순찰 교체 가능 구조
4단계  FlockManager 추가     → 특정 방에서만 활성화
5단계  WeaknessType 연동     → 약점 시스템 완성
```

### 4-5. CLAUDE.md 규칙 준수 체크리스트

- [x] `Awake()`에서 `GetComponent` 및 `FindGameObjectWithTag` 캐싱
- [x] `Update()` 내 `Find` / `FindObjectOfType` 없음
- [x] `[SerializeField] private` 사용 (Inspector 노출 변수)
- [x] `InvokeRepeating`으로 FOV 체크 주기 조절 (성능 최적화)
- [x] `EnemyBase` 상속 구조 → 교체 가능한 능력 설계 유지

---

## 참고 링크

- [Unity Discussions — Field of View using Raycasting](https://answers.unity.com/questions/15735/field-of-view-using-raycasting.html)
- [Unity Discussions — 2D FOV Cone Top-Down](https://forum.unity.com/threads/2d-top-down-field-of-view-cone.945119/)
- [Unity Discussions — How to create FOV for enemy AI Unity 2D](https://answers.unity.com/questions/1522104/how-to-create-a-field-of-view-for-enemy-ai-that-de.html)
- [Pav Creations — Finite State Machine for AI Enemy Controller in 2D](https://pavcreations.com/finite-state-machine-for-ai-enemy-controller-in-2d/)
- [GitHub Gist — Simple Unity Enemy Patrol over Waypoints (CodingDino)](https://gist.github.com/CodingDino/cdd5e4b319dc5be5d7c6b52c1b84ebee)
- [DevSourceHub — Flocking Algorithms in Unity: Simulating Swarm Behavior](https://devsourcehub.com/flocking-algorithms-in-unity-simulating-swarm-behavior/)
- [GitHub — RafaelKuebler/Flocking: 2D Flocking in Unity3D (Boids)](https://github.com/RafaelKuebler/Flocking)
- [GitHub — ZainGill45/2DBoidsSimulation: 2D Boids Simulation in Unity](https://github.com/ZainGill45/2DBoidsSimulation)
- [GitHub — blaz-cerpnjak/intelligent-opponent-shooter-game-unity (FSM + FOV)](https://github.com/blaz-cerpnjak/intelligent-opponent-shooter-game-unity)
- [GitHub — DevUrf/2D-Unity-Enemy-AI (Patrol, Chase, Attack, Evade)](https://github.com/DevUrf/2D-Unity-Enemy-AI)
- [GitHub — Inspiaaa/UnityHFSM: Hierarchical FSM for Unity](https://github.com/Inspiaaa/UnityHFSM)
- [Code Monkey — Simple Enemy AI (State Machine) YouTube](https://www.youtube.com/watch?v=db0KWYaWfeM)
- [Toptal — Unity AI Development: Finite-state Machine Tutorial](https://www.toptal.com/unity/unity-ai-development-finite-state-machine-tutorial)
- [Game Dev Beginner — State Machines in Unity](https://gamedevbeginner.com/state-machines-in-unity-how-and-when-to-use-them/)
