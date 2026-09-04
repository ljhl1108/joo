# AoE 데미지 존 시스템 (Area of Effect Damage Zone)

리서치 날짜: 2026-09-04

## 개요

AoE(Area of Effect) 데미지 존은 특정 영역에 순간 또는 지속적인 피해를 주는 시스템이다. 폭발, 화염 웅덩이, 독 구름, 전기 장판 등 다양한 형태로 응용된다. OnionCat에서는 Onion의 패리 반격 폭발, Cat의 슬래시 충격파, 폭탄 아이템, 트랩 방 환경 위험 요소에 직접 활용할 수 있다.

---

## Unity 구현 방법

### 방식 1: 순간 범위 피해 (Instant AoE Burst)
폭탄 폭발, 패리 반격 등 한 순간에 발동하는 AoE.

```csharp
public static class AoEHelper
{
    // center 위치에서 radius 반경 내 targetLayer 오브젝트에 피해
    public static void ExplodeAoE(Vector2 center, float radius, float damage, LayerMask targetLayer)
    {
        Collider2D[] hits = Physics2D.OverlapCircleAll(center, radius, targetLayer);
        foreach (var hit in hits)
        {
            if (!hit.TryGetComponent<IDamageable>(out var damageable)) continue;

            // 거리 비례 피해 감소 (중심에 가까울수록 강함)
            float dist = Vector2.Distance(center, hit.transform.position);
            float falloff = Mathf.Clamp01(1f - (dist / radius));
            damageable.TakeDamage(damage * falloff);

            // 넉백
            var rb = hit.GetComponent<Rigidbody2D>();
            if (rb != null)
            {
                Vector2 dir = ((Vector2)hit.transform.position - center).normalized;
                rb.AddForce(dir * (1f - falloff) * 10f, ForceMode2D.Impulse);
            }
        }
    }
}
```

**사용 예시:**
```csharp
// Onion 패리 성공 시
void OnParrySuccess(Vector2 position)
{
    AoEHelper.ExplodeAoE(position, radius: 2.5f, damage: 30f, targetLayer: enemyLayer);
    // 이펙트 재생
    Instantiate(parryExplosionVFX, position, Quaternion.identity);
}
```

---

### 방식 2: 지속 데미지 존 (Persistent Zone — OverlapCircle 방식)
화염 장판, 독 구름 등 일정 시간 동안 영역 내 적에게 지속 피해.

```csharp
public class DamageZone : MonoBehaviour
{
    [SerializeField] private float damagePerSecond = 10f;
    [SerializeField] private float duration = 3f;
    [SerializeField] private float radius = 1.5f;
    [SerializeField] private LayerMask targetLayer;

    private float _remainingTime;

    void OnEnable()
    {
        _remainingTime = duration;
    }

    void Update()
    {
        _remainingTime -= Time.deltaTime;
        if (_remainingTime <= 0f)
        {
            gameObject.SetActive(false); // 오브젝트 풀 반환
            return;
        }

        Collider2D[] hits = Physics2D.OverlapCircleAll(transform.position, radius, targetLayer);
        foreach (var hit in hits)
        {
            if (hit.TryGetComponent<IDamageable>(out var d))
                d.TakeDamage(damagePerSecond * Time.deltaTime);
        }
    }
}
```

---

### 방식 3: Trigger 기반 지속 존 (성능 우수, 권장)
OnTrigger 이벤트로 존 안에 있는 대상만 추적. OverlapCircle 반복 호출보다 효율적.

```csharp
public class TriggerDamageZone : MonoBehaviour
{
    [SerializeField] private float damagePerSecond = 10f;
    [SerializeField] private float duration = 3f;

    private readonly HashSet<IDamageable> _inZone = new();
    private float _timer;

    void OnEnable()
    {
        _timer = duration;
        _inZone.Clear();
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.TryGetComponent<IDamageable>(out var d))
            _inZone.Add(d);
    }

    void OnTriggerExit2D(Collider2D other)
    {
        if (other.TryGetComponent<IDamageable>(out var d))
            _inZone.Remove(d);
    }

    void Update()
    {
        _timer -= Time.deltaTime;
        if (_timer <= 0f)
        {
            gameObject.SetActive(false);
            return;
        }

        foreach (var d in _inZone)
            d.TakeDamage(damagePerSecond * Time.deltaTime);
    }
}
```

> `CircleCollider2D`를 `isTrigger = true`로 설정해야 한다.

---

### 방식 4: 오브젝트 풀과 연계

```csharp
public class BombItem : MonoBehaviour
{
    [SerializeField] private GameObject damageZonePrefab;

    void Explode()
    {
        // ObjectPool에서 가져오거나 Instantiate
        var zone = ObjectPool.Instance.Get("DamageZone");
        zone.transform.position = transform.position;
        zone.SetActive(true);
        // zone 내부에서 duration 후 자동 반환
    }
}
```

---

### 방식 5: 시각 연출 연계

```csharp
// AnimationCurve로 폭발 반경 성장
public class ExpandingAoE : MonoBehaviour
{
    [SerializeField] private AnimationCurve radiusCurve;
    [SerializeField] private float duration = 0.5f;
    private CircleCollider2D _col;
    private SpriteRenderer _spr;
    private float _t;

    void Awake()
    {
        _col = GetComponent<CircleCollider2D>();
        _spr = GetComponent<SpriteRenderer>();
    }

    void Update()
    {
        _t += Time.deltaTime / duration;
        float r = radiusCurve.Evaluate(_t);
        _col.radius = r;
        _spr.transform.localScale = Vector3.one * (r * 2f);
        if (_t >= 1f) gameObject.SetActive(false);
    }
}
```

---

## OnionCat 적용 포인트

### 1. Onion 패리 반격 폭발
- 패리 성공 직후 `AoEHelper.ExplodeAoE()` 호출
- 반경 2~3 유닛, 피해 = 막은 투사체 피해량의 150%
- 근접 적에게 강한 패리 인센티브 → 능동적 방어 강조

### 2. Cat 업그레이드: 충격파 슬래시
- 특정 업그레이드 시 Cat 슬래시 → 전방 AoE 충격파 추가
- `Physics2D.OverlapCircleAll` → 전방 반원 필터링
  ```csharp
  Vector2 facingDir = cat.FacingDirection;
  foreach (var hit in hits)
  {
      Vector2 toHit = (hit.transform.position - transform.position).normalized;
      if (Vector2.Dot(toHit, facingDir) > 0f) // 전방만
          hit.GetComponent<IDamageable>()?.TakeDamage(damage);
  }
  ```

### 3. 트랩 방 환경 위험 요소
- 불 기둥, 독 웅덩이, 전기 장판 등을 `TriggerDamageZone`으로 구현
- 플레이어와 적 모두에게 피해 → 협력 이동 필요
- Cat은 대시로 통과, Onion은 Cat이 안전 경로 확보해야 통과

### 4. 자폭형 적 설계
- 특정 적(Kamikaze 타입) 사망 시 `ExplodeAoE()` 호출
- 플레이어가 AoE 범위 밖으로 대피해야 → 긴장감 조성

### 5. 보스 2페이즈 전환
- 보스가 특정 HP 이하 → 대규모 AoE 폭발 후 2페이즈 시작
- `ExpandingAoE`로 시각적 경고 → 플레이어 대피 유도

---

## 레이어 설정 주의

```
Layers:
  Enemy   → 적 레이어
  Player  → 플레이어 레이어
  Hazard  → 환경 위험 레이어

AoE 충돌 설정:
  적 AoE    → Player 레이어만 감지
  플레이어 AoE → Enemy 레이어만 감지
  환경 AoE  → Player + Enemy 모두 감지
```

---

## 참고 링크

- Unity Docs - Physics2D.OverlapCircleAll: https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircleAll.html
- Unity Docs - CircleCollider2D: https://docs.unity3d.com/Manual/class-CircleCollider2D.html
- Unity Docs - OnTriggerEnter2D: https://docs.unity3d.com/ScriptReference/MonoBehaviour.OnTriggerEnter2D.html
- Unity Learn - 2D Physics: https://learn.unity.com/tutorial/2d-physics
- 유튜브 "Unity 2D AoE explosion damage" 검색으로 구현 예시 다수 확인 가능
