# 컨트롤러 페어링 & 2인 세션 시작 화면

리서치 날짜: 2026-06-28

## 개요

2인 로컬 Co-op 게임에서 게임 시작 전, 두 플레이어가 자신의 입력 장치(키보드, 게임패드)를 역할(Cat/Onion)에 배정하는 화면.
"Press any button to join" 방식으로 자연스럽게 진입 → 역할 선택 → 준비 확인 순서.
Unity의 New Input System `PlayerInputManager`를 활용하면 장치 자동 감지 + 분리 관리가 간결해진다.

---

## Unity 구현 방법

### 1. 전체 흐름

```
메인 메뉴 → [2인 시작 선택]
    ↓
컨트롤러 페어링 화면
    ├── "Press any button to join" (P1 먼저)
    ├── P1 입력 → Cat 역할 배정 + 조작법 표시
    ├── "Press any button to join" (P2)
    ├── P2 입력 → Onion 역할 배정 + 조작법 표시
    └── 둘 다 Ready 확인 → GameplayScene 로드
```

---

### 2. PlayerInputManager 세팅

```csharp
// 씬에 PlayerInputManager 컴포넌트를 가진 빈 오브젝트 배치
// Inspector 설정:
//   Join Behavior: Join Players When Button Is Pressed
//   Player Prefab: (없음 — 로비에서는 PlayerInput만 생성)
//   Notification Behavior: Invoke Unity Events

public class LobbyManager : MonoBehaviour
{
    [SerializeField] private PlayerInputManager _pim;
    [SerializeField] private LobbySlotUI[] _slots; // 인덱스 0=Cat, 1=Onion

    private List<PlayerInput> _joined = new();

    void Awake()
    {
        _pim.onPlayerJoined += OnPlayerJoined;
    }

    private void OnPlayerJoined(PlayerInput pi)
    {
        int idx = _joined.Count; // 0이면 Cat, 1이면 Onion
        if (idx >= 2) { Destroy(pi.gameObject); return; }

        _joined.Add(pi);
        _slots[idx].Show(pi, idx == 0 ? "Cat (P1)" : "Onion (P2)");
    }
}
```

---

### 3. LobbySlotUI — 역할 패널

```csharp
public class LobbySlotUI : MonoBehaviour
{
    [SerializeField] private GameObject _waitingPanel;
    [SerializeField] private GameObject _joinedPanel;
    [SerializeField] private TMP_Text _deviceLabel;
    [SerializeField] private TMP_Text _controlsLabel;
    [SerializeField] private Button _readyButton;

    public bool IsReady { get; private set; }

    public void Show(PlayerInput pi, string roleName)
    {
        _waitingPanel.SetActive(false);
        _joinedPanel.SetActive(true);

        string device = pi.currentControlScheme; // "Keyboard&Mouse" or "Gamepad"
        _deviceLabel.text = $"{roleName} — {device}";
        _controlsLabel.text = GetControlsHint(roleName, device);

        _readyButton.onClick.AddListener(OnReady);
    }

    private void OnReady()
    {
        IsReady = true;
        _readyButton.interactable = false;
        _readyButton.GetComponentInChildren<TMP_Text>().text = "READY!";
    }

    private string GetControlsHint(string role, string device)
    {
        if (role.Contains("Cat"))
            return device.Contains("Keyboard")
                ? "이동: WASD  슬래시: J  대쉬: K"
                : "이동: 왼쪽스틱  슬래시: A버튼  대쉬: B버튼";
        else
            return device.Contains("Keyboard")
                ? "조준: 마우스  발사: 좌클릭  방패: 우클릭"
                : "조준: 오른쪽스틱  발사: RT  방패: LT";
    }
}
```

---

### 4. 준비 확인 후 씬 전환

```csharp
public class LobbyManager : MonoBehaviour
{
    // ... (위 코드 이어서)

    void Update()
    {
        if (_joined.Count == 2 && _slots[0].IsReady && _slots[1].IsReady)
            StartGame();
    }

    private void StartGame()
    {
        // 씬 전환 전 PlayerInput 오브젝트가 DontDestroyOnLoad로 넘어가게 설정
        foreach (var pi in _joined)
            DontDestroyOnLoad(pi.gameObject);

        SceneManager.LoadScene("GameplayScene");
    }
}
```

**GameplayScene에서의 복구:**

```csharp
public class GameplaySceneInitializer : MonoBehaviour
{
    void Start()
    {
        // DontDestroyOnLoad로 넘어온 PlayerInput들을 역할별로 연결
        var inputs = FindObjectsByType<PlayerInput>(FindObjectsSortMode.None);
        foreach (var pi in inputs)
        {
            int idx = pi.playerIndex; // 0=Cat, 1=Onion
            if (idx == 0) catController.AssignInput(pi);
            else onionController.AssignInput(pi);
        }
    }
}
```

---

### 5. Input Actions 분리 방식 (두 가지 선택)

#### 방법 A: 단일 에셋 + 다중 ActionMap (추천)
```
OnionCatInputActions.inputactions
├── Cat    (ActionMap)
└── Onion  (ActionMap)

// PlayerInput 하나에 ActionMap을 "Cat"으로, 다른 PlayerInput은 "Onion"으로 지정
```

#### 방법 B: 별도 에셋 2개
```
CatInputActions.inputactions
OnionInputActions.inputactions
```
구분이 명확하지만 관리 파일 수 증가. 소규모 팀에선 방법 A가 낫다.

---

### 6. 엣지 케이스 처리

| 상황 | 처리 |
|---|---|
| 게임패드 2개 모두 연결 | PlayerInputManager가 자동으로 분리 장치에 배정 |
| 키보드+게임패드 혼용 | Control Scheme 감지로 자동 분류 |
| 한 명만 버튼 누른 채 대기 | 타임아웃 없음 — 두 번째 플레이어 올 때까지 대기 |
| 게임패드 연결 해제 됨 | `PlayerInput.onDeviceLost` 이벤트로 UI에 경고 표시 |
| 뒤로 가기 (한 명 이탈) | `PlayerInput.onPlayerLeft` 이벤트로 슬롯 리셋 |

```csharp
// 장치 분리 처리
pi.onDeviceLost += _ => _slots[pi.playerIndex].ShowDeviceLost();
```

---

## OnionCat 적용 포인트

1. **P2 항상 Onion으로 고정**: OnionCat은 역할 선택 없이 P1=Cat, P2=Onion으로 하드코딩해도 무방. 선택지를 줄여 UX 단순화.

2. **1인 플레이 지원 고려**: P2가 없을 때 AI 또는 단일 플레이어 모드 전환 여부를 결정해두기. 없으면 "2인 필수" 문구 명시.

3. **첫 씬 진입 시 패드 진동 = 연결 확인**: `Gamepad.current?.SetMotorSpeeds(0.3f, 0.3f)` 0.1초 → 플레이어가 자신의 패드 인식

4. **조작법 UI는 이미지로**: 버튼 아이콘(Xbox A, PS Cross)을 Sprite로 교체해주면 직관성 향상. Input System에 `InputBinding.GetBindingDisplayString()` API 활용.

5. **씬 전환 시 PlayerInput DontDestroyOnLoad**: 이 처리가 없으면 새 씬에서 입력이 초기화되어 두 컨트롤러가 서로 바뀌는 버그 발생.

---

## 구현 순서 요약

1. `PlayerInputManager` 컴포넌트 설정 (Join Behavior: Button Press)
2. `LobbyManager` 스크립트 작성 — 플레이어 합류 이벤트 처리
3. `LobbySlotUI` — Cat/Onion 패널 UI 구성 (대기 / 합류 / 준비 상태)
4. 조작법 힌트 텍스트 / 이미지 설계
5. Ready 버튼 → 둘 다 Ready → `DontDestroyOnLoad` + `SceneManager.LoadScene`
6. GameplayScene에서 `PlayerInput` 오브젝트를 찾아 각 컨트롤러에 연결

---

## 참고 링크

- [Unity PlayerInputManager 공식 문서](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html)
- [Input System 멀티플레이어 셋업 가이드](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInput.html#setting-up-player-input-for-multiple-players)
- [GetBindingDisplayString API](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/api/UnityEngine.InputSystem.InputBinding.html#UnityEngine_InputSystem_InputBinding_GetBindingDisplayString)
- [Unity 로컬 멀티플레이어 튜토리얼 — Code Monkey](https://www.youtube.com/watch?v=8w2ps7-IOyI)
- [DontDestroyOnLoad 씬 전환 패턴](https://docs.unity3d.com/ScriptReference/Object.DontDestroyOnLoad.html)
