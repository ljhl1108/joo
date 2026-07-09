# FlowField Pathfinding (플로우필드 경로탐색)

리서치 날짜: 2026-07-09

## 개요

플로우필드(Flow Field)는 **맵 전체에 방향 벡터를 미리 계산**해두고, 모든 적이 그 벡터를 따라 목표에 접근하는 경로탐색 알고리즘이다.

### 왜 중요한가?
- A* 알고리즘: 적 1마리당 경로 계산 → 적 100마리면 CPU 100배
- FlowField: 목표 1개당 벡터필드 1번 계산 → 적 1000마리가 같은 필드를 참조

| 방식 | 적 10마리 | 적 100마리 | 특징 |
|------|----------|-----------|------|
| A* | 보통 | 느림 | 개별 경로 |
| NavMesh | 보통 | 보통 | Unity 내장 (3D) |
| FlowField | 보통 | **빠름** | 군집 이동에 최적 |

**OnionCat에서 중요한 이유**: 방 하나에 20~30마리 적이 동시에 플레이어를 쫓아오는 상황에서 A*는 프레임 드롭을 유발할 수 있음.

---

## Unity 구현 방법

### 1. 기본 구조

```csharp
// 그리드 셀 하나의 데이터
public struct FlowFieldCell
{
    public Vector2Int gridPos;
    public float bestCost;      // 목표까지의 비용
    public Vector2 bestDirection; // 이동 방향 벡터
}
```

### 2. 단계별 구현

#### Step 1: 코스트 맵(Cost Map) 생성
각 셀의 통과 비용 설정 (벽=255, 일반=1)

```csharp
public class FlowField
{
    public FlowFieldCell[,] grid;
    private int width, height;
    private float cellSize;

    public void CreateCostField()
    {
        // 각 셀마다 충돌체 검사
        foreach (var cell in grid)
        {
            Collider2D[] obstacles = Physics2D.OverlapBoxAll(
                GetWorldPos(cell.gridPos), 
                Vector2.one * cellSize * 0.9f, 
                0f, 
                LayerMask.GetMask("Wall"));
            
            cell.cost = obstacles.Length > 0 ? byte.MaxValue : 1;
        }
    }
```

#### Step 2: 통합 비용(Integration Field) 계산
목표 지점에서 BFS로 전파

```csharp
    public void CreateIntegrationField(Vector2Int targetCell)
    {
        // 목표 셀 초기화
        grid[targetCell.x, targetCell.y].bestCost = 0;
        
        Queue<Vector2Int> openList = new Queue<Vector2Int>();
        openList.Enqueue(targetCell);
        
        while (openList.Count > 0)
        {
            Vector2Int current = openList.Dequeue();
            float currentCost = grid[current.x, current.y].bestCost;
            
            // 4방향 이웃 탐색
            foreach (Vector2Int neighbor in GetNeighbors(current))
            {
                float newCost = currentCost + grid[neighbor.x, neighbor.y].cost;
                if (newCost < grid[neighbor.x, neighbor.y].bestCost)
                {
                    grid[neighbor.x, neighbor.y].bestCost = newCost;
                    openList.Enqueue(neighbor);
                }
            }
        }
    }
```

#### Step 3: 방향 필드(Direction Field) 생성
각 셀에서 가장 비용 낮은 이웃 방향 설정

```csharp
    public void CreateFlowField()
    {
        foreach (var cell in grid)
        {
            Vector2Int bestNeighborPos = cell.gridPos;
            float bestCost = cell.bestCost;
            
            foreach (Vector2Int neighbor in GetNeighbors(cell.gridPos))
            {
                if (grid[neighbor.x, neighbor.y].bestCost < bestCost)
                {
                    bestCost = grid[neighbor.x, neighbor.y].bestCost;
                    bestNeighborPos = neighbor;
                }
            }
            
            cell.bestDirection = (Vector2)(bestNeighborPos - cell.gridPos);
        }
    }
}
```

#### Step 4: 적이 필드 샘플링

```csharp
// EnemyController.cs
public class EnemyFlowFieldMover : MonoBehaviour
{
    private FlowField currentField;

    void Update()
    {
        if (currentField == null) return;
        
        Vector2Int myCell = currentField.WorldToGrid(transform.position);
        Vector2 moveDir = currentField.grid[myCell.x, myCell.y].bestDirection;
        
        rb.linearVelocity = moveDir.normalized * moveSpeed;
    }
}
```

### 3. 성능 최적화 팁

```csharp
// 플레이어가 이동할 때만 필드 재계산 (매 프레임 불필요)
void Update()
{
    Vector2Int playerCell = flowField.WorldToGrid(player.position);
    if (playerCell != lastPlayerCell)
    {
        flowField.CreateIntegrationField(playerCell);
        flowField.CreateFlowField();
        lastPlayerCell = playerCell;
    }
}
```

### 4. 그리드 사이즈 권장

| 방 크기 | 셀 크기 | 그리드 해상도 |
|--------|--------|------------|
| 16×9 타일 | 1타일 | 16×9 = 144셀 |
| 32×18 타일 | 1타일 | 32×18 = 576셀 |

OnionCat 방 크기 기준: 20×12 타일 정도 → 240셀, 매우 가볍게 계산 가능.

---

## OnionCat 적용 포인트

### 언제 FlowField가 필요한가?
- 방당 **적 15마리 이상** 동시 출현 시 A* 대비 확실한 이점
- 군집 이동 적(슬라임 무리, 잡몹 웨이브) 구현 시
- 플레이어 근처에서 적들이 "뭉치는" 느낌 방지 (분산 이동 효과)

### OnionCat 아키텍처 통합
```csharp
// RoomManager가 방 진입 시 FlowField 생성
public class RoomManager : MonoBehaviour
{
    private FlowField roomFlowField;
    
    void OnPlayerEnterRoom()
    {
        roomFlowField = new FlowField(roomWidth, roomHeight, cellSize);
        roomFlowField.CreateCostField(); // 벽 위치 스캔
        // 이후 플레이어 위치 변화마다 Integration+Direction 재계산
    }
}
```

### 주의사항
- A*와 병행: 보스나 특수 적은 개별 A* 사용, 잡몹은 FlowField 사용
- 방 전환 시 반드시 필드 초기화/재생성
- 8방향(대각선 포함) vs 4방향: OnionCat 픽셀아트 환경에서는 8방향 권장

---

## 참고 링크

- The Coding Train — Flow Field: https://thecodingtrain.com/challenges/24-perlin-noise-flow-field
- Unity FlowField Tutorial (TaroDev): https://www.youtube.com/watch?v=zr6ObNVgytk
- 알고리즘 이론: https://leifnode.com/2013/12/flow-field-pathfinding/
- GitHub 구현체 참고: https://github.com/OnurErtunc/Unity2D-FlowField
- 관련 파일: [Enemy_AI_StateMachine.md](Enemy_AI_StateMachine.md), [NavMesh_2D_Pathfinding.md](NavMesh_2D_Pathfinding.md)
