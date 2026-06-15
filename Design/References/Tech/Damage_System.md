# 데미지 시스템 (Damage System)

리서치 날짜: 2026-06-15

## 개요

데미지 시스템은 "누가 누구에게 얼마나 피해를 주는가"와 그 결과(체력 감소, 넉백, 무적 시간, 사망)를 처리하는 게임의 핵심 기반 시스템. OnionCat에서는 Cat·Crop의 공유 체력, 각자 다른 데미지 타입(근접/원거리), Cat의 무적 대시, Crop의 패리 등 복잡한 상호작용을 모두 이 시스템이 조율해야 함.

잘 설계된 데미지 시스템의 특성:
- 피격·데미지 로직이 한 곳에 집중(IDamageable 인터페이스)
- 무적 프레임(i-frames)으로 연속 피격 방지
- 넉백으로 타격감 부여
- 데미지 타입으로 적 약점 시스템 구현 가능

---

## Unity 구현 방법

### 1. IDamageable 인터페이스

```csharp
// IDamageable.cs
public interface IDamageable
{
    void TakeDamage(int damage, DamageType type, Vector2 knockbackDir, float knockbackForce);
    bool IsInvincible { get; }
}

public enum DamageType
{
    Melee,      // 근접 — Cat의 슬래시
    Ranged,     // 원거리 — 투사체
    Any,        // 모든 타입에 피해
    Environment // 함정·환경 데미지
}
```

### 2. 체력 컴포넌트 (HealthComponent)

```csharp
// HealthComponent.cs
using System;
using UnityEngine;

public class HealthComponent : MonoBehaviour, IDamageable
{
    [SerializeField] private int maxHealth = 100;
    [SerializeField] private float invincibleDuration = 0.5f;  // 피격 후 무적 시간(초)
    [SerializeField] private DamageType weakness = DamageType.Any;  // 약점 타입

    public int CurrentHealth { get; private set; }
    public bool IsInvincible { get; private set; }

    public event Action<int, int> OnHealthChanged;  // (current, max)
    public event Action OnDeath;

    private Rigidbody2D _rb;
    private SpriteRenderer _sr;

    private void Awake()
    {
        CurrentHealth = maxHealth;
        _rb = GetComponent<Rigidbody2D>();
        _sr = GetComponent<SpriteRenderer>();
    }

    public void TakeDamage(int damage, DamageType type, Vector2 knockbackDir, float knockbackForce)
    {
        if (IsInvincible) return;

        // 약점 타입이 아니면 피해 무효
        if (weakness != DamageType.Any && weakness != type) return;

        CurrentHealth = Mathf.Max(0, CurrentHealth - damage);
        OnHealthChanged?.Invoke(CurrentHealth, maxHealth);

        if (knockbackForce > 0f && _rb != null)
            ApplyKnockback(knockbackDir, knockbackForce);

        StartCoroutine(InvincibilityCoroutine());
        StartCoroutine(HitFlashCoroutine());

        if (CurrentHealth <= 0)
            OnDeath?.Invoke();
    }

    public void Heal(int amount)
    {
        CurrentHealth = Mathf.Min(maxHealth, CurrentHealth + amount);
        OnHealthChanged?.Invoke(CurrentHealth, maxHealth);
    }

    // 외부에서 무적 상태 직접 제어 (Cat 대시 등)
    public void SetInvincible(bool value) => IsInvincible = value;

    private void ApplyKnockback(Vector2 dir, float force)
    {
        _rb.linearVelocity = Vector2.zero;   // 기존 속도 초기화 후 힘 적용
        _rb.AddForce(dir.normalized * force, ForceMode2D.Impulse);
    }

    private System.Collections.IEnumerator InvincibilityCoroutine()
    {
        IsInvincible = true;
        yield return new WaitForSeconds(invincibleDuration);
        IsInvincible = false;
    }

    // 피격 시 흰색 플래시
    private System.Collections.IEnumerator HitFlashCoroutine()
    {
        _sr.color = Color.white;
        yield return new WaitForSeconds(0.08f);
        _sr.color = Color.red;
        yield return new WaitForSeconds(0.08f);
        _sr.color = Color.white;
    }
}
```

### 3. 데미지 발사체 / 히트박스에서 TakeDamage 호출

```csharp
// EnemyProjectile.cs (투사체 예시)
private void OnTriggerEnter2D(Collider2D other)
{
    IDamageable target = other.GetComponent<IDamageable>();
    if (target == null) return;

    Vector2 knockbackDir = (other.transform.position - transform.position).normalized;
    target.TakeDamage(damage, DamageType.Ranged, knockbackDir, knockbackForce);

    gameObject.SetActive(false);  // 오브젝트 풀로 반환
}

// CatMeleeAttack.cs (근접 슬래시 예시)
private void OnTriggerEnter2D(Collider2D other)
{
    if (other.CompareTag("Enemy"))
    {
        IDamageable target = other.GetComponent<IDamageable>();
        Vector2 knockbackDir = (other.transform.position - transform.position).normalized;
        target?.TakeDamage(slashDamage, DamageType.Melee, knockbackDir, 5f);
    }
}
```

### 4. 데미지 숫자 UI (Floating Damage Text)

```csharp
// DamageNumberSpawner.cs
public class DamageNumberSpawner : MonoBehaviour
{
    [SerializeField] private GameObject damageTextPrefab;  // TMPro 텍스트 포함 프리팹
    private static DamageNumberSpawner _instance;
    public static DamageNumberSpawner Instance => _instance;

    private void Awake() => _instance = this;

    public void Spawn(Vector3 worldPos, int damage, Color color)
    {
        var obj = Instantiate(damageTextPrefab, worldPos + Vector3.up * 0.5f, Quaternion.identity);
        obj.GetComponent<DamageNumber>().Init(damage, color);
    }
}

// DamageNumber.cs — 위로 떠오르며 사라짐
public class DamageNumber : MonoBehaviour
{
    public void Init(int damage, Color color)
    {
        var tmp = GetComponent<TMPro.TextMeshPro>();
        tmp.text = damage.ToString();
        tmp.color = color;
        StartCoroutine(FloatAndFade());
    }

    private System.Collections.IEnumerator FloatAndFade()
    {
        float elapsed = 0f, duration = 0.7f;
        Vector3 startPos = transform.position;
        var tmp = GetComponent<TMPro.TextMeshPro>();

        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / duration;
            transform.position = startPos + Vector3.up * (t * 0.8f);
            tmp.color = new Color(tmp.color.r, tmp.color.g, tmp.color.b, 1f - t);
            yield return null;
        }
        Destroy(gameObject);
    }
}
```

### 5. 무적 프레임 레이어 방식 (선택적)

코루틴 대신 레이어를 이용한 무적 구현 — 충돌 자체를 끊는 방식:

```csharp
// 무적 중 플레이어-적 투사체 충돌 레이어 무시
private System.Collections.IEnumerator InvincibilityCoroutine()
{
    IsInvincible = true;
    Physics2D.IgnoreLayerCollision(LayerMask.NameToLayer("Player"),
                                   LayerMask.NameToLayer("EnemyProjectile"), true);
    yield return new WaitForSeconds(invincibleDuration);
    Physics2D.IgnoreLayerCollision(LayerMask.NameToLayer("Player"),
                                   LayerMask.NameToLayer("EnemyProjectile"), false);
    IsInvincible = false;
}
```

> 주의: Physics2D.IgnoreLayerCollision은 전역 설정. 여러 플레이어가 있을 때는 개별 Collider2D.enabled 또는 레이어 스왑 방식 사용 권장.

---

## OnionCat 적용 포인트

### 1. 공유 체력 vs. 개별 체력

Cat과 Crop은 **하나의 몸**이므로 공유 체력이 자연스러움:

```csharp
// SharedPlayerHealth.cs — 하나의 HealthComponent를 Cat·Crop 모두가 참조
public class SharedPlayerHealth : HealthComponent
{
    // Cat과 Crop 모두 이 컴포넌트를 통해 피해를 받음
    // Cat 몸체 콜라이더, Crop 콜라이더 둘 다 이 컴포넌트 TakeDamage 호출
}
```

### 2. Cat 무적 대시 연동

```csharp
// CatDash.cs
private IEnumerator DashCoroutine(Vector2 direction)
{
    _health.SetInvincible(true);   // 무적 ON
    _rb.AddForce(direction * dashForce, ForceMode2D.Impulse);
    yield return new WaitForSeconds(dashDuration);
    _health.SetInvincible(false);  // 무적 OFF
}
```

### 3. Crop 패리 → 피해 반사

```csharp
// CropShield.cs
private void OnTriggerEnter2D(Collider2D other)
{
    if (other.TryGetComponent<EnemyProjectile>(out var proj))
    {
        if (_isParrying)
        {
            // 패리 성공: 투사체 반사
            proj.Reflect();
            // 히트스톱 + 화면 진동 등 피드백
        }
        else
        {
            // 방어막만: 피해 감소 또는 차단
            _sharedHealth.TakeDamage(proj.damage / 2, DamageType.Ranged, 
                                      Vector2.zero, 0f);
        }
    }
}
```

### 4. 적 약점 타입 시스템

`DamageType.Melee` / `DamageType.Ranged`를 이용해 약점 적 구현:
- `weakness = DamageType.Melee` → Crop의 투사체로는 피해 0
- `weakness = DamageType.Ranged` → Cat의 슬래시로는 피해 0
- 이를 적 디자인 레벨에서 `[SerializeField]`로 설정

### 5. 데미지 숫자 색상 코딩

| 상황 | 색상 |
|-----|-----|
| 근접 데미지 | 주황색 |
| 원거리 데미지 | 하늘색 |
| 크리티컬/약점 공격 | 노란색 + 큰 폰트 |
| 플레이어 피격 | 빨간색 |
| 무효(면역) | 회색 "IMMUNE" 텍스트 |

---

## 참고 링크

- Unity 공식 — Rigidbody2D.AddForce: https://docs.unity3d.com/ScriptReference/Rigidbody2D.AddForce.html
- Unity 공식 — Physics2D.IgnoreLayerCollision: https://docs.unity3d.com/ScriptReference/Physics2D.IgnoreLayerCollision.html
- 무적 프레임(i-frames) 설계 가이드: https://www.gamedeveloper.com/design/the-design-of-invincibility-frames
- 데미지 숫자 구현 튜토리얼: https://www.youtube.com/watch?v=iD1_JczQcFY
- Brackeys — Health System in Unity: https://www.youtube.com/watch?v=BLfNP4Sc_iA
- 넉백 물리 구현: https://gamedev.stackexchange.com/questions/76792/how-do-i-apply-knockback-to-a-player-in-unity
