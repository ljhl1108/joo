# 컨트롤러 핫플러그 / 재연결 화면

리서치 날짜: 2026-07-14

## 개요

로컬 2인 협동 게임에서 컨트롤러가 갑자기 분리되면 게임을 자동으로 일시정지하고, 재연결을 안내하는 화면을 띄워야 한다.
OnionCat은 고양이(P1, 키보드 or 컨트롤러)와 양파(P2, 마우스 or 컨트롤러)의 입력이 동시에 필요하므로, 한 명의 입력이 끊기면 게임이 사실상 진행 불가 — 핫플러그 처리는 반드시 구현해야 한다.

---

## Unity 구현 방법

### 1. 컨트롤러 연결/해제 감지 (New Input System)

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

public class DeviceConnectionMonitor : MonoBehaviour
{
    void OnEnable()
    {
        InputSystem.onDeviceChange += OnDeviceChange;
    }

    void OnDisable()
    {
        InputSystem.onDeviceChange -= OnDeviceChange;
    }

    void OnDeviceChange(InputDevice device, InputDeviceChange change)
    {
        switch (change)
        {
            case InputDeviceChange.Disconnected:
                Debug.Log($"Device disconnected: {device.displayName}");
                OnControllerDisconnected(device);
                break;
            case InputDeviceChange.Reconnected:
                Debug.Log($"Device reconnected: {device.displayName}");
                OnControllerReconnected(device);
                break;
        }
    }

    void OnControllerDisconnected(InputDevice device)
    {
        // 어떤 플레이어의 기기인지 확인
        var playerInput = FindPlayerUsingDevice(device);
        if (playerInput != null)
        {
            GameManager.Instance.PauseForReconnect(playerInput.playerIndex);
        }
    }

    void OnControllerReconnected(InputDevice device)
    {
        // 재연결 시 자동 감지 or 버튼 누르면 재개
        GameManager.Instance.TryResumeAfterReconnect();
    }

    PlayerInput FindPlayerUsingDevice(InputDevice device)
    {
        foreach (var player in PlayerInput.all)
        {
            if (player.devices.Contains(device))
                return player;
        }
        return null;
    }
}
```

---

### 2. 재연결 UI 화면 제어

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class ReconnectScreen : MonoBehaviour
{
    [SerializeField] private GameObject panel;
    [SerializeField] private TextMeshProUGUI messageText;
    [SerializeField] private Image playerIcon;

    public void Show(int playerIndex)
    {
        panel.SetActive(true);
        Time.timeScale = 0f; // 게임 일시정지
        messageText.text = $"P{playerIndex + 1} 컨트롤러 연결이 끊어졌습니다.\n컨트롤러를 연결하면 자동으로 재개됩니다.";
    }

    public void Hide()
    {
        panel.SetActive(false);
        Time.timeScale = 1f; // 재개
    }
}
```

---

### 3. GameManager 연동

```csharp
public class GameManager : Singleton<GameManager>
{
    [SerializeField] private ReconnectScreen reconnectScreen;
    
    private bool _waitingForReconnect = false;
    private int _disconnectedPlayerIndex = -1;

    public void PauseForReconnect(int playerIndex)
    {
        _waitingForReconnect = true;
        _disconnectedPlayerIndex = playerIndex;
        reconnectScreen.Show(playerIndex);
    }

    public void TryResumeAfterReconnect()
    {
        if (!_waitingForReconnect) return;
        
        // 모든 플레이어의 기기가 연결됐는지 확인
        if (AllPlayersConnected())
        {
            _waitingForReconnect = false;
            _disconnectedPlayerIndex = -1;
            reconnectScreen.Hide();
        }
    }

    bool AllPlayersConnected()
    {
        foreach (var player in PlayerInput.all)
        {
            if (player.devices.Count == 0) return false;
        }
        return true;
    }
}
```

---

### 4. PlayerInput Manager 설정 (Inspector)

PlayerInputManager를 씬에 추가:
```
PlayerInputManager
  - Joining Behavior: Join Players Manually
  - Player Prefab: [PlayerPrefab 드래그]
  - Max Player Count: 2
```

각 PlayerInput 컴포넌트:
```
PlayerInput
  - Behavior: Invoke Unity Events
  - Actions: [InputActionAsset 드래그]
  - Default Control Scheme: Auto (또는 Gamepad/KeyboardMouse)
```

---

### 5. 재연결 후 입력 디바이스 재할당

컨트롤러를 뺐다 꽂으면 다른 기기로 인식될 수 있음:

```csharp
void OnControllerReconnected(InputDevice device)
{
    // 재연결된 기기를 해당 플레이어에 다시 페어링
    if (_disconnectedPlayerIndex >= 0 && PlayerInput.all.Count > _disconnectedPlayerIndex)
    {
        var player = PlayerInput.all[_disconnectedPlayerIndex];
        player.SwitchCurrentControlScheme(device);
    }
    TryResumeAfterReconnect();
}
```

---

### 6. "어느 버튼이든 누르면 재개" 방식 (더 심플)

재연결 감지가 복잡하다면, UI에서 버튼 입력 대기:

```csharp
// ReconnectScreen.cs
void Update()
{
    if (!panel.activeSelf) return;
    
    // 어떤 게임패드 버튼이든 누르면 재개 시도
    if (Gamepad.all.Count >= 2) // 두 개 이상 연결됐으면
    {
        foreach (var gp in Gamepad.all)
        {
            if (gp.buttonSouth.wasPressedThisFrame)
            {
                GameManager.Instance.TryResumeAfterReconnect();
                break;
            }
        }
    }
}
```

---

### 7. UI 디자인 가이드

```
┌─────────────────────────────────────────┐
│                                         │
│   [P2 아이콘 + 깜빡이는 효과]             │
│                                         │
│   P2 컨트롤러 연결이 끊어졌습니다.        │
│                                         │
│   컨트롤러를 다시 연결해주세요.           │
│                                         │
│   [연결 기다리는 애니메이션 (점 3개)]      │
│                                         │
│   [ESC] 메인 메뉴로  [계속 대기]         │
│                                         │
└─────────────────────────────────────────┘
```

- **배경**: 반투명 어두운 오버레이 (게임 화면이 보이도록)
- **P1/P2 식별**: 색상으로 구분 (고양이=주황, 양파=초록)
- **대기 애니메이션**: DOTween으로 점 깜빡임
- **ESC 옵션**: 재연결 안 되면 메뉴로 나갈 수 있게

---

## OnionCat 적용 포인트

### 1. 언제 핫플러그가 필요한가
- P1(고양이)이 키보드+마우스, P2(양파)가 컨트롤러인 경우
- P1 컨트롤러, P2 컨트롤러인 경우 (플레이 스타일 다양화)
- 인 게임 중 컨트롤러 배터리 방전 → 갑자기 P2 입력 없어짐

### 2. OnionCat 특수 고려사항
- 고양이+양파가 **한 몸** → P2 입력 없으면 이동 + 원거리 동시 불가
- 보스전 중 끊기면? → 자동 일시정지 필수
- **재연결 화면에서도 P1은 안전하게 대기** → 적 AI 일시정지 포함

### 3. 구현 우선순위 (초보자용)
1. `InputSystem.onDeviceChange` 이벤트 구독 (즉시 감지)
2. 감지 시 `Time.timeScale = 0` + 재연결 UI 표시
3. 재연결 후 버튼 입력으로 재개 (자동 재개보다 안전)
4. (선택) 메인 메뉴로 이동 버튼 제공

### 4. 씬 배치
- `DeviceConnectionMonitor.cs`는 **DontDestroyOnLoad** 오브젝트에 부착
- `ReconnectScreen` UI는 인게임 씬의 Canvas에 배치 (처음엔 비활성화)
- `유니티 에디터에서 드래그 앤 드롭 설정 필요`: ReconnectScreen 패널, 메시지 텍스트, P1/P2 아이콘

---

## 참고 링크

- Unity 공식 - Input System Device Callbacks: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/Devices.html#monitoring-devices
- Unity 공식 - PlayerInput Component: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInput.html
- Unity Input System Device Pairing: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html
- 유튜브 - "Unity Input System Controller Disconnect": 검색 권장
- Unity Forum - Controller Hot Plug Example: https://forum.unity.com/threads/input-system-detect-gamepad-disconnect.859600/
