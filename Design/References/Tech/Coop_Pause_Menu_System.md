# 협력 모드 일시정지 메뉴 시스템 (Coop Pause Menu)

리서치 날짜: 2026-08-30

## 개요

2인 협력 게임에서 일시정지 메뉴는 단일 플레이어와 다르게 설계해야 한다.
OnionCat은 두 플레이어가 하나의 몸체를 공유하므로 어느 쪽이든 정지를 요청할 수 있어야 하고,
"런 포기"처럼 한쪽에만 영향을 미칠 수 없는 행동은 확인 단계를 거쳐야 한다.
또한 New Input System에서 ActionMap 전환을 정확히 처리하지 않으면 UI 입력이 게임에도 전달되는 버그가 발생한다.

---

## Unity 구현 방법

### 핵심 설계 결정

| 질문 | OnionCat 답변 |
|------|--------------|
| 누가 정지할 수 있나? | P1 또는 P2 중 하나만 눌러도 정지 |
| 정지 중 다른 플레이어 입력? | 둘 다 UI 조작 가능 (어느 버튼으로든 재개) |
| "런 포기" 시 확인 필요? | 네 → "정말 포기하시겠습니까?" 확인창 |
| 온라인/로컬 차이? | 현재 로컬 코옵만 → Time.timeScale 단순 조작 |

### PauseManager 구현

```csharp
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

public class CoopPauseManager : MonoBehaviour
{
    public static CoopPauseManager Instance { get; private set; }

    [SerializeField] private GameObject pauseOverlay;
    [SerializeField] private GameObject confirmAbandonPanel;

    // 각 플레이어의 PlayerInput 참조 (Inspector에서 드래그 앤 드롭 설정 필요)
    [SerializeField] private PlayerInput playerInput1;
    [SerializeField] private PlayerInput playerInput2;

    private bool isPaused;

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
    }

    // PlayerInput의 OnPause Action에 이벤트 바인딩
    public void OnPauseInput(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed) return;
        if (isPaused) Resume();
        else Pause();
    }

    public void Pause()
    {
        if (isPaused) return;
        isPaused = true;
        Time.timeScale = 0f;
        pauseOverlay.SetActive(true);
        SwitchToUIMap();
    }

    public void Resume()
    {
        if (!isPaused) return;
        isPaused = false;
        Time.timeScale = 1f;
        pauseOverlay.SetActive(false);
        confirmAbandonPanel.SetActive(false);
        SwitchToGameplayMap();
    }

    // "런 포기" 버튼 클릭 → 확인창 표시
    public void RequestAbandonRun()
    {
        confirmAbandonPanel.SetActive(true);
    }

    // 확인창 "예" 클릭
    public void ConfirmAbandonRun()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene("MainMenu");
    }

    // 확인창 "아니오"
    public void CancelAbandon()
    {
        confirmAbandonPanel.SetActive(false);
    }

    private void SwitchToUIMap()
    {
        playerInput1?.SwitchCurrentActionMap("UI");
        playerInput2?.SwitchCurrentActionMap("UI");
    }

    private void SwitchToGameplayMap()
    {
        playerInput1?.SwitchCurrentActionMap("Gameplay");
        playerInput2?.SwitchCurrentActionMap("Gameplay");
    }
}
```

### New Input System — ActionMap 설계

```
InputActionAsset
├── Gameplay (ActionMap)
│   ├── Move (P1)
│   ├── Dash (P1)
│   ├── Slash (P1)
│   ├── Aim (P2)
│   ├── Shoot (P2)
│   ├── Shield (P2)
│   └── Pause (P1 + P2 공용) ← 두 플레이어 모두에 바인딩
└── UI (ActionMap)
    ├── Navigate (방향키/스틱)
    ├── Submit (Enter/A버튼)
    ├── Cancel (ESC/B버튼)  ← Resume에도 사용
    └── Pause (ESC/Start) ← Resume 역할
```

### 정지 중 애니메이션 (UnscaledTime)

`Time.timeScale = 0f`이면 Animator가 멈춘다.
폴드인/폴드아웃 연출에는 반드시 `UpdateMode = UnscaledTime` 사용.

```csharp
// Animator 설정 (코드 또는 Inspector)
GetComponent<Animator>().updateMode = AnimatorUpdateMode.UnscaledTime;

// DOTween 사용 시
pauseCanvasGroup.DOFade(1f, 0.15f).SetUpdate(true); // SetUpdate(true) = unscaledTime
```

### 일시정지 UI 구조 (권장)

```
PauseOverlay (Canvas, Sort Order 10)
├── Dimmer (Image, alpha 0.5, black)
└── PausePanel
    ├── Title: "일시정지"
    ├── [재개] → Resume()
    ├── [설정] → Open Settings (Settings 패널 활성화)
    ├── [런 포기] → RequestAbandonRun()
    └── ConfirmAbandonPanel (기본 비활성화)
        ├── Text: "런을 포기하시겠습니까? 진행 상황이 초기화됩니다."
        ├── [예] → ConfirmAbandonRun()
        └── [아니오] → CancelAbandon()
```

---

## OnionCat 적용 포인트

### 공유 몸체 → 두 플레이어 모두 정지 가능

P1과 P2 모두 Pause 액션이 있으므로 어느 플레이어든 멈출 수 있음.
재개도 마찬가지 — UI ActionMap에서 둘 다 Cancel/Submit으로 재개 가능하게 설정.

### "런 포기" 확인 절차

단순한 ESC → 메인 메뉴가 아니라 반드시 2단계 확인:
1. 정지 메뉴 → "런 포기" 버튼
2. 확인창 → "예/아니오"

OnionCat은 퍼마데스 로그라이크이므로 실수로 런을 날리는 것은 치명적.

### 설정 메뉴 연결

설정 메뉴를 별도 패널로 만들어 정지 중에도 음량·밝기·키 설정 가능하게.
`Time.timeScale = 0` 상태를 유지하면서 패널만 스택 방식으로 전환.

### 유니티 에디터에서 설정 필요

- `CoopPauseManager` 오브젝트의 Inspector에서:
  - `pauseOverlay` → PauseOverlay GameObject 드래그 앤 드롭 설정 필요
  - `confirmAbandonPanel` → ConfirmAbandonPanel 드래그 앤 드롭 설정 필요
  - `playerInput1`, `playerInput2` → 두 플레이어 PlayerInput 컴포넌트 드래그 앤 드롭 설정 필요
- Pause 애니메이션을 쓰는 Animator: `Update Mode → Unscaled Time` 설정

---

## 참고 링크

- Unity Input System ActionMap 전환: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/ActionBindings.html
- Time.timeScale과 UI 애니메이션: https://docs.unity3d.com/ScriptReference/Time-timeScale.html
- DOTween SetUpdate(true): http://dotween.demigiant.com/documentation.php
- Unity UI EventSystem 멀티 플레이어: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/UISupport.html
