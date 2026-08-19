# Melee Arc Slash Hitbox (180° 슬래시 히트박스)

리서치 날짜: 2026-08-19

## 개요

OnionCat의 Cat(P1)은 캐릭터 앞쪽 180° 부채꼴 범위를 슬래시하는 근접 공격을 가진다.
단순한 원형 오버랩이 아니라 "방향을 향한 부채꼴" 판정이 필요하다.
Unity 2D에서 `Physics2D.OverlapCircleNonAlloc` + 각도 필터링으로 구현한다.

---

## Unity 구현 방법

### 핵심 개념: 원형 오버랩 + 각도 체크

1. `Physics2D.OverlapCircleNonAlloc`으로 슬래시 반경 내 모든 콜라이더 탐지
2. 탐지된 콜라이더마다 **캐릭터 → 적 벡터**와 **캐릭터 이동 방향 벡터** 사이 각도 계산
3. 각도가 90° 이내(180° 부채꼴이면 양쪽 90°)이면 히트 판정

```csharp
public class CatSlashAttack : MonoBehaviour
{
    [SerializeField] private float slashRadius = 1.5f;
    [SerializeField] private float slashAngle = 180f;   // 전체 호 각도
    [SerializeField] private LayerMask enemyLayer;
    [SerializeField] private int damage = 20;

    private Collider2D[] _hitBuffer = new Collider2D[16];

    // 이동 방향(또는 마지막 방향) 벡터를 외부에서 주입받아 사용
    public void ExecuteSlash(Vector2 facingDirection)
    {
        if (facingDirection == Vector2.zero)
            facingDirection = Vector2.right;

        int count = Physics2D.OverlapCircleNonAlloc(
            transform.position, slashRadius, _hitBuffer, enemyLayer);

        for (int i = 0; i < count; i++)
        {
            if (_hitBuffer[i] == null) continue;

            Vector2 toEnemy = (Vector2)(_hitBuffer[i].transform.position - transform.position);
            float angle = Vector2.Angle(facingDirection, toEnemy);

            if (angle <= slashAngle * 0.5f)   // 절반 각도 이내
            {
                var damageable = _hitBuffer[i].GetComponent<IDamageable>();
                damageable?.TakeDamage(damage, DamageType.Melee);
            }
        }
    }
}
```

### 슬래시 방향 결정 (New Input System 연동)

Cat의 이동 방향에서 슬래시 방향을 결정한다:

```csharp
// PlayerController.cs (Cat)
private Vector2 _lastMoveDirection = Vector2.right;

private void OnMove(InputValue value)
{
    Vector2 input = value.Get<Vector2>();
    if (input.magnitude > 0.1f)
        _lastMoveDirection = input.normalized;
}

private void OnSlash(InputValue value)
{
    if (value.isPressed)
        _slashAttack.ExecuteSlash(_lastMoveDirection);
}
```

### 시각적 디버그 (Scene View에서 부채꼴 확인)

```csharp
// 에디터에서 히트박스 시각화 (OnDrawGizmosSelected)
private void OnDrawGizmosSelected()
{
    Gizmos.color = new Color(1f, 0.3f, 0.3f, 0.4f);

    // 부채꼴 근사: 여러 선분으로 호를 그림
    Vector3 facingDir = Vector3.right; // 테스트용 고정 방향
    float halfAngle = 90f; // 180°/2
    int segments = 20;

    Vector3 prevPoint = transform.position + 
        Quaternion.Euler(0, 0, -halfAngle) * facingDir * slashRadius;

    for (int i = 1; i <= segments; i++)
    {
        float t = (float)i / segments;
        float currentAngle = Mathf.Lerp(-halfAngle, halfAngle, t);
        Vector3 point = transform.position + 
            Quaternion.Euler(0, 0, currentAngle) * facingDir * slashRadius;
        Gizmos.DrawLine(prevPoint, point);
        prevPoint = point;
    }
    Gizmos.DrawLine(transform.position, transform.position + facingDir * slashRadius);
}
```

### 애니메이션과 히트 타이밍 동기화 (AnimationEvent 방식)

슬래시 애니메이션 중간 특정 프레임에 히트 판정 발동:

```csharp
// Animator에서 AnimationEvent로 이 메서드 호출
public void OnSlashHitFrame()
{
    ExecuteSlash(_lastMoveDirection);
}
```

**유니티 에디터에서 드래그 앤 드롭 설정 필요:**
- Animator 창 → Slash 애니메이션 선택 → 원하는 프레임에 AnimationEvent 추가
- Function: `OnSlashHitFrame`

### 히트스톱 연동

공격이 적에게 맞았을 때 짧은 시간 동작 정지(히트스톱):

```csharp
// 히트 성공 시
if (hitCount > 0)
{
    StartCoroutine(HitStop(0.06f));
}

private IEnumerator HitStop(float duration)
{
    Time.timeScale = 0.05f;
    yield return new WaitForSecondsRealtime(duration);
    Time.timeScale = 1f;
}
```

---

## OnionCat 적용 포인트

### Cat(P1) 슬래시 구현 체크리스트
- [ ] `CatSlashAttack` 컴포넌트 작성 및 Cat 프리팹에 추가
- [ ] `slashRadius`, `slashAngle` Inspector에서 조정 가능하게 노출
- [ ] `enemyLayer` LayerMask 설정 (Enemy 레이어 지정)
- [ ] New Input System Action Map에 Slash 액션 바인딩 (키보드: Space / 게임패드: X)
- [ ] 슬래시 방향 = 마지막 이동 방향 (8방향 고정 or 연속 방향)
- [ ] 히트스톱 0.05~0.08초 적용
- [ ] AnimationEvent로 히트 판정 타이밍 조절

### 픽셀아트에 맞는 히트박스 철학
- 적에게 유리하게: 슬래시 반경을 실제 스프라이트보다 약간 넓게 설정 (너그러운 히트박스)
- `Hitbox_Design.md` 참고

### 근접 전용 취약 적 설계
이 슬래시 시스템과 `Enemy_Weakness_Resistance_System.md`를 연동:
- `DamageType.Melee`에만 피해를 받는 적 → Cat이 접근해야 함
- `DamageType.Ranged`에만 피해를 받는 적 → Onion이 조준해야 함

---

## 참고 링크

- Unity Physics2D.OverlapCircleNonAlloc: https://docs.unity3d.com/ScriptReference/Physics2D.OverlapCircleNonAlloc.html
- Vector2.Angle 레퍼런스: https://docs.unity3d.com/ScriptReference/Vector2.Angle.html
- AnimationEvent 설정: https://docs.unity3d.com/Manual/AnimationEventsOnImportedClips.html
- 히트스톱 구현 가이드: https://www.gamedeveloper.com/design/the-power-of-the-pause-hitstop-and-impact-in-games
