# 쿨다운 & 타이머 관리 시스템

리서치 날짜: 2026-07-01

## 개요

로그라이크에서 쿨다운은 어디에나 있다. 대시, 패링, 스킬, 무기 재장전, 방어막 회복 등 모든 행동에 "다시 쓸 수 있을 때까지의 대기 시간"이 필요하다. OnionCat에서도 고양이의 대시, 양파의 방패/패링, 업그레이드 아이템 능력들이 각각의 쿨다운을 갖는다. 이 시스템을 재사용 가능한 구조로 만들지 않으면 유지보수가 급격히 어려워진다.

---

## Unity 구현 방법

### 방법 1: float 직접 비교 (가장 단순)

```csharp
public class PlayerDash : MonoBehaviour
{
    [SerializeField] private float dashCooldown = 1.5f;
    private float _lastDashTime = -999f;

    public bool CanDash => Time.time >= _lastDashTime + dashCooldown;

    public void TryDash()
    {
        if (!CanDash) return;
        _lastDashTime = Time.time;
        // 대시 실행
    }
}
```

장점: 코드가 짧음, 이해하기 쉬움  
단점: 쿨다운마다 코드 중복, UI 연동 번거로움, 게임 일시정지 처리 어려움

---

### 방법 2: 재사용 가능한 CooldownTimer 클래스 (권장)

```csharp
/// <summary>
/// 재사용 가능한 쿨다운 타이머. 모노비헤이비어 상속 없이 사용.
/// </summary>
public class CooldownTimer
{
    private float _duration;
    private float _endTime;

    public bool IsReady => Time.time >= _endTime;
    public float Remaining => Mathf.Max(0f, _endTime - Time.time);
    // 0=쿨다운 시작, 1=사용 가능 (UI fillAmount에 바로 사용)
    public float Progress => _duration > 0f
        ? Mathf.Clamp01(1f - (Remaining / _duration))
        : 1f;

    public void Trigger(float duration)
    {
        _duration = duration;
        _endTime = Time.time + duration;
    }

    public void Reset() => _endTime = 0f;
}
```

**사용 예시 — PlayerCat.cs:**

```csharp
public class PlayerCat : MonoBehaviour
{
    [SerializeField] private float dashCooldown = 1.5f;
    private readonly CooldownTimer _dashTimer = new CooldownTimer();

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space) && _dashTimer.IsReady)
        {
            _dashTimer.Trigger(dashCooldown);
            ExecuteDash();
        }
    }
}
```

**사용 예시 — PlayerOnion.cs:**

```csharp
public class PlayerOnion : MonoBehaviour
{
    [SerializeField] private float parryCooldown = 2f;
    private readonly CooldownTimer _parryTimer = new CooldownTimer();

    // UI Image.fillAmount = _parryTimer.Progress;
}
```

---

### 방법 3: 코루틴 기반 (조건부 권장)

```csharp
private bool _canDash = true;

private IEnumerator DashCooldownRoutine(float duration)
{
    _canDash = false;
    yield return new WaitForSeconds(duration);
    _canDash = true;
}
```

장점: 직관적, WaitForSecondsRealtime으로 일시정지 무시 쿨다운 구현 가능  
단점: 쿨다운 진행률(Progress)을 별도로 추적해야 함, 다수 타이머 시 코루틴 관리 복잡

---

### UI 연동 — 원형 쿨다운 아이콘

```csharp
// Image 컴포넌트의 Image Type을 Filled로 설정 후
[SerializeField] private Image cooldownFillImage;

private void Update()
{
    // fillAmount: 0=완전히 채워짐(사용 불가), 1=비어있음(사용 가능)
    cooldownFillImage.fillAmount = 1f - _dashTimer.Progress;
}
```

Inspector 설정:
- Image Type: **Filled**
- Fill Method: **Radial 360**
- Fill Origin: **Top**

---

### 게임 일시정지 대응

Time.timeScale을 0으로 설정하면 `Time.time`은 멈추지 않지만 `Time.deltaTime`은 0이 됨.

```csharp
// 일시정지 호환: Time.unscaledTime 사용
public class CooldownTimerUnscaled
{
    private float _duration;
    private float _endTime;

    public bool IsReady => Time.unscaledTime >= _endTime;
    public float Remaining => Mathf.Max(0f, _endTime - Time.unscaledTime);
    public float Progress => _duration > 0f
        ? Mathf.Clamp01(1f - Remaining / _duration)
        : 1f;

    public void Trigger(float duration)
    {
        _duration = duration;
        _endTime = Time.unscaledTime + duration;
    }
}
```

대부분 게임 내 쿨다운은 일시정지 시 같이 멈춰야 함 → `Time.time` 사용이 기본.  
일시정지 메뉴 자체의 애니메이션 등 예외만 `Time.unscaledTime` 사용.

---

### 쿨다운 감소 업그레이드 적용

업그레이드로 쿨다운 단축 구현 시:

```csharp
public class PlayerCat : MonoBehaviour
{
    [SerializeField] private float baseDashCooldown = 1.5f;
    private float _cooldownMultiplier = 1f; // 업그레이드로 0.8f, 0.6f 등으로 감소

    private float ActualDashCooldown => baseDashCooldown * _cooldownMultiplier;

    public void ApplyCooldownReduction(float multiplier)
    {
        _cooldownMultiplier = Mathf.Max(0.1f, multiplier); // 최소 10%로 하한 설정
    }
}
```

---

## OnionCat 적용 포인트

### 필요한 쿨다운 목록

| 액션 | 플레이어 | 기본 쿨다운 | 업그레이드 가능 |
|------|--------|------------|---------------|
| 무적 대시 | 고양이(P1) | ~1.5초 | 쿨다운 감소 |
| 패링/방어막 | 양파(P2) | ~2초 | 쿨다운 감소 |
| 근거리 공격 | 고양이(P1) | 공격속도로 제어 | 공격속도 증가 |
| 원거리 발사 | 양파(P2) | 발사속도로 제어 | 발사속도 증가 |

### 구현 순서 (OnionCat 기준)

1. `CooldownTimer` 클래스를 `Scripts/Utils/CooldownTimer.cs`에 생성
2. `PlayerCat`에 대시 쿨다운 연결
3. `PlayerOnion`에 패링 쿨다운 연결
4. HUD의 각 아이콘에 Image(Filled) 연결 → `fillAmount` 업데이트
5. 업그레이드 아이템이 `_cooldownMultiplier`를 변경하도록 연결

---

## 참고 링크

- Unity 공식 — Time 클래스: https://docs.unity3d.com/ScriptReference/Time.html
- Unity 공식 — WaitForSeconds: https://docs.unity3d.com/ScriptReference/WaitForSeconds.html
- Unity 공식 — Image.fillAmount: https://docs.unity3d.com/ScriptReference/UI.Image-fillAmount.html
- Brackeys — Cooldown System: https://www.youtube.com/watch?v=qc-0PR9iBW0
- Game Dev Guide — Timer 패턴: https://gamedevguide.com/programming/unity/timer-pattern
