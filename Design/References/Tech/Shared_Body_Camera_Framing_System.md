# Shared Body Camera Framing System

리서치 날짜: 2026-09-20

## 개요

두 플레이어가 한 몸을 공유하는 게임(OnionCat)에서, 한 명(Cat)은 캐릭터를 이동시키고
다른 한 명(Onion)은 마우스로 화면 어딘가를 조준한다. 이때 카메라는:
1. Cat의 이동 방향을 따라가야 하고
2. Onion의 마우스 커서/조준점도 화면에 담아야 한다

이 두 요구를 동시에 만족시키는 카메라 프레임 설계가 핵심이다.

---

## 왜 중요한가

- 일반 탑다운 카메라는 캐릭터를 화면 중앙에 고정 → Onion이 먼 곳을 조준하면 커서가 화면 밖으로 나감
- 커서가 화면 밖 = 조준 대상이 안 보임 = Onion 플레이어가 답답함
- 반면 커서를 항상 보이게 하려면 카메라가 Cat에서 크게 벗어남 → Cat 플레이어가 길을 잃음
- 해결: **캐릭터 위치와 마우스 커서 위치의 가중 중점(weighted midpoint)** 으로 카메라 목표를 설정

---

## Unity 구현 방법

### 기본 원리

```csharp
// 카메라 목표 위치 = 캐릭터 + (커서방향 * 오프셋 비율)
Vector3 characterPos = player.transform.position;
Vector3 cursorWorldPos = GetMouseWorldPosition();

// 가중 중점: alpha=0이면 캐릭터에 고정, alpha=1이면 커서에 고정
float alpha = 0.35f; // 35%쪽으로 커서를 당김
Vector3 targetPos = Vector3.Lerp(characterPos, cursorWorldPos, alpha);
```

### 커서 월드 좌표 변환

```csharp
Vector3 GetMouseWorldPosition()
{
    Vector3 mouseScreen = Mouse.current.position.ReadValue();
    mouseScreen.z = -Camera.main.transform.position.z;
    return Camera.main.ScreenToWorldPoint(mouseScreen);
}
```

### 카메라 오프셋 제한 (중요)

커서가 너무 멀면 카메라가 과도하게 이동함 → 최대 오프셋을 제한해야 함:

```csharp
Vector3 rawOffset = targetPos - characterPos;
float maxOffset = 3f; // 유닛 기준 (PPU 32이면 96px)
Vector3 clampedOffset = Vector3.ClampMagnitude(rawOffset, maxOffset);
Vector3 finalTarget = characterPos + clampedOffset;
```

### Cinemachine과 통합

Cinemachine Virtual Camera의 Follow 타겟을 직접 캐릭터가 아닌
"카메라 앵커" Transform으로 설정하고, 그 앵커를 스크립트로 이동:

```csharp
public class CameraAimAnchor : MonoBehaviour
{
    [SerializeField] private Transform _catTransform;
    [SerializeField] private float _aimWeight = 0.35f;
    [SerializeField] private float _maxOffset = 3f;
    [SerializeField] private float _smoothTime = 0.1f;

    private Vector3 _velocity;

    void LateUpdate()
    {
        Vector3 mouseWorld = GetMouseWorldPosition();
        Vector3 rawOffset = mouseWorld - _catTransform.position;
        Vector3 clamped = Vector3.ClampMagnitude(rawOffset, _maxOffset);
        Vector3 target = _catTransform.position + clamped * _aimWeight;

        transform.position = Vector3.SmoothDamp(
            transform.position, target, ref _velocity, _smoothTime);
    }

    Vector3 GetMouseWorldPosition()
    {
        var mp = Mouse.current.position.ReadValue();
        var screenPos = new Vector3(mp.x, mp.y, Mathf.Abs(Camera.main.transform.position.z));
        return Camera.main.ScreenToWorldPoint(screenPos);
    }
}
```

### 컨트롤러 지원 (Onion이 게임패드를 쓸 경우)

게임패드 우측 스틱으로 조준 방향을 입력받을 때:

```csharp
// 스틱 입력을 방향벡터로 받아 캐릭터 기준 오프셋 계산
Vector2 aimDir = gamepadActions.AimDirection.ReadValue<Vector2>();
if (aimDir.magnitude < 0.2f) return _catTransform.position; // 데드존

Vector3 aimOffset = new Vector3(aimDir.x, aimDir.y, 0) * _maxOffset;
return _catTransform.position + aimOffset;
```

### 화면 경계 클램프 (방 기반 게임에 추가)

방 안에서 카메라가 벽 밖을 보이면 안 될 때:

```csharp
// Cinemachine Confiner2D 컴포넌트를 Virtual Camera에 추가
// BoundingShape2D: 방 영역 폴리곤 콜라이더를 참조
// Damping: 0.5 정도로 부드럽게 경계에 걸리도록
```

---

## OnionCat 적용 포인트

### 구체적 수치 권장값

- **aimWeight**: 0.3~0.4 (너무 높으면 Cat이 길을 잃음)
- **maxOffset**: 2.5~4 유닛 (PPU 32 기준 80~128px 범위)
- **smoothTime**: 0.08~0.12초 (너무 느리면 커서 추적 불량)

### 적용 순서

1. 씬에 `CameraAimAnchor` 빈 오브젝트 생성
2. Cinemachine Virtual Camera의 Follow = CameraAimAnchor
3. CinemachineConfiner2D로 방 경계 설정
4. Cat 이동 중에는 aimWeight를 약간 낮춤 (이동 방향으로 약간 선행)
5. 일시정지/업그레이드 선택 중엔 앵커를 캐릭터 중앙으로 고정

### 이동 선행 (Look-Ahead) 추가

```csharp
// Cat의 이동 속도에 비례해 이동 방향으로 약간 앞을 보여줌
Vector3 moveOffset = _catRigidbody.velocity.normalized * _lookAheadDistance;
Vector3 target = _catTransform.position + clamped * _aimWeight + moveOffset;
```

### 테스트 체크리스트

- [ ] Cat이 화면 구석으로 이동해도 캐릭터가 잘리지 않는가
- [ ] Onion이 화면 끝까지 커서를 이동해도 적이 보이는가
- [ ] 방 경계에서 카메라가 벽 밖을 비추지 않는가
- [ ] 두 입력 기기(키보드+마우스) 동시 사용 시 부드러운가

---

## 참고 링크

- [Cinemachine Virtual Camera Follow 공식 문서](https://docs.unity3d.com/Packages/com.unity.cinemachine@2.9/manual/CinemachineVirtualCamera.html)
- [Cinemachine Confiner2D](https://docs.unity3d.com/Packages/com.unity.cinemachine@2.9/api/Cinemachine.CinemachineConfiner2D.html)
- [Camera Techniques for 2D Top-Down Games - Unity Blog](https://unity.com/blog)
- [New Input System - Mouse Position to World](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/index.html)
