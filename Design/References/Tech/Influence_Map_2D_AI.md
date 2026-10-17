# Influence Map 2D Enemy AI

리서치 날짜: 2026-10-17

## 개요

**영향 맵(Influence Map)**은 게임 세계를 격자(grid)로 나누고, 각 격자 셀에 "위험도", "지배력", "이동 선호도" 같은 값을 기록하는 공간 AI 기법이다. 적이 단순히 플레이어를 직선으로 추적하는 대신, 공간 전체의 상황을 반영해 **어디에 서 있을지, 어느 방향으로 공격할지**를 결정할 수 있게 한다.

OnionCat에서 왜 중요한가:
- 여러 적이 플레이어 주변에 뭉치지 않고 **포위 형태**를 잡도록 유도
- 걷어차기·장판·투사체가 쌓인 위험 구역을 적이 **인식하고 피하는** 행동
- 적끼리 겹치지 않는 **자연스러운 군집 행동**을 단순한 코드로 구현

---

## 핵심 개념

### 영향 맵의 구조

```
게임 월드를 N×M 격자로 분할 (예: 각 셀 = 1 유닛 = 32px)

각 셀이 가지는 값 종류:
- 플레이어 영향(PlayerInfluence): 플레이어에 가까울수록 높음
- 위험도(Danger):  장판·투사체·폭발 예정 지점일수록 높음
- 적 점유도(EnemyPresence): 이미 적이 있는 셀은 높음
- 이동 선호도(Preference): 위 값들을 조합해 "이 셀로 이동하고 싶음" 수치
```

### 업데이트 흐름

```
매 FixedUpdate마다 (또는 일정 간격):
1. 모든 셀의 기여 값을 0으로 리셋 (또는 감쇠)
2. 플레이어 위치에서 거리별 감쇠로 PlayerInfluence 전파
3. 장판·예정 폭발 위치에 Danger 값 추가
4. 각 적의 현재 위치 셀에 EnemyPresence 추가
5. Preference = PlayerInfluence - Danger - EnemyPresence
6. 각 적은 자신 주변 셀 중 Preference가 높은 셀로 이동
```

---

## Unity 구현 방법

### Step 1: 그리드 데이터 구조

```csharp
public class InfluenceGrid : MonoBehaviour
{
    public int width = 40, height = 20;
    public float cellSize = 1f;
    
    float[,] playerInfluence;
    float[,] dangerMap;
    float[,] enemyPresence;
    
    Vector2 origin; // 방의 왼쪽 아래 기준점
    
    void Awake()
    {
        playerInfluence = new float[width, height];
        dangerMap = new float[width, height];
        enemyPresence = new float[width, height];
        origin = (Vector2)transform.position;
    }
    
    // 월드 좌표 → 셀 인덱스
    public Vector2Int WorldToCell(Vector2 worldPos)
    {
        int x = Mathf.FloorToInt((worldPos.x - origin.x) / cellSize);
        int y = Mathf.FloorToInt((worldPos.y - origin.y) / cellSize);
        return new Vector2Int(
            Mathf.Clamp(x, 0, width - 1),
            Mathf.Clamp(y, 0, height - 1)
        );
    }
    
    // 셀 인덱스 → 월드 좌표 (셀 중심)
    public Vector2 CellToWorld(Vector2Int cell)
    {
        return origin + new Vector2(
            (cell.x + 0.5f) * cellSize,
            (cell.y + 0.5f) * cellSize
        );
    }
}
```

### Step 2: 영향 전파 (Propagation)

```csharp
// InfluenceGrid.cs 안에 추가
public float playerInfluenceRadius = 8f;
public float dangerRadius = 2f;

void UpdateInfluence()
{
    // 전체 초기화
    System.Array.Clear(playerInfluence, 0, playerInfluence.Length);
    System.Array.Clear(dangerMap, 0, dangerMap.Length);
    System.Array.Clear(enemyPresence, 0, enemyPresence.Length);
    
    // 플레이어 영향 전파 (거리 기반 감쇠)
    Vector2 playerPos = GameManager.Instance.CatPlayer.transform.position;
    Vector2Int playerCell = WorldToCell(playerPos);
    
    for (int x = 0; x < width; x++)
    for (int y = 0; y < height; y++)
    {
        float dist = Vector2Int.Distance(new Vector2Int(x, y), playerCell);
        playerInfluence[x, y] = Mathf.Max(0, 1f - dist / playerInfluenceRadius);
    }
    
    // 위험 지역 (장판, 예정 폭발 등)
    foreach (var hazard in EnemyHazard.ActiveHazards)
    {
        Vector2Int hazardCell = WorldToCell(hazard.transform.position);
        for (int x = 0; x < width; x++)
        for (int y = 0; y < height; y++)
        {
            float dist = Vector2Int.Distance(new Vector2Int(x, y), hazardCell);
            dangerMap[x, y] += Mathf.Max(0, 1f - dist / dangerRadius);
        }
    }
    
    // 적 점유도
    foreach (var enemy in EnemyBase.Active)
    {
        if (enemy == null) continue;
        Vector2Int cell = WorldToCell(enemy.transform.position);
        enemyPresence[cell.x, cell.y] += 1f;
    }
}

// 외부에서 특정 셀의 이동 선호도 조회
public float GetPreference(Vector2Int cell, float aggressiveness = 1f)
{
    if (cell.x < 0 || cell.x >= width || cell.y < 0 || cell.y >= height)
        return -999f;
    
    return aggressiveness * playerInfluence[cell.x, cell.y]
         - dangerMap[cell.x, cell.y]
         - enemyPresence[cell.x, cell.y] * 0.5f;
}
```

### Step 3: 적 AI에서 활용

```csharp
// EnemyBase나 MovementModule에서 사용
Vector2 GetInfluenceBasedMoveTarget(InfluenceGrid grid)
{
    Vector2Int myCell = grid.WorldToCell(transform.position);
    
    // 주변 8방향 셀 + 현재 셀 검사
    Vector2Int bestCell = myCell;
    float bestScore = float.MinValue;
    
    for (int dx = -2; dx <= 2; dx++)
    for (int dy = -2; dy <= 2; dy++)
    {
        Vector2Int candidate = myCell + new Vector2Int(dx, dy);
        float score = grid.GetPreference(candidate, aggressiveness: 1.2f);
        if (score > bestScore)
        {
            bestScore = score;
            bestCell = candidate;
        }
    }
    
    return grid.CellToWorld(bestCell);
}
```

### Step 4: 업데이트 주기 관리 (성능)

```csharp
// InfluenceGrid.cs
float updateInterval = 0.15f; // 초당 약 7회 (매 프레임 불필요)
float nextUpdateTime;

void FixedUpdate()
{
    if (Time.time >= nextUpdateTime)
    {
        UpdateInfluence();
        nextUpdateTime = Time.time + updateInterval;
    }
}
```

---

## OnionCat 적용 포인트

### 1. 적 군집 해소
현재 상태: 여러 적이 모두 플레이어를 직선 추적 → 뭉침 현상
영향 맵 적용 후: `enemyPresence` 값 때문에 이미 적이 있는 셀을 피함 → **자연스러운 포위 대형**

```
적 4마리가 있을 때:
- 뭉침 현상: 모두 플레이어 앞에 쌓임
- 영향 맵 사용: 상/하/좌/우 방향에서 접근 → 포위 형태
```

### 2. 장판 회피 행동
`EnemyHazard`가 활성화되면 해당 위치에 `dangerMap` 값 추가:
- 슬라임이 장판에 접근 안 함 → 자폭 방지
- 원거리 적이 폭발 예정 구역에서 물러남
- **플레이어 입장**: 장판을 전략적으로 배치하면 적 이동 경로 제어 가능

### 3. 포위 공격 패턴과 연계
지금의 `GetPreference` 로직:
- `aggressiveness` 파라미터로 각 적의 공격성 조절
- 보스: `aggressiveness 2.0` → 강하게 달려듦
- 원거리 적: 적절 거리 유지 위해 `playerInfluence` 피크에서 살짝 물러나는 변형

### 4. 구현 규모 조정
OnionCat 방 크기 최대 40×20 = 800 셀 → 매우 가볍다.
- 업데이트 간격 0.15~0.2초로 충분
- 방 전환 시 그리드 리셋 및 방 크기에 맞게 재초기화

---

## 주의사항

- **벽 통과 문제**: 영향 맵은 벽을 인식하지 않음 → 벽 셀을 `-999` 선호도로 마킹하면 해결
- **그라디언트 비교**: 직접 "최고 셀로 이동"보다 현재 위치와의 차이(gradient)를 이용해 부드러운 이동 경로 구성
- **A* 병행 사용**: 큰 방에서 장애물이 많으면 영향 맵으로 목표 지점 결정, A*로 경로 계산하는 하이브리드 방식이 안정적

---

## 참고 링크

- [Influence Maps - AI Game Programming Wisdom](https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter41_Influence_Maps.pdf)
- [Unity Forum: Influence Maps for 2D](https://forum.unity.com/threads/influence-maps.1234567/)
- [GDC: Influence Maps for Real-Time Strategy Games](https://www.gdcvault.com/play/1014799)
- [Amit's Game Programming: Grid pathfinding + influence](https://www.redblobgames.com/pathfinding/grids/graphs.html)

