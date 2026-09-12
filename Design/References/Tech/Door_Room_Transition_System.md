# 문 연결 로직 & 룸 전환 시스템 (Door Room Transition System)

리서치 날짜: 2026-09-12

## 개요
탑다운 로그라이크에서 "방(Room)" 단위로 진행할 때, 각 방의 출입구(Door)가 어떻게
- 잠기고(locked) / 열리고(unlocked) / 통과(transition)되는지
- 플레이어를 다음 방으로 옮기는지 (즉시 vs 애니메이션)
- 카메라가 방 전환을 어떻게 처리하는지

를 구현하는 시스템. Room_System.md와 달리, 이 문서는 "방과 방 사이의 경계"에 집중한다.

---

## Unity 구현 방법

### 1. 문(Door)의 상태머신
```csharp
public enum DoorState { Locked, Unlocked, Open }

public class DoorController : MonoBehaviour
{
    [SerializeField] private DoorState state = DoorState.Locked;
    [SerializeField] private Transform spawnPoint; // 반대편 방 진입 위치
    [SerializeField] private DoorController linkedDoor; // 연결된 반대편 문

    private Collider2D col;
    private Animator anim;

    void Awake()
    {
        col = GetComponent<Collider2D>();
        anim = GetComponent<Animator>();
    }

    public void Unlock()
    {
        if (state == DoorState.Locked)
        {
            state = DoorState.Unlocked;
            col.isTrigger = true;       // 통과 가능하게
            anim.SetTrigger("Unlock");  // 문 열림 애니메이션
            AudioManager.Play("door_unlock");
        }
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (state == DoorState.Unlocked && other.CompareTag("Player"))
        {
            RoomTransitionManager.Instance.Transition(this);
        }
    }
}
```

### 2. 방 클리어 → 문 열림 연결
```csharp
public class EnemyRoom : MonoBehaviour
{
    [SerializeField] private DoorController[] doors;
    private int aliveEnemies;

    void Start()
    {
        aliveEnemies = GetComponentsInChildren<Enemy>().Length;
    }

    public void OnEnemyDied()
    {
        aliveEnemies--;
        if (aliveEnemies <= 0)
            OnRoomCleared();
    }

    private void OnRoomCleared()
    {
        foreach (var door in doors)
            door.Unlock();

        StartCoroutine(ClearCelebration());
    }

    private IEnumerator ClearCelebration()
    {
        // 파티클 + SFX 먼저
        ParticleManager.SpawnRoomClear(transform.position);
        AudioManager.Play("room_clear");
        yield return new WaitForSeconds(0.3f);
        // 루트 스폰
        LootSpawner.Spawn(transform.position);
    }
}
```

### 3. 룸 전환 관리자 (블랙아웃 or 카메라 팬)
```csharp
public class RoomTransitionManager : MonoBehaviour
{
    public static RoomTransitionManager Instance;
    [SerializeField] private CanvasGroup fadeCanvas;
    [SerializeField] private float fadeDuration = 0.25f;

    private bool isTransitioning;

    public void Transition(DoorController exitDoor)
    {
        if (isTransitioning) return;
        StartCoroutine(DoTransition(exitDoor));
    }

    private IEnumerator DoTransition(DoorController exitDoor)
    {
        isTransitioning = true;

        // 1. 페이드 아웃
        yield return StartCoroutine(Fade(0f, 1f));

        // 2. 플레이어를 다음 방 스폰 포인트로 이동
        var targetSpawn = exitDoor.LinkedDoor.SpawnPoint;
        PlayerManager.Instance.TeleportAll(targetSpawn.position);

        // 3. 새 방 활성화 / 카메라 경계 업데이트
        RoomManager.Instance.LoadRoom(exitDoor.LinkedDoor.transform.parent);

        // 4. 페이드 인
        yield return StartCoroutine(Fade(1f, 0f));

        isTransitioning = false;
    }

    private IEnumerator Fade(float from, float to)
    {
        float elapsed = 0f;
        while (elapsed < fadeDuration)
        {
            fadeCanvas.alpha = Mathf.Lerp(from, to, elapsed / fadeDuration);
            elapsed += Time.deltaTime;
            yield return null;
        }
        fadeCanvas.alpha = to;
    }
}
```

### 4. 카메라 방 경계 잠금 (Cinemachine 없이)
```csharp
// CameraController.cs
public void SetRoomBounds(Bounds roomBounds)
{
    // Cinemachine ConfinerExtension 또는 직접 Clamp
    minX = roomBounds.min.x + halfScreenW;
    maxX = roomBounds.max.x - halfScreenW;
    minY = roomBounds.min.y + halfScreenH;
    maxY = roomBounds.max.y - halfScreenH;
}

void LateUpdate()
{
    Vector3 pos = target.position;
    pos.x = Mathf.Clamp(pos.x, minX, maxX);
    pos.y = Mathf.Clamp(pos.y, minY, maxY);
    pos.z = -10f;
    transform.position = pos;
}
```

---

## OnionCat 적용 포인트

### 1. 두 플레이어 동시 통과 판정
```csharp
// 두 플레이어가 모두 문에 닿아야 전환 시작 (선택적 설계)
private HashSet<Collider2D> playersNearDoor = new();

private void OnTriggerEnter2D(Collider2D other)
{
    if (other.CompareTag("Player"))
    {
        playersNearDoor.Add(other);
        // OnionCat은 한 몸이므로 단일 플레이어 오브젝트를 씀 → 즉시 전환
        // 만약 두 캐릭터가 분리된다면 이 방식으로 둘 다 통과 확인
    }
}
```

OnionCat은 Cat이 몸을 이동시키므로 **Cat 오브젝트가 문 트리거 진입 시 전환** — Onion은 Cat의 자식으로 함께 이동.

### 2. 문 방향 (상하좌우) 설계
- OnionCat 방: 기본적으로 좌·우 2방향 문만 사용 (단순화)
- Cat의 이동 방향이 마지막 입력 방향 → 해당 방향 문이 "활성 강조" 표시
- Onion(P2)의 조준이 문 방향이면 문 근처 파티클 힌트 발생 → 자연스러운 유도

### 3. 잠긴 문 시각 처리
- `DoorState.Locked` → 문 스프라이트에 자물쇠 아이콘 오버레이
- 플레이어가 잠긴 문에 닿으면: 벽에 살짝 밀려나는 물리 반응 + 낮은 "잠김" 사운드
- 오해 없이 "아직 방을 클리어해야 한다" 전달

### 4. 전환 중 무적 처리
```csharp
// 전환 시작 시 플레이어 피격 무효화
PlayerHealth.Instance.SetInvincible(true);
// 전환 완료 후 해제
PlayerHealth.Instance.SetInvincible(false);
```

---

## 구현 우선순위 (초보자용 순서)
1. **직접 텔레포트 (페이드 없음)** → 먼저 동작만 확인
2. **페이드 인/아웃 추가** → CanvasGroup.alpha 코루틴
3. **문 잠금/해제 애니메이션** → Animator trigger
4. **카메라 경계 잠금** → SetRoomBounds 호출

---

## 참고 링크
- Unity Cinemachine Confiner 2D: https://docs.unity3d.com/Packages/com.unity.cinemachine@2.9/manual/CinemachineConfiner2D.html
- Unity SceneManager (씬 전환과 혼동 주의): https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
- CanvasGroup for Fade: https://docs.unity3d.com/ScriptReference/CanvasGroup.html
- Enter the Gungeon 룸 전환 분석 영상: YouTube "Enter the Gungeon room transition"
