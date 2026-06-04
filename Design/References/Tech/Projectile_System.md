# 투사체 시스템 (Projectile System)

## 개요

투사체 시스템은 원거리 공격의 근간이며 OnionCat에서 Player 2(Crop/Onion)의 핵심 무기다. 단순한 직선 투사체부터 탄막 패턴, 유도탄, 반사탄까지 확장 가능한 구조가 필요하다. 투사체는 생성/소멸이 빈번해서 **오브젝트 풀링(Object Pooling)** 없이는 GC Spike가 발생한다.

---

## Unity 구현 방법

### 1. 기본 투사체 구조

```csharp
public class Projectile : MonoBehaviour
{
    [SerializeField] private float speed = 10f;
    [SerializeField] private int damage = 1;
    [SerializeField] private float lifetime = 3f;

    private Vector2 direction;
    private Rigidbody2D rb;

    void Awake() => rb = GetComponent<Rigidbody2D>();

    public void Init(Vector2 dir)
    {
        direction = dir.normalized;
        rb.linearVelocity = direction * speed;
        Invoke(nameof(ReturnToPool), lifetime);
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.TryGetComponent<IDamageable>(out var target))
        {
            target.TakeDamage(damage);
            ReturnToPool();
        }
    }

    void ReturnToPool()
    {
        CancelInvoke();
        ProjectilePool.Instance.Return(this);
    }
}
```

### 2. 오브젝트 풀링 (Object Pooling)

투사체는 Unity 2021+ 내장 `ObjectPool<T>` 사용 권장.

```csharp
using UnityEngine.Pool;

public class ProjectilePool : MonoBehaviour
{
    public static ProjectilePool Instance { get; private set; }

    [SerializeField] private Projectile prefab;
    private ObjectPool<Projectile> pool;

    void Awake()
    {
        Instance = this;
        pool = new ObjectPool<Projectile>(
            createFunc: () => Instantiate(prefab),
            actionOnGet: p => p.gameObject.SetActive(true),
            actionOnRelease: p => p.gameObject.SetActive(false),
            actionOnDestroy: p => Destroy(p.gameObject),
            maxSize: 50
        );
    }

    public Projectile Get(Vector3 pos, Vector2 dir)
    {
        var p = pool.Get();
        p.transform.position = pos;
        p.Init(dir);
        return p;
    }

    public void Return(Projectile p) => pool.Release(p);
}
```

### 3. 탄막 패턴 (Danmaku Patterns)

```csharp
public class BulletPatternShooter : MonoBehaviour
{
    // 원형 탄막: n발을 360도 균등 분산
    public void FireCircle(int count)
    {
        float angleStep = 360f / count;
        for (int i = 0; i < count; i++)
        {
            float angle = i * angleStep;
            Vector2 dir = new Vector2(
                Mathf.Cos(angle * Mathf.Deg2Rad),
                Mathf.Sin(angle * Mathf.Deg2Rad)
            );
            ProjectilePool.Instance.Get(transform.position, dir);
        }
    }

    // 부채꼴 탄막: 목표 방향 기준 spread각도 내에 count발
    public void FireSpread(Vector2 target, int count, float spread)
    {
        float baseAngle = Mathf.Atan2(target.y, target.x) * Mathf.Rad2Deg;
        float step = count > 1 ? spread / (count - 1) : 0;
        float startAngle = baseAngle - spread / 2f;

        for (int i = 0; i < count; i++)
        {
            float angle = (startAngle + step * i) * Mathf.Deg2Rad;
            Vector2 dir = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
            ProjectilePool.Instance.Get(transform.position, dir);
        }
    }
}
```

### 4. 유도탄 (Homing Projectile)

```csharp
public class HomingProjectile : Projectile
{
    [SerializeField] private float turnSpeed = 200f;
    private Transform target;

    public void InitHoming(Vector2 dir, Transform target)
    {
        this.target = target;
        base.Init(dir);
    }

    void FixedUpdate()
    {
        if (target == null) return;
        Vector2 toTarget = ((Vector2)target.position - rb.position).normalized;
        float angle = Mathf.Atan2(toTarget.y, toTarget.x) * Mathf.Rad2Deg;
        float newAngle = Mathf.MoveTowardsAngle(rb.rotation, angle, turnSpeed * Time.fixedDeltaTime);
        rb.rotation = newAngle;
        rb.linearVelocity = new Vector2(Mathf.Cos(newAngle * Mathf.Deg2Rad), Mathf.Sin(newAngle * Mathf.Deg2Rad)) * speed;
    }
}
```

### 5. 반사탄 (Bouncing Projectile)

```csharp
public class BouncingProjectile : Projectile
{
    [SerializeField] private int maxBounces = 3;
    private int bounceCount;

    void OnCollisionEnter2D(Collision2D col)
    {
        if (col.gameObject.CompareTag("Wall"))
        {
            if (bounceCount >= maxBounces) { ReturnToPool(); return; }
            bounceCount++;
            Vector2 reflected = Vector2.Reflect(rb.linearVelocity.normalized, col.contacts[0].normal);
            rb.linearVelocity = reflected * speed;
        }
    }
}
// 주의: 반사탄은 Trigger 대신 Collider를 사용해야 normal 벡터를 얻을 수 있음
```

### 6. 투사체 타입 관리 — ScriptableObject 기반

```csharp
[CreateAssetMenu(menuName = "OnionCat/ProjectileData")]
public class ProjectileData : ScriptableObject
{
    public GameObject prefab;
    public float speed;
    public int damage;
    public float lifetime;
    public bool isHoming;
    public int bounces;
    public int spreadCount;
    public float spreadAngle;
}
```

---

## OnionCat 적용 포인트

### Player 2 (Crop/Onion) 기본 공격
- `ProjectileData` ScriptableObject로 기본 투사체 정의
- 마우스 방향으로 `FireSingle()` 호출
- 업그레이드 시 `ProjectileData`를 교체하거나 파라미터 수정 → 탄막/유도탄으로 진화

### 적 투사체와 차별화
- 플레이어 투사체: `Layer = "PlayerBullet"` → 적에게만 충돌
- 적 투사체: `Layer = "EnemyBullet"` → 플레이어에게만 충돌
- Physics2D Layer Matrix에서 `PlayerBullet ↔ EnemyBullet` 충돌 비활성화

### Parry 시스템 연계
- Crop의 방패/패리 시 `EnemyBullet`을 감지해 방향 반전 후 `PlayerBullet` 레이어로 전환
- `Projectile.Reflect(hitNormal)` 메서드 추가로 패리 로직 구현

### 오브젝트 풀 초기화
- 씬 로드 시 `ProjectilePool`이 prefab별로 풀을 미리 생성 (defaultCapacity: 20)
- 보스 패턴처럼 순간 대량 발사 시 풀이 자동 확장

---

## 참고 링크

- [Unity ObjectPool 공식 문서](https://docs.unity3d.com/ScriptReference/Pool.ObjectPool_1.html)
- [Unity 2D Physics Layer Matrix](https://docs.unity3d.com/Manual/LayerBasedCollision.html)
- [GDC: Bullet Patterns in 2D Games](https://www.youtube.com/results?search_query=bullet+pattern+design+GDC)
- [Brackeys - Object Pooling in Unity](https://www.youtube.com/watch?v=tdSmKaJvCoA)
