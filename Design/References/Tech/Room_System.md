# 방 시스템 (Room System)

## 개요

절차적 방 배치(Procedural Room Layout)는 로그라이크의 핵심. 매 런마다 다른 던전을 만들면서도 항상 클리어 가능하고, 플레이 흐름이 자연스럽게 이어지도록 설계하는 기술이다. OnionCat에서는 2인 협력의 "근접/원거리 취약 적 배치"가 방마다 의미 있게 달라야 하므로 방 시스템 설계가 특히 중요하다.

---

## Unity 구현 방법

### 1단계: 방 프리팹 구조 설계

각 방은 독립적인 Unity 프리팹으로 제작한다.

```
Assets/Prefabs/Rooms/
  ├── Room_Combat_01.prefab   (기본 전투방)
  ├── Room_Combat_02.prefab
  ├── Room_Elite.prefab       (정예 적 방)
  ├── Room_Treasure.prefab    (보물방)
  ├── Room_Shop.prefab        (상점방)
  ├── Room_Boss.prefab        (보스방)
  └── Room_Start.prefab       (시작방)
```

각 프리팹 내부 구조:
```
Room_Combat_01 (GameObject)
  ├── Walls         (타일맵 레이어 — 벽)
  ├── Floor         (타일맵 레이어 — 바닥)
  ├── Doors         (4방향 문 오브젝트)
  │   ├── Door_North
  │   ├── Door_South
  │   ├── Door_East
  │   └── Door_West
  ├── EnemySpawnPoints  (적 스폰 위치 마커)
  └── RoomData      (RoomDataComponent 스크립트)
```

### 2단계: RoomData 컴포넌트

```csharp
public enum RoomType { Start, Combat, Elite, Treasure, Shop, Boss }

public class RoomData : MonoBehaviour
{
    [SerializeField] public RoomType roomType;
    [SerializeField] public Transform[] enemySpawnPoints;
    [SerializeField] public Door[] doors; // 4방향
    
    // 어떤 방향으로 통로가 있는지
    [SerializeField] public bool hasNorth, hasSouth, hasEast, hasWest;
    
    public bool IsCleared { get; private set; }
    
    public void OnRoomCleared()
    {
        IsCleared = true;
        foreach (var door in doors)
            door.Open();
    }
}
```

### 3단계: 던전 레이아웃 생성기 (Spelunky 방식)

```csharp
public class DungeonGenerator : MonoBehaviour
{
    [SerializeField] private int gridWidth = 4;
    [SerializeField] private int gridHeight = 4;
    [SerializeField] private float roomSize = 20f; // 월드 단위

    // 그리드 좌표 → 방 타입
    private RoomType[,] grid;
    private List<Vector2Int> criticalPath;

    void Start()
    {
        GenerateDungeon();
    }

    void GenerateDungeon()
    {
        grid = new RoomType[gridWidth, gridHeight];
        criticalPath = new List<Vector2Int>();

        // 1. 반드시 클리어 가능한 경로 생성 (왼쪽 위 → 오른쪽 아래)
        BuildCriticalPath();

        // 2. 나머지 방 채우기
        FillRemainingRooms();

        // 3. 실제 방 프리팹 배치
        SpawnRooms();
    }

    void BuildCriticalPath()
    {
        // 시작: (0, 0), 목표: (gridWidth-1, gridHeight-1)
        Vector2Int current = Vector2Int.zero;
        criticalPath.Add(current);
        grid[0, 0] = RoomType.Start;

        while (current != new Vector2Int(gridWidth - 1, gridHeight - 1))
        {
            // 오른쪽 또는 아래 방향으로만 이동 (항상 진행 보장)
            bool canGoRight = current.x < gridWidth - 1;
            bool canGoDown = current.y < gridHeight - 1;

            if (canGoRight && canGoDown)
                current += (Random.value > 0.5f) ? Vector2Int.right : Vector2Int.down;
            else if (canGoRight)
                current += Vector2Int.right;
            else
                current += Vector2Int.down;

            criticalPath.Add(current);
            grid[current.x, current.y] = RoomType.Combat;
        }

        // 마지막 방을 보스방으로
        grid[gridWidth - 1, gridHeight - 1] = RoomType.Boss;
    }

    void FillRemainingRooms()
    {
        for (int x = 0; x < gridWidth; x++)
        {
            for (int y = 0; y < gridHeight; y++)
            {
                if (grid[x, y] == RoomType.Start) continue;
                if (criticalPath.Contains(new Vector2Int(x, y))) continue;

                // 가중치 랜덤으로 방 타입 결정
                float roll = Random.value;
                if (roll < 0.1f)       grid[x, y] = RoomType.Treasure;
                else if (roll < 0.2f)  grid[x, y] = RoomType.Shop;
                else if (roll < 0.3f)  grid[x, y] = RoomType.Elite;
                else                   grid[x, y] = RoomType.Combat;
            }
        }
    }
}
```

### 4단계: 방 간 연결 (문 로직)

```csharp
void SpawnRooms()
{
    for (int x = 0; x < gridWidth; x++)
    {
        for (int y = 0; y < gridHeight; y++)
        {
            if (grid[x, y] == default) continue;

            Vector3 worldPos = new Vector3(x * roomSize, -y * roomSize, 0);
            GameObject roomPrefab = GetRoomPrefab(grid[x, y]);
            GameObject roomObj = Instantiate(roomPrefab, worldPos, Quaternion.identity);
            RoomData roomData = roomObj.GetComponent<RoomData>();

            // 인접 방이 있는 방향의 문만 활성화
            bool openNorth = y > 0 && grid[x, y - 1] != default;
            bool openSouth = y < gridHeight - 1 && grid[x, y + 1] != default;
            bool openEast  = x < gridWidth - 1  && grid[x + 1, y] != default;
            bool openWest  = x > 0 && grid[x - 1, y] != default;

            roomData.SetActiveDoors(openNorth, openSouth, openEast, openWest);
        }
    }
}
```

### 5단계: 방 전환 — 카메라 & 플레이어 이동

```csharp
public class DoorTrigger : MonoBehaviour
{
    [SerializeField] private Direction direction;
    [SerializeField] private Vector2Int targetRoomCoord;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (!other.CompareTag("Player")) return;
        if (!currentRoom.IsCleared) return; // 클리어 전 이동 불가

        DungeonManager.Instance.TransitionToRoom(targetRoomCoord, direction);
    }
}
```

---

## OnionCat 적용 포인트

### 1. 방 타입별 "의무 적 구성" 규칙
```
OnionCat 방 설계 원칙:
- 전투방은 반드시 근접 약점 적 + 원거리 약점 적을 함께 배치
  → 두 플레이어가 모두 활약해야 클리어 가능
- 정예방은 특정 타입 적만 배치해도 OK (전략적 선택지)
- 보스방: 2페이즈 구성 — 1페이즈 원거리 약점, 2페이즈 근접 약점
```

### 2. EnemySpawnPoint에 태그 달기
```csharp
public enum SpawnPointType { Any, MeleeWeak, RangedWeak }

public class EnemySpawnPoint : MonoBehaviour
{
    [SerializeField] public SpawnPointType type;
    // DungeonGenerator가 방 생성 시 타입에 맞는 적 스폰
}
```

### 3. 미니맵 연동
- 그리드 배열을 그대로 미니맵 UI에 활용
- 방문한 방: 밝게, 미방문: 어둡게, 현재 방: 깜빡임

### 4. 방 클리어 조건 — 모든 적 처치
```csharp
void CheckRoomClear()
{
    int aliveEnemies = FindObjectsOfType<Enemy>()
        .Count(e => e.IsAlive);
    if (aliveEnemies == 0)
        roomData.OnRoomCleared();
}
```

---

## 참고 링크

- Spelunky 레벨 생성 알고리즘: https://tinysubversions.com/spelunkyGen/
- Unity 2D 타일맵 공식 문서: https://docs.unity3d.com/Manual/class-Tilemap.html
- 절차적 던전 생성 (RogueBasin): http://www.roguebasin.com/index.php/Dungeon-Building_Algorithm
- Unity 프리팹 시스템: https://docs.unity3d.com/Manual/Prefabs.html
- 게임메이커 로그라이크 방 생성 튜토리얼: https://www.youtube.com/watch?v=gHlmZsiGC8o
