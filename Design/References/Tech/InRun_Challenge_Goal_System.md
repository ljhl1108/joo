# 인게임 챌린지 목표 시스템 (In-Run Challenge Goal System)

리서치 날짜: 2026-08-29

## 개요

"이번 방에서 연속 5킬", "피격 없이 클리어", "방패 패리 3회 성공" 같은 조건부 목표를 런 중에 제시하고, 달성 시 보너스 보상(골드, 특수 아이템, 업그레이드 선택권)을 주는 시스템. 플레이어에게 뚜렷한 단기 목표를 주어 플레이 집중도를 높이고 협동 전략 동기를 부여한다.

**OnionCat 관련도**: ★★★★☆  
두 플레이어가 각각 근접/원거리를 담당하는 구조에서 "Player 1 근접 처치 5회 + Player 2 패리 2회 성공 동시 달성" 같은 협동 챌린지는 게임 핵심 필러를 강화한다.

유사 사례:
- **Hades**: 방 클리어 보상의 암묵적 목표 (Darkness, Keys 등)
- **Dead Cells**: 특정 무기/조합 사용 조건 보상
- **Enter the Gungeon**: 콤보 킬 보너스

---

## Unity 구현 방법

### 1. 챌린지 ScriptableObject 정의

```csharp
[CreateAssetMenu(menuName = "OnionCat/ChallengeGoal")]
public class ChallengeGoalData : ScriptableObject
{
    public string goalName;
    [TextArea] public string description;
    public ChallengeConditionType conditionType;
    public int targetValue;
    public RewardType rewardType;
    public int rewardAmount;
}

public enum ChallengeConditionType
{
    KillCount,           // 처치 수
    NoDamageRoomClear,   // 피격 없이 방 클리어
    ParryCount,          // 패리 성공 횟수
    MeleeKillOnly,       // 근접만으로 처치
    RangedKillOnly,      // 원거리만으로 처치
    CoopComboKill,       // 두 플레이어 동시 공격 처치
    DashCount,           // 대시 횟수
    TimeLimitClear,      // 제한 시간 내 클리어
}
```

---

### 2. 챌린지 매니저

```csharp
public class ChallengeGoalManager : MonoBehaviour
{
    public static ChallengeGoalManager Instance { get; private set; }

    [SerializeField] private List<ChallengeGoalData> allChallenges;
    [SerializeField] private ChallengeGoalUI challengeUI;

    private ChallengeGoalData currentChallenge;
    private int currentProgress;
    private bool isActive;

    public event System.Action<ChallengeGoalData> OnChallengeCompleted;

    void Awake()
    {
        Instance = this;
        SubscribeToGameEvents();
    }

    public void StartNewChallenge()
    {
        currentChallenge = allChallenges[Random.Range(0, allChallenges.Count)];
        currentProgress = 0;
        isActive = true;
        challengeUI.Show(currentChallenge);
    }

    private void SubscribeToGameEvents()
    {
        EventBus.Subscribe<EnemyKilledEvent>(OnEnemyKilled);
        EventBus.Subscribe<PlayerDamagedEvent>(OnPlayerDamaged);
        EventBus.Subscribe<ParrySuccessEvent>(OnParrySuccess);
        EventBus.Subscribe<PlayerDashedEvent>(OnPlayerDashed);
        EventBus.Subscribe<RoomClearedEvent>(OnRoomCleared);
    }

    private void OnEnemyKilled(EnemyKilledEvent e)
    {
        if (!isActive) return;
        if (currentChallenge.conditionType == ChallengeConditionType.KillCount ||
            (currentChallenge.conditionType == ChallengeConditionType.MeleeKillOnly && e.isMeleeKill) ||
            (currentChallenge.conditionType == ChallengeConditionType.RangedKillOnly && !e.isMeleeKill))
        {
            AddProgress(1);
        }
    }

    private void OnPlayerDamaged(PlayerDamagedEvent e)
    {
        if (!isActive) return;
        if (currentChallenge.conditionType == ChallengeConditionType.NoDamageRoomClear)
            FailChallenge();
    }

    private void OnParrySuccess(ParrySuccessEvent e)
    {
        if (!isActive) return;
        if (currentChallenge.conditionType == ChallengeConditionType.ParryCount)
            AddProgress(1);
    }

    private void OnPlayerDashed(PlayerDashedEvent e)
    {
        if (!isActive) return;
        if (currentChallenge.conditionType == ChallengeConditionType.DashCount)
            AddProgress(1);
    }

    private void OnRoomCleared(RoomClearedEvent e)
    {
        if (!isActive) return;
        if (currentChallenge.conditionType == ChallengeConditionType.NoDamageRoomClear)
            CompleteChallenge();
    }

    private void AddProgress(int amount)
    {
        currentProgress += amount;
        challengeUI.UpdateProgress(currentProgress, currentChallenge.targetValue);
        if (currentProgress >= currentChallenge.targetValue) CompleteChallenge();
    }

    private void CompleteChallenge()
    {
        isActive = false;
        challengeUI.ShowCompleted();
        OnChallengeCompleted?.Invoke(currentChallenge);
        RewardManager.Instance.GiveReward(currentChallenge.rewardType, currentChallenge.rewardAmount);
    }

    private void FailChallenge()
    {
        isActive = false;
        challengeUI.ShowFailed();
    }
}
```

---

### 3. 챌린지 UI (HUD에 소형 패널)

```csharp
public class ChallengeGoalUI : MonoBehaviour
{
    [SerializeField] private GameObject panel;
    [SerializeField] private TMP_Text goalNameText;
    [SerializeField] private TMP_Text progressText;
    [SerializeField] private Slider progressBar;
    [SerializeField] private GameObject completedBadge;
    [SerializeField] private GameObject failedBadge;

    public void Show(ChallengeGoalData data)
    {
        panel.SetActive(true);
        goalNameText.text = data.goalName;
        progressBar.maxValue = data.targetValue;
        progressBar.value = 0;
        completedBadge.SetActive(false);
        failedBadge.SetActive(false);
    }

    public void UpdateProgress(int current, int target)
    {
        progressText.text = $"{current} / {target}";
        progressBar.value = current;
    }

    public void ShowCompleted()
    {
        completedBadge.SetActive(true);
        // DOTween 팝업 애니메이션
        completedBadge.transform.DOPunchScale(Vector3.one * 0.2f, 0.3f);
    }

    public void ShowFailed()
    {
        failedBadge.SetActive(true);
        panel.GetComponent<CanvasGroup>()
            .DOFade(0, 1.5f).SetDelay(1f)
            .OnComplete(() => panel.SetActive(false));
    }
}
```

---

### 4. 방 입장 시 챌린지 시작

```csharp
// RoomController.cs
void OnRoomEntered()
{
    ChallengeGoalManager.Instance.StartNewChallenge();
    // 타이머 챌린지면 InGame_Timer_System.md 참고하여 타이머 시작
}
```

---

## OnionCat 적용 포인트

### 협동 챌린지 (OnionCat 핵심 필러 강화)
```
"이번 방에서 Player 1 근접 처치 3회 + Player 2 패리 2회 성공"
→ ChallengeConditionType.CoopCombo 커스텀 구현
→ 두 조건을 AND로 연결: 둘 다 달성해야 Complete
```

```csharp
public enum ChallengeConditionType
{
    // 기존 + 협동 전용 추가
    CoopMeleeAndParry,    // Player1 근접 N킬 AND Player2 패리 M회
    CoopRoleSwitch,       // 이번 방에서 두 캐릭터가 모두 공격 참여
}
```

### OnionCat용 추천 챌린지 목록
| 챌린지명 | 조건 | 보상 |
|---------|------|------|
| 무피격 클리어 | 이번 방 피격 0 | 골드 +30 |
| 원거리 특화 | Player 2만으로 5킬 | 원거리 업그레이드 선택권 |
| 근접 특화 | Player 1만으로 5킬 | 근접 업그레이드 선택권 |
| 패리 마스터 | 패리 3회 성공 | 특수 아이템 |
| 속공 클리어 | 30초 이내 방 클리어 | 골드 +20 |
| 협동 연계 | 근접 처치 3 + 패리 2 동시 | 희귀 업그레이드 선택권 |

### 구현 우선순위
1. `ChallengeGoalData` ScriptableObject 5~10개 먼저 제작
2. `ChallengeGoalManager` 싱글턴 + EventBus 연결
3. HUD에 소형 패널 (우상단 권장)
4. 방 입장 시 랜덤 챌린지 1개 선택 → 방 클리어/실패 시 종료
5. DOTween 완료 애니메이션으로 피드백 강화

---

## 참고 링크

- Unity UI TMP: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
- Unity ScriptableObject: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- DOTween 공식: http://dotween.demigiant.com/documentation.php
- Hades 디자인 분석 참고: GDC 2019 Supergiant Games 강연
