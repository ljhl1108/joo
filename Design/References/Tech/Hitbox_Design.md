# 히트박스 설계 (Hitbox Design)

## 개요

### Hitbox vs Hurtbox 기본 개념

픽셀아트 액션 게임에서 두 가지 충돌 영역을 반드시 구분해야 한다.

| 용어 | 역할 | Unity 구현 |
|------|------|-----------|
| **Hitbox** | 공격이 피해를 입히는 영역 (칼날, 투사체 앞부분) | `IsTrigger = true`, 공격 오브젝트에 부착 |
| **Hurtbox** | 캐릭터가 피해를 받는 영역 (몸통, 취약 부위) | `IsTrigger = true`, 캐릭터 본체에 부착 |

두 영역이 겹쳤을 때만 피해가 발생한다. 둘 다 Trigger이므로 물리적 밀어냄 없이 오버랩만 감지한다.

### 너그러운 히트박스 (Lenient Hitbox) 철학

**핵심 원칙:** 히트박스는 스프라이트 비주얼보다 **작게** 만든다.

Hollow Knight, Celeste 등 유명 픽셀아트 게임이 이 원칙을 따른다.

1. **플레이어 좌절 방지** — "나는 맞지 않았는데 피해를 받았다"는 느낌 제거
2. **공격의 손맛** — 적을 공격할 때 판정이 넉넉하면 타격이 시원하게 느껴짐
3. **픽셀 단위 오차 보정** — 저해상도 스프라이트는 경계가 불명확 → 히트박스를 약 10~20% 줄여야 의도대로 느껴짐

**실용 규칙:**
- 플레이어 Hurtbox = 스프라이트의 약 70~80% 크기
- 적 Hurtbox = 스프라이트의 약 85~90% (공격이 쉽게 들어가도록)
- Cat 슬래시 반경 = 스프라이트보다 약간 넓게 (시원한 타격감)
- 투사체 콜라이더 = 투사체 스프라이트보다 약간 작게

---

## Unity 구현 방법

### 1. Physics 2D Layer 설정

**레이어 생성 경로:** `Edit → Project Settings → Tags and Layers`

OnionCat 권장 레이어 구성:

| 레이어 번호 | 레이어 이름 | 사용 오브젝트 |
|------------|------------|-------------|
| 6 | `Player` | 플레이어 본체 (물리 이동) |
| 7 | `Enemy` | 적 본체 |
| 8 | `PlayerHitbox` | 플레이어의 공격 판정 |
| 9 | `EnemyHitbox` | 적의 공격 판정 |
| 10 | `PlayerHurtbox` | 플레이어의 피격 판정 |
| 11 | `EnemyHurtbox` | 적의 피격 판정 |
| 12 | `Projectile` | Crop의 투사체 |
| 13 | `Shield` | Crop의 방패 / 패리 판정 |
| 14 | `Wall` | 타일맵 벽, 장애물 |

**Layer Collision Matrix 설정:** `Edit → Project Settings → Physics 2D → Layer Collision Matrix`

활성화해야 할 상호작용:

| 레이어 A | ↔ | 레이어 B | 이유 |
|---------|---|---------|------|
| `PlayerHitbox` | ↔ | `EnemyHurtbox` | 플레이어 공격 → 적 피격 |
| `EnemyHitbox` | ↔ | `PlayerHurtbox` | 적 공격 → 플레이어 피격 |
| `Projectile` | ↔ | `EnemyHurtbox` | 투사체 → 적 피격 |
| `Projectile` | ↔ | `Wall` | 투사체가 벽에서 소멸 |
| `Shield` | ↔ | `EnemyHitbox` | 방패/패리가 적 공격 감지 |
| `Player` | ↔ | `Wall` | 플레이어 벽 충돌 |
| `Enemy` | ↔ | `Wall` | 적 벽 충돌 |

비활성화해야 할 주요 조합:

| 레이어 A | ↔ | 레이어 B | 이유 |
|---------|---|---------|------|
| `PlayerHitbox` | ↔ | `PlayerHurtbox` | 자기 공격이 자신에게 피해 주지 않도록 |
| `EnemyHitbox` | ↔ | `EnemyHurtbox` | 적끼리 아군 피해 방지 |
| `Projectile` | ↔ | `Player` | 투사체가 플레이어 본체를 통과 |

---

### 2. Trigger vs Collider 선택 기준

| 상황 | Collider (isTrigger=false) | Trigger (isTrigger=true) |
|------|--------------------------|--------------------------|
| 플레이어/적 본체 이동 | ✅ (벽에 막혀야 함) | ❌ |
| 벽, 바닥, 장애물 | ✅ | ❌ |
| 공격 판정 (Hitbox) | ❌ | ✅ (물리 밀어냄 불필요) |
| 피격 판정 (Hurtbox) | ❌ | ✅ |
| 투사체 | Rigidbody2D + Trigger 결합 | ✅ |
| 방패/패리 | ❌ | ✅ |

**중요:** `OnTriggerEnter2D`가 발동하려면 충돌하는 두 오브젝트 중 최소 하나에 `Rigidbody2D`가 있어야 한다. Hitbox/Hurtbox 오브젝트에는 `Rigidbody2D (Body Type: Kinematic)`을 추가한다.

---

### 3. 기반 인터페이스 & 공통 구조

```csharp
// IDamageable.cs
public interface IDamageable
{
    void TakeDamage(float amount, Vector2 knockbackDir);
}
```

```csharp
// Hurtbox.cs
using UnityEngine;

public class Hurtbox : MonoBehaviour
{
    // [유니티 에디터에서 드래그 앤 드롭 설정 필요] — IDamageable을 구현한 컴포넌트 할당
    [SerializeField] private MonoBehaviour damageableTarget;
    private IDamageable _damageable;

    private void Awake()
    {
        _damageable = damageableTarget as IDamageable;
        if (_damageable == null)
            Debug.LogError($"{name}: damageableTarget이 IDamageable을 구현하지 않습니다.");
    }

    public void ReceiveHit(float damage, Vector2 knockbackDir)
    {
        _damageable?.TakeDamage(damage, knockbackDir);
    }
}
```

```csharp
// Hitbox.cs
using UnityEngine;
using System.Collections.Generic;

public class Hitbox : MonoBehaviour
{
    [SerializeField] private float damage = 10f;
    private readonly HashSet<Collider2D> _hitTargets = new HashSet<Collider2D>();

    private void OnEnable()
    {
        _hitTargets.Clear();
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (_hitTargets.Contains(other)) return;

        Hurtbox hurtbox = other.GetComponent<Hurtbox>();
        if (hurtbox != null)
        {
            _hitTargets.Add(other);
            Vector2 knockbackDir = (other.transform.position - transform.position).normalized;
            hurtbox.ReceiveHit(damage, knockbackDir);
        }
    }
}
```

---

### 4. Cat — 180° 근접 슬래시 히트박스

`Physics2D.OverlapCircleAll`로 반경 내 콜라이더를 탐지한 뒤, `Vector2.Angle`로 전방 180° 내 대상만 필터링한다.

```csharp
// CatMeleeAttack.cs
using UnityEngine;
using UnityEngine.InputSystem;

public class CatMeleeAttack : MonoBehaviour
{
    [SerializeField] private float attackRadius = 1.5f;
    [SerializeField] private float attackAngle = 180f;
    [SerializeField] private float attackDamage = 25f;
    // [유니티 에디터에서 드래그 앤 드롭 설정 필요] — EnemyHurtbox 레이어 마스크 설정
    [SerializeField] private LayerMask enemyHurtboxLayer;

    private InputAction _attackAction;

    private void Awake()
    {
        var playerInput = GetComponent<PlayerInput>();
        _attackAction = playerInput.actions["Attack"];
    }

    private void OnEnable() => _attackAction.performed += _ => PerformSlash();
    private void OnDisable() => _attackAction.performed -= _ => PerformSlash();

    private void PerformSlash()
    {
        Vector2 forward = transform.up;
        Collider2D[] hits = Physics2D.OverlapCircleAll(transform.position, attackRadius, enemyHurtboxLayer);

        foreach (Collider2D hit in hits)
        {
            Vector2 dirToTarget = (hit.transform.position - transform.position).normalized;
            float angle = Vector2.Angle(forward, dirToTarget);

            if (angle <= attackAngle / 2f)
            {
                Hurtbox hurtbox = hit.GetComponent<Hurtbox>();
                hurtbox?.ReceiveHit(attackDamage, dirToTarget);
            }
        }
    }

    private void OnDrawGizmosSelected()
    {
        Gizmos.color = new Color(1f, 0f, 0f, 0.3f);
        Gizmos.DrawWireSphere(transform.position, attackRadius);
    }
}
```

**팁:** `PerformSlash()`를 Animation Event로 호출하면 슬래시 애니메이션의 정확한 프레임에 판정을 맞출 수 있다.

---

### 5. Crop — 원거리 투사체

```csharp
// Projectile.cs
using UnityEngine;

public class Projectile : MonoBehaviour
{
    [SerializeField] private float speed = 8f;
    [SerializeField] private float damage = 15f;
    [SerializeField] private float lifetime = 5f;

    private Rigidbody2D _rb;

    private void Awake()
    {
        _rb = GetComponent<Rigidbody2D>();
    }

    private void Start()
    {
        _rb.velocity = transform.right * speed;
        Destroy(gameObject, lifetime);
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.gameObject.layer == LayerMask.NameToLayer("Wall"))
        {
            Destroy(gameObject);
            return;
        }

        Hurtbox hurtbox = other.GetComponent<Hurtbox>();
        if (hurtbox != null)
        {
            hurtbox.ReceiveHit(damage, _rb.velocity.normalized);
            Destroy(gameObject);
        }
    }
}
```

---

### 6. Crop — 방향 방패 + 패리

```csharp
// ShieldController.cs
using UnityEngine;
using UnityEngine.InputSystem;
using System.Collections;

public class ShieldController : MonoBehaviour
{
    [SerializeField] private float parryWindow = 0.25f;

    private bool _isBlocking;
    private bool _isParrying;
    private Coroutine _parryCoroutine;
    private InputAction _blockAction;

    private void Awake()
    {
        var playerInput = GetComponentInParent<PlayerInput>();
        _blockAction = playerInput.actions["Block"];
    }

    private void OnEnable()
    {
        _blockAction.started += OnBlockStarted;
        _blockAction.canceled += OnBlockCanceled;
    }

    private void OnDisable()
    {
        _blockAction.started -= OnBlockStarted;
        _blockAction.canceled -= OnBlockCanceled;
    }

    private void OnBlockStarted(InputAction.CallbackContext ctx)
    {
        _isBlocking = true;
        gameObject.SetActive(true);
        if (_parryCoroutine != null) StopCoroutine(_parryCoroutine);
        _parryCoroutine = StartCoroutine(ParryWindowCoroutine());
    }

    private void OnBlockCanceled(InputAction.CallbackContext ctx)
    {
        _isBlocking = false;
        gameObject.SetActive(false);
    }

    private IEnumerator ParryWindowCoroutine()
    {
        _isParrying = true;
        yield return new WaitForSeconds(parryWindow);
        _isParrying = false;
    }

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (_isParrying)
        {
            // 패리 성공 — 반격 이펙트, 사운드 재생, 적 스턴 처리
            Debug.Log("패리 성공!");
        }
        else if (_isBlocking)
        {
            // 일반 블록 — 피해 감소/무효
            Debug.Log("블록!");
        }
    }

    public void SetShieldDirection(Vector2 direction)
    {
        if (direction == Vector2.zero) return;
        float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
        transform.localRotation = Quaternion.Euler(0f, 0f, angle);
    }
}
```

---

### 7. 무적 대시 — Hurtbox 비활성화

```csharp
// CatDash.cs (일부)
private IEnumerator DashCoroutine()
{
    _isDashing = true;
    // [유니티 에디터에서 드래그 앤 드롭 설정 필요] — playerHurtbox 필드에 Hurtbox Collider 할당
    if (playerHurtbox != null) playerHurtbox.enabled = false;

    _rb.velocity = transform.up * dashSpeed;
    yield return new WaitForSeconds(dashDuration);

    if (playerHurtbox != null) playerHurtbox.enabled = true;
    _isDashing = false;
}
```

---

## OnionCat 적용 포인트

| 항목 | 적용 내용 |
|------|---------|
| **레이어 설정** | 위 표대로 9개 레이어 생성 후 Layer Collision Matrix 설정 — 자기 공격에 자신이 맞지 않도록 |
| **Cat 슬래시** | `OverlapCircleAll` + 각도 필터링으로 180° 판정 구현. Animation Event로 정확한 판정 프레임 연동 |
| **Crop 투사체** | 프리팹에 `Rigidbody2D (Gravity Scale: 0)` + `CircleCollider2D (isTrigger=true)` 조합 |
| **패리 타이밍** | 방패 활성화 직후 0.2~0.3초 윈도우 내 공격 감지 시 패리. 플레이 테스트로 값 조정 |
| **무적 대시** | 대시 코루틴 내에서 PlayerHurtbox Collider를 `enabled = false/true`로 토글 |
| **너그러운 히트박스** | 플레이어 Hurtbox = 스프라이트 70%, 적 Hurtbox = 스프라이트 85~90% |
| **IDamageable** | EnemyController, CatHealth, CropHealth 모두 IDamageable 구현 → 코드 통일성 확보 |

**적 타입별 취약점 구현 힌트:**
```csharp
public enum DamageType { Melee, Ranged }

// Hurtbox.ReceiveHit에 DamageType 파라미터 추가
// 각 적의 IDamageable.TakeDamage에서 자신의 weakness와 비교해 피해량 결정
```

---

## 참고 링크

- [Physics 2D Layer Collision Matrix — Unity Manual](https://docs.unity3d.com/Manual/LayerBasedCollision.html)
- [OnTriggerEnter2D — Unity Scripting API](https://docs.unity3d.com/ScriptReference/MonoBehaviour.OnTriggerEnter2D.html)
- [Physics2D.OverlapCircleAll — Unity Scripting API](https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircleAll.html)
- [Rigidbody 2D — Unity Manual](https://docs.unity3d.com/530/Documentation/Manual/class-Rigidbody2D.html)
- [HitBox Attack System in Unity — Gabriel Perez (Medium)](https://sleepingdaemon.medium.com/hitbox-attack-system-in-unity-4722664f65c3)
- [Setting Up a Hitbox Attack System in Unity2D — Marcus Ansley (Medium)](https://m-ansley.medium.com/setting-up-a-hitbox-attack-system-in-unity2d-1-animated-boxcollider2d-and-attack-script-cc97fcd3b268)
- [Layer Collision Matrix — Unity Code Monkey](https://unitycodemonkey.com/tutorial_text_contents_tinymce.php?v=uDYE3RFMNzk)
- [IDamageable Interface — Nerd For Tech (Medium)](https://medium.com/nerd-for-tech/idamageable-interface-unity-45bf961d141)
- [Hollow Knight Hitboxes Explained (YouTube)](https://www.youtube.com/watch?v=42fCSd22FBQ)
