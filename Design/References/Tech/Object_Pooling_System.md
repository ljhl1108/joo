# 오브젝트 풀링 시스템 (Object Pooling System)

리서치 날짜: 2026-08-01

## 개요

오브젝트 풀링은 게임 오브젝트를 매번 생성(Instantiate)/파괴(Destroy)하는 대신,
미리 일정 수를 생성해두고 **비활성화(Inactive) 상태로 보관**했다가 필요할 때 꺼내 쓰고
사용 후 다시 풀에 반납하는 패턴이다.

### 왜 OnionCat에 필수적인가?
- Onion의 투사체가 빠른 속도로 발사될 때 매 발사마다 `Instantiate`를 호출하면 **GC 스파이크** 발생 → 프레임 드랍
- 탄막 패턴(Danmaku), 파티클 이펙트, 피격 이펙트, 드롭 아이템 모두 풀링 대상
- 모바일/저사양 빌드를 고려하면 더욱 중요

---

## Unity 구현 방법

### 방법 1: Unity 내장 ObjectPool<T> (Unity 2021+, 권장)

```csharp
using UnityEngine.Pool;

public class ProjectilePool : MonoBehaviour
{
    [SerializeField] private GameObject prefab;
    [SerializeField] private int defaultCapacity = 20;
    [SerializeField] private int maxSize = 100;

    private ObjectPool<GameObject> pool;

    void Awake()
    {
        pool = new ObjectPool<GameObject>(
            createFunc:    () => Instantiate(prefab),
            actionOnGet:   obj => obj.SetActive(true),
            actionOnRelease: obj => obj.SetActive(false),
            actionOnDestroy: obj => Destroy(obj),
            collectionCheck: false,
            defaultCapacity: defaultCapacity,
            maxSize: maxSize
        );
    }

    public GameObject Get() => pool.Get();
    public void Release(GameObject obj) => pool.Release(obj);
}
```

### 방법 2: 싱글턴 Generic Pool Manager (여러 타입 풀 통합 관리)

```csharp
public class PoolManager : MonoBehaviour
{
    public static PoolManager Instance { get; private set; }

    private Dictionary<string, ObjectPool<GameObject>> pools = new();
    private Dictionary<string, GameObject> prefabMap = new();

    void Awake() => Instance = this;

    public void RegisterPool(string key, GameObject prefab, int capacity = 20)
    {
        prefabMap[key] = prefab;
        pools[key] = new ObjectPool<GameObject>(
            () => Instantiate(prefabMap[key]),
            obj => obj.SetActive(true),
            obj => obj.SetActive(false),
            obj => Destroy(obj),
            false, capacity
        );
    }

    public GameObject Spawn(string key, Vector3 pos, Quaternion rot)
    {
        var obj = pools[key].Get();
        obj.transform.SetPositionAndRotation(pos, rot);
        return obj;
    }

    public void Despawn(string key, GameObject obj) => pools[key].Release(obj);
}
```

### 방법 3: 투사체 자동 반납 (수명 기반)

```csharp
// 투사체 컴포넌트에 부착
public class Projectile : MonoBehaviour
{
    [SerializeField] private float lifetime = 3f;
    private string poolKey;

    public void Init(string key)
    {
        poolKey = key;
        CancelInvoke();
        Invoke(nameof(ReturnToPool), lifetime);
    }

    void OnDisable() => CancelInvoke();

    public void ReturnToPool()
    {
        PoolManager.Instance.Despawn(poolKey, gameObject);
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        // 히트 처리 후...
        ReturnToPool();
    }
}
```

### 핵심 주의사항

| 주의 항목 | 설명 |
|-----------|------|
| **상태 초기화** | Get()으로 꺼낼 때 속도·방향·HP 등 반드시 리셋 |
| **Coroutine 정리** | 반납 전 `StopAllCoroutines()` 또는 `CancelInvoke()` 필수 |
| **이벤트 구독 해제** | UnityEvent/Action에 구독 중이면 Release 전 Unsubscribe |
| **Transform 부모** | Pool 오브젝트들을 공통 부모 Transform 아래 두면 Hierarchy 정리됨 |
| **maxSize 설정** | 무제한 풀은 메모리 누수 위험. 100~200 사이로 상한 설정 권장 |

---

## OnionCat 적용 포인트

### 1. 투사체 풀 (Onion 원거리 공격)
- `PoolManager`에 `"onion_bullet"`, `"onion_homing"` 등 키로 풀 등록
- Onion이 발사할 때마다 `PoolManager.Instance.Spawn("onion_bullet", ...)` 호출
- 투사체 충돌 또는 수명 초과 시 자동 `ReturnToPool()`
- **권장 초기 풀 크기**: 기본 투사체 20~30개, 탄막 패턴용 50~100개

### 2. 히트 이펙트 풀
- 적 피격 시 파티클 이펙트(붉은 섬광, 흰 스파크)를 풀로 관리
- 파티클 시스템의 경우 `OnParticleSystemStopped` 콜백으로 자동 반납
- `"hit_effect_melee"`, `"hit_effect_ranged"`, `"hit_effect_parry"` 세 풀 분리 권장

### 3. 드롭 아이템/픽업 풀
- 방 클리어 후 드롭되는 아이템들도 풀링 대상
- 방 전환 시 현재 방에 남은 드롭 아이템을 일괄 반납: `RoomManager.OnRoomExit()` → 드롭 풀 전체 정리

### 4. 탄막 패턴 대량 투사체
- 보스 탄막 패턴은 순간 50~100개 발사 가능 → 풀 없으면 스파이크 확실
- `DanmakuPatternSystem`에서 패턴 시작 전 `pool.PrewarmPool(count)` 호출로 사전 준비

### 5. PoolManager 초기화 순서 (Awake 순서 주의)
```
PoolManager.Awake()  → 가장 먼저 (ExecutionOrder -100)
ProjectileSpawner.Start()  → PoolManager 등록 후 사용
```
- `[DefaultExecutionOrder(-100)]` 어트리뷰트로 PoolManager가 최우선 Awake되도록 보장

---

## 참고 링크

- Unity 공식 ObjectPool 문서: https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html
- Unity 공식 오브젝트 풀링 튜토리얼: https://learn.unity.com/tutorial/object-pooling
- Unity Blog — Object Pooling (2021): https://blog.unity.com/games/create-a-simple-messaging-system-with-events
- Catlike Coding — Object Management: https://catlikecoding.com/unity/tutorials/object-management/
- Game Dev Guide — Object Pooling in Unity: https://www.youtube.com/watch?v=tdSmKaJvCoA
