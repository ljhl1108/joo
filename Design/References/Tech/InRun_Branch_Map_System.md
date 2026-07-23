# 런 내 경로 선택 맵 시스템 (In-Run Branch Map System)

리서치 날짜: 2026-07-23

## 개요

런 진행 중 플레이어가 다음에 갈 방/구간을 선택하는 **분기 경로 맵(Node Map)** 시스템. Slay the Spire의 분기 트리, Hades의 방 간 선택, Dead Cells의 경로 선택 등에서 공통으로 사용되는 로그라이크 핵심 구조다. 단순히 방을 랜덤으로 이어 붙이는 것이 아니라 **플레이어가 다음 경험을 선택할 수 있게 함으로써 플레이어 에이전시(주도권)를 부여하고 런마다 다른 전략을 유도**한다.

---

## Unity 구현 방법

### 전체 구조 개요

```
[RoomNodeMapData] (ScriptableObject)
    └─ List<NodeRow>
        └─ List<RoomNodeData> (각 노드: 방 유형, 보상, 연결 정보)

[MapGenerator]
    └─ RoomNodeMapData를 기반으로 UI 노드 생성

[MapUI] (Canvas)
    ├─ NodeButton (각 방 선택 버튼)
    └─ ConnectionLine (노드 간 연결선 UI)

[MapManager] (싱글톤)
    └─ 현재 위치 추적, 선택 이벤트 처리, 씬 로드 연결
```

### 1. 노드 데이터 정의

```csharp
// RoomNodeType.cs
public enum RoomNodeType
{
    Combat,         // 일반 전투 방
    Elite,          // 엘리트 적 방
    Boss,           // 보스 방
    Shop,           // 상점
    Rest,           // 휴식 방 (체력 회복)
    Event,          // 랜덤 이벤트
    Treasure,       // 보물 방
}

// RoomNodeData.cs
[System.Serializable]
public class RoomNodeData
{
    public string nodeId;
    public RoomNodeType nodeType;
    public List<string> nextNodeIds;   // 이 노드에서 이동 가능한 다음 노드 ID 목록
    public bool isCompleted;
    public bool isAccessible;          // 현재 선택 가능한 노드인지
}

// RoomNodeMapData.cs (런 당 하나씩 생성)
[CreateAssetMenu(fileName = "RunMap", menuName = "OnionCat/RunMap")]
public class RoomNodeMapData : ScriptableObject
{
    public List<List<RoomNodeData>> rows = new();   // rows[floor][column]
    public string currentNodeId;
}
```

### 2. 맵 생성 (MapGenerator)

```csharp
// MapGenerator.cs
public class MapGenerator : MonoBehaviour
{
    [SerializeField] private int totalFloors = 15;       // 총 층 수
    [SerializeField] private int pathsPerFloor = 3;      // 층당 최대 경로 수
    [SerializeField] private RoomNodeMapData mapData;    // [SerializeField] — 에디터 설정 필요

    // 보스 방은 반드시 마지막 층에 배치
    private readonly Dictionary<int, RoomNodeType[]> forcedTypes = new()
    {
        { 0,  new[] { RoomNodeType.Combat } },    // 시작은 항상 전투
        { 8,  new[] { RoomNodeType.Rest } },      // 중간 항상 휴식
        { 14, new[] { RoomNodeType.Boss } },      // 마지막은 보스
    };

    // 가중치 기반 랜덤 유형 선택
    private RoomNodeType GetRandomType(int floor)
    {
        if (forcedTypes.TryGetValue(floor, out var forced))
            return forced[Random.Range(0, forced.Length)];

        // 가중치 테이블 (총합 100)
        var weights = new (RoomNodeType type, int weight)[]
        {
            (RoomNodeType.Combat,   40),
            (RoomNodeType.Elite,    15),
            (RoomNodeType.Shop,     15),
            (RoomNodeType.Rest,     10),
            (RoomNodeType.Event,    10),
            (RoomNodeType.Treasure, 10),
        };

        int roll = Random.Range(0, 100);
        int cumulative = 0;
        foreach (var (type, weight) in weights)
        {
            cumulative += weight;
            if (roll < cumulative) return type;
        }
        return RoomNodeType.Combat;
    }

    public RoomNodeMapData GenerateMap(int seed)
    {
        Random.InitState(seed);
        var data = ScriptableObject.CreateInstance<RoomNodeMapData>();

        for (int floor = 0; floor < totalFloors; floor++)
        {
            int nodeCount = floor == 0 || floor == totalFloors - 1 ? 1 : Random.Range(2, pathsPerFloor + 1);
            var row = new List<RoomNodeData>();
            for (int i = 0; i < nodeCount; i++)
            {
                row.Add(new RoomNodeData
                {
                    nodeId = $"f{floor}_n{i}",
                    nodeType = GetRandomType(floor),
                    nextNodeIds = new List<string>()
                });
            }
            data.rows.Add(row);
        }

        // 연결 생성: 각 노드에서 다음 층 노드로 1~2개 연결
        for (int floor = 0; floor < totalFloors - 1; floor++)
        {
            var currentRow = data.rows[floor];
            var nextRow = data.rows[floor + 1];
            foreach (var node in currentRow)
            {
                // 최소 1개 연결 보장
                int connectCount = Random.Range(1, Mathf.Min(3, nextRow.Count + 1));
                var shuffled = new List<RoomNodeData>(nextRow);
                for (int k = shuffled.Count - 1; k > 0; k--)
                {
                    int r = Random.Range(0, k + 1);
                    (shuffled[k], shuffled[r]) = (shuffled[r], shuffled[k]);
                }
                for (int c = 0; c < connectCount; c++)
                    node.nextNodeIds.Add(shuffled[c].nodeId);
            }
        }

        // 첫 번째 노드를 접근 가능 상태로 초기화
        data.rows[0].ForEach(n => n.isAccessible = true);
        return data;
    }
}
```

### 3. 맵 UI 표시 (MapUI)

```csharp
// MapUI.cs
public class MapUI : MonoBehaviour
{
    [SerializeField] private GameObject nodeButtonPrefab;   // [SerializeField] — 에디터 드래그 앤 드롭 필요
    [SerializeField] private GameObject connectionLinePrefab;
    [SerializeField] private Transform mapContainer;
    [SerializeField] private Sprite[] nodeTypeIcons;        // [SerializeField] — 방 유형별 아이콘

    [SerializeField] private float floorHeight = 80f;
    [SerializeField] private float nodeSpacing = 100f;

    private Dictionary<string, RectTransform> nodePositions = new();

    public void BuildMapUI(RoomNodeMapData data)
    {
        foreach (Transform child in mapContainer) Destroy(child.gameObject);
        nodePositions.Clear();

        // 노드 버튼 생성
        for (int floor = 0; floor < data.rows.Count; floor++)
        {
            var row = data.rows[floor];
            float totalWidth = (row.Count - 1) * nodeSpacing;
            for (int i = 0; i < row.Count; i++)
            {
                var node = row[i];
                float x = -totalWidth / 2 + i * nodeSpacing;
                float y = floor * floorHeight;
                var btn = Instantiate(nodeButtonPrefab, mapContainer);
                var rt = btn.GetComponent<RectTransform>();
                rt.anchoredPosition = new Vector2(x, y);
                nodePositions[node.nodeId] = rt;

                // 노드 버튼 설정
                var nodeBtn = btn.GetComponent<NodeButton>();
                nodeBtn.Setup(node, OnNodeSelected);
            }
        }

        // 연결선 그리기
        for (int floor = 0; floor < data.rows.Count - 1; floor++)
        {
            foreach (var node in data.rows[floor])
            {
                foreach (var nextId in node.nextNodeIds)
                {
                    if (nodePositions.TryGetValue(node.nodeId, out var fromPos) &&
                        nodePositions.TryGetValue(nextId, out var toPos))
                    {
                        DrawConnection(fromPos.anchoredPosition, toPos.anchoredPosition);
                    }
                }
            }
        }
    }

    private void DrawConnection(Vector2 from, Vector2 to)
    {
        var line = Instantiate(connectionLinePrefab, mapContainer);
        // UI Image를 선으로 늘리거나 LineRenderer UI 사용
        var rt = line.GetComponent<RectTransform>();
        Vector2 dir = to - from;
        rt.anchoredPosition = (from + to) / 2;
        rt.sizeDelta = new Vector2(dir.magnitude, 2f);
        rt.localRotation = Quaternion.Euler(0, 0, Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg);
    }

    private void OnNodeSelected(RoomNodeData node)
    {
        MapManager.Instance.SelectNode(node);
    }
}
```

### 4. 맵 관리자 (MapManager)

```csharp
// MapManager.cs
public class MapManager : MonoBehaviour
{
    public static MapManager Instance { get; private set; }

    [SerializeField] private MapUI mapUI;   // [SerializeField] — 에디터 설정 필요

    private RoomNodeMapData currentMap;

    void Awake() => Instance = this;

    public void StartNewRun(int seed)
    {
        var generator = FindObjectOfType<MapGenerator>();
        currentMap = generator.GenerateMap(seed);
        RefreshMapUI();
    }

    public void SelectNode(RoomNodeData node)
    {
        if (!node.isAccessible) return;

        // 현재 노드 완료 처리
        if (!string.IsNullOrEmpty(currentMap.currentNodeId))
        {
            var prevNode = FindNode(currentMap.currentNodeId);
            if (prevNode != null) prevNode.isCompleted = true;
        }

        currentMap.currentNodeId = node.nodeId;

        // 다음 노드 접근 가능 설정
        foreach (var row in currentMap.rows)
            foreach (var n in row) n.isAccessible = false;

        foreach (var nextId in node.nextNodeIds)
        {
            var nextNode = FindNode(nextId);
            if (nextNode != null) nextNode.isAccessible = true;
        }

        RefreshMapUI();
        // 해당 방 씬 로드
        LoadRoomScene(node.nodeType);
    }

    private RoomNodeData FindNode(string id)
    {
        foreach (var row in currentMap.rows)
            foreach (var node in row)
                if (node.nodeId == id) return node;
        return null;
    }

    private void LoadRoomScene(RoomNodeType type)
    {
        string sceneName = type switch
        {
            RoomNodeType.Boss     => "BossRoom",
            RoomNodeType.Shop     => "ShopRoom",
            RoomNodeType.Rest     => "RestRoom",
            _                     => "CombatRoom"
        };
        SceneManager.LoadScene(sceneName, LoadSceneMode.Additive);
    }

    private void RefreshMapUI() => mapUI.BuildMapUI(currentMap);
}
```

### 5. 맵 열기/닫기 단축키 (M키)

```csharp
// MapToggleInput.cs (New Input System)
public class MapToggleInput : MonoBehaviour
{
    [SerializeField] private GameObject mapPanel;    // [SerializeField] — 에디터 설정 필요
    private InputAction mapAction;

    void Awake()
    {
        mapAction = new InputAction(binding: "<Keyboard>/m");
        mapAction.performed += _ => ToggleMap();
    }

    void OnEnable()  => mapAction.Enable();
    void OnDisable() => mapAction.Disable();

    void ToggleMap() => mapPanel.SetActive(!mapPanel.activeSelf);
}
```

---

## OnionCat 적용 포인트

### 경로 선택으로 두 플레이어 소통 유도

```
OnionCat 특화 맵 설계:
- 분기 선택 화면에서 Cat과 Crop이 각자 선호 방향을 "투표"하는 연출
  예: Cat(P1)이 A경로, Crop(P2)이 B경로 가리키면 3초 후 Cat 방향 우선 (P1이 이동을 담당하므로)
  → 두 플레이어가 잠깐 토론하는 자연스러운 협력 순간 생성

방 유형별 역할 연관:
- Combat  → Cat이 주로 활약 (근접)
- Elite   → Crop 패링 필요 (강력한 원거리 적)
- Shop    → 공유 골드로 Cat용/Crop용 업그레이드 구분 구매
- Rest    → 두 캐릭터 HP 회복 (공유 HP이므로 한 번에)
- Event   → 두 플레이어 각자 선택지 다르게 표시 가능
```

### 맵 저장 & 런 계속하기

```
currentMap 데이터를 JSON으로 직렬화 → Save_Load_System과 연동
런 중 게임 종료 후 재시작 시 맵 상태 복원
```

### 방 유형 아이콘 권장

```
방 유형 → 아이콘 제안:
Combat  → 검 아이콘 (Cat 무기)
Elite   → 해골+별
Boss    → 왕관
Shop    → 동전
Rest    → 하트
Event   → ?표시
Treasure → 보물상자
```

---

## 참고 링크

- Unity ScriptableObject 활용: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Slay the Spire 맵 시스템 분석: https://www.gamedeveloper.com/design/how-slay-the-spire-s-map-creates-meaningful-decisions
- Unity 씬 관리자: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- UI Image로 선 그리기 (연결선): https://discussions.unity.com/t/draw-line-between-two-ui-elements/
- 참고 오픈소스 맵 구현: "Slay the Spire Map Generator Unity" 깃허브 검색
