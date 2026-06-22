# 컨트롤러 진동 & 햅틱 피드백 (Controller Rumble & Haptic Feedback)

리서치 날짜: 2026-06-22

## 개요

컨트롤러 진동(Rumble)은 게임의 타격감·몰입감을 물리적으로 전달하는 피드백 시스템이다. Unity New Input System의 `IDualMotorRumble` 인터페이스를 통해 **왼쪽 모터(저주파, 둔한 진동)** + **오른쪽 모터(고주파, 날카로운 진동)** 를 개별 제어한다. OnionCat은 2인 협동 게임이므로 각 플레이어의 컨트롤러에 독립적으로 진동을 줄 수 있어 게임플레이 피드백의 품질을 크게 높인다.

---

## Unity 구현 방법

### 사전 조건

- Unity New Input System 패키지 설치 필요
- `using UnityEngine.InputSystem;`

### 기본 API

```csharp
// 진동 시작 (왼쪽 모터 속도, 오른쪽 모터 속도) — 0.0f ~ 1.0f
Gamepad.current.SetMotorSpeeds(0.25f, 0.75f);

// 진동 정지
Gamepad.current.SetMotorSpeeds(0f, 0f);

// 일시 정지 (상태 유지, 하드웨어만 멈춤)
InputSystem.PauseHaptics();

// 재개
InputSystem.ResumeHaptics();

// 완전 초기화 (상태도 초기화)
InputSystem.ResetHaptics();
```

**왼쪽 모터**: 저주파 → 강한 충격, 폭발, 착지  
**오른쪽 모터**: 고주파 → 날카로운 타격, 총기 발사, 아이템 픽업

### RumbleManager 싱글턴 구현

```csharp
public class RumbleManager : MonoBehaviour
{
    public static RumbleManager Instance { get; private set; }

    private Coroutine _rumbleCoroutine;

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    // 지정 시간 동안 진동 후 자동 정지
    public void Rumble(float lowFreq, float highFreq, float duration, Gamepad gamepad = null)
    {
        var pad = gamepad ?? Gamepad.current;
        if (pad == null) return;

        if (_rumbleCoroutine != null)
            StopCoroutine(_rumbleCoroutine);
        _rumbleCoroutine = StartCoroutine(RumbleRoutine(pad, lowFreq, highFreq, duration));
    }

    private IEnumerator RumbleRoutine(Gamepad pad, float low, float high, float duration)
    {
        pad.SetMotorSpeeds(low, high);
        yield return new WaitForSeconds(duration);
        pad.SetMotorSpeeds(0f, 0f);
    }

    // 일시정지 메뉴 진입 시 호출
    public void PauseAll() => InputSystem.PauseHaptics();
    public void ResumeAll() => InputSystem.ResumeHaptics();

    private void OnApplicationFocus(bool hasFocus)
    {
        if (!hasFocus) InputSystem.PauseHaptics();
        else InputSystem.ResumeHaptics();
    }

    private void OnDestroy() => InputSystem.ResetHaptics();
}
```

### 2인 컨트롤러 독립 제어

OnionCat은 Cat(P1)과 Crop(P2)이 각각 다른 컨트롤러를 사용:

```csharp
// 플레이어별 Gamepad 참조 보관
public class PlayerInputHolder : MonoBehaviour
{
    public Gamepad AssignedGamepad { get; private set; }

    private void OnEnable()
    {
        // PlayerInput 컴포넌트로부터 gamepad 획득
        var pi = GetComponent<PlayerInput>();
        AssignedGamepad = pi.devices.OfType<Gamepad>().FirstOrDefault();
    }
}

// 사용 예: Cat이 피격 시 P1 컨트롤러만 진동
void OnHit()
{
    var gamepad = GetComponent<PlayerInputHolder>().AssignedGamepad;
    RumbleManager.Instance.Rumble(0.8f, 0.3f, 0.2f, gamepad);
}
```

### 진동 프리셋 정의

```csharp
public static class RumblePresets
{
    // Cat 밀리 공격 히트
    public static (float low, float high, float dur) MeleeHit    = (0.5f, 0.8f, 0.1f);
    // Crop 원거리 발사
    public static (float low, float high, float dur) ProjectileFire = (0.1f, 0.6f, 0.05f);
    // 플레이어 피격
    public static (float low, float high, float dur) PlayerDamaged = (0.9f, 0.4f, 0.25f);
    // 보스 사망
    public static (float low, float high, float dur) BossDeath    = (1.0f, 1.0f, 0.8f);
    // 아이템 픽업
    public static (float low, float high, float dur) ItemPickup   = (0.0f, 0.4f, 0.1f);
}
```

---

## 플랫폼 지원 범위

| 컨트롤러 | Windows | macOS | Linux | Console |
|---------|---------|-------|-------|---------|
| Xbox    | ✅       | ❌     | ❌     | ✅ (Xbox) |
| PS4/PS5 | ✅       | ✅     | ❌     | ✅ (PS4) |
| Switch Pro | ❌    | ❌     | ❌     | ✅ (Switch) |
| Android (Unity 6000.6+) | ✅ | - | - | - |

> 지원되지 않는 플랫폼/컨트롤러에서 `SetMotorSpeeds`를 호출해도 오류 없이 무시됨 → 안전하게 호출 가능

---

## OnionCat 적용 포인트

### 진동 설계 원칙

1. **짧고 강하게**: 0.05s~0.3s 범위, 너무 길면 불쾌감
2. **역할별 차별화**:
   - **Cat 히트**: 저주파 강조 (둔탁한 물리적 타격감)
   - **Crop 발사**: 고주파 강조 (날카로운 총기 반동)
3. **일시정지 시 반드시 PauseHaptics()**: 메뉴 중 진동 지속되면 불쾌

### 구현 우선순위 (초보자용)

1. `RumbleManager` 싱글턴 먼저 구현
2. 플레이어 피격 시 진동 연결 (가장 체감 큰 순간)
3. 보스 사망 롱 진동 추가
4. 세부 프리셋 조정 (마지막에)

### 주의사항

- `Gamepad.current`는 마지막 입력한 패드를 반환 → 2인 플레이 시 반드시 `PlayerInput`에서 패드 별도 추적
- 장시간 최대 속도 진동 시 모터 과열 방지를 위해 하드웨어가 자동 차단할 수 있음
- 일시정지 메뉴·로딩 화면에서는 항상 `PauseHaptics()` 호출

---

## 참고 링크

- Unity Input System 공식 Gamepad 문서: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/Gamepad.html
- IDualMotorRumble API: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.0/api/UnityEngine.InputSystem.Haptics.IDualMotorRumble.html
- GitHub InputSystem Gamepad.md: https://github.com/Unity-Technologies/InputSystem/blob/develop/Packages/com.unity.inputsystem/Documentation~/Gamepad.md
- Unity 토론: https://discussions.unity.com/t/haptic-feedback-on-different-devices/759474
- YouTube 튜토리얼: https://www.youtube.com/watch?v=SmmBC-yCJ28
