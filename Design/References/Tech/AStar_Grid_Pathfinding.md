# A* 그리드 기반 경로 탐색

리서치 날짜: 2026-08-03

## 개요

A*(A-star)는 출발점에서 목적지까지 **최단 경로**를 그리드 위에서 찾는 알고리즘. Unity 2D 탑다운 게임에서 NavMesh 없이 적 이동 경로를 계산할 때 핵심 선택지.

**NavMesh_2D vs A\* 그리드 선택 기준**:
| 상황 | 권장 |
|------|------|
| Tilemap 기반 방, 벽이 격자로 고정 | A\* 그리드 |
| 자유형 지형, 다각형 장애물 | NavMesh 2D |
| 적 수 10마리 이하 | 둘 다 무방 |
| 적 수 50+ | FlowField 고려 |

OnionCat은 Tilemap 기반 방 구조이므로 **A\* 그리드가 더 적합**.

---

## Unity 구현 방법

### 1단계: 그리드 노드 정의

```csharp
public class PathNode {
    public int x, y;
    public bool walkable;   // 벽이면 false
    
    // A* 비용
    public int gCost;       // 출발점 → 이 노드 실제 비용
    public int hCost;       // 이 노드 → 목적지 추정 비용 (휴리스틱)
    public int fCost => gCost + hCost;
    
    public PathNode parent; // 경로 역추적용
    
    public PathNode(int x, int y, bool walkable) {
        this.x = x;
        this.y = y;
        this.walkable = walkable;
    }
}
```

### 2단계: 그리드 생성 (Tilemap 연동)

```csharp
using UnityEngine;
using UnityEngine.Tilemaps;

public class PathGrid : MonoBehaviour {
    [SerializeField] private Tilemap wallTilemap;
    [SerializeField] private int width = 20;
    [SerializeField] private int height = 20;
    [SerializeField] private float cellSize = 1f;
    
    private PathNode[,] grid;
    private Vector3 originPosition;
    
    void Awake() {
        originPosition = transform.position;
        BuildGrid();
    }
    
    public void BuildGrid() {
        grid = new PathNode[width, height];
        for (int x = 0; x < width; x++) {
            for (int y = 0; y < height; y++) {
                Vector3Int cellPos = new Vector3Int(x, y, 0);
                bool isWall = wallTilemap.HasTile(cellPos);
                grid[x, y] = new PathNode(x, y, !isWall);
            }
        }
    }
    
    public PathNode GetNode(int x, int y) {
        if (x < 0 || y < 0 || x >= width || y >= height) return null;
        return grid[x, y];
    }
    
    // 월드 좌표 → 그리드 좌표 변환
    public PathNode GetNodeFromWorldPos(Vector3 worldPos) {
        int x = Mathf.FloorToInt((worldPos.x - originPosition.x) / cellSize);
        int y = Mathf.FloorToInt((worldPos.y - originPosition.y) / cellSize);
        return GetNode(x, y);
    }
    
    // 그리드 좌표 → 월드 좌표 중심 변환
    public Vector3 GetWorldPosition(int x, int y) {
        return new Vector3(x, y) * cellSize + originPosition + new Vector3(cellSize, cellSize) * 0.5f;
    }
}
```

### 3단계: A* 알고리즘 구현

```csharp
using System.Collections.Generic;
using UnityEngine;

public class AStarPathfinder : MonoBehaviour {
    [SerializeField] private PathGrid pathGrid;
    
    public List<Vector3> FindPath(Vector3 startWorld, Vector3 endWorld) {
        PathNode startNode = pathGrid.GetNodeFromWorldPos(startWorld);
        PathNode endNode   = pathGrid.GetNodeFromWorldPos(endWorld);
        
        if (startNode == null || endNode == null || !endNode.walkable) 
            return null;
        
        // 열린 목록(탐색 예정), 닫힌 목록(탐색 완료)
        List<PathNode> openList   = new List<PathNode> { startNode };
        HashSet<PathNode> closedSet = new HashSet<PathNode>();
        
        // 모든 노드 초기화
        for (int x = 0; x < pathGrid.Width; x++)
            for (int y = 0; y < pathGrid.Height; y++) {
                PathNode n = pathGrid.GetNode(x, y);
                n.gCost = int.MaxValue;
                n.parent = null;
            }
        
        startNode.gCost = 0;
        startNode.hCost = GetHeuristic(startNode, endNode);
        
        while (openList.Count > 0) {
            // fCost 최소 노드 선택
            PathNode current = GetLowestFCost(openList);
            
            if (current == endNode)
                return ReconstructPath(endNode);
            
            openList.Remove(current);
            closedSet.Add(current);
            
            foreach (PathNode neighbor in GetNeighbors(current)) {
                if (!neighbor.walkable || closedSet.Contains(neighbor)) continue;
                
                int tentativeG = current.gCost + GetDistance(current, neighbor);
                if (tentativeG < neighbor.gCost) {
                    neighbor.parent = current;
                    neighbor.gCost  = tentativeG;
                    neighbor.hCost  = GetHeuristic(neighbor, endNode);
                    if (!openList.Contains(neighbor)) openList.Add(neighbor);
                }
            }
        }
        return null; // 경로 없음
    }
    
    // 맨해튼 거리 휴리스틱 (대각선 허용 시 체비쇼프 거리 사용)
    private int GetHeuristic(PathNode a, PathNode b) {
        int dx = Mathf.Abs(a.x - b.x);
        int dy = Mathf.Abs(a.y - b.y);
        // 대각선 이동 허용: 10 * (dx + dy) + (14 - 20) * Mathf.Min(dx, dy)
        return 10 * (dx + dy); // 4방향만 허용 시
    }
    
    private int GetDistance(PathNode a, PathNode b) {
        int dx = Mathf.Abs(a.x - b.x);
        int dy = Mathf.Abs(a.y - b.y);
        if (dx == 1 && dy == 1) return 14; // 대각선 ≈ √2 * 10
        return 10;
    }
    
    private PathNode GetLowestFCost(List<PathNode> list) {
        PathNode lowest = list[0];
        foreach (var node in list)
            if (node.fCost < lowest.fCost || (node.fCost == lowest.fCost && node.hCost < lowest.hCost))
                lowest = node;
        return lowest;
    }
    
    private List<PathNode> GetNeighbors(PathNode node) {
        var neighbors = new List<PathNode>();
        int[] dx = { 0, 0, 1, -1 }; // 4방향 (대각선 추가 시 +4)
        int[] dy = { 1, -1, 0, 0 };
        for (int i = 0; i < 4; i++) {
            PathNode n = pathGrid.GetNode(node.x + dx[i], node.y + dy[i]);
            if (n != null) neighbors.Add(n);
        }
        return neighbors;
    }
    
    private List<Vector3> ReconstructPath(PathNode endNode) {
        var path = new List<Vector3>();
        PathNode current = endNode;
        while (current != null) {
            path.Add(pathGrid.GetWorldPosition(current.x, current.y));
            current = current.parent;
        }
        path.Reverse();
        return path;
    }
}
```

### 4단계: 적에게 경로 따라 이동 적용

```csharp
public class EnemyAStarMover : MonoBehaviour {
    [SerializeField] private AStarPathfinder pathfinder;
    [SerializeField] private float moveSpeed = 3f;
    [SerializeField] private float repathInterval = 0.5f; // 0.5초마다 재탐색
    
    private List<Vector3> currentPath;
    private int pathIndex;
    private Transform target;
    
    void Awake() {
        target = GameObject.FindWithTag("Player").transform; // Awake에서 캐싱
        InvokeRepeating(nameof(UpdatePath), 0f, repathInterval);
    }
    
    void UpdatePath() {
        currentPath = pathfinder.FindPath(transform.position, target.position);
        pathIndex = 0;
    }
    
    void Update() {
        if (currentPath == null || pathIndex >= currentPath.Count) return;
        
        Vector3 dir = (currentPath[pathIndex] - transform.position);
        if (dir.magnitude < 0.1f) {
            pathIndex++;
            return;
        }
        transform.position += dir.normalized * moveSpeed * Time.deltaTime;
    }
}
```

### 5단계: 성능 최적화 팁

```csharp
// 1. PriorityQueue 사용 (List<> 대신) — Unity 2022+
// System.Collections.Generic.PriorityQueue<PathNode, int>
// openList.Enqueue(node, node.fCost);

// 2. 경로 재탐색 빈도 제한 — 적 수가 많을수록 중요
// InvokeRepeating으로 0.3~0.5초 간격 탐색

// 3. 그리드 캐싱 — BuildGrid()는 방 생성 시 한 번만
// 벽 변경(문 열림 등) 시에만 부분 업데이트

// 4. Job System 연동 (고급) — 많은 적 동시 처리 시
// Unity.Jobs.IJob으로 A* 로직을 백그라운드 스레드 실행
```

---

## OnionCat 적용 포인트

### 방 구조와 A* 연동
- OnionCat 방은 Tilemap 기반 → `PathGrid`를 방 생성 시(`RoomSystem`) 자동 초기화
- 적 스폰 시 `AStarPathfinder` 컴포넌트 할당
- 문이 잠겨 있을 때 문 타일을 walkable=false로 설정 → 열릴 때 true로 변경 후 `BuildGrid()` 재호출

```csharp
// RoomDoor.cs에서
public void OpenDoor() {
    wallTilemap.SetTile(doorCellPos, null); // 문 타일 제거
    pathGrid.BuildGrid(); // 그리드 재생성
    isOpen = true;
}
```

### 근접형 vs 원거리형 적 이동 전략 분리
- **근접형 적** (Cat만 공격 가능): A* 경로로 Cat 위치 추적
- **원거리형 적** (Onion만 공격 가능): A* 경로로 최적 사거리 유지 (너무 가까우면 후퇴, 멀면 접근)

```csharp
// RangedEnemyMover.cs
void Update() {
    float dist = Vector3.Distance(transform.position, target.position);
    if (dist > optimalRange) {
        // 목표 쪽으로 A* 이동
    } else if (dist < minRange) {
        // A* 역방향 이동 (도망)
        currentPath = pathfinder.FindPath(transform.position, 
            transform.position + (transform.position - target.position));
    }
    // 최적 거리면 정지 후 사격
}
```

### 적 수에 따른 전략
- **적 5마리 이하** (OnionCat 방 크기 기준): 매 프레임 A* → 문제없음
- **적 10마리 이상**: `repathInterval = 0.5f` + 시간 분산(각 적 다른 offset으로 InvokeRepeating)
- **보스 적**: 단독이므로 매 프레임 재탐색해도 OK

---

## 참고 링크

- Sebastian Lague A\* 튜토리얼 (Unity): https://www.youtube.com/watch?v=-L-WgKMFuhE
- Unity 공식 Tilemap 문서: https://docs.unity3d.com/Manual/class-Tilemap.html
- A\* 알고리즘 시각화: https://www.redblobgames.com/pathfinding/a-star/introduction.html
- Red Blob Games (경로 탐색 최고 참고 자료): https://www.redblobgames.com/
- Unity PriorityQueue (2022+): https://learn.microsoft.com/ko-kr/dotnet/api/system.collections.generic.priorityqueue-2
