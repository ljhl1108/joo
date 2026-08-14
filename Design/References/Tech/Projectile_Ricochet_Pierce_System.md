# 투사체 반사 & 관통 시스템 (Projectile Ricochet & Pierce)

리서치 날짜: 2026-08-14

## 개요

로그라이크에서 흔히 등장하는 두 가지 고급 투사체 행동:
- **반사 (Ricochet)**: 벽(또는 방패)에 닿으면 물리 각도로 튕겨나감
- **관통 (Pierce)**: 적을 통과하며 뒤의 적에게도 대미지

Enter the Gungeon의 "바운서 탄환", Dead Cells의 "관통 화살" 같은 업그레이드가 대표 예시.  
OnionCat에서는 P2(파)의 원거리 투사체가 업그레이드를 통해 두 특성을 얻는 시스템에 활용.

---

## Unity 구현 방법

### 반사 (Ricochet) — 벽 반사 각도 계산

핵심 원리: 입사 방향 벡터를 충돌 노말로 Reflect.

```csharp
// ProjectileRicochet.cs
public class ProjectileRicochet : MonoBehaviour
{
    [SerializeField] private int maxBounces = 3;
    private int bounceCount;
    private Vector2 currentDirection;
    private Rigidbody2D rb;

    void Awake()
    {
        rb = GetComponent<Rigidbody2D>();
        currentDirection = transform.right; // 발사 방향
    }

    void OnCollisionEnter2D(Collision2D col)
    {
        if (col.gameObject.CompareTag("Wall"))
        {
            if (bounceCount >= maxBounces)
            {
                Destroy(gameObject);
                return;
            }
            // 반사 벡터 계산
            Vector2 normal = col.contacts[0].normal;
            currentDirection = Vector2.Reflect(currentDirection, normal);
            rb.linearVelocity = currentDirection * rb.linearVelocity.magnitude;
            transform.right = currentDirection;
            bounceCount++;
        }
    }
}
```

**주의**: `Rigidbody2D.Collision Detection Mode`를 `Continuous`로 설정해야 얇은 벽 통과 방지.

---

### 관통 (Pierce) — 중복 피해 방지

```csharp
// ProjectilePierce.cs
public class ProjectilePierce : MonoBehaviour
{
    [SerializeField] private int maxPierceCount = 3; // 관통 가능 적 수
    private int pierceLeft;
    private HashSet<int> hitEnemyIds = new();

    void Awake() => pierceLeft = maxPierceCount;

    void OnTriggerEnter2D(Collider2D col)
    {
        if (!col.CompareTag("Enemy")) return;

        int id = col.gameObject.GetInstanceID();
        if (hitEnemyIds.Contains(id)) return; // 이미 맞은 적 재피해 방지
        hitEnemyIds.Add(id);

        col.GetComponent<EnemyHealth>()?.TakeDamage(damage);

        pierceLeft--;
        if (pierceLeft <= 0) Destroy(gameObject);
    }
}
```

**관통 탄은 Trigger 사용**, 반사 탄은 Collision 사용 — 물리 응답 방식이 다르기 때문.

---

### 콤보: 반사 + 관통

두 컴포넌트를 같은 Prefab에 부착. Collider 설정:
- 벽 레이어와는 `Collision`
- 적 레이어와는 `Trigger`

Layer Collision Matrix (Edit → Project Settings → Physics 2D):
```
Projectile ↔ Wall: Collision ON
Projectile ↔ Enemy: Trigger ON
Wall ↔ Enemy: OFF
```

---

### 오브젝트 풀링과 연동

반사/관통 탄은 수명이 길어 `Destroy` 대신 풀 반환 필수.

```csharp
// 풀 반환 전 상태 초기화
public void ResetState()
{
    bounceCount = 0;
    pierceLeft = maxPierceCount;
    hitEnemyIds.Clear();
}
```

---

### 업그레이드 시스템 연동 예시

```csharp
// 업그레이드 적용 시 Prefab 교체 또는 컴포넌트 파라미터 수정
public void ApplyRicochetUpgrade(ProjectileConfig config)
{
    var ricochet = GetComponent<ProjectileRicochet>();
    if (ricochet == null) ricochet = gameObject.AddComponent<ProjectileRicochet>();
    ricochet.maxBounces = config.bounceCount;
}
```

---

## OnionCat 적용 포인트

### P2 투사체 업그레이드 트리
기본 투사체(직선, 1관통 없음) → 업그레이드로 성질 추가:

| 업그레이드 | 효과 | 구현 |
|-----------|------|------|
| 탄성 씨앗 | 벽 1회 반사 | `maxBounces = 1` |
| 고무 파 | 벽 3회 반사 | `maxBounces = 3` |
| 뾰족 잎사귀 | 적 2명 관통 | `maxPierceCount = 2` |
| 무한 관통 | 모든 적 관통, 1회 반사 | `maxPierceCount = 99, maxBounces = 1` |

### 약점 타입과 조합
- 원거리에만 약점인 적 + 벽 뒤에 숨은 적 → 반사 탄환으로 뒤에서 명중
- P1 근접 공격으로 적을 밀면 → P2 관통탄이 일렬로 늘어선 적들 관통

### 파티클 이펙트 포인트
- 벽 반사 시: `Instantiate(sparkParticle, hitPoint, Quaternion.identity)`
- 관통 시: 적 위에 `GrazeEffect` 짧은 파티클

---

## 참고 링크

- Unity Physics 2D 공식 문서: https://docs.unity3d.com/Manual/Physics2DReference.html
- Vector2.Reflect API: https://docs.unity3d.com/ScriptReference/Vector2.Reflect.html
- Enter the Gungeon Bouncer Bullets 분석: https://www.reddit.com/r/gamedev/comments/etg_ricochet_bullets
- Unity 탄환 관통 구현 튜토리얼: https://www.youtube.com/results?search_query=unity+pierce+projectile+2d
- Continuous Collision Detection: https://docs.unity3d.com/Manual/ContinuousCollisionDetection.html
