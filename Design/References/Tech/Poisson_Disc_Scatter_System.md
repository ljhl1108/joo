# Poisson Disc Scatter System (2D 포아송 디스크 흩뿌리기)

리서치 날짜: 2026-11-09

## 개요

방 바닥 장식, 나뭇잎, 풀, 소품 등을 2D 공간에 "자연스럽게" 배치하는 알고리즘.
순수 `Random.insideUnitCircle`로 뿌리면 무리 짓거나 텅 빈 곳이 생기는데,
포아송 디스크는 **최소 거리 r 이상 간격을 보장**하면서도 무작위처럼 보이는 점 집합을 생성한다.

OnionCat에서는 `RoomDecor.Scatter`가 바닥 장식을 흩뿌리는데, 이 알고리즘을 쓰면
소품이 겹치거나 한쪽에 몰리는 현상 없이 균일하게 분포된다.

---

## 알고리즘 원리 (Bridson 2007)

```
입력: 셀 너비 w, 높이 h, 최소 거리 r, 최대 시도 k (보통 30)

1. 그리드 초기화: 각 셀 크기 = r / √2 (한 셀에 점 최대 1개 보장)
2. 첫 번째 점 p0 무작위 배치 → active list, result list에 추가
3. active list가 빌 때까지:
   a. active list에서 임의 점 p 선택
   b. k회 시도:
      p 주변 [r, 2r] 환형 영역에서 임의 후보 점 q 생성
      q가 그리드 내 이웃들과 r 이상 떨어지면:
        result list 추가, active list 추가, 그리드 기록
   c. k회 모두 실패하면 p를 active list에서 제거
4. result list 반환
```

**시간 복잡도**: O(n) — 순수 랜덤 거부 샘플링보다 훨씬 빠름

---

## Unity C# 구현

```csharp
using System.Collections.Generic;
using UnityEngine;

public static class PoissonDisc
{
    // 반환값: 로컬 좌표 Vector2 목록 (원점 = 왼쪽 아래)
    public static List<Vector2> Sample(float width, float height, float minDist,
                                        int maxAttempts = 30, int seed = 0)
    {
        var rng = new System.Random(seed);
        float cellSize = minDist / Mathf.Sqrt(2f);
        int cols = Mathf.CeilToInt(width  / cellSize);
        int rows = Mathf.CeilToInt(height / cellSize);

        var grid    = new int[cols, rows];           // -1 = 비어 있음, 나머지 = 점 인덱스
        var points  = new List<Vector2>();
        var active  = new List<int>();

        for (int i = 0; i < cols; i++)
            for (int j = 0; j < rows; j++)
                grid[i, j] = -1;

        // 첫 점
        Vector2 p0 = new Vector2((float)(rng.NextDouble() * width),
                                  (float)(rng.NextDouble() * height));
        AddPoint(p0);

        while (active.Count > 0)
        {
            int idx = rng.Next(active.Count);
            Vector2 p = points[active[idx]];
            bool found = false;

            for (int attempt = 0; attempt < maxAttempts; attempt++)
            {
                float angle = (float)(rng.NextDouble() * Mathf.PI * 2f);
                float dist  = minDist * (1f + (float)rng.NextDouble());
                Vector2 q   = p + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * dist;

                if (q.x < 0 || q.x >= width || q.y < 0 || q.y >= height) continue;
                if (TooClose(q)) continue;

                AddPoint(q);
                found = true;
                break;
            }

            if (!found) active.RemoveAt(idx);
        }

        return points;

        // ---- 로컬 함수 ----
        void AddPoint(Vector2 pt)
        {
            int gx = Mathf.FloorToInt(pt.x / cellSize);
            int gy = Mathf.FloorToInt(pt.y / cellSize);
            grid[gx, gy] = points.Count;
            active.Add(points.Count);
            points.Add(pt);
        }

        bool TooClose(Vector2 pt)
        {
            int gx = Mathf.FloorToInt(pt.x / cellSize);
            int gy = Mathf.FloorToInt(pt.y / cellSize);
            int r2 = 2;
            for (int dx = -r2; dx <= r2; dx++)
            for (int dy = -r2; dy <= r2; dy++)
            {
                int nx = gx + dx, ny = gy + dy;
                if (nx < 0 || nx >= cols || ny < 0 || ny >= rows) continue;
                int pidx = grid[nx, ny];
                if (pidx < 0) continue;
                if ((points[pidx] - pt).sqrMagnitude < minDist * minDist) return true;
            }
            return false;
        }
    }
}
```

### 사용 예

```csharp
// RoomDecor.Scatter 적용 예시
void ScatterDecorations(Bounds roomBounds, float minSpacing = 1.5f)
{
    var pts = PoissonDisc.Sample(
        roomBounds.size.x, roomBounds.size.y,
        minDist: minSpacing,
        seed: GameManager.Instance.Run.Seed);

    foreach (var local in pts)
    {
        Vector2 world = (Vector2)roomBounds.min + local;
        // 벽/충돌체 위인지 추가 체크
        if (Physics2D.OverlapCircle(world, 0.3f, wallLayer)) continue;
        var go = PoolManager.Spawn(decorPrefab, world, Quaternion.identity);
    }
}
```

---

## 순수 Random과 비교

| 방법 | 균일성 | 최소 간격 보장 | 속도 |
|------|--------|--------------|------|
| `Random.insideUnitCircle` | 나쁨 (무리짐) | ✗ | 빠름 |
| 거부 샘플링 (naive) | 보통 | ✓ | 느림 (밀도 높아질수록) |
| **포아송 디스크 (Bridson)** | **좋음** | **✓** | **O(n), 빠름** |
| Jittered Grid | 보통 | 부분적 | 빠름 |

---

## OnionCat 적용 포인트

### 1. `RoomDecor.Scatter` 개선

현재 구현이 단순 Random이라면 포아송 디스크로 교체:
- `minDist`를 소품 종류마다 다르게 (큰 바위 2.0, 작은 꽃 0.8)
- `Run.Seed`를 사용해서 같은 씨드 = 같은 방 장식 → 중간 저장 후 재개 시 동일하게 복원

### 2. 충돌체 회피 필터링

포아송 샘플링 후 각 점에 `Physics2D.OverlapCircle` 한 번만 체크:
- Wall 레이어·Props 레이어와 겹치는 점 제외
- 출구 근처 (DoorTile 위) 제외

### 3. 적 스폰 위치 분산

`EnemyRoster.ResolveRoom`에서 적 스폰 위치도 포아송 디스크로 분산 가능:
- 적들이 처음부터 뭉쳐 있으면 범위 공격 1번에 전멸 → 최소 간격 2.5 유닛 보장

### 4. 씨앗 드롭 연출

적 처치 후 씨앗 아이템이 사방으로 튀어나올 때 포아송 디스크 사전 계산으로
자연스러운 패턴 생성 (완전 랜덤보다 겹침 없이 모아 놓는 느낌)

### 5. 성능 주의

- 방 1개 기준 (약 15×10유닛) `minDist=0.8`로 약 150~200개 점 생성
- 방 진입 시 1회만 계산 (`Awake` 또는 `Room.ResetForReuse`)
- GC 최소화: `List<Vector2>` 재사용 또는 `stackalloc` 고려

---

## 변형: 가중치 포아송 (Weighted Poisson)

맵 위치마다 `minDist`를 다르게 주면 중앙은 빽빽하고 가장자리는 성기게:

```csharp
float DistAt(Vector2 pt, Vector2 center)
{
    float t = (pt - center).magnitude / maxRadius;
    return Mathf.Lerp(minDistCenter, minDistEdge, t);
}
```

이를 응용하면 보스 방 중앙은 소품 없이 비어 있고, 가장자리로만 장식이 모이는 효과.

---

## 참고 링크

- Bridson, R. (2007). "Fast Poisson Disk Sampling in Arbitrary Dimensions" — SIGGRAPH Sketches
  https://www.cs.ubc.ca/~rbridson/docs/bridson-siggraph07-poissondisk.pdf
- Sebastian Lague Unity 구현 튜토리얼: https://www.youtube.com/watch?v=7WcmyxyFO7o
- Red Blob Games 시각화: https://www.redblobgames.com/x/2022-poisson-disk-samples/
- Unity 공식 Random 문서: https://docs.unity3d.com/ScriptReference/Random.html
