# 게임 종료 확인 다이얼로그 (Game Exit Confirmation Dialog)

리서치 날짜: 2026-09-06

## 개요

플레이어가 게임을 종료하려 할 때 표시되는 확인 화면이다. 특히 **런 중 종료 시 진행상황 손실 경고**를 제공한다. 완성도 있는 게임을 출시할 때 반드시 필요하지만 자주 간과되는 기능이다.

OnionCat에서는:
- 로그라이크 런 중 종료 시 → "진행 중인 런이 사라집니다" 경고 표시
- 메인 메뉴에서 종료 시 → 간단한 "종료하시겠습니까?" 확인
- ESC / Alt+F4 / 창 X 버튼 모두 처리

---

## 종료 시나리오별 처리

| 상황 | 표시 내용 | 버튼 |
|------|-----------|------|
| 런 진행 중 종료 | "런이 종료됩니다. 진행 상황은 저장되지 않습니다." | 종료 / 계속하기 |
| 메인 메뉴에서 종료 | "게임을 종료하시겠습니까?" | 종료 / 취소 |
| 인트로/로딩 중 종료 | 경고 없이 즉시 종료 허용 | — |

---

## Unity 구현 방법

### 1. Application.wantsToQuit 이벤트 (Unity 권장 방식)

```csharp
public class GameExitHandler : MonoBehaviour
{
    [SerializeField] private ExitConfirmDialog exitDialog;

    private void OnEnable()
    {
        Application.wantsToQuit += OnApplicationWantsToQuit;
    }

    private void OnDisable()
    {
        Application.wantsToQuit -= OnApplicationWantsToQuit;
    }

    // 창 X 버튼, Alt+F4 모두 이 이벤트를 발생시킴
    private bool OnApplicationWantsToQuit()
    {
        // true를 반환하면 즉시 종료, false를 반환하면 종료 취소
        if (ShouldShowExitConfirm())
        {
            exitDialog.Show(OnConfirmExit, OnCancelExit);
            return false; // 종료 중단, 다이얼로그에서 처리
        }
        return true; // 즉시 종료
    }

    private bool ShouldShowExitConfirm()
    {
        // 런 진행 중이거나 메인 메뉴 이외의 씬에서
        return GameStateManager.Instance.CurrentState != GameState.MainMenu
            && GameStateManager.Instance.CurrentState != GameState.Loading;
    }

    private void OnConfirmExit()
    {
        // 종료 전 런 데이터 정리
        RunManager.Instance?.AbandonRun();
        Application.Quit();
    }

    private void OnCancelExit()
    {
        // 아무것도 안 함 — 게임 계속
    }
}
```

### 2. ESC 키로 종료 다이얼로그 트리거

```csharp
public class ExitOnEsc : MonoBehaviour
{
    [SerializeField] private ExitConfirmDialog exitDialog;

    // 메인 메뉴에서만 부착 (런 중에는 Pause Menu가 ESC 처리)
    private void Update()
    {
        if (Keyboard.current.escapeKey.wasPressedThisFrame)
            exitDialog.Show();
    }
}
```

### 3. 다이얼로그 UI 컴포넌트

```csharp
public class ExitConfirmDialog : MonoBehaviour
{
    [SerializeField] private GameObject panel;
    [SerializeField] private TMP_Text messageText;
    [SerializeField] private Button confirmButton;
    [SerializeField] private Button cancelButton;

    private Action onConfirm;
    private Action onCancel;

    public void Show(Action confirm = null, Action cancel = null)
    {
        onConfirm = confirm;
        onCancel = cancel;

        // 씬 상태에 따른 메시지
        messageText.text = RunManager.Instance != null && RunManager.Instance.IsRunActive
            ? "런 진행 중입니다.\n종료하면 이번 런의 진행상황을 잃습니다."
            : "게임을 종료하시겠습니까?";

        panel.SetActive(true);
        Time.timeScale = 0f; // 일시정지

        confirmButton.onClick.RemoveAllListeners();
        cancelButton.onClick.RemoveAllListeners();
        confirmButton.onClick.AddListener(HandleConfirm);
        cancelButton.onClick.AddListener(HandleCancel);
    }

    private void HandleConfirm()
    {
        Time.timeScale = 1f;
        panel.SetActive(false);
        onConfirm?.Invoke();
    }

    private void HandleCancel()
    {
        Time.timeScale = 1f;
        panel.SetActive(false);
        onCancel?.Invoke();
    }
}
```

### 4. 새 Input System (InputAction) 연동

```csharp
// PlayerInput 컴포넌트의 UI Input Actions에 Cancel 액션 추가 후:
public void OnCancel(InputValue value)
{
    if (value.isPressed)
        exitDialog.Show();
}
```

### 5. WebGL 플랫폼 예외 처리

WebGL에서는 `Application.Quit()`이 동작하지 않음:

```csharp
private void OnConfirmExit()
{
#if UNITY_EDITOR
    UnityEditor.EditorApplication.isPlaying = false;
#elif UNITY_WEBGL
    // 브라우저 탭을 닫을 수 없으므로 메인 메뉴로 이동
    SceneManager.LoadScene("MainMenu");
#else
    Application.Quit();
#endif
}
```

### 6. 런 포기 처리 (로그라이크 필수)

```csharp
public class RunManager : MonoBehaviour
{
    public bool IsRunActive { get; private set; }

    public void AbandonRun()
    {
        if (!IsRunActive) return;

        // 통계 기록 (포기한 런도 통계에 포함)
        StatsManager.Instance.RecordRunAbandoned(currentRunData);

        // 영구 재화는 유지 (런 중 얻은 영구 재화)
        MetaProgressionManager.Instance.SavePermanentCurrency(currentRunData.earnedCurrency);

        // 런 데이터 초기화
        IsRunActive = false;
        currentRunData = null;
    }
}
```

---

## OnionCat 적용 포인트

### 우선순위: 런 포기 확인이 핵심

로그라이크에서 실수로 게임을 끄면 런 진행이 사라진다. OnionCat 구현 순서:

1. `GameExitHandler` — `Application.wantsToQuit` 구독 (창 X, Alt+F4 처리)
2. `ExitConfirmDialog` UI 제작 (Canvas, 반투명 오버레이, 두 버튼)
3. 일시정지 메뉴(ESC)와 연동 — Pause Menu에 "메인 메뉴로" 버튼 → 별도 확인 다이얼로그
4. `RunManager.AbandonRun()` — 영구 재화만 저장, 나머지 초기화

### Unity Inspector에서 설정 필요

- `GameExitHandler` 컴포넌트를 `PersistentManagers` 씬의 GameObject에 부착
- `ExitConfirmDialog` 프리팹을 `GameExitHandler.exitDialog`에 드래그 앤 드롭 설정 필요
- Canvas Sort Order를 최상위(999)로 설정해 모든 UI 위에 표시

### 주의사항

- `Time.timeScale = 0f`로 게임 일시정지하되 UI 애니메이션은 `unscaledTime` 사용
- 협동 게임이므로 **두 플레이어 모두 동의** 없이 한 명이 종료하면 어떻게 할지 설계 필요
  - OnionCat은 로컬 협동이므로 "종료하면 두 플레이어 모두 종료" 안내 문구 추가

---

## 참고 링크

- Unity 공식: [Application.wantsToQuit](https://docs.unity3d.com/ScriptReference/Application-wantsToQuit.html)
- Unity 공식: [Application.Quit](https://docs.unity3d.com/ScriptReference/Application.Quit.html)
- Unity Forum: "How to intercept Alt+F4 / window close button" — wantsToQuit 활용법 상세
- Unity Blog: WebGL 플랫폼 제한 사항 — Application.Quit 미지원 확인
