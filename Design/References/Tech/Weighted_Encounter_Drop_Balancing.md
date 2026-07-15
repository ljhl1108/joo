# 가중치 기반 인카운터 & 드롭 밸런싱 시스템

리서치 날짜: 2026-07-15

## 개요

로그라이크 게임에서 "매 런이 다르게 느껴지는" 핵심 메카닉은 **가중치 랜덤(Weighted Random)**이다.  
단순 `Random.Range(0, n)` 대신 각 항목에 가중치를 부여해 확률을 설계자가 조율할 수 있게 한다.

OnionCat에 직접 필요한 곳:
- **룸 인카운터**: 어떤 적 구성이 이 방에 등장할지
- **드롭 아이템/업그레이드**: 방 클리어 후 어떤 업그레이드 선택지가 뜰지
- **상점 재고**: 상점에 어떤 아이템이 진열될지

---

## Unity 구현 방법

### 1. 기본 가중치 선택 유틸리티

```csharp
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

[System.Serializable]
public class WeightedEntry<T>
{
    public T value;
    [Min(0f)] public float weight;
}

public static class WeightedRandom
{
    public static T Pick<T>(IList<WeightedEntry<T>> entries)
    {
        float total = entries.Sum(e => e.weight);
        if (total <= 0f) return entries[0].value;

        float roll = Random.Range(0f, total);
        float cumulative = 0f;
        foreach (var entry in entries)
        {
            cumulative += entry.weight;
            if (roll <= cumulative) return entry.value;
        }
        return entries[entries.Count - 1].value;
    }

    // 중복 없이 N개 뽑기
    public static List<T> PickMultiple<T>(IList<WeightedEntry<T>> entries, int count)
    {
        var pool = new List<WeightedEntry<T>>(entries);
        var result = new List<T>();
        for (int i = 0; i < count && pool.Count > 0; i++)
        {
            var picked = Pick(pool);
            result.Add(picked);
            pool.RemoveAll(e => EqualityComparer<T>.Default.Equals(e.value, picked));
        }
        return result;
    }
}
```

### 2. 적 구성 — 위협 예산(Threat Budget) 방식

```csharp
[CreateAssetMenu(menuName = "OnionCat/EnemyGroup")]
public class EnemyGroupSO : ScriptableObject
{
    public List<WeightedEntry<EnemyData>> enemyPool;
    public int threatBudget;        // 이 방의 총 위협 포인트
    public int minFloor;            // 몇 층부터 등장 가능
}

// EnemyData ScriptableObject
[CreateAssetMenu(menuName = "OnionCat/EnemyData")]
public class EnemyData : ScriptableObject
{
    public GameObject prefab;
    public int threatCost;          // 소환 시 소비되는 위협 포인트
    public WeaknessType weakness;   // Melee / Ranged / None
}

// 룸 생성 시 적 배치
public class RoomSpawner : MonoBehaviour
{
    [SerializeField] private List<WeightedEntry<EnemyGroupSO>> groupPool;
    [SerializeField] private Transform[] spawnPoints;

    public void PopulateRoom(int currentFloor)
    {
        // 현재 층에서 등장 가능한 그룹만 필터
        var available = groupPool
            .Where(e => e.value.minFloor <= currentFloor)
            .ToList();

        var group = WeightedRandom.Pick(available);
        int budget = group.threatBudget + currentFloor * 2;  // 층마다 예산 증가

        while (budget > 0)
        {
            // 예산 이내의 적만 선택 가능
            var affordable = group.enemyPool
                .Where(e => e.value.threatCost <= budget)
                .ToList();
            if (affordable.Count == 0) break;

            var enemy = WeightedRandom.Pick(affordable);
            SpawnEnemy(enemy);
            budget -= enemy.threatCost;
        }
    }

    private void SpawnEnemy(EnemyData data)
    {
        var point = spawnPoints[Random.Range(0, spawnPoints.Length)];
        Instantiate(data.prefab, point.position, Quaternion.identity);
    }
}
```

### 3. 드롭 시스템 — 희귀도 티어 + 층 보정

```csharp
public enum Rarity { Common, Uncommon, Rare, Legendary }

[CreateAssetMenu(menuName = "OnionCat/UpgradeData")]
public class UpgradeData : ScriptableObject
{
    public string upgradeName;
    public Rarity rarity;
    public bool targetCat;      // Cat 전용 업그레이드
    public bool targetCrop;     // Crop 전용 업그레이드
}

public class DropManager : MonoBehaviour
{
    [SerializeField] private List<UpgradeData> allUpgrades;

    // 층 깊이에 따라 희귀도 가중치 반환
    private Dictionary<Rarity, float> GetRarityWeights(int floor)
    {
        return new Dictionary<Rarity, float>
        {
            { Rarity.Common,     Mathf.Max(0f, 60f - floor * 5f) },
            { Rarity.Uncommon,   Mathf.Min(30f, 20f + floor * 2f) },
            { Rarity.Rare,       Mathf.Min(15f, 5f + floor * 1.5f) },
            { Rarity.Legendary,  floor >= 5 ? 5f : 0f }
        };
    }

    public List<UpgradeData> GetUpgradeOptions(int floor, List<UpgradeData> owned, int count = 3)
    {
        var weights = GetRarityWeights(floor);

        // 이미 보유한 업그레이드 제외
        var pool = allUpgrades
            .Where(u => !owned.Contains(u))
            .Select(u => new WeightedEntry<UpgradeData>
            {
                value = u,
                weight = weights[u.rarity]
            })
            .ToList();

        return WeightedRandom.PickMultiple(pool, count);
    }
}
```

### 4. ScriptableObject 에디터 설정

Inspector에서 가중치를 시각적으로 조율하려면:
```csharp
// 각 WeightedEntry의 weight 총합 대비 퍼센트를 에디터에서 볼 수 있도록
// Custom Editor 또는 [PropertyDrawer] 적용 권장
// 또는 Odin Inspector 사용 시 [TableList] 어트리뷰트로 표 형태로 편집 가능
```

---

## OnionCat 적용 포인트

### 근접/원거리 취약 적 비율 관리

OnionCat의 핵심 협동 강제 메카닉은 "어떤 적은 근접으로만, 어떤 적은 원거리로만 처치 가능".  
가중치 시스템으로 이 비율을 층별로 조정:

```
1층: 근접 취약 60% / 원거리 취약 30% / 양쪽 가능 10%
3층: 근접 취약 40% / 원거리 취약 40% / 양쪽 가능 20%
5층(최종): 근접 30% / 원거리 30% / 혼합 요구 40%
```

### 실용 팁

1. **층 0에서 Legendary 확률 = 0**: 극초반 강력 아이템으로 인한 게임 붕괴 방지
2. **업그레이드 카테고리 분리**: Cat 업그레이드와 Crop 업그레이드가 동시에 등장하도록 보장
   - 3지선다 중 Cat 1개 보장 + Crop 1개 보장 + 랜덤 1개
3. **시드(Seed) 기반 결정**: `Random.InitState(seed)` 후 WeightedRandom 사용 → 재현 가능한 런
4. **가중치 밸런스 테스트**: PlayTest 시 드롭 로그를 파일로 저장해 분포 확인

---

## 참고 링크

- [Unity Docs - Random.Range](https://docs.unity3d.com/ScriptReference/Random.Range.html)
- [Game Dev Underground - Weighted Random in Unity (YouTube)](https://www.youtube.com/watch?v=VRMhtR05L4Q)
- [Catlike Coding - Pseudorandom Noise](https://catlikecoding.com/unity/tutorials/pseudorandom-noise/)
- [Roguelike Dev - Drop Table Design (Reddit r/roguelikedev)](https://www.reddit.com/r/roguelikedev/wiki/faq_general)
- [GDC - 'Enter the Gungeon' Design Postmortem (YouTube)](https://www.youtube.com/watch?v=pMSBuSBPNfQ)
