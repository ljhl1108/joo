# 앱 부트 순서 & 초기화 관리 (App Boot Sequence)

리서치 날짜: 2026-08-04

## 개요

Unity 프로젝트에서 씬이 시작될 때 스크립트 초기화 순서를 제어하지 않으면, 싱글톤이 아직 생성되지 않은 상태에서 다른 스크립트가 접근하거나, 세이브 데이터 로드 전에 게임플레이가 시작되는 문제가 발생한다.

**OnionCat에서 왜 중요한가?**
- GameManager, AudioManager, InputManager 등이 있을 때 초기화 순서가 뒤섞이면 NullReferenceException 발생
- 메인 메뉴 씬 진입 전에 세이브 데이터, 설정, 리소스가 모두 로드되어야 함
- 2인 입력 시스템 초기화가 게임플레이보다 먼저 완료되어야 함

---

## Unity 구현 방법

### 1. Script Execution Order 설정

**Project Settings → Script Execution Order** 에서 순서 지정:
- 기본값 0. 숫자가 낮을수록 먼저 실행.

권장 순서 (OnionCat 기준):
```
-1000: BootManager         (최우선 초기화)
 -100: GameManager
  -50: AudioManager
  -20: InputManager
    0: (기타 스크립트)
  100: UIManager            (나중에 초기화)
```

Unity 에디터에서 설정하거나, 코드로:
```csharp
// 이 방법은 사용 불가 (에디터 전용)
// 코드로는 [DefaultExecutionOrder] 어트리뷰트 사용
[DefaultExecutionOrder(-1000)]
public class BootManager : MonoBehaviour { }
```

### 2. RuntimeInitializeOnLoadMethod — 씬 없이 실행

씬보다 먼저 실행되어야 하는 코드에 사용:

```csharp
public static class GameBootstrapper
{
    // 씬 로드 전에 실행 (가장 빠름)
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
    private static void InitializeBeforeScene()
    {
        Debug.Log("[Boot] Before Scene Load");
        // 여기서 리소스 로드, 설정 파싱 등 가능
        LoadSettings();
    }

    // 첫 씬 Awake() 후, Start() 전에 실행
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void InitializeAfterScene()
    {
        Debug.Log("[Boot] After Scene Load");
    }

    private static void LoadSettings()
    {
        // PlayerPrefs 읽기 or JSON 파싱
        int masterVolume = PlayerPrefs.GetInt("MasterVolume", 100);
        AudioListener.volume = masterVolume / 100f;
    }
}
```

### 3. BootScene 전용 씬 패턴 (권장)

프로젝트에 `BootScene`을 추가 (빌드 씬 목록의 Index 0):

```
빌드 씬 순서:
0: BootScene    ← 항상 처음 로드
1: MainMenu
2: Game
3: ...
```

```csharp
// BootScene에 존재하는 유일한 스크립트
public class BootManager : MonoBehaviour
{
    private IEnumerator Start()
    {
        // 1. 싱글톤 초기화 (DontDestroyOnLoad 오브젝트들)
        yield return StartCoroutine(InitializeSingletons());
        
        // 2. 세이브 데이터 로드
        yield return StartCoroutine(SaveSystem.LoadAsync());
        
        // 3. 에셋 프리로드 (필요시)
        yield return StartCoroutine(PreloadAssets());
        
        // 4. 메인 메뉴로 이동
        SceneManager.LoadScene("MainMenu");
    }

    private IEnumerator InitializeSingletons()
    {
        // 순서대로 초기화 보장
        GameManager.Initialize();
        yield return null;
        AudioManager.Initialize();
        yield return null;
        InputManager.Initialize();
        yield return null;
    }

    private IEnumerator PreloadAssets()
    {
        var handle = Addressables.LoadAssetsAsync<Sprite>("UI", null);
        yield return handle;
    }
}
```

### 4. DontDestroyOnLoad 싱글톤 패턴

```csharp
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public static void Initialize()
    {
        if (Instance != null) return;
        
        // Resources에서 프리팹 로드하여 인스턴스 생성
        var prefab = Resources.Load<GameManager>("Prefabs/GameManager");
        Instantiate(prefab);
    }
}
```

### 5. 초기화 완료 이벤트

```csharp
public static class BootEvents
{
    public static event Action OnBootComplete;
    
    public static void NotifyBootComplete()
    {
        OnBootComplete?.Invoke();
    }
}

// 사용
public class MainMenuController : MonoBehaviour
{
    private void OnEnable()
    {
        // 부팅 완료 전에는 UI 비활성화
        BootEvents.OnBootComplete += EnableUI;
    }
    
    private void EnableUI()
    {
        GetComponent<CanvasGroup>().alpha = 1f;
    }
}
```

---

## OnionCat 적용 포인트

### 권장 씬 구조

```
BootScene (Index 0)
  └── BootManager.cs
      ├── GameManager (DontDestroyOnLoad)
      ├── AudioManager (DontDestroyOnLoad)  
      ├── InputManager (DontDestroyOnLoad)  ← 2인 입력 초기화
      └── SaveSystem 로드

MainMenuScene (Index 1)
  └── 메뉴 UI만 존재 (싱글톤은 이미 초기화됨)

GameScene (Index 2)
  └── 방 시스템, 적, 플레이어
```

### OnionCat 초기화 체크리스트

| 순서 | 항목 | 이유 |
|------|------|------|
| 1 | 설정 로드 (볼륨, 해상도) | UI 뜨기 전에 적용 필요 |
| 2 | 세이브 데이터 로드 | 메타 진행도, 잠금 해제 |
| 3 | 로컬 2인 입력 초기화 | Player 1(키보드) + Player 2(마우스) |
| 4 | 오디오 시스템 | BGM이 메뉴와 함께 시작 |
| 5 | 씬 전환 (MainMenu) | 모든 초기화 완료 후 |

### 주의사항
1. `DontDestroyOnLoad` 오브젝트가 많아지면 씬 전환 후 중복 생성 문제 발생 → 반드시 `Instance != null` 체크
2. BootScene은 최대한 가볍게: 이미지/사운드 없이 단순 초기화만
3. 빌드 시 BootScene이 반드시 Index 0에 있는지 확인 (File → Build Settings)
4. Editor에서 GameScene을 직접 열어 플레이 테스트할 때 싱글톤이 없는 경우를 대비한 null 체크 필요

---

## 참고 링크

- Unity 공식 — Script Execution Order: https://docs.unity3d.com/Manual/class-MonoManager.html
- Unity 공식 — RuntimeInitializeOnLoadMethod: https://docs.unity3d.com/ScriptReference/RuntimeInitializeOnLoadMethodAttribute.html
- Game Architecture with ScriptableObjects (GDC 2017): https://www.gdcvault.com/play/1024084
- Unity Best Practices — DontDestroyOnLoad: https://docs.unity3d.com/Manual/BestPracticeUnderstandingPerformanceInUnity2.html
