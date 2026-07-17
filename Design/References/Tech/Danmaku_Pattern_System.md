# 탄막 패턴 시스템 (Danmaku Pattern System)

리서치 날짜: 2026-07-17

## 개요

탄막(弾幕, Danmaku)은 총알/투사체를 패턴으로 배열해 쏘는 시스템이다. 기본 `Projectile_System.md`가 오브젝트 풀링과 단일 투사체를 다룬다면, 이 문서는 **패턴 자체의 설계와 구현**에 집중한다.

OnionCat에서는:
- **Onion 플레이어** — 마우스 조준 단발/연사 투사체 (플레이어 측 공격)
- **적 탄막** — 플레이어를 압박하는 다양한 패턴, 근접 전용 적 vs 원거리 전용 적 구분
- 탄막 패턴의 풍부함이 전투 다양성의 핵심

---

## 핵심 탄막 패턴 분류

### 패턴 1: N-Way 방사형 (N-Way Spread)

가장 기본. N개의 총알을 균등 각도로 배포.

```csharp
public class NWayPattern : MonoBehaviour
{
    [SerializeField] private int bulletCount = 8;
    [SerializeField] private float speed = 5f;
    [SerializeField] private GameObject bulletPrefab;

    public void Fire(Vector2 origin, float startAngle = 0f)
    {
        float angleStep = 360f / bulletCount;
        for (int i = 0; i < bulletCount; i++)
        {
            float angle = startAngle + angleStep * i;
            Vector2 dir = AngleToDirection(angle);
            SpawnBullet(origin, dir * speed);
        }
    }

    private Vector2 AngleToDirection(float degrees)
    {
        float rad = degrees * Mathf.Deg2Rad;
        return new Vector2(Mathf.Cos(rad), Mathf.Sin(rad));
    }

    private void SpawnBullet(Vector2 pos, Vector2 velocity)
    {
        // 오브젝트 풀에서 꺼냄 (BulletPool.Instance.Get())
        var bullet = Instantiate(bulletPrefab, pos, Quaternion.identity);
        bullet.GetComponent<Rigidbody2D>().linearVelocity = velocity;
    }
}
```

### 패턴 2: 나선형 (Spiral / Rotating Spread)

매 발사마다 시작 각도를 조금씩 회전.

```csharp
public class SpiralPattern : MonoBehaviour
{
    [SerializeField] private int armsCount = 3;      // 나선 팔 개수
    [SerializeField] private float rotationSpeed = 120f; // 초당 회전 각도
    [SerializeField] private float fireRate = 0.05f;
    private float _currentAngle;
    private float _timer;

    void Update()
    {
        _currentAngle += rotationSpeed * Time.deltaTime;
        _timer -= Time.deltaTime;
        if (_timer <= 0f)
        {
            _timer = fireRate;
            FireSpiral();
        }
    }

    private void FireSpiral()
    {
        float armOffset = 360f / armsCount;
        for (int i = 0; i < armsCount; i++)
        {
            float angle = _currentAngle + armOffset * i;
            Vector2 dir = new Vector2(Mathf.Cos(angle * Mathf.Deg2Rad),
                                      Mathf.Sin(angle * Mathf.Deg2Rad));
            SpawnBullet(transform.position, dir * 4f);
        }
    }
}
```

### 패턴 3: 조준탄 (Aimed Shot)

플레이어 위치를 향해 발사. 피할 수는 있지만 방심하면 맞음.

```csharp
public class AimedPattern : MonoBehaviour
{
    [SerializeField] private Transform target;  // 플레이어 Transform
    [SerializeField] private float speed = 6f;
    [SerializeField] private int spreadCount = 3;    // 추가 확산 수
    [SerializeField] private float spreadAngle = 15f; // 좌우 확산 각도

    public void FireAimed()
    {
        if (target == null) return;
        Vector2 toPlayer = (target.position - transform.position).normalized;
        float baseAngle = Mathf.Atan2(toPlayer.y, toPlayer.x) * Mathf.Rad2Deg;

        // 중앙 + 좌우 확산
        for (int i = -(spreadCount / 2); i <= spreadCount / 2; i++)
        {
            float angle = baseAngle + spreadAngle * i;
            Vector2 dir = new Vector2(Mathf.Cos(angle * Mathf.Deg2Rad),
                                      Mathf.Sin(angle * Mathf.Deg2Rad));
            SpawnBullet(transform.position, dir * speed);
        }
    }
}
```

### 패턴 4: 유도탄 (Homing Missile)

일정 시간 플레이어를 추적하다가 직선 비행으로 전환.

```csharp
public class HomingBullet : MonoBehaviour
{
    [SerializeField] private float speed = 4f;
    [SerializeField] private float homingDuration = 1.5f; // 추적 시간
    [SerializeField] private float rotateSpeed = 200f;    // 회전 속도
    private Transform _target;
    private float _homingTimer;
    private Rigidbody2D _rb;

    public void Initialize(Transform target)
    {
        _target = target;
        _homingTimer = homingDuration;
        _rb = GetComponent<Rigidbody2D>();
        _rb.linearVelocity = transform.right * speed;
    }

    void Update()
    {
        if (_homingTimer > 0f && _target != null)
        {
            _homingTimer -= Time.deltaTime;
            // 플레이어 방향으로 부드럽게 회전
            Vector2 toTarget = ((Vector2)_target.position - _rb.position).normalized;
            float targetAngle = Mathf.Atan2(toTarget.y, toTarget.x) * Mathf.Rad2Deg;
            float currentAngle = _rb.rotation;
            float newAngle = Mathf.MoveTowardsAngle(currentAngle, targetAngle,
                                                     rotateSpeed * Time.deltaTime);
            _rb.rotation = newAngle;
            _rb.linearVelocity = new Vector2(Mathf.Cos(newAngle * Mathf.Deg2Rad),
                                       Mathf.Sin(newAngle * Mathf.Deg2Rad)) * speed;
        }
        else
        {
            // 추적 종료 → 직선 비행
            _rb.linearVelocity = transform.right * (speed * 1.5f);
        }
    }
}
```

### 패턴 5: 반사탄 (Bouncing / Reflecting Bullet)

벽에 N번 반사. Onion의 쉴드 패리 + 반사탄 역이용에 유용.

```csharp
public class BouncingBullet : MonoBehaviour
{
    [SerializeField] private int maxBounces = 3;
    private int _bounceCount;
    private Vector2 _velocity;

    public void Initialize(Vector2 direction, float speed)
    {
        _velocity = direction.normalized * speed;
    }

    void Update()
    {
        transform.Translate(_velocity * Time.deltaTime, Space.World);
    }

    private void OnCollisionEnter2D(Collision2D col)
    {
        if (col.gameObject.CompareTag("Wall") && _bounceCount < maxBounces)
        {
            _bounceCount++;
            // 충돌 노멀을 기준으로 반사
            Vector2 normal = col.contacts[0].normal;
            _velocity = Vector2.Reflect(_velocity, normal);
        }
        else if (col.gameObject.CompareTag("Enemy"))
        {
            // 적에게 히트
            col.gameObject.GetComponent<EnemyHealth>()?.TakeDamage(10);
            ReturnToPool();
        }
    }
}
```

---

## 패턴 시퀀서 (코루틴 기반)

여러 패턴을 순서/타이밍에 맞춰 조합하는 시퀀서.

```csharp
public class BossAttackSequencer : MonoBehaviour
{
    [SerializeField] private NWayPattern nWayPattern;
    [SerializeField] private SpiralPattern spiralPattern;
    [SerializeField] private AimedPattern aimedPattern;

    // 보스 페이즈 1 공격 루틴
    public IEnumerator Phase1Routine()
    {
        while (true)
        {
            // 8방향 방사 3회
            for (int i = 0; i < 3; i++)
            {
                nWayPattern.Fire(transform.position);
                yield return new WaitForSeconds(0.4f);
            }

            yield return new WaitForSeconds(1f);

            // 나선 2초
            spiralPattern.enabled = true;
            yield return new WaitForSeconds(2f);
            spiralPattern.enabled = false;

            yield return new WaitForSeconds(0.5f);

            // 조준 5발 연속
            for (int i = 0; i < 5; i++)
            {
                aimedPattern.FireAimed();
                yield return new WaitForSeconds(0.3f);
            }

            yield return new WaitForSeconds(2f);
        }
    }

    // 페이즈 전환
    public void TransitionToPhase2()
    {
        StopAllCoroutines();
        StartCoroutine(Phase2Routine());
    }
}
```

---

## 탄막 속도와 밀도 조정 공식

```csharp
// 난이도/층수에 따른 탄막 파라미터 스케일링
public static class BulletScaler
{
    public static float GetBulletSpeed(int floor, float baseSpeed = 4f)
    {
        // 층마다 5% 증가, 최대 2배
        return Mathf.Min(baseSpeed * (1f + floor * 0.05f), baseSpeed * 2f);
    }

    public static int GetBulletCount(int floor, int baseCount = 4)
    {
        // 5층마다 총알 1개 추가, 최대 12개
        return Mathf.Min(baseCount + floor / 5, 12);
    }

    public static float GetFireRate(int floor, float baseRate = 1f)
    {
        // 층마다 발사 간격 3% 감소, 최소 0.4초
        return Mathf.Max(baseRate * (1f - floor * 0.03f), 0.4f);
    }
}
```

---

## OnionCat 적용 포인트

### A. 적 유형별 탄막 패턴 매핑

| 적 유형 | 추천 패턴 | OnionCat 협력 요구 |
|---------|-----------|-------------------|
| 기본 슬라임 | 4-Way 방사 | Cat 근접 처치 (약함) |
| 마법사 적 | 조준탄 3발 | Onion 방패로 파리 후 Cat 돌진 |
| 포탑 적 | 회전 나선 | Cat 접근 불가 → Onion 원거리만 유효 |
| 보스 페이즈1 | N-Way + 조준 조합 | 번갈아 역할 |
| 보스 페이즈2 | 유도탄 4개 | Onion 쉴드 파리 필수 |

### B. Onion 패리 + 반사탄 역이용
- 적의 탄막을 Onion 방패로 막으면 반사탄 생성
- 반사 방향 = 마우스 조준 방향으로 제어 가능 (설계 선택)
- "적의 탄막을 이용해 다른 적 처치" → 스킬 표현 포인트

### C. 근접 전용 적 구분
- 근접 전용 적은 탄막을 쏘지 않음 → Cat만 유효
- 원거리 전용 적은 Cat이 닿기 전에 계속 탄막 → Onion 처치
- 혼합 방에서 긴장감 극대화

### D. 탄막 피하기 공간 확보
- 방 크기 최소 18×12 타일 (1타일=1유닛 기준)
- 탄속 × 투사체 수 × 방 크기 균형 공식:
  - 안전 범위: 탄속 3~6, 8-Way, 방 18×12
  - 위험 범위: 탄속 7이상 + 12-Way → 방 26×18 이상 필요

---

## 참고 링크

- Unity 공식 투사체 튜토리얼: https://docs.unity3d.com/Manual/class-Rigidbody2D.html
- 탄막 패턴 설계 논문 분석: https://www.gamedeveloper.com/design/bullet-hell-game-design-theory
- ShmupDev 패턴 라이브러리: https://shmup.dev (검색: bullet pattern library)
- 오브젝트 풀링 연계: `Design/References/Tech/Projectile_System.md` 참고
