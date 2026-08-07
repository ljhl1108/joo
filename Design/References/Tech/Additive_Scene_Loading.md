# Additive Scene Loading (애디티브 씬 로딩)

리서치 날짜: 2026-08-07

## 개요

Unity의 `LoadSceneAsync(Additive)` 모드를 활용해 하나의 씬을 항상 유지하면서 다른 씬을 위에 덮어 로드하는 기법.

일반적인 `LoadScene`(단일 씬 교체)과 달리:
- **Persistent Scene**: GameManager, AudioManager, EventBus 등 게임 전체 생명주기 오브젝트 유지
- **동적 씬**: Menu, Gameplay, UI 씬을 독립적으로 교체

OnionCat같은 로그라이크에서 런 중 씬 전환(방 이동, 게임오버 → 메뉴)을 깔끔하게 처리하는 프로 아키텍처.

---

## Unity 구현 방법

### 씬 구조 설계

```
Build Settings 씬 순서:
  0. _Persistent  ← 최초 로드, 절대 언로드 안됨 (GameManager, AudioManager 등)
  1. MainMenu
  2. Gameplay
  3. GameOver
  4. UI_HUD       ← HUD는 별도 씬으로 Gameplay와 함께 로드
```

### Persistent Scene 진입점 (Bootstrap)

```csharp
// _Persistent 씬에만 있는 부트스트랩
using UnityEngine;
using UnityEngine.SceneManagement;

public class GameBootstrap : MonoBehaviour
{
    [SerializeField] private string startScene = "MainMenu";

    void Start()
    {
        // Persistent 씬은 이미 로드됨(씬 0) — 메인메뉴를 위에 로드
        SceneManager.LoadSceneAsync(startScene, LoadSceneMode.Additive);
    }
}
```

### 씬 전환 매니저

```csharp
using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections;

public class SceneLoader : MonoBehaviour
{
    public static SceneLoader Instance { get; private set; }

    private string _currentScene;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);  // Persistent 씬에서 이미 유지되지만 명시
    }

    // 기존 씬 언로드 → 새 씬 로드
    public void LoadScene(string sceneName, string sceneToUnload = null)
    {
        StartCoroutine(LoadSceneRoutine(sceneName, sceneToUnload ?? _currentScene));
    }

    private IEnumerator LoadSceneRoutine(string toLoad, string toUnload)
    {
        // 1. 페이드 아웃 (FadeManager가 Persistent에 있다고 가정)
        yield return FadeManager.Instance?.FadeOut(0.3f);

        // 2. 새 씬 로드 (Additive)
        var loadOp = SceneManager.LoadSceneAsync(toLoad, LoadSceneMode.Additive);
        yield return loadOp;

        // 3. 구 씬 언로드
        if (!string.IsNullOrEmpty(toUnload))
        {
            var unloadOp = SceneManager.UnloadSceneAsync(toUnload);
            yield return unloadOp;
        }

        _currentScene = toLoad;

        // 4. 페이드 인
        yield return FadeManager.Instance?.FadeIn(0.3f);
    }
}
```

### 외부에서 호출 예시

```csharp
// 메인메뉴 → 게임플레이 진입
SceneLoader.Instance.LoadScene("Gameplay", "MainMenu");

// 게임플레이 → 게임오버
SceneLoader.Instance.LoadScene("GameOver", "Gameplay");

// 게임오버 → 메인메뉴 (재시작)
SceneLoader.Instance.LoadScene("MainMenu", "GameOver");
```

---

## 동시 로드 (Gameplay + UI_HUD)

```csharp
// 두 씬을 동시에 로드
IEnumerator LoadGameplay()
{
    yield return FadeManager.Instance?.FadeOut(0.3f);

    // 동시에 두 씬 로드
    var op1 = SceneManager.LoadSceneAsync("Gameplay", LoadSceneMode.Additive);
    var op2 = SceneManager.LoadSceneAsync("UI_HUD", LoadSceneMode.Additive);

    yield return op1;
    yield return op2;

    SceneManager.UnloadSceneAsync("MainMenu");

    yield return FadeManager.Instance?.FadeIn(0.3f);
}
```

---

## 씬 레퍼런스 찾기 (활성 씬 내 오브젝트)

Additive 로드 시 `FindObjectOfType`은 모든 씬에서 찾으므로 주의.
특정 씬의 오브젝트를 찾으려면:

```csharp
// 특정 씬의 루트 오브젝트 순회
Scene gameplayScene = SceneManager.GetSceneByName("Gameplay");
foreach (var go in gameplayScene.GetRootGameObjects())
{
    var spawner = go.GetComponent<RoomSpawner>();
    if (spawner != null) { /* 사용 */ }
}
```

---

## OnionCat 적용 포인트

### 씬 구조 제안

```
_Persistent (씬 0 — 항상 로드)
├── GameManager          ← 런 상태 (현재 룸, 플레이어 체력 등)
├── AudioManager         ← BGM 유지 (씬 전환 중 음악 끊김 없음)
├── EventBus             ← 씬 간 이벤트 통신
├── SceneLoader          ← 씬 전환 제어
└── FadeManager          ← 페이드 인/아웃 캔버스

MainMenu (씬 1)
Gameplay (씬 2)          ← 룸 생성, 플레이어, 적 등
UI_HUD (씬 3)            ← HP 바, 아이템 슬롯, 쿨다운 UI
GameOver (씬 4)
RunResult (씬 5)
```

### 런 흐름 (씬 전환)

```
앱 시작
→ _Persistent 로드 (자동)
→ MainMenu 로드 (Additive)

[게임 시작]
→ MainMenu 언로드
→ Gameplay + UI_HUD 동시 로드 (Additive)

[게임오버]
→ Gameplay 언로드 + UI_HUD 언로드
→ GameOver 로드 (Additive)
   (AudioManager는 Persistent에 있어 BGM 자연스럽게 전환)

[재시작]
→ GameOver 언로드
→ Gameplay + UI_HUD 다시 로드
→ GameManager.ResetRun() 호출
```

### 중요한 함정과 해결책

| 함정 | 해결책 |
|------|--------|
| Additive 로드 시 활성 씬이 여러 개 → Physics가 어느 씬에서 생성될지 불명확 | `SceneManager.SetActiveScene()`으로 활성 씬 명시 |
| DontDestroyOnLoad 오브젝트와 Persistent 씬 오브젝트 중복 | Persistent 씬에 놓고 DontDestroyOnLoad 사용 금지 |
| UI Canvas가 여러 씬에 있을 때 레이캐스트 충돌 | UI 씬 분리 후 GraphicRaycaster 씬별 관리 |
| 씬 언로드 중 Coroutine이 살아있어 에러 | 씬 언로드 전 GameManager에서 씬 관련 Coroutine 전부 중단 |

---

## 참고 링크

- Unity LoadSceneAsync 공식 문서: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadSceneAsync.html
- Additive Scene Loading 패턴 (Unity Blog): https://unity.com/how-to/use-additive-scene-loading
- 씬 관리 아키텍처 (GameDev.tv): https://www.gamedev.tv/courses/unity-game-dev-advanced-topics/lectures/additive-scenes
- Bootstrap 패턴 설명: https://stackoverflow.com/questions/35890932/unity-game-manager-script-work-with-every-scene
