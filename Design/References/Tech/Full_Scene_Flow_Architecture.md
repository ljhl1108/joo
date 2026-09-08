# 씬 전체 흐름 통합 아키텍처 (Full Scene Flow Architecture)

리서치 날짜: 2026-09-08

## 개요

로그라이크 게임을 완성하려면 개별 씬을 만드는 것보다 **씬을 올바른 순서와 데이터 흐름으로 연결하는 것**이 더 어렵다. 대부분의 초보 개발자는 각 씬을 독립적으로 만들다가 씬 전환 시 데이터 소실, 뒤로 가기 처리 누락, SceneManager 문자열 오타 등의 문제를 겪는다.

이 문서는 OnionCat의 전체 씬 흐름을 하나의 구조로 정리하고, Unity 구현 코드 패턴을 제공한다.

---

## OnionCat 씬 흐름 맵

```
[Splash Screen]
       ↓ (1~2초 후 자동 전환)
[Main Menu]
   ↓ 시작          ↓ 종료
[Game Scene]    [앱 종료]
   ↓ ESC
[Pause Menu] ← → [재개]
   ↓ 재시작            ↓ 메인메뉴
[Game Scene]        [Main Menu]
   ↓ 양쪽 HP=0
[Game Over]
   ↓ 재시작            ↓ 메인메뉴
[Game Scene]        [Main Menu]
   
[Run Result Screen]  ← 보스 처치 클리어 시
   ↓ 메인메뉴
[Main Menu]
```

---

## Unity 구현 방법

### Step 1: 씬 이름 상수 클래스

```csharp
// SceneNames.cs — 문자열 오타 방지
public static class SceneNames
{
    public const string Splash    = "SplashScene";
    public const string MainMenu  = "MainMenuScene";
    public const string Game      = "GameScene";
    public const string GameOver  = "GameOverScene";
    public const string RunResult = "RunResultScene";
}
```

`SceneNames.Game`처럼 타입 안전하게 씬 이름 관리 → Build Settings 씬 순서와 일치시킬 것.

---

### Step 2: 씬 전환 매니저 (SceneFlowController)

```csharp
// SceneFlowController.cs
using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;

public class SceneFlowController : MonoBehaviour
{
    private static SceneFlowController _instance;
    public static SceneFlowController Instance => _instance;

    [SerializeField] private CanvasGroup _fadePanel; // 전체화면 검은 패널
    [SerializeField] private float _fadeDuration = 0.4f;

    void Awake()
    {
        if (_instance != null) { Destroy(gameObject); return; }
        _instance = this;
        DontDestroyOnLoad(gameObject);
    }

    // 공개 API
    public void GoToMainMenu()   => StartCoroutine(LoadScene(SceneNames.MainMenu));
    public void StartGame()      => StartCoroutine(LoadScene(SceneNames.Game));
    public void ShowGameOver()   => StartCoroutine(LoadScene(SceneNames.GameOver));
    public void ShowRunResult()  => StartCoroutine(LoadScene(SceneNames.RunResult));
    public void RestartGame()    => StartCoroutine(LoadScene(SceneNames.Game));

    private IEnumerator LoadScene(string sceneName)
    {
        // 페이드 아웃
        yield return StartCoroutine(Fade(0f, 1f));
        
        // 씬 로드
        AsyncOperation op = SceneManager.LoadSceneAsync(sceneName);
        op.allowSceneActivation = false;
        while (op.progress < 0.9f) yield return null;
        op.allowSceneActivation = true;
        yield return null; // 한 프레임 대기
        
        // 페이드 인
        yield return StartCoroutine(Fade(1f, 0f));
    }

    private IEnumerator Fade(float from, float to)
    {
        float elapsed = 0f;
        _fadePanel.alpha = from;
        _fadePanel.gameObject.SetActive(true);
        while (elapsed < _fadeDuration)
        {
            elapsed += Time.unscaledDeltaTime; // Pause 중에도 동작
            _fadePanel.alpha = Mathf.Lerp(from, to, elapsed / _fadeDuration);
            yield return null;
        }
        _fadePanel.alpha = to;
        if (to == 0f) _fadePanel.gameObject.SetActive(false);
    }
}
```

**유니티 에디터에서 드래그 앤 드롭 설정 필요:**
- `SceneFlowController` 오브젝트를 Bootstrap Scene에 배치
- `_fadePanel`에 Canvas > Image (검은색) CanvasGroup 컴포넌트가 달린 패널 할당

---

### Step 3: Bootstrap Scene 설정 (씬 초기화)

```
Build Settings 씬 순서:
  0: BootstrapScene  ← 게임 시작 시 가장 먼저 로드
  1: SplashScene
  2: MainMenuScene
  3: GameScene
  4: GameOverScene
  5: RunResultScene
```

```csharp
// BootstrapLoader.cs (Bootstrap Scene에 배치)
using UnityEngine;
using UnityEngine.SceneManagement;

public class BootstrapLoader : MonoBehaviour
{
    void Start()
    {
        // SceneFlowController, AudioManager, RunDataManager 등이
        // DontDestroyOnLoad로 초기화된 후 스플래시 씬으로 이동
        SceneFlowController.Instance.GoToSplash();
    }
}
```

---

### Step 4: 일시정지 오버레이 (씬 전환 없이 처리)

Pause Menu는 별도 씬이 아닌 **같은 Game Scene 내의 UI Panel**로 구현하는 것이 권장된다.

```csharp
// PauseController.cs
public class PauseController : MonoBehaviour
{
    [SerializeField] private GameObject _pausePanel;

    void Update()
    {
        // New Input System: 둘 중 하나가 ESC/Start 누르면
        if (PlayerInput.all.Count > 0 && /* 입력 감지 */ false)
            TogglePause();
    }

    public void TogglePause()
    {
        bool isPaused = !_pausePanel.activeSelf;
        _pausePanel.SetActive(isPaused);
        Time.timeScale = isPaused ? 0f : 1f;
    }

    public void OnResumeClicked()  => TogglePause();
    public void OnRestartClicked() { Time.timeScale = 1f; SceneFlowController.Instance.RestartGame(); }
    public void OnMainMenuClicked(){ Time.timeScale = 1f; SceneFlowController.Instance.GoToMainMenu(); }
}
```

---

### Step 5: 씬 간 데이터 전달 (RunData)

씬이 전환되면 지역 변수는 모두 사라진다. 런 데이터는 DontDestroyOnLoad 오브젝트나 ScriptableObject에 보관.

```csharp
// RunData.cs — DontDestroyOnLoad 싱글톤
public class RunData : MonoBehaviour
{
    public static RunData Instance { get; private set; }
    
    // 씬 전환 후에도 유지되는 런 데이터
    public int KillCount;
    public float RunTimeSeconds;
    public int TotalDamageDealt;
    public List<string> AcquiredUpgrades = new();
    public bool IsClear;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void ResetForNewRun()
    {
        KillCount = 0;
        RunTimeSeconds = 0f;
        TotalDamageDealt = 0;
        AcquiredUpgrades.Clear();
        IsClear = false;
    }
}
```

Game Scene에서 데이터 기록 → Game Over / Run Result Scene에서 읽기.

---

## OnionCat 적용 포인트

### 1. 씬 흐름 구현 우선순위 (초보 개발자용 추천 순서)

1. `SceneNames.cs` 상수 클래스 먼저 만들기 (10분)
2. Bootstrap Scene 구성 + `SceneFlowController` 배치 (30분)
3. MainMenu → Game 전환 연결 (30분)
4. Game → GameOver 전환 연결 (20분)
5. Pause Menu 오버레이 연결 (20분)
6. Run Result Scene 연결 (20분)

**총 약 2시간으로 전체 씬 흐름 완성 가능.**

### 2. 2인 협력 특이사항

- Pause: **두 컨트롤러 중 하나라도** Start/ESC 누르면 일시정지
- Game Over: **두 플레이어 HP 모두 0**일 때 트리거 (한 명만 죽으면 부활 시스템 가동)
- 재시작: `RunData.ResetForNewRun()` 호출 필수 → 이전 런 통계 초기화

### 3. 흔한 초보 실수

| 실수 | 해결책 |
|------|--------|
| Pause 중 페이드 애니메이션 안 되는 경우 | `Time.unscaledDeltaTime` 사용 |
| 씬 전환 후 BGM이 두 번 재생 | AudioManager도 DontDestroyOnLoad |
| 재시작 시 이전 런 데이터 남아있음 | `RunData.ResetForNewRun()` 호출 확인 |
| 씬 이름 오타로 런타임 크래시 | `SceneNames.cs` 상수 사용 |
| Game Over씬에서 RunData 없음 | RunData도 DontDestroyOnLoad 확인 |

---

## 참고 링크

- [Unity SceneManager 공식 문서](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html)
- [Unity AsyncOperation.allowSceneActivation 문서](https://docs.unity3d.com/ScriptReference/AsyncOperation-allowSceneActivation.html)
- [DontDestroyOnLoad 공식 문서](https://docs.unity3d.com/ScriptReference/Object.DontDestroyOnLoad.html)
- [Game Architecture with ScriptableObjects — Unite 2017 (Ryan Hipple)](https://www.youtube.com/watch?v=raQ3iHhE_Kk)
- [Bootstrap Pattern in Unity — Jason Weimann](https://www.youtube.com/results?search_query=unity+bootstrap+scene+pattern)
