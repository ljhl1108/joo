# Controller Hot-plug & Device Assignment System (컨트롤러 핫플러그 및 기기 할당)

리서치 날짜: 2026-11-27

## 개요

비대칭 2인 협동 게임에서 컨트롤러가 게임 도중에 연결되거나 끊길 때 적절히 대응하는 시스템.
OnionCat에서:
- **고양이(Player 1)**: 게임패드만 사용
- **양파(Player 2)**: 마우스 + 키보드만 사용

게임패드가 갑자기 끊어지면 고양이 조작이 불가능해지므로 반드시 처리해야 함.

---

## Unity 구현 방법

### 1. 기기 연결/해제 감지

```csharp
using UnityEngine.InputSystem;

public class DeviceMonitor : MonoBehaviour
{
    public static event Action<InputDevice> OnDeviceConnected;
    public static event Action<InputDevice> OnDeviceDisconnected;

    private void OnEnable()
    {
        InputSystem.onDeviceChange += HandleDeviceChange;
    }

    private void OnDisable()
    {
        InputSystem.onDeviceChange -= HandleDeviceChange;
    }

    private void HandleDeviceChange(InputDevice device, InputDeviceChange change)
    {
        switch (change)
        {
            case InputDeviceChange.Added:
            case InputDeviceChange.Reconnected:
                OnDeviceConnected?.Invoke(device);
                break;

            case InputDeviceChange.Removed:
            case InputDeviceChange.Disconnected:
                OnDeviceDisconnected?.Invoke(device);
                break;
        }
    }
}
```

---

### 2. 플레이어별 기기 고정 (Device Pairing)

```csharp
using UnityEngine.InputSystem;

// New Input System의 PlayerInput 없이 직접 관리하는 방식
public class PlayerDeviceManager : MonoBehaviour
{
    // 각 플레이어가 사용하는 기기를 명시적으로 고정
    private InputDevice catDevice;    // Gamepad
    private InputDevice onionDevice;  // Keyboard + Mouse (항상 존재)

    private void Start()
    {
        // 양파는 항상 키보드+마우스
        onionDevice = Keyboard.current;

        // 고양이는 현재 연결된 첫 번째 게임패드
        var gamepads = Gamepad.all;
        if (gamepads.Count > 0)
            catDevice = gamepads[0];

        DeviceMonitor.OnDeviceConnected += OnDeviceConnected;
        DeviceMonitor.OnDeviceDisconnected += OnDeviceDisconnected;
    }

    private void OnDeviceConnected(InputDevice device)
    {
        if (device is Gamepad && catDevice == null)
        {
            catDevice = device;
            Debug.Log($"[DeviceMgr] 게임패드 연결됨: {device.displayName} → 고양이에 할당");
            // 일시정지 해제, 재연결 UI 닫기
            ResumeAfterReconnect();
        }
    }

    private void OnDeviceDisconnected(InputDevice device)
    {
        if (device == catDevice)
        {
            catDevice = null;
            Debug.Log("[DeviceMgr] 고양이 게임패드 연결 끊김 → 일시정지");
            PauseForReconnect();
        }
    }

    // InputAction에서 실제 기기를 필터링할 때 사용
    public bool IsCatDevice(InputDevice device) => device == catDevice;
    public bool IsOnionDevice(InputDevice device) => device == onionDevice || device is Mouse;
}
```

---

### 3. 재연결 대기 UI

```csharp
public class ReconnectScreen : MonoBehaviour
{
    [SerializeField] private GameObject panel;
    [SerializeField] private TMP_Text messageText;

    public void Show(string playerName)
    {
        GameManager.Instance.ChangeState(GameState.Paused); // 게임 일시정지
        panel.SetActive(true);
        messageText.text = $"{playerName}의 컨트롤러 연결이 끊겼습니다.\n컨트롤러를 다시 연결해 주세요.";
    }

    public void Hide()
    {
        panel.SetActive(false);
        GameManager.Instance.ChangeState(GameState.Playing); // 게임 재개
    }
}
```

---

### 4. New Input System PlayerInput 컴포넌트 사용 시

PlayerInput 컴포넌트를 쓰는 경우 더 간단:

```csharp
public class CatInputHandler : MonoBehaviour
{
    private PlayerInput playerInput;

    private void Awake()
    {
        playerInput = GetComponent<PlayerInput>();
        playerInput.onDeviceLost += OnDeviceLost;
        playerInput.onDeviceRegained += OnDeviceRegained;
    }

    private void OnDeviceLost(PlayerInput pi)
    {
        Debug.Log("고양이 컨트롤러 연결 끊김");
        // 자동으로 입력이 멈춤 — 별도 차단 불필요
        FindObjectOfType<ReconnectScreen>().Show("고양이");
    }

    private void OnDeviceRegained(PlayerInput pi)
    {
        Debug.Log("고양이 컨트롤러 재연결");
        FindObjectOfType<ReconnectScreen>().Hide();
    }
}
```

---

### 5. 싱글플레이 대체 (고양이 없이 양파 혼자)

```csharp
// OnionCat에서 Solo Fallback: 게임패드 없을 때 양파가 고양이도 조작
public class CoopInputLayout : MonoBehaviour
{
    public bool IsSoloMode => CatDeviceManager.catDevice == null;

    private void Update()
    {
        // 솔로 모드: 키보드 WASD로 고양이 이동, 마우스로 양파 조작
        if (IsSoloMode)
            ApplySoloKeyboardCatControl();
    }
}
```

---

## OnionCat 적용 포인트

### 현재 구조 확인 사항

OnionCat은 `CoopInputLayout`이 컨트롤 스킴을 자동 전환한다고 CLAUDE.md에 명시됨:
- 패드 모드(패드 연결): 고양이 = 패드 / 양파 = 마우스 + 키보드
- 키보드 모드(패드 없음): 고양이 = WASD 등

이 자동 전환이 `InputSystem.onDeviceChange`를 쓴다면 위 패턴이 이미 구현된 것.
**확인**: `CoopInputLayout.cs`에서 기기 변경 이벤트 구독 여부 체크

### 게임 도중 연결 끊김 처리 체크리스트

```
[ ] 게임패드 연결 끊김 → 자동 일시정지 (실행 중 갑자기 멈추지 않게)
[ ] 재연결 UI 표시 (한글: "고양이 컨트롤러가 끊겼습니다")
[ ] 재연결 감지 → UI 자동 닫힘 + 게임 재개
[ ] 보스 컷씬 / 대화 중 끊기면 → 대화 완료 후 재연결 UI
[ ] 메인 메뉴 / 온실에서 끊기면 → 경고만, 게임 멈추지 않음
```

### 기기 할당 충돌 방지

두 번째 게임패드가 연결되면 고양이가 중복 입력을 받을 수 있음:

```csharp
// 첫 번째 게임패드만 고양이에 할당
// 두 번째 패드는 무시 (또는 "P1용 패드를 선택하세요" UI)
if (device is Gamepad && catDevice != null) return; // 이미 할당됨
```

### 콘솔 발매 고려 시

Steam에서 PS5/Xbox 컨트롤러는 각각 다른 `Gamepad` 서브타입:
```csharp
if (device is DualSenseGamepadHID)      // PS5
if (device is XInputController)          // Xbox
```
버튼 프롬프트 아이콘을 맞출 때 타입 체크 필요.

---

## 참고 링크

- Unity InputSystem Device Events 공식: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/Devices.html
- PlayerInput onDeviceLost: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/api/UnityEngine.InputSystem.PlayerInput.html
- 관련 기술 문서: `Design/References/Tech/Asymmetric_Coop_Input_System.md`, `Design/References/Tech/Local_Coop_Input_System.md`
