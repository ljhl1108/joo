# 씬 전환 관리 심화 — 비동기 로딩 & 페이드 인/아웃

리서치 날짜: 2026-08-26

## 개요
Unity `SceneManager.LoadScene()`은 동기(Synchronous) 방식으로 씬을 로드해 **화면이 한 프레임
동안 멈추거나(히치)** 게임 오버/재시작 시 눈에 띄는 끊김이 발생한다. 비동기 씬 로딩
(`LoadSceneAsync`)과 페이드 인/아웃(코루틴 + CanvasGroup)을 조합하면 씬 전환이 부드럽고
전문적으로 보인다. 초보 개발자가 가장 쉽게 완성도를 높일 수 있는 포인트 중 하나.

---

## Unity 구현 방법

### 1. 페이드 UI 준비
1. 최상위 Canvas(Screen Space - Overlay) 생성, `Sort Order` 999 (모든 UI 위)
2. 자식으로 `Image` 추가 → 색상 검정, 전체 화면 크기 (Stretch All)
3. `CanvasGroup` 컴포넌트 추가 (Alpha 조절용)
4. 시작 시 `Alpha = 0`, `BlocksRaycasts = false`

### 2. SceneLoader 싱글턴
```csharp
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

public class SceneLoader : MonoBehaviour
{
    public static SceneLoader Instance { get; private set; }

    [SerializeField] private CanvasGroup fadeGroup;
    [SerializeField] private float fadeDuration = 0.4f;

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void LoadScene(string sceneName)
    {
        StartCoroutine(LoadSceneRoutine(sceneName));
    }

    private IEnumerator LoadSceneRoutine(string sceneName)
    {
        // 1) 페이드 아웃 (검게)
        yield return StartCoroutine(Fade(0f, 1f));

        // 2) 비동기 로딩 시작
        AsyncOperation op = SceneManager.LoadSceneAsync(sceneName);
        op.allowSceneActivation = false; // 로딩 완료 후 바로 전환 안 함

        // 3) 로딩 진행률 대기 (0.9 = 로딩 완료, 활성화 대기 상태)
        while (op.progress < 0.9f)
        {
            yield return null;
        }

        // 4) 로딩 완료 → 씬 활성화
        op.allowSceneActivation = true;
        yield return null; // 씬 활성화 한 프레임 대기

        // 5) 페이드 인 (밝게)
        yield return StartCoroutine(Fade(1f, 0f));
        fadeGroup.blocksRaycasts = false;
    }

    private IEnumerator Fade(float from, float to)
    {
        fadeGroup.blocksRaycasts = true;
        float elapsed = 0f;
        while (elapsed < fadeDuration)
        {
            elapsed += Time.unscaledDeltaTime; // 일시정지 중에도 동작
            fadeGroup.alpha = Mathf.Lerp(from, to, elapsed / fadeDuration);
            yield return null;
        }
        fadeGroup.alpha = to;
    }
}
```

> `Time.unscaledDeltaTime` 사용 → `Time.timeScale = 0` (일시정지 상태)에서도 페이드 동작.

### 3. 호출 방법
```csharp
// 게임 오버 시
SceneLoader.Instance.LoadScene("MainMenu");

// 다음 스테이지 이동 시
SceneLoader.Instance.LoadScene("GameScene");
```

### 4. 로딩 화면 (선택 사항)
긴 로딩이 필요한 경우, 중간에 로딩바 추가:
```csharp
[SerializeField] private Slider loadingBar;

// LoadSceneRoutine 내부에서
while (op.progress < 0.9f)
{
    if (loadingBar != null) loadingBar.value = op.progress;
    yield return null;
}
```

### 5. 씬 이름 상수 관리 (오타 방지)
```csharp
public static class SceneNames
{
    public const string MainMenu = "MainMenu";
    public const string Game     = "GameScene";
    public const string GameOver = "GameOverScene";
}
// 사용: SceneLoader.Instance.LoadScene(SceneNames.Game);
```

### 6. Build Settings 등록 필수
`File > Build Settings > Scenes In Build`에 모든 씬 추가해야 `LoadSceneAsync` 동작.

---

## OnionCat 적용 포인트

### 씬 구성 권장
| 씬 이름       | 용도                              |
|--------------|----------------------------------|
| `MainMenu`   | 타이틀, 시작/설정/종료 버튼       |
| `GameScene`  | 실제 플레이 (방 생성 포함)        |
| `GameOver`   | 런 결과, 재시작/메뉴 버튼         |

### 게임 오버 → 재시작 흐름
```
GameScene (게임 오버 발생)
   → SceneLoader.LoadScene("GameOver")   [페이드 아웃/인]
   → GameOver 씬에서 "재시작" 클릭
   → SceneLoader.LoadScene("GameScene")  [새 런 시작]
```

### PersistentDataManager와 조합
`DontDestroyOnLoad` 오브젝트는 SceneLoader와 PersistentDataManager 2개만 유지.
런 데이터(RunDataManager)는 `GameScene` 오브젝트에 두어 씬 재로드 시 자동 초기화.

### 협력 게임 특성상 주의점
- 2인 협력이므로 씬 전환 시 양쪽 입력 처리를 모두 차단해야 함
- 페이드 아웃 시작과 동시에 `PlayerInput.enabled = false` 처리 권장
- `fadeGroup.blocksRaycasts = true`는 UI만 차단 → 게임 오브젝트 입력은 별도로 막아야 함

---

## 참고 링크
- [Unity 공식 — LoadSceneAsync](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadSceneAsync.html)
- [Unity 공식 — AsyncOperation.allowSceneActivation](https://docs.unity3d.com/ScriptReference/AsyncOperation-allowSceneActivation.html)
- [Unity 공식 — CanvasGroup](https://docs.unity3d.com/Manual/class-CanvasGroup.html)
- [Game Dev Guide — Scene Manager Tutorial (YouTube)](https://www.youtube.com/results?search_query=unity+async+scene+loading+fade+transition+tutorial)
- [Brackeys — Scene Transitions (YouTube)](https://www.youtube.com/results?search_query=brackeys+scene+transitions+unity)
