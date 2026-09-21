# 쿱 런 결과 화면 (Coop Run Result Screen)

리서치 날짜: 2026-09-21

## 개요

런 결과 화면은 **플레이어가 게임을 끝내는 순간의 감정적 클로징**이다.
로그라이크에서 특히 중요한 이유: 죽었을 때 "이번 런에서 뭘 했는지" 보여줘야 다음 도전 동기가 생긴다.

OnionCat에서는 **2인 쿱** 구조 때문에 일반 싱글 결과 화면과 다른 점이 많다:
- Cat과 Onion의 기여도를 각각 보여줘야 함
- 두 플레이어가 동시에 버튼을 확인하는 UX 설계 필요
- "누가 더 잘했나" 가 아닌 "함께 얼마나 멀리 갔나" 강조

---

## Unity 구현 방법

### 1. 런 통계 데이터 구조

```csharp
[System.Serializable]
public class RunResult
{
    // 공통
    public int floorsCleared;
    public float runDuration;       // 초 단위
    public int totalEnemiesKilled;
    public bool isVictory;
    public int seedUsed;

    // Cat (Player 1) 통계
    public int catMeleeKills;
    public int catDashCount;
    public int catDamageTaken;
    public string catFavoriteUpgrade;  // 가장 많이 활용한 업그레이드

    // Onion (Player 2) 통계
    public int onionRangedKills;
    public int onionProjectilesFired;
    public int onionParryCount;
    public int onionDamageTaken;
    public string onionFavoriteUpgrade;

    // 업그레이드 목록
    public List<string> upgradesCollected;
}
```

### 2. 런 중 통계 수집

```csharp
// GameManager의 RunData에 통계 수집 로직 추가
public class RunStatsTracker : MonoBehaviour
{
    void OnEnable()  => GameManager.OnStateChanged += HandleStateChange;
    void OnDisable() => GameManager.OnStateChanged -= HandleStateChange;

    // 각 시스템에서 호출
    public static void RecordMeleeKill()
        => GameManager.Instance.Run.result.catMeleeKills++;

    public static void RecordRangedKill()
        => GameManager.Instance.Run.result.onionRangedKills++;

    public static void RecordParry()
        => GameManager.Instance.Run.result.onionParryCount++;

    void HandleStateChange(GameState newState)
    {
        if (newState == GameState.GameOver || newState == GameState.Victory)
        {
            GameManager.Instance.Run.result.runDuration =
                Time.time - GameManager.Instance.Run.startTime;
        }
    }
}
```

### 3. 결과 화면 UI 구조

```
[RunResultScreen]
├── HeaderPanel
│   ├── Title ("RUN OVER" or "VICTORY!")
│   └── FloorReached ("Reached Floor 5")
│
├── StatsPanel
│   ├── CatStatsColumn
│   │   ├── PlayerIcon (고양이 스프라이트)
│   │   ├── MeleeKills: 23
│   │   ├── DashCount: 15
│   │   └── DamageTaken: 84
│   │
│   └── OnionStatsColumn
│       ├── PlayerIcon (양파 스프라이트)
│       ├── RangedKills: 31
│       ├── ParryCount: 7
│       └── DamageTaken: 62
│
├── UpgradesPanel
│   └── ScrollRect (업그레이드 아이콘 목록)
│
├── BestRecordPanel
│   ├── "New Record!" 배지 (갱신 시)
│   └── PreviousBest: Floor 3
│
└── ButtonPanel
    ├── [Retry] 버튼
    └── [Main Menu] 버튼
```

### 4. 결과 화면 컨트롤러

```csharp
public class RunResultScreen : MonoBehaviour
{
    [SerializeField] private TMP_Text titleText;
    [SerializeField] private TMP_Text floorText;
    [SerializeField] private TMP_Text runTimeText;

    [SerializeField] private TMP_Text catKillsText;
    [SerializeField] private TMP_Text catDashText;
    [SerializeField] private TMP_Text onionKillsText;
    [SerializeField] private TMP_Text onionParryText;

    [SerializeField] private GameObject newRecordBadge;

    void Start()
    {
        var result = GameManager.Instance.Run.result;
        Display(result);
    }

    void Display(RunResult r)
    {
        titleText.text    = r.isVictory ? "VICTORY!" : "RUN OVER";
        floorText.text    = $"Reached Floor {r.floorsCleared}";
        runTimeText.text  = FormatTime(r.runDuration);

        catKillsText.text   = $"Melee Kills: {r.catMeleeKills}";
        catDashText.text    = $"Dashes: {r.catDashCount}";
        onionKillsText.text = $"Ranged Kills: {r.onionRangedKills}";
        onionParryText.text = $"Parries: {r.onionParryCount}";

        // 베스트 기록 갱신 확인
        int prev = PlayerPrefs.GetInt("BestFloor", 0);
        if (r.floorsCleared > prev)
        {
            PlayerPrefs.SetInt("BestFloor", r.floorsCleared);
            newRecordBadge.SetActive(true);
        }
    }

    string FormatTime(float seconds)
    {
        int m = (int)(seconds / 60);
        int s = (int)(seconds % 60);
        return $"{m:00}:{s:00}";
    }

    public void OnRetry()
    {
        GameManager.Instance.ChangeState(GameState.StartRun);
    }

    public void OnMainMenu()
    {
        GameManager.Instance.ChangeState(GameState.MainMenu);
    }
}
```

### 5. 통계 표시 애니메이션 (선택 사항)

```csharp
// 숫자가 0에서 최종값으로 올라가는 연출
IEnumerator AnimateCount(TMP_Text label, string prefix, int target, float duration = 1f)
{
    float elapsed = 0f;
    while (elapsed < duration)
    {
        elapsed += Time.deltaTime;
        int current = Mathf.RoundToInt(Mathf.Lerp(0, target, elapsed / duration));
        label.text = $"{prefix}: {current}";
        yield return null;
    }
    label.text = $"{prefix}: {target}";
}
```

---

## OnionCat 적용 포인트

### 쿱 특화 설계 원칙

1. **기여도 대등하게 표시**: Cat 통계 / Onion 통계를 좌우 분할 → "누가 이겼는지"가 아니라 "둘 다 활약했다" 인상
2. **공동 스탯은 가운데**: 클리어 층수, 총 처치 수, 런 시간은 공통 영역에 크게 표시
3. **하이라이트 모멘트 한 줄**: "Onion used Parry 7 times!" 같은 개인 하이라이트 문구 — 재미있는 스탯 강조

### 구현 순서 (초보자용)

```
1. RunData에 RunResult 필드 추가
2. 처치/대쉬/패리 등 주요 이벤트에서 RunStatsTracker.Record~() 호출
3. GameOver/Victory 씬에 RunResultScreen 오브젝트 배치
4. RunResultScreen.Display()에서 GameManager.Instance.Run.result 읽기
5. Retry/MainMenu 버튼 연결
6. PlayerPrefs로 최고 층수 저장/비교
```

### 주의사항

- **씬 전환 시 RunData 유지**: `GameManager`가 `DontDestroyOnLoad`면 씬 전환 후에도 `Run.result` 접근 가능
- **게임 오버 씬 vs 오버레이**: 별도 씬으로 만들면 씬 전환 애니메이션 가능. 오버레이(캔버스)로 만들면 구현 단순 — 초보자는 오버레이 먼저 권장
- **두 플레이어 입력 처리**: Retry 버튼을 어느 플레이어가 눌러도 동작하게 `PlayerInput` 두 개 모두 리스닝

---

## 참고 링크

- [Unity Docs: SceneManager.LoadScene](https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager.LoadScene.html)
- [PlayerPrefs Best Practices](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [Hades 결과 화면 UX 분석](https://www.rockpapershotgun.com/how-hades-handles-player-death)
- [Rogue Legacy 2 Stats Screen](https://roguelegacy.fandom.com/wiki/Statistics)
