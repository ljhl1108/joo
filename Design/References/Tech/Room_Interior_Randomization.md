# 방 내부 콘텐츠 랜덤 배치 시스템

리서치 날짜: 2026-09-01

## 개요

절차적 던전 생성(방 연결 레이아웃)과는 별개로, 이미 만들어진 방 프리팹 안에서
"무엇이 등장할지"를 런타임에 랜덤으로 결정하는 시스템.

로그라이크의 "매 런 다른 경험"은 방의 연결 구조뿐 아니라 방 내부 콘텐츠도
랜덤이어야 완성된다. 방마다 스폰 포인트를 미리 배치해두고,
런타임에 가중치 랜덤으로 적·아이템·트랩을 배정한다.

OnionCat에서는 방 프리팹 내에 `RoomContentPoint`를 배치해두고,
층 번호와 방 유형에 따라 적 구성을 달리 스폰한다.

---

## Unity 구현 방법

### 1. 스폰 포인트 컴포넌트

방 프리팹 안에 빈 GameObject를 배치하고 컴포넌트로 역할 정의.

```csharp
// RoomContentPoint.cs
public class RoomContentPoint : MonoBehaviour
{
    public enum PointType { Enemy, Item, Trap }

    [SerializeField] private PointType type;
    [SerializeField] [Range(0f, 1f)] private float spawnChance = 1f;

    public PointType Type => type;
    public float SpawnChance => spawnChance;
}
```

유니티 에디터에서 드래그 앤 드롭 설정 필요:
- 방 프리팹에 빈 GameObject 추가 → `RoomContentPoint` 컴포넌트 부착
- Type: Enemy / Item / Trap 중 선택
- SpawnChance: 0~1 (1.0 = 항상 스폰, 0.5 = 50% 확률)

---

### 2. 방 콘텐츠 테이블 (ScriptableObject)

층별·방 유형별로 독립 테이블을 만들어 에디터에서 설정.

```csharp
// RoomContentTable.cs
[CreateAssetMenu(menuName = "OnionCat/RoomContentTable")]
public class RoomContentTable : ScriptableObject
{
    [System.Serializable]
    public struct WeightedEntry
    {
        public GameObject prefab;
        public int weight;  // 가중치 (클수록 자주 등장)
    }

    [Header("적 풀")]
    public WeightedEntry[] enemyPool;
    public int minEnemies = 2;
    public int maxEnemies = 5;

    [Header("아이템 풀")]
    public WeightedEntry[] itemPool;
    [Range(0f, 1f)] public float itemRoomChance = 0.3f;

    [Header("트랩 풀")]
    public WeightedEntry[] trapPool;
    public int maxTraps = 2;
}
```

유니티 에디터에서 드래그 앤 드롭 설정 필요:
- Assets 우클릭 → Create → OnionCat → RoomContentTable
- enemyPool에 적 프리팹 드래그 + 가중치 수치 입력

---

### 3. 방 입장 시 콘텐츠 배치

```csharp
// RoomContentSpawner.cs
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public class RoomContentSpawner : MonoBehaviour
{
    [SerializeField] private RoomContentTable contentTable;
    private RoomContentPoint[] points;

    void Awake()
    {
        points = GetComponentsInChildren<RoomContentPoint>();
    }

    public void SpawnContents(int floorLevel)
    {
        SpawnEnemies(floorLevel);
        SpawnItems();
        SpawnTraps();
    }

    private void SpawnEnemies(int floorLevel)
    {
        var enemyPoints = points
            .Where(p => p.Type == RoomContentPoint.PointType.Enemy)
            .ToList();
        Shuffle(enemyPoints);

        int count = Mathf.Min(
            Random.Range(contentTable.minEnemies, contentTable.maxEnemies + floorLevel),
            enemyPoints.Count);

        for (int i = 0; i < count; i++)
        {
            if (Random.value > enemyPoints[i].SpawnChance) continue;
            var prefab = GetWeightedRandom(contentTable.enemyPool);
            if (prefab != null)
                Instantiate(prefab, enemyPoints[i].transform.position, Quaternion.identity);
        }
    }

    private void SpawnItems()
    {
        if (Random.value > contentTable.itemRoomChance) return;

        var itemPoints = points
            .Where(p => p.Type == RoomContentPoint.PointType.Item)
            .ToList();
        if (itemPoints.Count == 0) return;

        int idx = Random.Range(0, itemPoints.Count);
        var prefab = GetWeightedRandom(contentTable.itemPool);
        if (prefab != null)
            Instantiate(prefab, itemPoints[idx].transform.position, Quaternion.identity);
    }

    private void SpawnTraps()
    {
        var trapPoints = points
            .Where(p => p.Type == RoomContentPoint.PointType.Trap)
            .ToList();
        Shuffle(trapPoints);

        int count = Mathf.Min(contentTable.maxTraps, trapPoints.Count);
        for (int i = 0; i < count; i++)
        {
            if (Random.value > trapPoints[i].SpawnChance) continue;
            var prefab = GetWeightedRandom(contentTable.trapPool);
            if (prefab != null)
                Instantiate(prefab, trapPoints[i].transform.position, Quaternion.identity);
        }
    }

    private GameObject GetWeightedRandom(RoomContentTable.WeightedEntry[] pool)
    {
        if (pool == null || pool.Length == 0) return null;
        int total = pool.Sum(e => e.weight);
        if (total <= 0) return pool[0].prefab;

        int roll = Random.Range(0, total);
        foreach (var entry in pool)
        {
            roll -= entry.weight;
            if (roll < 0) return entry.prefab;
        }
        return pool[0].prefab;
    }

    private void Shuffle<T>(List<T> list)
    {
        for (int i = list.Count - 1; i > 0; i--)
        {
            int j = Random.Range(0, i + 1);
            (list[i], list[j]) = (list[j], list[i]);
        }
    }
}
```

---

### 4. 층별 난이도 스케일링

`RoomController`에서 현재 층 번호를 `SpawnContents(floorLevel)`에 전달.

```csharp
// RoomController.cs (발췌)
[SerializeField] private RoomContentTable[] floorTables;  // 층별 테이블 배열

public void OnRoomEntered(int currentFloor)
{
    int tableIndex = Mathf.Min(currentFloor - 1, floorTables.Length - 1);
    spawner.contentTable = floorTables[tableIndex];
    spawner.SpawnContents(currentFloor);
}
```

---

### 5. 방 유형별 테이블 분리

| 방 유형 | ScriptableObject 예시 |
|---------|----------------------|
| 일반 전투 방 | `Floor1_Normal.asset` |
| 보스 전 방 | `PreBoss.asset` — 엘리트 적 필수, 트랩 없음 |
| 상점 방 | `Shop.asset` — 적 없음, 아이템만 |
| 도전 방 | `Challenge.asset` — 적 많음, 보상 높음 |

---

## OnionCat 적용 포인트

- **취약점 혼합 보장**: `enemyPool`에 근접 취약 적·원거리 취약 적을 모두 포함시키고,
  `minEnemies` 설정으로 양쪽이 최소 1마리씩 스폰되도록 설계
  → P1·P2 역할 분담이 모든 방에서 자연 발생
- **공간 구역 분리**: 스폰 포인트를 방의 좌/우 구역으로 분류
  (좌측 = 근접 전용 적 포인트, 우측 = 원거리 전용 적 포인트)
  → 두 플레이어가 화면을 물리적으로 분담
- **보스 전 방 긴장감**: `floorLevel >= BOSS_THRESHOLD` 조건일 때
  엘리트 적 1마리를 강제 추가 (`Enemy_Elite_Variant_System.md` 연계)
- **ScriptableObject 분리로 밸런싱 편의성**: 코드 수정 없이 에디터에서
  적 가중치 수치만 조정 → 빠른 밸런스 이터레이션 가능

---

## 참고 링크

- Unity Random API: https://docs.unity3d.com/ScriptReference/Random.html
- ScriptableObject 가이드: https://unity.com/how-to/scriptableobjects
- Brackeys — Level Generation Tutorial: https://www.youtube.com/watch?v=ItJEuFt5WGw
- 연관 파일: `Room_System.md`, `Random_Generation.md`, `Weighted_Encounter_Drop_Balancing.md`
