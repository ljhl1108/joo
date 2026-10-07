# 협동 런 재시작 투표 화면 (Coop Run Restart Vote Screen)

리서치 날짜: 2026-10-07

## 개요

2인 협동 로그라이크에서 한 플레이어가 런을 포기하고 싶을 때, **상대방의 동의 없이 강제 종료되면 안 된다**. 양쪽이 모두 동의해야 재시작/종료하는 "투표(Vote)" 화면은 완성된 코-옵 게임의 필수 UX 기능이다.

실제 출시 코-옵 게임(Deep Rock Galactic, Hades II 멀티플레이) 모두 이 패턴을 사용한다.

---

## Unity 구현 방법

### 1. 데이터 구조

```csharp
// RestartVoteData.cs
public enum VoteResult { Pending, Confirmed, Cancelled }
public enum VoteAction { Restart, ReturnToMenu, Quit }
```

### 2. 투표 시스템 코어

```csharp
// CoopRestartVoteManager.cs
public class CoopRestartVoteManager : MonoBehaviour
{
    public static CoopRestartVoteManager Instance { get; private set; }

    [SerializeField] private CoopRestartVoteUI voteUI;
    [SerializeField] private float voteTimeoutSeconds = 15f;

    private bool[] playerVotes = new bool[2];
    private bool[] playerCancels = new bool[2];
    private VoteAction pendingAction;
    private Coroutine timeoutCoroutine;
    private bool isVoteActive;

    public event Action<VoteResult, VoteAction> OnVoteResolved;

    void Awake() => Instance = this;

    // ESC 입력 시 호출 (PauseMenu에서 연결)
    public void InitiateVote(VoteAction action)
    {
        if (isVoteActive) return;

        isVoteActive = true;
        pendingAction = action;
        playerVotes = new bool[2];
        playerCancels = new bool[2];

        voteUI.Show(action, voteTimeoutSeconds);
        GameManager.Instance.ChangeState(GameState.VotePause); // 게임 일시정지

        timeoutCoroutine = StartCoroutine(VoteTimeout());
    }

    // 플레이어가 "예" 버튼 누를 때
    public void PlayerConfirm(int playerIndex)
    {
        if (!isVoteActive) return;
        playerVotes[playerIndex] = true;
        voteUI.SetPlayerVote(playerIndex, confirmed: true);

        if (playerVotes[0] && playerVotes[1])
            ResolveVote(VoteResult.Confirmed);
    }

    // 플레이어가 "아니오" 버튼 누를 때
    public void PlayerCancel(int playerIndex)
    {
        if (!isVoteActive) return;
        CancelVote();
    }

    IEnumerator VoteTimeout()
    {
        float remaining = voteTimeoutSeconds;
        while (remaining > 0f)
        {
            remaining -= Time.unscaledDeltaTime;
            voteUI.UpdateTimer(remaining / voteTimeoutSeconds);
            yield return null;
        }
        CancelVote(); // 타임아웃 = 취소
    }

    void ResolveVote(VoteResult result)
    {
        isVoteActive = false;
        if (timeoutCoroutine != null) StopCoroutine(timeoutCoroutine);

        voteUI.Hide();
        OnVoteResolved?.Invoke(result, pendingAction);

        if (result == VoteResult.Confirmed)
            ExecuteAction(pendingAction);
        else
            GameManager.Instance.ChangeState(GameState.Gameplay); // 게임 재개
    }

    void CancelVote() => ResolveVote(VoteResult.Cancelled);

    void ExecuteAction(VoteAction action)
    {
        switch (action)
        {
            case VoteAction.Restart:
                GameManager.Instance.ChangeState(GameState.RunStart);
                break;
            case VoteAction.ReturnToMenu:
                SceneManager.LoadScene(SceneNames.MainMenu);
                break;
        }
    }
}
```

### 3. 투표 UI

```csharp
// CoopRestartVoteUI.cs
public class CoopRestartVoteUI : MonoBehaviour
{
    [SerializeField] private TMP_Text actionLabel;
    [SerializeField] private Image timerFill;
    [SerializeField] private GameObject[] playerVoteIndicators; // 체크/X 아이콘 2개
    [SerializeField] private TMP_Text hintText;

    public void Show(VoteAction action, float timeout)
    {
        gameObject.SetActive(true);
        actionLabel.text = GetActionLabel(action);
        // 플레이어별 힌트 표시 (Cat = A버튼/Z키, Onion = 마우스 클릭)
        hintText.text = "Cat: [A] / Onion: [Left Click] to confirm";
        SetPlayerVote(0, false);
        SetPlayerVote(1, false);
    }

    public void SetPlayerVote(int playerIndex, bool confirmed)
    {
        // 체크 = 동의, X = 미결정
        playerVoteIndicators[playerIndex].GetComponent<Image>().sprite = 
            confirmed ? checkSprite : questionSprite;
    }

    public void UpdateTimer(float ratio) => timerFill.fillAmount = ratio;
    public void Hide() => gameObject.SetActive(false);

    string GetActionLabel(VoteAction action) => action switch
    {
        VoteAction.Restart => "Restart Run?",
        VoteAction.ReturnToMenu => "Return to Menu?",
        _ => "Confirm?"
    };
}
```

### 4. 일시정지 메뉴에서 연결

```csharp
// PauseMenu.cs (기존 코드에 추가)
public void OnRestartButtonClicked()
{
    // 기존: GameManager.Instance.ChangeState(GameState.RunStart);
    // 변경: 투표 시작
    CoopRestartVoteManager.Instance.InitiateVote(VoteAction.Restart);
}
```

### 5. 입력 라우팅 (Cat vs Onion)

```csharp
// PlayerInputRouter.cs — 투표 입력 처리
void OnInteractPerformed(InputAction.CallbackContext ctx)
{
    if (GameManager.Instance.State == GameState.VotePause)
        CoopRestartVoteManager.Instance.PlayerConfirm(playerIndex);
}

void OnCancelPerformed(InputAction.CallbackContext ctx)
{
    if (GameManager.Instance.State == GameState.VotePause)
        CoopRestartVoteManager.Instance.PlayerCancel(playerIndex);
}
```

---

## OnionCat 적용 포인트

### 언제 투표를 트리거할까

| 상황 | 투표 필요 여부 |
|------|--------------|
| 일시정지 메뉴 → 재시작 | ✅ 필수 |
| 일시정지 메뉴 → 메인 메뉴 이동 | ✅ 필수 |
| 게임 오버 화면 → 재시작 | ✅ 권장 (두 플레이어가 준비됐을 때) |
| 게임 오버 화면 → 메인 메뉴 | ✅ 권장 |
| 한 플레이어가 조이스틱 뽑음 | ✅ 자동 투표 트리거 |

### UI 배치 아이디어

```
┌─────────────────────────────────┐
│        Restart Run?             │
│                                 │
│  [Cat Icon]        [Onion Icon] │
│     ❓                  ❓      │
│    Press A             Click    │
│    to Confirm         to Confirm│
│                                 │
│  [━━━━━━━━━━━━━━━] 12s          │
│         타임아웃 시 취소         │
└─────────────────────────────────┘
```

### OnionCat 특수 고려사항

- **Onion 입력**: Onion은 마우스 조작 → 투표 확인은 Left Click (또는 별도 키)
- **Cat 입력**: Cat은 게임패드 or WASD → A버튼 또는 Z키로 확인
- 두 플레이어의 입력 방식이 완전히 다르므로 힌트 텍스트를 **각 플레이어별로** 표시
- `GameState.VotePause` 상태 추가 필요 (`GameManager` GameState enum 확장)

### 구현 우선순위

1. 게임 오버 시 "재시작" 버튼에 투표 적용 (가장 많이 쓰는 케이스)
2. 일시정지 메뉴 재시작에 투표 적용
3. 타임아웃 15초 → 취소 (너무 오래 기다리지 않도록)
4. 타임아웃 UI (진행 바) 추가

---

## 참고 링크

- Deep Rock Galactic 재시작 투표 UX 분석: YouTube 검색 "Deep Rock Galactic quit vote"
- Unity EventSystem + UnityEngine.InputSystem 조합: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/index.html
- 비슷한 구현: r/gamedev "coop quit vote implementation unity"
