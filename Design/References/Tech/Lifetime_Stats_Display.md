# Lifetime Stats Display (생애 통계 표시 화면)

리서치 날짜: 2026-10-04

## 개요

게임 전체 기간에 걸친 누적 통계(총 런 횟수, 총 처치 수, 최장 생존 시간, 최고 층 클리어 등)를 보여주는 화면.
로그라이크의 "다시 시작해도 발전이 보인다"는 심리적 보상을 강화하고, 장기 플레이 동기를 제공한다.

### 왜 중요한가
- **Hades**, **Dead Cells**, **Binding of Isaac** 모두 생애 통계 화면을 통해 플레이어의 성장감 제공
- 별도의 메타 진행 없이도 "지난주보다 더 잘한다"는 느낌을 수치로 증명
- 비교적 구현이 단순하면서 플레이어 체감 완성도에 크게 기여

---

## Unity 구현 방법

### Step 1: 통계 데이터 구조 설계

```csharp
[System.Serializable]
public class LifetimeStats
{
    // 런 기록
    public int TotalRuns;
    public int TotalWins;
    public int BestFloor;           // 도달한 최고 층
    public float BestRunTime;       // 가장 빨리 클리어한 시간 (초)
    public float TotalPlayTime;     // 누적 플레이 시간 (초)

    // 전투 기록
    public int TotalEnemiesKilled;
    public int TotalDamageTaken;
    public int TotalDamageDealt;
    public int TotalSynergyActivations; // 협동 시너지 발동 횟수

    // 업그레이드 기록
    public int TotalUpgradesPicked;
    public Dictionary<string, int> UpgradePickCounts; // 업그레이드별 선택 횟수

    // 사망 통계
    public string MostFrequentKiller; // 가장 많이 죽인 적
    public int DeathsByEnemy;
    public int DeathsByPit;

    public LifetimeStats()
    {
        UpgradePickCounts = new Dictionary<string, int>();
    }
}
```

### Step 2: 통계 저장 (JSON + PlayerPrefs 혼합)

```csharp
public static class LifetimeStatsManager
{
    private const string SaveKey = "LifetimeStats";

    public static LifetimeStats Load()
    {
        string json = PlayerPrefs.GetString(SaveKey, "");
        if (string.IsNullOrEmpty(json))
            return new LifetimeStats();
        return JsonUtility.FromJson<LifetimeStats>(json);
    }

    public static void Save(LifetimeStats stats)
    {
        PlayerPrefs.SetString(SaveKey, JsonUtility.ToJson(stats));
        PlayerPrefs.Save();
    }

    // 런 종료 시 호출 (GameManager 또는 RunData에서)
    public static void CommitRun(RunData run, bool cleared)
    {
        LifetimeStats stats = Load();
        stats.TotalRuns++;
        if (cleared) stats.TotalWins++;
        stats.BestFloor = Mathf.Max(stats.BestFloor, run.CurrentFloor);
        if (cleared && (stats.BestRunTime <= 0 || run.ElapsedTime < stats.BestRunTime))
            stats.BestRunTime = run.ElapsedTime;
        stats.TotalPlayTime += run.ElapsedTime;
        stats.TotalEnemiesKilled += run.EnemiesKilled;
        stats.TotalSynergyActivations += run.SynergyCount;
        // ... 기타 필드
        Save(stats);
    }
}
```

### Step 3: UI 화면 구성

```
┌────────────────────────────────┐
│  LIFETIME RECORDS              │
├────────────────┬───────────────┤
│ Total Runs     │ 42            │
│ Total Wins     │ 7 (16.7%)     │
│ Best Floor     │ Floor 5       │
│ Best Run Time  │ 8:32          │
│ Total Playtime │ 4h 22m        │
├────────────────┼───────────────┤
│ Enemies Slain  │ 1,204         │
│ Synergies      │ 388           │
│ Damage Dealt   │ 24,891        │
├────────────────┼───────────────┤
│ Killed By      │ Blue Slime x23│
└────────────────┴───────────────┘
```

```csharp
public class LifetimeStatsUI : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI _totalRunsText;
    [SerializeField] private TextMeshProUGUI _winRateText;
    [SerializeField] private TextMeshProUGUI _bestFloorText;
    [SerializeField] private TextMeshProUGUI _totalPlaytimeText;
    [SerializeField] private TextMeshProUGUI _enemiesKilledText;
    [SerializeField] private TextMeshProUGUI _synergiesText;

    private void OnEnable()
    {
        LifetimeStats s = LifetimeStatsManager.Load();
        _totalRunsText.text = s.TotalRuns.ToString();
        float winRate = s.TotalRuns > 0 ? (float)s.TotalWins / s.TotalRuns * 100f : 0f;
        _winRateText.text = $"{s.TotalWins} ({winRate:F1}%)";
        _bestFloorText.text = s.BestFloor > 0 ? $"Floor {s.BestFloor}" : "--";
        _totalPlaytimeText.text = FormatTime(s.TotalPlayTime);
        _enemiesKilledText.text = s.TotalEnemiesKilled.ToString("N0");
        _synergiesText.text = s.TotalSynergyActivations.ToString("N0");
    }

    private string FormatTime(float seconds)
    {
        int h = (int)(seconds / 3600);
        int m = (int)(seconds % 3600 / 60);
        return h > 0 ? $"{h}h {m}m" : $"{m}m";
    }
}
```

### Step 4: 통계 화면 진입 경로

권장: **메인 메뉴** → "Records" 버튼 또는 **런 종료 화면** 하단 "Lifetime Stats" 링크.

```csharp
// MainMenu에서
public void OnRecordsButton()
{
    SceneManager.LoadScene(SceneNames.LifetimeStats);
    // 또는 캔버스 그룹 show/hide (씬 전환 없이 오버레이)
}
```

---

## 통계 수집 지점 (OnionCat 아키텍처 기준)

| 이벤트 | 수집 위치 | 업데이트 필드 |
|--------|-----------|---------------|
| 런 시작 | `GameManager.ChangeState(GameState.InRun)` | TotalRuns++ |
| 적 사망 | `EnemyBase.Die()` | TotalEnemiesKilled++, MostFrequentKiller 갱신 |
| 시너지 발동 | `EnemyBase.TriggerSynergyEffect()` | TotalSynergyActivations++ |
| 피격 | `PlayerHealth.TakeDamage()` | TotalDamageTaken += |
| 층 클리어 | `DungeonManager.OnFloorCleared` | BestFloor 갱신 |
| 런 종료 | `GameManager.ChangeState(GameState.GameOver/Victory)` | CommitRun() 호출 |

---

## OnionCat 적용 포인트

### 협동 시너지 통계 강조
`TotalSynergyActivations`를 일반 통계와 같은 수준으로 표시.
"두 플레이어가 함께한 시너지 횟수" = 협동의 증거 → 게임 정체성과 일치.

### 통계 초기화 주의
- 런 데이터(`RunData`)는 런마다 초기화 → `GameManager.Instance.Run`
- 생애 통계(`LifetimeStats`)는 절대 런 종료 시 초기화하지 말 것.
  `CommitRun()`은 누적이지 덮어쓰기가 아님.

### 세이브 파일 손상 방어
PlayerPrefs JSON이 깨질 경우를 대비해 `try/catch` + 기본값 반환:
```csharp
try { return JsonUtility.FromJson<LifetimeStats>(json); }
catch { return new LifetimeStats(); }
```

### 나중에 추가할 수 있는 통계
- 캐릭터별 선호 업그레이드 Top 3
- 가장 오래 생존한 런의 타임스탬프
- 총 합동기 발동 횟수
- 시너지 연속 발동 최고 기록

---

## 구현 우선순위

| 우선순위 | 항목 | 이유 |
|----------|------|------|
| ★★★ | 총 런·승리·최고 층 | 가장 기본적인 진행 지표 |
| ★★★ | 총 플레이 시간 | "내가 얼마나 투자했나" 실감 |
| ★★☆ | 시너지 발동 횟수 | OnionCat 정체성 강조 |
| ★★☆ | 총 처치 수 | 전투 성과 |
| ★☆☆ | MostFrequentKiller | 재미 요소, 후순위 |

---

## 참고 링크

- Unity PlayerPrefs 공식: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- Unity JsonUtility: https://docs.unity3d.com/ScriptReference/JsonUtility.html
- Hades 통계 화면 분석: https://www.gamedeveloper.com/design/the-stat-tracking-design-of-hades
- Dead Cells Statistics Screen 구현 사례: https://store.steampowered.com/app/588650/Dead_Cells/
