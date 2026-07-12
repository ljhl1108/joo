# Player Movement System (탑다운 플레이어 이동)

리서치 날짜: 2026-07-12

## 개요

탑다운 로그라이크에서 플레이어 이동은 **모든 전투의 기반**이다. OnionCat의 고양이는 키보드/패드로 8방향 이동하고, 양파는 동일 바디에 탑승하므로 이동 코드가 하나로 통합된다. 이동의 "느낌(game feel)"이 전투 재미를 좌우하므로, Rigidbody2D 설계 방식과 파라미터 튜닝을 제대로 잡는 것이 중요하다.

---

## Unity 구현 방법

### 1. Rigidbody2D vs CharacterController

| 방식 | 장점 | 단점 | 추천 |
|------|------|------|------|
| **Rigidbody2D + MovePosition** | 물리 반응 자동, 충돌 자연스러움 | 관성/미끄러짐 발생 가능 | ✅ 탑다운 로그라이크 표준 |
| **Transform.position 직접 수정** | 완전한 제어 | 충돌 무시, 물리 버그 | ❌ |
| **CharacterController** | 3D에 적합 | 2D에서 어색함 | ❌ |

**결론**: `Rigidbody2D` + `linearVelocity` 직접 설정이 탑다운에서 가장 빠르고 안정적.

---

### 2. 기본 이동 구현

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Rigidbody2D))]
public class PlayerMovement : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 5f;

    private Rigidbody2D _rb;
    private Vector2 _moveInput;

    private void Awake()
    {
        _rb = GetComponent<Rigidbody2D>();
        // Rigidbody2D 설정: Gravity Scale = 0, Linear Drag = 10 (즉시 정지용)
    }

    // New Input System 콜백
    public void OnMove(InputAction.CallbackContext context)
    {
        _moveInput = context.ReadValue<Vector2>();
    }

    private void FixedUpdate()
    {
        // 대각선 이동 시 속도 정규화 (normalize)
        Vector2 move = _moveInput.normalized * moveSpeed;
        _rb.linearVelocity = move;
    }
}
```

**핵심**: `_moveInput.normalized` — 대각선(√2 ≈ 1.41배 빠름)을 막기 위해 반드시 정규화.

---

### 3. 관성(미끄러짐) 제어

즉각 정지 원하면 → `Linear Drag` 높이거나 FixedUpdate에서 직접 velocity 설정  
부드러운 가속 원하면 → `Vector2.MoveTowards` 또는 `Lerp` 사용

```csharp
// 방식 A: 즉각 반응 (Dead Cells, Windblown 느낌)
_rb.linearVelocity = _moveInput.normalized * moveSpeed;

// 방식 B: 부드러운 가속 (Hades 느낌)
Vector2 targetVel = _moveInput.normalized * moveSpeed;
_rb.linearVelocity = Vector2.MoveTowards(_rb.linearVelocity, targetVel, acceleration * Time.fixedDeltaTime);
```

OnionCat 권장: **방식 A** (즉각 반응). 로그라이크 전투에서 빠른 회피가 중요.

---

### 4. 이동 방향 스프라이트 전환

8방향 대신 보통 4방향 애니메이션 + FlipX로 처리:

```csharp
private void UpdateFacingDirection()
{
    if (_moveInput.x != 0)
    {
        // 좌우 반전
        transform.localScale = new Vector3(
            _moveInput.x < 0 ? -1 : 1, 1, 1);
    }
}
```

또는 Animator 파라미터에 `MoveX`, `MoveY` 전달 후 Blend Tree 사용.

---

### 5. 이동 속도 스탯 연동

```csharp
// 스탯 시스템과 연동
public float MoveSpeed => baseMoveSpeed * statModifier.GetSpeedMultiplier();

private void FixedUpdate()
{
    _rb.linearVelocity = _moveInput.normalized * MoveSpeed;
}
```

업그레이드 아이템이 `statModifier`를 수정하면 이동 속도가 자동 반영.

---

### 6. 이동 불가 상태 처리

```csharp
public bool CanMove { get; set; } = true;

private void FixedUpdate()
{
    if (!CanMove)
    {
        _rb.linearVelocity = Vector2.zero;
        return;
    }
    _rb.linearVelocity = _moveInput.normalized * MoveSpeed;
}
```

히트스톱, 컷신, 스턴 등 다양한 상황에서 `CanMove = false`로 일괄 차단.

---

## OnionCat 적용 포인트

### 통합 바디 구조
고양이가 이동을 담당하고 양파는 같은 GameObject(또는 자식)에 탑승:
- `PlayerMovement` 컴포넌트는 부모 GameObject에 하나만 존재
- 양파의 마우스 조준은 별도 `CropAimController`로 처리 (이동과 독립)
- 고양이 대시 시 `CanMove = false` + 대시 벡터 직접 적용 후 복구

### 고양이-양파 역할 분리 입력
```csharp
// Cat: WASD / 왼쪽 스틱 → 이동
public void OnCatMove(InputAction.CallbackContext ctx) => _moveInput = ctx.ReadValue<Vector2>();

// Crop: 마우스 / 오른쪽 스틱 → 조준 (CropAimController에서 처리)
// 이동에 영향 없음
```

### Rigidbody2D 인스펙터 권장 설정
| 항목 | 값 |
|------|----|
| Gravity Scale | 0 |
| Linear Drag | 0 (코드로 직접 velocity 제어) |
| Angular Drag | Infinity |
| Freeze Rotation | Z 체크 (회전 방지) |
| Collision Detection | Continuous (빠른 이동 시 관통 방지) |

---

## 참고 링크

- Unity Docs - Rigidbody2D: https://docs.unity3d.com/Manual/class-Rigidbody2D.html
- Unity Docs - New Input System: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/index.html
- Game Feel 튜닝 가이드 (Celeste 개발자): https://www.youtube.com/watch?v=yorTG9at90g
- 탑다운 움직임 튜토리얼 (Code Monkey): https://www.youtube.com/watch?v=whzomFgjT50
- Input System 탑다운 세팅: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/QuickStartGuide.html
