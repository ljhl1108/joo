# 앱 라이프사이클 & 자동 저장 시스템 (Application Lifecycle & Auto-Save)

리서치 날짜: 2026-08-01

## 개요

"세이브/로드 시스템"이 저장 파일의 구조와 읽기/쓰기 방법을 다룬다면,
이 문서는 **언제, 어떤 이유로 저장해야 하는가**와 **예기치 않은 앱 종료 시 데이터를 지키는 방법**을 다룬다.

### OnionCat에서 왜 필요한가?
- Alt+F4(PC), 홈 버튼(모바일), 배터리 방전(모바일) 등 예기치 않은 종료 시 런 진행 데이터를 보호해야 함
- 방 클리어 시점마다 자동 저장하면 게임 크래시 시 진행 손실 최소화
- Steam Deck / 슬립 모드 지원 시 반드시 OnApplicationFocus 처리 필요
- "게임을 이어서 하시겠습니까?" 팝업 구현에 필요

---

## Unity 구현 방법

### 1. Unity 앱 라이프사이클 이벤트

```csharp
// MonoBehaviour에서 수신 가능한 앱 이벤트들
public class AppLifecycleHandler : MonoBehaviour
{
    // 앱이 포커스를 얻거나 잃을 때 (Alt+Tab, 알림, 전화 등)
    void OnApplicationFocus(bool hasFocus)
    {
        if (!hasFocus)
        {
            // 포커스 잃음: 자동 저장
            AutoSaveManager.Instance.SaveNow();
        }
    }

    // 앱이 백그라운드로 가거나 돌아올 때 (모바일 홈 버튼)
    void OnApplicationPause(bool isPaused)
    {
        if (isPaused)
        {
            // 백그라운드 진입: 자동 저장
            AutoSaveManager.Instance.SaveNow();
        }
    }

    // 앱 종료 직전 (PC: Alt+F4 / 코드에서 Application.Quit())
    void OnApplicationQuit()
    {
        // 마지막 저장
        AutoSaveManager.Instance.SaveNow();
        // 런 중이면 "비정상 종료 플래그" 해제
        AppStateTracker.ClearDirtyFlag();
    }
}
```

> **주의**: `OnApplicationQuit`은 모바일에서 OS가 앱을 강제 종료할 때는 호출되지 않음. 따라서 모바일은 `OnApplicationPause`가 주 자동 저장 타이밍.

### 2. 자동 저장 매니저

```csharp
public class AutoSaveManager : MonoBehaviour
{
    public static AutoSaveManager Instance { get; private set; }

    [SerializeField] private float autoSaveIntervalSeconds = 60f;
    private float nextAutoSave;
    private bool isDirty = false;   // 저장이 필요한 변경사항 여부

    void Awake() => Instance = this;

    void Update()
    {
        if (isDirty && Time.time >= nextAutoSave)
            SaveNow();
    }

    public void MarkDirty()
    {
        isDirty = true;
        nextAutoSave = Time.time + autoSaveIntervalSeconds;
    }

    public void SaveNow()
    {
        if (!isDirty) return;
        SaveLoadManager.Instance.SaveRunState();   // 실제 저장 로직
        isDirty = false;
    }
}

// 사용: 방 클리어 후, 아이템 획득 후 등에서 호출
// AutoSaveManager.Instance.MarkDirty();
```

### 3. 비정상 종료 감지 (Dirty Flag)

```csharp
public static class AppStateTracker
{
    private const string KEY = "app_dirty_flag";

    // 런 시작 시 호출 → "런 진행 중" 플래그 설정
    public static void SetDirtyFlag()
    {
        PlayerPrefs.SetInt(KEY, 1);
        PlayerPrefs.Save();
    }

    // 정상 런 종료 시 (게임 오버, 클리어, 메뉴 복귀) 호출
    public static void ClearDirtyFlag()
    {
        PlayerPrefs.SetInt(KEY, 0);
        PlayerPrefs.Save();
    }

    // 앱 시작 시 이전 런이 비정상 종료됐는지 확인
    public static bool WasAbnormallyTerminated()
        => PlayerPrefs.GetInt(KEY, 0) == 1;
}
```

### 4. 이어하기 팝업 (재시작 시 확인 다이얼로그)

```csharp
public class GameStartHandler : MonoBehaviour
{
    [SerializeField] private GameObject resumePopup;

    void Start()
    {
        if (AppStateTracker.WasAbnormallyTerminated()
            && SaveLoadManager.Instance.HasSavedRunState())
        {
            resumePopup.SetActive(true);
        }
    }

    // "이어하기" 버튼
    public void OnResumeClicked()
    {
        AppStateTracker.SetDirtyFlag();   // 다시 플래그 설정
        SaveLoadManager.Instance.LoadRunState();
        SceneManager.LoadScene("GameScene");
    }

    // "새 런" 버튼
    public void OnNewRunClicked()
    {
        AppStateTracker.ClearDirtyFlag();
        SaveLoadManager.Instance.ClearRunState();
        SceneManager.LoadScene("GameScene");
    }
}
```

### 5. PC 종료 확인 다이얼로그

Unity PC 빌드에서 Alt+F4 또는 창 닫기 버튼을 가로채려면
별도 플러그인 또는 `Application.wantsToQuit` 이벤트를 사용:

```csharp
public class QuitConfirmHandler : MonoBehaviour
{
    [SerializeField] private GameObject quitConfirmUI;
    private bool isQuitting = false;

    void OnEnable()
    {
        Application.wantsToQuit += OnWantsToQuit;
    }

    void OnDisable()
    {
        Application.wantsToQuit -= OnWantsToQuit;
    }

    bool OnWantsToQuit()
    {
        if (isQuitting) return true;   // 두 번째 호출 시 실제 종료

        // 런 중일 때만 확인 다이얼로그 표시
        if (GameStateManager.Instance.IsRunActive())
        {
            quitConfirmUI.SetActive(true);
            AutoSaveManager.Instance.SaveNow();   // 다이얼로그 표시 전 저장 먼저
            return false;   // 종료 취소
        }
        return true;
    }

    public void ConfirmQuit()
    {
        isQuitting = true;
        Application.Quit();
    }
}
```

### 6. 저장 파일 원자적 쓰기 (데이터 손상 방지)

갑작스러운 종료 시 파일 쓰기 도중 끊기면 저장 파일이 손상될 수 있음:

```csharp
public static void SafeWrite(string path, string json)
{
    string tempPath = path + ".tmp";
    File.WriteAllText(tempPath, json);          // 1. 임시 파일에 먼저 씀
    if (File.Exists(path)) File.Delete(path);   // 2. 기존 파일 삭제
    File.Move(tempPath, path);                  // 3. 임시 파일 → 실제 경로로 이동 (원자적)
}
```

---

## OnionCat 적용 포인트

### 자동 저장 트리거 타이밍

| 타이밍 | 이유 |
|--------|------|
| 방 클리어 시 | 가장 자연스러운 체크포인트 |
| 아이템 획득 시 | 빌드 변화 보존 |
| 층 이동 시 | 층 간 전환 = 큰 진행 지점 |
| OnApplicationPause/Focus | 플랫폼 필수 |

### 런 데이터 vs 영구 데이터 저장 구분

```
런 데이터 (RunState.json) — 비정상 종료 대비 자동 저장 대상
  └── 현재 HP, 보유 아이템, 현재 층, 방 위치, 런 번호

영구 데이터 (Persistent.json) — 런 종료 시 저장, 자동 저장 불필요
  └── 총 런 횟수, 최고 기록, 해금된 캐릭터, 설정값
```

### 모바일 대응 시 주의 (향후 확장 시)

- `OnApplicationPause(true)` 시 모든 코루틴이 일시 정지됨 → 저장 로직을 코루틴 없이 동기적으로 실행
- `PlayerPrefs.Save()` 반드시 명시적 호출 (모바일에서 앱 강종 시 자동 플러시 안 될 수 있음)
- iOS: 앱이 백그라운드에서 최대 ~5초 후 OS가 강제 종료 가능 → 저장 로직을 최대 2초 내 완료

---

## 참고 링크

- Unity 공식 — OnApplicationQuit: https://docs.unity3d.com/ScriptReference/MonoBehaviour.OnApplicationQuit.html
- Unity 공식 — OnApplicationPause: https://docs.unity3d.com/ScriptReference/MonoBehaviour.OnApplicationPause.html
- Unity 공식 — Application.wantsToQuit: https://docs.unity3d.com/ScriptReference/Application-wantsToQuit.html
- Unity 공식 — PlayerPrefs.Save: https://docs.unity3d.com/ScriptReference/PlayerPrefs.Save.html
- 원자적 파일 쓰기 패턴 (Game Dev SE): https://gamedev.stackexchange.com/questions/174248/how-to-prevent-save-file-corruption
