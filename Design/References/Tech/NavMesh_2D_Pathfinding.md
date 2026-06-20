# NavMesh & 2D 경로탐색 시스템

리서치 날짜: 2026-06-20

## 개요

2D 탑다운 게임에서 적이 장애물을 피해 플레이어를 추적하려면 **경로탐색(Pathfinding)** 이 필요하다. Unity의 NavMesh는 3D 전용이라 2D에서는 별도 전략이 필요하다. OnionCat의 적 AI가 방 내 장애물(벽, 기둥, 상자)을 피해 두 플레이어를 추적할 수 있어야 하므로, 올바른 경로탐색 방법 선택이 중요하다.

---

## Unity 구현 방법

### 방법 1: 직선 추적 (최단, 가장 쉬움)

장애물이 없거나 단순한 방에서 사용. 기존 Enemy_AI_StateMachine에서 이미 구현.

```csharp
// EnemyMovement.cs - 기본 직선 추적
void ChaseTarget(Transform target)
{
    Vector2 dir = (target.position - transform.position).normalized;
    rb.MovePosition(rb.position + dir * moveSpeed * Time.fixedDeltaTime);
}
```

**단점**: 장애물에 끼임. 벽이 있는 방에서 적이 막힘.

---

### 방법 2: A* Pathfinding Project (추천 — 무료/유료)

Aron Granberg의 **A* Pathfinding Project** 플러그인. 2D 그리드 경로탐색을 Unity에서 가장 쉽게 구현.

**설치**: Asset Store에서 "A* Pathfinding Project" 검색 → 무료 버전 충분

#### 설정 단계

1. **AstarPath 컴포넌트 추가** (씬에 빈 오브젝트 생성 → AstarPath 컴포넌트 부착)
2. **Grid Graph 추가**: Inspector → A* Inspector → Add New Graph → Grid Graph
   - Width/Depth: 방 크기에 맞게 (예: 40×40)
   - Node Size: 타일 크기와 동일 (예: 1.0)
   - Collision Testing: 장애물 레이어 설정 (Layer: Wall)
3. **그래프 스캔**: Play Mode 진입 or Inspector에서 Scan 버튼

```csharp
using Pathfinding;

public class EnemyAI : MonoBehaviour
{
    private Seeker seeker;
    private Path currentPath;
    private int currentWaypoint = 0;
    private float repathRate = 0.5f; // 0.5초마다 경로 재계산

    [SerializeField] private float moveSpeed = 3f;
    [SerializeField] private float nextWaypointDistance = 0.5f;

    private void Awake()
    {
        seeker = GetComponent<Seeker>();
    }

    private void Start()
    {
        InvokeRepeating(nameof(RecalculatePath), 0f, repathRate);
    }

    private void RecalculatePath()
    {
        if (target == null) return;
        seeker.StartPath(transform.position, target.position, OnPathComplete);
    }

    private void OnPathComplete(Path p)
    {
        if (!p.error)
        {
            currentPath = p;
            currentWaypoint = 0;
        }
    }

    private void FixedUpdate()
    {
        if (currentPath == null) return;
        if (currentWaypoint >= currentPath.vectorPath.Count) return;

        Vector2 dir = ((Vector2)currentPath.vectorPath[currentWaypoint] - rb.position).normalized;
        rb.MovePosition(rb.position + dir * moveSpeed * Time.fixedDeltaTime);

        float dist = Vector2.Distance(rb.position, currentPath.vectorPath[currentWaypoint]);
        if (dist < nextWaypointDistance) currentWaypoint++;
    }
}
```

#### 동적 장애물 처리

방에 움직이는 장애물(닫히는 문 등)이 있을 때:
```csharp
// 장애물 오브젝트에 부착
using Pathfinding;

public class DynamicObstacle : MonoBehaviour
{
    private void OnEnable()  => AstarPath.active?.UpdateGraphs(GetComponent<Collider2D>().bounds);
    private void OnDisable() => AstarPath.active?.UpdateGraphs(GetComponent<Collider2D>().bounds);
}
```

---

### 방법 3: Unity NavMesh + NavMeshSurface 2D 트릭

Unity 공식 NavMesh를 2D에서 사용하는 트릭. **권장하지 않음** — 복잡하고 유지보수 어려움.

- NavMeshSurface를 XY 평면으로 회전해서 2D처럼 동작시키는 방식
- 설정이 까다롭고 픽셀아트 레이아웃과 안 맞는 경우 많음
- **대신 방법 2 (A* PP) 사용 권장**

---

### 방법 4: 플로우 필드(Flow Field) 경로탐색

많은 적이 동시에 같은 목표를 추적할 때 최적. 각 적이 개별적으로 경로 계산 대신, 전체 맵에 "흐름 방향" 벡터 필드를 한 번 계산하고 모든 적이 공유.

```csharp
// FlowFieldPathfinder.cs (개념 구현)
public class FlowFieldPathfinder : MonoBehaviour
{
    private Vector2[,] flowField; // 각 셀의 이동 방향
    private int width, height;

    public void BuildFlowField(Vector2Int targetCell)
    {
        // BFS로 목표에서 역방향으로 거리 계산
        var distances = new int[width, height];
        var queue = new Queue<Vector2Int>();
        queue.Enqueue(targetCell);
        distances[targetCell.x, targetCell.y] = 0;

        while (queue.Count > 0)
        {
            var cell = queue.Dequeue();
            foreach (var neighbor in GetNeighbors(cell))
            {
                if (!IsWall(neighbor) && distances[neighbor.x, neighbor.y] == 0)
                {
                    distances[neighbor.x, neighbor.y] = distances[cell.x, cell.y] + 1;
                    queue.Enqueue(neighbor);
                }
            }
        }

        // 각 셀에서 가장 짧은 이웃 방향으로 flowField 설정
        for (int x = 0; x < width; x++)
            for (int y = 0; y < height; y++)
                flowField[x, y] = GetBestDirection(x, y, distances);
    }
}
```

**OnionCat 적합성**: 방 단위로 적이 많지 않으므로 방법 2(A* PP)로 충분.

---

### 방법 5: 레이캐스트 장애물 회피 (간단한 중간 방법)

A* PP 없이 간단하게 장애물을 피하는 방법. 직선 경로가 막혔을 때 우회.

```csharp
// RaycastSteering.cs
void ChaseWithObstacleAvoidance(Transform target)
{
    Vector2 toTarget = (target.position - transform.position).normalized;
    
    // 직선 경로 확인
    RaycastHit2D hit = Physics2D.Raycast(transform.position, toTarget, 2f, wallLayer);
    
    if (hit.collider == null)
    {
        // 장애물 없음 → 직선 이동
        rb.MovePosition(rb.position + toTarget * moveSpeed * Time.fixedDeltaTime);
    }
    else
    {
        // 장애물 있음 → 법선 벡터로 우회
        Vector2 avoidDir = Vector2.Perpendicular(hit.normal);
        rb.MovePosition(rb.position + avoidDir * moveSpeed * Time.fixedDeltaTime);
    }
}
```

---

## OnionCat 적용 포인트

### 권장 구현 전략 (단계별)

**1단계 (프로토타입)**: 직선 추적만 사용 → 방을 열린 공간으로 설계해서 문제 최소화  
**2단계 (알파)**: A* Pathfinding Project 도입 → 방 내 장애물 있는 레이아웃 지원  
**3단계 (폴리싱)**: 적 유형별 경로탐색 차별화 (느린 적 = 정확한 경로, 빠른 적 = 대략적 추적)

### 두 플레이어 추적 처리

OnionCat은 P1/P2가 같은 몸 위치를 공유하므로 단일 추적 목표로 처리:
```csharp
// EnemyAI.cs
private Transform GetTarget()
{
    // 항상 같은 Transform (온어캣 본체)
    return PlayerController.Instance.transform;
}
```

### 방 그래프 동적 생성

방 진입 시 AstarPath 그래프를 해당 방 레이아웃으로 재스캔:
```csharp
// RoomManager.cs
public void OnRoomEntered(Room room)
{
    // 방 활성화 후 경로탐색 그래프 재스캔
    AstarPath.active.Scan();
}
```

### 적 유형별 경로탐색 전략

| 적 유형 | 추적 방식 | 이유 |
|---------|-----------|------|
| 일반 슬라임 | A* (정확) | 느리고 예측 가능해야 함 |
| 돌진형 | 직선 + 레이캐스트 | 빠른 돌진이라 정확한 경로 불필요 |
| 원거리 궁수 | A* (거리 유지) | 특정 거리 이상 유지하면서 이동 |
| 보스 | 커스텀 패턴 | 경로탐색 없이 페이즈별 이동 패턴 |

---

## 참고 링크

- [A* Pathfinding Project 공식 문서](https://arongranberg.com/astar/documentation/)
- [A* Pathfinding Project Asset Store (무료)](https://assetstore.unity.com/packages/tools/ai/a-pathfinding-project-87397)
- [Unity 공식 NavMesh 2D 사용 가이드](https://docs.unity3d.com/Manual/nav-HowTos.html)
- [Flow Field Pathfinding 설명 (YouTube)](https://www.youtube.com/results?search_query=flow+field+pathfinding+unity+2d)
- [2D 탑다운 게임 경로탐색 비교 (Unity Forum)](https://discussions.unity.com/t/2d-pathfinding-options/791847)
- [Sebastian Lague A* 경로탐색 시리즈 (YouTube)](https://www.youtube.com/playlist?list=PLFt_AvWsXl0cq5Umv3pMC9SPnKjfp9eGW)
