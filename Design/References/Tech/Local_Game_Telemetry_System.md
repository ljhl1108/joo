# 로컬 게임 텔레메트리 시스템 (Local Game Telemetry for Balance)

리서치 날짜: 2026-10-18

## 개요

외부 분석 서비스(Unity Analytics, GameAnalytics 등) 없이 **게임 이벤트를 로컬 파일에 기록**해 밸런스 조정에 활용하는 시스템.
1인 개발자가 플레이테스트 중 "실제로 어떤 일이 일어났는가"를 객관적으로 파악하기 위한 도구.

OnionCat에서 특히 중요한 이유:
- 밸런스 수치(데미지, 쿨다운, 방 클리어 시간)가 많고 장비 163종이 상호작용
- 직감만으로 밸런스 파악 어려움 → 데이터가 반드시 필요
- 외부 서버 없이도 로컬 JSON/CSV로 충분

## Unity 구현 방법

### 1. TelemetryEvent 구조 설계

```csharp
[System.Serializable]
public class TelemetryEvent
{
    public string eventType;    // "enemy_killed", "room_cleared", "player_died", etc.
    public float timestamp;     // Time.time
    public int roomIndex;       // 몇 번째 방인지
    public string stageId;      // 스테이지 이름
    public Dictionary<string, object> data; // 이벤트별 추가 데이터
}
```

### 2. TelemetryManager (싱글턴, DontDestroyOnLoad)

```csharp
public class TelemetryManager : MonoBehaviour
{
    private static TelemetryManager _instance;
    public static TelemetryManager Instance => _instance;

    private List<TelemetryEvent> _events = new();
    private string _runId;

    void Awake()
    {
        if (_instance != null) { Destroy(gameObject); return; }
        _instance = this;
        DontDestroyOnLoad(gameObject);
        _runId = System.DateTime.Now.ToString("yyyyMMdd_HHmmss");
    }

    // 이벤트 기록
    public void Log(string eventType, Dictionary<string, object> data = null)
    {
        _events.Add(new TelemetryEvent
        {
            eventType = eventType,
            timestamp = Time.time,
            roomIndex = GameManager.Instance?.Run?.roomIndex ?? -1,
            stageId = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name,
            data = data ?? new Dictionary<string, object>()
        });
    }

    // 런 종료 시 파일로 저장
    public void SaveToFile()
    {
        string dir = System.IO.Path.Combine(Application.persistentDataPath, "Telemetry");
        System.IO.Directory.CreateDirectory(dir);
        string path = System.IO.Path.Combine(dir, $"run_{_runId}.json");
        string json = JsonUtility.ToJson(new TelemetryData { events = _events }, prettyPrint: true);
        System.IO.File.WriteAllText(path, json);
        Debug.Log($"[Telemetry] 저장됨: {path}");
    }
}
```

### 3. 기록할 핵심 이벤트

| 이벤트 | 기록 위치 | 주요 데이터 |
|--------|----------|------------|
| `run_start` | 런 시작 시 | 난이도, 시작 장비 |
| `room_enter` | 방 입장 시 | 방 타입, 적 목록 |
| `room_cleared` | 모든 적 처치 시 | 소요 시간, 피해 받은 횟수, 남은 HP |
| `enemy_killed` | 적 사망 시 | 적 종류, 처치자(Cat/Onion), 딜 출처 |
| `damage_taken` | 플레이어 피격 시 | 공격 종류, 데미지량, HP 잔여 |
| `gear_acquired` | 장비 획득/선택 시 | 장비 ID, 등급, 칸, 무엇과 교체 |
| `skill_used` | 스킬(Q/W/E/R) 사용 시 | 스킬 ID, 적 수, 명중 여부 |
| `coop_combo` | 협동 콤보 발생 시 | 콤보 횟수, 데미지 |
| `player_died` | 사망 시 | 원인 적, 마지막 방, 남은 HP |
| `run_end` | 런 종료 시 | 클리어 여부, 총 시간, 처치 수, 획득 장비 목록 |

### 4. 호출 예시 — 기존 코드에 한 줄씩 추가

```csharp
// EnemyBase.cs의 Die() 메서드
TelemetryManager.Instance?.Log("enemy_killed", new Dictionary<string, object>
{
    {"enemyId", enemyData.id},
    {"killedBy", lastAttacker.ToString()},  // Attacker.Cat or Onion
    {"roomIndex", GameManager.Instance.Run.roomIndex}
});

// 방 클리어 처리
TelemetryManager.Instance?.Log("room_cleared", new Dictionary<string, object>
{
    {"clearTime", Time.time - roomEnterTime},
    {"remainingHp", GameManager.Instance.Run.currentHp},
    {"damageCount", roomDamageCount}
});
```

### 5. 저장 경로 및 분석

- **저장 위치**: `Application.persistentDataPath/Telemetry/run_YYYYMMDD_HHmmss.json`
  - Windows: `%APPDATA%\..\LocalLow\<CompanyName>\<GameName>\Telemetry\`
- **분석 방법**:
  - Python 스크립트로 여러 런 JSON 합산 → 평균 방 클리어 시간, 최다 사망 원인, 장비 픽률 등
  - Excel/Google Sheets에서 JSON 파싱
  - 간단한 뷰어 HTML (`python Design/Data/build_viewer.py` 유사 방식)

### 6. CSV 요약 파일 (인간이 읽기 쉬운 버전)

```csharp
public void SaveCsvSummary()
{
    var sb = new System.Text.StringBuilder();
    sb.AppendLine("timestamp,eventType,roomIndex,key1,value1,key2,value2");
    foreach (var e in _events)
    {
        var d = e.data;
        sb.AppendLine($"{e.timestamp:F2},{e.eventType},{e.roomIndex},...");
    }
    System.IO.File.WriteAllText(csvPath, sb.ToString());
}
```

### 7. 빌드에서 비활성화 (릴리즈 버전)

```csharp
// TelemetryManager.Log()
public void Log(string eventType, Dictionary<string, object> data = null)
{
#if UNITY_EDITOR || DEVELOPMENT_BUILD
    _events.Add(...);
#endif
}
```

`Development Build` 체크 시에만 수집. 릴리즈 빌드에서는 완전히 제거.

## OnionCat 적용 포인트

### 즉시 사용 가능한 밸런스 질문들

1. **방 클리어 평균 시간은?** → 너무 쉬우면 <30초, 너무 어려우면 >3분
2. **가장 많이 죽이는 적은?** → 데미지 조정 필요
3. **어떤 장비를 가장 많이 선택하는가?** → 강한 장비가 명확히 편향되는지 확인
4. **협동 콤보 발생 빈도** → 콤보가 너무 드물면 시스템이 안 보임
5. **어떤 방에서 가장 많이 피격?** → 해당 방 적 배치 문제

### 구현 순서 권장

1. `TelemetryManager` 싱글턴 추가 (5분)
2. `room_cleared`, `player_died`, `run_end`만 먼저 기록 (20분)
3. 플레이테스트 5런 후 JSON 열어보기
4. 분석 결과로 수치 조정 → 다시 플레이테스트 → 반복
5. 나중에 `enemy_killed`, `gear_acquired` 등 추가

## 참고 링크

- Unity Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Unity JsonUtility: https://docs.unity3d.com/ScriptReference/JsonUtility.html
- 게임 밸런싱용 로컬 분석 패턴: https://www.gamedeveloper.com/design/data-driven-game-balance-for-indie-devs
- Python JSON 분석 예시: https://docs.python.org/3/library/json.html
