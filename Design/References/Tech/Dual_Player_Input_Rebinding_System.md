# 듀얼 플레이어 입력 리바인딩 시스템

리서치 날짜: 2026-08-28

## 개요

OnionCat은 Player 1(고양이, 게임패드)과 Player 2(작물, 키보드+마우스)가 동시에 플레이한다. 설정 메뉴에서 두 플레이어의 키 배치를 각각 변경할 수 있어야 완성된 게임이다. Unity New Input System의 런타임 리바인딩 기능을 활용한 구현 방법을 다룬다.

---

## Unity 구현 방법

### 1. InputActionAsset 이중 바인딩 구조

```
InputActionAsset
├── Player1 Action Map
│   ├── Move (Gamepad Left Stick / WASD)
│   ├── Dash (Gamepad South / Space)
│   └── Attack (Gamepad West / F)
└── Player2 Action Map
    ├── Aim (Mouse Position)
    ├── Fire (Mouse Left Button / J)
    └── Shield (Mouse Right Button / K)
```

두 플레이어를 **별도 Action Map**으로 분리하는 것이 핵심. 같은 Action Map을 공유하면 리바인딩 시 충돌.

### 2. 런타임 리바인딩 기본 구현

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

public class InputRebindingUI : MonoBehaviour
{
    [SerializeField] private InputActionAsset inputActions;
    private InputActionRebindingExtensions.RebindingOperation _rebindOperation;

    // 리바인딩 시작
    public void StartRebinding(string actionMapName, string actionName, int bindingIndex)
    {
        var actionMap = inputActions.FindActionMap(actionMapName);
        var action = actionMap.FindAction(actionName);

        // 리바인딩 중 해당 액션 비활성화
        action.Disable();

        _rebindOperation = action.PerformInteractiveRebinding(bindingIndex)
            .WithCancelingThrough("<Keyboard>/escape")
            .OnComplete(operation =>
            {
                action.Enable();
                operation.Dispose();
                _rebindOperation = null;
                SaveBindings();
                RefreshUI(actionMapName, actionName, bindingIndex);
            })
            .OnCancel(operation =>
            {
                action.Enable();
                operation.Dispose();
                _rebindOperation = null;
            })
            .Start();
    }

    // 리바인딩 취소
    public void CancelRebinding()
    {
        _rebindOperation?.Cancel();
    }

    // 기본값 복원
    public void ResetToDefault(string actionMapName, string actionName)
    {
        var action = inputActions.FindActionMap(actionMapName).FindAction(actionName);
        action.RemoveAllBindingOverrides();
        SaveBindings();
    }
}
```

### 3. 바인딩 저장 및 불러오기

```csharp
private const string BINDING_SAVE_KEY = "InputBindings";

private void SaveBindings()
{
    string json = inputActions.SaveBindingOverridesAsJson();
    PlayerPrefs.SetString(BINDING_SAVE_KEY, json);
    PlayerPrefs.Save();
}

private void LoadBindings()
{
    if (PlayerPrefs.HasKey(BINDING_SAVE_KEY))
    {
        string json = PlayerPrefs.GetString(BINDING_SAVE_KEY);
        inputActions.LoadBindingOverridesFromJson(json);
    }
}

// 게임 시작 시 또는 InputSystem 초기화 시 호출
private void Awake()
{
    LoadBindings();
}
```

### 4. 설정 UI 구현 (UnityEngine.UI 기반)

```csharp
public class RebindButtonUI : MonoBehaviour
{
    [SerializeField] private string actionMapName;
    [SerializeField] private string actionName;
    [SerializeField] private int bindingIndex = 0;
    [SerializeField] private TMPro.TMP_Text bindingText;
    [SerializeField] private InputRebindingUI rebindingUI;
    [SerializeField] private InputActionAsset inputActions;

    private void OnEnable()
    {
        RefreshDisplay();
    }

    public void StartRebind()
    {
        bindingText.text = "입력 대기...";
        rebindingUI.StartRebinding(actionMapName, actionName, bindingIndex);
    }

    public void RefreshDisplay()
    {
        var action = inputActions.FindActionMap(actionMapName).FindAction(actionName);
        // 현재 바인딩 표시명 가져오기
        bindingText.text = InputControlPath.ToHumanReadableString(
            action.bindings[bindingIndex].effectivePath,
            InputControlPath.HumanReadableStringOptions.OmitDevice
        );
    }
}
```

### 5. 듀얼 플레이어 충돌 방지

두 플레이어가 같은 키를 사용하면 충돌 → 리바인딩 전 중복 검사 필요:

```csharp
private bool IsKeyAlreadyUsed(string newPath, string excludeActionMap, string excludeAction)
{
    foreach (var actionMap in inputActions.actionMaps)
    {
        foreach (var action in actionMap.actions)
        {
            // 현재 리바인딩 중인 액션은 제외
            if (actionMap.name == excludeActionMap && action.name == excludeAction)
                continue;

            foreach (var binding in action.bindings)
            {
                if (binding.effectivePath == newPath)
                    return true;
            }
        }
    }
    return false;
}
```

리바인딩 완료 콜백에서 중복 검사 후 충돌 시 자동 취소:

```csharp
.OnComplete(operation =>
{
    string newPath = action.bindings[bindingIndex].effectivePath;
    if (IsKeyAlreadyUsed(newPath, actionMapName, actionName))
    {
        // 충돌 → 원래 바인딩 복원
        action.RemoveBindingOverride(bindingIndex);
        ShowConflictWarning();
    }
    // ...
})
```

### 6. 게임패드 + 키보드 혼합 디바이스 설정

Player 1은 게임패드, Player 2는 키보드+마우스 전용으로 고정:

```csharp
// PlayerInput 컴포넌트 설정
// Player 1 GameObject → PlayerInput → Default Control Scheme: Gamepad
// Player 2 GameObject → PlayerInput → Default Control Scheme: KeyboardMouse

// 또는 코드로:
playerInput.SwitchCurrentControlScheme("Gamepad", Gamepad.current);
playerInput2.SwitchCurrentControlScheme("KeyboardMouse", Keyboard.current, Mouse.current);
```

Action Map에서 각 바인딩에 Control Scheme 제한 적용:
- Player1/Move → `Gamepad` 스킴만 활성화
- Player2/Fire → `KeyboardMouse` 스킴만 활성화

---

## OnionCat 적용 포인트

### 설정 메뉴 구조 제안

```
설정 메뉴
├── 음량
│   ├── BGM
│   └── SFX
├── Player 1 조작 (게임패드)
│   ├── 이동: 왼쪽 스틱 (고정, 변경 불가)
│   ├── 대시: South(A) [변경 가능]
│   └── 공격: West(X) [변경 가능]
└── Player 2 조작 (키보드+마우스)
    ├── 조준: 마우스 (고정)
    ├── 발사: 마우스 좌클릭 [변경 가능]
    └── 방패: 마우스 우클릭 [변경 가능]
```

### 구현 순서 (초보 개발자 권장)

1. **InputActionAsset 생성** — Player1, Player2 Action Map 분리
2. **기본 입력 동작 확인** — 리바인딩 없이 게임플레이 완성
3. **PlayerPrefs 저장/불러오기** — 가장 먼저 구현 (재시작 시 유지)
4. **UI 버튼 → 리바인딩 연결** — 버튼 클릭 → `StartRebinding()` 호출
5. **중복 키 검사** — 마지막에 추가 (없어도 게임은 돌아감)

### 주의 사항

- **리바인딩 중 Action 비활성화 필수**: 활성화 상태에서 리바인딩하면 입력이 게임에도 들어감
- **Scene 전환 시 InputActionAsset은 공유 자산**: 씬을 바꿔도 바인딩 오버라이드 유지됨 (PlayerPrefs 로드는 게임 시작 시 1회만)
- **마우스 Position은 리바인딩 불필요**: 마우스 위치는 항상 동일 → Aim Action에서 리바인딩 UI 숨기기
- **게임패드 없을 때**: `Gamepad.current == null` 체크 → Player 1에게 키보드 대체 제공 또는 경고

---

## 참고 링크

- Unity 런타임 리바인딩 공식 문서: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.8/manual/ActionBindings.html#interactive-rebinding
- Input System 바인딩 저장/불러오기: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.8/manual/ActionBindings.html#saving-and-loading-rebinds
- 멀티 플레이어 Input System 설정: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.8/manual/PlayerInputManager.html
- 런타임 리바인딩 튜토리얼 (Unity 공식 블로그): https://blog.unity.com/games/new-input-system-how-to-get-started
