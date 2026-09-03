# Unity New Input System — Action Map 런타임 전환 심화

리서치 날짜: 2026-09-03

## 개요

Unity New Input System에서 **Action Map**은 "지금 어떤 입력을 받을 수 있는가"를 상태별로 관리하는 핵심 단위다. 게임 상태(게임플레이/UI/대화/일시정지)에 따라 Action Map을 전환하면 입력 처리 코드를 깔끔하게 분리할 수 있다. OnionCat은 **2인 로컬 협동**이며 P1(Cat)은 게임패드, P2(Onion)는 키보드+마우스를 사용하는 비대칭 구조라, Action Map 설계가 특히 중요하다.

---

## 핵심 개념

### Action Map이란?
- Input Actions 에셋 내부의 "맥락별 입력 묶음"
- 예: `Gameplay` 맵(이동/공격), `UI` 맵(메뉴 탐색), `Cutscene` 맵(스킵만 허용)
- 맵 단위로 활성화/비활성화 가능 → 상태에 따라 바꿔 끼우는 방식

### PlayerInput 컴포넌트 (OnionCat 권장 방식)
```csharp
// Inspector에서 설정
// Behavior: Invoke Unity Events 또는 Send Messages
// Actions: InputActions 에셋 참조
// Default Map: "Gameplay"
```

각 플레이어 오브젝트에 `PlayerInput`을 붙이면 자동으로 기기 할당/Action Map 관리

---

## Unity 구현 방법

### 1. Input Actions 에셋 구조 설계

```
OnionCatInputActions
├── Gameplay (Action Map)
│   ├── P1_Move          [Gamepad LeftStick, WASD]
│   ├── P1_Dash          [Gamepad South, Space]
│   ├── P1_Slash         [Gamepad West, F]
│   ├── P2_Aim           [Mouse Position]
│   ├── P2_Shoot         [Mouse Left, J]
│   └── P2_Shield        [Mouse Right, K]
├── UI (Action Map)
│   ├── Navigate         [Gamepad DPad/LeftStick, Arrow/WASD]
│   ├── Submit           [Gamepad South, Enter/Space]
│   └── Cancel           [Gamepad East, Escape]
└── Pause (Action Map)
    └── Resume           [Gamepad Start, Escape]
```

### 2. 두 PlayerInput을 별도 오브젝트에 배치

```csharp
// CatInputHandler.cs (P1 오브젝트에 부착)
public class CatInputHandler : MonoBehaviour
{
    [SerializeField] private PlayerInput playerInput;

    private void OnMove(InputValue value)
    {
        Vector2 dir = value.Get<Vector2>();
        CatController.Instance.SetMoveDirection(dir);
    }

    private void OnDash(InputValue value)
    {
        if (value.isPressed) CatController.Instance.Dash();
    }

    private void OnSlash(InputValue value)
    {
        if (value.isPressed) CatController.Instance.Slash();
    }
}
```

```csharp
// OnionInputHandler.cs (P2 오브젝트에 부착)
public class OnionInputHandler : MonoBehaviour
{
    [SerializeField] private PlayerInput playerInput;

    private void OnAim(InputValue value)
    {
        // 마우스 월드 좌표 변환
        Vector2 screenPos = value.Get<Vector2>();
        Vector2 worldPos = Camera.main.ScreenToWorldPoint(screenPos);
        OnionController.Instance.SetAimTarget(worldPos);
    }

    private void OnShoot(InputValue value)
    {
        if (value.isPressed) OnionController.Instance.Shoot();
    }

    private void OnShield(InputValue value)
    {
        OnionController.Instance.SetShield(value.isPressed);
    }
}
```

### 3. Action Map 런타임 전환

```csharp
// GameStateManager.cs
public class GameStateManager : MonoBehaviour
{
    [SerializeField] private PlayerInput catInput;
    [SerializeField] private PlayerInput onionInput;

    public void EnterGameplay()
    {
        catInput.SwitchCurrentActionMap("Gameplay");
        onionInput.SwitchCurrentActionMap("Gameplay");
        Time.timeScale = 1f;
    }

    public void EnterPause()
    {
        // UI 맵으로 전환 → 게임플레이 입력 차단
        catInput.SwitchCurrentActionMap("UI");
        onionInput.SwitchCurrentActionMap("UI");
        Time.timeScale = 0f;
    }

    public void EnterCutscene()
    {
        // 모든 입력 비활성화 (스킵 버튼만 남김)
        catInput.SwitchCurrentActionMap("Cutscene");
        onionInput.SwitchCurrentActionMap("Cutscene");
    }
}
```

### 4. 디바이스 자동 할당 (게임패드 + 키보드/마우스 공존)

```csharp
// PlayerJoinManager.cs — 씬 시작 시 기기 배정
public class PlayerJoinManager : MonoBehaviour
{
    private void Awake()
    {
        // P1: 첫 번째 감지된 게임패드
        // P2: 키보드+마우스 강제 배정
        var gamepad = Gamepad.all.Count > 0 ? Gamepad.all[0] : null;
        
        if (gamepad != null)
            catInput.SwitchCurrentControlScheme("Gamepad", gamepad);
        
        onionInput.SwitchCurrentControlScheme(
            "KeyboardMouse",
            Keyboard.current,
            Mouse.current
        );
    }
}
```

### 5. 게임패드 연결/해제 감지

```csharp
// 게임패드 뽑혔다 꽂힐 때 자동 재연결
private void OnEnable()
{
    InputSystem.onDeviceChange += OnDeviceChange;
}

private void OnDeviceChange(InputDevice device, InputDeviceChange change)
{
    if (device is Gamepad gamepad)
    {
        if (change == InputDeviceChange.Added)
        {
            catInput.SwitchCurrentControlScheme("Gamepad", gamepad);
            // 재연결 팝업 숨기기
        }
        else if (change == InputDeviceChange.Removed)
        {
            // 일시정지 + "P1 컨트롤러 재연결" 팝업
        }
    }
}

private void OnDisable()
{
    InputSystem.onDeviceChange -= OnDeviceChange;
}
```

---

## OnionCat 적용 포인트

### Action Map 전환 타임라인

| 게임 상태 | P1(Cat) Action Map | P2(Onion) Action Map |
|-----------|-------------------|----------------------|
| 메인 메뉴 | UI | UI |
| 게임플레이 | Gameplay | Gameplay |
| 일시정지 | UI | UI |
| 업그레이드 선택 | UI (방향키 탐색) | UI (마우스 클릭) |
| 게임오버 | UI | UI |
| 컷씬 | Cutscene | Cutscene |

### OnionCat 특수 고려사항

1. **P2 마우스 조준 + P1 이동 분리**: Onion의 `P2_Aim`은 MousePosition을 매 프레임 읽어야 함 → `PlayerInput`의 콜백 방식보다 `InputAction.ReadValue<Vector2>()` 직접 폴링이 나을 수 있음
2. **일시정지 중 Onion 마우스 커서 표시**: `Cursor.visible = true` / `Cursor.lockState = CursorLockMode.None`을 Pause 진입 시 처리
3. **업그레이드 화면에서 두 플레이어 독립 입력**: 같은 UI 맵이지만 각자 다른 버튼으로 다른 항목 선택 가능하도록 설계

---

## 참고 링크

- Unity 공식 Input System 패키지 문서: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/index.html
- PlayerInput 컴포넌트 레퍼런스: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInput.html
- Action Map 전환: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/ActionBindings.html#action-maps
- 멀티플레이어 입력: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html
- 유튜브: "Unity New Input System Complete Guide" by Code Monkey
- 디바이스 연결 감지: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/api/UnityEngine.InputSystem.InputSystem.html#UnityEngine_InputSystem_InputSystem_onDeviceChange
