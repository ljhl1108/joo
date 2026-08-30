# 적 군집 행동 — Boids 알고리즘 (Unity 2D)

리서치 날짜: 2026-08-30

## 개요

Craig Reynolds(1986)가 고안한 Boids 알고리즘은 새 떼·물고기 무리처럼 자연스러운 군집 행동을 3가지 규칙만으로 재현한다. OnionCat에서 작은 파리형 적, 슬라임 무리처럼 집단으로 압박하는 적에 적용하면 P1(근접)과 P2(원거리)의 역할 분담을 자연스럽게 강제할 수 있다.

---

## Unity 구현 방법

### 핵심 3규칙

| 규칙 | 설명 | 연산 |
|------|------|------|
| **Separation** (분리) | 너무 가까운 이웃에게서 멀어진다 | 이웃 방향의 역방향 합산 |
| **Alignment** (정렬) | 이웃과 같은 방향으로 이동한다 | 이웃 속도 벡터 평균 |
| **Cohesion** (응집) | 이웃 무리의 중심으로 향한다 | 이웃 위치 평균 → 목표로 조향 |

### 단일 Boid 컴포넌트

```csharp
using UnityEngine;
using System.Collections.Generic;

public class BoidEnemy : MonoBehaviour
{
    [SerializeField] private float detectionRadius = 2.5f;
    [SerializeField] private float separationRadius = 1.0f;
    [SerializeField] private float maxSpeed = 3.0f;
    [SerializeField] private float turnSpeed = 4.0f;

    [SerializeField] private float separationWeight = 1.5f;
    [SerializeField] private float alignmentWeight  = 1.0f;
    [SerializeField] private float cohesionWeight   = 1.0f;
    [SerializeField] private float chaseWeight      = 2.0f;

    private Rigidbody2D rb;
    private Transform target;
    private static List<BoidEnemy> allBoids = new();

    private void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    private void OnEnable()  => allBoids.Add(this);
    private void OnDisable() => allBoids.Remove(this);

    public void SetTarget(Transform t) => target = t;

    private void FixedUpdate()
    {
        List<BoidEnemy> neighbors = GetNeighbors();

        Vector2 sep = CalcSeparation(neighbors);
        Vector2 ali = CalcAlignment(neighbors);
        Vector2 coh = CalcCohesion(neighbors);
        Vector2 chase = target != null
            ? ((Vector2)(target.position - transform.position)).normalized
            : Vector2.zero;

        Vector2 desired = sep  * separationWeight
                        + ali  * alignmentWeight
                        + coh  * cohesionWeight
                        + chase * chaseWeight;

        // 부드럽게 속도 전환
        rb.linearVelocity = Vector2.Lerp(rb.linearVelocity,
                                   desired.normalized * maxSpeed,
                                   Time.fixedDeltaTime * turnSpeed);
    }

    private List<BoidEnemy> GetNeighbors()
    {
        var result = new List<BoidEnemy>();
        float sqrRadius = detectionRadius * detectionRadius;
        foreach (var b in allBoids)
        {
            if (b == this) continue;
            if ((b.transform.position - transform.position).sqrMagnitude < sqrRadius)
                result.Add(b);
        }
        return result;
    }

    private Vector2 CalcSeparation(List<BoidEnemy> neighbors)
    {
        Vector2 steer = Vector2.zero;
        float sqrSep = separationRadius * separationRadius;
        foreach (var n in neighbors)
        {
            Vector2 diff = (Vector2)(transform.position - n.transform.position);
            if (diff.sqrMagnitude < sqrSep)
                steer += diff.normalized / diff.magnitude; // 가까울수록 강하게
        }
        return steer;
    }

    private Vector2 CalcAlignment(List<BoidEnemy> neighbors)
    {
        if (neighbors.Count == 0) return Vector2.zero;
        Vector2 avgVel = Vector2.zero;
        foreach (var n in neighbors) avgVel += n.rb.linearVelocity;
        return (avgVel / neighbors.Count).normalized;
    }

    private Vector2 CalcCohesion(List<BoidEnemy> neighbors)
    {
        if (neighbors.Count == 0) return Vector2.zero;
        Vector2 center = Vector2.zero;
        foreach (var n in neighbors) center += (Vector2)n.transform.position;
        center /= neighbors.Count;
        return ((center - (Vector2)transform.position)).normalized;
    }
}
```

### 성능 최적화: 공간 분할

적이 50마리 이상 되면 O(n²) 이웃 탐색이 병목이 된다.

```csharp
// Physics2D.OverlapCircleNonAlloc 사용 (GC 없음)
private readonly Collider2D[] nearbyBuffer = new Collider2D[16];

private List<BoidEnemy> GetNeighborsFast()
{
    int count = Physics2D.OverlapCircleNonAlloc(
        transform.position, detectionRadius, nearbyBuffer, boidLayer);
    var result = new List<BoidEnemy>(count);
    for (int i = 0; i < count; i++)
    {
        var b = nearbyBuffer[i].GetComponent<BoidEnemy>();
        if (b != null && b != this) result.Add(b);
    }
    return result;
}
```

### 업데이트 주기 분산 (LOD)

```csharp
// 화면 밖 적은 프레임마다 계산하지 않아도 됨
private int updateInterval => isOnScreen ? 1 : 3;
private int frameOffset;

private void Awake()
{
    frameOffset = GetInstanceID() % 3; // 개체마다 다른 오프셋
}

private void FixedUpdate()
{
    if (Time.frameCount % updateInterval != frameOffset) return;
    // ... 기존 계산
}
```

---

## OnionCat 적용 포인트

### 적 유형: 무리형 소형 적

- **파리 떼(Fly Swarm)**: 빠르게 날아다니며 군집, HP 낮음 → P2 원거리로 클리어 or P1 범위 슬래시
- **슬라임 덩어리**: 느리고 뭉쳐서 이동, HP 중간 → P1 근접 효과적, P2는 뒤쪽 유닛 정리
- **유령 군단**: 벽 통과, 분리 없이 겹쳐 이동 → 다른 패턴 필요, Cohesion만 켜기

### 역할 강제 설계 활용

```
무리형 적 → P1 슬래시로 한 번에 여럿 타격 (근접 우위)
사방 분산 시 → P2 산탄 발사 (원거리 우위)
```

근접형 P1이 무리 속에 들어가면 → 분산됨 → P2가 흩어진 개체 처리
→ 자연스럽게 두 플레이어가 역할 교환

### 가중치 조절 팁 (Inspector)

| 상황 | separationW | alignmentW | cohesionW | chaseW |
|------|-------------|------------|-----------|--------|
| 전투 전 배회 | 1.0 | 1.5 | 1.5 | 0.5 |
| 플레이어 추격 | 0.8 | 0.5 | 0.5 | 3.0 |
| 산개 도주 (HP < 30%) | 3.0 | 0.3 | 0.1 | -1.0 |

---

## 참고 링크

- Reynolds, Craig. "Flocks, Herds, and Schools" (원논문): https://www.red3d.com/cwr/boids/
- Unity 공식 예제 (Boids): https://github.com/SebLague/Boids
- Sebastian Lague Boids 튜토리얼: https://www.youtube.com/watch?v=bqtqltqcQhw
- Unity Physics2D.OverlapCircleNonAlloc: https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircleNonAlloc.html
