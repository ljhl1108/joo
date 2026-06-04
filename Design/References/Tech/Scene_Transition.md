# 씬 전환 관리 (Scene Transition Management)

## 개요

씬 전환은 게임 완성도를 결정하는 핵심 "폴리시"다. 메인 메뉴 → 게임 → 게임 오버 → 메인 메뉴 루프를 끊기지 않게 연결하고, 로딩 중 프리즈처럼 느껴지지 않도록 페이드 인/아웃 및 로딩 화면을 적용한다. OnionCat처럼 방 전환이 많은 로그라이크에서는 씬 전환과 방 전환(씬 내부 전환)을 구분해야 한다.

---

## Unity 구현 방법

### 1. 씬 등록

`File > Build Settings`에서 사용할 씬 모두 등록 필수.

```
Index 0: MainMenu
Index 1: Game
Index 2: GameOver
```

### 2. 기본 씬 전환 (동기 — 작은 씬에 적합)

```csharp
using UnityEngine.SceneManagement;

// 씬 이름으로 로드
SceneManager.LoadScene("Game");

// 씬 인덱스로 로드
SceneManager.LoadScene(1);
```

### 3. 비동기 씬 전환 + 로딩 화면 (권장)

```csharp
public class SceneLoader : MonoBehaviour
{
    public static SceneLoader Instance { get; private set; }

    [SerializeField] private CanvasGroup fadeCanvas; // 검은 화면 CanvasGroup
    [SerializeField] private float fadeDuration = 0.5f;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void LoadScene(string sceneName)
    {
        StartCoroutine(LoadRoutine(sceneName));
    }

    private IEnumerator LoadRoutine(string sceneName)
    {
        // 1. 페이드 아웃 (현재 씬 어둡게)
        yield return FadeRoutine(0f, 1f);

        // 2. 비동기 로드 시작
        AsyncOperation op = SceneManager.LoadSceneAsync(sceneName);
        op.allowSceneActivation = false; // 로드 완료 후 즉시 전환 방지

        // 3. 90%까지 로드 대기 (Unity 비동기 로드는 0.9에서 멈춤)
        while (op.progress < 0.9f)
            yield return null;

        // 4. (선택) 최소 로딩 시간 보장
        yield return new WaitForSeconds(0.2f);

        // 5. 씬 전환 허용
        op.allowSceneActivation = true;
        yield return new WaitUntil(() => op.isDone);

        // 6. 페이드 인 (새 씬 밝아짐)
        yield return FadeRoutine(1f, 0f);
    }

    private IEnumerator FadeRoutine(float from, float to)
    {
        float elapsed = 0f;
        fadeCanvas.gameObject.SetActive(true);
        while (elapsed < fadeDuration)
        {
            elapsed += Time.deltaTime;
            fadeCanvas.alpha = Mathf.Lerp(from, to, elapsed / fadeDuration);
            yield return null;
        }
        fadeCanvas.alpha = to;
        if (to == 0f) fadeCanvas.gameObject.SetActive(false);
    }
}
```

### 4. 페이드용 Canvas 설정

```
Canvas (Sort Order: 999, Render Mode: Screen Space Overlay)
  └── Panel (Image: black, CanvasGroup 컴포넌트)
      └── LoadingText (선택)
```

- `CanvasGroup.alpha = 0` → 투명 (게임 플레이 중)
- `CanvasGroup.alpha = 1` → 불투명 (씬 전환 중)
- `CanvasGroup.blocksRaycasts = true`로 전환 중 클릭 차단

### 5. SceneLoader 사용법

```csharp
// 어디서든 호출
SceneLoader.Instance.LoadScene("GameOver");
SceneLoader.Instance.LoadScene("MainMenu");
SceneLoader.Instance.LoadScene("Game");
```

### 6. DontDestroyOnLoad 주의사항

- `SceneLoader`는 씬 간 유지되어야 하므로 `DontDestroyOnLoad` 적용
- 씬 로드 시 중복 생성 방지를 위해 싱글톤 패턴 필수
- `SceneManager.sceneLoaded` 이벤트로 씬 로드 완료 후 초기화 가능

```csharp
void OnEnable() => SceneManager.sceneLoaded += OnSceneLoaded;
void OnDisable() => SceneManager.sceneLoaded -= OnSceneLoaded;

void OnSceneLoaded(Scene scene, LoadSceneMode mode)
{
    // 새 씬 로드 완료 후 처리 (BGM 교체 등)
}
```

### 7. 방 전환 (씬 내부 — OnionCat 특화)

로그라이크에서 방 이동은 **씬 전환이 아닌 카메라 이동 + 방 활성화**로 처리:

```csharp
// 씬 전환 X — 카메라 이동 + 방 오브젝트 활성/비활성
public void MoveToRoom(Room nextRoom)
{
    currentRoom.SetActive(false);
    nextRoom.SetActive(true);
    // 카메라 타겟 변경 or Cinemachine 가상 카메라 전환
    StartCoroutine(CameraTransition(nextRoom.transform.position));
}
```

---

## OnionCat 적용 포인트

### 씬 구성 제안

| 씬 이름 | 용도 |
|---|---|
| `MainMenu` | 타이틀, 시작/종료 버튼 |
| `Game` | 실제 게임플레이 (방 전환은 씬 내부) |
| `GameOver` | 런 결과 요약, 재시작 버튼 |

### 구현 우선순위

1. `SceneLoader` 싱글톤 작성 → `DontDestroyOnLoad` 씬에 배치
2. 검은 Fade Canvas 준비 (Sort Order 999)
3. 메인 메뉴 "시작" 버튼 → `SceneLoader.Instance.LoadScene("Game")`
4. 게임 오버 시 → `SceneLoader.Instance.LoadScene("GameOver")`
5. 게임 오버 화면 "재시작" → `SceneLoader.Instance.LoadScene("Game")`

### 흔한 실수

- `SceneManager.LoadScene()`을 `Update()`에서 직접 호출하면 다음 프레임에 씬이 즉시 파괴됨 → 반드시 코루틴으로 감싸거나 조건 플래그 사용
- `Time.timeScale = 0` (일시정지 상태)에서 코루틴의 `WaitForSeconds`는 작동 안 함 → `WaitForSecondsRealtime` 사용
- 씬 전환 직전 오디오 클리핑 방지: 페이드 아웃 완료 후 씬 로드 시작

---

## 참고 링크

- [Unity 공식 SceneManager 문서](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html)
- [Unity 공식 AsyncOperation 문서](https://docs.unity3d.com/ScriptReference/AsyncOperation.html)
- [Brackeys - How to make a LOADING SCREEN in Unity](https://www.youtube.com/watch?v=YMj2qPq9CP8)
- [Code Monkey - Scene Management Best Practices](https://www.youtube.com/results?search_query=unity+scene+management+code+monkey)
