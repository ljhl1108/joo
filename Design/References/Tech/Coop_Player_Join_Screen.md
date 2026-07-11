# 협동 플레이 준비 화면 (Co-op Player Join / Ready Screen)

리서치 날짜: 2026-07-11

## 개요

로컬 협동 게임에서 두 플레이어가 각자 컨트롤러·키보드를 누르면 합류 확인하고, 모두 준비 완료(Ready) 시 게임이 시작되는 씬.  
OnionCat은 **2인 로컬 협동** 고정이므로, "Player 1 합류 → Player 2 합류 → 둘 다 Ready → 게임 시작" 흐름을 처리해야 한다.  
Unity New Input System의 **PlayerInputManager**를 사용하면 기기 자동 감지와 플레이어 스폰을 간단하게 구현할 수 있다.

---

## Unity 구현 방법

### 1. 전체 흐름

```
MainMenu 씬
  → [시작 버튼]
    → PlayerJoin 씬 (준비 화면)
      → 두 플레이어 모두 Ready
        → GamePlay 씬 (본 게임)
```

### 2. PlayerInputManager 설정

New Input System의 핵심 컴포넌트. 빈 GameObject에 추가.

Inspector 설정:
- **Joining Behavior**: Join Players When Button Is Pressed
- **Player Prefab**: PlayerJoinSlot 프리팹 (준비 화면용)
- **Max Player Count**: 2
- **Notification Behavior**: Invoke Unity Events

```csharp
// PlayerJoinManager.cs
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

public class PlayerJoinManager : MonoBehaviour
{
    [SerializeField] private PlayerInputManager inputManager;
    [SerializeField] private PlayerJoinSlot[] slots;  // UI 슬롯 2개

    private bool[] readyStates = new bool[2];
    private int joinedCount = 0;

    void Awake()
    {
        inputManager.onPlayerJoined += OnPlayerJoined;
        inputManager.onPlayerLeft   += OnPlayerLeft;
    }

    void OnDestroy()
    {
        inputManager.onPlayerJoined -= OnPlayerJoined;
        inputManager.onPlayerLeft   -= OnPlayerLeft;
    }

    private void OnPlayerJoined(PlayerInput player)
    {
        int index = player.playerIndex;  // 0 또는 1
        slots[index].SetJoined(player);
        joinedCount++;
        readyStates[index] = false;
    }

    private void OnPlayerLeft(PlayerInput player)
    {
        int index = player.playerIndex;
        slots[index].SetEmpty();
        joinedCount--;
        readyStates[index] = false;
    }

    public void SetReady(int playerIndex, bool ready)
    {
        readyStates[playerIndex] = ready;
        slots[playerIndex].SetReady(ready);
        CheckAllReady();
    }

    private void CheckAllReady()
    {
        if (joinedCount == 2 && readyStates[0] && readyStates[1])
            StartGame();
    }

    private void StartGame()
    {
        // 합류 시 생성된 PlayerInput 오브젝트를 다음 씬으로 유지
        DontDestroyOnLoad(inputManager.gameObject);
        SceneManager.LoadScene("GamePlay");
    }
}
```

### 3. PlayerJoinSlot (UI 슬롯)

각 플레이어 슬롯의 상태를 표시하는 UI 컴포넌트.

```csharp
// PlayerJoinSlot.cs
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class PlayerJoinSlot : MonoBehaviour
{
    [SerializeField] private GameObject emptyPanel;
    [SerializeField] private GameObject joinedPanel;
    [SerializeField] private GameObject readyPanel;
    [SerializeField] private TextMeshProUGUI deviceNameText;
    [SerializeField] private Image characterImage;

    private PlayerJoinInput playerJoinInput;

    public void SetEmpty()
    {
        emptyPanel.SetActive(true);
        joinedPanel.SetActive(false);
        readyPanel.SetActive(false);
    }

    public void SetJoined(UnityEngine.InputSystem.PlayerInput player)
    {
        emptyPanel.SetActive(false);
        joinedPanel.SetActive(true);
        readyPanel.SetActive(false);

        // 어떤 기기로 합류했는지 표시
        string device = player.currentControlScheme;
        deviceNameText.text = device == "Keyboard&Mouse" ? "키보드 + 마우스" : "게임패드";

        // ReadyInput 스크립트 연결
        playerJoinInput = player.GetComponent<PlayerJoinInput>();
    }

    public void SetReady(bool isReady)
    {
        joinedPanel.SetActive(!isReady);
        readyPanel.SetActive(isReady);
    }
}
```

### 4. PlayerJoinInput (각 플레이어 입력 처리)

합류 후 "Ready 버튼"을 처리하는 스크립트. PlayerInput과 같은 GameObject에 부착.

```csharp
// PlayerJoinInput.cs
using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerJoinInput : MonoBehaviour
{
    private bool isReady = false;
    private PlayerJoinManager manager;

    void Start()
    {
        manager = FindObjectOfType<PlayerJoinManager>();
    }

    // Input System Action Map에서 호출됨
    public void OnReady(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed) return;
        isReady = !isReady;
        manager.SetReady(GetComponent<PlayerInput>().playerIndex, isReady);
    }

    public void OnLeave(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed) return;
        GetComponent<PlayerInput>().DestroyIfDeviceNoLongerAvailable();
        Destroy(gameObject);
    }
}
```

### 5. Input Action 설정

- Action Map: "UI" 또는 별도 "JoinScreen"
- **Ready** 액션: 게임패드 South 버튼 (A/X), 키보드 Enter
- **Leave** 액션: 게임패드 East 버튼 (B/O), 키보드 Escape

### 6. OnionCat 특수 처리: 비대칭 조작

OnionCat은 P1(고양이)은 키보드 또는 게임패드, P2(양파)는 마우스 + 키보드.  
이 경우 **두 기기를 한 플레이어로 묶는 것은 불가능**하므로, 대신 고정 배분 방식 사용:

```csharp
// 간단 고정 배분 방식 (OnionCat 전용)
// PlayerInputManager 대신 직접 관리

public class OnionCatJoinManager : MonoBehaviour
{
    // P1: 게임패드 또는 키보드 WASD
    // P2: 마우스 (항상 합류된 것으로 간주)
    
    [SerializeField] private PlayerJoinSlot p1Slot;
    [SerializeField] private PlayerJoinSlot p2Slot;

    private bool p1Ready = false;
    private bool p2Ready = false;

    void Start()
    {
        // P2(양파/마우스)는 항상 합류 완료 표시
        p2Slot.ShowAutoJoined("마우스 조준");
    }

    void Update()
    {
        // P1 준비: Enter 또는 게임패드 A
        if (Input.GetKeyDown(KeyCode.Return) || /* gamepad A */ false)
        {
            p1Ready = !p1Ready;
            p1Slot.SetReady(p1Ready);
            CheckStart();
        }

        // P2 준비: 마우스 클릭 (별도 UI 버튼 클릭)
    }

    public void OnP2ReadyClicked()
    {
        p2Ready = !p2Ready;
        p2Slot.SetReady(p2Ready);
        CheckStart();
    }

    void CheckStart()
    {
        if (p1Ready && p2Ready)
            SceneManager.LoadScene("GamePlay");
    }
}
```

### 7. UI 구성 예시

```
[준비 화면 레이아웃]

┌─────────────────────────────────────────┐
│           OnionCat — 플레이어 준비       │
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │  PLAYER 1   │    │  PLAYER 2   │    │
│  │  🐱 고양이  │    │  🧅 양파    │    │
│  │             │    │             │    │
│  │ [키보드/패드]│    │ [마우스]    │    │
│  │             │    │             │    │
│  │ ENTER=준비  │    │ 클릭=준비   │    │
│  │  [ 대기중 ] │    │  [ 준비! ] │    │
│  └─────────────┘    └─────────────┘    │
│                                         │
│         둘 다 준비하면 시작!             │
└─────────────────────────────────────────┘
```

---

## OnionCat 적용 포인트

### A. 준비 화면의 목적

- 두 플레이어에게 **각자의 조작 방식**을 미리 알려주는 화면
- 고양이: WASD 이동, Space 슬래시, Shift 대쉬
- 양파: 마우스 조준·발사, RMB 방패
- 컨트롤 요약을 이 화면에 표시 → 튜토리얼 부담 감소

### B. 캐릭터 소개 삽입

- 준비 화면에서 고양이·양파 애니메이션 루프 재생 (Idle 상태)
- 플레이어가 Ready 하면 애니메이션이 "점프" 또는 "환호" 동작으로 변경

### C. 씬 간 플레이어 정보 유지

```csharp
// GameData.cs (DontDestroyOnLoad 싱글톤)
public static bool P1UsingGamepad = false;
public static bool P2UsingMouse   = true;  // OnionCat 고정
```

### D. 간단 구현 우선순위

초보 개발자이므로 복잡한 PlayerInputManager 대신 **OnionCat 고정 배분 방식**을 먼저 구현하는 것을 권장:
1. P2(양파/마우스)는 항상 합류 완료 표시
2. P1(고양이)만 "준비 버튼" 제공
3. 둘 다 Ready 누르면 시작

이후 컨트롤러 지원 추가 시 PlayerInputManager로 리팩토링.

---

## 참고 링크

- Unity PlayerInputManager 공식 문서: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html
- Local Multiplayer Setup 가이드: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/LocalMultiplayer.html
- 유튜브: "Unity Local Co-op Setup New Input System" (Tarodev 채널 추천)
- 유튜브: "Unity Player Join Screen" (Code Monkey 채널 추천)
