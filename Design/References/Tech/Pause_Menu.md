# 일시정지 메뉴 (Pause Menu)

## 개요

일시정지 메뉴는 게임의 완성도를 좌우하는 기본 기능이다. 로그라이크에서는 단순히 게임을 멈추는 것 외에 "현재 런 재시작", "메인 메뉴로", "게임 종료" 흐름이 명확하게 연결되어야 한다. New Input System을 사용하는 OnionCat에서는 ESC 처리, timeScale 제어, 액션 맵 전환이 세트로 구현되어야 한다.

---

## Unity 구현 방법

### 1. ESC 입력 처리 (New Input System)

Input Action Asset에서 두 개의 Action Map을 만든다:
- `Gameplay` 맵: 이동, 공격, 능력, **Pause(ESC)**
- `UI` 맵: 메뉴 탐색, Select, **Cancel(ESC)**

ESC를 두 맵에 분리하면 "일시정지 → ESC → 즉시 닫힘" 더블 트리거 버그를 방지한다.

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

public class PauseManager : MonoBehaviour
{
    public static PauseManager Instance { get; private set; }

    [SerializeField] private GameObject pauseMenuPanel;

    private GameInputActions inputActions; // Input Action Asset에서 자동 생성된 클래스
    private bool isPaused = false;

    private void Awake()
    {
        if (Instance == null) Instance = this;
        else { Destroy(gameObject); return; }

        inputActions = new GameInputActions();
    }

    private void OnEnable()
    {
        inputActions.Gameplay.Pause.performed += OnPauseInput;
        inputActions.UI.Cancel.performed += OnCancelInput;
        inputActions.Gameplay.Enable();
    }

    private void OnDisable()
    {
        inputActions.Gameplay.Pause.performed -= OnPauseInput;
        inputActions.UI.Cancel.performed -= OnCancelInput;
    }

    private void OnPauseInput(InputAction.CallbackContext ctx) => PauseGame();
    private void OnCancelInput(InputAction.CallbackContext ctx) => ResumeGame();
}
```

---

### 2. Time.timeScale 패턴 — 게임 멈춤 + UI 유지

```csharp
public void PauseGame()
{
    if (isPaused) return;
    isPaused = true;

    Time.timeScale = 0f; // 게임 로직, 물리, 일반 애니메이션 정지

    // 입력 맵 전환: Gameplay → UI
    inputActions.Gameplay.Disable();
    inputActions.UI.Enable();

    pauseMenuPanel.SetActive(true);
}

public void ResumeGame()
{
    if (!isPaused) return;
    isPaused = false;

    Time.timeScale = 1f; // 반드시 복원 — 이 줄 빠지면 재시작 후에도 게임이 얼어있음

    inputActions.UI.Disable();
    inputActions.Gameplay.Enable();

    pauseMenuPanel.SetActive(false);
}
```

**UI 애니메이션이 멈추는 문제 해결:**
```csharp
// 일시정지 중에도 UI 애니메이터가 돌아가야 할 때
Animator menuAnimator = pauseMenuPanel.GetComponent<Animator>();
menuAnimator.updateMode = AnimatorUpdateMode.UnscaledTime;

// 코루틴에서 페이드 등 UI 이펙트
IEnumerator FadeIn(CanvasGroup cg, float duration)
{
    float t = 0f;
    while (t < duration)
    {
        t += Time.unscaledDeltaTime; // timeScale 무시
        cg.alpha = t / duration;
        yield return null;
    }
}
```

---

### 3. Canvas/UI 구조 설정

```
Canvas (Screen Space - Overlay)
└── PauseMenuPanel (Image: #000000 반투명 80%)
    ├── TitleText "PAUSED" (TextMeshPro)
    ├── StatsText (현재 층, 체력, 처치 수)
    ├── ResumeButton
    ├── RestartButton
    ├── SettingsButton (선택)
    └── QuitButton
```

**버튼 연결 코드:**
```csharp
public class PauseUI : MonoBehaviour
{
    [SerializeField] private Button resumeButton;
    [SerializeField] private Button restartButton;
    [SerializeField] private Button quitButton;

    private void Awake()
    {
        resumeButton.onClick.AddListener(() => PauseManager.Instance.ResumeGame());
        restartButton.onClick.AddListener(() => PauseManager.Instance.RestartLevel());
        quitButton.onClick.AddListener(() => PauseManager.Instance.QuitToMainMenu());
    }

    public void Open()
    {
        gameObject.SetActive(true);
        resumeButton.Select(); // 첫 번째 버튼 자동 선택 (패드 지원)
    }
}
```

---

### 4. 재시작 / 메인 메뉴 이동 — SceneManager

```csharp
using UnityEngine.SceneManagement;

public void RestartLevel()
{
    Time.timeScale = 1f; // 반드시 먼저 복원
    SceneManager.LoadScene(SceneManager.GetActiveScene().name);
}

public void QuitToMainMenu()
{
    Time.timeScale = 1f;
    SceneManager.LoadScene("MainMenu"); // Build Settings에 씬 추가 필수
}

public void QuitGame()
{
    Time.timeScale = 1f;
#if UNITY_EDITOR
    UnityEditor.EditorApplication.isPlaying = false;
#else
    Application.Quit();
#endif
}
```

**Build Settings 주의**: `File > Build Settings > Scenes in Build`에 사용하는 모든 씬을 추가해야 런타임에서 `LoadScene`이 작동한다.

---

### 5. 로그라이크 일시정지 메뉴 필수 요소

| 버튼 | 설명 | 구현 |
|------|------|------|
| Resume | 게임 재개 (첫 번째, 자동 선택) | `ResumeGame()` |
| Restart Run | 현재 런 처음부터 재시작 | `RestartLevel()` |
| Quit to Menu | 타이틀 화면으로 이동 | `QuitToMainMenu()` |
| (선택) Settings | 음량 등 설정 | 별도 패널 |

**UX 원칙:**
- Resume이 항상 최상단에 위치
- 창이 열릴 때 Resume 버튼이 포커스됨 → 엔터/A 버튼으로 즉시 재개
- 게임 상태 표시 (현재 층, 체력) → 플레이어가 맥락 파악 가능

---

## OnionCat 적용 포인트

### 두 플레이어 중 누가 ESC를 눌러도 일시정지

OnionCat은 2인 로컬 코옵이므로 두 플레이어 모두 일시정지를 트리거할 수 있어야 한다.

```csharp
// Player 1 (Cat) - Keyboard ESC
inputActions.Player1.Pause.performed += OnPauseInput;

// Player 2 (Crop) - Gamepad Start 또는 별도 키
inputActions.Player2.Pause.performed += OnPauseInput;
```

### 런 통계 표시

일시정지 화면에 현재 런 정보를 보여주면 플레이어가 전략을 재검토할 수 있다:
```csharp
statsText.text = $"층: {GameManager.CurrentFloor}\n" +
                 $"처치: {GameManager.KillCount}\n" +
                 $"Cat HP: {cat.HP}/{cat.MaxHP}\n" +
                 $"Crop HP: {crop.HP}/{crop.MaxHP}";
```

### 구현 순서 (초보자 권장)

1. `PauseMenuPanel` Canvas/UI 구조 먼저 만들기 (눈에 보이게)
2. ESC 하드코딩으로 `SetActive(true/false)` + `timeScale` 동작 확인
3. New Input System Action Map 연결로 전환
4. Resume/Restart/Quit 버튼 기능 연결
5. UI 애니메이션 및 Unscaled Time 적용

---

## 참고 링크

- [The Right Way to Pause in Unity - Game Dev Beginner](https://gamedevbeginner.com/the-right-way-to-pause-the-game-in-unity/)
- [New Input System Complete Guide - Game Dev Beginner](https://gamedevbeginner.com/input-in-unity-made-easy-complete-guide-to-the-new-system/)
- [Action Map Switching - One Wheel Studio](https://onewheelstudio.com/blog/2021/6/27/changing-action-maps-with-unitys-new-input-system)
- [Time.timeScale 공식 문서](https://docs.unity3d.com/ScriptReference/Time-timeScale.html)
- [Time.unscaledDeltaTime 공식 문서](https://docs.unity3d.com/ScriptReference/Time-unscaledDeltaTime.html)
- [SceneManager.LoadScene 공식 문서](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadScene.html)
