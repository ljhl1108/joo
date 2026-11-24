# Softlock Prevention System (소프트락 방지 시스템)

리서치 날짜: 2026-11-24

## 개요

소프트락(soft lock)이란 게임이 종료되지 않고 계속 실행되지만 플레이어가 더 이상 진행할 수 없는 상태다. 로그라이크에서는 특히 흔하다: 적이 맵 경계 밖에 떨어져 방이 클리어 불가, 플레이어가 지형에 끼어 움직임 불가, 보스가 무한 무적 상태, 문이 열려야 하는데 조건이 충족되지 않음 등. OnionCat처럼 절차적으로 생성되는 방이 있고 비대칭 2인 조작이 있는 게임은 소프트락 경우의 수가 더 많다. 출시 전에 체계적으로 대비해야 한다.

---

## 소프트락 유형별 원인 분석 (OnionCat 기준)

| 유형 | 원인 | 증상 |
|---|---|---|
| **적 소실** | 적이 구덩이(`Pit`)에 빠졌는데 체력이 아직 남음, 적이 맵 경계 밖으로 이동 | 방 클리어 조건 미달 → 문이 안 열림 |
| **문 고장** | 방 클리어 이벤트 누락, `GameState` 전환 실패 | 적 없는데 문이 잠김 |
| **플레이어 끼임** | 타일맵 모서리, 방이 새로 생성되면서 충돌체 겹침 | 움직임 불가 |
| **보스 무한 루프** | 보스 페이즈 전환 버그, 무적 상태 해제 실패 | 보스 체력이 0인데 죽지 않음 |
| **씬 전환 실패** | 문 판정 버그, 비동기 로드 중 입력 발생 | 화면이 그대로 멈춤 |
| **공동 협동 교착** | 한 플레이어 입력 장치 연결 끊김 → 진행 불가 화면 | 게임 진행 멈춤 |

---

## Unity 구현 방법

### 1. RoomClearWatchdog — 방 클리어 타임아웃

```csharp
public class RoomClearWatchdog : MonoBehaviour
{
    [SerializeField] private float timeoutSeconds = 30f; // 적이 0마리인데 문이 안 열리면
    private float timer;
    private bool watchActive;

    private void OnEnable()
    {
        GameManager.OnStateChanged += OnStateChanged;
    }
    private void OnDisable()
    {
        GameManager.OnStateChanged -= OnStateChanged;
    }

    private void OnStateChanged(GameState state)
    {
        watchActive = (state == GameState.Combat);
        timer = 0f;
    }

    private void Update()
    {
        if (!watchActive) return;

        // 적이 없는데 클리어가 안 된 상태
        if (EnemyBase.Active.Count == 0)
        {
            timer += Time.deltaTime;
            if (timer >= timeoutSeconds)
            {
                Debug.LogWarning("[Watchdog] Room clear timeout — forcing door open");
                ForceRoomClear();
            }
        }
        else
        {
            timer = 0f;
        }
    }

    private void ForceRoomClear()
    {
        watchActive = false;
        // GameManager를 통해 강제로 클리어 상태로 전환
        GameManager.Instance.ChangeState(GameState.RoomClear);
    }
}
```

### 2. EnemyFallSafety — 구덩이 낙하 적 처리

```csharp
// EnemyBase.cs에 이미 있는 Pit 처리 로직에 추가
// 구덩이에 빠진 적이 있으면 즉시 Despawn하고 사망 처리

private void OnPitFall()
{
    // 현재: immuneToPits 체크 후 Launch로 처리
    // 추가: 구덩이에 빠진 적은 즉시 EnemyBase.Active에서 제거 보장
    EnemyBase.Active.Remove(this);
    PoolManager.Despawn(gameObject);
}
```

### 3. PlayerUnstuck — 플레이어 끼임 감지 & 탈출

```csharp
public class PlayerUnstuck : MonoBehaviour
{
    private Vector2 lastPosition;
    private float stuckTimer;
    [SerializeField] private float stuckThreshold = 0.05f;  // 이 거리 이하면 "안 움직임"
    [SerializeField] private float stuckTimeLimit = 3f;      // 3초 이상이면 끼인 것
    private bool inputActive;

    private void Update()
    {
        // 입력이 있는데 움직임이 없는 경우만 감지
        inputActive = GetComponent<CatController>().MoveInput.magnitude > 0.3f;

        if (inputActive)
        {
            float moved = Vector2.Distance(transform.position, lastPosition);
            if (moved < stuckThreshold)
            {
                stuckTimer += Time.deltaTime;
                if (stuckTimer >= stuckTimeLimit)
                {
                    TeleportToSafePosition();
                    stuckTimer = 0f;
                }
            }
            else
            {
                stuckTimer = 0f;
            }
        }

        lastPosition = transform.position;
    }

    private void TeleportToSafePosition()
    {
        // 방 중앙 쪽으로 살짝 이동
        Vector2 roomCenter = Vector2.zero; // DungeonManager에서 현재 방 중앙 가져오기
        Vector2 dir = (roomCenter - (Vector2)transform.position).normalized;
        transform.position = (Vector2)transform.position + dir * 2f;
        Debug.Log("[Unstuck] Player teleported away from stuck position");
    }
}
```

### 4. 비상 탈출 입력 (Hold-to-Skip)

```csharp
// 플레이어가 고의로 방을 건너뛰는 비상 탈출 (디버그용)
// 화면에 "ESC 5초 홀드 → 방 강제 종료" 표시 가능

public class EmergencyEscape : MonoBehaviour
{
    private float holdTime;
    [SerializeField] private float requiredHold = 5f;
    private bool escapeActive;

    private void Update()
    {
        if (Keyboard.current.escapeKey.isPressed)
        {
            holdTime += Time.deltaTime;
            if (!escapeActive && holdTime >= requiredHold)
            {
                escapeActive = true;
                ShowEscapeWarning();
            }
            if (holdTime >= requiredHold + 1f)
            {
                ExecuteEscape();
            }
        }
        else
        {
            holdTime = 0f;
            HideEscapeWarning();
        }
    }

    private void ExecuteEscape()
    {
        // 강제 클리어 → 다음 방으로 이동
        GameManager.Instance.ChangeState(GameState.RoomClear);
        Debug.LogWarning("[EmergencyEscape] Player used emergency escape");
    }
}
```

### 5. 보스 무적 타임아웃

```csharp
// BossBase.cs에 추가
private float invincibleTimer;
private const float MAX_INVINCIBLE_TIME = 10f;

private void Update()
{
    if (isInvincible)
    {
        invincibleTimer += Time.deltaTime;
        if (invincibleTimer >= MAX_INVINCIBLE_TIME)
        {
            Debug.LogWarning("[Boss] Invincibility timeout — force ending");
            isInvincible = false;
            invincibleTimer = 0f;
        }
    }
    else
    {
        invincibleTimer = 0f;
    }
}
```

### 6. 소프트락 로그 수집 (출시 후 버그 추적)

```csharp
// RoomClearWatchdog.ForceRoomClear()에 추가
private void LogSoftlockEvent(string reason)
{
    var log = new SoftlockLog
    {
        timestamp = DateTime.UtcNow.ToString(),
        reason = reason,
        roomId = DungeonManager.Instance.CurrentRoom?.id ?? "unknown",
        enemyCount = EnemyBase.Active.Count,
        gameState = GameManager.Instance.State.ToString()
    };

    // JSON으로 로컬 로그 파일에 추가
    var path = Path.Combine(Application.persistentDataPath, "softlock_log.json");
    // ... (실제 저장 코드는 Save/Load 시스템 활용)
}
```

---

## OnionCat 적용 포인트

### 가장 발생 가능성 높은 소프트락 (우선 대응 순서)

1. **구덩이에 적이 떨어졌는데 EnemyBase.Active에 남아있음**
   → `EnemyBase.Active.Remove(this)`를 Pit 처리와 Despawn 두 곳에서 모두 호출
   → `RoomClearWatchdog` 30초 타임아웃으로 최후 방어선

2. **GameManager.ChangeState()가 호출되지 않은 채 적 소멸**
   → 방 클리어 체크 로직에 `EnemyBase.Active.Count == 0` 조건을 프레임마다 확인하는 fallback 추가

3. **그려진 방(PaintedRoom)에서 플레이어 끼임**
   → `PaintedRoomImporter.Soften` 처리 후에도 좁은 통로에 끼는 경우 발생 가능
   → `PlayerUnstuck` 컴포넌트를 Cat에 부착

4. **비대칭 2인 조작에서 한 명이 조작 불능 화면에 묶임**
   → `CoopPauseMenu` 혹은 `UpgradeSelectUI` 등 "양쪽 확인 필요" 화면에 타임아웃 추가 (120초 후 자동 확인)

### 구현 우선순위

```
1순위 — RoomClearWatchdog + EnemyBase.Active 정합성
   (가장 흔한 소프트락, 가장 쉽게 구현 가능)

2순위 — PlayerUnstuck
   (그려진 방 추가 이후 필요성 증가)

3순위 — 비상 탈출 입력 (ESC 홀드)
   (QA·플레이테스터용으로 먼저 추가, 나중에 일반 플레이어에게도 공개 가능)

4순위 — 보스 무적 타임아웃
   (보스 패턴 확정 이후)
```

---

## 참고 링크

- Unity Event System: https://docs.unity3d.com/ScriptReference/Events.UnityEvent.html
- 로그라이크 버그 추적 사례 (Hades 개발자 GDC): https://www.gdcvault.com/play/1026462
- Physics2D OverlapPoint (안전 위치 찾기): https://docs.unity3d.com/ScriptReference/Physics2D.OverlapPoint.html
- 소프트락 UX 가이드 (Game Accessibility Guidelines): https://gameaccessibilityguidelines.com/
