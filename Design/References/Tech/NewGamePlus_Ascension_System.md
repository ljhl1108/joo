# New Game+ / Ascension Mode System (뉴게임플러스 / 상승 난이도 시스템)

리서치 날짜: 2026-07-16

## 개요

첫 클리어 후 해금되는 점진적 난이도 상승 시스템.
Hades의 **Heat 시스템**, Binding of Isaac의 **Hard Mode**, Dead Cells의 **Boss Cell**이 대표 사례.
- 엔딩 후 콘텐츠 수명 대폭 연장
- 숙련 플레이어에게 지속적인 도전 제공
- 메타 진행 레이어 추가 → 장기 플레이 동기 부여
- OnionCat에서는 "협력 난이도 조절"이라는 고유 컨셉과 결합 가능

---

## 레퍼런스 사례 분석

### Hades — Pact of Punishment (처벌 계약)
- **구조**: 20개 조건 각각 독립적으로 활성/강도 설정
- **예시 조건**: 
  - Hard Labor: 적 HP 20/40/60% 증가
  - Jury Summons: 미니보스 추가 등장
  - Tight Deadline: 방 탈출에 시간 제한
  - Extreme Measures: 보스 추가 페이즈 해금
- **보상**: 특정 Heat 수치 달성 시 전용 대화/아이템/외형 해금
- **핵심**: 자유 조합 → 내가 원하는 방식으로 어렵게 가능

### Dead Cells — Boss Cells
- **구조**: 선형 스택 (1BC → 2BC → 5BC)
- **1BC**: 타이머 추가, 데미지 증가
- **5BC**: 모든 악조건 합산, 매우 어려움
- **핵심**: 달성할 수록 더 강한 셀 드롭 → 자동 갱신

### Binding of Isaac — Hard Mode
- **구조**: 단순 ON/OFF
- **효과**: 적 HP 증가, 아이템 드롭율 감소, 저주 발생률 증가
- **핵심**: 진입 장벽 낮음, 복잡하지 않음

---

## Unity 구현 방법

### 1. 데이터 구조 설계 (ScriptableObject)

```csharp
[CreateAssetMenu(menuName = "OnionCat/AscensionModifier")]
public class AscensionModifier : ScriptableObject
{
    public string modifierName;
    [TextArea] public string description;
    public int maxLevel;
    public Sprite icon;
    // 실제 효과는 GameDifficultyManager가 읽어서 적용
}
```

```csharp
// 런타임에서 사용하는 저장 가능한 구조체
[System.Serializable]
public class AscensionState
{
    public string modifierId;
    public int currentLevel;  // 0 = 비활성
}
```

### 2. 저장/로드 (SaveManager 연동)

```csharp
[System.Serializable]
public class MetaSaveData
{
    public bool ng_unlocked = false;  // 첫 클리어 후 true
    public List<AscensionState> ascensionStates = new();
    public int totalHeatLevel = 0;    // 활성 레벨 합산
}

public class MetaSaveManager : MonoBehaviour
{
    private const string SAVE_PATH = "/meta_save.json";

    public void Save(MetaSaveData data)
    {
        string json = JsonUtility.ToJson(data, true);
        File.WriteAllText(Application.persistentDataPath + SAVE_PATH, json);
    }

    public MetaSaveData Load()
    {
        string path = Application.persistentDataPath + SAVE_PATH;
        if (!File.Exists(path)) return new MetaSaveData();
        return JsonUtility.FromJson<MetaSaveData>(File.ReadAllText(path));
    }
}
```

### 3. 난이도 적용 매니저

```csharp
public class GameDifficultyManager : MonoBehaviour
{
    public static GameDifficultyManager Instance { get; private set; }

    [SerializeField] private MetaSaveData saveData;

    // 각 시스템이 값을 조회하는 방식으로 설계
    public float EnemyHPMultiplier =>
        1f + GetLevelOf("hard_labor") * 0.2f;

    public float DropRateMultiplier =>
        1f - GetLevelOf("scarcity") * 0.1f;

    public bool IsTimerEnabled =>
        GetLevelOf("tight_deadline") > 0;

    public float RoomTimerSeconds =>
        120f - GetLevelOf("tight_deadline") * 20f;

    private int GetLevelOf(string id)
    {
        var state = saveData.ascensionStates.Find(s => s.modifierId == id);
        return state?.currentLevel ?? 0;
    }

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        saveData = FindFirstObjectByType<MetaSaveManager>().Load();
    }
}
```

### 4. 적 AI에 적용

```csharp
// EnemyStats.cs
private void Awake()
{
    float hpMult = GameDifficultyManager.Instance?.EnemyHPMultiplier ?? 1f;
    currentHP = Mathf.RoundToInt(baseHP * hpMult);
}
```

### 5. Ascension 선택 UI 씬

```
[씬 구성]
AscensionMenuScene
├── Canvas
│   ├── ModifierList (ScrollView)
│   │   └── ModifierItem (Prefab) × N
│   │       ├── Icon (Image)
│   │       ├── Name (TMP)
│   │       ├── Description (TMP)
│   │       └── LevelSelector (+ / - 버튼)
│   ├── TotalHeatDisplay (TMP) — "현재 Heat: 7"
│   ├── StartRunButton
│   └── BackButton
└── AscensionMenuController.cs
```

```csharp
public class AscensionMenuController : MonoBehaviour
{
    [SerializeField] private TMP_Text heatLabel;
    [SerializeField] private AscensionModifier[] allModifiers;

    private MetaSaveData saveData;
    private MetaSaveManager saveManager;

    private void Start()
    {
        saveManager = FindFirstObjectByType<MetaSaveManager>();
        saveData = saveManager.Load();
        RefreshHeatDisplay();
    }

    public void ChangeLevel(string modifierId, int delta)
    {
        var state = saveData.ascensionStates.Find(s => s.modifierId == modifierId);
        if (state == null)
        {
            state = new AscensionState { modifierId = modifierId };
            saveData.ascensionStates.Add(state);
        }

        var mod = System.Array.Find(allModifiers, m => m.name == modifierId);
        state.currentLevel = Mathf.Clamp(state.currentLevel + delta, 0, mod.maxLevel);
        saveData.totalHeatLevel = saveData.ascensionStates.Sum(s => s.currentLevel);

        saveManager.Save(saveData);
        RefreshHeatDisplay();
    }

    private void RefreshHeatDisplay()
    {
        heatLabel.text = $"현재 Heat: {saveData.totalHeatLevel}";
    }

    public void StartRun()
    {
        SceneManager.LoadScene("GameScene");
    }
}
```

### 6. 첫 클리어 시 해금

```csharp
// 엔딩 씬 또는 GameOverManager에서 호출
public void OnRunCleared()
{
    var meta = saveManager.Load();
    if (!meta.ng_unlocked)
    {
        meta.ng_unlocked = true;
        saveManager.Save(meta);
        ShowUnlockMessage("상승 모드 해금!");
    }
}
```

---

## 권장 Modifier 세트 (OnionCat용)

| ID | 이름 | 효과 | 최대 레벨 |
|----|------|------|-----------|
| `hard_labor` | 혹독한 노동 | 적 HP +20% per level | 3 |
| `tight_deadline` | 제한 시간 | 방 클리어 타이머 추가 | 2 |
| `scarcity` | 아이템 희귀 | 드롭율 -10% per level | 3 |
| `elite_squad` | 정예 부대 | 엘리트 적 등장률 증가 | 2 |
| `no_mercy` | 무자비 | 부활 기회 감소 | 2 |
| `double_trouble` | 이중 고난 | 보스 2개 동시 등장 | 1 |
| `cat_only` | 고양이만 | P2(Onion) 능력 일시 잠금 | 1 |

---

## OnionCat 적용 포인트

### 1. 협력 특화 Modifier
- **"역할 반전"**: 고양이가 원거리, 양파가 근접으로 강제 전환
- **"단독 수행"**: 특정 방에서 한 명의 조작 일시 잠금 → 나머지 한 명이 클리어
- **"공유 체력"**: 개별 HP 대신 공유 HP 사용 → 협력 긴장감 MAX

### 2. 단계별 해금 구조
```
0클리어: 기본 모드
1클리어: Ascension 1-3 해금 (기본 강화)
5클리어: Ascension 4-6 해금 (고난이도 변형)
10클리어: Ascension 7 해금 "진짜 협력" 도전 모드
```

### 3. 씬 구성 순서
1. `MetaSaveManager.cs` 작성 (JSON 저장/로드)
2. `GameDifficultyManager.cs` 작성 (Singleton, 게임 씬에서 참조)
3. `AscensionModifier ScriptableObject` 데이터 에셋 생성
4. `AscensionMenuScene` 구성 (UI + `AscensionMenuController.cs`)
5. `GameClearManager`에서 `ng_unlocked = true` 처리

---

## 참고 링크

- [Hades 개발자 GDC 강연: Pact of Punishment Design](https://www.youtube.com/watch?v=JHPCxHEA4hQ)
- [Unity 공식: PlayerPrefs vs JSON 저장](https://docs.unity3d.com/Manual/PlayerPrefs.html)
- [Unity 공식: ScriptableObject](https://docs.unity3d.com/Manual/class-ScriptableObject.html)
- [Game Maker's Toolkit: Difficulty Settings That Work](https://www.youtube.com/watch?v=ZW8gWgpptI8)
- [Dead Cells Boss Cell 시스템 분석 블로그](https://www.motiontwingames.com/)
