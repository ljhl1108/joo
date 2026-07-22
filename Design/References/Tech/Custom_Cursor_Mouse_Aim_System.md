# 커스텀 커서 & 마우스 조준 비주얼 시스템

리서치 날짜: 2026-07-22

## 개요

Crop(양파)은 마우스로 조준하고 투사체를 발사한다. 기본 Windows OS 커서 대신 게임에 맞는 조준선(crosshair) 커서를 보여주는 것은 완성도 높은 게임의 필수 요소다. 커서 자체가 UI이자 실시간 피드백 도구이므로, 잘 구현하면 타격감·조준감·게임 몰입도가 한꺼번에 향상된다.

## Unity 구현 방법

### 방법 A: Cursor.SetCursor() — 하드웨어 커서 (추천 첫 단계)

```csharp
public class CustomCursorManager : MonoBehaviour
{
    [SerializeField] private Texture2D crosshairTexture;
    private Vector2 hotspot = new Vector2(16, 16); // 클릭 감지 중심점

    void Start()
    {
        Cursor.SetCursor(crosshairTexture, hotspot, CursorMode.Auto);
        Cursor.visible = true;
    }

    void OnDestroy()
    {
        Cursor.SetCursor(null, Vector2.zero, CursorMode.Auto); // 기본 커서 복원
    }
}
```

- 장점: 하드웨어 가속(OS 수준 렌더링) → 지연 없음, 구현 5분
- 단점: 애니메이션 구현 복잡, 텍스처 크기 32×32 또는 64×64 권장
- `hotspot`: 텍스처 내 클릭 감지 좌표 (crosshair 정중앙)

### 방법 B: 소프트웨어 커서 — UI 오브젝트 마우스 추적 (애니메이션 필요 시)

```csharp
using UnityEngine.InputSystem;

public class SoftwareCursor : MonoBehaviour
{
    [SerializeField] private RectTransform cursorUI; // Screen Space Canvas 하위 Image
    [SerializeField] private Canvas canvas;

    void Awake()
    {
        Cursor.visible = false; // 기본 커서 숨김
    }

    void Update()
    {
        Vector2 mousePos = Mouse.current.position.ReadValue();

        RectTransformUtility.ScreenPointToLocalPointInRectangle(
            canvas.GetComponent<RectTransform>(),
            mousePos,
            canvas.worldCamera,
            out Vector2 localPos
        );

        cursorUI.localPosition = localPos;
    }
}
```

- 장점: DOTween 애니메이션, 색상 변경, 충전 바 등 자유롭게 추가 가능
- 단점: 약 1프레임 지연 발생

### Crop 투사체 방향 — 마우스 월드 좌표 변환

```csharp
using UnityEngine.InputSystem;

public class CropAimController : MonoBehaviour
{
    [SerializeField] private Camera mainCamera;
    [SerializeField] private Transform cropTransform;
    [SerializeField] private Transform aimDot; // 월드 공간 조준점 표시용 (선택)

    void Update()
    {
        Vector2 mouseScreen = Mouse.current.position.ReadValue();
        Vector3 worldPos = mainCamera.ScreenToWorldPoint(
            new Vector3(mouseScreen.x, mouseScreen.y, -mainCamera.transform.position.z)
        );
        worldPos.z = 0f;

        // 조준점 월드 표시
        if (aimDot != null)
            aimDot.position = worldPos;

        // Crop 스프라이트 조준 방향 회전
        Vector2 dir = (Vector2)worldPos - (Vector2)cropTransform.position;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
        cropTransform.rotation = Quaternion.Euler(0f, 0f, angle - 90f);
    }

    // 투사체 발사 시 방향 계산
    public Vector2 GetAimDirection()
    {
        Vector2 mouseScreen = Mouse.current.position.ReadValue();
        Vector3 worldPos = mainCamera.ScreenToWorldPoint(
            new Vector3(mouseScreen.x, mouseScreen.y, -mainCamera.transform.position.z)
        );
        return ((Vector2)worldPos - (Vector2)cropTransform.position).normalized;
    }
}
```

### 커서 상태 변화 (Context-Sensitive Cursor)

```csharp
public enum CursorState { Default, Aim, Shield, Interact }

public class CursorStateManager : MonoBehaviour
{
    [SerializeField] private Texture2D[] cursorTextures; // 상태별 텍스처 배열
    [SerializeField] private Vector2[] hotspots;

    public void SetState(CursorState state)
    {
        int i = (int)state;
        Cursor.SetCursor(cursorTextures[i], hotspots[i], CursorMode.Auto);
    }
}
// 전투 기본 → Aim / 방어막 활성 → Shield / 상호작용 오브젝트 위 → Interact
```

### 충전 투사체 시각화 — 소프트웨어 커서 활용

```csharp
// 마우스 버튼 홀드 중 커서 주변에 원형 충전 바 채우기
[SerializeField] private Image chargeRingImage; // Image Type: Filled, Method: Radial 360

void Update()
{
    if (Mouse.current.leftButton.isPressed)
    {
        chargeTime += Time.deltaTime;
        chargeRingImage.fillAmount = Mathf.Clamp01(chargeTime / maxChargeTime);
    }
    else
    {
        chargeTime = 0f;
        chargeRingImage.fillAmount = 0f;
    }
}
```

### 게임패드 감지 시 커서 숨기기

```csharp
// New Input System 기반 — 입력 장치 전환 감지
InputSystem.onActionChange += (obj, change) =>
{
    if (change == InputActionChange.ActionPerformed)
    {
        var action = (InputAction)obj;
        bool usingGamepad = action.activeControl?.device is Gamepad;
        Cursor.visible = !usingGamepad;
    }
};
```

## OnionCat 적용 포인트

### Crop 전용 커서 3단계 디자인

| 상태 | 커서 모양 | 조건 |
|------|-----------|------|
| 기본 조준 | 작은 십자선(crosshair) + 중심 점 | 기본 상태 |
| 방어막 활성 | 방패 아이콘 + 파란 테두리 | Shield 버튼 홀드 |
| 충전 중 | 십자선 + 원형 충전 바 | 투사체 차지 중 |
| 상호작용 가능 | 십자선 + 하단 화살표 | 상호작용 오브젝트 위 |

### 구현 우선순위 (초보자 권장 순서)

1. `Cursor.SetCursor()`로 기본 crosshair 즉시 적용 (5분)
2. `ScreenToWorldPoint()`로 Crop 투사체 발사 방향 계산
3. AimDot(빈 GameObject + SpriteRenderer) 월드 공간에 조준점 표시
4. 방어막 상태 → CursorStateManager로 커서 전환
5. 충전 투사체 → 소프트웨어 커서로 전환 + 원형 충전 바 추가

### P1 Cat (게임패드) 처리
Cat은 게임패드 스틱으로 이동 → 커서 불필요. `Gamepad.all.Count > 0` 감지 시 OS 커서 숨김. 단, P2 Crop은 항상 마우스 사용 → 커서 유지.

## 참고 링크

- Unity 공식 - Cursor class: https://docs.unity3d.com/ScriptReference/Cursor.html
- Unity 공식 - Cursor.SetCursor: https://docs.unity3d.com/ScriptReference/Cursor.SetCursor.html
- Unity - ScreenToWorldPoint: https://docs.unity3d.com/ScriptReference/Camera.ScreenToWorldPoint.html
- Unity New Input System - Mouse: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/Mouse.html
- Unity UI Image (Filled / Radial): https://docs.unity3d.com/Manual/script-Image.html
