# 게임패드 아날로그 스틱 — 데드존·방향 보정·디지털 혼용

리서치 날짜: 2026-11-13

## 개요

게임패드 아날로그 스틱은 물리적으로 완전한 0을 출력하지 못한다. 쉬고 있어도 작은 값이 나와 캐릭터가 천천히 미끄러진다. 반대로 키보드 WASD는 0 또는 1의 디지털 신호다. OnionCat은 고양이(P1)가 게임패드, 양파(P2)가 키보드+마우스이므로 두 입력 방식이 공존한다. 아날로그 스틱을 보정하지 않으면 고양이 조작이 불안정하고, 보정을 과도하게 하면 느낌이 뭉개진다.

---

## Unity 구현 방법 (New Input System 기준)

### 1. Input Actions 에서 Processor로 데드존 설정

Input Actions 에셋 → 해당 Action 선택 → Processors 탭에서 추가:

```
Dead Zone Processor
  Min (inner dead zone): 0.125   ← 이 범위 안은 0으로 클램프
  Max (outer dead zone): 0.925   ← 이 범위 밖은 1로 클램프
```

내부 데드존(0.0~Min) 안에 있으면 `Vector2.zero`로 처리 → 가만히 있을 때 미끄러짐 방지.
외부 데드존(Max~1.0) 밖에 있으면 1.0으로 처리 → 완전히 밀었을 때 100% 출력 보장.
두 데드존 사이는 0~1로 선형 재매핑.

```csharp
// 코드에서 Vector2를 받으면 이미 Processor가 적용된 값
Vector2 move = _moveAction.ReadValue<Vector2>();
// move.magnitude == 0이면 완전 정지, 1이면 최대
```

### 2. 디지털(WASD) + 아날로그(스틱) 통일

Unity Input System의 **Composite Binding** (2D Vector Composite, WASD)은 자동으로 Normalize 처리하므로 대각선도 Vector2(0.707, 0.707)이 된다.

```csharp
// WASD와 스틱 모두 같은 Action에 바인딩하면 자동 통합
// Action: "Move" → 바인딩 1: Gamepad/Left Stick, 바인딩 2: 2D Composite(WASD)
```

중요: WASD는 디지털이라 가속 없이 즉시 최대 속도 → 스틱보다 "딱딱"하게 느껴질 수 있다.
이를 맞추려면 코드에서 보간을 적용:

```csharp
Vector2 _currentMove;

void Update() {
    Vector2 target = _moveAction.ReadValue<Vector2>();
    bool isGamepad = Gamepad.current != null && Gamepad.current.leftStick.IsActuated();
    
    // 게임패드: 부드럽게 / 키보드: 즉시 반응
    float lerpSpeed = isGamepad ? 10f : 999f;
    _currentMove = Vector2.Lerp(_currentMove, target, lerpSpeed * Time.deltaTime);
}
```

### 3. 8방향 스냅 (선택적 적용)

픽셀아트 탑다운에서 대각선 이동이 애매하게 느껴질 때 사용.

```csharp
Vector2 SnapTo8Direction(Vector2 input) {
    if (input.sqrMagnitude < 0.01f) return Vector2.zero;
    float angle = Mathf.Atan2(input.y, input.x) * Mathf.Rad2Deg;
    // 45도 단위로 반올림
    angle = Mathf.Round(angle / 45f) * 45f;
    return new Vector2(Mathf.Cos(angle * Mathf.Deg2Rad),
                       Mathf.Sin(angle * Mathf.Deg2Rad));
}
```

OnionCat처럼 자유 각도 이동이 필요하면 8방향 스냅을 쓰지 않고, 애니메이션만 4방향(DirectionalSprite)으로 처리하는 것이 좋다.

### 4. 조준 시 아날로그 스틱 가속도 보정 (에임 어시스트 없이 느낌 개선)

스틱을 천천히 움직이면 미세 조준이 쉽도록, 빠르게 움직이면 큰 각도를 빠르게 돌리도록:

```csharp
float ApplyResponseCurve(float raw) {
    // 비선형 곡선: 느린 입력에서는 작은 출력, 빠른 입력에서는 큰 출력
    return Mathf.Sign(raw) * Mathf.Pow(Mathf.Abs(raw), 1.5f);
}
```

하지만 OnionCat에서 고양이는 이동 용도이고 조준은 양파(마우스)이므로 이 보정은 주로 이동 감도에 활용한다.

### 5. 런타임에서 데드존 조정 (접근성)

설정 화면에서 사용자가 데드존을 직접 조정할 수 있도록:

```csharp
// InputSystem에서 Processor 값 런타임 변경은 번거로우므로
// Action에서 raw 값을 받아 코드에서 처리하는 방법을 권장
float innerDead = PlayerPrefs.GetFloat("DeadZoneInner", 0.125f);

Vector2 ApplyDeadZone(Vector2 raw, float inner, float outer = 0.925f) {
    float mag = raw.magnitude;
    if (mag < inner) return Vector2.zero;
    if (mag > outer) return raw.normalized;
    return raw.normalized * ((mag - inner) / (outer - inner));
}
```

---

## OnionCat 적용 포인트

| 상황 | 권장 처리 |
|------|-----------|
| 고양이 이동 (스틱) | Dead Zone Processor: Min 0.15, Max 0.925 / 느린 가속 보간 10f |
| 고양이 이동 (WASD 대체) | Lerp 즉시(999f), 8방향 스냅 없음 — 자유 각도 유지 |
| 패드 모드 자동 감지 | `Gamepad.current != null`로 확인, 없으면 키보드 모드 |
| 설정 메뉴 | 고양이 P1 데드존 조절 슬라이더 추가 고려 |

**현재 `CoopInputLayout`**: 패드 연결 여부로 Cat 제어 방식이 자동 전환됨.
두 경로에서 `move` 값이 같은 단위(0~1 Vector2)로 오도록 맞추면 `PlayerMovement`는 수정 없이 동작.

---

## 참고 링크
- Unity Input System 공식 문서 — Processors: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.8/manual/Processors.html
- Unity 블로그 — New Input System 소개: https://blog.unity.com/engine-platform/introducing-the-new-input-system
- Game Feel 관련 아날로그 스틱 보정: https://www.gamedeveloper.com/design/the-art-of-the-analog-stick
- Marques Brownlee의 게임패드 드리프트 원인 설명 (데드존의 필요성 이해용): YouTube 검색 "controller drift explained"
