# 2인 공유 캐릭터 아키텍처 시스템

리서치 날짜: 2026-06-28

## 개요

"2인 1체" — 두 플레이어가 하나의 캐릭터 오브젝트를 공동으로 제어하는 시스템.
OnionCat의 핵심 정체성: Cat(P1)은 이동·근접 슬래시·무적 대쉬, Onion(P2)은 마우스 조준·원거리 투사체·방향성 방패+패리.
두 입력이 동시에 하나의 Rigidbody2D를 공유하기 때문에 입력 라우팅, 우선순위, 상태 충돌을 명확히 설계해야 한다.

---

## Unity 구현 방법

### 1. 컴포넌트 분리 원칙

```
[OnionCatBody] (단일 GameObject)
├── Rigidbody2D               ← 물리(이동)
├── SpriteRenderer
├── Animator
├── HealthSystem              ← 공유 체력
│
├── CatController             ← P1 입력 처리 (이동, 슬래시, 대쉬)
└── OnionController           ← P2 입력 처리 (조준, 발사, 방패)
```

두 Controller는 같은 Rigidbody2D 참조를 공유하되, 동시에 velocity를 직접 쓰지 않도록 **이동 소유권(Move Authority)** 개념을 사용한다.

---

### 2. 이동 소유권 시스템

```csharp
public enum MoveAuthority { Cat, None }

public class SharedBodyLocomotion : MonoBehaviour
{
    public MoveAuthority CurrentAuthority { get; private set; } = MoveAuthority.Cat;

    private Rigidbody2D _rb;
    private Vector2 _catMoveInput;

    void Awake() => _rb = GetComponent<Rigidbody2D>();

    // CatController가 매 프레임 호출
    public void SetCatMoveInput(Vector2 input) => _catMoveInput = input;

    void FixedUpdate()
    {
        if (CurrentAuthority == MoveAuthority.Cat)
            _rb.linearVelocity = _catMoveInput * catSpeed;
    }

    // 대쉬 시작 시 Cat이 호출
    public void ClaimAuthority(MoveAuthority auth, float duration)
    {
        CurrentAuthority = auth;
        StartCoroutine(ReleaseAfter(duration));
    }

    private IEnumerator ReleaseAfter(float t)
    {
        yield return new WaitForSeconds(t);
        CurrentAuthority = MoveAuthority.Cat;
    }
}
```

**핵심**: 대쉬 중에는 Cat이 Authority를 독점하고 Onion 측은 방패/조준만 가능.

---

### 3. P1 CatController

```csharp
public class CatController : MonoBehaviour
{
    [SerializeField] private SharedBodyLocomotion _locomotion;
    [SerializeField] private SlashAbility _slash;
    [SerializeField] private DashAbility _dash;

    private PlayerInput _input;
    private InputAction _moveAction;
    private InputAction _slashAction;
    private InputAction _dashAction;

    void Awake()
    {
        _input = GetComponent<PlayerInput>();
        _moveAction = _input.actions["Cat/Move"];
        _slashAction = _input.actions["Cat/Slash"];
        _dashAction = _input.actions["Cat/Dash"];
    }

    void Update()
    {
        _locomotion.SetCatMoveInput(_moveAction.ReadValue<Vector2>());

        if (_slashAction.WasPressedThisFrame())
            _slash.Execute();

        if (_dashAction.WasPressedThisFrame())
            _dash.Execute(_locomotion);
    }
}
```

---

### 4. P2 OnionController

```csharp
public class OnionController : MonoBehaviour
{
    [SerializeField] private ProjectileShooter _shooter;
    [SerializeField] private ShieldAbility _shield;

    private PlayerInput _input;
    private InputAction _aimAction;
    private InputAction _fireAction;
    private InputAction _shieldAction;

    void Awake()
    {
        _input = GetComponent<PlayerInput>();
        _aimAction = _input.actions["Onion/Aim"];
        _fireAction = _input.actions["Onion/Fire"];
        _shieldAction = _input.actions["Onion/Shield"];
    }

    void Update()
    {
        Vector2 aimDir = GetAimDirection();
        _shooter.SetAimDirection(aimDir);

        if (_fireAction.WasPressedThisFrame())
            _shooter.Fire();

        _shield.SetActive(_shieldAction.IsPressed(), aimDir);
    }

    private Vector2 GetAimDirection()
    {
        // 마우스면 스크린→월드 변환, 게임패드면 스틱 값 그대로
        if (_aimAction.activeControl?.device is Mouse)
        {
            Vector3 world = Camera.main.ScreenToWorldPoint(_aimAction.ReadValue<Vector2>());
            return ((Vector2)(world - transform.position)).normalized;
        }
        return _aimAction.ReadValue<Vector2>().normalized;
    }
}
```

---

### 5. 상태 충돌 해결 규칙

| 상황 | 우선순위 | 처리 방식 |
|---|---|---|
| 대쉬 중 방패 시도 | 대쉬 우선 | 대쉬 중 Shield.SetActive 무시 |
| 방패 전개 중 이동 | 이동 허용 (속도 감소) | 방패 활성 시 CatMoveSpeed * 0.5 |
| 슬래시 중 투사체 발사 | 둘 다 허용 | 독립 실행 (공유 자원 없음) |
| 사망 → 둘 다 입력 잠금 | HealthSystem 이벤트로 | OnDeath → 두 Controller disable |

---

### 6. Input Actions 에셋 구조

```
OnionCatInputActions.inputactions
├── Cat (Action Map)
│   ├── Move        → Vector2, WASD/GamepadStick
│   ├── Slash       → Button, J/GamepadButtonSouth
│   └── Dash        → Button, K/GamepadButtonEast
└── Onion (Action Map)
    ├── Aim         → Vector2, Mouse Position/RightStick
    ├── Fire        → Button, MouseLeft/RightTrigger
    └── Shield      → Button, MouseRight/LeftTrigger
```

PlayerInput 컴포넌트를 두 개 사용하거나, 하나의 InputActions 에셋에 두 ActionMap을 두고 각 Controller가 GetActionMap으로 참조하는 방식.

---

## OnionCat 적용 포인트

1. **단일 Rigidbody2D**: 이동 충돌/물리는 Cat만 담당하고 Onion은 물리에 개입하지 않아야 함. Rigidbody2D.linearVelocity를 두 곳에서 동시에 쓰면 떨림 발생.

2. **능력 스크립터블 오브젝트화**: SlashAbility, DashAbility, ShieldAbility, ProjectileShooter를 ScriptableObject 기반으로 만들어두면 에디터에서 수치 조정이 쉬움.

3. **사망 이벤트 공유**: HealthSystem에 UnityEvent `OnDeath`를 두고 두 Controller가 구독 — 죽으면 둘 다 자동 비활성화.

4. **애니메이션 레이어 분리**: Animator에 Base Layer(이동·대쉬·사망)와 Attack Layer(슬래시·방패)를 분리해 두 플레이어 액션이 동시에 재생 가능하게.

5. **카메라 팔로우**: 공유 몸체이므로 Cinemachine이 단일 타깃(OnionCatBody)을 따라가면 됨.

---

## 참고 링크

- [Unity New Input System — Multiple Action Maps](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/ActionAssets.html)
- [PlayerInput 컴포넌트 공식 문서](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/Components.html)
- [2D Rigidbody linearVelocity 공식 문서](https://docs.unity3d.com/ScriptReference/Rigidbody2D-linearVelocity.html)
- [ScriptableObject 기반 능력 시스템 — Ryan Hipple GDC](https://www.youtube.com/watch?v=raQ3iHhE_Kk)
- [Unity 2D Character Controller 튜토리얼 — Brackeys](https://www.youtube.com/watch?v=dwcT-Dch0bA)
