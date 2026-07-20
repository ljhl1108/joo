# 유도탄 & 반사탄 시스템 (Homing & Bouncing Projectiles)

리서치 날짜: 2026-07-20

## 개요

Projectile_System.md가 기본 투사체를 다룬다면, 이 문서는 두 가지 특수 탄종에 집중한다.

- **유도탄(Homing)**: 목표물을 추적하며 궤적을 바꾸는 탄. Enter the Gungeon의 유도 탄환, Binding of Isaac의 Mom's Eye 등에서 사용.
- **반사탄(Bouncing)**: 벽/적에 맞아 궤적이 반전되는 탄. Nuclear Throne의 반사 총기, BoI의 Rubber Cement 등.

OnionCat에서 Crop(P2)의 원거리 공격 다양화 및 특수 업그레이드 탄종으로 핵심적.

---

## Unity 구현 방법

### 1. 유도탄 (Homing Projectile)

#### A. 기본 구조 — 회전 추적
```csharp
public class HomingProjectile : MonoBehaviour
{
    [SerializeField] private float speed = 8f;
    [SerializeField] private float rotateSpeed = 200f; // 초당 회전 각도
    [SerializeField] private float homingDuration = 3f; // 유도 지속 시간
    [SerializeField] private float acquisitionRadius = 10f; // 타겟 탐지 반경

    private Transform target;
    private Rigidbody2D rb;
    private float homingTimer;

    void Awake() => rb = GetComponent<Rigidbody2D>();

    void Start()
    {
        AcquireTarget();
        homingTimer = homingDuration;
    }

    void FixedUpdate()
    {
        homingTimer -= Time.fixedDeltaTime;

        if (target != null && homingTimer > 0f)
            RotateTowardTarget();

        rb.linearVelocity = transform.up * speed; // transform.up = 탄 앞 방향
    }

    void AcquireTarget()
    {
        // 가장 가까운 적 탐지
        Collider2D[] hits = Physics2D.OverlapCircleAll(transform.position, acquisitionRadius,
            LayerMask.GetMask("Enemy"));

        float minDist = float.MaxValue;
        foreach (var h in hits)
        {
            float d = Vector2.Distance(transform.position, h.transform.position);
            if (d < minDist) { minDist = d; target = h.transform; }
        }
    }

    void RotateTowardTarget()
    {
        if (target == null) { AcquireTarget(); return; }

        Vector2 dir = (target.position - transform.position).normalized;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg - 90f;
        float newAngle = Mathf.MoveTowardsAngle(transform.eulerAngles.z, angle,
            rotateSpeed * Time.fixedDeltaTime);
        transform.rotation = Quaternion.Euler(0, 0, newAngle);
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Enemy"))
        {
            // 데미지 처리 후 반환
            Destroy(gameObject); // 또는 풀 반환
        }
    }
}
```

#### B. 고급: 예측 조준 (Predictive Aiming)
```csharp
// 현재 위치 대신 적의 미래 위치를 겨냥
Vector2 PredictTargetPosition(Transform tgt, float projSpeed)
{
    Rigidbody2D tgtRb = tgt.GetComponent<Rigidbody2D>();
    if (tgtRb == null) return tgt.position;

    Vector2 toTarget = (Vector2)tgt.position - rb.position;
    float timeToHit = toTarget.magnitude / projSpeed;
    return (Vector2)tgt.position + tgtRb.linearVelocity * timeToHit;
}
```

#### C. 유도력 단계 (Lock-On 딜레이)
```csharp
[SerializeField] private float lockOnDelay = 0.3f; // 발사 후 0.3초는 직진
private float lockOnTimer;

void Start() { lockOnTimer = lockOnDelay; }

void FixedUpdate()
{
    if (lockOnTimer > 0f) { lockOnTimer -= Time.fixedDeltaTime; }
    else if (target != null) { RotateTowardTarget(); }

    rb.linearVelocity = transform.up * speed;
}
```

---

### 2. 반사탄 (Bouncing Projectile)

#### A. Rigidbody2D + PhysicsMaterial2D 방식 (간단)
- PhysicsMaterial2D 생성: Friction=0, Bounciness=1
- Rigidbody2D에 할당
- Collision Detection Mode = Continuous
- 단점: 물리 계산이 약간 부정확할 수 있음

#### B. Raycast 방식 (정밀 반사)
```csharp
public class BouncingProjectile : MonoBehaviour
{
    [SerializeField] private float speed = 12f;
    [SerializeField] private int maxBounces = 3;
    [SerializeField] private LayerMask wallMask;
    [SerializeField] private LayerMask enemyMask;

    private Vector2 moveDir;
    private int bounceCount;
    private Rigidbody2D rb;

    public void Init(Vector2 direction)
    {
        moveDir = direction.normalized;
        rb = GetComponent<Rigidbody2D>();
    }

    void FixedUpdate()
    {
        float moveDistance = speed * Time.fixedDeltaTime;
        RaycastHit2D wallHit = Physics2D.Raycast(rb.position, moveDir, moveDistance + 0.1f, wallMask);
        RaycastHit2D enemyHit = Physics2D.Raycast(rb.position, moveDir, moveDistance + 0.1f, enemyMask);

        // 적 먼저 체크
        if (enemyHit && (!wallHit || enemyHit.distance < wallHit.distance))
        {
            HitEnemy(enemyHit);
            return;
        }

        if (wallHit)
        {
            // 반사 처리
            rb.MovePosition(wallHit.point + wallHit.normal * 0.05f);
            moveDir = Vector2.Reflect(moveDir, wallHit.normal);
            bounceCount++;

            if (bounceCount >= maxBounces)
                Destroy(gameObject);
        }
        else
        {
            rb.MovePosition(rb.position + moveDir * moveDistance);
        }
    }

    void HitEnemy(RaycastHit2D hit)
    {
        hit.collider.GetComponent<IDamageable>()?.TakeDamage(10);
        Destroy(gameObject);
    }
}
```

#### C. 반사 시 데미지 증폭
```csharp
[SerializeField] private float bounceMultiplier = 1.2f; // 반사마다 20% 증가
private float damageMultiplier = 1f;

// 반사 처리 후:
damageMultiplier *= bounceMultiplier;

// 적 히트 시:
int damage = Mathf.RoundToInt(baseDamage * damageMultiplier);
```

---

### 3. 오브젝트 풀 통합

```csharp
// 풀에서 꺼낼 때 초기화
public class HomingProjectile : MonoBehaviour
{
    void OnEnable()
    {
        AcquireTarget();
        homingTimer = homingDuration;
    }

    void OnDisable()
    {
        target = null;
        rb.linearVelocity = Vector2.zero;
    }
}
```

---

### 4. 시각 피드백

```csharp
// 유도탄: 회오리 파티클이 탄 주변을 도는 효과
[SerializeField] private ParticleSystem homingTrail;
// → 탄이 돌 때 파티클도 같이 회전

// 반사탄: 벽 충돌 시 불꽃 파티클
[SerializeField] private ParticleSystem sparks;
void OnBounce() => sparks.Play();
```

---

## OnionCat 적용 포인트

### 유도탄 업그레이드 예시
- **기본 씨앗** → 직선 투사체
- **유도 씨앗** → 가장 가까운 적 추적 (HomingProjectile)
- **스마트 씨앗** → 예측 조준 + 짧은 사거리
- **적 타입 연동**: Cat이 발각한 적에게만 유도되는 탄 (공유 타겟 시스템)

### 반사탄 업그레이드 예시
- **탱탱볼 씨앗** → 최대 3회 반사, 매 반사마다 대미지 +20%
- **Cat 협력 콤보**: Cat의 대시 중 Crop의 반사탄이 Cat을 통과할 경우 강화 효과

### 적 설계 응용
- **미러 몬스터**: Crop의 투사체만 반사해 도로 쏘는 적 → Cat이 근접 처리해야 함
- **유도탄 사용 보스**: 보스가 유도탄을 쏘면 Cat이 Crop 앞에서 대시로 방어
- **반사 벽 방**: 방 벽에 반사 레이어를 배치해 퍼즐형 전투 방 구성

---

## 참고 링크

- [Unity Docs: Rigidbody2D](https://docs.unity3d.com/Manual/class-Rigidbody2D.html)
- [Unity Docs: Physics2D.Raycast](https://docs.unity3d.com/ScriptReference/Physics2D.Raycast.html)
- [Vector2.Reflect](https://docs.unity3d.com/ScriptReference/Vector2.Reflect.html)
- [PhysicsMaterial2D](https://docs.unity3d.com/Manual/class-PhysicsMaterial2D.html)
- [Brackeys: Homing Missile in Unity](https://www.youtube.com/watch?v=0v_H3oOR0aU)
- [Game Dev Guide: Bouncing Projectile](https://www.youtube.com/c/GameDevGuide)
