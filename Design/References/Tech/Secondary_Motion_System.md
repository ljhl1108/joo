# Secondary Motion System (세컨더리 모션 / 관성 애니메이션)

리서치 날짜: 2026-07-18

## 개요

Secondary Motion(세컨더리 모션)은 캐릭터의 주요 동작(이동·공격)에 반응해 **부속 요소들이 물리적으로 흔들리는 느낌**을 주는 기법이다. 본격적인 물리 시뮬레이션 없이 간단한 수식만으로 구현할 수 있어 2D 픽셀 게임에서 광범위하게 사용된다.

OnionCat에서는 **고양이 등의 화분과 작물(양파)**이 고양이의 이동·대시·공격에 반응해 흔들리는 효과에 직접 적용된다. 화분이 "살아있다"는 느낌을 주는 핵심 시각 요소다.

---

## Unity 구현 방법

### 방법 1: Spring-Damper (스프링 감쇠 수식) — 권장

가장 자연스러운 구현. 스프링처럼 흔들리다가 감쇠되며 원위치 복귀.

```csharp
public class SecondaryMotion : MonoBehaviour
{
    [SerializeField] private Transform target; // 화분/작물 Transform
    [SerializeField] private float springStrength = 200f; // 스프링 강도
    [SerializeField] private float damping = 15f;         // 감쇠 계수
    [SerializeField] private float maxOffset = 0.3f;      // 최대 변위

    private Vector2 _velocity;
    private Vector2 _offset;
    private Vector2 _prevParentPos;

    private void Start()
    {
        _prevParentPos = transform.parent.position;
    }

    private void Update()
    {
        // 부모(고양이)의 가속도를 입력으로 사용
        Vector2 parentPos = transform.parent.position;
        Vector2 parentAccel = ((Vector2)transform.parent.position - _prevParentPos) / Time.deltaTime;
        _prevParentPos = parentPos;

        // 스프링-감쇠 공식: F = -k*x - d*v
        Vector2 springForce = -springStrength * _offset - damping * _velocity;
        // 부모 가속도 반대 방향으로 관성 효과
        Vector2 inertiaForce = -parentAccel * 0.5f;

        _velocity += (springForce + inertiaForce) * Time.deltaTime;
        _offset += _velocity * Time.deltaTime;
        _offset = Vector2.ClampMagnitude(_offset, maxOffset);

        target.localPosition = (Vector3)_offset;
    }

    // 외부에서 충격(대시, 공격) 줄 때 호출
    public void AddImpulse(Vector2 force)
    {
        _velocity += force;
    }
}
```

---

### 방법 2: Lerp/SmoothDamp 기반 지연 추적 (간단 버전)

구현은 가장 단순하지만 약간 딱딱한 느낌.

```csharp
public class DelayedFollow : MonoBehaviour
{
    [SerializeField] private Transform leader;    // 고양이
    [SerializeField] private float smoothTime = 0.1f;
    [SerializeField] private Vector3 baseOffset = new Vector3(0, 0.5f, 0);

    private Vector3 _velocity;

    private void LateUpdate()
    {
        Vector3 targetPos = leader.position + baseOffset;
        transform.position = Vector3.SmoothDamp(
            transform.position, targetPos, ref _velocity, smoothTime);
    }
}
```

---

### 방법 3: 각도 기반 흔들림 (회전 세컨더리 모션)

화분이 좌우로 기울어지는 효과. 스프링 공식을 회전에 적용.

```csharp
public class RotationSpring : MonoBehaviour
{
    [SerializeField] private float springStrength = 300f;
    [SerializeField] private float damping = 20f;
    [SerializeField] private float maxAngle = 15f;

    private float _angularVelocity;
    private float _angle;
    private float _prevParentX;

    private void Update()
    {
        float parentX = transform.parent.position.x;
        float parentXSpeed = (parentX - _prevParentX) / Time.deltaTime;
        _prevParentX = parentX;

        float springForce = -springStrength * _angle - damping * _angularVelocity;
        float inertiaForce = -parentXSpeed * 2f;

        _angularVelocity += (springForce + inertiaForce) * Time.deltaTime;
        _angle += _angularVelocity * Time.deltaTime;
        _angle = Mathf.Clamp(_angle, -maxAngle, maxAngle);

        transform.localRotation = Quaternion.Euler(0, 0, _angle);
    }
}
```

---

### 방법 4: Unity Animation Rigging 패키지

Unity 공식 패키지로 Bone 기반 세컨더리 모션.
- `Window > Package Manager > Animation Rigging` 설치
- `Damped Transform` 컴포넌트: 부모 움직임에 지연·감쇠 반응
- 픽셀아트에는 다소 과한 경우가 많아 방법 1~3이 더 적합

---

### 대시/공격 시 충격 연동

```csharp
// 고양이 이동 스크립트에서 대시 시 SecondaryMotion에 충격 전달
private void OnDash(Vector2 dashDirection)
{
    _flowerPotMotion.AddImpulse(-dashDirection * 5f); // 대시 반대 방향으로 충격
}

// 공격(슬래시) 시
private void OnSlash()
{
    _flowerPotMotion.AddImpulse(new Vector2(0, -2f)); // 아래로 충격
}
```

---

### LateUpdate 사용 권장

Secondary Motion은 반드시 `LateUpdate()`에서 처리해야 부모 이동 후에 계산된다.
- `Update()`에서 처리하면 부모 위치와 순서 경쟁 발생 가능.

---

## OnionCat 적용 포인트

### 화분/작물 흔들림 구현 순서

1. 화분 GameObject를 고양이의 자식으로 배치 (`등 위치`에 localPosition 설정)
2. `SecondaryMotion` 스크립트를 화분 GameObject에 부착
3. **이동 흔들림**: 고양이의 Rigidbody2D velocity를 읽어 관성 효과 적용
4. **대시 충격**: Dash 이벤트 발생 시 `AddImpulse()` 호출 (대시 방향 반대로)
5. **공격 충격**: 180° 슬래시 시 아래 방향 충격 (휘두르는 느낌)
6. **착지 충격**: 피격 시 위아래 진동 (히트스톱과 연동)

### 작물(양파) 추가 흔들림

작물은 화분 위에 별도 Transform으로, 화분보다 더 큰 흔들림 값 적용:
```
화분: springStrength=200, damping=15, maxOffset=0.2
작물: springStrength=150, damping=10, maxOffset=0.35  (더 흔들림)
```

### 픽셀아트 주의사항

- 픽셀아트는 subpixel 이동 시 계단 현상 발생
- `maxOffset`을 픽셀 단위(4px = 0.25 units)로 맞추거나
- 렌더링은 픽셀 그리드에 스냅, 흔들림은 논리적으로만 계산

### 성능

- 스크립트 1개당 연산량 거의 없음 (벡터 덧셈·곱셈 수준)
- 화분·작물 2개 오브젝트에 적용해도 전혀 부담 없음

---

## 참고 링크

- Unity Blog — Secondary Motion: https://blog.unity.com/games/rigidbody-physics-and-secondary-motion
- GDC 2017 — Juice It or Lose It (세컨더리 모션의 중요성): https://www.youtube.com/watch?v=Fy0aCDmgnxg
- Unity Animation Rigging Docs: https://docs.unity3d.com/Packages/com.unity.animation.rigging@1.3/manual/constraints/DampedTransform.html
- Spring Damper 수식 설명: https://www.gamedeveloper.com/design/physics-based-spring-oscillations-for-game-feel
- Tarodev — 2D Secondary Motion Tutorial: https://www.youtube.com/watch?v=ZDjjLvluFRo
