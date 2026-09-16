# Asymmetric Co-op Input System (비대칭 협력 입력 시스템)

리서치 날짜: 2026-09-16

## 개요

두 플레이어가 **하나의 게임 오브젝트**를 공유하면서 서로 다른 입력 방식으로 제어하는 시스템.
OnionCat의 핵심 기둥: Cat(Player 1)이 이동/근접을 담당하고, Crop(Player 2)이 마우스 조준/원거리/방패를 담당하는데, 둘 다 같은 `CatBody` 오브젝트를 제어함.

### 왜 중요한가?
- 일반 2인 협력은 각자 독립된 캐릭터를 제어함
- OnionCat은 **1개의 캐릭터 = 2개의 입력 스트림** → 입력 충돌, 우선순위, 애니메이션 동기화 문제가 발생
- 초기 설계가 잘못되면 코드 전체를 갈아엎어야 함

---

## Unity 구현 방법

### 1. New Input System으로 두 개의 Action Map 분리

```csharp
// PlayerInputManager가 아닌 수동 InputAction 바인딩
// Assets/Settings/CatInputActions.inputactions 에 두 개의 Action Map:
// - "CatPlayer" (Player 1: WASD + Keyboard 또는 Gamepad Left Stick)
// - "CropPlayer" (Player 2: Mouse Aim + 마우스 버튼 또는 Gamepad Right Stick)

public class SharedBodyInputRouter : MonoBehaviour
{
    [SerializeField] private InputActionAsset inputActions;
    
    private InputAction _moveAction;       // Cat 전용
    private InputAction _dashAction;       // Cat 전용
    private InputAction _aimAction;        // Crop 전용
    private InputAction _shootAction;      // Crop 전용
    private InputAction _shieldAction;     // Crop 전용

    private void Awake()
    {
        var catMap  = inputActions.FindActionMap("CatPlayer");
        var cropMap = inputActions.FindActionMap("CropPlayer");

        _moveAction   = catMap.FindAction("Move");
        _dashAction   = catMap.FindAction("Dash");
        _aimAction    = cropMap.FindAction("Aim");
        _shootAction  = cropMap.FindAction("Shoot");
        _shieldAction = cropMap.FindAction("Shield");
    }

    private void OnEnable()
    {
        inputActions.Enable();
    }

    private void OnDisable()
    {
        inputActions.Disable();
    }
}
```

### 2. 컴포넌트 분리 원칙

```
CatBody (GameObject)
├── CatMovementController   ← _moveAction, _dashAction 구독
├── CatMeleeController      ← Cat 공격 버튼 구독
├── CropAimController       ← _aimAction 구독 (월드 좌표 변환)
├── CropShooterController   ← _shootAction 구독
└── CropShieldController    ← _shieldAction 구독
```

각 컨트롤러가 자신의 Action만 구독 → 입력 충돌 없음.

### 3. Mouse Aim → World Position 변환 (Crop 조준)

```csharp
public class CropAimController : MonoBehaviour
{
    private InputAction _aimAction;
    private Camera _mainCamera;
    
    public Vector2 AimDirection { get; private set; }

    private void Awake()
    {
        _mainCamera = Camera.main;
        // inputActions에서 가져오거나 SharedBodyInputRouter 참조
    }

    private void Update()
    {
        // 마우스/게임패드 우스틱 모두 지원
        Vector2 rawAim = _aimAction.ReadValue<Vector2>();
        
        if (IsMouseControl()) // 마우스면 스크린→월드 변환
        {
            Vector3 worldPos = _mainCamera.ScreenToWorldPoint(rawAim);
            AimDirection = ((Vector2)worldPos - (Vector2)transform.position).normalized;
        }
        else // 게임패드 우스틱이면 직접 방향값 사용
        {
            AimDirection = rawAim.normalized;
        }
    }
    
    private bool IsMouseControl()
    {
        // InputSystem의 lastUsedDevice로 판별
        return Mouse.current != null && Mouse.current.wasUpdatedThisFrame;
    }
}
```

### 4. 혼합 입력 시나리오 처리

```
시나리오 A: Player1=키보드/마우스, Player2=게임패드
→ CatMap: Keyboard WASD + Space(Dash) + Q(Melee)
→ CropMap: Gamepad Right Stick(Aim) + RT(Shoot) + LT(Shield)

시나리오 B: Player1=게임패드1, Player2=키보드/마우스
→ CatMap: Gamepad1 Left Stick + A(Dash) + X(Melee)
→ CropMap: Mouse Position(Aim) + LMB(Shoot) + RMB(Shield)

시나리오 C: 솔로 (AI 파트너)
→ CatMap: 사람이 조작
→ CropMap: CropAI 스크립트가 AimDirection / Shoot 직접 설정
```

```csharp
// AI 파트너 시 CropAimController 대신 CropAIController 활성화
public class CropAIController : MonoBehaviour
{
    [SerializeField] private CropAimController _aimController;
    [SerializeField] private CropShooterController _shooter;
    
    private Transform _nearestEnemy;
    
    private void Update()
    {
        _nearestEnemy = FindNearestEnemy();
        if (_nearestEnemy != null)
        {
            Vector2 dir = (_nearestEnemy.position - transform.position).normalized;
            _aimController.SetAimDirectionOverride(dir); // AI가 방향을 직접 주입
            _shooter.TryShoot();
        }
    }
}
```

### 5. 애니메이션 우선순위 처리

```csharp
// Cat 이동과 Crop 조준이 동시에 애니메이션에 영향을 줄 때
// Animator의 파라미터를 각 컨트롤러가 담당

public class CatBodyAnimator : MonoBehaviour
{
    private Animator _animator;
    
    [SerializeField] private CatMovementController _catMovement;
    [SerializeField] private CropAimController _cropAim;

    private void Update()
    {
        // 이동 방향은 Cat이 결정
        _animator.SetFloat("MoveX", _catMovement.MoveInput.x);
        _animator.SetFloat("MoveY", _catMovement.MoveInput.y);
        
        // 조준 방향은 Crop이 결정 (Upper body layer 분리 권장)
        _animator.SetFloat("AimX", _cropAim.AimDirection.x);
        _animator.SetFloat("AimY", _cropAim.AimDirection.y);
        
        // 이동 중 조준: Blend Tree로 처리
        _animator.SetBool("IsMoving", _catMovement.IsMoving);
        _animator.SetBool("IsAiming", _cropAim.IsAiming);
    }
}
```

---

## OnionCat 적용 포인트

### 입력 라우터 설계 순서 (권장)
1. `SharedBodyInputRouter` 먼저 구현 (Action Map 2개 활성화)
2. `CatMovementController`에 이동/대시 로직
3. `CropAimController`에 마우스/스틱 조준 변환
4. `CropShooterController`에 발사 로직
5. `CropShieldController`에 방패/패리 로직
6. 마지막으로 솔로 AI 모드 추가

### 핵심 규칙
- **절대 하나의 Update()에서 두 플레이어 입력을 동시에 처리하지 말 것**
- 각 컴포넌트가 자신의 입력만 담당 → 나중에 AI로 교체 쉬움
- `[SerializeField]`로 Inspector에서 컨트롤러 연결

### 솔로 모드 전환 패턴
```csharp
public void SetCoopMode(bool isCoop)
{
    _cropAimController.enabled  = isCoop;
    _cropShooterController.enabled = isCoop;
    _cropAIController.enabled   = !isCoop;
}
```

---

## 참고 링크

- Unity New Input System 공식 문서: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/index.html
- Action Map 멀티플레이어 설정: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/PlayerInputManager.html
- Screen to World Point: https://docs.unity3d.com/ScriptReference/Camera.ScreenToWorldPoint.html
- 비대칭 협력 게임 설계 GDC Talk: GDC Vault "Asymmetric game design"으로 검색
