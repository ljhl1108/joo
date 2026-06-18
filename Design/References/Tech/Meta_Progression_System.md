# 메타 진행 시스템 (Meta Progression)

리서치 날짜: 2026-06-18

## 개요

메타 진행(Meta Progression)은 한 런이 끝나도 영구적으로 보존되는 성장 시스템이다. 로그라이크에서 '퍼마데스'의 좌절을 완화하고, 반복 플레이 동기를 제공하는 핵심 장치다. Hades의 골드/다이아몬드 조각, Rogue Legacy 2의 골드 성장, Vampire Survivors의 코인 업그레이드가 모두 이 시스템이다. OnionCat은 농업 테마를 살려 "씨앗"이나 "양분"을 메타 통화로 활용할 수 있다.

---

## Unity 구현 방법

### 1. 메타 데이터 구조 설계

```csharp
[System.Serializable]
public class MetaProgressData
{
    // 누적 통화
    public int totalSeeds;          // 메타 통화 (씨앗)
    public int totalRunsCompleted;
    public int totalEnemiesKilled;

    // 영구 업그레이드 해금 상태 (인덱스 = 업그레이드 ID)
    public List<string> unlockedUpgradeIds = new List<string>();

    // 영구 스탯 보너스
    public float permanentHealthBonus = 0f;
    public float permanentDamageBonus = 0f;
    public int permanentExtraCardChoices = 0;
}
```

### 2. 저장/불러오기 (JSON 방식)

```csharp
public class MetaProgressManager : MonoBehaviour
{
    public static MetaProgressManager Instance { get; private set; }

    private MetaProgressData data = new MetaProgressData();
    private const string SavePath = "meta_progress.json";

    private string FullPath => System.IO.Path.Combine(
        Application.persistentDataPath, SavePath);

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        Load();
    }

    public void Save()
    {
        string json = JsonUtility.ToJson(data, prettyPrint: true);
        System.IO.File.WriteAllText(FullPath, json);
    }

    public void Load()
    {
        if (!System.IO.File.Exists(FullPath)) return;
        string json = System.IO.File.ReadAllText(FullPath);
        data = JsonUtility.FromJson<MetaProgressData>(json);
    }

    public void AddSeeds(int amount)
    {
        data.totalSeeds += amount;
        Save();
    }

    public bool SpendSeeds(int cost)
    {
        if (data.totalSeeds < cost) return false;
        data.totalSeeds -= cost;
        Save();
        return true;
    }

    public void OnRunEnd(int seedsEarned, int kills)
    {
        data.totalRunsCompleted++;
        data.totalEnemiesKilled += kills;
        AddSeeds(seedsEarned);
    }
}
```

### 3. 영구 업그레이드 ScriptableObject

```csharp
[CreateAssetMenu(menuName = "OnionCat/Meta Upgrade")]
public class MetaUpgradeData : ScriptableObject
{
    public string upgradeId;       // 고유 ID ("extra_health_1")
    public string displayName;
    [TextArea] public string description;
    public Sprite icon;
    public int seedCost;
    public string prerequisiteId;  // 선행 업그레이드 ID (트리 구조)

    // 효과 종류
    public MetaUpgradeEffect effect;
    public float effectValue;
}

public enum MetaUpgradeEffect
{
    MaxHealthBonus,
    DamageBonus,
    ExtraCardChoice,
    StartWithItem,
    UnlockCharacterVariant,
    SeedDropRateBonus
}
```

### 4. 업그레이드 트리 UI (메타 화면)

```csharp
public class MetaUpgradeShop : MonoBehaviour
{
    [SerializeField] private MetaUpgradeData[] allMetaUpgrades;
    [SerializeField] private MetaUpgradeButton buttonPrefab;
    [SerializeField] private Transform buttonContainer;
    [SerializeField] private TextMeshProUGUI seedCountText;

    private void Start()
    {
        seedCountText.text = $"씨앗: {MetaProgressManager.Instance.TotalSeeds}";
        foreach (var upgrade in allMetaUpgrades)
            CreateButton(upgrade);
    }

    private void CreateButton(MetaUpgradeData upgrade)
    {
        var btn = Instantiate(buttonPrefab, buttonContainer);
        bool isUnlocked = MetaProgressManager.Instance.IsUnlocked(upgrade.upgradeId);
        bool prerequisiteMet = string.IsNullOrEmpty(upgrade.prerequisiteId)
            || MetaProgressManager.Instance.IsUnlocked(upgrade.prerequisiteId);

        btn.Setup(upgrade, isUnlocked, prerequisiteMet, OnUpgradePurchased);
    }

    private void OnUpgradePurchased(MetaUpgradeData upgrade)
    {
        if (!MetaProgressManager.Instance.SpendSeeds(upgrade.seedCost)) return;
        MetaProgressManager.Instance.UnlockUpgrade(upgrade.upgradeId);
        ApplyEffect(upgrade);
        RefreshUI();
    }
}
```

### 5. 런 시작 시 메타 보너스 적용

```csharp
public class RunInitializer : MonoBehaviour
{
    [SerializeField] private PlayerStats catStats;
    [SerializeField] private PlayerStats onionStats;

    private void Start()
    {
        var meta = MetaProgressManager.Instance;

        // 영구 보너스 적용
        catStats.maxHealth += meta.PermanentHealthBonus;
        catStats.damageMultiplier += meta.PermanentDamageBonus;

        // 잠금 해제된 시작 아이템 지급
        foreach (var startItemId in meta.GetUnlockedStartItems())
            GrantStartItem(startItemId);
    }
}
```

### 6. 씨앗 드롭 시스템 (런 중)

```csharp
public class SeedDropper : MonoBehaviour
{
    [SerializeField] private GameObject seedPickupPrefab;

    public void DropSeeds(Vector2 position, int minAmount, int maxAmount)
    {
        int count = Random.Range(minAmount, maxAmount + 1);
        for (int i = 0; i < count; i++)
        {
            Vector2 offset = Random.insideUnitCircle * 0.5f;
            Instantiate(seedPickupPrefab, position + offset, Quaternion.identity);
        }
    }
}

// 런 종료 시 수집한 씨앗을 메타로 전달
public class RunEndHandler : MonoBehaviour
{
    public void HandleRunEnd(bool victory, int seedsCollected, int kills)
    {
        // 승리 보너스
        int bonus = victory ? seedsCollected / 2 : 0;
        MetaProgressManager.Instance.OnRunEnd(seedsCollected + bonus, kills);

        // 런 결과 화면으로 이동
        SceneManager.LoadScene("RunResult");
    }
}
```

---

## OnionCat 적용 포인트

### 메타 통화: 씨앗 (Seeds)
```
온전히 OnionCat 테마에 맞는 메타 통화:
- 런 중 적 처치, 보물상자, 이벤트 클리어로 씨앗 획득
- 런 실패해도 수집한 씨앗은 영구 보존
- 씨앗으로 홈베이스(화분 집)에서 영구 업그레이드 구매
```

### 추천 메타 업그레이드 트리 구조
```
티어 1 (저렴, 즉시 체감):
- 최대 체력 +10% (500씨앗)
- 런 시작 씨앗 +5 (300씨앗)
- 업그레이드 선택지 +1 (400씨앗)

티어 2 (중간, 빌드 영향):
- 캣 대쉬 쿨다운 -10% (800씨앗)
- 어니언 투사체 크기 +15% (800씨앗)
- 새 업그레이드 카드 해금 (1000씨앗)

티어 3 (고가, 게임 변화):
- 새 캐릭터 스킨/변형 해금 (2000씨앗)
- "씨앗 넘치는 스타트" (런 시작 시 업그레이드 1개 즉시 획득) (2500씨앗)
- 특수 비밀방 해금 조건 (3000씨앗)
```

### 씬 구성
```
MetaProgressManager: DontDestroyOnLoad 싱글톤
HomeBase 씬: 메타 업그레이드 구매 화면 (런 시작 전 로비)
RunResult 씬: 씨앗 정산 → HomeBase로 복귀
```

### 주의사항
- `Application.persistentDataPath`는 플랫폼마다 경로 다름 — 빌드 테스트 필수
- 씨앗 수가 많아지면 `int` 오버플로우 가능 → `long` 또는 상한선 설정
- 업그레이드 밸런스는 "첫 2~3런 내에 뭔가 달라진다" 느낌이 중요

---

## 참고 링크

- Unity 공식 - Application.persistentDataPath: https://docs.unity3d.com/ScriptReference/Application-persistentDataPath.html
- Unity JSON 직렬화: https://docs.unity3d.com/Manual/JSONSerialization.html
- Brackeys - Save & Load System: https://www.youtube.com/watch?v=XOjd_qU2Ido
- GDC - "Roguelite Retention Loop" 강연: https://www.gdcvault.com
- Rogue Legacy 2 메타 진행 분석: https://store.steampowered.com/app/1253920/Rogue_Legacy_2/
