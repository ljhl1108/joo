# 디버그 & 치트 시스템 (Debug & Cheat System)

리서치 날짜: 2026-06-16

## 개요

로그라이크 게임 개발에서 디버그 도구는 필수다. 매 런마다 처음부터 플레이해야 특정 상황을 테스트할 수 있다면 개발 속도가 급격히 저하된다. 빠른 이동, 무적 모드, 아이템 스폰, 특정 방 직접 이동 등의 치트 시스템을 개발 빌드에 내장해 테스트 사이클을 단축한다. OnionCat처럼 초보 개발자가 만드는 게임에서 특히 중요하다.

---

## Unity 구현 방법

### 1. 개발 빌드 전용 조건부 컴파일

```csharp
// 에디터 + 개발 빌드에서만 활성화
#if UNITY_EDITOR || DEVELOPMENT_BUILD
    // 치트 코드 실행
#endif
```

또는 `Debug.isDebugBuild` 체크:
```csharp
private void Update()
{
    if (!Debug.isDebugBuild) return;
    HandleCheatInput();
}
```

### 2. 기본 치트 매니저 구조

```csharp
public class CheatManager : MonoBehaviour
{
    public static CheatManager Instance { get; private set; }
    
    [Header("Cheat State")]
    public bool isGodMode = false;
    public bool isSpeedBoost = false;
    
    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }
    
    private void Update()
    {
#if UNITY_EDITOR || DEVELOPMENT_BUILD
        HandleCheatInput();
#endif
    }
    
    private void HandleCheatInput()
    {
        // 무적 모드 토글
        if (Input.GetKeyDown(KeyCode.F1))
            ToggleGodMode();
        
        // 모든 적 즉사
        if (Input.GetKeyDown(KeyCode.F2))
            KillAllEnemies();
        
        // 업그레이드 아이템 스폰
        if (Input.GetKeyDown(KeyCode.F3))
            SpawnUpgradeItem();
        
        // 다음 방으로 이동
        if (Input.GetKeyDown(KeyCode.F4))
            SkipToNextRoom();
        
        // 스피드 부스트 토글
        if (Input.GetKeyDown(KeyCode.F5))
            ToggleSpeedBoost();
    }
    
    private void ToggleGodMode()
    {
        isGodMode = !isGodMode;
        Debug.Log($"[CHEAT] God Mode: {isGodMode}");
    }
    
    private void KillAllEnemies()
    {
        var enemies = FindObjectsOfType<EnemyBase>();
        foreach (var e in enemies) e.TakeDamage(99999);
        Debug.Log($"[CHEAT] Killed {enemies.Length} enemies");
    }
    
    private void SpawnUpgradeItem()
    {
        // 플레이어 위치에 랜덤 업그레이드 아이템 생성
        Vector3 pos = PlayerController.Instance.transform.position + Vector3.right * 2f;
        ItemSpawner.Instance.SpawnRandom(pos);
        Debug.Log("[CHEAT] Spawned upgrade item");
    }
    
    private void SkipToNextRoom()
    {
        RoomManager.Instance.ForceCompleteCurrentRoom();
        Debug.Log("[CHEAT] Skipped to next room");
    }
    
    private void ToggleSpeedBoost()
    {
        isSpeedBoost = !isSpeedBoost;
        Debug.Log($"[CHEAT] Speed Boost: {isSpeedBoost}");
    }
}
```

### 3. 플레이어 컨트롤러에 치트 적용

```csharp
// PlayerController.cs의 이동 속도 계산 부분
private float GetCurrentSpeed()
{
    float speed = baseSpeed;
#if UNITY_EDITOR || DEVELOPMENT_BUILD
    if (CheatManager.Instance != null && CheatManager.Instance.isSpeedBoost)
        speed *= 3f;
#endif
    return speed;
}

// Health 시스템에 무적 적용
public void TakeDamage(int amount)
{
#if UNITY_EDITOR || DEVELOPMENT_BUILD
    if (CheatManager.Instance != null && CheatManager.Instance.isGodMode)
        return;
#endif
    currentHealth -= amount;
    // ... 나머지 처리
}
```

### 4. 인게임 디버그 UI (IMGUI 방식)

간단한 GUI로 상태 표시:

```csharp
public class DebugOverlay : MonoBehaviour
{
    private void OnGUI()
    {
#if UNITY_EDITOR || DEVELOPMENT_BUILD
        GUIStyle style = new GUIStyle(GUI.skin.label);
        style.fontSize = 14;
        style.normal.textColor = Color.yellow;
        
        float y = 10f;
        float lineH = 20f;
        
        GUI.Label(new Rect(10, y, 300, lineH), 
            $"FPS: {(int)(1f / Time.deltaTime)}", style);
        y += lineH;
        
        GUI.Label(new Rect(10, y, 300, lineH), 
            $"Room: {RoomManager.Instance?.CurrentRoomName ?? "N/A"}", style);
        y += lineH;
        
        if (CheatManager.Instance != null)
        {
            if (CheatManager.Instance.isGodMode)
            {
                style.normal.textColor = Color.red;
                GUI.Label(new Rect(10, y, 300, lineH), "[GOD MODE ON]", style);
                y += lineH;
            }
        }
#endif
    }
}
```

### 5. 씬 빠른 시작 (개발용)

게임을 Play할 때 항상 메인메뉴를 거치지 않고 특정 씬에서 바로 시작:

```csharp
// RuntimeInitializeOnLoadMethod 활용
public static class DevQuickStart
{
#if UNITY_EDITOR
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void OnBeforeSceneLoad()
    {
        // 에디터에서 Play 시 Game 씬이 아닌 경우 필요한 초기화 수행
        var currentScene = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name;
        if (currentScene != "MainMenu" && currentScene != "Boot")
        {
            // 전역 매니저 프리팹 인스턴스화 (없는 경우)
            if (GameManager.Instance == null)
            {
                var prefab = Resources.Load<GameObject>("Managers/GameManager");
                if (prefab != null) Instantiate(prefab);
            }
        }
    }
#endif
}
```

### 6. 치트 코드 목록 예시 (OnionCat 기준)

| 키 | 기능 |
|----|------|
| F1 | 무적 모드 토글 |
| F2 | 현재 방 모든 적 즉사 |
| F3 | 랜덤 업그레이드 아이템 스폰 |
| F4 | 다음 방으로 강제 진행 |
| F5 | 이동속도 3배 토글 |
| F6 | Cat HP 최대 회복 |
| F7 | 현재 런 스탯 콘솔 출력 |
| F8 | 보스 방으로 직행 |
| Ctrl+R | 런 재시작 |

---

## OnionCat 적용 포인트

### 1. 협동 테스트 가속
- 2인 협동 게임 테스트는 혼자 하기 어렵다
- F1(무적) + F5(스피드) → 혼자서도 빠르게 방 진행 테스트 가능
- F2(적 즉사) → 방 클리어 로직, 문 열림, 다음 방 전환 빠르게 테스트

### 2. 업그레이드 시스템 테스트
- F3으로 아이템 스폰 → 특정 업그레이드 획득 후 전투 느낌 바로 확인
- 여러 번 F3 연타 → 강한 빌드 상태에서 후반 방 밸런스 테스트

### 3. CheatManager 씬 배치
- `GameScene`에 `CheatManager` GameObject 배치
- `DontDestroyOnLoad` 적용 → 방 전환 시에도 유지
- **에디터에서 Inspector로 `isGodMode` 체크박스 직접 토글 가능** (가장 편한 방법)

### 4. 배포 시 자동 제거
- `#if UNITY_EDITOR || DEVELOPMENT_BUILD` 사용 시 **Release 빌드에서 자동 제거**
- File > Build Settings에서 `Development Build` 체크 해제 → 치트 코드 비활성화
- 별도 작업 불필요

### 5. 디버그 오버레이
- FPS, 현재 방 이름, 플레이어 체력 수치를 화면 왼쪽 상단에 표시
- 개발 중 성능 문제 빠른 감지

---

## 참고 링크

- Unity IMGUI 문서: https://docs.unity3d.com/Manual/GUIScriptingGuide.html
- Unity 조건부 컴파일 (#if): https://docs.unity3d.com/Manual/PlatformDependentCompilation.html
- RuntimeInitializeOnLoadMethod: https://docs.unity3d.com/ScriptReference/RuntimeInitializeOnLoadMethodAttribute.html
- Debug.isDebugBuild: https://docs.unity3d.com/ScriptReference/Debug-isDebugBuild.html
