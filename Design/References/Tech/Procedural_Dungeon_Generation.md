# 절차적 던전 생성 알고리즘

리서치 날짜: 2026-06-25

## 개요

절차적 던전 생성은 런마다 다른 레이아웃을 만드는 로그라이크의 핵심 기술이다. 기존 `Room_System.md`가 "방 프리팹의 내부 구조와 문 연결 방식"을 다뤘다면, 이 문서는 **어떤 방들이 어떤 순서로 연결되는가 — 던전 맵 레이아웃 생성 알고리즘** 자체를 다룬다.

OnionCat에 필요한 것: 매번 다르지만 클리어 가능한, 보스방/상점/시작방 위치가 의미 있게 배치되는 방 배치 알고리즘.

## 주요 알고리즘 비교

| 알고리즘 | 난이도 | 연결성 보장 | 제어 가능성 | OnionCat 추천도 |
|--------|-------|-----------|-----------|--------------|
| BSP (이진 공간 분할) | 중 | 자동 보장 | 높음 | ★★★★★ |
| 난보행 (Drunkard's Walk) | 낮 | 자동 보장 | 낮음 | ★★★ |
| 들로네 삼각분할 + MST | 높음 | 알고리즘 보장 | 중간 | ★★★★ |

### 1. BSP — 이진 공간 분할 (권장)

공간을 재귀적으로 두 구역으로 나누고, 각 리프 노드에 방을 배치, 형제 노드 사이에 복도를 연결한다.

```csharp
public class BSPDungeonGenerator : MonoBehaviour
{
    [SerializeField] private int mapWidth = 80;
    [SerializeField] private int mapHeight = 60;
    [SerializeField] private int minRoomSize = 6;
    [SerializeField] private int maxRoomSize = 14;
    [SerializeField] private int totalRooms = 10;

    private List<RectInt> rooms = new();

    public List<RectInt> Generate()
    {
        rooms.Clear();
        var root = new BSPNode(new RectInt(0, 0, mapWidth, mapHeight));
        Split(root, totalRooms);
        PlaceRooms(root);
        ConnectRooms(root);
        return rooms;
    }

    private void Split(BSPNode node, int depth)
    {
        if (depth <= 0 || node.Rect.width < minRoomSize * 2 || node.Rect.height < minRoomSize * 2)
            return;

        bool splitHorizontal = Random.value > 0.5f;
        if (node.Rect.width > node.Rect.height * 1.25f) splitHorizontal = false;
        if (node.Rect.height > node.Rect.width * 1.25f) splitHorizontal = true;

        int splitPos;
        if (splitHorizontal)
        {
            splitPos = Random.Range(minRoomSize, node.Rect.height - minRoomSize);
            node.Left  = new BSPNode(new RectInt(node.Rect.x, node.Rect.y, node.Rect.width, splitPos));
            node.Right = new BSPNode(new RectInt(node.Rect.x, node.Rect.y + splitPos, node.Rect.width, node.Rect.height - splitPos));
        }
        else
        {
            splitPos = Random.Range(minRoomSize, node.Rect.width - minRoomSize);
            node.Left  = new BSPNode(new RectInt(node.Rect.x, node.Rect.y, splitPos, node.Rect.height));
            node.Right = new BSPNode(new RectInt(node.Rect.x + splitPos, node.Rect.y, node.Rect.width - splitPos, node.Rect.height));
        }

        Split(node.Left, depth - 1);
        Split(node.Right, depth - 1);
    }

    private void PlaceRooms(BSPNode node)
    {
        if (node.Left == null && node.Right == null)
        {
            int w = Random.Range(minRoomSize, Mathf.Min(maxRoomSize, node.Rect.width - 2));
            int h = Random.Range(minRoomSize, Mathf.Min(maxRoomSize, node.Rect.height - 2));
            int x = node.Rect.x + Random.Range(1, node.Rect.width - w - 1);
            int y = node.Rect.y + Random.Range(1, node.Rect.height - h - 1);
            node.Room = new RectInt(x, y, w, h);
            rooms.Add(node.Room);
            return;
        }
        if (node.Left  != null) PlaceRooms(node.Left);
        if (node.Right != null) PlaceRooms(node.Right);
    }

    private void ConnectRooms(BSPNode node)
    {
        if (node.Left == null || node.Right == null) return;
        ConnectRooms(node.Left);
        ConnectRooms(node.Right);

        // 두 서브트리의 방 중심을 L자 복도로 연결
        var leftCenter  = node.Left.GetCenterRoom();
        var rightCenter = node.Right.GetCenterRoom();
        CreateCorridor(leftCenter, rightCenter);
    }

    private void CreateCorridor(Vector2Int a, Vector2Int b)
    {
        // L자 복도: 수평 먼저, 그 다음 수직
        // 실제 구현에서는 Tilemap에 타일 배치
    }
}

public class BSPNode
{
    public RectInt Rect;
    public BSPNode Left, Right;
    public RectInt Room;

    public BSPNode(RectInt rect) { Rect = rect; }

    public Vector2Int GetCenterRoom()
    {
        if (Left == null && Right == null)
            return new Vector2Int(Room.x + Room.width / 2, Room.y + Room.height / 2);
        if (Left  != null) return Left.GetCenterRoom();
        return Right.GetCenterRoom();
    }
}
```

### 2. 난보행 (Drunkard's Walk)

구현이 가장 단순하지만 결과가 불규칙해 방 배치 제어가 어렵다. 타일 기반 동굴 생성에 적합.

```csharp
// 시작점에서 랜덤 방향으로 N번 걷는다
// 걸어간 타일을 바닥으로 설정
Vector2Int pos = startPos;
for (int i = 0; i < steps; i++)
{
    int dir = Random.Range(0, 4);
    pos += directions[dir];
    pos = Vector2Int.Clamp(pos, Vector2Int.zero, new Vector2Int(width-1, height-1));
    tileMap[pos.x, pos.y] = TileType.Floor;
}
```

### 3. 들로네 삼각분할 + MST (고급)

1. 방들을 랜덤 배치
2. 들로네 삼각분할로 인접 방 그래프 생성
3. 최소 신장 트리(MST)로 최소 연결 경로 추출
4. 일부 엣지 추가 (15~20%)하여 루프 생성

복잡하지만 Enter the Gungeon 스타일의 자연스러운 경로가 만들어진다.

## 실제 게임 사례

### Binding of Isaac — 격자 기반 배치

```
[START] - [ROOM] - [ROOM]
             |
          [ROOM] - [BOSS]
```

- 10×10 격자에서 BFS로 방 배치
- 시작방에서 일정 거리 이상에 보스방 자동 배치
- 격자의 인접 셀에만 문 생성 (상/하/좌/우)

### Enter the Gungeon — 하이브리드

- 손으로 디자인한 "흐름(flow)" 템플릿 + 랜덤 방 배치 조합
- 메인 경로 보장 + 선택적 사이드 방

### Dead Cells — 3계층 시스템

1. 고정된 큰 구조물 (항상 동일)
2. 템플릿 영역 (매번 다른 방 프리팹 배치)
3. 개념 그래프 (목표/보상 배치 규칙)

## OnionCat 적용 포인트

### 권장 접근: 격자 기반 BSP 하이브리드

OnionCat은 방 프리팹을 이미 사용하므로, 격자 좌표 기반으로 방 배치하는 Binding of Isaac 스타일이 가장 호환성이 높다.

```csharp
[System.Serializable]
public class DungeonGenerationSettings
{
    public int gridWidth = 8;
    public int gridHeight = 8;
    public int minRooms = 8;
    public int maxRooms = 14;
    public int minPathLength = 5;  // 시작 → 보스 최소 거리
}

public class GridDungeonGenerator : MonoBehaviour
{
    [SerializeField] private DungeonGenerationSettings settings;

    // 방 타입 배치 규칙
    // - 시작방: (0,0) 고정
    // - 보스방: 시작방에서 최대 거리 방
    // - 상점방: 경로 중간 (분기점 우선)
    // - 비밀방: 막다른 골목(Dead-end) 중 랜덤 1개
    // - 일반방: 나머지

    public DungeonMap Generate(int seed)
    {
        Random.InitState(seed);
        var map = new DungeonMap(settings.gridWidth, settings.gridHeight);

        // 1. BFS로 방 배치
        PlaceRoomsBFS(map);

        // 2. 보스방 위치 결정 (최대 거리)
        AssignBossRoom(map);

        // 3. 상점/비밀방 배치
        AssignSpecialRooms(map);

        // 4. 각 방에 프리팹 할당
        AssignRoomPrefabs(map);

        return map;
    }

    private void PlaceRoomsBFS(DungeonMap map)
    {
        var queue = new Queue<Vector2Int>();
        var start = new Vector2Int(settings.gridWidth / 2, settings.gridHeight / 2);
        queue.Enqueue(start);
        map.SetRoom(start, RoomType.Start);
        int placed = 1;
        int target = Random.Range(settings.minRooms, settings.maxRooms + 1);

        while (queue.Count > 0 && placed < target)
        {
            var current = queue.Dequeue();
            var neighbors = GetEmptyNeighbors(map, current);
            foreach (var n in neighbors)
            {
                if (placed >= target) break;
                if (Random.value > 0.5f) continue;
                map.SetRoom(n, RoomType.Normal);
                map.ConnectRooms(current, n);
                queue.Enqueue(n);
                placed++;
            }
        }
    }

    private void AssignBossRoom(DungeonMap map)
    {
        // 시작방에서 BFS로 거리 계산 후 최대 거리 방을 보스방으로
        var distances = map.BFS(map.StartRoom);
        var farthest = distances.OrderByDescending(kv => kv.Value)
                                .First(kv => kv.Value >= settings.minPathLength).Key;
        map.SetRoomType(farthest, RoomType.Boss);
    }
}
```

### 연결성 보장

```csharp
// Flood fill로 모든 방이 연결되어 있는지 검증
public bool ValidateConnectivity(DungeonMap map)
{
    var visited = new HashSet<Vector2Int>();
    var stack = new Stack<Vector2Int>();
    stack.Push(map.StartRoom);

    while (stack.Count > 0)
    {
        var curr = stack.Pop();
        if (visited.Contains(curr)) continue;
        visited.Add(curr);
        foreach (var neighbor in map.GetConnectedRooms(curr))
            if (!visited.Contains(neighbor))
                stack.Push(neighbor);
    }

    return visited.Count == map.RoomCount; // 모든 방 방문 시 연결 보장
}
```

### 특수방 배치 규칙 (OnionCat)

| 방 타입 | 배치 조건 |
|--------|---------|
| 시작방 | 격자 중심 고정 |
| 보스방 | 시작방에서 최소 5칸 거리, 막다른 골목 |
| 상점 | 경로 중간 분기점 (연결이 3개 이상인 방) |
| 비밀방 | 격자상 방이 없는 칸과 인접한 막다른 방 |
| 휴식방 | 보스방 바로 직전 방 |

### Room_System.md와의 통합

```csharp
// 생성된 DungeonMap을 기반으로 실제 씬에 방 프리팹 인스턴스화
public class DungeonInstantiator : MonoBehaviour
{
    [SerializeField] private RoomPrefabDatabase roomDatabase;
    [SerializeField] private float roomSpacing = 20f; // 월드 공간 방 간격

    public void InstantiateDungeon(DungeonMap map)
    {
        foreach (var roomData in map.AllRooms)
        {
            var prefab = roomDatabase.GetPrefab(roomData.Type);
            var worldPos = new Vector3(
                roomData.GridPos.x * roomSpacing,
                roomData.GridPos.y * roomSpacing, 0);
            var room = Instantiate(prefab, worldPos, Quaternion.identity);

            // 방향에 따른 문 활성화
            room.GetComponent<RoomController>().SetDoors(
                roomData.ConnectedDirections);
        }
    }
}
```

### 구현 단계 (권장 순서)

1. **격자 데이터 구조** — DungeonMap 클래스 (방 좌표 + 연결 정보)
2. **BFS 방 배치** — 시작방에서 BFS로 방 추가
3. **연결성 검증** — Flood fill로 고립 방 체크 후 재생성
4. **특수방 배치** — 보스/상점/비밀방 규칙 적용
5. **프리팹 인스턴스화** — Room_System.md의 프리팹 DB와 연동
6. **씨드 기반 재현** — `Random.InitState(seed)`로 동일 던전 재생성 가능

## 참고 링크

- [Procedural Dungeon Generation Tutorial - Vazgriz (GitHub)](https://github.com/vazgriz/DungeonGenerator) — Unity C# BSP 구현 예제
- [Binding of Isaac Level Generation 분석 - Reddit](https://www.reddit.com/r/bindingofisaac/comments/5jq3ms/how_does_the_games_room_generation_work/) — 격자 기반 BFS 설명
- [Procedural Generation Wiki](https://www.pcgwiki.au/wiki/Procedural_Dungeon_Generation) — 알고리즘 비교
- [Unity Learn - Procedural Cave Generation](https://learn.unity.com/project/procedural-cave-generation-tutorial) — Tilemap 기반 구현
- [Red Blob Games - BSP 설명](https://www.redblobgames.com/) — 비주얼 설명
- [Dungeon Generation Techniques - BorisTheBrave](https://www.boristhebrave.com/2019/07/28/dungeon-generation-in-binding-of-isaac/) — Isaac 구체적 분석
- [Procedural Content Generation in Games (무료 교재)](http://pcgbook.com/) — 챕터 3: Dungeon Generation
