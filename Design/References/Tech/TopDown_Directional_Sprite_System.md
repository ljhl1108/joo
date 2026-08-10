# Top-Down 방향 스프라이트 시스템

리서치 날짜: 2026-08-10

## 개요

탑다운 2D 게임에서 캐릭터와 적이 8방향(또는 4방향)으로 움직일 때, 어느 방향을 바라보느냐에 따라 스프라이트를 올바르게 전환하는 시스템. OnionCat에서는 Cat의 슬래시 방향, Crop의 마우스 조준 방향, 모든 적의 이동·공격 방향에 핵심적으로 사용된다.

### 왜 중요한가

- 탑다운 게임에서 캐릭터가 "아무 방향이나" 이동할 수 있으면 스프라이트가 어색하게 보임
- 단순 `flipX` 만으로는 상하 이동을 처리할 수 없음
- 4방향/8방향 애니메이션 세트를 Animator와 올바르게 연결하지 않으면 전환이 뚝뚝 끊김

---

## Unity 구현 방법

### 방법 1: Animator Parameter (가장 범용적)

**Animator 파라미터 설정**:
- `MoveX` (Float): -1~1 (좌우)
- `MoveY` (Float): -1~1 (상하)
- `IsMoving` (Bool)

**Blend Tree 구성** (2D Simple Directional):
```
Blend Tree
├── Direction.Right (MoveX=1, MoveY=0)
├── Direction.UpRight (MoveX=0.7, MoveY=0.7)  // 8방향 시
├── Direction.Up (MoveX=0, MoveY=1)
├── Direction.Left (MoveX=-1, MoveY=0)
├── Direction.Down (MoveX=0, MoveY=-1)
```

**스크립트**:
```csharp
// DirectionalAnimator.cs
using UnityEngine;

[RequireComponent(typeof(Animator))]
public class DirectionalAnimator : MonoBehaviour
{
    Animator _anim;
    Vector2 _lastDir = Vector2.right; // 정지 시 마지막 방향 유지

    static readonly int HashMoveX = Animator.StringToHash("MoveX");
    static readonly int HashMoveY = Animator.StringToHash("MoveY");
    static readonly int HashIsMoving = Animator.StringToHash("IsMoving");

    void Awake() => _anim = GetComponent<Animator>();

    public void SetDirection(Vector2 moveDir)
    {
        bool isMoving = moveDir.sqrMagnitude > 0.01f;
        if (isMoving) _lastDir = moveDir.normalized;

        _anim.SetBool(HashIsMoving, isMoving);
        _anim.SetFloat(HashMoveX, _lastDir.x);
        _anim.SetFloat(HashMoveY, _lastDir.y);
    }
}
```

---

### 방법 2: 4방향 Int 파라미터 (애니메이션 수 적을 때 간단)

```csharp
// FacingDirection.cs
public enum FacingDir { Right = 0, Up = 1, Left = 2, Down = 3 }

public static FacingDir VectorToFacing(Vector2 dir)
{
    if (dir.sqrMagnitude < 0.01f) return FacingDir.Down; // 기본값
    if (Mathf.Abs(dir.x) >= Mathf.Abs(dir.y))
        return dir.x >= 0 ? FacingDir.Right : FacingDir.Left;
    return dir.y >= 0 ? FacingDir.Up : FacingDir.Down;
}

// 사용 예시 (애니메이터에 Int 파라미터 "FacingDir" 설정 필요)
_anim.SetInteger("FacingDir", (int)VectorToFacing(moveDir));
```

Animator에서 각 상태에 `FacingDir Equals 0/1/2/3` 조건 트랜지션 설정.

---

### 방법 3: SpriteRenderer flipX만으로 처리 (좌우만 필요할 때)

```csharp
// 좌우 이동만 있는 적/NPC에 가장 가볍고 빠름
void Update()
{
    if (Mathf.Abs(moveDir.x) > 0.01f)
        spriteRenderer.flipX = moveDir.x < 0;
}
```

> 주의: flipX를 사용할 때는 히트박스(Collider2D), 투사체 발사 위치도 함께 반전되도록 부모 Transform 구조 확인 필요.

---

### 방법 4: 마우스 방향 조준 (Crop 전용)

Crop은 키보드 이동과 무관하게 마우스 방향으로 조준한다. 스프라이트 회전 대신 4방향 분기를 사용:

```csharp
// CropAimDirector.cs
Vector2 GetAimDir()
{
    Vector3 mouseWorld = Camera.main.ScreenToWorldPoint(Input.mousePosition);
    return ((Vector2)(mouseWorld - transform.position)).normalized;
}

void Update()
{
    Vector2 aimDir = GetAimDir();
    FacingDir facing = FacingDirection.VectorToFacing(aimDir);
    _anim.SetInteger("FacingDir", (int)facing);

    // 투사체 발사점 회전도 함께 처리
    float angle = Mathf.Atan2(aimDir.y, aimDir.x) * Mathf.Rad2Deg;
    aimPivot.rotation = Quaternion.Euler(0, 0, angle);
}
```

---

## OnionCat 적용 포인트

### Cat
- 이동 방향 기반 4방향 → `DirectionalAnimator.SetDirection(moveInput)` 호출
- 슬래시는 Cat이 바라보는 방향에서 180° 반원형으로 발사
- 대시 시 이동 방향 유지 (대시 중 방향 전환 금지)

### Crop
- 마우스 조준 방향으로 독립적인 상반신 방향 결정
- 하반신(다리/화분)은 Cat의 이동 방향, 상반신(작물)은 마우스 방향
- 두 Animator를 `AvatarMask`로 분리해 각각 적용 (`UpperBody` / `FullBody` 레이어)

```
Animator Layer 구성:
- Layer 0 "FullBody" (Weight 1.0): 이동 애니메이션
- Layer 1 "UpperBody" (Weight 1.0, AvatarMask=상반신): Crop 조준 방향 애니메이션
```

### 적
- 대부분의 적: `MoveDir` 기반 4방향 → 방법 1 또는 2 사용
- 원거리 적(투사체 발사형): 플레이어를 바라보는 방향으로 `VectorToFacing` 계산
- 보스: 8방향 Blend Tree 사용 (더 자연스러운 전환)

---

## 참고 링크

- Unity Blend Tree (2D Simple Directional): https://docs.unity3d.com/Manual/BlendTree-2DBlending.html
- Animator Parameters: https://docs.unity3d.com/Manual/AnimationParameters.html
- Avatar Mask (레이어 마스킹): https://docs.unity3d.com/Manual/class-AvatarMask.html
- Unity 공식 튜토리얼 — 2D 탑다운 이동: https://learn.unity.com/tutorial/2d-top-down-character-controller
- 참고 영상: "How to make a top-down 8-directional animation in Unity" (YouTube 검색)
