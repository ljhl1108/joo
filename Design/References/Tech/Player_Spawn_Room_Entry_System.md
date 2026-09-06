# 플레이어 스폰 & 방 진입 시스템 (Player Spawn & Room Entry System)

리서치 날짜: 2026-09-06

## 개요

로그라이크 게임에서 플레이어가 새 방에 진입할 때 **어디에 스폰될지, 어떤 연출과 함께 나타날지**를 관리하는 시스템이다. 잘 구현된 방 진입 시스템은:
- 플레이어가 문 통과 시 자연스러운 위치에 나타나게 함
- 방 진입 연출(페이드, 슬라이드, 카메라 전환)을 제공
- 온라인/오프라인 협동에서 두 플레이어가 같은 지점에서 시작하게 조율
- 방 상태(적 리셋, 오브젝트 초기화)를 올바르게 설정

OnionCat에서는 단일 복합 캐릭터(Cat + Crop)가 문을 통과하므로, 스폰 포지션이 하나여야 한다.

---

## 핵심 개념

### 스폰 포인트 설계 원칙

1. **문별 스폰 포인트**: 각 문(Door)에 스폰 위치 마커 오브젝트를 배치
2. **방향성 오프셋**: 문 안쪽(방 내부) 방향으로 일정 거리(예: 1.5~2 유닛) 떨어진 위치
3. **충돌 체크**: 스폰 위치가 벽/장애물과 겹치지 않도록 검증

```
[문 오브젝트]
   ↓ 방향 벡터 * 오프셋
[SpawnPoint Transform]  ← 플레이어가 여기서 나타남
```

### 방 진입 흐름

```
문 트리거 Enter
  → 현재 방 완료 여부 확인 (적 전멸 조건 등)
  → 다음 방 씬/오브젝트 활성화
  → 플레이어를 스폰 포인트 위치로 이동
  → 카메라 전환 연출
  → 다음 방 적 스폰 시작
```

---

## Unity 구현 방법

### 1. Door 컴포넌트 설계

```csharp
public class RoomDoor : MonoBehaviour
{
    [SerializeField] private Transform spawnPoint;
    [SerializeField] private RoomDoor connectedDoor; // 연결된 반대편 문
    [SerializeField] private Direction doorDirection; // North, South, East, West

    private bool isLocked = true;

    public void Unlock()
    {
        isLocked = false;
        // 문 열림 애니메이션 트리거
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (isLocked) return;
        if (!other.CompareTag("Player")) return;
        
        RoomManager.Instance.TransitionToConnectedRoom(this);
    }

    public Vector3 GetSpawnPosition() => spawnPoint.position;
}
```

### 2. RoomManager — 방 전환 처리

```csharp
public class RoomManager : MonoBehaviour
{
    public static RoomManager Instance { get; private set; }

    [SerializeField] private float transitionDuration = 0.5f;

    private Room currentRoom;
    private bool isTransitioning;

    public void TransitionToConnectedRoom(RoomDoor exitDoor)
    {
        if (isTransitioning) return;
        StartCoroutine(DoRoomTransition(exitDoor));
    }

    private IEnumerator DoRoomTransition(RoomDoor exitDoor)
    {
        isTransitioning = true;

        // 1. 플레이어 입력 잠금
        PlayerController.Instance.SetInputEnabled(false);

        // 2. 페이드 아웃
        yield return FadeManager.Instance.FadeOut(transitionDuration);

        // 3. 플레이어를 다음 방 스폰 포인트로 이동
        RoomDoor entryDoor = exitDoor.connectedDoor;
        Vector3 spawnPos = entryDoor.GetSpawnPosition();
        PlayerController.Instance.TeleportTo(spawnPos);

        // 4. 카메라를 새 방 위치로 즉시 이동
        CameraController.Instance.SnapToRoom(entryDoor.GetComponentInParent<Room>());

        // 5. 새 방 초기화 (적 스폰, 문 잠금 등)
        currentRoom = entryDoor.GetComponentInParent<Room>();
        currentRoom.Initialize();

        // 6. 페이드 인
        yield return FadeManager.Instance.FadeIn(transitionDuration);

        // 7. 입력 복구
        PlayerController.Instance.SetInputEnabled(true);

        isTransitioning = false;
    }
}
```

### 3. Room 초기화 패턴

```csharp
public class Room : MonoBehaviour
{
    [SerializeField] private EnemySpawner[] spawners;
    [SerializeField] private RoomDoor[] doors;
    [SerializeField] private bool isBossRoom;

    private bool isCleared;

    public void Initialize()
    {
        if (isCleared) return; // 이미 클리어한 방은 재초기화 안 함

        // 문 잠금 (전투 시작 전)
        foreach (var door in doors)
            door.Lock();

        // 적 스폰
        foreach (var spawner in spawners)
            spawner.SpawnAll();

        // 적 전멸 이벤트 구독
        EnemyManager.Instance.OnAllEnemiesDefeated += HandleRoomCleared;
    }

    private void HandleRoomCleared()
    {
        isCleared = true;
        EnemyManager.Instance.OnAllEnemiesDefeated -= HandleRoomCleared;

        // 문 열기
        foreach (var door in doors)
            door.Unlock();

        // 보상 드롭
        if (isBossRoom)
            RewardManager.Instance.SpawnBossReward(transform.position);
    }
}
```

### 4. 진입 연출 — 슬라이드 스크롤 방식 (Hades 스타일)

페이드 대신 카메라가 슬라이드되는 방식:

```csharp
private IEnumerator SlideTransition(RoomDoor exitDoor)
{
    RoomDoor entryDoor = exitDoor.connectedDoor;
    Room nextRoom = entryDoor.GetComponentInParent<Room>();

    // 다음 방 활성화 (현재는 보이지 않는 위치)
    nextRoom.gameObject.SetActive(true);

    // 플레이어 순간이동 (카메라 이동 전에)
    Vector3 spawnPos = entryDoor.GetSpawnPosition();
    PlayerController.Instance.TeleportTo(spawnPos);

    // 카메라 슬라이드
    Vector3 targetPos = nextRoom.CameraCenter;
    float elapsed = 0f;
    while (elapsed < transitionDuration)
    {
        elapsed += Time.deltaTime;
        float t = Mathf.SmoothStep(0, 1, elapsed / transitionDuration);
        Camera.main.transform.position = Vector3.Lerp(Camera.main.transform.position, targetPos, t);
        yield return null;
    }

    // 이전 방 비활성화
    currentRoom.gameObject.SetActive(false);
    currentRoom = nextRoom;
    currentRoom.Initialize();
}
```

### 5. 스폰 포인트 씬 배치

Unity 에디터에서:
- 각 Door 오브젝트 자식으로 `SpawnPoint` Empty 오브젝트 추가
- Door 방향에 따라 오프셋 설정:
  - 북쪽 문 → SpawnPoint를 문 아래 (Y: -1.5)
  - 남쪽 문 → SpawnPoint를 문 위 (Y: +1.5)
  - 동쪽 문 → SpawnPoint를 문 왼쪽 (X: -1.5)
  - 서쪽 문 → SpawnPoint를 문 오른쪽 (X: +1.5)

---

## OnionCat 적용 포인트

### 단일 복합 캐릭터의 스폰

OnionCat은 Cat이 Crop을 등에 진 **단일 오브젝트**이므로 스폰 포인트도 하나다. 단, 입장 시 연출:

```csharp
// 방 진입 시 플레이어를 잠시 무적 상태로
private IEnumerator RoomEntryInvincibility()
{
    PlayerStats.Instance.SetInvincible(true);
    yield return new WaitForSeconds(0.5f); // 0.5초 무적
    PlayerStats.Instance.SetInvincible(false);
}
```

### 방 클리어 조건

OnionCat은 "모든 적 처치" 조건 외에 추가 고려:
- 메달리아 약점 공략 조건 (근접으로 처치 or 원거리로 처치 카운팅)
- 방 타이머 보너스 (빠른 클리어 시 추가 재화)

### 문 방향 기반 스폰 오프셋 구현

```csharp
public enum Direction { North, South, East, West }

public static Vector2 GetSpawnOffset(Direction dir, float distance = 1.5f)
{
    return dir switch
    {
        Direction.North => Vector2.down * distance,
        Direction.South => Vector2.up * distance,
        Direction.East  => Vector2.left * distance,
        Direction.West  => Vector2.right * distance,
        _ => Vector2.zero
    };
}
```

### 방 상태 저장 (이미 클리어한 방 재방문)

로그라이크에서 플레이어가 이미 클리어한 방으로 돌아올 경우:
- 적은 리스폰 안 함
- 문은 열려있음
- 보상은 이미 가져간 상태
- `Room.isCleared` 플래그로 간단히 처리

---

## 참고 링크

- Unity 공식: [Physics2D.OverlapCircle](https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircle.html) — 스폰 위치 충돌 검증
- Unity 공식: [Coroutines](https://docs.unity3d.com/Manual/Coroutines.html) — 전환 시퀀스 구현
- Unity Learn: [2D Roguelike Tutorial](https://learn.unity.com/project/2d-roguelike-tutorial) — 방 기반 레벨 구조 참고
- Catlike Coding: Room & Camera transitions in 2D — 카메라 슬라이드 구현 심화
- GDC: "Rooms and Transitions in Hades" — Supergiant의 방 전환 설계 철학
