# 런 내 씬 간 데이터 공유 시스템 (In-Run Data Persistence Across Scenes)

리서치 날짜: 2026-08-02

## 개요

로그라이크 게임은 "로비 씬 → 던전 씬 → 보상 씬 → 다음 방 씬" 식으로 여러 씬을 넘나든다. 문제는 **Unity에서 씬을 전환하면 해당 씬의 모든 오브젝트가 파괴**된다는 것. 런 중에 쌓인 HP·인벤토리·업그레이드·진행 상황을 씬 전환 사이에도 유지해야 한다. 이것이 "런 내 씬 간 데이터 공유"의 핵심 문제다.

OnionCat에서는:
- Cat/Onion 각각의 능력 업그레이드 상태
- 현재 HP (공유 체력)
- 획득한 렐릭/패시브 목록
- 방 번호, 층 번호, 방문한 방 기록
- 런 통계 (처치 수, 경과 시간 등)

이 모든 것을 씬 간에 유지해야 한다.

---

## Unity 구현 방법

### 방법 1: DontDestroyOnLoad (가장 단순)

```csharp
// RunManager.cs — 씬 전환 후에도 살아남는 싱글턴
public class RunManager : MonoBehaviour
{
    public static RunManager Instance { get; private set; }

    [Header("Run State")]
    public int currentHp = 100;
    public int maxHp = 100;
    public int roomNumber = 0;
    public int floorNumber = 1;
    public List<string> acquiredRelicIds = new();
    public List<string> catUpgradeIds = new();
    public List<string> onionUpgradeIds = new();

    void Awake()
    {
        if (Instance != null)
        {
            Destroy(gameObject);  // 중복 방지
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    public void ResetRun()
    {
        currentHp = maxHp;
        roomNumber = 0;
        floorNumber = 1;
        acquiredRelicIds.Clear();
        catUpgradeIds.Clear();
        onionUpgradeIds.Clear();
    }
}
```

**장점**: 가장 쉽고 빠름  
**단점**: Inspector에서 실시간 상태 확인이 어렵고, 씬 리로드 시 중복 생성 버그 주의

---

### 방법 2: ScriptableObject 런타임 데이터 컨테이너 (권장)

ScriptableObject는 씬과 무관하게 존재하는 에셋이다. 씬이 전환돼도 Reference가 유지된다.

```csharp
// RunDataSO.cs
[CreateAssetMenu(menuName = "OnionCat/RunData")]
public class RunDataSO : ScriptableObject
{
    [Header("Player State")]
    public int currentHp;
    public int maxHp;

    [Header("Run Progress")]
    public int roomNumber;
    public int floorNumber;
    public float runTime;  // 경과 시간 (초)
    public int killCount;

    [Header("Upgrades & Relics")]
    public List<string> catUpgradeIds = new();
    public List<string> onionUpgradeIds = new();
    public List<string> relicIds = new();

    public void ResetForNewRun()
    {
        currentHp = maxHp = 100;
        roomNumber = 0;
        floorNumber = 1;
        runTime = 0f;
        killCount = 0;
        catUpgradeIds.Clear();
        onionUpgradeIds.Clear();
        relicIds.Clear();
    }
}
```

```csharp
// 사용처 — 어느 씬에서든 [SerializeField]로 연결해서 참조
public class PlayerHealthController : MonoBehaviour
{
    [SerializeField] private RunDataSO runData;  // Inspector에서 드래그

    void Start()
    {
        // 씬 전환 후에도 runData는 동일 에셋을 참조 → 데이터 유지
        GetComponent<HealthSystem>().Initialize(runData.currentHp, runData.maxHp);
    }
}
```

**장점**: Inspector에서 실시간 값 확인 가능, 씬 간 자동 공유, 에디터 플레이 중 디버깅 쉬움  
**단점**: 에디터 플레이 테스트 종료 후에도 값이 남아 있을 수 있음 → `OnEnable`에서 Reset 또는 별도 초기화 로직 필요

**주의**: 에디터 종료 후 SO 값이 남는 문제 해결법:
```csharp
// 게임 시작점(MainMenu.cs)에서 항상 리셋
void Start()
{
    runData.ResetForNewRun();  // 새 게임 시작 시 항상 초기화
}
```

---

### 방법 3: 정적 클래스 (Static Class)

```csharp
// RunState.cs — MonoBehaviour 없이 순수 데이터 클래스
public static class RunState
{
    public static int CurrentHp { get; set; } = 100;
    public static int MaxHp { get; set; } = 100;
    public static int RoomNumber { get; set; } = 0;
    public static List<string> RelicIds { get; } = new();

    public static void Reset()
    {
        CurrentHp = MaxHp = 100;
        RoomNumber = 0;
        RelicIds.Clear();
    }
}
```

**장점**: 가장 간단한 문법, 어디서든 `RunState.CurrentHp` 형태로 접근  
**단점**: Inspector에서 보이지 않음, 직렬화/역직렬화 불편, 단위 테스트 어려움

---

### 방법 비교 정리

| 방법 | 난이도 | Inspector 확인 | 씬 간 공유 | 저장 파일 연동 | 추천 상황 |
|------|--------|--------------|-----------|--------------|---------|
| DontDestroyOnLoad | ★☆☆ | 가능 | 자동 | 보통 | 빠른 프로토타입 |
| ScriptableObject | ★★☆ | 쉬움 | 자동 | 쉬움 | **OnionCat 권장** |
| 정적 클래스 | ★☆☆ | 불가 | 자동 | 어려움 | 작은 임시 데이터 |

---

### 씬 전환 시 초기화 타이밍

```csharp
// 새 방 씬이 로드되면 자동 호출
public class RoomInitializer : MonoBehaviour
{
    [SerializeField] private RunDataSO runData;

    void OnEnable()
    {
        SceneManager.sceneLoaded += OnSceneLoaded;
    }

    void OnDisable()
    {
        SceneManager.sceneLoaded -= OnSceneLoaded;
    }

    void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        if (scene.name == "RoomScene")
        {
            runData.roomNumber++;
            // 방 입장 시 필요한 초기화 수행
        }
    }
}
```

---

### OnionCat 권장 아키텍처

```
[RunDataSO 에셋] ─────────────────────────────────────┐
     │                                                 │
     ├── PlayerHealthController (체력 읽기/쓰기)       │
     ├── UpgradeManager (업그레이드 목록 읽기/쓰기)    │
     ├── RelicManager (렐릭 목록 관리)                 │
     ├── RoomInitializer (방 번호 증가)                │
     ├── RunResultScreen (런 결과 화면에 표시)         │
     └── SaveManager (파일에 직렬화)                   │
                                                       │
※ 모든 씬에서 동일한 RunDataSO 에셋을 참조 ───────────┘
```

---

## OnionCat 적용 포인트

1. **RunDataSO 에셋 1개 생성** → `Assets/Data/RunData.asset`으로 저장
2. **Cat 업그레이드 목록** `catUpgradeIds`, **Onion 업그레이드 목록** `onionUpgradeIds` 별도 관리
3. **방 클리어 시** `roomNumber++`, `killCount += enemiesKilled` → SO에 즉시 저장
4. **씬 전환 애니메이션(페이드 아웃)** 중에 SO 데이터를 JSON 파일로 동시 백업 → 앱 강제 종료 대응
5. **RunResultScreen**에서 `runData.killCount`, `runData.runTime`, `runData.relicIds.Count` 등을 읽어 결과 화면 표시

---

## 참고 링크

- Unity 공식: ScriptableObjects as data containers — https://docs.unity3d.com/Manual/class-ScriptableObject.html
- DontDestroyOnLoad 공식 — https://docs.unity3d.com/ScriptReference/Object.DontDestroyOnLoad.html
- SceneManager.sceneLoaded 이벤트 — https://docs.unity3d.com/ScriptReference/SceneManagement.SceneManager-sceneLoaded.html
- Game Dev Guide — "How to pass data between scenes in Unity" — https://www.youtube.com/watch?v=ON0rc9GBgUI
