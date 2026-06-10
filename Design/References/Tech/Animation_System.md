# 애니메이션 시스템 (Animator StateMachine / AnimationEvent / Blend Tree)

## 개요

Unity의 애니메이션 시스템은 로그라이크 액션 게임에서 **캐릭터의 의도와 상태를 시각적으로 전달**하는 핵심 도구다.  
OnionCat에서는 Cat의 이동·슬래시·대시, Onion의 조준·발사·방패, 그리고 다양한 적들의 움직임 모두 애니메이터로 관리한다.  
잘못 설계된 Animator는 버그와 성능 문제의 주요 원인이 되므로 초반에 올바른 구조를 잡는 것이 중요하다.

---

## Unity 구현 방법

### 1. Animator StateMachine 기본 구조

```
Any State
   └── (Hit Trigger) → Hit State
   └── (Die Trigger) → Die State

Idle ←→ Run
  └── (Attack Trigger) → Attack → [Exit Time] → Idle
  └── (Dash Trigger) → Dash → [Exit Time] → Idle
```

**파라미터 타입 선택 가이드**:
- `Bool`: 지속 상태 (isMoving, isGrounded)
- `Trigger`: 순간 이벤트 (Attack, Hit, Die) — 자동 리셋됨
- `Float`: 연속 값 (moveSpeed, blendX, blendY)
- `Int`: 선택지 (weaponType, directionIndex)

**주의**: Trigger는 콜백 방식으로 단 한 번만 소모됨. Bool처럼 true/false 관리 불필요.

---

### 2. 이동 방향 Blend Tree (8방향 애니메이션)

```csharp
// Animator에 2D Freeform Directional Blend Tree 생성
// 파라미터: moveX (float), moveY (float)

// 코드에서 이동 방향 전달
void Update()
{
    Vector2 moveInput = _moveAction.ReadValue<Vector2>();
    
    if (moveInput.sqrMagnitude > 0.01f)
    {
        animator.SetFloat("moveX", moveInput.x);
        animator.SetFloat("moveY", moveInput.y);
        animator.SetBool("isMoving", true);
    }
    else
    {
        animator.SetBool("isMoving", false);
    }
}
```

**Blend Tree 설정** (Inspector):
- Blend Type: 2D Freeform Directional
- 8개 모션 배치: 상/하/좌/우/대각선 4방향
- 각 포인트: (0,1), (0,-1), (-1,0), (1,0), (0.7,0.7) ...

**팁**: 4방향으로 시작하고 나중에 8방향으로 확장해도 됨.

---

### 3. AnimationEvent — 정밀 타이밍 연동

애니메이션 특정 프레임에 C# 함수를 호출하는 기능. **히트박스 활성화**에 필수.

```csharp
public class CatAnimationEventHandler : MonoBehaviour
{
    [SerializeField] private CatAttack _catAttack;
    [SerializeField] private CatMovement _catMovement;

    // Animator에서 호출 — 슬래시 히트박스 ON
    public void OnSlashHitboxStart()
    {
        _catAttack.EnableHitbox();
    }

    // 슬래시 히트박스 OFF
    public void OnSlashHitboxEnd()
    {
        _catAttack.DisableHitbox();
    }

    // 발소리 재생
    public void OnFootstep()
    {
        AudioManager.Instance.PlaySFX("footstep");
    }

    // 대시 이펙트 생성
    public void OnDashTrail()
    {
        _catMovement.SpawnDashTrail();
    }
}
```

**설정 방법**:
1. Animation 창 열기 (Window > Animation > Animation)
2. 이벤트 추가할 프레임으로 이동
3. 상단 "Add Event" 버튼 클릭
4. Inspector에서 Function 선택 (해당 오브젝트에 있는 public 메서드만 표시)

**중요**: AnimationEvent 수신 스크립트는 **Animator가 붙은 같은 GameObject 또는 그 자식**에 있어야 함.

---

### 4. 공격 모션 히트스톱 연동

```csharp
// 히트스톱 중 애니메이션도 멈춰야 함
public class HitStopManager : MonoBehaviour
{
    public void TriggerHitStop(float duration)
    {
        StartCoroutine(HitStopCoroutine(duration));
    }

    private IEnumerator HitStopCoroutine(float duration)
    {
        Time.timeScale = 0f;
        yield return new WaitForSecondsRealtime(duration); // timeScale=0이라도 작동
        Time.timeScale = 1f;
    }
}
```

애니메이터는 `Time.timeScale`을 따르므로 별도 처리 불필요.  
단, `updateMode = AnimatorUpdateMode.UnscaledTime`으로 설정된 UI 애니메이션은 영향 없음.

---

### 5. 상태 전환 최적화 — Has Exit Time vs Transition Duration

| 설정 | 언제 사용 |
|------|-----------|
| Has Exit Time ON | 애니메이션이 끝난 후에만 전환 (Attack → Idle) |
| Has Exit Time OFF | 즉시 전환 가능 (Hit 피격은 즉각 반응 필요) |
| Transition Duration 0 | 피격/사망처럼 즉각적으로 바뀌어야 할 때 |
| Transition Duration 0.1~0.2 | 일반 이동 블렌딩 |

**공격 캔슬 지원**: Has Exit Time OFF + `Can Transition To Self` OFF 조합으로 공격 중 재공격 입력 가능.

---

### 6. Sub-State Machine — 복잡한 상태 정리

적이 여러 공격 패턴을 가질 때 최상위 SM이 복잡해짐. Sub-SM으로 묶어서 관리:

```
[Root SM]
├── Idle
├── Move  
├── [Attack Sub-SM]
│   ├── AttackA
│   ├── AttackB
│   └── AttackC
└── Die
```

방법: SM 빈 공간 우클릭 → Create Sub-State Machine

---

### 7. Animator Override Controller — 캐릭터 변형

같은 로직으로 다른 스프라이트를 쓸 때 유용:

```csharp
// 베이스 컨트롤러의 애니메이션 클립만 교체
AnimatorOverrideController overrideCtrl = new AnimatorOverrideController(baseAnimatorController);
overrideCtrl["Cat_Idle"] = newIdleClip; // 클립 이름으로 교체
animator.runtimeAnimatorController = overrideCtrl;
```

적 변형이 많을 때 컨트롤러를 하나 만들고 클립만 교체하는 식으로 활용.

---

## OnionCat 적용 포인트

### Cat 애니메이터 구조 (권장)
```
[Cat Animator]
파라미터: isMoving(bool), moveX(float), moveY(float), 
          attack(trigger), dash(trigger), hit(trigger), die(trigger)

States:
  Idle ←→ Move (Blend Tree: 4방향 이동)
  Any → Attack (trigger) → Idle
  Any → Dash (trigger) → Idle  
  Any → Hit (trigger) → Idle
  Any → Die (trigger) [No transition out]
```

### Onion 애니메이터 구조 (권장)
```
[Onion Animator]
파라미터: aimAngle(float), shoot(trigger), shield(bool), hit(trigger)

States:
  Idle (aimAngle에 따라 스프라이트 방향 변경)
  Any → Shoot (trigger) → Idle
  Idle ↔ Shield (bool)
  Any → Hit (trigger) → Idle
```

### 핵심 구현 순서 (OnionCat)
1. Cat의 Idle/Run 스프라이트 준비 → 4방향 Blend Tree 설정
2. Cat Attack 애니메이션 추가 + AnimationEvent로 히트박스 ON/OFF
3. Onion의 조준 방향에 따른 스프라이트 전환 (aimAngle 파라미터)
4. Hit/Die 공통 Trigger 추가
5. 적 캐릭터는 AnimatorOverrideController로 재활용

### AnimationEvent 필수 적용 포인트
- `CatSlash`: 프레임 3에서 히트박스 ON, 프레임 7에서 OFF
- `OnionShoot`: 프레임 2에서 ProjectileManager.SpawnProjectile() 호출
- `OnionParry`: 프레임 1~4 사이 패리 판정 활성화

---

## 참고 링크
- Unity 공식 - Animator Controller: https://docs.unity3d.com/Manual/class-AnimatorController.html
- Unity 공식 - Animation Events: https://docs.unity3d.com/Manual/AnimationEventsOnImportedClips.html
- Unity 공식 - Blend Trees: https://docs.unity3d.com/Manual/class-BlendTree.html
- Unity Learn - 2D Character Animation: https://learn.unity.com/tutorial/2d-animation
- 유튜브 - "Unity Animator Tutorial for Beginners" (Brackeys)
- 유튜브 - "Unity Animation Events" (Code Monkey)
