# Room Prefab Reuse Architecture (방 씬 재사용 아키텍처)

리서치 날짜: 2026-11-27

## 개요

로그라이크에서 방(Room)은 수백 번 반복 사용된다. 매번 Instantiate/Destroy하면:
- GC(가비지 컬렉션) 스파이크 → 프레임 드랍
- 씬 이동 비용 → 로딩 화면 필요
- 오브젝트 상태 초기화 코드 분산

**방 씬 재사용 아키텍처**는 방 오브젝트를 풀처럼 유지하고 "방에 들어갈 때마다 상태를 리셋"하는 패턴이다.
OnionCat이 `Room.ResetForReuse()`로 이미 구현한 방식과 정확히 같은 패턴.

---

## Unity 구현 방법

### 패턴 1: 단일 방 재사용 (OnionCat 현재 방식)

```csharp
// 씬에 방 오브젝트 하나 고정, 들어갈 때마다 상태 교체
public class Room : MonoBehaviour
{
    public void ResetForReuse(RoomData data)
    {
        // 1. 이전 적 제거 (풀 반환)
        foreach (var enemy in spawnedEnemies)
            PoolManager.Despawn(enemy);
        spawnedEnemies.Clear();

        // 2. 문 상태 초기화
        foreach (var door in doors)
            door.SetLocked(true);

        // 3. 소품 리셋 (파괴된 항아리 복원 등)
        foreach (var prop in props)
            prop.Reset();

        // 4. 새 데이터로 적·소품·보상 세팅
        ApplyRoomData(data);
    }
}
```

**장점**: 구조 단순, 항상 같은 Transform에 방이 있음
**단점**: 이전 방으로 돌아가기 불가, 방이 하나뿐이어서 이웃 방 미리보기 어려움

---

### 패턴 2: 방 오브젝트 풀 (방이 여러 개 동시에 존재)

```csharp
public class RoomPool : MonoBehaviour
{
    [SerializeField] private Room roomPrefab;
    [SerializeField] private int poolSize = 5; // 현재 방 + 주변 방 미리 활성화
    
    private Queue<Room> available = new();
    private List<Room> active = new();

    private void Awake()
    {
        for (int i = 0; i < poolSize; i++)
        {
            var r = Instantiate(roomPrefab);
            r.gameObject.SetActive(false);
            available.Enqueue(r);
        }
    }

    public Room GetRoom(RoomData data)
    {
        var room = available.Count > 0 ? available.Dequeue() : Instantiate(roomPrefab);
        room.ResetForReuse(data);
        room.gameObject.SetActive(true);
        active.Add(room);
        return room;
    }

    public void ReturnRoom(Room room)
    {
        active.Remove(room);
        room.gameObject.SetActive(false);
        available.Enqueue(room);
    }
}
```

**장점**: 이웃 방 미리 로드 가능, 방 전환이 부드러움
**단점**: 여러 방이 동시에 존재 → 메모리 더 사용, 적 AI가 다른 방 오브젝트를 감지할 수 있음

---

### 패턴 3: Additive Scene Loading (방마다 별도 씬)

```csharp
// 방마다 Unity 씬 하나 (가장 격리됨)
public class RoomSceneManager : MonoBehaviour
{
    private string currentRoomScene;

    public async Task TransitionToRoom(string sceneName, RoomData data)
    {
        // 현재 방 씬 언로드 (비동기)
        if (currentRoomScene != null)
            await SceneManager.UnloadSceneAsync(currentRoomScene);

        // 새 방 씬 로드 (비동기)
        await SceneManager.LoadSceneAsync(sceneName, LoadSceneMode.Additive);
        currentRoomScene = sceneName;

        // 로드된 씬에서 Room 컴포넌트 찾아 초기화
        var room = FindObjectOfType<Room>();
        room.Initialize(data);
    }
}
```

**장점**: 씬별 완전 격리, 에디터에서 각 방을 독립적으로 편집 가능
**단점**: 씬 전환 비용, 로딩 시간 발생, 방 개수가 많으면 Build Settings 관리 복잡

---

### OnionCat에 맞는 초기화 패턴

```csharp
public class Room : MonoBehaviour
{
    // 비활성화 시 자동 초기화되는 컴포넌트들이 OnEnable에서 상태 초기화
    // → PoolManager.Spawn과 같은 원리
    
    private void OnEnable()
    {
        // 방이 활성화될 때마다 항상 깨끗한 상태로 시작
        ClearEnemies();
        ResetDoors();
        ResetProps();
        isCleared = false;
    }

    public void PopulateRoom(DungeonNode node)
    {
        // OnEnable 이후에 적·보상 세팅
        // node.enemyList, node.rewardType 등 사용
        SpawnEnemies(node);
        PlaceReward(node.rewardType);
    }
}
```

**핵심 원칙**: 초기화는 `OnEnable`에서, 데이터 주입은 `PopulateRoom()`에서 — 순서 보장

---

## OnionCat 적용 포인트

### 현재 구조 (CLAUDE.md 기준)

```
Room.ResetForReuse() — 패턴 1 (단일 방 재사용)
Room_Special — 보물/상점/휴식 방을 하나의 오브젝트로 돌려씀
Room_Painted — 그려진 방; PaintedRoomView.Apply()로 교체
```

### 주의: `OnEnable` 순서

여러 컴포넌트가 `OnEnable`에서 초기화할 때 순서 보장이 필요하면:

```csharp
// Script Execution Order 설정 (Project Settings > Script Execution Order)
// 또는 명시적 의존성:

public class Room : MonoBehaviour
{
    [SerializeField] private RoomArt roomArt;      // 먼저
    [SerializeField] private EnemySpawner spawner; // 나중

    private void OnEnable()
    {
        roomArt.Reset();    // 비주얼 먼저
        spawner.Reset();    // 그 다음 적
    }
}
```

### 그려진 방(Painted Room) 최적화

그려진 방은 Back/Front/Mask 스프라이트가 크므로:

```csharp
public class PaintedRoomView : MonoBehaviour
{
    // 같은 스테이지 내에서는 텍스처 재사용 (에셋 레퍼런스 유지)
    private Sprite cachedBack;
    private Sprite cachedFront;

    public void Apply(PaintedRoom data)
    {
        // 같은 방이면 Apply 스킵
        if (currentRoom == data) return;

        backRenderer.sprite = data.backSprite;
        frontRenderer.sprite = data.frontSprite;
        // 판정 메시 갱신은 최초 1회 or 방이 바뀔 때만
        if (currentRoom?.shape != data.shape)
            RebuildCollider(data.colliderMesh);

        currentRoom = data;
    }
}
```

### 적 재등장 방지

방을 재방문할 때 적이 다시 나오면 안 됨:

```csharp
public class DungeonNode
{
    public bool isCleared;    // 클리어한 방은 적 없이 재입장
    public bool isVisited;    // 방문 기록 (지도 표시용)
}

// Room.PopulateRoom() 첫 줄:
if (node.isCleared)
{
    OpenAllDoors();
    return; // 적 스폰 없이 종료
}
```

---

## 참고 링크

- Unity Additive Scene Loading 공식: https://docs.unity3d.com/Manual/LoadingMultipleScenes.html
- Object Pool API (Unity 2021+): https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- OnionCat 현재 구조: `Assets/Scripts/Dungeon/Room.cs`, `DungeonManager.cs`
- 관련 기술 문서: `Design/References/Tech/Door_Room_Transition_System.md`, `Design/References/Tech/Unity_Object_Pool_API.md`
