# 기기별 버튼 프롬프트 자동 전환 시스템 (Device-Specific Button Prompt)

리서치 날짜: 2026-11-18

## 개요

게임에 연결된 입력 기기(패드/키보드/마우스)를 감지하고, **UI의 버튼 안내 아이콘을 자동으로 해당 기기에 맞게 교체**하는 시스템.

OnionCat에서 특히 중요한 이유: P1(고양이)은 패드, P2(작물)는 키보드+마우스로 **같은 화면에 두 가지 아이콘 세트가 동시에 필요**하다. 패드 없이 키보드 단독 모드일 때는 P1도 키보드 아이콘으로 전환돼야 한다.

---

## Unity 구현 방법

### Step 1: 입력 기기 감지 (New Input System)

```csharp
using UnityEngine.InputSystem;

public class InputDeviceTracker : MonoBehaviour
{
    // 플레이어별 마지막 사용 기기
    public static InputDevice LastUsed_P1 { get; private set; }
    public static InputDevice LastUsed_P2 { get; private set; }

    public static event Action<int, InputDevice> OnDeviceChanged;

    void OnEnable()
    {
        InputSystem.onActionChange += HandleActionChange;
    }
    void OnDisable()
    {
        InputSystem.onActionChange -= HandleActionChange;
    }

    void HandleActionChange(object action, InputActionChange change)
    {
        if (change != InputActionChange.ActionPerformed) return;
        
        var inputAction = action as InputAction;
        var device = inputAction?.activeControl?.device;
        if (device == null) return;

        // 어느 플레이어의 액션인지 판단 (PlayerInput 컴포넌트 연동)
        int playerId = GetPlayerIdFromAction(inputAction);
        
        if (playerId == 1 && device != LastUsed_P1)
        {
            LastUsed_P1 = device;
            OnDeviceChanged?.Invoke(1, device);
        }
        else if (playerId == 2 && device != LastUsed_P2)
        {
            LastUsed_P2 = device;
            OnDeviceChanged?.Invoke(2, device);
        }
    }
}
```

### Step 2: 기기 종류 분류

```csharp
public enum ControllerType { KeyboardMouse, Gamepad_Xbox, Gamepad_PS, Gamepad_Switch }

public static ControllerType Classify(InputDevice device)
{
    if (device is Keyboard || device is Mouse) return ControllerType.KeyboardMouse;
    
    if (device is Gamepad pad)
    {
        string name = pad.name.ToLower();
        if (name.Contains("dualshock") || name.Contains("dualsense") || name.Contains("ps"))
            return ControllerType.Gamepad_PS;
        if (name.Contains("switch") || name.Contains("joy-con") || name.Contains("pro controller"))
            return ControllerType.Gamepad_Switch;
        // Xbox, Steam Deck, 기타 패드는 Xbox 계열로
        return ControllerType.Gamepad_Xbox;
    }
    return ControllerType.KeyboardMouse;
}
```

### Step 3: 아이콘 에셋 구조 (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "OnionCat/Button Prompt Set")]
public class ButtonPromptSet : ScriptableObject
{
    public ControllerType type;
    
    // 키 → 스프라이트 매핑
    public List<ButtonPromptEntry> entries;
    
    public Sprite Get(string keyName)
        => entries.FirstOrDefault(e => e.keyName == keyName)?.sprite;
}

[Serializable]
public class ButtonPromptEntry
{
    public string keyName;    // "A", "B", "LB", "Space", "LShift" 등
    public Sprite sprite;
}
```

### Step 4: TMP 텍스트에서 아이콘 치환

TextMeshPro의 `<sprite>` 태그를 활용.

```csharp
public class ButtonPromptText : MonoBehaviour
{
    [SerializeField] TMP_Text label;
    [SerializeField] string rawText = "점프: <btn=A>";  // 원본 텍스트
    [SerializeField] int playerId = 1;

    void OnEnable()
    {
        InputDeviceTracker.OnDeviceChanged += Refresh;
        Refresh(0, null);
    }
    void OnDisable()
    {
        InputDeviceTracker.OnDeviceChanged -= Refresh;
    }
    
    void Refresh(int pid, InputDevice _)
    {
        // 이 컴포넌트가 관심 없는 플레이어의 변경은 무시
        // (0은 초기화 호출을 의미)
        
        var device = playerId == 1 ? InputDeviceTracker.LastUsed_P1 
                                   : InputDeviceTracker.LastUsed_P2;
        var type = device != null ? InputDeviceTracker.Classify(device)
                                  : ControllerType.KeyboardMouse;
        
        var set = ButtonPromptManager.GetSet(type);
        string result = Regex.Replace(rawText, @"<btn=(\w+)>", m =>
        {
            string key = m.Groups[1].Value;
            int spriteIndex = set.GetSpriteIndex(key); // TMP 아틀라스 인덱스
            return spriteIndex >= 0 ? $"<sprite={spriteIndex}>" : $"[{key}]";
        });
        
        label.SetText(result);
    }
}
```

### Step 5: 패드 연결/해제 감지 (OnionCat 모드 전환)

```csharp
void OnEnable()
{
    InputSystem.onDeviceChange += HandleDeviceChange;
}

void HandleDeviceChange(InputDevice device, InputDeviceChange change)
{
    if (change == InputDeviceChange.Added && device is Gamepad)
    {
        // 패드 연결 → CoopInputLayout이 패드 모드로 전환
        // 고양이=패드, 작물=마우스+Q/W/E/R
        CoopInputLayout.SetMode(CoopMode.GamepadKeyboard);
    }
    else if (change == InputDeviceChange.Removed && device is Gamepad)
    {
        // 패드 해제 → 키보드 단독 모드
        // 고양이=WASD+Shift+Ctrl, 작물=마우스+1~4
        CoopInputLayout.SetMode(CoopMode.KeyboardOnly);
    }
}
```

---

## OnionCat 적용 포인트

### OnionCat 고유 케이스: 플레이어별 다른 아이콘

```
HUD 튜토리얼 힌트 예시:
- 패드 모드: "고양이 [RB] + 작물 [Space] 동시에 → 합동기!"
- 키보드 모드: "고양이 [E] + 작물 [Space(휠클릭)] 동시에 → 합동기!"
```

P1 아이콘 세트와 P2 아이콘 세트를 **동시에 한 문장에** 표시해야 함.
`ButtonPromptText`에 `playerId` 대신 `List<(int playerId, string key)>` 로 여러 플레이어 키를 처리하도록 확장.

### HUD 버튼 아이콘 위치

OnionCat의 HUD(CoreHUD)에서 버튼 프롬프트가 필요한 위치:
1. **합동기 게이지 옆** — P1+P2 동시 버튼 아이콘
2. **대쉬 충전 PIP 아래** — "대쉬 버튼" 아이콘 (Space/LB)
3. **가방 슬롯 번호** — 키보드 모드 1~5 / 패드 모드 방향키
4. **말풍선 "계속" 프롬프트** — Enter / A버튼

### 구현 순서 (추천)

```
1. ButtonPromptSet SO 2개 만들기 (Xbox, Keyboard)
2. InputDeviceTracker 싱글턴 추가 (GameManager 옆)
3. ButtonPromptText 컴포넌트를 HUD 합동기 아이콘 하나에만 먼저 붙이기
4. 테스트: 패드 뽑았다 꽂으면 아이콘이 바뀌는지 확인
5. 나머지 HUD 위치에 적용 확장
```

---

## 참고 링크

- Unity Input System 기기 감지: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.5/manual/HowDoI.html#how-do-i-know-what-the-current-input-device-is
- TMP Sprite Asset 커스텀 아이콘: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/Sprites.html
- Rewired (유료, 기기 감지 더 강력): https://assetstore.unity.com/packages/tools/utilities/rewired-21676
- 무료 Xbox/PS/Switch 버튼 아이콘 에셋: https://thoseawesomeguys.com/prompts/ (Xelu's FREE Controller Prompts, Creative Commons 0)
- Unity Input System 패드 연결 이벤트: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.5/api/UnityEngine.InputSystem.InputSystem.html#UnityEngine_InputSystem_InputSystem_onDeviceChange
