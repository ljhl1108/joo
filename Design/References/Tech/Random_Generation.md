# 랜덤 생성 (Random Generation)

## 개요
로그라이크 게임의 핵심은 "매 런이 다르게 느껴지는 것". 이를 위해 가중치 랜덤, 드롭 테이블, 씨드 기반 생성 세 가지 기법이 필수다. OnionCat에서는 방 배치, 적 스폰, 업그레이드 선택지, 아이템 드롭 전반에 사용된다.

---

## Unity 구현 방법

### 1. 가중치 랜덤 (Weighted Random)
특정 항목이 더 자주 나오도록 확률에 가중치를 부여하는 방식.

```csharp
[System.Serializable]
public class WeightedItem<T>
{
    public T item;
    public float weight;
}

public static T PickWeighted<T>(List<WeightedItem<T>> items)
{
    float totalWeight = 0f;
    foreach (var w in items) totalWeight += w.weight;

    float roll = Random.Range(0f, totalWeight);
    float cumulative = 0f;
    foreach (var w in items)
    {
        cumulative += w.weight;
        if (roll <= cumulative) return w.item;
    }
    return items[items.Count - 1].item;
}
```

**사용 예**:
```csharp
var enemyPool = new List<WeightedItem<GameObject>>
{
    new() { item = normalEnemyPrefab, weight = 60f },
    new() { item = rangedEnemyPrefab, weight = 30f },
    new() { item = eliteEnemyPrefab,  weight = 10f }
};
GameObject spawned = WeightedRandomPicker.Pick(enemyPool);
```

**런 진행에 따른 가중치 동적 조정**:
```csharp
// 방이 깊어질수록 Elite 비중 증가
eliteItem.weight = 10f + (currentRoomIndex * 2f);
```

---

### 2. 드롭 테이블 (Drop Table)
적 처치 시 아이템 드롭을 관리하는 구조. ScriptableObject로 만들면 디자이너가 Unity Inspector에서 편집 가능.

```csharp
[CreateAssetMenu(menuName = "OnionCat/DropTable")]
public class DropTable : ScriptableObject
{
    [System.Serializable]
    public class DropEntry
    {
        public GameObject itemPrefab;
        [Range(0f, 100f)] public float dropChance;
        public int minCount = 1;
        public int maxCount = 1;
    }

    public List<DropEntry> entries;

    public List<GameObject> Roll()
    {
        var results = new List<GameObject>();
        foreach (var entry in entries)
        {
            if (Random.Range(0f, 100f) < entry.dropChance)
            {
                int count = Random.Range(entry.minCount, entry.maxCount + 1);
                for (int i = 0; i < count; i++)
                    results.Add(entry.itemPrefab);
            }
        }
        return results;
    }
}
```

**적 컴포넌트에서 사용**:
```csharp
public class Enemy : MonoBehaviour
{
    [SerializeField] private DropTable dropTable;

    void Die()
    {
        var drops = dropTable.Roll();
        foreach (var prefab in drops)
            Instantiate(prefab, transform.position, Quaternion.identity);
        Destroy(gameObject);
    }
}
```

---

### 3. 씨드 기반 생성 (Seed-based Generation)
같은 씨드를 쓰면 항상 동일한 결과가 나옴. 디버깅, 데일리 런, 스피드런 검증에 필수.

```csharp
public class RunSeedManager : MonoBehaviour
{
    public static int CurrentSeed { get; private set; }

    public static void InitNewRun(int seed = -1)
    {
        CurrentSeed = (seed == -1) ? System.Environment.TickCount : seed;
        Random.InitState(CurrentSeed);
        Debug.Log($"[Run] Seed: {CurrentSeed}");
    }
}
```

**주의**: Unity의 `Random.InitState()`는 전역 상태를 바꾼다. 여러 시스템이 독립적으로 랜덤을 써야 한다면 `System.Random` 인스턴스를 각자 가져야 함:

```csharp
public class RoomGenerator
{
    private System.Random rng;

    public RoomGenerator(int seed)
    {
        rng = new System.Random(seed);
    }

    public int NextInt(int min, int max) => rng.Next(min, max);
    public double NextDouble() => rng.NextDouble();
}
```

---

### 4. 업그레이드 선택지 (Upgrade Picker) — 로그라이크 핵심
런 도중 업그레이드 3개 중 1개를 고르는 시스템. 중복 방지 + 희귀도 가중치 포함:

```csharp
public class UpgradePool : MonoBehaviour
{
    [SerializeField] private List<WeightedItem<UpgradeData>> allUpgrades;
    private HashSet<UpgradeData> offeredThisRun = new();

    public List<UpgradeData> GetChoices(int count = 3)
    {
        var available = allUpgrades
            .Where(u => !offeredThisRun.Contains(u.item))
            .ToList();

        var choices = new List<UpgradeData>();
        for (int i = 0; i < count && available.Count > 0; i++)
        {
            var picked = WeightedRandomPicker.Pick(available);
            choices.Add(picked.item);
            available.Remove(available.First(u => u.item == picked.item));
            offeredThisRun.Add(picked.item);
        }
        return choices;
    }
}
```

---

### 5. 가중치 시각화 팁 (Inspector에서 확인)
```csharp
#if UNITY_EDITOR
[CustomEditor(typeof(DropTable))]
public class DropTableEditor : Editor
{
    public override void OnInspectorGUI()
    {
        base.OnInspectorGUI();
        var dt = (DropTable)target;
        float total = dt.entries.Sum(e => e.dropChance);
        EditorGUILayout.HelpBox($"총 드롭 기대치: {total:F1}%", MessageType.Info);
    }
}
#endif
```

---

## OnionCat 적용 포인트

### 적 스폰 가중치
- **고양이 전용 약점 적**: 초반 가중치 높음, 중반 이후 줄어듦
- **양파 전용 약점 적**: 중반부터 등장 비중 증가
- **양쪽 모두 필요한 적**: 보스 직전 방에서 비중 증가
- 방 번호(`currentRoomIndex`)로 동적 가중치 조정

### 업그레이드 선택지
- 고양이 전용 / 양파 전용 / 공통 세 카테고리 각각 드롭 테이블 분리
- 균형: 매 선택지에서 최소 1개는 두 플레이어 모두에게 유리한 공통 업그레이드 보장
  ```
  고양이 업그레이드: weight 35
  양파 업그레이드:   weight 35
  공통 업그레이드:   weight 30
  ```

### 씨드 기반 데일리 런 (미래 기능)
- 날짜를 씨드로 사용 → 하루 동안 전 세계 플레이어가 동일한 런 경험
  ```csharp
  int dailySeed = System.DateTime.Today.GetHashCode();
  RunSeedManager.InitNewRun(dailySeed);
  ```

### 아이템 드롭 테이블
- 적 종류별 ScriptableObject DropTable 분리 (근접형 적, 원거리형 적, 엘리트 적)
- 방어막 파괴 아이템은 양파 약점 적에서만 드롭 (전략적 유도)

---

## 참고 링크
- Unity 공식 Random 문서: https://docs.unity3d.com/ScriptReference/Random.html
- System.Random vs UnityEngine.Random: https://docs.microsoft.com/en-us/dotnet/api/system.random
- Game Dev Beginner — Weighted Random: https://gamedevbeginner.com/random-in-unity/
- GDC — "Diablo: A Classic Game Postmortem" (드롭 테이블 설계 원조): https://www.gdcvault.com/play/1021580
- Catlike Coding — Procedural Generation: https://catlikecoding.com/unity/tutorials/procedural-meshes/
