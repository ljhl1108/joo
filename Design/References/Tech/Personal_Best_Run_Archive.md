# 개인 기록 아카이브 시스템 (Personal Best Run Archive)

리서치 날짜: 2026-11-02

## 개요

런 종료 시 자동으로 통계를 로컬에 저장하고, 나중에 "내 최고 기록" 화면에서 열람하는 시스템.
온라인 리더보드(UGS)와 달리 완전 로컬 저장 — 인터넷 없이도 동작.

플레이어가 자신의 성장을 돌아보는 수단이 되고,
"이번 런은 역대 최고 협동 콤보다"는 작은 성취감을 제공.

기존 `Lifetime_Stats_Display`(누적 통계)와의 차이:
- 누적 통계 = 전체 합산 (총 처치 수 등)
- **개인 기록 아카이브 = 런 단위 기록** (특정 런이 어땠는지 돌아볼 수 있음)

---

## Unity 구현 방법

### 데이터 구조

```csharp
[Serializable]
public class RunRecord
{
    public string date;             // "2026-11-02 14:32"
    public string cropType;         // "Onion", "Sunflower"
    public int floorsCleared;       // 클리어한 방 수
    public float clearTimeSeconds;
    public int totalKills;
    public int totalDamageDealt;
    public int totalDamageTaken;
    public int coopComboCount;
    public int jointUltimateCount;
    public bool cleared;            // 최종 보스 처치 여부
    public int chapter;             // MetaProgress.Chapter 기준 시작 챕터
    public List<string> gearIds;    // 획득한 장비 ID 목록
}

[Serializable]
public class RunArchive
{
    public List<RunRecord> records = new();
    public const int MAX_RECORDS = 50; // 오래된 것부터 자동 삭제
}
```

### RunArchiveManager

```csharp
public static class RunArchiveManager
{
    static string FilePath => Path.Combine(
        Application.persistentDataPath, "run_archive.json");

    public static void SaveRecord(RunRecord record)
    {
        var archive = Load();
        archive.records.Insert(0, record); // 최신 순 정렬
        if (archive.records.Count > RunArchive.MAX_RECORDS)
            archive.records.RemoveRange(
                RunArchive.MAX_RECORDS,
                archive.records.Count - RunArchive.MAX_RECORDS);
        try { File.WriteAllText(FilePath, JsonUtility.ToJson(archive, true)); }
        catch (Exception e) { Debug.LogWarning($"RunArchive save failed: {e.Message}"); }
    }

    public static RunArchive Load()
    {
        if (!File.Exists(FilePath)) return new RunArchive();
        try { return JsonUtility.FromJson<RunArchive>(File.ReadAllText(FilePath)); }
        catch { return new RunArchive(); }
    }

    // 특정 지표 기준 개인 최고 조회
    public static RunRecord GetPersonalBest(Func<RunRecord, float> metric)
        => Load().records.OrderByDescending(metric).FirstOrDefault();

    // 클리어 런 중 최단 시간
    public static float GetBestClearTime()
        => Load().records
            .Where(r => r.cleared)
            .Select(r => r.clearTimeSeconds)
            .DefaultIfEmpty(float.MaxValue)
            .Min();
}
```

### 런 종료 시 기록 저장

```csharp
// GameManager.cs (런 종료 시점)
void OnRunEnd(bool cleared)
{
    var record = new RunRecord
    {
        date = DateTime.Now.ToString("yyyy-MM-dd HH:mm"),
        cropType = RunData.Crop?.name ?? "None",
        floorsCleared = RunData.FloorsCleared,
        clearTimeSeconds = RunData.ElapsedSeconds,
        totalKills = RunData.TotalKills,
        totalDamageDealt = RunData.TotalDamageDealt,
        totalDamageTaken = RunData.TotalDamageTaken,
        coopComboCount = RunData.CoopComboCount,
        jointUltimateCount = RunData.JointUltimateCount,
        cleared = cleared,
        chapter = MetaProgress.data.chapter,
        gearIds = RunData.GetAllGearIds()
    };
    RunArchiveManager.SaveRecord(record); // 즉시 저장 (강제 종료 대비)
}
```

### 기록 목록 UI (RunArchiveScreen)

```
┌─────────────────────────────────────────────────────┐
│  내 기록                          [클리어만 / 전체]  │
├──────────┬──────┬────────┬────────┬─────────────────┤
│ 날짜     │ 작물 │ 방 수  │ 시간   │ 처치 / 협동     │
├──────────┼──────┼────────┼────────┼─────────────────┤
│ ★ 11/01 │ 양파 │ 18 ★  │ 48:22  │ 63 / 콤보 41    │
│ 10/30   │ 양파 │ 15     │ 52:10  │ 45 / 콤보 28    │
│ 10/28   │해바라│ 12     │ 38:44  │ 38 / 콤보 19    │
└──────────┴──────┴────────┴────────┴─────────────────┘
```

- `★` = 해당 지표 개인 최고
- ScrollRect + RunRecordRow 프리팹으로 구성
- 최대 50행

### 런 결과 화면에서 신기록 알림

```csharp
// RunResultScreen.cs
void ShowPersonalBestMessage(RunRecord newRecord)
{
    var best = RunArchiveManager.GetPersonalBest(r => r.floorsCleared);
    if (best != null && newRecord.floorsCleared > best.floorsCleared)
        ShowBanner("역대 최고 방 수 갱신! 🎉");

    var bestCombo = RunArchiveManager.GetPersonalBest(r => r.coopComboCount);
    if (bestCombo != null && newRecord.coopComboCount > bestCombo.coopComboCount)
        ShowBanner("역대 최고 협동 콤보! 🎉");
}
```

---

## OnionCat 적용 포인트

### MetaProgress와 파일 분리
`MetaProgress` = 이야기 진행·등불 빛·해금 (게임 세계 상태)
`RunArchive` = 플레이 통계 기록 (플레이어 역사)
→ `Application.persistentDataPath/run_archive.json` (별도 파일, meta.json과 독립)

테스트 목적으로 meta.json을 되돌릴 때도 **기록 아카이브는 건드리지 않아도 됨**.

### 협동 통계 강조
OnionCat은 2인 협동 게임이므로 `coopComboCount`, `jointUltimateCount` 통계를 전면에 배치.
"역대 최고 협동 콤보: 42번" 같은 메시지가 협동 플레이 의식을 강화.

### 해금 조건 연결
`RunArchiveManager`의 기록을 `MetaProgress` 해금 조건으로 연결 가능:
- "협동 콤보 50번 달성 런" 기록 존재 → `Greenhouse`에서 특정 장비 해금
- `GearItem.UnlockCost`를 seeds가 아닌 RunStat 기준으로 설정하는 방식으로 확장 가능

### 저장 안전성
런 종료 판정 **즉시** SaveRecord 호출 — 씬 전환 전에 저장해 강제 종료·씬 전환 실패에도 기록 보존.
예외 처리로 저장 실패 시 런타임 오류 없이 경고만 출력 (기록 저장 실패가 게임을 중단시키지 않도록).

---

## 참고 링크

- Unity Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- JsonUtility 직렬화 주의사항: https://docs.unity3d.com/Manual/JSONSerialization.html
- Hades 통계 화면 UX: https://store.steampowered.com/app/1145360/Hades/
- Dead Cells 기록 화면 분석: https://store.steampowered.com/app/588650/Dead_Cells/
