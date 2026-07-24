# Character Select Screen

리서치 날짜: 2026-07-24

## 개요

게임 시작 전 플레이어가 캐릭터/시작 로드아웃을 선택하는 화면. OnionCat에서는 2명의 플레이어가 준비 완료를 확인하고 시작 옵션(난이도, 시작 아이템 등)을 선택하는 **Pre-Run Lobby 화면**으로 활용된다. 이 화면 없이는 멀티플레이 시작 플로우가 어색해지고 플레이어 귀속 상태가 불명확해진다.

---

## Unity 구현 방법

### 1. 기본 씬 구조

```
CharacterSelectScene
├── Canvas (Screen Space - Overlay)
│   ├── Player1Panel
│   │   ├── CharacterPreview (Image)
│   │   ├── ReadyIndicator (Text: "준비 완료!")
│   │   └── SelectionCursor
│   ├── Player2Panel
│   │   └── (동일 구조)
│   ├── StartButton (두 플레이어 모두 Ready일 때 활성화)
│   └── BackButton
└── PreviewCamera
```

### 2. 플레이어 준비 상태 관리

```csharp
public class CharacterSelectManager : MonoBehaviour
{
    [SerializeField] private PlayerReadyPanel[] playerPanels; // 크기 2
    [SerializeField] private Button startButton;

    private bool[] _playerReady = new bool[2];

    private void Start()
    {
        startButton.interactable = false;
    }

    // 각 플레이어 패널에서 호출
    public void SetPlayerReady(int playerIndex, bool isReady)
    {
        _playerReady[playerIndex] = isReady;
        playerPanels[playerIndex].SetReadyDisplay(isReady);
        CheckAllReady();
    }

    private void CheckAllReady()
    {
        bool allReady = _playerReady[0] && _playerReady[1];
        startButton.interactable = allReady;

        if (allReady)
        {
            // 자동 카운트다운 시작 (선택적)
            StartCoroutine(AutoStartCountdown());
        }
    }

    private IEnumerator AutoStartCountdown()
    {
        yield return new WaitForSeconds(3f);
        // 3초 후 자동 시작
        if (_playerReady[0] && _playerReady[1])
            StartGame();
    }

    public void StartGame()
    {
        SceneManager.LoadScene("GameScene");
    }
}
```

### 3. 개별 플레이어 패널

```csharp
public class PlayerReadyPanel : MonoBehaviour
{
    [SerializeField] private int playerIndex;
    [SerializeField] private Image characterPreview;
    [SerializeField] private GameObject readyIndicator;
    [SerializeField] private CharacterSelectManager manager;

    private bool _isReady = false;
    private PlayerInput _input; // New Input System

    private void Awake()
    {
        _input = GetComponent<PlayerInput>();
    }

    // 확인 버튼 (South/A) → 준비 완료 토글
    public void OnConfirm(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed) return;
        _isReady = !_isReady;
        manager.SetPlayerReady(playerIndex, _isReady);
    }

    // 취소 버튼 (East/B) → 준비 해제
    public void OnCancel(InputAction.CallbackContext ctx)
    {
        if (!ctx.performed) return;
        _isReady = false;
        manager.SetPlayerReady(playerIndex, false);
    }

    public void SetReadyDisplay(bool isReady)
    {
        readyIndicator.SetActive(isReady);
        // 준비 완료 시 캐릭터 애니메이션 변경 등
    }
}
```

### 4. 선택지 확장 — 시작 옵션 (선택적)

```csharp
// 캐릭터 선택 외에 시작 조건 선택 지원
[System.Serializable]
public class RunStartConfig
{
    public int DifficultyLevel;      // 0=Normal, 1=Hard
    public AbilityBase StartAbility; // 시작 능력 (있다면)
}

// 씬 전환 시 다음 씬에 전달
public static class RunConfigTransfer
{
    public static RunStartConfig PendingConfig;
}
```

### 5. 캐릭터 미리보기 애니메이션

```csharp
// 선택 화면에서 캐릭터 idle 애니메이션 재생
public class CharacterPreviewAnimator : MonoBehaviour
{
    [SerializeField] private Animator animator;

    private void OnEnable()
    {
        animator.Play("Idle");
    }

    // 준비 완료 시 다른 애니메이션
    public void PlayReadyAnim()
    {
        animator.SetTrigger("Ready");
    }
}
```

### 6. New Input System — 2P 입력 분리

```csharp
// PlayerInputManager를 씬에 배치하면
// 컨트롤러 연결 시 자동으로 Player 1/2 패널 활성화
public class SelectScreenInputManager : MonoBehaviour
{
    [SerializeField] private PlayerInputManager playerInputManager;

    private void Awake()
    {
        // 플레이어 조인 허용
        playerInputManager.EnableJoining();
    }

    private void OnPlayerJoined(PlayerInput player)
    {
        int idx = player.playerIndex;
        // 해당 인덱스 패널 활성화
        FindObjectOfType<CharacterSelectManager>()
            .ActivatePanel(idx, player);
    }
}
```

---

## OnionCat 적용 포인트

### 화면 구성 제안

```
┌──────────────────────────────────┐
│        OnionCat — 게임 시작       │
├────────────────┬─────────────────┤
│  Player 1      │   Player 2      │
│  [고양이 스프]  │  [양파 스프]    │
│  키보드/패드1   │  마우스/패드2    │
│  [ 준비 완료 ] │  [ 준비 완료 ]  │
├────────────────┴─────────────────┤
│        [두 명 모두 준비 시 시작]   │
└──────────────────────────────────┘
```

### 구현 우선순위
1. **최소 구현**: Player 1/2 각각 "준비 완료" 버튼 → 둘 다 누르면 게임 시작
2. **추가 구현**: 3초 카운트다운 자동 시작
3. **고급 구현**: 시작 능력 선택, 난이도 선택

### 씬 흐름
```
MainMenu → CharacterSelect → (두 플레이어 Ready) → GameScene
                           ↑
                     BackButton → MainMenu
```

### 주의사항
- **싱글 플레이 대비**: Player 2 없이 시작할 수 있어야 하면 타임아웃 또는 AI 대체 플레이어 필요
- **키보드 + 마우스 분리**: Player 1 = 키보드, Player 2 = 마우스로 고정하거나, `PlayerInputManager` 자동 할당 활용
- **씬 전환 전 입력 잠금**: `playerInputManager.DisableJoining()` 호출 후 씬 이동

---

## 참고 링크

- Unity PlayerInputManager 공식 문서: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html
- New Input System Multiplayer 튜토리얼: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/HowDoI.html#handle-multiplayer-input
- Unity UI Button 클릭 이벤트: https://docs.unity3d.com/Manual/script-Button.html
- SceneManager: https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.html
