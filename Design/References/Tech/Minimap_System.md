# 미니맵 시스템 (Minimap System)

리서치 날짜: 2026-06-19

## 개요

미니맵은 플레이어가 전체 던전 구조를 한눈에 파악할 수 있게 해주는 UI 요소다.  
로그라이크에서는 절차적으로 생성된 방들을 탐색 중에 발견되는 방식이 일반적이다.  
OnionCat은 방 단위 탐험 구조이므로 "방 아이콘 기반 미니맵"이 가장 적합하다.

---

## 미니맵 구현 방식 비교

| 방식 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **RenderTexture** | 별도 카메라로 씬 전체를 렌더링 | 실시간, 정확함 | 성능 비용 높음 |
| **방 아이콘 UI** | 방 데이터 기반으로 UI 그리드 생성 | 가볍고 제어 쉬움 | 직접 구현 필요 |
| **Raw Image + UI** | RenderTexture를 UI RawImage에 표시 | 쉬운 통합 | 카메라 시야 조정 필요 |

OnionCat 추천: **방 아이콘 UI 방식** (절차적 방 시스템과 자연스럽게 연동, 저성능 장치에서도 안정적)

---

## Unity 구현 방법 — 방 아이콘 기반 미니맵

### 전제: 방 데이터 구조

```csharp
// Room.cs (기존 방 시스템과 연동)
public class Room : MonoBehaviour
{
    public Vector2Int gridPosition;  // 던전 그리드 상의 좌표
    public bool isVisited = false;
    public bool isCurrent = false;
    public RoomType roomType;        // Normal, Boss, Shop, Start 등
    public List<Direction> openDoors; // 연결된 방향
}

public enum RoomType { Normal, Boss, Shop, Start, Treasure }
public enum Direction { Up, Down, Left, Right }
```

### 1. MinimapManager — 미니맵 전체 관리

```csharp
public class MinimapManager : MonoBehaviour
{
    [SerializeField] private GameObject roomIconPrefab;
    [SerializeField] private Transform minimapContainer;
    [SerializeField] private float iconSize = 20f;      // UI 픽셀 크기
    [SerializeField] private float iconSpacing = 24f;   // 아이콘 간격

    private Dictionary<Vector2Int, MinimapRoomIcon> iconMap = new();

    public void RegisterRoom(Room room)
    {
        if (iconMap.ContainsKey(room.gridPosition)) return;

        GameObject iconGO = Instantiate(roomIconPrefab, minimapContainer);
        var icon = iconGO.GetComponent<MinimapRoomIcon>();
        icon.Initialize(room);

        // 그리드 좌표 → UI 위치 변환
        var rt = iconGO.GetComponent<RectTransform>();
        rt.anchoredPosition = new Vector2(
            room.gridPosition.x * iconSpacing,
            room.gridPosition.y * iconSpacing
        );

        iconMap[room.gridPosition] = icon;
        icon.SetState(MinimapIconState.Hidden); // 처음엔 숨김
    }

    public void RevealRoom(Room room)
    {
        if (iconMap.TryGetValue(room.gridPosition, out var icon))
            icon.SetState(MinimapIconState.Visited);
    }

    public void SetCurrentRoom(Room room)
    {
        // 이전 현재 방 초기화
        foreach (var icon in iconMap.Values)
            if (icon.State == MinimapIconState.Current)
                icon.SetState(MinimapIconState.Visited);

        if (iconMap.TryGetValue(room.gridPosition, out var currentIcon))
            currentIcon.SetState(MinimapIconState.Current);
    }
}
```

### 2. MinimapRoomIcon — 개별 방 아이콘

```csharp
public enum MinimapIconState { Hidden, Visited, Current }

public class MinimapRoomIcon : MonoBehaviour
{
    [SerializeField] private Image roomImage;
    [SerializeField] private Image playerDot;  // 현재 위치 표시

    [SerializeField] private Color hiddenColor = new Color(0, 0, 0, 0);
    [SerializeField] private Color visitedColor = new Color(0.5f, 0.5f, 0.5f, 1f);
    [SerializeField] private Color currentColor = Color.white;

    [SerializeField] private Sprite normalSprite;
    [SerializeField] private Sprite bossSprite;
    [SerializeField] private Sprite shopSprite;
    [SerializeField] private Sprite treasureSprite;

    public MinimapIconState State { get; private set; }
    private Room linkedRoom;

    public void Initialize(Room room)
    {
        linkedRoom = room;
        roomImage.sprite = room.roomType switch
        {
            RoomType.Boss => bossSprite,
            RoomType.Shop => shopSprite,
            RoomType.Treasure => treasureSprite,
            _ => normalSprite
        };
        playerDot.gameObject.SetActive(false);
    }

    public void SetState(MinimapIconState state)
    {
        State = state;
        roomImage.color = state switch
        {
            MinimapIconState.Hidden => hiddenColor,
            MinimapIconState.Visited => visitedColor,
            MinimapIconState.Current => currentColor,
            _ => hiddenColor
        };
        playerDot.gameObject.SetActive(state == MinimapIconState.Current);
    }
}
```

### 3. 방 전환 시 미니맵 업데이트

```csharp
// RoomManager.cs 또는 DungeonManager.cs
public class RoomManager : MonoBehaviour
{
    [SerializeField] private MinimapManager minimapManager;

    public void OnPlayerEnterRoom(Room room)
    {
        if (!room.isVisited)
        {
            room.isVisited = true;
            minimapManager.RevealRoom(room);

            // 인접 방도 미리 공개 (선택사항 — Binding of Isaac 스타일)
            // RevealAdjacentRooms(room);
        }
        minimapManager.SetCurrentRoom(room);
    }
}
```

### 4. 던전 생성 시 미니맵에 방 등록

```csharp
// DungeonGenerator.cs
[SerializeField] private MinimapManager minimapManager;

private void RegisterAllRooms(List<Room> rooms)
{
    foreach (var room in rooms)
        minimapManager.RegisterRoom(room);
}
```

### 5. 미니맵 UI 구조 (Canvas 계층)

```
Canvas (Screen Space - Overlay)
└── MinimapPanel (Image — 반투명 배경)
    ├── MinimapViewport (Mask 컴포넌트 — 스크롤 영역 제한)
    │   └── MinimapContainer (RectTransform — 여기에 아이콘 배치)
    └── PlayerPositionDot (Image — 선택사항: 별도 오버레이)
```

### 6. RenderTexture 방식 (참고용)

```csharp
// MinimapCamera.cs
public class MinimapCamera : MonoBehaviour
{
    [SerializeField] private Camera minimapCam;
    [SerializeField] private RawImage minimapDisplay;
    [SerializeField] private Transform playerTransform;

    private void LateUpdate()
    {
        // 미니맵 카메라를 플레이어 위에 배치
        transform.position = new Vector3(
            playerTransform.position.x,
            playerTransform.position.y,
            transform.position.z
        );
    }
}
// 미니맵 카메라 LayerMask: "Minimap" 레이어만 렌더링
// RenderTexture를 Canvas의 RawImage에 연결
```

---

## 미니맵 고급 기능

### 안개 효과 (Fog of War)
- 방문하지 않은 방: 완전 숨김 or 어둡게
- 방문한 방: 회색
- 현재 방: 밝게 + 플레이어 도트

### 방 연결선 (복도 표시)
```csharp
// 방 아이콘 사이에 얇은 선 UI 이미지 생성
private void DrawConnection(Vector2Int from, Vector2Int to)
{
    // from과 to의 중간점에 1×4픽셀 이미지 배치
    // Horizontal/Vertical 판단 후 회전
}
```

### 특수 방 아이콘
- 보스방: 해골 아이콘 + 붉은 색
- 상점: 금화 아이콘
- 보물방: 상자 아이콘
- 시작방: 집 아이콘

---

## OnionCat 적용 포인트

### 1. 두 플레이어 동시 위치 표시
- OnionCat은 한 몸체이므로 플레이어 도트 1개만 필요
- 단, P2(양파) 조준 방향을 화살표로 미니맵에 표시하면 재미있는 UI 가능

### 2. 방 유형별 색상 코드
- 일반 방: 흰색
- 보스 방: 빨간색 (발견 전엔 숨김)
- 상점: 노란색
- 현재 방: 초록색 or 밝은 파란색

### 3. 미니맵 토글
```csharp
// 전체 맵 보기 (M키 등으로 토글)
[SerializeField] private GameObject fullMapPanel;
public void ToggleFullMap() => fullMapPanel.SetActive(!fullMapPanel.activeSelf);
```

### 4. 방 방문 시 효과
- 미니맵 방 아이콘이 처음 공개될 때 작은 "팝인" 애니메이션
- DOTween 또는 Animator로 scale 0→1 트윈

### 5. UI 배치
- 화면 우상단에 소형 미니맵
- `[SerializeField] private Sprite` 변수들 → **유니티 에디터에서 드래그 앤 드롭 설정 필요**

---

## 주의사항

- `MinimapContainer` 크기가 화면을 벗어날 수 있음 → **Mask 컴포넌트**로 뷰포트 제한 필수
- 방 그리드 좌표와 UI 좌표 매핑 시 y축 방향 주의 (Unity UI는 위가 +y, 게임 월드와 같음)
- RenderTexture 방식은 카메라가 하나 더 필요 → 성능 신중히 고려
- `[SerializeField] private GameObject roomIconPrefab` → **유니티 에디터에서 드래그 앤 드롭 설정 필요**
- `[SerializeField] private Transform minimapContainer` → **유니티 에디터에서 드래그 앤 드롭 설정 필요**

---

## 참고 링크

- [Unity UI Mask](https://docs.unity3d.com/Manual/script-Mask.html)
- [Unity RenderTexture](https://docs.unity3d.com/Manual/class-RenderTexture.html)
- [Unity RectTransform.anchoredPosition](https://docs.unity3d.com/ScriptReference/RectTransform-anchoredPosition.html)
- [Binding of Isaac Minimap Implementation Analysis (Gamasutra)](https://www.gamedeveloper.com/design/the-binding-of-isaac)
- [Unity 2D Minimap Tutorial - Brackeys (YouTube)](https://www.youtube.com/results?search_query=unity+minimap+2d+brackeys)
