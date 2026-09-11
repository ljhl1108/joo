# In-Game Analytics Event Tracker (인게임 분석 이벤트 시스템)

리서치 날짜: 2026-09-11

## 개요

플레이테스트 중 "어디서 많이 죽는지", "어떤 업그레이드를 선택하는지", "방 클리어에 얼마나 걸리는지"를 **실시간으로 로깅**하면 밸런스 조정과 레벨 디자인에 데이터 근거가 생긴다.

외부 분석 서비스 없이 **JSON 파일로 로컬 저장**하는 방식이 초보자에게 가장 현실적이다. OnionCat처럼 2인 협동 게임은 특히 "어느 캐릭터 행동이 어느 상황에서 발생했는지" 추적이 중요하다.

---

## Unity 구현 방법

### 1. 이벤트 데이터 구조 설계

```csharp
[System.Serializable]
public class AnalyticsEvent
{
    public string eventName;
    public string timestamp;
    public int runNumber;
    public int roomNumber;
    public string playerID; // "Cat" 또는 "Onion"
    public Vector2 position;
    public Dictionary<string, string> metadata; // 추가 정보
}

[System.Serializable]
public class SessionData
{
    public string sessionID;
    public string gameVersion;
    public List<AnalyticsEvent> events = new List<AnalyticsEvent>();
}
```

### 2. Analytics Manager (싱글턴)

```csharp
public class AnalyticsManager : MonoBehaviour
{
    public static AnalyticsManager Instance { get; private set; }

    private SessionData _session;
    private int _runNumber;
    private int _roomNumber;

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        InitSession();
    }

    private void InitSession()
    {
        _session = new SessionData
        {
            sessionID = System.Guid.NewGuid().ToString(),
            gameVersion = Application.version
        };
    }

    public void Track(string eventName, string playerID = "",
                      Vector2 position = default,
                      Dictionary<string, string> metadata = null)
    {
        var evt = new AnalyticsEvent
        {
            eventName = eventName,
            timestamp = System.DateTime.Now.ToString("HH:mm:ss.fff"),
            runNumber = _runNumber,
            roomNumber = _roomNumber,
            playerID = playerID,
            position = position,
            metadata = metadata ?? new Dictionary<string, string>()
        };
        _session.events.Add(evt);
    }

    public void SetRunNumber(int run) => _runNumber = run;
    public void SetRoomNumber(int room) => _roomNumber = room;

    // 게임 종료 또는 주기적으로 파일에 저장
    public void SaveToDisk()
    {
        string path = System.IO.Path.Combine(
            Application.persistentDataPath,
            $"analytics_{_session.sessionID}.json");
        string json = JsonUtility.ToJson(_session, prettyPrint: true);
        System.IO.File.WriteAllText(path, json);
        Debug.Log($"[Analytics] 저장됨: {path}");
    }

    private void OnApplicationQuit() => SaveToDisk();
}
```

### 3. OnionCat 전용 추적 이벤트 정의

```csharp
public static class AnalyticsEvents
{
    // 공통
    public const string RUN_START = "run_start";
    public const string RUN_END = "run_end";
    public const string ROOM_CLEAR = "room_clear";
    public const string GAME_OVER = "game_over";

    // Cat (P1) 전용
    public const string CAT_DEATH = "cat_death";
    public const string CAT_DASH = "cat_dash";
    public const string CAT_SLASH_HIT = "cat_slash_hit";
    public const string CAT_SLASH_MISS = "cat_slash_miss";

    // Onion (P2) 전용
    public const string ONION_DEATH = "onion_death";
    public const string ONION_PROJECTILE_HIT = "onion_proj_hit";
    public const string ONION_PARRY_SUCCESS = "onion_parry_success";
    public const string ONION_PARRY_FAIL = "onion_parry_fail";
    public const string ONION_SHIELD_UP = "onion_shield_up";

    // 업그레이드
    public const string UPGRADE_OFFERED = "upgrade_offered";
    public const string UPGRADE_SELECTED = "upgrade_selected";

    // 적
    public const string ENEMY_KILLED_MELEE = "enemy_killed_melee";
    public const string ENEMY_KILLED_RANGED = "enemy_killed_ranged";
}
```

### 4. 사용 예시 (실제 호출 위치)

```csharp
// 게임 오버 시
void OnGameOver(Vector2 deathPosition)
{
    AnalyticsManager.Instance.Track(
        AnalyticsEvents.CAT_DEATH,
        playerID: "Cat",
        position: deathPosition,
        metadata: new Dictionary<string, string>
        {
            { "hp_remaining", currentHp.ToString() },
            { "enemy_type", lastAttackerType },
            { "room_number", RoomManager.Instance.CurrentRoomIndex.ToString() }
        }
    );
}

// 패리 성공 시
void OnParrySuccess(Vector2 parryPos, string blockedProjectileType)
{
    AnalyticsManager.Instance.Track(
        AnalyticsEvents.ONION_PARRY_SUCCESS,
        playerID: "Onion",
        position: parryPos,
        metadata: new Dictionary<string, string>
        {
            { "projectile_type", blockedProjectileType }
        }
    );
}

// 업그레이드 선택 시
void OnUpgradeSelected(string upgradeName, string[] allOfferedOptions)
{
    AnalyticsManager.Instance.Track(
        AnalyticsEvents.UPGRADE_SELECTED,
        metadata: new Dictionary<string, string>
        {
            { "selected", upgradeName },
            { "offered", string.Join("|", allOfferedOptions) }
        }
    );
}
```

### 5. 히트맵 데이터 분석 (Python 스크립트)

로컬 JSON 파일을 분석하는 간단한 Python 스크립트 (선택 사항):

```python
import json, glob, collections

events = []
for f in glob.glob("analytics_*.json"):
    with open(f) as file:
        data = json.load(file)
        events.extend(data["events"])

# 가장 많이 죽는 방 찾기
death_rooms = [e["roomNumber"] for e in events if e["eventName"] == "cat_death"]
print("죽음 분포:", collections.Counter(death_rooms).most_common(5))

# 선택된 업그레이드 통계
upgrades = [e["metadata"]["selected"] for e in events
            if e["eventName"] == "upgrade_selected" and "selected" in e.get("metadata", {})]
print("인기 업그레이드:", collections.Counter(upgrades).most_common(10))

# 패리 성공률
parry_ok = len([e for e in events if e["eventName"] == "onion_parry_success"])
parry_fail = len([e for e in events if e["eventName"] == "onion_parry_fail"])
total = parry_ok + parry_fail
print(f"패리 성공률: {parry_ok}/{total} = {parry_ok/total*100:.1f}%")
```

---

## OnionCat 적용 포인트

### 협동 게임 특화 지표

OnionCat은 2인 협동이므로 **두 플레이어의 행동 비율**이 핵심 지표:

```
Cat 슬래시 명중률 = cat_slash_hit / (cat_slash_hit + cat_slash_miss)
→ 50% 이하면 적의 근접 공격 패턴이 너무 어렵거나 Cat 이동 속도 과부족

Onion 패리 성공률 = onion_parry_success / total_parry_attempts  
→ 70% 이상이면 너무 쉬움, 30% 이하면 너무 어려움 → 패리 윈도우 조정

근접 vs. 원거리 적 처치 비율 = enemy_killed_melee / enemy_killed_ranged
→ 비율이 극단적이면 두 캐릭터 중 하나가 무의미해짐 → 적 설계 재검토
```

### 구현 우선순위 (초보자 권장)

1. **게임 오버 추적만 먼저**: `CAT_DEATH` + `ROOM_CLEAR` 2개로 시작
2. **업그레이드 선택 추적**: 어떤 업그레이드가 인기 있는지 → 밸런스 조정
3. **패리/슬래시 성공률**: 난이도 튜닝에 직결
4. **히트맵 시각화**: 나중에 Python이나 Excel로 분석

### 파일 저장 위치

```
Application.persistentDataPath:
- Windows: C:\Users\[user]\AppData\LocalLow\[company]\[game]\
- Mac: ~/Library/Application Support/[company]/[game]/
- Android: /storage/emulated/0/Android/data/[package]/files/
```

---

## 참고 링크

- Unity Analytics 공식 문서 (외부 서비스 버전): https://docs.unity.com/analytics/
- Unity `Application.persistentDataPath` 문서: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- "How to Add Analytics to Your Game" (Game Dev Unlocked): YouTube 검색
- "Playtesting Your Game With Data" (GDC 강연): GDC Vault 검색
- Python `collections.Counter` 문서: https://docs.python.org/3/library/collections.html#collections.Counter
