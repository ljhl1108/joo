# 런타임 입력 리바인딩 UI (Runtime Key Rebinding UI)

리서치 날짜: 2026-07-15

## 개요

플레이어가 인게임 설정 메뉴에서 키/버튼을 직접 바꿀 수 있는 기능.  
Unity New Input System에는 `PerformInteractiveRebinding()` API가 내장되어 있어  
별도 라이브러리 없이 구현 가능하다.

OnionCat에서 필요한 이유:
- Player 1(게임패드)과 Player 2(키보드+마우스)의 조작키가 다름
- 두 플레이어 모두 자신의 키 배치를 커스텀할 수 있어야 함
- 저장/불러오기로 다음 세션에도 유지

---

## Unity 구현 방법

### 1. InputActionAsset 준비

```
Project/Assets/Settings/InputActions.inputactions
  ├── Player1 Action Map (Gamepad)
  │     ├── Move (Left Stick / WASD)
  │     ├── Slash (South Button / J)
  │     └── Dash (East Button / Shift)
  └── Player2 Action Map (Keyboard+Mouse)
        ├── Aim (Mouse Position)
        ├── Shoot (Left Mouse Button)
        └── Shield (Right Mouse Button)
```

- Inspector에서 Action Map → 바인딩마다 Control Scheme 지정
- `PlayerInput` 컴포넌트의 `Actions`에 해당 Asset 연결

### 2. 리바인딩 매니저

```csharp
using UnityEngine;
using UnityEngine.InputSystem;
using System;

public class RebindingManager : MonoBehaviour
{
    private InputActionAsset _actions;
    private InputActionRebindingExtensions.RebindingOperation _rebindOp;

    // PlayerPrefs 저장 키
    private const string SAVE_KEY = "InputBindingOverrides";

    private void Awake()
    {
        // PlayerInput 컴포넌트에서 Actions 참조 (또는 직접 할당)
        _actions = GetComponent<PlayerInput>().actions;
        LoadBindings();
    }

    /// <summary>
    /// 리바인딩 시작. UI에서 버튼 클릭 시 호출.
    /// </summary>
    /// <param name="actionName">Action 이름 (예: "Player1/Slash")</param>
    /// <param name="bindingIndex">0부터 시작하는 바인딩 인덱스</param>
    /// <param name="onComplete">완료 콜백 (UI 갱신용)</param>
    public void StartRebinding(string actionName, int bindingIndex, Action<string> onComplete)
    {
        var action = _actions.FindAction(actionName);
        if (action == null) return;

        // 리바인딩 중엔 액션 비활성화 필수
        action.Disable();

        _rebindOp = action.PerformInteractiveRebinding(bindingIndex)
            .WithCancelingThrough("<Keyboard>/escape")   // ESC로 취소
            .WithControlsExcluding("Mouse/position")     // 마우스 이동 제외
            .WithControlsExcluding("Mouse/scroll")
            .OnMatchWaitForAnother(0.1f)                 // 동시 입력 구분 대기
            .OnComplete(op =>
            {
                string newPath = op.selectedControl.path;
                op.Dispose();
                _rebindOp = null;

                action.Enable();
                SaveBindings();

                // 표시용 이름 반환 (예: "S Key", "A Button (Gamepad)")
                string displayName = InputControlPath.ToHumanReadableString(
                    action.bindings[bindingIndex].effectivePath,
                    InputControlPath.HumanReadableStringOptions.OmitDevice);
                onComplete?.Invoke(displayName);
            })
            .OnCancel(op =>
            {
                op.Dispose();
                _rebindOp = null;
                action.Enable();
                onComplete?.Invoke(null); // null → 취소 신호
            })
            .Start();
    }

    /// <summary>ESC 등으로 리바인딩 강제 취소</summary>
    public void CancelRebinding()
    {
        _rebindOp?.Cancel();
    }

    /// <summary>특정 Action의 바인딩을 기본값으로 초기화</summary>
    public void ResetToDefault(string actionName)
    {
        var action = _actions.FindAction(actionName);
        action?.RemoveAllBindingOverrides();
        SaveBindings();
    }

    private void SaveBindings()
    {
        string json = _actions.SaveBindingOverridesAsJson();
        PlayerPrefs.SetString(SAVE_KEY, json);
        PlayerPrefs.Save();
    }

    private void LoadBindings()
    {
        if (PlayerPrefs.HasKey(SAVE_KEY))
        {
            string json = PlayerPrefs.GetString(SAVE_KEY);
            _actions.LoadBindingOverridesFromJson(json);
        }
    }
}
```

### 3. UI — 리바인딩 버튼 하나의 구조

```csharp
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class RebindButton : MonoBehaviour
{
    [SerializeField] private string actionName;       // "Player1/Slash"
    [SerializeField] private int bindingIndex = 0;
    [SerializeField] private TextMeshProUGUI bindingLabel;  // 현재 키 이름 표시
    [SerializeField] private GameObject waitingOverlay;     // "아무 키나 누르세요" 패널
    [SerializeField] private RebindingManager rebindManager;

    private void Start() => RefreshLabel();

    public void OnRebindButtonClicked()
    {
        waitingOverlay.SetActive(true);

        rebindManager.StartRebinding(actionName, bindingIndex, result =>
        {
            waitingOverlay.SetActive(false);
            if (result != null) bindingLabel.text = result;
        });
    }

    private void RefreshLabel()
    {
        // 현재 적용된 바인딩 이름을 가져와 표시
        var action = rebindManager.GetComponent<PlayerInput>().actions.FindAction(actionName);
        if (action == null) return;

        string path = action.bindings[bindingIndex].effectivePath;
        bindingLabel.text = InputControlPath.ToHumanReadableString(
            path, InputControlPath.HumanReadableStringOptions.OmitDevice);
    }
}
```

### 4. 충돌(Conflict) 감지

```csharp
// 리바인딩 완료 후 다른 Action과 같은 키인지 체크
private bool HasConflict(InputAction targetAction, int bindingIdx)
{
    string newPath = targetAction.bindings[bindingIdx].effectivePath;
    foreach (var action in _actions)
    {
        if (action == targetAction) continue;
        foreach (var binding in action.bindings)
        {
            if (binding.effectivePath == newPath) return true;
        }
    }
    return false;
}
```

### 5. OnionCat 2플레이어 분리 저장

플레이어 1과 2가 다른 Action Map을 쓰므로, 저장 키를 분리:
```csharp
private const string P1_SAVE_KEY = "P1_InputOverrides";
private const string P2_SAVE_KEY = "P2_InputOverrides";
```

---

## OnionCat 적용 포인트

### 설정 메뉴 레이아웃

```
[설정] - 조작 설정
┌─────────────────────────────────────┐
│ Player 1 (고양이)                   │
│ 이동     : [WASD]        [변경]     │
│ 근접공격 : [J]           [변경]     │
│ 대시     : [Shift]       [변경]     │
├─────────────────────────────────────┤
│ Player 2 (크롭)                     │
│ 조준     : [마우스]      (고정)     │
│ 사격     : [좌클릭]      [변경]     │
│ 방어막   : [우클릭]      [변경]     │
├─────────────────────────────────────┤
│          [기본값 초기화]            │
└─────────────────────────────────────┘
```

### 주의 사항

1. **리바인딩 중엔 반드시 해당 Action 비활성화** — `action.Disable()` 빠뜨리면 리바인딩 도중 게임에 입력됨
2. **마우스 이동(position/delta) 제외 설정** — 그냥 마우스를 움직이면 즉시 바인딩됨
3. **UI 네비게이션 Action 분리** — UI용 Action Map(Submit, Cancel)은 리바인딩 대상에서 제외
4. **게임패드 버튼 이름 표시** — `InputControlPath.ToHumanReadableString()`이 "Button South"처럼 영문으로 나올 수 있음 → 아이콘 매핑 딕셔너리 별도 준비

---

## 참고 링크

- [Unity Docs - PerformInteractiveRebinding()](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/api/UnityEngine.InputSystem.InputActionRebindingExtensions.html)
- [Unity Learn - Rebinding Input Controls at Runtime](https://learn.unity.com/tutorial/rebinding-input-controls-at-runtime)
- [Tarodev - Input Rebinding in Unity New Input System (YouTube)](https://www.youtube.com/watch?v=TD0R5x0yL0Y)
- [Unity Forum - SaveBindingOverridesAsJson](https://forum.unity.com/threads/saving-binding-overrides.838849/)
- [Unity Input System GitHub - Rebinding Example](https://github.com/Unity-Technologies/InputSystem/blob/develop/Assets/Samples/RebindingUI/RebindingUI.cs)
