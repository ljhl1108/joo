# 런 히스토리 뷰어 & 통계 UI (Run History Viewer)

리서치 날짜: 2026-08-09

## 개요

**런 히스토리 뷰어**란 플레이어가 이전 런들의 결과를 돌아볼 수 있는 화면이다.
Hades의 "통계" 화면, Dead Cells의 "기록" 화면처럼, 클리어/사망 통계, 최고 기록, 처치 수 등을 보여준다.

OnionCat에서 왜 필요한가:
- 플레이어가 자신의 성장을 체감할 수 있음 ("10번 시도 만에 2층 도달!")
- 리플레이 동기 제공 — 자신의 최고 기록 경신 욕구
- 협력 게임에서 두 플레이어 각자 기여도 확인 가능
- 게임 완성도의 핵심 지표 중 하나

---

## Unity 구현 방법

### 1. 런 데이터 구조 설계

```csharp
[System.Serializable]
public class RunRecord
{
    public string runId;          // GUID
    public string dateTime;       // "2026-08-09 14:32"
    public bool isVictory;        // 클리어 여부
    public int floorsReached;     // 도달한 층수
    public int totalKills;        // 총 처치 수
    public int catKills;          // Cat이 처치한 수
    public int cropKills;         // Crop이 처치한 수
    public float runDuration;     // 런 소요 시간 (초)
    public string deathCause;     // "사망 원인: 보스 3의 돌진"
    public List<string> upgrades; // 획득한 업그레이드 목록
    public int goldEarned;        // 획득한 골드
    public int damageTaken;       // 받은 총 피해량
}

[System.Serializable]
public class RunHistory
{
    public List<RunRecord> records = new List<RunRecord>();
    public int totalRuns;
    public int totalVictories;
    public int bestFloor;
    public float bestClearTime;   // 클리어 최단 시간
}
```

### 2. 저장 / 불러오기 (JSON)

```csharp
public static class RunHistoryManager
{
    private static readonly string SavePath = 
        Application.persistentDataPath + "/run_history.json";

    public static void SaveRun(RunRecord record)
    {
        RunHistory history = LoadHistory();
        history.records.Add(record);
        history.totalRuns++;
        if (record.isVictory) history.totalVictories++;
        if (record.floorsReached > history.bestFloor)
            history.bestFloor = record.floorsReached;
        if (record.isVictory && (history.bestClearTime == 0 || 
            record.runDuration < history.bestClearTime))
            history.bestClearTime = record.runDuration;

        string json = JsonUtility.ToJson(history, true);
        System.IO.File.WriteAllText(SavePath, json);
    }

    public static RunHistory LoadHistory()
    {
        if (!System.IO.File.Exists(SavePath))
            return new RunHistory();
        string json = System.IO.File.ReadAllText(SavePath);
        return JsonUtility.FromJson<RunHistory>(json);
    }
}
```

### 3. 런 종료 시 기록 저장

```csharp
// GameOverManager.cs 또는 RunEndManager.cs에서 호출
public void OnRunEnd(bool isVictory)
{
    var record = new RunRecord
    {
        runId = System.Guid.NewGuid().ToString(),
        dateTime = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm"),
        isVictory = isVictory,
        floorsReached = GameManager.Instance.currentFloor,
        totalKills = KillTracker.Instance.TotalKills,
        catKills = KillTracker.Instance.CatKills,
        cropKills = KillTracker.Instance.CropKills,
        runDuration = Time.realtimeSinceStartup - _runStartTime,
        deathCause = isVictory ? "" : DeathTracker.Instance.LastDeathCause,
        upgrades = UpgradeManager.Instance.GetAcquiredUpgradeNames()
    };
    RunHistoryManager.SaveRun(record);
}
```

### 4. UI 구성 — 히스토리 목록

```csharp
// RunHistoryUI.cs
public class RunHistoryUI : MonoBehaviour
{
    [SerializeField] private GameObject runEntryPrefab;
    [SerializeField] private Transform contentParent;        // ScrollRect Content
    [SerializeField] private TextMeshProUGUI totalRunsText;
    [SerializeField] private TextMeshProUGUI totalVictoriesText;
    [SerializeField] private TextMeshProUGUI bestFloorText;

    void OnEnable()
    {
        RefreshUI();
    }

    void RefreshUI()
    {
        // 기존 항목 제거
        foreach (Transform child in contentParent)
            Destroy(child.gameObject);

        RunHistory history = RunHistoryManager.LoadHistory();
        
        // 최신 런부터 표시 (역순)
        for (int i = history.records.Count - 1; i >= 0; i--)
        {
            var entry = Instantiate(runEntryPrefab, contentParent);
            entry.GetComponent<RunEntryUI>().SetData(history.records[i], i + 1);
        }

        // 요약 통계
        totalRunsText.text = $"총 시도: {history.totalRuns}회";
        totalVictoriesText.text = $"클리어: {history.totalVictories}회";
        bestFloorText.text = $"최고 층수: {history.bestFloor}층";
    }
}
```

### 5. 개별 런 엔트리 프리팹 (RunEntryUI.cs)

```csharp
public class RunEntryUI : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI runNumberText;
    [SerializeField] private TextMeshProUGUI resultText;
    [SerializeField] private TextMeshProUGUI floorText;
    [SerializeField] private TextMeshProUGUI killsText;
    [SerializeField] private TextMeshProUGUI timeText;
    [SerializeField] private Image backgroundImage;
    [SerializeField] private Color victoryColor;
    [SerializeField] private Color defeatColor;

    public void SetData(RunRecord record, int runNumber)
    {
        runNumberText.text = $"#{runNumber}";
        resultText.text = record.isVictory ? "클리어!" : $"사망: {record.deathCause}";
        floorText.text = $"{record.floorsReached}층";
        killsText.text = $"처치 {record.totalKills} (Cat:{record.catKills} / Crop:{record.cropKills})";
        
        // 시간 포맷: "3분 42초"
        int minutes = (int)(record.runDuration / 60);
        int seconds = (int)(record.runDuration % 60);
        timeText.text = $"{minutes}분 {seconds:00}초";
        
        backgroundImage.color = record.isVictory ? victoryColor : defeatColor;
    }
}
```

### 6. Unity UI 구조 (Hierarchy)

```
Canvas
└── RunHistoryPanel
    ├── Header
    │   ├── TitleText ("런 기록")
    │   └── CloseButton
    ├── SummaryPanel
    │   ├── TotalRunsText
    │   ├── TotalVictoriesText
    │   └── BestFloorText
    ├── ScrollRect
    │   └── Viewport
    │       └── Content (Vertical Layout Group)
    │           └── [RunEntryPrefab × N]
    └── BackButton
```

**Vertical Layout Group 설정**:
- Control Child Size Width: ✓
- Child Force Expand Width: ✓
- Spacing: 8px
- Content Size Fitter: Vertical Fit = Preferred Size

---

## OnionCat 적용 포인트

### 1. 빠른 구현 순서 (초보자 권장)

1. `RunRecord`, `RunHistory` 클래스 작성
2. `RunHistoryManager.SaveRun()` 구현, 게임 오버 화면에서 호출
3. 메인 메뉴에 "런 기록" 버튼 추가 (Main_Menu_Scene.md 참조)
4. `RunHistoryUI.cs`와 `RunEntryUI.cs` 작성
5. ScrollRect + ContentSizeFitter로 목록 UI 구성
6. 테스트: 5회 런 후 기록이 잘 저장되는지 확인

### 2. Cat vs Crop 기여도 분리 표시
두 플레이어의 처치 수를 별도 집계:
```
[런 #5 — 2층 사망 — 2분 18초]
처치: 총 23마리 (Cat: 15 / Crop: 8)
사망 원인: 1번 보스 돌진 공격
```
→ 두 플레이어가 게임 후 자신의 기여도를 확인할 수 있어 재미 요소

### 3. 데이터 보호 — 최대 저장 수 제한
```csharp
// 최대 50개 기록 유지 (오래된 것 삭제)
const int MaxRecords = 50;
if (history.records.Count > MaxRecords)
    history.records.RemoveAt(0);
```

### 4. 접근 경로
메인 메뉴 → "런 기록" 버튼 → RunHistoryPanel 활성화
- 씬 전환 없이 패널 Show/Hide로 구현해 빠른 확인 가능
- ESC 키로 닫기

### 5. 향후 확장
- 층별 클리어 시간 그래프 (LineRenderer 또는 간단한 이미지)
- "가장 많이 선택한 업그레이드 TOP 3"
- 사망 원인 통계 (어떤 적에 가장 많이 죽었는지)

---

## 참고 링크

- Unity Docs — Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Unity Docs — JsonUtility: https://docs.unity3d.com/ScriptReference/JsonUtility.html
- Unity Docs — ScrollRect: https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-ScrollRect.html
- Unity Docs — Content Size Fitter: https://docs.unity3d.com/Packages/com.unity.ugui@1.0/manual/script-ContentSizeFitter.html
- 튜토리얼 (유튜브 검색): "Unity scrollable list UI tutorial", "Unity JSON save system"
