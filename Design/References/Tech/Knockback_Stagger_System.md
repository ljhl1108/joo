# 넉백 & 스태거 시스템 (Knockback & Stagger System)

리서치 날짜: 2026-07-06

## 개요

넉백(Knockback)은 피격 시 캐릭터가 공격 반대 방향으로 밀려나는 물리 반응이다.
스태거(Stagger)는 피격 시 일정 시간 행동이 제한되는 상태(경직)다.

OnionCat에서 이 시스템이 중요한 이유:
- **전투 리듬 형성**: Cat의 근접 공격은 강한 넉백, Onion 원거리는 중간 경직 → 역할 차별화
- **피격 피드백**: 타격감(게임 쥬스)의 핵심 — 넉백이 없으면 타격이 느껴지지 않음
- **전략 도구**: 넉백으로 적을 구덩이/벽으로 밀거나 적끼리 충돌시키는 전술
- **무적 프레임과 연동**: 피격 후 넉백 중 추가 피격 방지 처리 필요

---

## Unity 구현 방법

### 1. 기본 넉백 — Rigidbody2D.AddForce

```csharp
// Enemy 또는 Player에 붙이는 Knockback 컴포넌트
public class KnockbackReceiver : MonoBehaviour
{
    [SerializeField] private float knockbackResistance = 0f; // 0~1, 1이면 면역

    private Rigidbody2D rb;

    void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
    }

    // 공격 측에서 호출
    public void ApplyKnockback(Vector2 direction, float force)
    {
        float actualForce = force * (1f - knockbackResistance);
        rb.linearVelocity = Vector2.zero; // 기존 속도 초기화 후 적용
        rb.AddForce(direction.normalized * actualForce, ForceMode2D.Impulse);
    }
}
```

### 2. 스태거 상태 — 이동/공격 차단

```csharp
public class StaggerController : MonoBehaviour
{
    public bool IsStaggered { get; private set; }

    private Coroutine staggerCoroutine;

    public void ApplyStagger(float duration)
    {
        if (staggerCoroutine != null)
            StopCoroutine(staggerCoroutine);
        staggerCoroutine = StartCoroutine(StaggerRoutine(duration));
    }

    IEnumerator StaggerRoutine(float duration)
    {
        IsStaggered = true;
        // 애니메이션 트리거
        GetComponent<Animator>()?.SetTrigger("Stagger");
        yield return new WaitForSeconds(duration);
        IsStaggered = false;
    }
}
```

```csharp
// 이동/공격 스크립트에서 스태거 체크
void Update()
{
    if (staggerController.IsStaggered) return; // 경직 중 입력 무시
    HandleMovement();
    HandleAttack();
}
```

### 3. 공격 측 넉백 데이터 구조

```csharp
[System.Serializable]
public struct KnockbackData
{
    public float force;          // 넉백 힘
    public float staggerDuration; // 경직 시간 (0이면 경직 없음)
    public bool useAttackerDirection; // true: 공격자→피격자 방향, false: 고정 방향
    public Vector2 fixedDirection;    // useAttackerDirection == false 일 때 사용
}
```

```csharp
// AttackHitbox 또는 DamageDealer에서 사용
void OnTriggerEnter2D(Collider2D other)
{
    if (!other.TryGetComponent<KnockbackReceiver>(out var receiver)) return;

    Vector2 dir = useAttackerDirection
        ? (other.transform.position - transform.position).normalized
        : fixedDirection;

    receiver.ApplyKnockback(dir, knockbackData.force);

    if (other.TryGetComponent<StaggerController>(out var stagger))
        stagger.ApplyStagger(knockbackData.staggerDuration);
}
```

### 4. 넉백 중 무적 프레임 연동

```csharp
// KnockbackReceiver에 무적 처리 추가
public void ApplyKnockback(Vector2 direction, float force, float invincibilityDuration = 0.2f)
{
    float actualForce = force * (1f - knockbackResistance);
    rb.linearVelocity = Vector2.zero;
    rb.AddForce(direction.normalized * actualForce, ForceMode2D.Impulse);

    // 무적 프레임 시작 (IDamageable 인터페이스 또는 별도 컴포넌트)
    GetComponent<InvincibilityHandler>()?.StartInvincibility(invincibilityDuration);
}
```

### 5. 보스/엘리트 적 넉백 면역

```csharp
// 보스는 KnockbackResistance = 1로 설정 (Inspector)
// 또는 스태거만 짧게 적용 (0.1초)
[SerializeField] private float knockbackResistance = 1f; // 보스 기본값
```

### 6. 벽 충돌 시 추가 데미지 (선택 구현)

```csharp
void OnCollisionEnter2D(Collision2D collision)
{
    if (!collision.gameObject.CompareTag("Wall")) return;

    float wallDamage = rb.linearVelocity.magnitude * wallDamageMultiplier;
    GetComponent<IDamageable>()?.TakeDamage(wallDamage);

    // 벽 충돌 파티클 이펙트
    ParticleSystem.Emit(...);
}
```

---

## OnionCat 적용 포인트

### Cat의 근접 vs Onion의 원거리 넉백 차별화
| 공격 | 넉백 힘 | 경직 시간 | 방향 |
|------|---------|----------|------|
| Cat 180° 슬래시 | 강 (15~20) | 0.3초 | 공격 방향 |
| Cat 대시 충돌 | 매우 강 (25~30) | 0.5초 | 대시 방향 |
| Onion 기본 투사체 | 약 (5~8) | 0.15초 | 투사체 방향 |
| Onion 차지 샷 | 중 (12~15) | 0.3초 | 투사체 방향 |
| 패리 반사 | 강 (20) | 0.6초 | 반사 방향 |

### 협력 기회 창출
- Cat 슬래시로 적을 Onion 쪽으로 밀기 → Onion이 차지 샷으로 마무리
- 또는 Onion이 투사체로 적을 Cat 쪽으로 몰기 → Cat이 대시로 일격
- "밀기" 방향 제어가 협력 전략의 핵심이므로 넉백 방향 일관성 중요

### 적별 넉백 저항값 설정
- 일반 잡몹: 저항 0 (잘 밀림)
- 중간 보스급: 저항 0.5 (절반만 밀림)
- 보스: 저항 0.8~1 (경직만, 밀리지 않음)
- 근접 약점 적 (Onion이 못 잡는 적): 저항 0 → Cat 슬래시로 몰아붙이는 재미

### 히트스톱 연동
넉백 적용 전 히트스톱(0.05~0.1초 슬로우)을 먼저 실행하면 타격감 극대화:
```csharp
StartCoroutine(HitstopThenKnockback(0.08f, dir, force));
```

---

## 참고 링크

- Unity Rigidbody2D.AddForce 공식 문서: https://docs.unity3d.com/ScriptReference/Rigidbody2D.AddForce.html
- Unity ForceMode2D: https://docs.unity3d.com/ScriptReference/ForceMode2D.html
- "The Art of Screenshake" GDC Talk (Jan Willem Nijman): https://www.youtube.com/watch?v=AJdEqssNZ-U
- Game Feel Book (Steve Swink) 요약: knockback은 "게임 쥬스"의 핵심 요소
- Unity 2D Physics Best Practices: https://docs.unity3d.com/Manual/2D-physics.html
