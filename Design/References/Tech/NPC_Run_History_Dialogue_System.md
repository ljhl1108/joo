# NPC Run History Dialogue System (런 히스토리 반응 NPC 대화 시스템)

리서치 날짜: 2026-10-09

## 개요

Hades처럼 NPC가 **이전 런에서 일어난 일을 기억**하고 반응하는 대화 시스템.
"또 죽었군요" "이번엔 마지막 보스까지 갔군요!" 같은 대사가 플레이어의 런 히스토리에 기반해 동적으로 선택된다.

### OnionCat에서 중요한 이유
- 로그라이크의 반복 플레이에서 **서사적 투자감**을 만드는 핵심 도구
- Hades의 성공 비결 중 하나가 반복 사망을 부정적 사건이 아닌 **스토리 진행**으로 전환한 것
- 개발 난이도 대비 플레이어 몰입도 향상 효과가 큼 (텍스트 작업이지만 시스템은 단순)

---

## 핵심 아키텍처

### 1. RunHistory 저장소

런이 끝날 때마다 결과를 기록하는 **영속 데이터 컨테이너**.

```csharp
[Serializable]
public class RunEvent
{
    public string eventId;      // "boss_defeated", "player_died", "reached_floor_3"
    public string detail;       // "by_slime", "Cat", "Onion" 등 부가 정보
    public int runNumber;
    public float timestamp;
}

[CreateAssetMenu]
public class RunHistoryData : ScriptableObject
{
    public int totalRuns;
    public int totalWins;
    public List<RunEvent> events = new();

    public void AddEvent(string id, string detail = "")
    {
        events.Add(new RunEvent
        {
            eventId = id,
            detail = detail,
            runNumber = totalRuns,
            timestamp = Time.time
        });
    }

    public bool HasEvent(string id) =>
        events.Exists(e => e.eventId == id);

    public int CountEvent(string id) =>
        events.Count(e => e.eventId == id);

    public RunEvent LastEvent(string id) =>
        events.LastOrDefault(e => e.eventId == id);
}
```

런 종료 시 `GameManager`에서 호출:
```csharp
// 사망 시
RunHistory.AddEvent("player_died", killer == "slime" ? "by_slime" : "by_boss");

// 보스 격파 시
RunHistory.AddEvent("boss_defeated", bossId);

// 런 완료 시
RunHistory.totalRuns++;
```

### 2. DialogueLine ScriptableObject

각 대사를 데이터로 관리. 조건을 충족할 때만 표시.

```csharp
[CreateAssetMenu]
public class DialogueLine : ScriptableObject
{
    public string npcId;            // "blacksmith", "witch"
    public string lineId;           // 고유 ID (일회성 체크에 사용)
    public bool oneTimeOnly;        // true: 한 번 보면 다시 안 나옴

    [TextArea] public string text;

    // 조건 목록 (AND 조건)
    public List<DialogueCondition> conditions = new();
    public int priority = 0;        // 높을수록 우선 선택
}

[Serializable]
public class DialogueCondition
{
    public enum ConditionType
    {
        RunCountMin,        // 총 런 횟수 >= value
        HasEvent,           // 특정 이벤트 발생 여부
        EventCountMin,      // 특정 이벤트 횟수 >= value
        WinCountMin,        // 승리 횟수 >= value
        NeverHappened,      // 특정 이벤트가 한 번도 없을 때
    }

    public ConditionType type;
    public string eventId;
    public int value;

    public bool Evaluate(RunHistoryData history) => type switch
    {
        ConditionType.RunCountMin    => history.totalRuns >= value,
        ConditionType.HasEvent       => history.HasEvent(eventId),
        ConditionType.EventCountMin  => history.CountEvent(eventId) >= value,
        ConditionType.WinCountMin    => history.totalWins >= value,
        ConditionType.NeverHappened  => !history.HasEvent(eventId),
        _ => false
    };
}
```

### 3. DialogueSelector — 조건 체크 후 최적 대사 선택

```csharp
public class DialogueSelector : MonoBehaviour
{
    [SerializeField] private RunHistoryData history;
    [SerializeField] private List<DialogueLine> allLines;

    private HashSet<string> shownOneTimeLines = new();  // 저장 필요

    public DialogueLine SelectLine(string npcId)
    {
        var eligible = allLines
            .Where(l => l.npcId == npcId)
            .Where(l => !l.oneTimeOnly || !shownOneTimeLines.Contains(l.lineId))
            .Where(l => l.conditions.All(c => c.Evaluate(history)))
            .OrderByDescending(l => l.priority)
            .ToList();

        if (eligible.Count == 0) return null;

        // 우선순위 동점이면 무작위
        int topPriority = eligible[0].priority;
        var topCandidates = eligible.Where(l => l.priority == topPriority).ToList();
        var selected = topCandidates[Random.Range(0, topCandidates.Count)];

        if (selected.oneTimeOnly)
            shownOneTimeLines.Add(selected.lineId);

        return selected;
    }
}
```

### 4. 저장/로드

`shownOneTimeLines`는 런 간 유지되어야 하므로 `PlayerPrefs` 또는 JSON으로 저장.

```csharp
// 저장
string json = JsonUtility.ToJson(new SerializableHashSet(shownOneTimeLines));
PlayerPrefs.SetString("ShownDialogues", json);

// 로드
if (PlayerPrefs.HasKey("ShownDialogues"))
{
    var data = JsonUtility.FromJson<SerializableHashSet>(PlayerPrefs.GetString("ShownDialogues"));
    shownOneTimeLines = new HashSet<string>(data.items);
}
```

---

## 대사 설계 패턴 (Hades 방식)

### 계층 구조
1. **일회성 특수 대사** (priority 10+): "처음 보스 격파 후 첫 귀환" 등 희귀 이벤트
2. **런 히스토리 반응 대사** (priority 5~9): 특정 이벤트 n회 후 발동
3. **일반 상황 반응 대사** (priority 1~4): 런 횟수, 승패 여부 등 일반 조건
4. **기본 대사** (priority 0): 조건 없음, 항상 후보군

### 예시 대사 표

| NPC | 조건 | 대사 | 우선순위 |
|-----|------|------|--------|
| 대장장이 | 슬라임에게 3번 이상 사망 | "그 초록 녀석들 조심해요. 이미 세 번이나 당했잖아요." | 8 |
| 대장장이 | 첫 보스 격파 | "해냈군요! 처음이었는데 대단한데요." | 10 |
| 마녀 | 총 런 횟수 >= 10 | "10번이나 왔군요... 이 길에 익숙해졌나요?" | 5 |
| 마녀 | 승리 횟수 >= 1, 이벤트 없음 | "또 올 줄 알았어요." | 3 |
| 마녀 | 기본 | "어서 오세요." | 0 |

---

## OnionCat 적용 포인트

### 구현 순서 (최소 버전 → 확장)

**Step 1 (최소)**: `RunHistoryData` ScriptableObject 생성, 런 종료/사망 시 이벤트 기록
**Step 2**: 마을 귀환 씬(있다면)에서 NPC 1명에게 `DialogueSelector` 연결, 대사 5~10개 작성
**Step 3**: 일회성 대사 저장/로드 추가
**Step 4**: NPC 수, 대사 수 확장

### RunData와 연동
현재 `GameManager.Instance.Run`(RunData)가 씬 내 런 상태를 추적한다.
런 종료 시 RunData → RunHistoryData로 **요약 이벤트 추출**하는 변환 로직 필요:

```csharp
public static void ExtractEvents(RunData run, RunHistoryData history)
{
    if (run.CatDeathCount > 0) history.AddEvent("cat_died", $"{run.CatDeathCount}times");
    if (run.BossDefeated)      history.AddEvent("boss_defeated", run.BossId);
    if (run.FloorReached >= 3) history.AddEvent("reached_floor_3");
    history.totalRuns++;
    if (run.IsCleared) history.totalWins++;
}
```

### 고양이·양파 별도 히스토리
- 두 플레이어가 각자의 죽음/성과를 가질 수 있음
- `detail` 필드에 `"Cat"` / `"Onion"` 태그 → NPC가 특정 플레이어에게 다른 대사 가능

### 최소 저장 비용
- `RunHistoryData.events`가 너무 많아지면 **런 단위로 요약본만 보관** (최근 20런)
- 모든 이벤트 원본은 버리고 집계(총 사망수, 보스 격파 여부 등)만 유지해도 충분

---

## 참고 링크

- [Echo Dynamic Dialogue System — Devlog (itch.io)](https://rottencone83.itch.io/echo-dynamic-dialogue-faction-system/devlog/985419/how-to-create-dialogue-that-actually-reacts-to-your-players)
- [Dialog Graph System (GitHub)](https://github.com/arjanbekaa/DialogGraphSystem)
- [Unity Forum: Dialogue storage for RPG interactions](https://forum.unity.com/threads/how-where-to-store-dialogues-for-rpg-like-interactions.1243486/)
- Hades (Supergiant Games) — GDC 2020: "The Narrative Design of Hades" 강연 참고
- `Design/References/Tech/Save_Load_System.md` — RunHistoryData 영속화 방법
- `Design/References/Tech/Game_State_Manager.md` — 런 종료 이벤트 훅 지점
