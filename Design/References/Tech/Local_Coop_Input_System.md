# 2P 협동 입력 시스템 (Local Co-op Input)

리서치 날짜: 2026-06-12

---

## 개요

OnionCat은 두 플레이어가 **하나의 캐릭터 몸통**을 공유하는 특이한 구조다. Player 1(Cat)은 키보드로 몸 이동을 담당하고, Player 2(Onion)는 마우스로 조준·사격·방어를 담당한다. 두 사람이 **같은 컴퓨터에서 동시에** 키보드와 마우스를 각자 맡아 플레이한다.

Unity New Input System(UnityEngine.InputSystem)으로 이를 구현하려면 **두 개의 독립 컨트롤 스킴**을 하나의 InputActionAsset에 정의하고, 각 플레이어 핸들러가 자신의 입력만 읽도록 분리해야 한다. PlayerInputManager의 "장치 독점 배정" 기본값은 이 구조에 방해가 되므로, 직접 InputUser 또는 PlayerInput을 설정하는 접근이 필요하다.

---

## Unity 구현 방법

### 1. Input Action Asset 설계

**핵심 원칙**: 하나의 `.inputactions` 파일 안에 두 개의 Action Map과 두 개의 Control Scheme을 정의한다.

#### 1-1. Control Scheme 구성

| Control Scheme 이름 | 필수 장치 | 담당 플레이어 |
|---|---|---|
| `CatScheme` | Keyboard | Player 1 (Cat) |
| `OnionScheme` | Mouse | Player 2 (Onion) |

> **주의**: 두 스킴 모두 같은 컴퓨터의 장치를 쓰지만, "Keyboard만 필요", "Mouse만 필요"로 각각 선언한다. 이렇게 하면 PlayerInput이 컨트롤 스킴 전환 없이 각자의 장치만 바인딩한다.

#### 1-2. Action Map 구성

**Action Map: `Cat`** (Player 1용)

| Action 이름 | Action Type | Binding |
|---|---|---|
| `Move` | Value / Vector2 | WASD Composite (W=up, S=down, A=left, D=right) |
| `Slash` | Button | Space, Mouse Left Button |
| `Dash` | Button | Left Shift |

**Action Map: `Onion`** (Player 2용)

| Action 이름 | Action Type | Binding |
|---|---|---|
| `AimPosition` | Value / Vector2 | `<Mouse>/position` |
| `Fire` | Button | `<Mouse>/leftButton` |
| `Shield` | Button | `<Mouse>/rightButton` |

#### 1-3. 에디터 설정 순서

1. `Project > Create > Input Actions`로 `OnionCatInput.inputactions` 생성
2. 상단 "No Control Schemes" 클릭 → "Add Control Scheme"
   - 이름: `CatScheme` → "+ Add Device" → `Keyboard` 선택 → Required 체크
   - 이름: `OnionScheme` → "+ Add Device" → `Mouse` 선택 → Required 체크
3. "+" 클릭으로 Action Map 추가: `Cat`, `Onion` 두 개 생성
4. 각 Action Map에 위 표의 Action 추가
5. 각 바인딩 선택 시 우측 "Control Schemes" 패널에서 해당 스킴만 체크
   - Cat Action Map 바인딩들 → `CatScheme`만 체크
   - Onion Action Map 바인딩들 → `OnionScheme`만 체크

---

### 2. Player 1 (Cat) 입력 처리

Cat은 키보드 WASD 이동, Space/마우스 좌클릭 근접 공격, Shift 대시를 담당한다.

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

public class CatInputHandler : MonoBehaviour
{
    // [SerializeField] 필드 — 유니티 에디터에서 드래그 앤 드롭 설정 필요
    [SerializeField] private Rigidbody2D rb;
    [SerializeField] private float moveSpeed = 5f;

    private OnionCatInput _input;  // 자동 생성된 C# 클래스
    private Vector2 _moveInput;
    private bool _dashRequested;

    private void Awake()
    {
        _input = new OnionCatInput();

        // 콜백 등록 — Awake에서 캐싱 (Update 내 GetComponent 금지)
        _input.Cat.Move.performed += ctx => _moveInput = ctx.ReadValue<Vector2>();
        _input.Cat.Move.canceled  += ctx => _moveInput = Vector2.zero;

        _input.Cat.Slash.performed += ctx => OnSlash();
        _input.Cat.Dash.performed  += ctx => _dashRequested = true;
    }

    private void OnEnable()  { _input.Cat.Enable(); }
    private void OnDisable() { _input.Cat.Disable(); }

    private void FixedUpdate()
    {
        rb.linearVelocity = _moveInput * moveSpeed;

        if (_dashRequested)
        {
            PerformDash();
            _dashRequested = false;
        }
    }

    private void OnSlash()
    {
        // 근접 공격 로직 연결
        Debug.Log("Cat Slash!");
    }

    private void PerformDash()
    {
        // 대시 로직 연결
        Debug.Log("Cat Dash!");
    }
}
```

**WASD Composite 바인딩 방식**: Input Action Asset 에디터에서 Move Action을 선택 → "+ Binding" 대신 "+ Add Up/Down/Left/Right Composite"을 선택하면 WASD를 자동으로 Vector2로 합성해준다.

---

### 3. Player 2 (Onion) 입력 처리

Onion은 마우스 커서 위치를 **월드 좌표(World Position)**로 변환해 360도 조준에 활용한다. 마우스 좌클릭은 사격, 우클릭은 방향 방어막이다.

```csharp
using UnityEngine;
using UnityEngine.InputSystem;

public class OnionInputHandler : MonoBehaviour
{
    [SerializeField] private Transform aimIndicator;  // 조준 방향 표시용 — 드래그 앤 드롭 설정 필요
    [SerializeField] private float projectileSpeed = 10f;

    private OnionCatInput _input;
    private Camera _mainCamera;
    private Vector2 _aimWorldPos;

    private void Awake()
    {
        _input = new OnionCatInput();
        _mainCamera = Camera.main;  // Awake에서 캐싱

        _input.Onion.AimPosition.performed += ctx => UpdateAim(ctx.ReadValue<Vector2>());
        _input.Onion.Fire.performed   += ctx => OnFire();
        _input.Onion.Shield.performed += ctx => OnShieldStart();
        _input.Onion.Shield.canceled  += ctx => OnShieldEnd();
    }

    private void OnEnable()  { _input.Onion.Enable(); }
    private void OnDisable() { _input.Onion.Disable(); }

    private void UpdateAim(Vector2 screenPos)
    {
        // 스크린 좌표 → 월드 좌표 변환 (2D)
        Vector3 worldPos = _mainCamera.ScreenToWorldPoint(
            new Vector3(screenPos.x, screenPos.y, _mainCamera.nearClipPlane)
        );
        _aimWorldPos = new Vector2(worldPos.x, worldPos.y);

        // 조준 방향 계산
        Vector2 dir = _aimWorldPos - (Vector2)transform.position;
        UpdateAimVisual(dir.normalized);
    }

    private void UpdateAimVisual(Vector2 direction)
    {
        if (aimIndicator == null) return;
        float angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
        aimIndicator.rotation = Quaternion.AngleAxis(angle, Vector3.forward);
    }

    private void OnFire()
    {
        Vector2 dir = (_aimWorldPos - (Vector2)transform.position).normalized;
        Debug.Log($"Onion Fire toward {dir}");
        // ProjectilePool에서 투사체 꺼내서 dir 방향으로 발사
    }

    private void OnShieldStart()
    {
        Vector2 shieldDir = (_aimWorldPos - (Vector2)transform.position).normalized;
        Debug.Log($"Shield raised toward {shieldDir}");
        // 방향 방어막 활성화
    }

    private void OnShieldEnd()
    {
        Debug.Log("Shield lowered");
        // 방어막 비활성화
    }
}
```

**핵심**: `Camera.ScreenToWorldPoint()`에 반드시 `z = camera.nearClipPlane`을 설정해야 한다. z가 0이면 카메라 위치 자체가 반환되어 잘못된 월드 좌표가 된다.

---

### 4. 두 플레이어 동시 입력 연결

OnionCat의 "한 몸 두 조종사" 구조에서는 **두 개의 독립 핸들러 스크립트**를 하나의 게임오브젝트(또는 부모-자식 구조)에 붙이는 것이 가장 단순하다.

#### 추천 구조: 단일 입력 매니저 + 개별 핸들러

```csharp
// OnionCatInputManager.cs — 메인 캐릭터 오브젝트에 부착
using UnityEngine;
using UnityEngine.InputSystem;

public class OnionCatInputManager : MonoBehaviour
{
    // 두 핸들러를 같은 오브젝트의 컴포넌트로 참조
    // 유니티 에디터에서 드래그 앤 드롭 설정 필요
    [SerializeField] private CatInputHandler catHandler;
    [SerializeField] private OnionInputHandler onionHandler;

    // PlayerInput은 사용하지 않음.
    // 각 핸들러가 자신의 OnionCatInput 인스턴스를 Awake에서 직접 생성하고
    // 각자의 Action Map만 Enable 한다.
    // CatInputHandler  → _input.Cat.Enable()
    // OnionInputHandler → _input.Onion.Enable()
}
```

**같은 게임오브젝트에 PlayerInput 두 개는 불가능**하다. 대신 `PlayerInput` 컴포넌트 없이, 자동 생성된 C# 클래스(`OnionCatInput`)를 각 핸들러에서 `new`로 인스턴스화하면 두 핸들러가 독립적으로 입력을 읽는다.

#### 게임오브젝트 계층 예시

```
[OnionCat Character]
├── OnionCatInputManager.cs
├── CatInputHandler.cs          ← Cat Action Map만 Enable
├── OnionInputHandler.cs        ← Onion Action Map만 Enable
├── CharacterMovement.cs        ← Cat에서 받은 moveInput 적용
└── CombatController.cs         ← Slash/Fire/Shield 이벤트 수신
```

#### 이벤트 기반 연결 (권장)

핸들러 간 직접 참조를 피하려면 C# 이벤트로 분리한다:

```csharp
// CatInputHandler.cs
public event System.Action<Vector2> OnMoveInput;
public event System.Action OnSlashTriggered;
public event System.Action OnDashTriggered;

// _input.Cat.Move.performed 콜백 안에서:
OnMoveInput?.Invoke(ctx.ReadValue<Vector2>());
```

```csharp
// CharacterMovement.cs
private void Awake()
{
    var cat = GetComponent<CatInputHandler>();
    cat.OnMoveInput      += HandleMove;
    cat.OnDashTriggered  += HandleDash;
}
```

---

### 5. 주요 코드 패턴

#### 5-1. Input System C# 클래스 자동 생성

`.inputactions` 파일 선택 → Inspector → "Generate C# Class" 체크 → Apply. 이후 `new OnionCatInput()`으로 인스턴스 생성 가능.

#### 5-2. Action Map별 Enable/Disable

```csharp
var input = new OnionCatInput();

// Cat 조종사만 활성화
input.Cat.Enable();
input.Onion.Disable();  // 또는 처음부터 Enable 안 함

// Onion 조종사만 활성화
input.Onion.Enable();
input.Cat.Disable();

// 둘 다 동시 활성화 (OnionCat 정상 플레이)
input.Cat.Enable();
input.Onion.Enable();
```

#### 5-3. 마우스 월드 좌표 — Update vs 콜백 비교

```csharp
// 방법 A: 콜백 (performed) — 마우스가 움직일 때만 호출, 권장
_input.Onion.AimPosition.performed += ctx => {
    Vector2 screen = ctx.ReadValue<Vector2>();
    _aimWorldPos = ScreenToWorld(screen);
};

// 방법 B: Update 폴링 — 매 프레임 읽기
void Update() {
    Vector2 screen = Mouse.current.position.ReadValue();
    _aimWorldPos = ScreenToWorld(screen);
}

// 공통 변환 함수
Vector2 ScreenToWorld(Vector2 screenPos)
{
    Vector3 w = _mainCamera.ScreenToWorldPoint(
        new Vector3(screenPos.x, screenPos.y, _mainCamera.nearClipPlane));
    return new Vector2(w.x, w.y);
}
```

> `AimPosition.performed`는 마우스가 이동할 때마다 트리거된다. 마우스가 정지하면 콜백이 오지 않으므로, 마지막 `_aimWorldPos`를 캐시해서 사용한다.

#### 5-4. 방향 계산 (360도 조준)

```csharp
// 캐릭터 → 마우스 방향 벡터
Vector2 dir = (_aimWorldPos - (Vector2)transform.position).normalized;

// 각도 (0~360, 오른쪽이 0도, 반시계 증가)
float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;

// 방어막 섹터 판정 예시 (마우스가 오른쪽 90도 범위 안에 있으면)
bool isRight = angle > -45f && angle < 45f;
```

#### 5-5. 버튼 상태 읽기 패턴

```csharp
// 콜백 방식 (권장)
_input.Onion.Fire.performed += ctx => StartFire();   // 누른 순간
_input.Onion.Fire.canceled  += ctx => StopFire();    // 뗀 순간

// 직접 폴링 방식 (Update 안에서)
if (Mouse.current.leftButton.wasPressedThisFrame)  { /* 누른 순간 */ }
if (Mouse.current.leftButton.isPressed)            { /* 누르는 동안 */ }
if (Mouse.current.leftButton.wasReleasedThisFrame) { /* 뗀 순간 */ }
```

---

## OnionCat 적용 포인트

### 핵심 설계 결정사항

| 이슈 | 결정 | 이유 |
|---|---|---|
| PlayerInput 컴포넌트 사용 여부 | **사용 안 함** | 한 오브젝트에 두 개 불가, 불필요한 복잡도 |
| 입력 읽기 방식 | **C# 자동 생성 클래스 + 콜백** | 명시적, 타입 안전, CLAUDE.md 코딩 컨벤션 준수 |
| 마우스 위치 처리 | **performed 콜백 + 캐시** | Update 매 프레임 읽기보다 효율적 |
| 두 핸들러 통신 | **C# 이벤트** | 직접 참조 의존성 제거 |

### 주의해야 할 함정

1. **`_mainCamera` null 체크**: `Camera.main`은 카메라 오브젝트가 없으면 null. Awake에서 캐싱 후 null 확인 필수.

2. **`nearClipPlane` vs 고정 z**: `ScreenToWorldPoint`의 z는 카메라 기준 거리. 2D 게임에서는 `Camera.main.nearClipPlane` (보통 0.3)을 쓰거나, 카메라가 z=-10에 있으면 `10f`를 쓰는 경우도 있다. 결과가 이상하면 z 값을 조정.

3. **Action Map 이름 오타**: 자동 생성 C# 클래스의 프로퍼티명은 `.inputactions`의 Action Map 이름과 정확히 일치. "Cat"이면 `input.Cat`, "Onion"이면 `input.Onion`.

4. **OnDisable에서 반드시 Disable**: 씬 전환이나 캐릭터 사망 시 Enable된 채로 남으면 NullReferenceException 발생.

5. **Slash가 마우스 좌클릭도 받는 경우**: Cat의 Slash에 `<Mouse>/leftButton`도 바인딩하면, Onion의 Fire(`<Mouse>/leftButton`)와 중복된다. 의도한 경우라면 괜찮지만, 둘이 분리되어야 한다면 Slash는 Space만 바인딩.

### 확장 고려사항

- **싱글 플레이어 모드**: `input.Onion.Disable()` 후 Cat의 Action Map에 마우스 바인딩을 추가하거나, 자동 조준 AI로 대체.
- **컨트롤러 지원**: CatScheme에 Gamepad를 추가 장치로 넣고, OnionScheme에 Gamepad 우측 스틱을 추가하면 두 컨트롤러로 플레이 가능.
- **입력 리매핑**: `InputActionRebindingExtensions.PerformInteractiveRebinding()`으로 런타임 키 변경 가능.

---

## 참고 링크

- **Unity Input System 공식 문서 (PlayerInput 컴포넌트)**
  `https://docs.unity3d.com/Packages/com.unity.inputsystem@1.5/manual/PlayerInput.html`

- **Unity Input System 공식 문서 (User Management / InputUser)**
  `https://docs.unity3d.com/Packages/com.unity.inputsystem@1.5/manual/UserManagement.html`

- **Unity Input System 공식 문서 (Control Schemes)**
  `https://docs.unity3d.com/Packages/com.unity.inputsystem@1.5/manual/ActionBindings.html#control-schemes`

- **Unity Input System 공식 문서 (Mouse)**
  `https://docs.unity3d.com/Packages/com.unity.inputsystem@1.5/manual/Mouse.html`

- **Unity Input System 공식 문서 (PlayerInputManager)**
  `https://docs.unity3d.com/Packages/com.unity.inputsystem@1.5/manual/PlayerInputManager.html`

- **Game Dev Beginner — New Input System 완전 가이드**
  `https://gamedevbeginner.com/input-in-unity-made-easy-complete-guide-to-the-new-system/`

- **Game Dev Beginner — 마우스 위치 월드 좌표 변환**
  `https://gamedevbeginner.com/how-to-convert-the-mouse-position-to-world-space-in-unity-2d-3d/`

- **One Wheel Studio — New Input System 튜토리얼**
  `https://onewheelstudio.com/blog/2021/5/8/unitys-new-input-system`

- **Unity Discussions — 키보드 두 플레이어 Input System**
  `https://discussions.unity.com/t/how-to-use-the-new-inputsystem-for-2-players-on-one-keyboard/800856`

- **Unity Discussions — 로컬 멀티플레이어 keyboard+mouse 동일 장치**
  `https://discussions.unity.com/t/local-multiplayer-keyboard-and-the-mouse-as-the-same-input-device/930191`

- **Robot Monkey Brain — Pair Keyboard and Mouse to InputUser**
  `https://www.robotmonkeybrain.com/unity-input-system-how-to-pair-keyboard-and-mouse-to-the-same-inputuser/`

- **Unity Input System 샘플 프로젝트 (Simple Multiplayer)**
  Package Manager → Input System → Samples → Simple Multiplayer
