# Animation Interrupt Priority System (애니메이터 상태 전환 우선순위)

리서치 날짜: 2026-09-19

## 개요

액션 게임에서 애니메이션 인터럽트란 현재 재생 중인 애니메이션을 **더 중요한 이벤트로 즉시 교체**하는 것이다.
예: 공격 모션 중 맞아서 경직 모션이 나와야 하는 상황, 또는 공격 중 사망 모션으로 전환.

Unity Animator는 기본적으로 트랜지션이 순서대로 처리되는데, **인터럽트 소스(Interrupt Source)** 설정과 트랜지션 우선순위를 잘못 설정하면 사망 애니메이션이 공격 애니메이션에 묻히거나, 히트 리액션이 무시된다.

OnionCat에서는:
- Cat의 대시 중 피격 → 무적(iFrame) 기간이라 피격 애니메이션 불필요
- Crop의 투사체 발사 중 피격 → 경직 모션으로 인터럽트
- 두 플레이어 모두 사망 → 최우선으로 사망 모션 재생

---

## Unity 구현 방법

### 1. 트랜지션 우선순위 (Priority 순서)

Animator의 AnyState → 각 상태 트랜지션은 **목록 위쪽이 우선순위 높음**.
Inspector에서 드래그로 순서 변경 가능.

권장 우선순위 (높은 순):
```
1. Death (사망) ← 항상 최우선
2. Stagger (경직/피격)
3. Dash (대시)
4. Attack (공격)
5. Move (이동)
6. Idle (대기)
```

### 2. Interrupt Source 설정

트랜지션 선택 → Inspector에서 **Interrupt Source** 옵션:

| 값 | 의미 |
|----|------|
| `None` | 인터럽트 없음 (현재 상태 완전히 끝나야 전환) |
| `Current State` | 현재 상태에서 나가는 트랜지션이 인터럽트 가능 |
| `Next State` | 다음 상태에서 들어오는 트랜지션이 인터럽트 가능 |
| `Current State Then Next State` | 현재 먼저, 그 다음 Next 확인 |

**실용 규칙**:
- `AnyState → Death`: Interrupt Source = `None`, Can Transition To Self = false
- `AnyState → Stagger`: Interrupt Source = `Current State` (공격 중에도 인터럽트)
- `Attack → Move`: Interrupt Source = `None` (공격은 끝까지 재생)

### 3. AnyState 트랜지션 활용

`AnyState`는 어떤 상태에서든 전환 가능. 사망/피격에 유용:

```
AnyState → Dead
  조건: isDead == true
  Has Exit Time: false
  Transition Duration: 0.05

AnyState → Hit
  조건: isHit trigger
  Has Exit Time: false
  Transition Duration: 0.1
  Interrupt Source: Current State
```

**주의**: `Can Transition To Self`를 false로 해야 Hit 중에 또 Hit 트리거가 Hit 재시작을 막을 수 있음 (또는 의도적으로 허용).

### 4. 코드에서 인터럽트 트리거 전송

```csharp
public class CharacterAnimator : MonoBehaviour
{
    [SerializeField] private Animator _animator;

    // 우선순위별 트리거 이름 상수
    private static readonly int DeathTrigger = Animator.StringToHash("Death");
    private static readonly int HitTrigger = Animator.StringToHash("Hit");
    private static readonly int DashTrigger = Animator.StringToHash("Dash");
    private static readonly int AttackTrigger = Animator.StringToHash("Attack");

    public void PlayDeath()
    {
        // 다른 트리거 모두 리셋 후 Death 트리거
        _animator.ResetTrigger(HitTrigger);
        _animator.ResetTrigger(DashTrigger);
        _animator.ResetTrigger(AttackTrigger);
        _animator.SetTrigger(DeathTrigger);
    }

    public void PlayHit()
    {
        // 대시 무적 중이면 히트 애니메이션 스킵
        if (_animator.GetCurrentAnimatorStateInfo(0).IsName("Dash")) return;
        _animator.SetTrigger(HitTrigger);
    }
}
```

### 5. 대시 무적(iFrame) 중 애니메이션 처리

OnionCat의 Cat은 대시 중 무적 → 피격 모션을 막아야 함:

```csharp
// DashAbility.cs
public class DashAbility : MonoBehaviour
{
    [SerializeField] private bool _isInvincible;
    public bool IsInvincible => _isInvincible;

    // CharacterAnimator에서 확인
    // if (dashAbility.IsInvincible) return; // Hit 스킵
}
```

또는 Animator의 Layer Weight를 활용: 대시 레이어(Layer 1)가 활성화되면 기본 레이어(Layer 0)의 Hit를 덮어씌움.

### 6. Animator Layer 활용 (고급)

복잡한 인터럽트는 **레이어 분리**로 해결:

```
Layer 0 (Base): Idle, Move, Attack, Death
Layer 1 (Reaction, Weight=0~1): Hit, Stagger
Layer 2 (Override, Weight=1): Dash (대시 중엔 이 레이어가 전부 덮음)
```

```csharp
// 대시 시작 시
_animator.SetLayerWeight(2, 1f); // 대시 레이어 활성화

// 대시 종료 시
_animator.SetLayerWeight(2, 0f);
```

### 7. AnimationEvent로 인터럽트 가능 타이밍 제어

공격 모션의 일부 구간만 캔슬 가능하게 하려면:

```csharp
// 애니메이션 클립에 AnimationEvent 추가
// 함수 이름: OnAttackCancellable / OnAttackNoCancelStart / OnAttackNoCancelEnd

public void OnAttackCancellable()
{
    _canCancelAttack = true;
}

public void OnAttackNoCancelStart()
{
    _canCancelAttack = false;
}
```

---

## OnionCat 적용 포인트

### Cat 애니메이터 우선순위
```
AnyState → Cat_Death       (최우선, isDead)
AnyState → Cat_Hit         (Stagger trigger, 대시 중 제외)
AnyState → Cat_Dash        (대시, 무적 기간 시작)
Cat_Dash → Cat_Idle        (대시 종료)
Cat_Idle → Cat_Attack      (공격 trigger)
Cat_Attack → Cat_Move/Idle (Has Exit Time: true, 공격 끝나면 자동 전환)
```

### Crop 애니메이터 우선순위
```
AnyState → Crop_Death
AnyState → Crop_Hit        (투사체 발사 중에도 인터럽트)
AnyState → Crop_Shield     (방패 들기)
Crop_Idle → Crop_Shoot     (발사 trigger)
Crop_Shoot → Crop_Idle     (Has Exit Time: true)
```

### 공유 몸(Shared Body) 특수 상황
- Cat이 사망하면 Crop도 사망 → SharedCharacterController에서 둘 다 Death 트리거
- Cat이 Hit 애니메이션 중에도 Crop은 계속 조준 가능 (별도 레이어/애니메이터)

### 실수 방지 체크리스트
- [ ] AnyState → Death에 `Can Transition To Self` = false
- [ ] 대시 중 Hit 트리거 차단 코드 추가
- [ ] 공격 중 Move 인터럽트 방지 (Has Exit Time 또는 Interrupt Source = None)
- [ ] 모든 AnyState 트랜지션에 `Has Exit Time` = false 확인

---

## 참고 링크

- Unity 공식 문서 - Transition Interruption Source: https://docs.unity3d.com/Manual/class-Transition.html
- Unity 공식 문서 - AnyState: https://docs.unity3d.com/Manual/AnimationStateMachines.html
- Unity 공식 문서 - Animator Layers: https://docs.unity3d.com/Manual/AnimationLayers.html
- YouTube - Brackeys "How to make an Animator in Unity": https://www.youtube.com/watch?v=vApG8aYD5aI
- Unity Discussions - Interrupt Source 설명: https://discussions.unity.com/t/explanation-for-interrupt-source-in-animator-transitions
