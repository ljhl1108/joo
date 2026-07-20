# 컨트롤러 UI 프롬프트 & 아이콘 시스템

리서치 날짜: 2026-07-20

## 개요

게임 내 UI에서 현재 연결된 입력 장치에 맞춰 버튼 아이콘을 자동으로 교체하는 시스템.
예) "공격: [X]" → Xbox 패드 연결 시 Xbox X 버튼 아이콘, PS5 연결 시 Cross 버튼 아이콘, 키보드 연결 시 "Z 키" 아이콘.

OnionCat은 2인 로컬 코업으로 P1(Cat)과 P2(Crop)가 각각 다른 컨트롤러를 쓸 수 있어, **두 플레이어 각각의 아이콘을 독립적으로 표시**해야 한다.

---

## Unity 구현 방법

### 1. Input System 장치 감지

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

public enum ControlSchemeType { KeyboardMouse, Xbox, PlayStation, Switch, Generic }

public static class InputDeviceDetector
{
    public static ControlSchemeType GetScheme(PlayerInput playerInput)
    {
        if (playerInput == null) return ControlSchemeType.KeyboardMouse;

        string scheme = playerInput.currentControlScheme;
        // currentControlScheme: "Keyboard&Mouse", "Gamepad" 등

        var device = playerInput.devices.Count > 0 ? playerInput.devices[0] : null;
        if (device == null) return ControlSchemeType.KeyboardMouse;

        string deviceName = device.displayName.ToLower();

        if (deviceName.Contains("keyboard")) return ControlSchemeType.KeyboardMouse;
        if (deviceName.Contains("xbox") || deviceName.Contains("xinput"))
            return ControlSchemeType.Xbox;
        if (deviceName.Contains("dualshock") || deviceName.Contains("dualsense")
            || deviceName.Contains("playstation"))
            return ControlSchemeType.PlayStation;
        if (deviceName.Contains("switch") || deviceName.Contains("joy-con"))
            return ControlSchemeType.Switch;

        return ControlSchemeType.Generic; // 기타 게임패드
    }
}
```

### 2. 버튼 아이콘 데이터 ScriptableObject

```csharp
[CreateAssetMenu(menuName = "OnionCat/Button Icon Set")]
public class ButtonIconSet : ScriptableObject
{
    [System.Serializable]
    public struct ButtonIcon
    {
        public string actionName;   // e.g. "Attack", "Dash", "Shield"
        public Sprite icon;
    }

    public ControlSchemeType schemeType;
    public ButtonIcon[] icons;

    public Sprite GetIcon(string actionName)
    {
        foreach (var b in icons)
            if (b.actionName == actionName) return b.icon;
        return null;
    }
}
```

### 3. 아이콘 관리자

```csharp
public class InputIconManager : MonoBehaviour
{
    public static InputIconManager Instance { get; private set; }

    [SerializeField] private ButtonIconSet[] iconSets; // 각 스킴별 아이콘 세트

    void Awake()
    {
        Instance = this;
        // 두 플레이어 모두 장치 변경 이벤트 구독
        InputSystem.onDeviceChange += OnDeviceChange;
    }

    void OnDestroy() => InputSystem.onDeviceChange -= OnDeviceChange;

    void OnDeviceChange(InputDevice device, InputDeviceChange change)
    {
        // 장치가 추가/제거될 때 모든 프롬프트 UI 갱신
        RefreshAllPrompts();
    }

    public Sprite GetIcon(PlayerInput playerInput, string actionName)
    {
        ControlSchemeType scheme = InputDeviceDetector.GetScheme(playerInput);
        foreach (var set in iconSets)
            if (set.schemeType == scheme)
                return set.GetIcon(actionName);
        return null;
    }

    void RefreshAllPrompts()
    {
        foreach (var prompt in FindObjectsByType<ButtonPromptUI>(FindObjectsSortMode.None))
            prompt.Refresh();
    }
}
```

### 4. 프롬프트 UI 컴포넌트

```csharp
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.InputSystem;

public class ButtonPromptUI : MonoBehaviour
{
    [SerializeField] private Image iconImage;
    [SerializeField] private string actionName; // "Attack", "Dash", "Shield"
    [SerializeField] private int playerIndex;   // 0 = P1 Cat, 1 = P2 Crop

    private PlayerInput cachedPlayerInput;

    void Start()
    {
        // PlayerInput 캐싱 (GameManager나 PlayerManager에서 가져옴)
        cachedPlayerInput = PlayerManager.Instance.GetPlayerInput(playerIndex);
        Refresh();
    }

    public void Refresh()
    {
        if (cachedPlayerInput == null) return;
        Sprite icon = InputIconManager.Instance.GetIcon(cachedPlayerInput, actionName);
        if (icon != null) iconImage.sprite = icon;
    }
}
```

### 5. 두 플레이어 독립 추적 (OnionCat 전용)

```csharp
// P1(Cat)의 컨트롤러가 Xbox, P2(Crop)가 키보드일 때 각각 다른 아이콘
// PlayerManager에서:

public class PlayerManager : MonoBehaviour
{
    public static PlayerManager Instance { get; private set; }
    
    [SerializeField] private PlayerInput p1Input; // Cat
    [SerializeField] private PlayerInput p2Input; // Crop

    void Awake() => Instance = this;

    public PlayerInput GetPlayerInput(int index)
        => index == 0 ? p1Input : p2Input;
}
```

---

### 6. 아이콘 에셋 준비 팁

**무료 아이콘 리소스:**
- [Xelu's Free Controllers & Keyboard Prompts](https://thoseawesomeguys.com/prompts/) — Xbox/PS/Switch/키보드 모두 포함, 상업용 무료
- [Kenney Input Prompts](https://kenney.nl/assets/input-prompts) — 벡터 기반, 크기 조절 용이
- **권장**: 각 스킴당 최소 10개 버튼 아이콘 준비 (주요 액션 버튼만)

**아이콘 Sprite Atlas 설정:**
- Window > 2D > Sprite Atlas로 하나의 Atlas에 묶기
- Pixels Per Unit = 게임 픽셀 사이즈에 맞게 (예: 16px 버튼 아이콘이면 16)

---

### 7. 버튼 바인딩 텍스트 자동화 (심화)

Input System의 `InputActionReference`를 활용하면 바인딩 경로에서 직접 텍스트 읽기 가능:

```csharp
// 바인딩 표시 이름 가져오기
InputActionReference actionRef; // Inspector에서 할당

string GetBindingText(PlayerInput playerInput, InputActionReference actionRef)
{
    var action = actionRef.action;
    int bindingIndex = action.GetBindingIndexForControl(
        playerInput.devices[0], // 현재 장치
        InputBinding.MaskByGroup(playerInput.currentControlScheme));
    return action.GetBindingDisplayString(bindingIndex);
    // → "A", "Cross", "Z" 등 자동 반환
}
```

---

## OnionCat 적용 포인트

### 적용 위치
| UI 위치 | 표시 내용 |
|---|---|
| HUD P1 영역 | Cat 액션 버튼 (공격, 대시) 아이콘 |
| HUD P2 영역 | Crop 액션 버튼 (발사, 방어, 조준) 아이콘 |
| 튜토리얼 팝업 | 해당 플레이어 기준 아이콘 표시 |
| 일시정지 메뉴 | 컨트롤 가이드에 현재 장치 아이콘 |
| 업그레이드 선택 | P1/P2 확인 버튼 아이콘 |

### 스킴 우선순위
1. 두 플레이어 모두 게임패드 → 각각 아이콘 표시
2. P1 게임패드 + P2 키보드 → 혼합 표시 (OnionCat에서 가장 일반적인 경우)
3. 두 플레이어 모두 키보드 → WASD 컨트롤(Cat) / 마우스+방향키(Crop) 아이콘

### 구현 순서 (개발 단계)
1. Kenney/Xelu 무료 아이콘 다운로드
2. ButtonIconSet ScriptableObject 각 스킴별 생성 (Xbox, PS, 키보드)
3. InputIconManager를 GameManager에 싱글턴으로 추가
4. HUD의 버튼 설명 Image 컴포넌트에 ButtonPromptUI 부착
5. 씬 로드 시 & 장치 변경 시 자동 Refresh 연결

---

## 참고 링크

- [Unity Input System Docs: PlayerInput](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInput.html)
- [Xelu's Free Prompts (상업용 무료)](https://thoseawesomeguys.com/prompts/)
- [Kenney Input Prompts](https://kenney.nl/assets/input-prompts)
- [Unity Input System: GetBindingDisplayString](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/api/UnityEngine.InputSystem.InputActionExtensions.html)
- [Brackeys: Controller Icons in Unity](https://www.youtube.com/c/Brackeys)
- [Samyam: Dynamic Button Prompts Unity](https://www.youtube.com/c/samyam)
