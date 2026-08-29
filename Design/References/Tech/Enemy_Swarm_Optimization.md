# 적 다수 처리 최적화 (Enemy Swarm Optimization)

리서치 날짜: 2026-08-29

## 개요

로그라이크 게임에서 화면에 30~100명 이상의 적이 등장하면 FPS 저하가 발생한다. 원인은 크게 두 가지: **물리 연산 비용**과 **Update() 호출 비용**. OnionCat은 방 기반 전투이므로 방 내 최대 50여 개 적까지 60fps를 유지하는 것이 목표.

핵심 기법:
1. **공간 해싱 (Spatial Hashing)** — 거리 계산 O(n²) → O(1)로 축소
2. **컴포넌트 비활성화** — 화면 밖 적 Update 중단
3. **Physics Layer Matrix** — 불필요한 충돌 계산 제거
4. **LOD (Level of Detail)** — 먼 적은 단순 AI로 전환

---

## Unity 구현 방법

### 1. 공간 해싱 (Spatial Hashing Grid)

가장 효과적인 방법. 세계를 고정 크기 셀로 나누고, 각 적이 자신의 셀에 등록한다.

```csharp
public class SpatialHashGrid
{
    private float cellSize;
    private Dictionary<Vector2Int, List<Transform>> grid = new();

    public SpatialHashGrid(float cellSize) => this.cellSize = cellSize;

    private Vector2Int GetCell(Vector2 pos)
        => new Vector2Int(Mathf.FloorToInt(pos.x / cellSize),
                          Mathf.FloorToInt(pos.y / cellSize));

    public void Register(Transform t)
    {
        var cell = GetCell(t.position);
        if (!grid.ContainsKey(cell)) grid[cell] = new List<Transform>();
        grid[cell].Add(t);
    }

    public void Clear() => grid.Clear();

    // 반경 내 이웃 조회 — O(1) 에 가까움
    public List<Transform> GetNeighbors(Vector2 pos, float radius)
    {
        var result = new List<Transform>();
        int range = Mathf.CeilToInt(radius / cellSize);
        var origin = GetCell(pos);
        for (int x = -range; x <= range; x++)
        for (int y = -range; y <= range; y++)
        {
            var key = new Vector2Int(origin.x + x, origin.y + y);
            if (grid.TryGetValue(key, out var list)) result.AddRange(list);
        }
        return result;
    }
}
```

**사용 예시 (EnemyManager)**:
```csharp
void FixedUpdate()
{
    spatialGrid.Clear();
    foreach (var enemy in activeEnemies) spatialGrid.Register(enemy.transform);

    // 각 적이 근접 여부 판단 시 Physics.OverlapCircle 대신 spatialGrid.GetNeighbors() 사용
}
```

---

### 2. 화면 밖 적 컴포넌트 비활성화

적이 카메라 뷰포트 밖에 있을 때 AI, 애니메이션, 물리를 중단.

```csharp
public class EnemyVisibilityCuller : MonoBehaviour
{
    [SerializeField] private MonoBehaviour[] componentsToDisable;
    private Camera mainCam;

    void Awake() => mainCam = Camera.main;

    void Update()
    {
        bool visible = IsVisible();
        foreach (var comp in componentsToDisable)
            if (comp.enabled != visible) comp.enabled = visible;
    }

    bool IsVisible()
    {
        Vector3 vp = mainCam.WorldToViewportPoint(transform.position);
        return vp.x > -0.1f && vp.x < 1.1f && vp.y > -0.1f && vp.y < 1.1f;
    }
}
```

비활성화 대상: `EnemyAI`, `Animator`, `Rigidbody2D.simulated = false`

---

### 3. Physics Layer Matrix 최적화

Project Settings → Physics 2D → Layer Collision Matrix에서 불필요한 레이어 조합을 모두 비활성화.

| 레이어 | Enemy | Player | PlayerProjectile | EnemyProjectile |
|--------|-------|--------|-----------------|----------------|
| Enemy | OFF | ON | ON | OFF |
| Player | ON | OFF | OFF | ON |
| PlayerProjectile | ON | OFF | OFF | OFF |
| EnemyProjectile | OFF | ON | OFF | OFF |

Enemy끼리 충돌을 OFF로 설정하면 군집 이동 시 물리 연산이 대폭 줄어듦. 대신 겹침 방지는 Steering Behavior로 처리.

---

### 4. Update 분산 (Staggered Update)

모든 적이 같은 프레임에 업데이트하지 않도록 분산.

```csharp
public class EnemyUpdateScheduler : MonoBehaviour
{
    private static List<EnemyAI> enemies = new();
    private int frameOffset;
    private const int UPDATE_INTERVAL = 3; // 3프레임마다 1회

    void OnEnable()
    {
        frameOffset = enemies.Count % UPDATE_INTERVAL;
        enemies.Add(GetComponent<EnemyAI>());
    }

    void OnDisable() => enemies.Remove(GetComponent<EnemyAI>());

    void Update()
    {
        if (Time.frameCount % UPDATE_INTERVAL == frameOffset)
            GetComponent<EnemyAI>().ManualUpdate();
    }
}
```

---

### 5. Object Pooling 필수 적용

적 사망/소환 시 Instantiate/Destroy 금지. 반드시 풀링 사용.

```csharp
// Unity 6 내장 ObjectPool 사용
var pool = new ObjectPool<EnemyController>(
    createFunc: () => Instantiate(enemyPrefab),
    actionOnGet: e => e.gameObject.SetActive(true),
    actionOnRelease: e => e.gameObject.SetActive(false),
    defaultCapacity: 30, maxSize: 100
);
```

---

## OnionCat 적용 포인트

| 상황 | 적용 기법 |
|------|----------|
| 방 내 30+ 적 등장 파도 | Staggered Update + Object Pooling |
| 근접 추적 AI 거리 계산 | SpatialHashGrid (cellSize ≈ 방 크기/8) |
| 화면 전환 시 이전 방 적 처리 | 카메라 뷰포트 컬링 + Rigidbody2D.simulated=false |
| 적 간 밀어내기 (Separation) | 물리 충돌 대신 Separation Steering 로직으로 대체 |
| 보스 방 이전 성능 예열 | 보스 등장 전 적 풀 미리 warm-up |

### 권장 구현 순서 (OnionCat 기준)
1. `EnemySpawner`에 `ObjectPool<EnemyController>` 적용
2. 방 입장 시 적 풀 Warm-up (5~10개 미리 생성)
3. `SpatialHashGrid` Manager 싱글턴 구현 (EnemyManager에 통합)
4. 각 EnemyAI는 플레이어까지 거리 계산 시 직접 Vector2.Distance 대신 SpatialHashGrid 쿼리 사용
5. Layer Collision Matrix에서 Enemy-Enemy 충돌 OFF
6. Profiler로 평균 ms 확인 → 목표: Update() 총 1ms 이하

---

## 참고 링크

- Unity Profiler 사용법: https://docs.unity3d.com/Manual/Profiler.html
- Unity ObjectPool API: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- Physics2D Layer Matrix: https://docs.unity3d.com/Manual/LayerBasedCollision.html
- Spatial Hashing 개념: https://www.cs.princeton.edu/~rs/talks/LLRB/LLRB.pdf (참고)
- Game Programming Patterns — Object Pool: https://gameprogrammingpatterns.com/object-pool.html
