# Encounter Budget System (방별 적 배치 예산 시스템)

리서치 날짜: 2026-09-22

## 개요

"Encounter Budget"는 각 전투 룸에 등장할 적의 조합과 수를 수치화된 예산(포인트)으로 제어하는 설계 기법이다.
OnionCat에서 룸마다 "쉽다/어렵다" 체감을 일관되게 만들고, 플로어가 깊어질수록 자연스럽게 난이도를 높이기 위해 필수적이다.

---

## 핵심 개념

### 1. 적 포인트 비용 할당
각 적 타입에 "위협도 포인트"를 부여:

| 적 타입 | 포인트 | 비고 |
|--------|--------|------|
| 슬라임 (약) | 1 | 기본 적 |
| 아처 슬라임 | 2 | 원거리, 이동 느림 |
| 스피드 슬라임 | 2 | 근접, 빠름 |
| 쉴드 적 | 3 | 방어력 높음 |
| 엘리트 적 | 5 | 특수 패턴 보유 |
| 미니보스 | 8 | 룸 1개당 1마리 |

### 2. 룸 예산 (Floor Budget)
플로어(층) 깊이에 따라 예산 증가:

```csharp
int GetRoomBudget(int floorDepth, int roomIndex) {
    int baseBudget = 6 + (floorDepth * 3);      // 1층=6, 2층=9, 3층=12
    int roomBonus  = roomIndex * 1;              // 같은 층 내 후반 룸 조금 더 어렵게
    return baseBudget + roomBonus;
}
```

### 3. 적 풀 (EnemyPool) ScriptableObject

```csharp
[CreateAssetMenu(menuName = "OnionCat/EncounterPool")]
public class EncounterPool : ScriptableObject {
    [System.Serializable]
    public struct Entry {
        public GameObject prefab;
        public int cost;           // 위협도 포인트
        public int minFloor;       // 이 적이 등장하기 시작하는 층
        [Range(0, 100)]
        public int weight;         // 랜덤 가중치
    }
    public List<Entry> entries;
}
```

---

## Unity 구현 방법

### Step 1: ScriptableObject로 적 데이터 정의

```csharp
// EncounterPool.cs (위 참고)
// Inspector에서 각 적의 cost, minFloor, weight 설정
```

### Step 2: 예산 소비 스폰 로직

```csharp
public class RoomEncounterSpawner : MonoBehaviour {
    [SerializeField] private EncounterPool pool;
    [SerializeField] private Transform[] spawnPoints;

    public void SpawnEncounter(int budget, int currentFloor) {
        var available = pool.entries
            .Where(e => e.minFloor <= currentFloor)
            .ToList();

        int remaining = budget;
        var selected = new List<EncounterPool.Entry>();

        // 예산 소진될 때까지 가중치 랜덤으로 적 선택
        int safety = 0;
        while (remaining > 0 && safety++ < 50) {
            var affordable = available.Where(e => e.cost <= remaining).ToList();
            if (affordable.Count == 0) break;

            var pick = WeightedRandom(affordable);
            selected.Add(pick);
            remaining -= pick.cost;
        }

        // 스폰
        for (int i = 0; i < selected.Count; i++) {
            var pt = spawnPoints[i % spawnPoints.Length];
            PoolManager.Spawn(selected[i].prefab, pt.position, Quaternion.identity);
        }
    }

    private EncounterPool.Entry WeightedRandom(List<EncounterPool.Entry> pool) {
        int total = pool.Sum(e => e.weight);
        int roll = Random.Range(0, total);
        int acc = 0;
        foreach (var e in pool) {
            acc += e.weight;
            if (roll < acc) return e;
        }
        return pool[^1];
    }
}
```

### Step 3: 예산 호출 (RoomManager에서)

```csharp
// RoomManager.cs
void OnRoomEntered(int floorDepth, int roomIndex) {
    int budget = GetRoomBudget(floorDepth, roomIndex);
    spawner.SpawnEncounter(budget, floorDepth);
}
```

### Step 4: 디버그 시각화

```csharp
#if UNITY_EDITOR
void OnDrawGizmosSelected() {
    // 스폰 포인트와 예산 표시
    UnityEditor.Handles.Label(transform.position,
        $"Budget: {lastBudget}");
}
#endif
```

---

## OnionCat 적용 포인트

### 약점 기반 적 구성 강제
OnionCat의 핵심은 "근접 약한 적 + 원거리 약한 적" 조합 강제. 예산 시스템 확장:

```csharp
[System.Serializable]
public struct Entry {
    // ... 기존 필드 ...
    public WeaknessType weakness;  // Melee, Ranged, Both
}

// 룸 생성 시: 반드시 Melee 약점 적 1마리 이상 + Ranged 약점 적 1마리 이상 포함
bool HasMeleeWeakness = selected.Any(e => e.weakness == WeaknessType.Melee);
bool HasRangedWeakness = selected.Any(e => e.weakness == WeaknessType.Ranged);
// 두 조건 미충족 시 재롤 또는 강제 추가
```

### 룸 타입별 예산 변형
- 일반 전투룸: 표준 예산
- 엘리트룸: 예산 × 1.5, 엘리트 적 필수 1마리
- 보스룸: 예산 × 0 (보스만 등장, 별도 spawner)
- 함정룸: 예산 × 0.5, 환경 위험 요소 추가

### 런 시드와 연동
```csharp
// 시드 기반 룸마다 재현 가능한 적 배치
Random.InitState(runSeed ^ (floorDepth * 1000 + roomIndex));
spawner.SpawnEncounter(budget, floorDepth);
```

---

## 밸런싱 팁

1. **예산보다 다양성 우선**: 같은 예산이어도 1마리 강적 vs 3마리 약적의 체감이 다름 → 양쪽 다 출현하도록 weight 조정
2. **데이터로 확인**: GameManager에서 "룸 클리어 시간"을 로그로 쌓아 너무 빠른/느린 룸 감지
3. **플레이어 버프 고려**: 런 중반 업그레이드로 플레이어가 강해지므로 동일 예산의 체감이 초반과 다름. 후반 예산 증가폭을 가파르게 설정

---

## 참고 링크

- Game Balance Concepts (Ernest Adams): https://gamebalanceconcepts.wordpress.com/
- GDC "Encounter Design in Dead Cells": YouTube 검색
- Unity ScriptableObject 공식 문서: https://docs.unity3d.com/Manual/class-ScriptableObject.html
- Weighted Random Selection: https://docs.unity3d.com/ScriptReference/Random.Range.html
