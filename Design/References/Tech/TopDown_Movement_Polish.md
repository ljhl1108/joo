# TopDown 이동 세밀화 (Movement Polish)

리서치 날짜: 2026-09-10

## 개요

기본 이동 코드를 작성한 후에도 게임이 "딱딱하게" 또는 "미끄럽게" 느껴지는 이유는 이동 세밀화(Polish)가 없기 때문이다. Hades, Enter the Gungeon, Dead Cells 등 명작 로그라이크는 모두 이동에 수십 가지 미세 조정을 적용한다. OnionCat의 Cat 이동과 Onion의 마우스 에임 모두 이 원칙이 적용된다.

---

## Unity 구현 방법

### 1. 입력 버퍼 (Input Buffer)
대시 또는 공격 버튼을 **동작 가능해지기 직전에 눌러도** 입력이 접수되는 시스템.

```csharp
public class InputBuffer
{
    private float _bufferDuration = 0.12f; // 120ms 여유
    private float _lastPressTime = -99f;

    public void RegisterPress() => _lastPressTime = Time.time;

    public bool Consume()
    {
        if (Time.time - _lastPressTime <= _bufferDuration)
        {
            _lastPressTime = -99f;
            return true;
        }
        return false;
    }
}

// 사용 예 (CatController.cs)
private InputBuffer _dashBuffer = new();

void Update()
{
    if (_dashInput.WasPressedThisFrame()) _dashBuffer.RegisterPress();
    if (_dashBuffer.Consume() && _dashCooldown <= 0) ExecuteDash();
}
```

### 2. 가속/감속 곡선 (Acceleration Curve)
Rigidbody2D를 직접 velocity 설정하면 즉각 반응. 대신 선형 보간으로 부드러운 가속 구현:

```csharp
[SerializeField] private float _acceleration = 15f;
[SerializeField] private float _deceleration = 20f;
[SerializeField] private float _maxSpeed = 6f;

private Vector2 _currentVelocity;

void FixedUpdate()
{
    Vector2 inputDir = _moveAction.ReadValue<Vector2>().normalized;
    float accel = inputDir.sqrMagnitude > 0.01f ? _acceleration : _deceleration;
    _currentVelocity = Vector2.MoveTowards(_currentVelocity, inputDir * _maxSpeed, accel * Time.fixedDeltaTime);
    _rb.linearVelocity = _currentVelocity;
}
```

### 3. 방향전환 쾌감 (Turn Responsiveness)
반대 방향 입력 시 즉각 감속하고 빠르게 방향 전환:

```csharp
void FixedUpdate()
{
    Vector2 inputDir = _moveAction.ReadValue<Vector2>().normalized;
    bool oppositeDir = Vector2.Dot(_currentVelocity, inputDir) < -0.1f;
    float accel = oppositeDir ? _turnAcceleration : _acceleration; // 방향 반전 시 더 빠른 가속
    // ...
}
```

### 4. 이동 중 공격 속도 감소 (Combat Momentum)
Enter the Gungeon처럼 조준/공격 중 이동속도 감소로 전술적 선택 강요:

```csharp
float speedMultiplier = _isAiming ? 0.5f : 1.0f;
_currentVelocity = Vector2.MoveTowards(_currentVelocity, inputDir * _maxSpeed * speedMultiplier, accel * Time.fixedDeltaTime);
```

### 5. 대시 후 이동 감쇠 (Post-Dash Friction)
무적 대시 이후 관성으로 살짝 더 이동하는 느낌:

```csharp
IEnumerator ExecuteDash()
{
    float dashSpeed = 18f;
    float dashDuration = 0.12f;
    Vector2 dashDir = _lastMoveDir;

    float elapsed = 0f;
    while (elapsed < dashDuration)
    {
        float t = elapsed / dashDuration;
        float speed = Mathf.Lerp(dashSpeed, 0f, t * t); // EaseIn 감속
        _rb.linearVelocity = dashDir * speed;
        elapsed += Time.fixedDeltaTime;
        yield return new WaitForFixedUpdate();
    }
}
```

### 6. 8방향 → 부드러운 각도 변환 (Directional Sprite Snap)
8방향 애니메이션을 유지하면서 실제 이동은 360도로:

```csharp
static Vector2 SnapToEightDir(Vector2 input)
{
    if (input.sqrMagnitude < 0.01f) return Vector2.zero;
    float angle = Mathf.Atan2(input.y, input.x) * Mathf.Rad2Deg;
    float snapped = Mathf.Round(angle / 45f) * 45f;
    return new Vector2(Mathf.Cos(snapped * Mathf.Deg2Rad), Mathf.Sin(snapped * Mathf.Deg2Rad));
}
// 애니메이션 파라미터에만 스냅 적용, Rigidbody는 raw input 사용
```

### 7. 벽 슬라이딩 (Wall Sliding)
벽에 대각선으로 막혔을 때 멈추지 않고 벽을 따라 미끄러짐:

```csharp
// Rigidbody2D + Composite Collider 사용 시 자동 처리
// Physics Material 2D: Friction=0, Bounciness=0 설정으로 구현
```

### 8. 스쿼시 & 스트레치 (Squash & Stretch)
이동 시작/정지에 스프라이트 스케일 미세 변화:

```csharp
void Update()
{
    float speed = _rb.linearVelocity.magnitude;
    float stretchY = Mathf.Lerp(1f, 1.08f, speed / _maxSpeed);
    float stretchX = Mathf.Lerp(1f, 0.93f, speed / _maxSpeed);
    _spriteTransform.localScale = new Vector3(stretchX, stretchY, 1f);
}
```

---

## OnionCat 적용 포인트

### Cat (P1) 이동 세밀화
- **입력 버퍼 0.12초**: 대시 직전에 버튼 눌러도 대시 발동 → 반응성 좋다는 느낌
- **방향전환 가속**: 반대 방향 입력 시 가속도 2배 → 즉각 방향전환 가능
- **대시 후 0.05초 감쇠**: 대시 종료 후 짧게 느려지는 "착지감"
- **전투 중 속도 0.75배**: Cat이 슬래시 모션 중 살짝 느려짐

### Onion (P2) 에임 세밀화
- **마우스 에임 보정**: 빠르게 움직이는 적에게 약간의 자동 선조준 (Aim Assist)
  - 이미 `Aim_Assist_System.md`에 구현 방법 있음
- **방패 방향 전환 딜레이**: 방패 방향이 즉각 바뀌면 너무 쉬움 → 0.08초 보간으로 방향 전환
  
### 권장 파라미터 값 (OnionCat)
| 파라미터 | 권장값 | 비고 |
|---------|--------|------|
| 최대 속도 | 5.5 m/s | 방 크기 12×9 타일 기준 |
| 가속도 | 14 | 즉각 반응, 미끄럽지 않음 |
| 감속도 | 18 | 입력 없을 때 빠르게 정지 |
| 방향전환 가속 | 28 | 반대 방향 시 2배 |
| 대시 속도 | 16 m/s | 0.15초 지속 |
| 입력 버퍼 시간 | 0.12초 | 대시/공격 모두 적용 |
| 전투 중 속도 배율 | 0.75 | 슬래시/투사체 발사 중 |

---

## 참고 링크

- Game Feel 바이블: https://www.gamedeveloper.com/design/the-art-of-screenshake
- Celeste 이동 코드 분석: https://maddythorson.medium.com/celeste-movement-and-input-buffering-e8d3eb51b432
- Unity 2D 이동 Best Practice: https://docs.unity3d.com/Manual/class-Rigidbody2D.html
- Input Buffer 구현: https://www.youtube.com/watch?v=2S3g8CgBG1g
- 8방향 스냅 애니메이션: https://www.youtube.com/watch?v=a8TIbMQRCMM
