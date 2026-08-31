# Hybrid Split-Input Onboarding Screen (혼합 입력 방식 온보딩 화면)

리서치 날짜: 2026-08-31

## 개요

P1(키보드/게임패드)과 P2(마우스)가 완전히 다른 입력 장치를 사용하는 비대칭 코옵 게임의 첫 실행 세션 온보딩 설계.  
OnionCat은 P1이 이동/슬래시/대쉬를 담당하고 P2가 마우스 에임/투사체/방패를 담당하는 구조라, 일반적인 "단일 플레이어 튜토리얼" 패턴을 그대로 쓸 수 없음.

**핵심 문제:**
1. 두 플레이어가 동시에 서로 다른 조작을 배워야 함
2. "같이 배우면서도 개별 역할을 이해"하는 경험이 필요
3. P2(마우스+키 없음)가 이동 없이 에임만 담당한다는 직관에서 벗어난 설계를 설명해야 함

---

## Unity 구현 방법

### 전체 흐름 (5단계)

```
[게임 최초 실행]
    → 컨트롤러 감지 화면 (어떤 기기가 연결됐는지)
    → 역할 배정 화면 (P1 = 움직이는 고양이, P2 = 등 위의 작물)
    → 분리 튜토리얼 패널 (P1 조작 / P2 조작 동시 표시)
    → 샌드박스 연습 방 (실제로 같이 해보기)
    → 튜토리얼 완료 → 첫 런 시작
```

---

### 1단계: 컨트롤러 감지 및 연결 화면

```csharp
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;
using TMPro;

public class InputOnboardingDetector : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI p1StatusText;
    [SerializeField] private TextMeshProUGUI p2StatusText;
    [SerializeField] private Button continueButton;

    private bool _p1Ready, _p2Ready;

    void OnEnable()
    {
        InputSystem.onDeviceChange += OnDeviceChange;
        RefreshStatus();
    }

    void OnDisable() => InputSystem.onDeviceChange -= OnDeviceChange;

    void OnDeviceChange(InputDevice device, InputDeviceChange change) => RefreshStatus();

    void RefreshStatus()
    {
        // P1: 게임패드 또는 키보드 WASD
        bool hasGamepad = Gamepad.all.Count > 0;
        bool hasKeyboard = Keyboard.current != null;
        _p1Ready = hasGamepad || hasKeyboard;
        p1StatusText.text = hasGamepad ? "🎮 게임패드 감지됨" : (hasKeyboard ? "⌨ 키보드 (WASD) 사용" : "❌ 입력 없음");

        // P2: 마우스 필수
        _p2Ready = Mouse.current != null;
        p2StatusText.text = _p2Ready ? "🖱 마우스 감지됨" : "❌ 마우스 없음";

        continueButton.interactable = _p1Ready && _p2Ready;
    }
}
```

> **[SerializeField] 변수**: `p1StatusText`, `p2StatusText`, `continueButton` → 유니티 에디터에서 드래그 앤 드롭 설정 필요

---

### 2단계: 역할 배정 화면 (Role Assignment Panel)

두 개의 패널을 나란히 배치:
- 왼쪽 패널: P1 (고양이) — 게임패드/키보드 아이콘 + 역할 설명
- 오른쪽 패널: P2 (작물/양파) — 마우스 아이콘 + 역할 설명

```csharp
public class RoleAssignmentUI : MonoBehaviour
{
    [SerializeField] private GameObject p1Panel;  // P1 역할 설명 패널
    [SerializeField] private GameObject p2Panel;  // P2 역할 설명 패널
    [SerializeField] private Button readyButton;

    // 두 플레이어가 각자의 패널에서 "확인" 버튼을 누르면 다음으로 진행
    private bool _p1Confirmed, _p2Confirmed;

    public void P1Confirm() { _p1Confirmed = true; CheckBothReady(); }
    public void P2Confirm() { _p2Confirmed = true; CheckBothReady(); }

    void CheckBothReady()
    {
        if (_p1Confirmed && _p2Confirmed)
            readyButton.interactable = true;
    }
}
```

**UI 텍스트 예시:**

| P1 패널 | P2 패널 |
|---------|---------|
| "당신은 **고양이**입니다" | "당신은 **등 위의 양파**입니다" |
| 🎮 WASD or 스틱 → 이동 | 🖱 마우스 → 조준 방향 |
| A버튼 / Space → 대쉬 (무적) | 좌클릭 → 씨앗 발사 |
| X버튼 / Z → 슬래시 (근접) | 우클릭 → 방패 / 패리 |
| "적 뒤로 파고들어라" | "방향을 잡고 커버해라" |

---

### 3단계: 분리 입력 안내 애니메이션 (Split Tutorial Panel)

화면을 반으로 나눠 P1 조작과 P2 조작을 동시에 애니메이션으로 표시.  
각 패널에 해당 입력 장치 아이콘이 실시간 하이라이트됨.

```csharp
public class SplitTutorialPanel : MonoBehaviour
{
    [Header("P1 Input Icons")]
    [SerializeField] private Image p1MoveIcon;
    [SerializeField] private Image p1SlashIcon;
    [SerializeField] private Image p1DashIcon;

    [Header("P2 Input Icons")]
    [SerializeField] private Image p2AimIcon;
    [SerializeField] private Image p2FireIcon;
    [SerializeField] private Image p2ShieldIcon;

    [SerializeField] private Color activeColor = Color.yellow;
    [SerializeField] private Color inactiveColor = Color.gray;

    void Update()
    {
        // P1 입력 실시간 하이라이트
        var gamepad = Gamepad.current;
        bool moving = gamepad != null && gamepad.leftStick.ReadValue().magnitude > 0.1f;
        p1MoveIcon.color = moving ? activeColor : inactiveColor;

        bool slash = gamepad != null && gamepad.buttonSouth.isPressed;
        p1SlashIcon.color = slash ? activeColor : inactiveColor;

        bool dash = gamepad != null && gamepad.buttonEast.isPressed;
        p1DashIcon.color = dash ? activeColor : inactiveColor;

        // P2 입력 실시간 하이라이트
        var mouse = Mouse.current;
        p2AimIcon.color = activeColor; // 마우스는 항상 에임 중
        p2FireIcon.color = (mouse != null && mouse.leftButton.isPressed) ? activeColor : inactiveColor;
        p2ShieldIcon.color = (mouse != null && mouse.rightButton.isPressed) ? activeColor : inactiveColor;
    }
}
```

---

### 4단계: 샌드박스 연습 방

실제 전투 없이 조작만 익히는 빈 방. 더미 타겟(마네킹)이 있어:
- P1: 슬래시 → 타겟에 피해 + 파티클
- P2: 발사 → 타겟에 피해 + 파티클
- P2: 방패 → 연습용 투사체 차단 데모 (자동으로 날아오는 안전 투사체)

```csharp
public class SandboxTutorialRoom : MonoBehaviour
{
    [SerializeField] private Transform dummyTarget;
    [SerializeField] private GameObject practiceProjectilePrefab;
    [SerializeField] private float spawnInterval = 3f;

    void Start() => InvokeRepeating(nameof(SpawnPracticeProjectile), 2f, spawnInterval);

    void SpawnPracticeProjectile()
    {
        // P2 방패 연습용 — 느린 속도로 캐릭터를 향해 발사
        var proj = Instantiate(practiceProjectilePrefab, dummyTarget.position, Quaternion.identity);
        // Projectile 컴포넌트에서 속도를 낮게 설정
    }
}
```

**완료 조건:**
- P1이 슬래시 3회 + 대쉬 2회
- P2가 발사 3회 + 방패 1회 → 모두 충족 시 "준비 완료!" UI + 첫 런 시작 버튼 활성화

```csharp
public class SandboxCompletionTracker : MonoBehaviour
{
    private int _p1Slash, _p1Dash, _p2Fire, _p2Shield;
    [SerializeField] private Button startRunButton;

    public void OnP1Slash() { _p1Slash++; CheckCompletion(); }
    public void OnP1Dash() { _p1Dash++; CheckCompletion(); }
    public void OnP2Fire() { _p2Fire++; CheckCompletion(); }
    public void OnP2Shield() { _p2Shield++; CheckCompletion(); }

    void CheckCompletion()
    {
        if (_p1Slash >= 3 && _p1Dash >= 2 && _p2Fire >= 3 && _p2Shield >= 1)
            startRunButton.gameObject.SetActive(true);
    }
}
```

---

## OnionCat 적용 포인트

### 비대칭 입력 명확화의 핵심
P2(마우스 전담)가 이동하지 않는다는 점은 직관에 반함. 역할 배정 화면에서 반드시 **"당신은 이동하지 않습니다. 방향을 잡으세요."** 를 명시해야 혼란 방지.  
→ UI 문구: "작물은 고양이 등 위에 있습니다. 마우스로 세상을 바라보세요."

### "같이 해야 완성" 메시지 전달
튜토리얼의 마지막 미션은 P1+P2 협력이 필요한 조합 공격 시연:  
"P1이 슬래시로 적을 날리면 P2가 공중에서 사격" → 두 플레이어가 동시에 해야 완료.  
이 경험이 게임의 핵심 필러를 자연스럽게 전달.

### 스킵 기능 필수
숙련 플레이어가 재런 시 불편함 없도록:
- 2회차 이후 "스킵" 버튼 표시 (PlayerPrefs에 `OnboardingComplete` 플래그 저장)
- `PlayerPrefs.SetInt("OnboardingComplete", 1)` 저장

### New Input System 연동 주의
`PlayerInput` 컴포넌트를 사용 시, 온보딩 화면에서는 `SwitchCurrentActionMap("UI")`로 전환.  
게임플레이 액션맵으로 전환하기 전까지 게임 입력 차단 필수.

---

## 참고 링크

- Unity New Input System 공식 문서: https://docs.unity3d.com/Packages/com.unity.inputsystem@latest
- 비대칭 코옵 UX 설계 사례 (Keep Talking and Nobody Explodes): https://www.gamedeveloper.com/design/designing-keep-talking-and-nobody-explodes
- Split-screen co-op UI best practices: https://www.gamedeveloper.com/design/co-op-game-ux-lessons
- Unity 튜토리얼 시스템 설계: https://unity.com/how-to/create-great-tutorials
