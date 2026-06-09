# 2D 물리 시스템 (Rigidbody2D, CollisionDetection, Layer Matrix)

## 개요
OnionCat 탑다운 로그라이크에서 물리 시스템은 다섯 가지 핵심 요구사항을 처리해야 한다:
1. **대쉬 무적**: 적을 통과하되 벽은 충돌
2. **투사체 고속 이동**: 벽 관통 없이 빠른 이동
3. **패링 방향 감지**: Onion 실드의 방향별 판정
4. **근접 공격**: Cat의 180° 부채꼴 히트박스
5. **성능**: 적 다수 + 투사체 다수 동시 처리 시 60FPS 유지

올바른 Layer Matrix + Rigidbody2D 설정만으로 불필요한 연산을 제거할 수 있다.

---

## Unity 구현 방법

### 1. Rigidbody2D BodyType 선택 기준

| BodyType | 용도 | 특성 |
|----------|------|------|
| **Dynamic** | 플레이어, 이동하는 적 | 물리 시뮬레이션 완전 적용, CPU 비용 높음 |
| **Kinematic** | 투사체, 특수 이동 | 수동 이동(velocity 직접 설정), 물리 영향 없음 |
| **Static** | 벽, 장애물 | 완전 고정, 연산 비용 최소 |

**OnionCat 설정**:
- Player_Cat: `Dynamic`, GravityScale=0, FreezeRotation Z
- 투사체: `Kinematic`, CollisionDetection=Continuous
- 적: `Dynamic` 또는 `Kinematic` (AI 이동 방식에 따라 선택)
- 벽/타일맵: `Static`

```csharp
void Awake()
{
    rb = GetComponent<Rigidbody2D>();
    rb.gravityScale = 0f;                                      // 탑다운: 중력 불필요
    rb.constraints = RigidbodyConstraints2D.FreezeRotation;    // Z축 회전 고정
    rb.interpolation = RigidbodyInterpolation2D.Extrapolate;   // 부드러운 이동
}
```

---

### 2. Collision Detection 모드

| 모드 | 설명 | 사용 대상 |
|------|------|----------|
| **Discrete** | 매 프레임 충돌 검사 | 플레이어, 적 (보통 속도) |
| **Continuous** | 레이캐스트로 프레임 사이 검사 | 빠른 투사체, 대쉬 중 플레이어 |

대쉬 중 Continuous로 전환해 고속 이동 시 벽 관통 방지:

```csharp
IEnumerator DashCoroutine(Vector2 direction)
{
    rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
    Physics2D.IgnoreLayerCollision(
        LayerMask.NameToLayer("Player"),
        LayerMask.NameToLayer("Enemy"),
        true   // 대쉬 중 적 통과
    );

    float elapsed = 0f;
    while (elapsed < dashDuration)
    {
        rb.velocity = direction * dashSpeed;
        elapsed += Time.deltaTime;
        yield return null;
    }

    rb.collisionDetectionMode = CollisionDetectionMode2D.Discrete;
    Physics2D.IgnoreLayerCollision(
        LayerMask.NameToLayer("Player"),
        LayerMask.NameToLayer("Enemy"),
        false  // 대쉬 종료 후 복원
    );
    rb.velocity = Vector2.zero;
}
```

---

### 3. Trigger vs Collider 실전 선택

| 속성 | Collider (isTrigger=false) | Trigger (isTrigger=true) |
|------|---------------------------|--------------------------|
| 물리 충돌(튕김) | 있음 | 없음 (통과) |
| 콜백 | OnCollisionEnter2D | OnTriggerEnter2D |
| 사용 | 벽, 적 본체 | 공격 판정, 감지 영역 |

**근접 공격 판정 (Trigger + OverlapCircle)**:
```csharp
// Cat의 180° 슬래시 판정
void PerformMeleeAttack()
{
    Collider2D[] hits = Physics2D.OverlapCircleAll(
        attackPoint.position,
        attackRadius,
        enemyLayerMask   // Awake()에서 캐싱한 LayerMask
    );

    foreach (var hit in hits)
    {
        if (IsInFrontCone(hit.transform.position, 180f))
            hit.GetComponent<IDamageable>()?.TakeDamage(attackDamage);
    }
}

bool IsInFrontCone(Vector3 targetPos, float coneAngle)
{
    Vector2 dir = (targetPos - transform.position).normalized;
    return Vector2.Angle(transform.right, dir) < coneAngle * 0.5f;
}
```

**Onion 패링 방향 판정 (Trigger)**:
```csharp
void OnTriggerEnter2D(Collider2D collision)
{
    if (!collision.CompareTag("EnemyProjectile")) return;

    Vector2 incomingDir = collision.GetComponent<Rigidbody2D>().velocity.normalized;
    float angle = Vector2.Angle(shieldAimDirection, incomingDir);

    if (angle < parryAngleTolerance)   // 기본 60°
        ParrySuccess(collision.gameObject);
}
```

---

### 4. Physics Layer Matrix 설정

**레이어 구성** (Edit > Project Settings > Physics 2D > Layer Collision Matrix):

```
레이어명            번호
─────────────────────────
Player              6
Enemy               7
EnemyProjectile     8
PlayerProjectile    9
Wall                10
TriggerZone         11
```

**충돌 매트릭스** (O=충돌, X=무시):

```
                Player  Enemy  EnemyProj  PlayerProj  Wall  TriggerZone
Player            X       O       O           X         O       X
Enemy             O       X       X           O         O       X
EnemyProjectile   O       X       X           X         X       O
PlayerProjectile  X       O       X           X         O       O
Wall              O       O       X           O         X       X
TriggerZone       X       X       O           O         X       X
```

- Enemy ↔ Enemy: X → 적끼리 통과 (군집 시 불필요한 밀림 방지)
- PlayerProjectile ↔ PlayerProjectile: X → 아군 투사체끼리 통과
- EnemyProjectile ↔ Wall: X → 적 투사체는 벽 통과 (원하지 않는다면 O로 변경)

**코드에서 LayerMask 사용**:
```csharp
// Awake()에서 레이어 마스크 캐싱
private int enemyLayerMask;
private int playerLayerMask;

void Awake()
{
    enemyLayerMask = LayerMask.GetMask("Enemy");
    playerLayerMask = LayerMask.GetMask("Player");
}
```

---

### 5. Physics2D 프로젝트 설정 최적화

Edit > Project Settings > Physics 2D에서 아래 값으로 변경:

| 설정 | 기본값 | 최적화 값 | 이유 |
|------|--------|-----------|------|
| Gravity Y | -9.81 | 0 | 탑다운, 중력 불필요 |
| Sleep Timeout | 0.5 | 0.2 | 정지 물체 빠른 슬립 → CPU 절약 |
| Velocity Iterations | 8 | 4 | 로그라이크에서 충분한 정확도 |
| Position Iterations | 3 | 2 | 위와 동일 |

---

### 6. 성능 최적화 체크리스트

```csharp
// 1. OverlapXXX 레이어 마스크 반드시 캐싱 (매 호출마다 GetMask 금지)
private readonly int enemyMask = LayerMask.GetMask("Enemy");

// 2. OverlapCircleAll은 공격 시에만 호출 (Update()에서 매 프레임 금지)
void OnAttackInput()
{
    var hits = Physics2D.OverlapCircleAll(pos, radius, enemyMask);
    // ...
}

// 3. 화면 밖 적 물리 비활성화
if (distanceToPlayer > deactivationRange)
{
    rb.constraints = RigidbodyConstraints2D.FreezeAll;
    enabled = false;
}
```

---

## OnionCat 적용 포인트

### 대쉬 무적 구현
- `Physics2D.IgnoreLayerCollision(Player, Enemy, true/false)`로 대쉬 중 적 레이어 통과
- 벽(Wall 레이어)은 항상 Player와 충돌 유지 → 벽은 통과 불가
- 대쉬 종료 시 반드시 복원 (`false`) 처리 필요

### 투사체 벽 관통 방지
- Projectile Rigidbody2D: BodyType=Kinematic, CollisionDetection=Continuous
- 빠른 투사체도 Continuous 모드로 벽을 건너뛰지 않음

### 패링 시스템
- OnionShield: CircleCollider2D (isTrigger=true), EnemyProjectile 레이어만 감지
- `Vector2.Angle(shieldDir, incomingDir) < 60f`로 방향 패링 윈도우 구현
- 패링 성공 시 투사체 velocity를 반전해 반사 투사체로 전환 가능

### 근접 공격
- AttackPoint 자식 오브젝트에 CircleCollider2D (isTrigger=true) + `OverlapCircleAll`
- `IsInFrontCone()` 함수로 180° 범위 필터링
- Enemy 레이어 마스크 캐싱으로 OverlapCircle 연산 비용 최소화

---

## 참고 링크
- [Rigidbody2D 공식 문서](https://docs.unity3d.com/Manual/class-Rigidbody2D.html)
- [2D Colliders 공식 문서](https://docs.unity3d.com/Manual/Collider2D.html)
- [Physics2D 스크립트 레퍼런스](https://docs.unity3d.com/ScriptReference/Physics2D.html)
- [Collision Detection Modes](https://docs.unity3d.com/Manual/RigidbodyCollisionDetection.html)
- [Physics2D 설정 (Layer Matrix)](https://docs.unity3d.com/Manual/class-Physics2DManager.html)
- [Triggers 공식 문서](https://docs.unity3d.com/Manual/Triggers.html)
