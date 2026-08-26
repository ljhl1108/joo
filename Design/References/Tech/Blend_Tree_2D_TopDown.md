# Animator Blend Tree 2D — 탑다운 8방향 애니메이션

리서치 날짜: 2026-08-26

## 개요
Unity Animator의 **2D Blend Tree**는 두 개의 float 파라미터(예: MoveX, MoveY)를 축으로
여러 애니메이션 클립을 위치 기반으로 블렌딩한다. 탑다운 픽셀아트 게임에서 **4방향/8방향
이동 애니메이션**을 자연스럽게 전환할 때 핵심 도구다. OnionCat의 Cat 캐릭터처럼
이동 방향에 따라 다른 스프라이트 시트를 재생할 때 가장 실용적인 방법이다.

---

## Unity 구현 방법

### 1. Animator 파라미터 설정
Animator 창에서 파라미터 추가:
- `MoveX` (Float)
- `MoveY` (Float)
- `IsMoving` (Bool) — 이동 중 여부 판단용

### 2. 2D Blend Tree 생성
1. Animator 창 → State 우클릭 → `Create State > From New Blend Tree`
2. Blend Tree 더블클릭 진입
3. Inspector에서 `Blend Type` → **`2D Simple Directional`** 선택
4. Parameters: `MoveX`, `MoveY` 지정

> **2D Simple Directional vs 2D Freeform Directional**
> - Simple: 방향이 겹치지 않을 때 (탑다운 4/8방향에 적합)
> - Freeform: 같은 방향에 여러 클립이 있을 때 (달리기/걷기 혼합 등)

### 3. Motion 추가 (8방향 기준)
각 방향에 스프라이트 애니메이션 클립 추가:

| 방향     | MoveX | MoveY | 클립 이름          |
|----------|-------|-------|-------------------|
| 아래 (↓) | 0     | -1    | Cat_Walk_Down      |
| 위 (↑)   | 0     | 1     | Cat_Walk_Up        |
| 왼쪽 (←) | -1    | 0     | Cat_Walk_Left      |
| 오른쪽(→) | 1    | 0     | Cat_Walk_Right     |
| 좌하 (↙) | -0.7  | -0.7  | Cat_Walk_DownLeft  |
| 우하 (↘) | 0.7   | -0.7  | Cat_Walk_DownRight |
| 좌상 (↖) | -0.7  | 0.7   | Cat_Walk_UpLeft    |
| 우상 (↗) | 0.7   | 0.7   | Cat_Walk_UpRight   |

> 픽셀아트는 대각선 스프라이트를 별도 제작하지 않는 경우가 많음.
> 그럴 때는 4방향만 쓰고 대각 입력 시 가장 가까운 방향 클립이 자동 선택됨.

### 4. 스크립트에서 파라미터 업데이트
```csharp
using UnityEngine;
using UnityEngine.InputSystem;

[RequireComponent(typeof(Animator))]
public class CatAnimator : MonoBehaviour
{
    [SerializeField] private Animator animator;

    private Vector2 _moveDir;
    private Vector2 _lastFacingDir = Vector2.down; // 정지 시 마지막 방향 유지

    private static readonly int MoveX = Animator.StringToHash("MoveX");
    private static readonly int MoveY = Animator.StringToHash("MoveY");
    private static readonly int IsMoving = Animator.StringToHash("IsMoving");

    private void Awake()
    {
        if (animator == null) animator = GetComponent<Animator>();
    }

    // PlayerController로부터 이동 입력을 받아서 호출
    public void UpdateAnimationDirection(Vector2 moveInput)
    {
        _moveDir = moveInput;
        bool isMoving = moveInput.sqrMagnitude > 0.01f;

        animator.SetBool(IsMoving, isMoving);

        if (isMoving)
        {
            _lastFacingDir = moveInput.normalized;
            animator.SetFloat(MoveX, _lastFacingDir.x);
            animator.SetFloat(MoveY, _lastFacingDir.y);
        }
        else
        {
            // 정지 시 마지막 방향 유지 (idle 애니메이션도 방향 유지)
            animator.SetFloat(MoveX, _lastFacingDir.x);
            animator.SetFloat(MoveY, _lastFacingDir.y);
        }
    }
}
```

> `Animator.StringToHash()`로 파라미터 이름을 미리 해싱 → Update에서 string 비교 없이 int로 빠르게 접근.

### 5. Idle / Move 전환 상태 구성
Animator 상태머신 권장 구조:
```
[Any State]
     ↓
[IdleBlendTree] ←→ [WalkBlendTree]
```
- `IsMoving = true` → WalkBlendTree 전환
- `IsMoving = false` → IdleBlendTree 전환
- `Idle Blend Tree`도 동일하게 MoveX/MoveY 파라미터 참조 → 방향 유지된 Idle

### 6. 4방향으로 단순화 (픽셀아트 입문자 권장)
8방향 스프라이트가 없다면 4방향으로 제한:
```csharp
private Vector2 QuantizeDirection(Vector2 input)
{
    if (input.sqrMagnitude < 0.01f) return _lastFacingDir;

    float angle = Mathf.Atan2(input.y, input.x) * Mathf.Rad2Deg;
    // 45도 단위로 스냅 → 4방향
    if (angle >= -45 && angle < 45) return Vector2.right;
    if (angle >= 45 && angle < 135) return Vector2.up;
    if (angle >= 135 || angle < -135) return Vector2.left;
    return Vector2.down;
}
```

---

## OnionCat 적용 포인트

### Cat 이동 애니메이션
- `New Input System`의 `Gamepad/WASD` 이동 벡터를 그대로 `UpdateAnimationDirection()` 에 전달
- **Onion은 Cat 등 위에 있으므로 별도 Animator 불필요** — Cat의 방향만 따라가면 됨
- 슬래시 공격 중: `AnimatorStateInfo.IsName("Slash")` 확인 후 이동 파라미터 업데이트 잠시 중단

### 슬래시 애니메이션과 Blend Tree 분리
- 슬래시는 Blend Tree에 포함하지 말고 **별도 레이어(Layer)**에 Override로 설정
- Animator > Layers > "UpperBody" 레이어 추가, Weight 1.0, Avatar Mask로 상체만 오버라이드
- 이렇게 하면 이동 중에도 슬래시 애니메이션이 자연스럽게 재생됨

### 성능 고려
- `Animator.SetFloat()`는 Update에서 매 프레임 호출해도 실제 변경이 없으면 내부에서 무시됨
- 픽셀아트라면 Animator Interpolation은 필요 없음 → Clip의 `Sample Rate`를 낮게 설정 (8~12fps)

---

## 참고 링크
- [Unity 공식 — 2D Blend Tree](https://docs.unity3d.com/Manual/BlendTree-2DBlending.html)
- [Unity 공식 — Animator Parameters](https://docs.unity3d.com/Manual/AnimationParameters.html)
- [Brackeys — 2D 캐릭터 애니메이션 (YouTube)](https://www.youtube.com/results?search_query=brackeys+2d+top+down+animation+blend+tree)
- [Mix and Jam — Blend Tree 고급 활용 (YouTube)](https://www.youtube.com/results?search_query=unity+blend+tree+2d+top+down+8+direction)
