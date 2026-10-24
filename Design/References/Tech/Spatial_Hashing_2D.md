# 2D 공간 해싱 (Spatial Hashing)

리서치 날짜: 2026-10-24

## 개요
탑다운 2D 게임에서 "반경 R 안의 적 목록", "가장 가까운 오브젝트" 같은 근접 쿼리를 효율적으로 수행하는 자료구조 기법. `Physics2D.OverlapCircleAll()`은 내부적으로 모든 활성 콜라이더를 검사하기 때문에 오브젝트가 많아질수록 O(n) 비용이 쌓인다. 공간 해싱은 월드를 고정 크기 격자로 나누어 **해당 셀과 인접 셀만** 검사함으로써 평균적으로 O(1)에 가까운 성능을 얻는다.

OnionCat 관련 시스템: AoE 데미지(포자 구름·박 폭발·합동기), 씨앗 자석 흡수 반경, 고양이 할퀴기 부채꼴 후보 추출, 적 군집 근접 감지.

---

## 작동 원리
1. 월드를 고정 크기 셀(예: 2×2 유닛)로 논리 분할
2. 각 셀은 현재 그 안에 있는 오브젝트 목록을 관리
3. 위치 `(x, y)` → 셀 좌표 `(floor(x/cellSize), floor(y/cellSize))`
4. 반경 R 쿼리: 반경을 포함하는 셀 범위를 열거하고 그 안의 오브젝트만 실제 거리 계산

---

## Unity 구현 방법

### SpatialHash2D 제네릭 클래스

```csharp
using System.Collections.Generic;
using UnityEngine;

public class SpatialHash2D<T> where T : Component
{
    readonly float cellSize;
    readonly Dictionary<Vector2Int, List<T>> cells = new();

    public SpatialHash2D(float cellSize) => this.cellSize = cellSize;

    Vector2Int Key(Vector2 pos) =>
        new(Mathf.FloorToInt(pos.x / cellSize),
            Mathf.FloorToInt(pos.y / cellSize));

    public void Insert(T obj, Vector2 pos)
    {
        var key = Key(pos);
        if (!cells.TryGetValue(key, out var list))
            cells[key] = list = new List<T>();
        list.Add(obj);
    }

    public void Remove(T obj, Vector2 pos)
    {
        if (cells.TryGetValue(Key(pos), out var list))
            list.Remove(obj);
    }

    // 매 프레임 Clear + 재삽입 패턴용 빠른 초기화
    public void Clear()
    {
        foreach (var list in cells.Values) list.Clear();
    }

    // 반경 내 오브젝트를 results에 추가 (할당 최소화를 위해 리스트 재사용)
    public void Query(Vector2 center, float radius, List<T> results)
    {
        int minX = Mathf.FloorToInt((center.x - radius) / cellSize);
        int maxX = Mathf.FloorToInt((center.x + radius) / cellSize);
        int minY = Mathf.FloorToInt((center.y - radius) / cellSize);
        int maxY = Mathf.FloorToInt((center.y + radius) / cellSize);

        float r2 = radius * radius;
        for (int cx = minX; cx <= maxX; cx++)
        for (int cy = minY; cy <= maxY; cy++)
        {
            if (!cells.TryGetValue(new Vector2Int(cx, cy), out var list)) continue;
            foreach (var obj in list)
            {
                if (obj == null) continue;
                Vector2 objPos = obj.transform.position;
                if ((objPos - center).sqrMagnitude <= r2)
                    results.Add(obj);
            }
        }
    }
}
```

### 사용 예 — EnemyManager에서 관리

```csharp
public class EnemyManager : MonoBehaviour
{
    static readonly SpatialHash2D<EnemyBase> hash = new(cellSize: 3f);
    static readonly List<EnemyBase> queryBuffer = new();

    void LateUpdate()
    {
        // 매 프레임 재구성 (이동이 잦으면 이 방식이 가장 단순)
        hash.Clear();
        foreach (var e in EnemyBase.Active)
            if (e != null) hash.Insert(e, e.transform.position);
    }

    // AoE 데미지: Physics2D.OverlapCircle 대신
    public static void DamageInRadius(Vector2 center, float radius,
                                       int damage, Attacker attacker)
    {
        queryBuffer.Clear();
        hash.Query(center, radius, queryBuffer);
        foreach (var e in queryBuffer)
            e.TakeDamage(damage, attacker);
    }
}
```

### 고양이 할퀴기 부채꼴 히트박스 예

```csharp
// 기존 Physics2D.OverlapCircle → 공간 해싱으로 후보 추출 후 각도 필터
void DetectSlashHits(Vector2 origin, Vector2 dir, float radius, float halfAngle)
{
    queryBuffer.Clear();
    EnemyManager.QueryEnemies(origin, radius, queryBuffer);

    foreach (var e in queryBuffer)
    {
        Vector2 toEnemy = (Vector2)e.transform.position - origin;
        float angle = Vector2.Angle(dir, toEnemy);
        if (angle <= halfAngle)
            e.TakeDamage(slashDamage, Attacker.Cat);
    }
}
```

---

## 성능 고려 사항

| 요소 | 권장 값 | 이유 |
|------|---------|------|
| 셀 크기 | 쿼리 반경의 1~2배 | 너무 작으면 셀 수↑, 너무 크면 후보 수↑ |
| 갱신 방식 | 매 프레임 Clear + 재삽입 | 단순, GC 없음 (List 내용만 지움) |
| Clear 방식 | `foreach cells.Values → list.Clear()` | Dictionary 자체는 유지하여 재할당 없음 |
| 오브젝트 수 | < 200일 때 실용적 이점 체감 | 그 이상이면 FixedUpdate 분산 갱신 고려 |

**주의**: `Vector2Int`는 struct이므로 Dictionary 키로 사용해도 GC 박싱 없음.

---

## OnionCat 적용 포인트

1. **AoE 데미지 (포자 구름·박 폭발·합동기)**: 현재 `Physics2D.OverlapCircleAll()` 대신 `EnemyManager.DamageInRadius()` 패턴으로 교체 가능. 방당 적이 20마리 이하인 지금은 체감 차이 없지만 코드 구조가 깔끔해짐.

2. **씨앗 자석 흡수**: `GearLoot` 오브젝트들도 같은 방식으로 공간 해싱에 등록하면 "고양이 밟기" 감지를 콜라이더 없이 구현 가능. Trigger 콜라이더 개수 감소 효과.

3. **할퀴기 부채꼴 탐지**: 현재 Physics2D.OverlapCircle → 각도 필터 패턴 유지. 해싱을 도입하면 반경 쿼리 단계만 대체되고 각도 필터 로직은 그대로.

4. **현실적 적용 시점**: 방당 적 수가 30마리를 넘거나, AoE가 밀집 화면에서 프레임 드롭을 일으킬 때 도입. 지금 당장보다는 Enemy Elite 방이나 소환형 적이 많아질 때 투자 대비 효과가 큼.

5. **OnionCat 아키텍처와의 호환**: `EnemyBase.Active` 정적 목록이 이미 있어 매 프레임 재삽입 루프 구현이 2~3줄. 별도 Component를 추가하거나 씬을 건드릴 필요 없음.

---

## 참고 링크
- Unity Physics2D 공식 문서: https://docs.unity3d.com/ScriptReference/Physics2D.html
- Unity 성능 최적화 가이드 (2D 물리): https://docs.unity3d.com/Manual/2D-Physics.html
- Spatial Hashing 개념 (Game Programming Gems): 격자 기반 공간 분할의 고전적 구현은 "Game Programming Gems 6" Chapter 4.4 참고
- Unity Dictionary + struct 키 성능: https://docs.unity3d.com/Manual/BestPracticeUnderstandingPerformanceInUnity.html
