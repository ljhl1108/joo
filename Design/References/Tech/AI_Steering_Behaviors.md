# AI Steering Behaviors (자율 조향 행동 AI)

리서치 날짜: 2026-07-19

## 개요

Craig Reynolds(1999)가 제안한 **조향 행동(Steering Behaviors)** 은 게임 AI 이동을 자연스럽게 만드는 저비용 알고리즘 집합. 상태머신(State Machine)이 "언제 무엇을 할지" 결정한다면, 조향 행동은 "어떻게 움직일지"를 담당. 두 시스템은 보완 관계: StateMachine이 Chase 상태로 전환하면, Seek 조향 행동이 실제 이동 방향을 부드럽게 계산한다.

OnionCat에서 단순 `transform.position = target` 이동을 쓰면 적이 즉각 방향 전환해 로봇 같아 보임. 조향 행동을 적용하면 관성, 예측, 회피가 생겨 훨씬 살아있는 느낌.

---

## 핵심 조향 행동 종류

| 행동 | 설명 | OnionCat 활용 |
|------|------|--------------|
| **Seek** | 목표 위치로 돌진 | 기본 추적 적 |
| **Flee** | 위협에서 도망 | 겁쟁이 소환수, HP 낮은 적 |
| **Arrive** | 목표에 접근할수록 감속 | 보스 2페이즈 느린 정밀 접근 |
| **Wander** | 자연스러운 배회 | Idle 상태 적의 순찰 |
| **Pursuit** | 목표 미래 위치를 예측해 선제 이동 | 고속 추적 적 (고양이를 예측) |
| **Evade** | 추격자의 미래 위치 예측해 회피 | 원거리 적이 작물 투사체 회피 |
| **Separation** | 같은 편과 일정 거리 유지 (군집) | 무리 적 자연 분산 |

---

## Unity 구현 방법

### 기본 구조 — SteeringAgent 컴포넌트

```csharp
[RequireComponent(typeof(Rigidbody2D))]
public class SteeringAgent : MonoBehaviour
{
    [SerializeField] private float maxSpeed = 4f;
    [SerializeField] private float maxForce = 8f;
    [SerializeField] private float mass = 1f;

    private Rigidbody2D rb;
    private Vector2 velocity;

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        rb.gravityScale = 0f;
        rb.drag = 0f;
    }

    // 외부에서 원하는 조향력 전달 → 물리 적용
    public void ApplySteering(Vector2 steeringForce)
    {
        Vector2 acceleration = Vector2.ClampMagnitude(steeringForce, maxForce) / mass;
        velocity = Vector2.ClampMagnitude(velocity + acceleration * Time.fixedDeltaTime, maxSpeed);
        rb.linearVelocity = velocity;
    }

    public Vector2 Velocity => velocity;
    public float MaxSpeed => maxSpeed;
}
```

### 1. Seek — 목표를 향해 돌진

```csharp
public static Vector2 Seek(SteeringAgent agent, Vector2 targetPos)
{
    Vector2 desired = (targetPos - (Vector2)agent.transform.position).normalized * agent.MaxSpeed;
    return desired - agent.Velocity;
}
```

### 2. Flee — 위협에서 도망

```csharp
public static Vector2 Flee(SteeringAgent agent, Vector2 threatPos, float panicDistance = 5f)
{
    float dist = Vector2.Distance(agent.transform.position, threatPos);
    if (dist > panicDistance) return Vector2.zero;

    Vector2 desired = ((Vector2)agent.transform.position - threatPos).normalized * agent.MaxSpeed;
    return desired - agent.Velocity;
}
```

### 3. Arrive — 목표 근처에서 자동 감속

```csharp
public static Vector2 Arrive(SteeringAgent agent, Vector2 targetPos, float slowingRadius = 2f)
{
    Vector2 toTarget = targetPos - (Vector2)agent.transform.position;
    float dist = toTarget.magnitude;

    float desiredSpeed = dist < slowingRadius
        ? agent.MaxSpeed * (dist / slowingRadius)   // 감속 구간
        : agent.MaxSpeed;

    Vector2 desired = toTarget.normalized * desiredSpeed;
    return desired - agent.Velocity;
}
```

### 4. Pursuit — 미래 위치 예측 추격

```csharp
public static Vector2 Pursuit(SteeringAgent agent, Transform target, Rigidbody2D targetRb)
{
    Vector2 toTarget = (Vector2)target.position - (Vector2)agent.transform.position;
    float lookAheadTime = toTarget.magnitude / (agent.MaxSpeed + targetRb.linearVelocity.magnitude);

    Vector2 futurePos = (Vector2)target.position + targetRb.linearVelocity * lookAheadTime;
    return Seek(agent, futurePos);
}
```

### 5. Wander — 자연스러운 배회

```csharp
public class WanderBehavior : MonoBehaviour
{
    [SerializeField] private float wanderRadius = 1.5f;
    [SerializeField] private float wanderDistance = 3f;
    [SerializeField] private float wanderJitter = 0.5f;

    private Vector2 wanderTarget = Vector2.right;

    public Vector2 Wander(SteeringAgent agent)
    {
        // 목표 원 위에서 조금씩 무작위 이동
        wanderTarget += new Vector2(
            Random.Range(-1f, 1f) * wanderJitter,
            Random.Range(-1f, 1f) * wanderJitter
        );
        wanderTarget = wanderTarget.normalized * wanderRadius;

        // 에이전트 앞쪽에 원을 투영
        Vector2 circleCenter = agent.Velocity.normalized * wanderDistance;
        return (circleCenter + wanderTarget).normalized * agent.MaxSpeed - agent.Velocity;
    }
}
```

### 6. Separation — 군집 분산 (무리 자연 분산)

```csharp
public static Vector2 Separation(SteeringAgent agent, List<SteeringAgent> neighbors, float desiredDist = 1.5f)
{
    Vector2 force = Vector2.zero;
    foreach (var neighbor in neighbors)
    {
        if (neighbor == agent) continue;
        Vector2 away = (Vector2)agent.transform.position - (Vector2)neighbor.transform.position;
        float dist = away.magnitude;
        if (dist < desiredDist && dist > 0.001f)
            force += away.normalized / dist;  // 가까울수록 강하게 밀어냄
    }
    return force;
}
```

### 적 AI와 통합 — 상태머신에서 조향력 선택

```csharp
public class EnemyController : MonoBehaviour
{
    private SteeringAgent steeringAgent;
    private EnemyStateMachine stateMachine;
    private Transform playerTransform;

    private void FixedUpdate()
    {
        Vector2 steeringForce = stateMachine.CurrentState switch
        {
            EnemyState.Chase  => SteeringBehaviors.Pursuit(steeringAgent, playerTransform, playerRb),
            EnemyState.Flee   => SteeringBehaviors.Flee(steeringAgent, playerTransform.position),
            EnemyState.Patrol => wanderBehavior.Wander(steeringAgent),
            _                 => Vector2.zero
        };

        // 군집 분산은 항상 더함
        steeringForce += SteeringBehaviors.Separation(steeringAgent, nearbyEnemies);
        steeringAgent.ApplySteering(steeringForce);
    }
}
```

---

## OnionCat 적용 포인트

### 근접 전용 적 — Arrive + Separation
- 고양이 근처까지 돌진(Seek) → 슬래시 사거리(Arrive)에서 정확히 멈춤
- Separation으로 여러 적이 몰리지 않아 고양이가 숨 쉴 공간 생김
- 결과: "적이 사거리 딱 밖에서 압박하다 달려드는" 긴장감

### 원거리 전용 적 — Evade + 고정 사거리 유지
- 작물 투사체 예측 Evade: 투사체 방향을 보고 옆으로 스텝 밟음
- 적정 거리 유지: `if (dist < preferredRange) Flee / if (dist > preferredRange) Seek` 단순 로직과 조합

### 겁쟁이 소환수 — Flee
- HP 30% 이하가 되면 Flee 조향으로 전환, 고양이 근처를 도망 다니다 재정비
- 작물 원거리로 잡아야 하는 상황 자연스럽게 유도

### Wander를 Idle 상태에 적용
- 적이 플레이어를 감지하기 전 배회할 때 Wander 사용
- 정적으로 서 있는 것보다 훨씬 살아있는 느낌, 패트롤 경로 없이도 자연 이동

### 성능 고려사항
- Separation은 `Physics2D.OverlapCircleNonAlloc`으로 주변 적을 매 0.2초마다 캐싱, FixedUpdate마다 전체 탐색 금지
- Pursuit에서 `lookAheadTime`은 0.5초로 클램프해 과도한 예측 방지

---

## 참고 링크

- [Craig Reynolds 원본 논문 - Steering Behaviors for Autonomous Characters](https://www.red3d.com/cwr/steer/gdc99/)
- [GDC 1999 강연 자료 (원본)](https://www.red3d.com/cwr/papers/1999/gdc99steer.pdf)
- [Unity 조향 행동 튜토리얼 - Allegra Kuipers](https://gamedevelopment.tutsplus.com/series/understanding-steering-behaviors--gamedev-12732)
- [Game Programming Patterns - AI 챕터](https://gameprogrammingpatterns.com/)
- [Sebastian Lague - AI and Pathfinding (YouTube)](https://www.youtube.com/playlist?list=PLFt_AvWsXl0cq5Umv3pMC9SPnKjfp9eGW)
- [Unity Docs: Rigidbody2D.velocity](https://docs.unity3d.com/ScriptReference/Rigidbody2D-velocity.html)
