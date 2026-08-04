# Unity 내장 오브젝트 풀 API (UnityEngine.Pool)

리서치 날짜: 2026-08-04

## 개요

Unity 2021.1부터 `UnityEngine.Pool` 네임스페이스가 공식 내장됨. 기존에는 직접 List나 Queue로 풀을 구현해야 했으나, 이제 표준화된 API로 프로젝타일·이펙트·파티클 등 반복 생성/소멸 오브젝트를 효율적으로 관리할 수 있다.

**OnionCat에서 왜 중요한가?**
- Crop의 투사체는 발사-충돌-소멸 사이클이 매우 빠름
- Instantiate/Destroy 반복 시 GC(가비지 컬렉터) 부하 → 프레임 드롭 스파이크
- ObjectPool로 전환 시 GC 할당 제거, 60fps 유지에 직접 기여

---

## Unity 구현 방법

### 1. 기본 ObjectPool<T> 사용

```csharp
using UnityEngine;
using UnityEngine.Pool;

public class ProjectilePool : MonoBehaviour
{
    [SerializeField] private Projectile prefab;
    
    private IObjectPool<Projectile> pool;

    private void Awake()
    {
        pool = new ObjectPool<Projectile>(
            createFunc:    () => Instantiate(prefab),          // 풀이 비어있을 때 새 오브젝트 생성
            actionOnGet:   p => p.gameObject.SetActive(true),  // 꺼낼 때
            actionOnRelease: p => p.gameObject.SetActive(false),// 반납할 때
            actionOnDestroy: p => Destroy(p.gameObject),       // 풀 초과 시 진짜 파괴
            collectionCheck: true,   // 개발 중 중복 반납 오류 감지 (Release 버전에서 false)
            defaultCapacity: 20,
            maxSize: 100
        );
    }

    public Projectile Get() => pool.Get();
    public void Release(Projectile p) => pool.Release(p);
}
```

### 2. Projectile 클래스에서 풀 참조 보유

```csharp
public class Projectile : MonoBehaviour
{
    private IObjectPool<Projectile> ownerPool;

    public void Init(IObjectPool<Projectile> pool)
    {
        ownerPool = pool;
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        // 충돌 처리 후 풀에 반납
        ownerPool?.Release(this);
    }

    private void OnDisable()
    {
        // 화면 밖 나갔을 때도 반납
        if (gameObject.activeSelf)
            ownerPool?.Release(this);
    }
}
```

### 3. 발사 위치에서 사용

```csharp
public class CropShooter : MonoBehaviour
{
    [SerializeField] private ProjectilePool projectilePool;

    public void Fire(Vector2 direction)
    {
        Projectile p = projectilePool.Get();
        p.transform.position = transform.position;
        p.Init(projectilePool.Pool);  // 풀 참조 전달
        p.Launch(direction);
    }
}
```

### 4. LinkedPool<T> (대안 — 메모리 연속성 중시)

```csharp
// 내부적으로 LinkedList 사용, 대용량(1000개+) 풀에서 더 빠를 수 있음
var pool = new LinkedPool<Projectile>(
    createFunc: () => Instantiate(prefab),
    actionOnGet: p => p.gameObject.SetActive(true),
    actionOnRelease: p => p.gameObject.SetActive(false),
    maxSize: 200
);
```

### 5. CollectionPool (List, Dictionary 풀링)

```csharp
// 일시적으로 List가 필요한 경우 (적 탐색, 오버랩 결과 등)
using (var list = CollectionPool<List<Enemy>, Enemy>.Get(out List<Enemy> enemies))
{
    Physics2D.OverlapCircleNonAlloc(pos, radius, enemies);
    foreach (var e in enemies) e.TakeDamage(10);
}   // using 블록 나가면 자동 반납
```

---

## OnionCat 적용 포인트

### 적용 대상 목록
| 오브젝트 | 생성 빈도 | 풀 최소 크기 |
|---------|---------|------------|
| Crop 기본 투사체 | 초당 2~5개 | 20 |
| 탄막 패턴 투사체 | 동시 50개+ | 100 |
| 히트 파티클 이펙트 | 피격마다 | 30 |
| 데미지 숫자 텍스트 | 피격마다 | 20 |
| 적 드롭 아이템 | 적 처치마다 | 30 |

### 아키텍처 권장 구조

```
ProjectileManager (싱글톤 or DI)
├── CropProjectilePool (기본 투사체)
├── EnemyProjectilePool (적 투사체)
└── ParticlePool (히트 이펙트)
```

- ProjectileManager를 싱글톤으로 만들고 각 풀을 보유
- 각 Projectile/Particle 컴포넌트는 자신이 반납될 풀 참조를 Init으로 받음

### 주의사항
1. `collectionCheck: true`는 개발 중만 사용 → Release 빌드에서 `false`로 변경
2. `OnDisable()`에서 Release 호출 시 이미 비활성화 상태이면 무한루프 가능 → `activeSelf` 체크 필수
3. 풀에서 꺼낸 오브젝트는 `SetActive(true)` 되지만 내부 상태(속도, 콜라이더)는 리셋 필요
4. `maxSize` 초과 시 `actionOnDestroy` 호출 → 로그 남겨서 적절한 maxSize 조정

---

## 참고 링크

- Unity 공식 문서 ObjectPool: https://docs.unity3d.com/2021.1/Documentation/ScriptReference/Pool.ObjectPool_1.html
- Unity Blog — Object Pooling: https://unity.com/blog/games/feature-highlight-object-pooling-using-unitys-new-api
- YouTube 튜토리얼 (Code Monkey): https://www.youtube.com/watch?v=tdSmKaJvCoA
- Unity Learn — Object Pooling: https://learn.unity.com/tutorial/introduction-to-object-pooling
