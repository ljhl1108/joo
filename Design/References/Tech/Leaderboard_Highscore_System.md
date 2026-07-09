# Leaderboard & Highscore System (리더보드 & 최고기록 시스템)

리서치 날짜: 2026-07-09

## 개요

로그라이크 게임에서 리더보드/최고기록 시스템은 **재플레이 동기**를 부여하는 핵심 완성 기능이다.  
OnionCat처럼 협동 게임의 경우 "두 플레이어 합산 기록" 또는 "듀오 클리어 타임"이 주요 지표가 된다.

### 구성 요소
1. **로컬 최고기록** — PlayerPrefs/JSON으로 기기 내 저장
2. **온라인 리더보드** — Steam Leaderboard (Steamworks.NET)
3. **UI 표시** — 런 결과 화면 + 별도 리더보드 화면

---

## Unity 구현 방법

### 1. 로컬 최고기록 — JSON 파일 방식 (권장)

```csharp
// RunRecord.cs
[System.Serializable]
public class RunRecord
{
    public int rank;
    public int score;
    public float clearTimeSeconds;
    public int enemiesKilled;
    public int floorReached;
    public string date;         // "2026-07-09"
    public string[] upgrades;   // 획득한 업그레이드 목록
}

[System.Serializable]
public class HighscoreData
{
    public List<RunRecord> records = new List<RunRecord>();
    public const int MAX_RECORDS = 10;
}
```

```csharp
// HighscoreManager.cs
public class HighscoreManager : MonoBehaviour
{
    public static HighscoreManager Instance { get; private set; }
    
    private HighscoreData data;
    private string savePath;
    
    void Awake()
    {
        Instance = this;
        savePath = Application.persistentDataPath + "/highscores.json";
        LoadScores();
    }
    
    public void SubmitRun(RunRecord record)
    {
        data.records.Add(record);
        // 점수 내림차순 정렬
        data.records.Sort((a, b) => b.score.CompareTo(a.score));
        // 상위 10개만 유지
        if (data.records.Count > HighscoreData.MAX_RECORDS)
            data.records.RemoveAt(data.records.Count - 1);
        
        // 순위 번호 갱신
        for (int i = 0; i < data.records.Count; i++)
            data.records[i].rank = i + 1;
        
        SaveScores();
    }
    
    public bool IsNewHighscore(int score)
    {
        if (data.records.Count < HighscoreData.MAX_RECORDS) return true;
        return score > data.records[data.records.Count - 1].score;
    }
    
    public List<RunRecord> GetTopRecords() => data.records;
    
    private void SaveScores()
    {
        string json = JsonUtility.ToJson(data, true);
        System.IO.File.WriteAllText(savePath, json);
    }
    
    private void LoadScores()
    {
        if (System.IO.File.Exists(savePath))
        {
            string json = System.IO.File.ReadAllText(savePath);
            data = JsonUtility.FromJson<HighscoreData>(json);
        }
        else
        {
            data = new HighscoreData();
        }
    }
}
```

### 2. 점수 계산 시스템

```csharp
// ScoreCalculator.cs
public static class ScoreCalculator
{
    public static int CalculateRunScore(RunStats stats)
    {
        int baseScore = stats.enemiesKilled * 100;
        
        // 클리어 시 보너스
        if (stats.cleared)
            baseScore += 10000;
        
        // 시간 보너스 (20분 이내 클리어 시)
        float targetTime = 1200f; // 20분
        if (stats.clearTime < targetTime && stats.cleared)
        {
            float timeBonus = (targetTime - stats.clearTime) / targetTime;
            baseScore += Mathf.RoundToInt(5000 * timeBonus);
        }
        
        // 층수 보너스
        baseScore += stats.floorReached * 500;
        
        // 협동 보너스 (2인 플레이 시)
        if (stats.isCoopRun)
            baseScore = Mathf.RoundToInt(baseScore * 1.2f);
        
        return baseScore;
    }
}
```

### 3. UI 구현 — 리더보드 화면

```csharp
// LeaderboardUI.cs
public class LeaderboardUI : MonoBehaviour
{
    [SerializeField] private Transform recordContainer;
    [SerializeField] private GameObject recordRowPrefab;
    
    void OnEnable()
    {
        RefreshDisplay();
    }
    
    void RefreshDisplay()
    {
        // 기존 항목 제거
        foreach (Transform child in recordContainer)
            Destroy(child.gameObject);
        
        var records = HighscoreManager.Instance.GetTopRecords();
        foreach (var record in records)
        {
            var row = Instantiate(recordRowPrefab, recordContainer);
            row.GetComponent<LeaderboardRow>().Setup(record);
        }
    }
}
```

```csharp
// LeaderboardRow.cs
public class LeaderboardRow : MonoBehaviour
{
    [SerializeField] private TMP_Text rankText;
    [SerializeField] private TMP_Text scoreText;
    [SerializeField] private TMP_Text timeText;
    [SerializeField] private TMP_Text dateText;
    
    public void Setup(RunRecord record)
    {
        rankText.text = $"#{record.rank}";
        scoreText.text = record.score.ToString("N0");
        timeText.text = FormatTime(record.clearTimeSeconds);
        dateText.text = record.date;
    }
    
    private string FormatTime(float seconds)
    {
        int m = (int)(seconds / 60);
        int s = (int)(seconds % 60);
        return $"{m:00}:{s:00}";
    }
}
```

### 4. Steam 리더보드 연동 (Steamworks.NET)

```csharp
// SteamLeaderboardManager.cs
// 주의: Steamworks.NET 패키지 설치 필요
// Package Manager → Add from URL: https://github.com/rlabrecque/Steamworks.NET.git

#if UNITY_STANDALONE && !DISABLESTEAMWORKS
using Steamworks;

public class SteamLeaderboardManager : MonoBehaviour
{
    private const string LEADERBOARD_NAME = "GlobalScore";
    private SteamLeaderboard_t currentLeaderboard;
    
    public void FindOrCreateLeaderboard()
    {
        SteamAPICall_t call = SteamUserStats.FindOrCreateLeaderboard(
            LEADERBOARD_NAME,
            ELeaderboardSortMethod.k_ELeaderboardSortMethodDescending,
            ELeaderboardDisplayType.k_ELeaderboardDisplayTypeNumeric);
        
        CallResult<LeaderboardFindResult_t>.Create(OnLeaderboardFound).Set(call);
    }
    
    private void OnLeaderboardFound(LeaderboardFindResult_t result, bool failure)
    {
        if (!failure && result.m_bLeaderboardFound == 1)
            currentLeaderboard = result.m_hSteamLeaderboard;
    }
    
    public void UploadScore(int score)
    {
        SteamUserStats.UploadLeaderboardScore(
            currentLeaderboard,
            ELeaderboardUploadScoreMethod.k_ELeaderboardUploadScoreMethodKeepBest,
            score,
            null, 0);
    }
}
#endif
```

### 5. 런 결과 화면에서 자동 제출

```csharp
// RunEndManager.cs
public class RunEndManager : MonoBehaviour
{
    void OnRunComplete(RunStats stats)
    {
        int score = ScoreCalculator.CalculateRunScore(stats);
        
        RunRecord record = new RunRecord
        {
            score = score,
            clearTimeSeconds = stats.clearTime,
            enemiesKilled = stats.enemiesKilled,
            floorReached = stats.floorReached,
            date = System.DateTime.Now.ToString("yyyy-MM-dd"),
            upgrades = stats.collectedUpgrades.ToArray()
        };
        
        bool isNewRecord = HighscoreManager.Instance.IsNewHighscore(score);
        HighscoreManager.Instance.SubmitRun(record);
        
        // UI에 신기록 여부 표시
        runResultUI.ShowResult(record, isNewRecord);
        
        // Steam 업로드 (있으면)
#if UNITY_STANDALONE && !DISABLESTEAMWORKS
        steamLeaderboard?.UploadScore(score);
#endif
    }
}
```

---

## OnionCat 적용 포인트

### 점수 지표 설계 (협동 게임 특화)
| 지표 | 비중 | 비고 |
|-----|------|------|
| 적 처치 수 | 40% | Cat/Crop 공동 카운트 |
| 클리어 여부 | 25% | 보스 처치 = 런 클리어 |
| 클리어 시간 | 20% | 빠를수록 보너스 |
| 도달 층 수 | 15% | 미클리어 시 주요 지표 |

### 협동 전용 기능
- **Co-op 태그**: 로컬 2인 플레이 기록에 "Co-op" 마크 표시
- **역할 통계**: Cat 처치 수 / Crop 처치 수 각각 기록 (누가 더 기여했나?)
- **베스트 파트너**: 같은 기기에서 최고 기록과 함께한 플레이어 이름 저장

### 구현 순서 (초보자용)
1. `RunRecord`, `HighscoreData` 데이터 클래스 작성
2. `HighscoreManager` 싱글톤 + JSON 저장/불러오기 구현
3. `ScoreCalculator` 점수 공식 확정
4. 런 결과 화면에 점수 + 순위 표시 UI 연결
5. (선택) Steam 리더보드 — 출시 직전에 추가

### 주의사항
- PlayerPrefs보다 **JSON 파일** 방식 권장 (복잡한 데이터 구조에 적합)
- `Application.persistentDataPath` 사용 — 유니티가 플랫폼별 올바른 경로 제공
- Steam 리더보드는 AppID 등록 이후에만 작동 (개발 중에는 로컬만)

---

## 참고 링크

- Unity 공식 — persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Steamworks.NET GitHub: https://github.com/rlabrecque/Steamworks.NET
- Steam Leaderboard API 문서: https://partner.steamgames.com/doc/features/leaderboards
- 유튜브 — Unity Leaderboard System: https://www.youtube.com/watch?v=7776T3M2T7A
- 관련 파일: [Run_Result_Screen.md](Run_Result_Screen.md), [Save_Load_System.md](Save_Load_System.md)
