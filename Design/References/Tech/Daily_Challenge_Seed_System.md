# Daily Challenge & Seed 공유 시스템

리서치 날짜: 2026-07-05

## 개요

**Seed(시드)** 기반 런 시스템은 난수 생성기(Random Number Generator)의 초깃값을 고정하여 같은 씨드로 게임하면 항상 동일한 맵·아이템·적 배치를 경험하도록 하는 시스템이다.

**Daily Challenge(데일리 챌린지)** 는 당일 날짜를 씨드로 자동 설정하여 전 세계 플레이어가 동일한 조건으로 경쟁하는 모드다.

OnionCat에서 이 시스템이 필요한 이유:
- 재플레이 가치 증가 — 매일 새로운 '고정 퍼즐'
- 커뮤니티 형성 — "오늘 데일리 클리어했어?"
- 버그 재현 용이 — 씨드 공유로 개발자가 같은 상황 재현 가능
- 스트리밍/방송 친화 — 시청자와 같은 런 공유

대표 사례:
- Hades — 매일 다른 챌린지 조건 (Pact of Punishment 조합)
- The Binding of Isaac — 데일리 런 (Steam 리더보드 연동)
- Noita — 씨드 입력 기능으로 같은 맵 재경험
- Spelunky 2 — 데일리 챌린지 (단 1회만 제출 가능)

---

## Unity 구현 방법

### 1. Random.InitState로 씨드 고정

```csharp
// 씨드 기반 랜덤 초기화
public static class SeededRandom
{
    private static int _currentSeed;
    
    public static void Initialize(int seed)
    {
        _currentSeed = seed;
        Random.InitState(seed);
        Debug.Log($"[Seed] Initialized with seed: {seed}");
    }
    
    public static int CurrentSeed => _currentSeed;
    
    // 날짜 기반 씨드 (데일리 챌린지용)
    public static int GetDailySeed()
    {
        // 날짜를 yyyyMMdd 형식 정수로 변환
        // 예: 2026-07-05 → 20260705
        var today = System.DateTime.UtcNow;
        return today.Year * 10000 + today.Month * 100 + today.Day;
    }
    
    // 랜덤 씨드 생성
    public static int GenerateRandomSeed()
    {
        return UnityEngine.Random.Range(100000, 999999);
    }
}
```

### 2. GameManager에서 씨드 관리

```csharp
public class GameManager : MonoBehaviour
{
    public static GameManager Instance;
    
    [SerializeField] private RunConfig currentRun;
    
    public void StartNormalRun()
    {
        int seed = SeededRandom.GenerateRandomSeed();
        StartRunWithSeed(seed, RunMode.Normal);
    }
    
    public void StartDailyChallenge()
    {
        int seed = SeededRandom.GetDailySeed();
        StartRunWithSeed(seed, RunMode.Daily);
    }
    
    public void StartRunWithSeed(int seed, RunMode mode = RunMode.Custom)
    {
        currentRun = new RunConfig
        {
            Seed = seed,
            Mode = mode,
            StartTime = System.DateTime.UtcNow
        };
        
        SeededRandom.Initialize(seed);
        SceneManager.LoadScene("GameScene");
    }
}

[System.Serializable]
public class RunConfig
{
    public int Seed;
    public RunMode Mode;
    public System.DateTime StartTime;
}

public enum RunMode { Normal, Daily, Custom }
```

### 3. 씨드 입력 UI

```csharp
using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class SeedInputPanel : MonoBehaviour
{
    [SerializeField] private TMP_InputField seedInputField;
    [SerializeField] private Button startButton;
    [SerializeField] private Button randomButton;
    [SerializeField] private TextMeshProUGUI feedbackText;
    
    void Start()
    {
        startButton.onClick.AddListener(OnStartWithSeed);
        randomButton.onClick.AddListener(OnRandomSeed);
    }
    
    void OnStartWithSeed()
    {
        string input = seedInputField.text.Trim();
        
        if (string.IsNullOrEmpty(input))
        {
            feedbackText.text = "씨드를 입력하세요.";
            return;
        }
        
        if (!int.TryParse(input, out int seed))
        {
            feedbackText.text = "숫자만 입력 가능합니다.";
            return;
        }
        
        GameManager.Instance.StartRunWithSeed(seed, RunMode.Custom);
    }
    
    void OnRandomSeed()
    {
        int randomSeed = SeededRandom.GenerateRandomSeed();
        seedInputField.text = randomSeed.ToString();
    }
}
```

### 4. 데일리 챌린지 — 1회 제출 제한

```csharp
using UnityEngine;

public class DailyChallenge : MonoBehaviour
{
    private const string DAILY_KEY_PREFIX = "daily_done_";
    
    // 오늘 이미 플레이했는지 확인
    public bool HasPlayedToday()
    {
        string todayKey = GetTodayKey();
        return PlayerPrefs.GetInt(todayKey, 0) == 1;
    }
    
    // 오늘 플레이 기록 저장
    public void MarkTodayAsPlayed()
    {
        PlayerPrefs.SetInt(GetTodayKey(), 1);
        PlayerPrefs.Save();
    }
    
    // 오늘 데일리 결과 저장
    public void SaveDailyResult(int score, float clearTime, bool cleared)
    {
        string todayKey = GetTodayKey();
        PlayerPrefs.SetInt($"{todayKey}_score", score);
        PlayerPrefs.SetFloat($"{todayKey}_time", clearTime);
        PlayerPrefs.SetInt($"{todayKey}_cleared", cleared ? 1 : 0);
        PlayerPrefs.Save();
    }
    
    private string GetTodayKey()
    {
        var today = System.DateTime.UtcNow;
        return DAILY_KEY_PREFIX + today.ToString("yyyyMMdd");
    }
}
```

### 5. 씨드 기반 방 생성 보장

씨드를 쓰더라도 `Random.Range`를 다른 순서로 호출하면 결과가 달라진다.  
일관성을 보장하려면 씨드 초기화 후 **호출 순서를 고정**해야 한다.

```csharp
// 방 생성기에서 씨드 의존 부분
public class DungeonGenerator : MonoBehaviour
{
    public Room[] GenerateRooms()
    {
        // 씨드 초기화는 GameManager에서 이미 완료된 상태
        // 순서 일관성: 항상 같은 순서로 Random.Range 호출
        
        int roomCount = Random.Range(5, 10);              // 1번 호출
        Room[] rooms = new Room[roomCount];
        
        for (int i = 0; i < roomCount; i++)
        {
            rooms[i].type = (RoomType)Random.Range(0, 4); // 2~N번 호출 (순서 고정)
        }
        
        return rooms;
    }
}
```

---

## OnionCat 적용 포인트

### 구현 우선순위

1. **1단계 (MVP)**: 씨드 저장/불러오기 + 씨드 표시 UI
   - 런 시작 시 랜덤 씨드 생성 → `Random.InitState()` 호출
   - 게임 오버/클리어 화면에 씨드 번호 표시 (공유 가능)

2. **2단계**: 씨드 입력 화면
   - 메인 메뉴에 "커스텀 씨드로 시작" 버튼
   - 숫자 6자리 입력 → 같은 런 재경험

3. **3단계**: 데일리 챌린지
   - 날짜 기반 자동 씨드
   - 오늘 클리어 여부 저장 (PlayerPrefs)

### 씨드와 2인 협동 주의점

- 두 플레이어가 같은 씨드로 플레이해도 **입력 순서가 다르면 결과 달라짐**
- 로컬 협동에서는 씨드 공유 쉬움 (같은 기기)
- 온라인 협동까지 고려한다면 씨드 동기화 처리 필요 (OnionCat은 로컬 Co-op이므로 단순)

### 씨드 공유 문자열 포맷

```csharp
// 공유용 문자열 생성: "ONION-123456" 형식
public string GetShareableCode()
{
    return $"ONION-{SeededRandom.CurrentSeed:D6}";
}

// 문자열에서 씨드 파싱
public bool TryParseCode(string code, out int seed)
{
    seed = 0;
    if (!code.StartsWith("ONION-")) return false;
    return int.TryParse(code.Substring(6), out seed);
}
```

---

## 참고 링크

- [Unity 공식 - Random.InitState](https://docs.unity3d.com/ScriptReference/Random.InitState.html)
- [Unity 공식 - PlayerPrefs](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [GDC - Procedural Level Design in Spelunky (YouTube)](https://www.youtube.com/watch?v=Uqk5Zf0tw3o)
- [The Binding of Isaac - Daily Challenge 분석](https://bindingofisaacrebirth.fandom.com/wiki/Daily_Challenges)
- [Game Design - Seeded Runs and Fairness in Roguelikes](https://www.gamedeveloper.com/design/seeded-randomness-in-roguelikes)
