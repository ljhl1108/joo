# 플레이테스트 세션 로그 시스템

리서치 날짜: 2026-09-01

## 개요

게임 밸런스 조정을 위해 플레이 중 중요 이벤트(사망 위치, 선택 업그레이드,
처치 수, 클리어 시간 등)를 로컬 JSON 파일로 기록하는 경량 개발 전용 시스템.

첫 게임을 만드는 인디 개발자에게 가장 실질적인 문제는
"어디서 너무 어렵고 어디서 너무 쉬운가"를 데이터로 확인하는 것.
플레이테스터가 게임을 하면 자동으로 로그가 쌓이고,
개발자는 JSON 파일을 열어 사망 위치·업그레이드 픽률·런 시간을 분석할 수 있다.

---

## Unity 구현 방법

### 1. 로그 데이터 구조

```csharp
// PlaytestSessionLog.cs
[System.Serializable]
public class RunLogEntry
{
    public string sessionId;
    public string timestamp;
    public int floorReached;
    public float runDurationSeconds;
    public int totalKills;
    public int meleeKills;
    public int rangedKills;
    public bool cleared;
    public System.Collections.Generic.List<string> upgradesTaken = new();
    public System.Collections.Generic.List<DeathRecord> deaths = new();
}

[System.Serializable]
public class DeathRecord
{
    public float posX;
    public float posY;
    public string killedByTag;  // 적 태그 또는 이름
    public int floor;
    public float timeIntoRun;
}
```

---

### 2. 싱글톤 로거

```csharp
// PlaytestLogger.cs
using UnityEngine;
using System.IO;

public class PlaytestLogger : MonoBehaviour
{
    public static PlaytestLogger Instance { get; private set; }

    [SerializeField] private bool enableLogging = true;

    private RunLogEntry currentRun;
    private float runStartTime;

    void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void StartRun()
    {
        if (!enableLogging) return;

        currentRun = new RunLogEntry
        {
            sessionId = System.Guid.NewGuid().ToString("N").Substring(0, 8),
            timestamp = System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
        };
        runStartTime = Time.realtimeSinceStartup;
    }

    public void LogDeath(Vector2 position, string killedByTag, int floor)
    {
        if (!enableLogging || currentRun == null) return;
        currentRun.deaths.Add(new DeathRecord
        {
            posX = position.x,
            posY = position.y,
            killedByTag = killedByTag,
            floor = floor,
            timeIntoRun = Time.realtimeSinceStartup - runStartTime,
        });
    }

    public void LogUpgrade(string upgradeName)
    {
        if (!enableLogging || currentRun == null) return;
        currentRun.upgradesTaken.Add(upgradeName);
    }

    public void LogKill(bool isMelee)
    {
        if (!enableLogging || currentRun == null) return;
        currentRun.totalKills++;
        if (isMelee) currentRun.meleeKills++;
        else currentRun.rangedKills++;
    }

    public void EndRun(int floorReached, bool cleared)
    {
        if (!enableLogging || currentRun == null) return;
        currentRun.floorReached = floorReached;
        currentRun.cleared = cleared;
        currentRun.runDurationSeconds = Time.realtimeSinceStartup - runStartTime;
        Save();
        currentRun = null;
    }

    private void Save()
    {
        string dir = Path.Combine(Application.persistentDataPath, "PlaytestLogs");
        Directory.CreateDirectory(dir);

        string dateStr = System.DateTime.Now.ToString("yyyyMMdd_HHmmss");
        string path = Path.Combine(dir, $"run_{currentRun.sessionId}_{dateStr}.json");
        File.WriteAllText(path, JsonUtility.ToJson(currentRun, prettyPrint: true));

        Debug.Log($"[PlaytestLog] 저장 완료: {path}");
    }
}
```

---

### 3. 이벤트 연결 방법

각 관련 스크립트에서 로거를 호출한다.

```csharp
// PlayerHealth.cs 사망 처리
void Die(string killedByTag)
{
    PlaytestLogger.Instance?.LogDeath(transform.position, killedByTag, GameManager.CurrentFloor);
    // 사망 처리 나머지 로직...
}

// UpgradeManager.cs 업그레이드 선택
void OnUpgradeSelected(UpgradeData data)
{
    PlaytestLogger.Instance?.LogUpgrade(data.upgradeName);
}

// Enemy.cs 처치 완료
void OnKilled(DamageType lastHitType)
{
    PlaytestLogger.Instance?.LogKill(lastHitType == DamageType.Melee);
}

// GameManager.cs 런 종료
void OnRunEnded(bool cleared)
{
    PlaytestLogger.Instance?.EndRun(CurrentFloor, cleared);
}
```

---

### 4. 로그 파일 위치

`Application.persistentDataPath`가 플랫폼별 경로를 자동 반환:

| 플랫폼 | 경로 |
|--------|------|
| Windows | `%AppData%\LocalLow\[회사명]\[게임명]\PlaytestLogs\` |
| macOS | `~/Library/Application Support/[회사명]/[게임명]/PlaytestLogs/` |
| Linux | `~/.config/unity3d/[회사명]/[게임명]/PlaytestLogs/` |

---

### 5. 로그 분석 방법

**방법 A — JSON 직접 확인**: VS Code에서 파일 열기 → 사망 위치·선택 업그레이드 육안 확인

**방법 B — 스프레드시트**: JSON을 Google Sheets에 붙여넣기 후 필터로 정렬

**방법 C — 간단한 Python 스크립트** (개발자용):
```python
import json, glob, collections

files = glob.glob("PlaytestLogs/*.json")
logs = [json.load(open(f, encoding="utf-8")) for f in files]

# 가장 많이 죽인 적
killer_counts = collections.Counter(
    d["killedByTag"] for log in logs for d in log["deaths"]
)
print("사망 원인 TOP 5:", killer_counts.most_common(5))

# 업그레이드 픽률
upgrade_counts = collections.Counter(
    u for log in logs for u in log["upgradesTaken"]
)
print("업그레이드 인기 TOP 5:", upgrade_counts.most_common(5))

# 평균 런 시간
avg_time = sum(log["runDurationSeconds"] for log in logs) / len(logs)
print(f"평균 런 시간: {avg_time:.1f}초")
```

---

## OnionCat 적용 포인트

- **meleeKills / rangedKills 분리 기록**: P1(근접) vs P2(원거리) 기여도 비율 확인
  → 한 플레이어가 일방적으로 기여하면 취약점 분배·밸런스 조정
- **사망 위치 분석**: `posX, posY`로 히트맵 작성 → 특정 방에서 집중 사망 시 해당 방 적 조정
- **업그레이드 픽률**: 인기 없는 업그레이드 발견 → 수치 보정 또는 제거
- **개발 초기 설치 권장**: 나중에 추가하면 각 이벤트 지점에 수동 삽입이 번거로움.
  게임 시작 시 `PlaytestLogger.StartRun()` 한 줄만 호출하고,
  나머지 `LogXxx()` 호출은 해당 스크립트 작성 시 바로 추가하면 공수 최소화.
- **빌드 배포 시 비활성화**: `enableLogging = false`로 토글 또는
  `#if UNITY_EDITOR` / `Debug.isDebugBuild` 조건으로 릴리즈 빌드에서 자동 제외

---

## 참고 링크

- Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- JsonUtility: https://docs.unity3d.com/ScriptReference/JsonUtility.ToJson.html
- 상용 분석 툴 참고: https://gameanalytics.com (무료 플랜 제공)
- 연관 파일: `Save_Load_System.md`, `Run_Result_Screen.md`, `Achievement_Stats_System.md`
