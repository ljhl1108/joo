# 프레임 데이터 & 캔슬 윈도우 (Frame Data & Cancel Windows)

리서치 날짜: 2026-10-26

## 개요

**프레임 데이터**는 액션 게임의 모든 공격 동작을 "발동 전(startup) / 활성(active) / 회복(recovery)" 세 구간으로 나눠 정의하는 방법이다. **캔슬 윈도우**는 회복 중 특정 프레임에서 다른 행동으로 취소할 수 있는 타이밍이다.

격투 게임(Street Fighter, Tekken)에서 발전했지만, 오늘날 대부분의 액션 게임(Hades, Dark Souls, Devil May Cry)에 암묵적으로 내재돼 있다. OnionCat의 고양이 할퀴기·대쉬·특수 공격처럼 "느낌 좋은 전투"의 이면에는 이 구조가 있다.

---

## 세 구간 정의

```
[ 발동 전 ] → [ 활성 ] → [ 회복 ]
   startup       active    recovery
  (예비 동작)   (히트박스)  (후딜레이)
```

| 구간 | 의미 | OnionCat 예시 |
|------|------|-------------|
| **startup** | 입력 → 히트박스 활성화 전 | 할퀴기 예비 동작 (40ms) |
| **active** | 히트박스가 살아있는 구간 | 부채꼴 판정 (100ms) |
| **recovery** | 활성 후 ~ 다음 행동 가능까지 | 후딜레이 (80ms) |

총 공격 시간 = startup + active + recovery. OnionCat 기본 할퀴기라면 약 220ms.

---

## Unity 구현 방법

### 방법 1: AnimationEvent + C# 코드로 구간 관리 (권장)

```csharp
// ClawAttack.cs
public class ClawAttack : MonoBehaviour
{
    [Header("Frame Data (ms)")]
    [SerializeField] float startupMs = 40f;
    [SerializeField] float activeMs = 100f;
    [SerializeField] float recoveryMs = 80f;

    // 취소 가능 구간: recovery의 앞 50% 이후부터
    [SerializeField] float cancelWindowStart = 0.5f; // recovery 시작 후 몇 %부터

    bool _isActive;
    bool _inRecovery;
    bool _canCancel;

    public void TriggerAttack()
    {
        StartCoroutine(AttackSequence());
    }

    IEnumerator AttackSequence()
    {
        // Startup
        _canCancel = false;
        yield return new WaitForSeconds(startupMs / 1000f);

        // Active — 히트박스 활성화
        _isActive = true;
        ActivateHitbox();
        yield return new WaitForSeconds(activeMs / 1000f);

        // Recovery
        _isActive = false;
        DeactivateHitbox();
        _inRecovery = true;

        float recoveryElapsed = 0f;
        float recoveryTotal = recoveryMs / 1000f;
        while (recoveryElapsed < recoveryTotal)
        {
            recoveryElapsed += Time.deltaTime;
            // 취소 윈도우 열기
            if (!_canCancel && recoveryElapsed >= recoveryTotal * cancelWindowStart)
                _canCancel = true;
            yield return null;
        }
        _inRecovery = false;
        _canCancel = false;
    }

    // 대쉬 입력이 들어왔을 때 취소 가능한지 확인
    public bool TryCancel()
    {
        if (_canCancel)
        {
            StopAllCoroutines();
            _isActive = false;
            _inRecovery = false;
            _canCancel = false;
            DeactivateHitbox();
            return true; // 취소 성공
        }
        return false;
    }
}
```

### 방법 2: Animator State + AnimationEvent로 구간 표시

```csharp
// Animator에서 ClawAttack 클립의 특정 프레임에 이벤트를 걸어두는 방식
// Animation 클립 인스펙터에서:
//   프레임 2 → 이벤트: OnAttackActive()
//   프레임 5 → 이벤트: OnAttackRecovery()
//   프레임 7 → 이벤트: OnCancelWindowOpen()
//   프레임 9 → 이벤트: OnAttackEnd()

public class PlayerAnimEvents : MonoBehaviour
{
    PlayerCombat _combat;
    void Awake() => _combat = GetComponentInParent<PlayerCombat>();

    public void OnAttackActive() => _combat.SetHitboxActive(true);
    public void OnAttackRecovery() => _combat.SetHitboxActive(false);
    public void OnCancelWindowOpen() => _combat.SetCancelWindowOpen(true);
    public void OnAttackEnd() => _combat.OnAttackEnd();
}
```

### 방법 3: HitFeelSettings ScriptableObject에 수치 통합 (OnionCat 구조에 맞춤)

OnionCat은 이미 `HitFeelSettings.asset`이 있으므로, 여기에 프레임 데이터를 추가:

```csharp
[CreateAssetMenu]
public class HitFeelSettings : ScriptableObject
{
    [Header("Claw Attack Frame Data")]
    public float clawStartupMs = 40f;
    public float clawActiveMs = 100f;
    public float clawRecoveryMs = 80f;
    [Range(0f, 1f)]
    public float clawCancelWindowStart = 0.5f; // recovery의 몇 %에서 대쉬 취소 허용

    [Header("Special Attack Frame Data")]
    public float specialStartupMs = 80f;
    public float specialActiveMs = 200f;
    public float specialRecoveryMs = 150f;
    // 특수 공격은 취소 불가 (_cancelWindowStart = 1f)
}
```

플레이 중에도 수치를 실시간 조절 가능하므로 타격감 튜닝에 적합.

---

## 캔슬 윈도우 설계 원칙

### OnionCat에 맞는 캔슬 체계

```
할퀴기 active → 할퀴기 recovery (50%~) → 대쉬 취소 가능
할퀴기 active → 또 다른 할퀴기 → 연속 공격 (광란 특수 공격 상태에서)
대쉬 → (어느 시점이든) → 할퀴기 취소 가능
특수 공격 → 취소 불가 (끝까지 강제)
```

### 취소 허용이 "느낌"에 미치는 영향

| 취소 없음 | 취소 있음 |
|----------|---------|
| 한 번 누르면 끝까지 재생 | 타이밍을 맞추면 더 빠른 연계 가능 |
| 예측 가능하지만 무거운 느낌 | 숙련자에게 보상, 초보자는 그냥 기다리면 됨 |
| 실수해도 회복 자동 | 잘못 취소하면 더 느려질 수 있음 |

OnionCat의 고양이는 "중간 난이도" 취소 설계가 적합:
- 대쉬 취소: 할퀴기 recovery 후반부에서만 가능 (초보도 실수 없이 쓸 수 있음)
- 특수 공격 취소 불가: 큰 공격은 "커밋"이 있어야 무게감이 생김

---

## OnionCat 적용 포인트

### 1. 현재 HitFeelSettings에 프레임 데이터 추가

`Assets/Resources/HitFeelSettings.asset`에 할퀴기/특수공격/대쉬의 startup·active·recovery 수치를 추가하면:

- Aseprite 애니메이션 타이밍과 C# 히트박스 활성화 타이밍을 **한 곳에서** 맞출 수 있음
- 이전 IdeaPool(2026-10-25)의 "홀드 프레임 200ms + 히트스톱 정렬" 작업과 연동 가능

### 2. 대쉬 취소 윈도우 명시화

현재 고양이 대쉬가 어느 타이밍에 취소를 허용하는지 코드에서 명시적으로 관리.
`Dash_Default.cs`나 `PlayerController`에서 `ClawAttack.TryCancel()`을 호출하는 시점 통일.

### 3. 할퀴기 연타 시스템에서의 캔슬 체인

"광란" 특수 공격 상태(`CatSpecial.cs`)에서 6초간 공속 2배:
- 이 상태에서 할퀴기 → 할퀴기 체인이 매끄럽게 연결되는지 active → 다음 startup 겹침 여부 확인
- "연타" 느낌을 위해 recovery를 짧게 줄이되, 캔슬 윈도우도 함께 당겨야 함

### 4. Aseprite 프레임 수 ↔ Unity ms 환산

OnionCat은 30fps 애니메이션을 사용 (PPU 32, Pixel Perfect):
- 1 Aseprite 프레임 ≈ 33ms
- startup 40ms = 약 1.2 프레임 → 실질적으로 1~2 프레임
- active 100ms = 약 3 프레임
- recovery 80ms = 약 2~3 프레임

Aseprite 타이밍 수정 시 이 환산을 기준으로 할 것.

---

## 참고 링크

- Unity AnimationEvent 공식 문서: https://docs.unity3d.com/Manual/animeditor-AnimationEvents.html
- Frame Data 설명 (격투게임 위키): https://glossary.infil.net/?t=Frame%20Data
- "Making Responsive Controls Feel Good" - GDC Talk: https://www.gdcvault.com/play/1025126/Making-Responsive-Controls-Feel-Good
- Vlambeer의 "The Art of Screenshake" (유사 주제): https://www.youtube.com/watch?v=AJdEqssNZ-U
- Brackeys "2D Attack" 튜토리얼 (AnimationEvent 기반): https://www.youtube.com/watch?v=sPiVz1k-fEs
