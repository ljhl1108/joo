# 씨드 기반 런 생성 (Seeded Run Generation)

리서치 날짜: 2026-09-21

## 개요

씨드(seed) 기반 생성은 로그라이크의 무작위 콘텐츠(방 배치, 아이템 드롭, 적 구성 등)를 **결정론적(deterministic)** 으로 재현할 수 있게 해준다.
같은 씨드 값을 쓰면 항상 동일한 런이 펼쳐진다.

OnionCat에서 필요한 이유:
- **데일리 챌린지**: 매일 모든 플레이어가 같은 던전을 경험
- **버그 재현**: 특정 씨드로 재현 가능한 버그 → 디버깅 훨씬 쉬움
- **스피드런 공정성**: 동일 씨드로 비교
- **리플레이 시스템**: 씨드 + 입력 기록으로 완전한 리플레이 가능

---

## Unity 구현 방법

### 1. Unity Random vs System.Random

```csharp
// Unity의 Random — 글로벌 상태, 씨드 초기화 가능
Random.InitState(seed);
int result = Random.Range(0, 10);

// System.Random — 인스턴스 기반, 여러 독립 스트림 가능
System.Random rng = new System.Random(seed);
int result = rng.Next(0, 10);
```

**OnionCat 권장**: `System.Random` 인스턴스를 용도별로 따로 유지.
Unity `Random`은 파티클/애니메이션 등 엔진 내부도 쓰기 때문에 씨드가 오염될 수 있다.

### 2. 씨드 생성 전략

```csharp
public static class SeedGenerator
{
    // 일반 런: 무작위 씨드
    public static int NewRunSeed() => Random.Range(int.MinValue, int.MaxValue);

    // 데일리 챌린지: 날짜 기반 고정 씨드
    public static int DailyChallengeSeed()
    {
        var today = System.DateTime.UtcNow.Date;
        return today.Year * 10000 + today.Month * 100 + today.Day;
    }

    // 문자열 → 정수 씨드 (플레이어가 직접 입력하는 씨드 코드 지원)
    public static int FromString(string s)
    {
        int hash = 17;
        foreach (char c in s)
            hash = hash * 31 + c;
        return hash;
    }
}
```

### 3. RunData에 씨드 저장

```csharp
// GameManager.RunData에 추가
[System.Serializable]
public class RunData
{
    public int seed;
    public System.Random roomRng;    // 방 배치용
    public System.Random enemyRng;   // 적 스폰용
    public System.Random lootRng;    // 아이템 드롭용
    public System.Random eventRng;   // 랜덤 이벤트용

    public void Initialize(int seed)
    {
        this.seed = seed;
        // 같은 씨드에서 서로 다른 오프셋으로 독립된 스트림 생성
        roomRng  = new System.Random(seed);
        enemyRng = new System.Random(seed + 1);
        lootRng  = new System.Random(seed + 2);
        eventRng = new System.Random(seed + 3);
    }
}
```

### 4. 방 배치에 씨드 적용

```csharp
public class DungeonGenerator : MonoBehaviour
{
    public RoomData[] roomPool;

    public RoomData PickRoom(RunData run, RoomType type)
    {
        // GameManager.Instance.Run.roomRng 사용
        var eligible = System.Array.FindAll(roomPool, r => r.type == type);
        int idx = run.roomRng.Next(0, eligible.Length);
        return eligible[idx];
    }
}
```

### 5. 가중치 랜덤에 씨드 적용

```csharp
public static T WeightedRandom<T>(IList<(T item, float weight)> table, System.Random rng)
{
    float total = 0f;
    foreach (var (_, w) in table) total += w;

    double roll = rng.NextDouble() * total;
    float cumulative = 0f;
    foreach (var (item, w) in table)
    {
        cumulative += w;
        if (roll <= cumulative) return item;
    }
    return table[table.Count - 1].item;
}
```

### 6. 씨드 UI (선택 사항)

```csharp
// 런 시작 화면에서 씨드 표시/입력
public class SeedInputUI : MonoBehaviour
{
    [SerializeField] private TMP_InputField seedField;
    [SerializeField] private TMP_Text displayText;

    private int currentSeed;

    void Start()
    {
        currentSeed = SeedGenerator.NewRunSeed();
        displayText.text = currentSeed.ToString();
    }

    public void OnPlayerTypesSeed(string input)
    {
        if (int.TryParse(input, out int parsed))
            currentSeed = parsed;
        else
            currentSeed = SeedGenerator.FromString(input);
    }

    public void StartRun()
    {
        GameManager.Instance.Run.Initialize(currentSeed);
        // 씬 전환
    }
}
```

---

## OnionCat 적용 포인트

### 즉시 적용 가능한 것

1. **RunData.Initialize(seed)** 추가 → 모든 무작위 생성에 `run.roomRng`/`run.lootRng` 사용
2. 현재 `Random.Range` 호출을 `run.roomRng.Next()` 로 교체 → 결정론적 런 확보
3. 런 시작 시 씨드를 `GameManager` 로그에 출력 → 버그 재현 즉시 가능

### 데일리 챌린지 구현 순서 (미래 기능)

```
1. SeedGenerator.DailyChallengeSeed() → 오늘 씨드 계산
2. RunData.Initialize(seed) → 던전/적/아이템 모두 고정
3. 완료 시 기록 저장 (PlayerPrefs or JSON)
4. 같은 날짜에 재도전 차단 (날짜 비교)
5. 씨드 공유 버튼 → 클립보드에 복사
```

### 주의사항

- **씬 전환 전 씨드 생성**: 씨드는 RunData에 저장 후 씬 넘어가야 함. 씬이 바뀌면 `DontDestroyOnLoad` 없이는 사라짐.
- **Physics2D는 씨드 영향 없음**: 물리 시뮬레이션은 프레임 타이밍 의존 → 완전한 결정론은 불가능. 씨드는 콘텐츠 생성에만 적용.
- **멀티스레드 주의**: `System.Random`은 스레드 안전하지 않음. 메인 스레드에서만 사용할 것.

---

## 참고 링크

- [Unity Docs: Random.InitState](https://docs.unity3d.com/ScriptReference/Random.InitState.html)
- [Roguelike Tutorial: Seeded Generation (Unity)](https://gamedevacademy.org/unity-random-seed-tutorial/)
- [Spelunky Daily Challenge 구현 방식 분석](https://spelunky.fandom.com/wiki/Daily_Challenge)
- [System.Random vs UnityEngine.Random](https://stackoverflow.com/questions/43294553/random-range-not-the-same-with-the-same-seed)
