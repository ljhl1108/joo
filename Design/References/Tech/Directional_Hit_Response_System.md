# 방향성 피격 반응 시스템 (Directional Hit Response System)

리서치 날짜: 2026-10-08

## 개요

피격된 방향을 감지해 **방향에 맞는 넉백·애니메이션·방패 판정**을 처리하는 시스템.  
OnionCat에서 특히 중요한 이유:
- **방패병 적**: 전면은 막히고 배후/측면에서만 피해 입힘 → 방향 판정 필수
- **양파 방패 패링**: 들어오는 공격 방향과 방패 방향 비교로 패링 성공/실패 결정
- **넉백 연출**: 같은 피격이라도 방향이 다르면 캐릭터가 다른 쪽으로 날아가야 자연스러움

---

## Unity 구현 방법

### 1. 피격 방향 벡터 계산

```csharp
// DamageInfo에 방향 포함
public struct DamageInfo {
    public int amount;
    public Vector2 hitPoint;   // 공격이 닿은 월드 좌표
    public Attacker attacker;
    public float knockbackForce;
}

// 피해를 받는 쪽에서 방향 계산
Vector2 knockbackDir = (transform.position - (Vector3)damageInfo.hitPoint).normalized;
// hitPoint가 없으면: 공격자 위치 기준
// Vector2 knockbackDir = (transform.position - attackerPos).normalized;
```

### 2. 8방향 Enum으로 변환

```csharp
public enum HitDirection { None, Front, Back, Left, Right, TopLeft, TopRight, BottomLeft, BottomRight }

HitDirection GetHitDirection(Vector2 incoming) {
    // incoming = 공격이 들어오는 방향 (공격자 → 피격자)
    float angle = Mathf.Atan2(incoming.y, incoming.x) * Mathf.Rad2Deg;
    // 0도 = Right, 90도 = Up, 180도 = Left
    // ...분기 처리 또는 Mathf.Round(angle / 45f)로 8방향 인덱스
    int index = Mathf.RoundToInt(angle / 45f);
    return (HitDirection)((index % 8 + 8) % 8);
}
```

### 3. 방패병 방어 판정

```csharp
public class ShieldEnemy : EnemyBase {
    [SerializeField] private float shieldBlockAngle = 60f; // ±60도 범위 방어

    public override bool TryBlock(Vector2 attackerPos) {
        Vector2 incomingDir = (transform.position - attackerPos).normalized;
        Vector2 shieldFacing = transform.right; // 적이 바라보는 방향 = 방패 방향

        float dot = Vector2.Dot(incomingDir, shieldFacing);
        // dot > cos(60°) = 0.5 이면 전면에서 온 공격 → 방어 성공
        return dot > Mathf.Cos(shieldBlockAngle * Mathf.Deg2Rad);
    }
}

// 피해 적용 시
public override void TakeDamage(DamageInfo info) {
    if (TryBlock(info.hitPoint)) {
        // 막힘 — 방어 이펙트만 재생
        PlayBlockVFX();
        return;
    }
    base.TakeDamage(info);
}
```

### 4. 양파 방패 패링 판정

```csharp
public class OnionShield : MonoBehaviour {
    [SerializeField] private float parryWindow = 0.2f;     // 패링 성공 타이밍 (초)
    [SerializeField] private float blockAngle = 90f;       // ±45도 범위 막기

    private bool _isRaised;
    private float _raiseTime;

    public bool CheckParry(Vector2 projectileDir) {
        Vector2 shieldFacing = transform.right;
        // 투사체가 날아오는 방향의 반대 = 방패가 바라봐야 할 방향
        float dot = Vector2.Dot(-projectileDir.normalized, shieldFacing);
        bool facingCorrect = dot > Mathf.Cos(blockAngle * 0.5f * Mathf.Deg2Rad);
        bool inParryWindow = Time.time - _raiseTime <= parryWindow;
        return facingCorrect && inParryWindow && _isRaised;
    }

    public bool CheckBlock(Vector2 projectileDir) {
        // 패링 윈도우 지나도 각도만 맞으면 막기 (피해 0)
        Vector2 shieldFacing = transform.right;
        float dot = Vector2.Dot(-projectileDir.normalized, shieldFacing);
        return dot > Mathf.Cos(blockAngle * 0.5f * Mathf.Deg2Rad) && _isRaised;
    }
}
```

### 5. 방향별 넉백 + 애니메이션 연동

```csharp
void ApplyKnockback(Vector2 dir, float force) {
    _rb.AddForce(dir * force, ForceMode2D.Impulse);

    // 애니메이터에 방향 전달 (Blend Tree용)
    // 지역 좌표로 변환해 스프라이트 방향 독립적으로
    Vector2 localDir = transform.InverseTransformDirection(dir);
    _animator.SetFloat("HitDirX", localDir.x);
    _animator.SetFloat("HitDirY", localDir.y);
    _animator.SetTrigger("Hit");
}
```

**Blend Tree 설정**:
- 2D Blend Tree (Freeform Directional)
- HitDirX / HitDirY 파라미터
- 클립: HitFront, HitBack, HitLeft, HitRight
- 픽셀아트의 경우 4방향만으로도 충분

### 6. 스프라이트 플립 자동 처리 주의

좌우 대칭 히트 애니메이션이 있다면, 피격 방향에 따라 `SpriteRenderer.flipX`만 토글해도 됨:

```csharp
void TriggerHitAnim(Vector2 knockbackDir) {
    // 오른쪽에서 맞았으면 → 왼쪽으로 날아가는 애니메이션
    _spriteRenderer.flipX = knockbackDir.x > 0;
    _animator.SetTrigger("HitSide");
}
```

---

## OnionCat 적용 포인트

### 방패병 (적 #4)
- `ShieldEnemy` 컴포넌트 또는 `EnemyBase`의 `TakeDamage` 오버라이드
- 방패 방향 = `transform.right` (적이 플레이어를 향해 회전하므로 자동 갱신)
- 배후에서 맞으면 `Launch(interruptTelegraph: false)` + 추가 피해 배율
- 보스는 `kickInterruptsTelegraph = false` 설정 (CLAUDE.md 규칙)

### 양파 방패 + 패링
- `OnionShield.CheckParry(projectile.Direction)` — 투사체가 방패에 닿을 때 호출
- 패링 성공 시: 투사체 반사, 양파에게 `Attacker.Onion`으로 피해, 화면 흔들림
- 블록(패링 아님): 투사체 소멸, 피해 0, 방패 이펙트

### 고양이 할퀴기 배후 보너스
- 적의 `transform.forward` vs 공격 방향으로 "배후 공격" 판정
- 배후 = 추가 피해 또는 스턴 → ClawStyle 카드 중 하나로 설계 가능

### 협동 필수 설계 강화
방향성 시스템을 활용하면 **방패병 = 혼자서는 공략 어려운 적**을 자연스럽게 구현:
1. 양파가 원거리 사격 → 방패로 막힘
2. 고양이가 뒤로 돌아 근접 → 방패 방어 범위 밖 → 피해
3. 또는 양파 패링으로 방패병을 스턴 → 그 사이 고양이가 공격

---

## 주의 사항

- **방향 계산 기준 일관성**: 피격자 기준(공격자 → 피격자)인지 공격자 기준인지 통일
- **방패 방향은 매 프레임 갱신**: 방패병이 플레이어를 추적해 회전하므로 `transform.right`가 자동으로 맞음
- **8방향 vs 4방향**: 픽셀아트에서 8방향 피격 애니메이션 제작은 부담 → 4방향 또는 좌/우 2방향으로도 충분
- **Kinematic Rigidbody와 넉백**: 적이 `Rigidbody2D.isKinematic = true`이면 `AddForce` 무효 → 코루틴으로 직접 position 이동

---

## 참고 링크

- [Unity Docs — Physics2D.Dot & Vector2.Dot](https://docs.unity3d.com/ScriptReference/Vector2.Dot.html)
- [Unity Docs — Rigidbody2D.AddForce](https://docs.unity3d.com/ScriptReference/Rigidbody2D.AddForce.html)
- [Unity Docs — Animator.SetFloat](https://docs.unity3d.com/ScriptReference/Animator.SetFloat.html)
- [GDC Talk: The Art of Screenshake (피격 반응 연출 원칙)](https://www.youtube.com/watch?v=AJdEqssNZ-U)
- [Game Feel: A Game Designer's Guide to Virtual Sensation (Bob Swain) — Chapter 5: Feedback]
