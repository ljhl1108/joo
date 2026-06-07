# 카메라 시스템 (Camera System)

## 개요

유니티 2D 탑다운 픽셀아트 로그라이크에서 카메라는 단순한 "화면 이동"이 아니라 게임 피드백의 핵심이다. OnionCat은 방 기반 던전 구조와 두 플레이어가 한 몸을 공유하는 특수 상황이 있어, 방 전환 카메라 + 화면 진동 + 픽셀 퍼펙트 설정이 모두 필요하다.

---

## Unity 구현 방법

### 1. Cinemachine 기반 기초 설정

**아키텍처 구조:**
```
Main Camera (World Space)
├── Cinemachine Brain  ← 필수, 없으면 Virtual Camera가 작동 안 함
└── CinemachineVirtualCamera(s)
    ├── Follow: Player Transform
    ├── Confiner2D (방 경계 제한)
    └── ImpulseListener (화면 진동 수신)
```

**Virtual Camera 기본 설정 (Inspector):**
- Projection: Orthographic (2D에서 필수)
- Body: Framing Transposer (Smooth Follow용)
- Aim: Do Nothing (탑다운에서 회전 불필요)

```csharp
public class CameraSetup : MonoBehaviour
{
    [SerializeField] private CinemachineVirtualCamera vcam;
    [SerializeField] private Transform playerFollow;

    private void Start()
    {
        vcam.Follow = playerFollow;

        var transposer = vcam.GetCinemachineComponent<CinemachineFramingTransposer>();
        transposer.m_XDamping = 0.7f; // 0 = 즉시 따라옴, 1 = 매우 느림
        transposer.m_YDamping = 0.7f;
        transposer.m_LookaheadTime = 0.5f; // 플레이어 이동 방향 미리 보기
    }
}
```

---

### 2. 방 전환 카메라 (Room Transition)

Priority 시스템으로 방마다 Virtual Camera를 전환. Cinemachine Brain이 자동으로 블렌드 처리.

```csharp
public class CameraRoomManager : MonoBehaviour
{
    [SerializeField] private CinemachineVirtualCamera[] roomCameras;
    private int currentRoomIndex = -1;

    public void TransitionToRoom(int roomIndex)
    {
        if (currentRoomIndex >= 0)
            roomCameras[currentRoomIndex].Priority = 0;

        roomCameras[roomIndex].Priority = 10;
        currentRoomIndex = roomIndex;
    }
}
```

**Cinemachine Brain 블렌드 설정 (Inspector):**
- Default Blend: EaseInOut, 0.5초 → 부드러운 방 전환
- Custom Blend: Cut → 즉시 전환 (Enter the Gungeon 스타일)

---

### 3. 방 경계 제한 (Confiner2D)

카메라가 방 밖의 빈 공간을 보여주지 않도록 제한.

**설정 순서:**
1. 방 오브젝트에 자식 GameObject 추가 → `BoxCollider2D` 추가 (방 크기로 설정)
2. Virtual Camera에 Extension 추가 → `CinemachineConfiner2D`
3. `Bounding Shape 2D` 필드에 해당 Collider 드래그

```csharp
public class RoomManager : MonoBehaviour
{
    [SerializeField] private CinemachineVirtualCamera vcam;

    public void EnterRoom(PolygonCollider2D roomBounds)
    {
        var confiner = vcam.GetComponent<CinemachineConfiner2D>();
        confiner.m_BoundingShape2D = roomBounds;
        confiner.InvalidateCache(); // 반드시 호출 — 경계 변경 후 캐시 무효화
    }
}
```

**주의**: 방 경계 Collider는 플레이 가능 영역보다 약간 커야 함. 같은 크기면 가장자리에서 카메라가 끊김.

---

### 4. 화면 진동 — CinemachineImpulse

**설정 순서:**
1. Virtual Camera에 Extension 추가 → `CinemachineImpulseListener`
2. 피격/폭발 오브젝트에 `CinemachineImpulseSource` 컴포넌트 추가
3. 코드에서 `GenerateImpulseWithForce()` 호출

```csharp
public class HitFeedback : MonoBehaviour
{
    [SerializeField] private CinemachineImpulseSource impulseSource;

    public void OnHit(float damage)
    {
        float strength = Mathf.Clamp(damage / 10f, 0.3f, 2.0f);
        impulseSource.GenerateImpulseWithForce(strength);
    }

    public void OnDirectionalHit(Vector2 hitDirection, float strength)
    {
        // 타격 방향으로 흔들림
        impulseSource.GenerateImpulse(hitDirection * strength);
    }
}
```

**권장 강도값:**
- 일반 피격: 0.5 ~ 1.0
- 폭발/보스 공격: 1.5 ~ 2.0
- 지속 시간: 0.2 ~ 0.3초 (너무 길면 멀미 유발)

**2D 설정 필수**: ImpulseSource Inspector에서 "2D Distance" 체크 — 미체크 시 Z 거리 계산 오류

---

### 5. 픽셀 퍼펙트 카메라 (Pixel Perfect Camera)

픽셀아트에서 서브픽셀 이동으로 스프라이트가 흔들리는 문제 방지.

**스프라이트 Import 설정 (필수):**
- Filter Mode: **Point** (Linear이면 블러 발생)
- Compression: **None**
- Pixels Per Unit: 일관되게 통일 (예: 32)

**Pixel Perfect Camera 컴포넌트 설정:**
```csharp
public class PixelPerfectSetup : MonoBehaviour
{
    private const int PPU = 32;           // Pixels Per Unit
    private const int REF_WIDTH = 320;    // 기준 해상도 (타겟 픽셀아트 해상도)
    private const int REF_HEIGHT = 180;

    private void Awake()
    {
        var ppc = Camera.main.GetComponent<PixelPerfectCamera>();
        ppc.assetsPPU = PPU;
        ppc.refResolutionX = REF_WIDTH;
        ppc.refResolutionY = REF_HEIGHT;
        ppc.upscaleRT = true;
        ppc.pixelSnapping = true;
    }
}
```

**카메라 이동 시 픽셀 그리드에 스냅:**
```csharp
// 서브픽셀 움직임 방지
Vector3 pos = Vector3.Lerp(transform.position, target, Time.deltaTime * speed);
float snap = 1f / PPU;
pos.x = Mathf.Round(pos.x / snap) * snap;
pos.y = Mathf.Round(pos.y / snap) * snap;
transform.position = pos;
```

---

## OnionCat 적용 포인트

### 두 플레이어 한 몸 → 조준 방향 카메라 오프셋

Cat이 이동, Crop이 마우스로 조준하므로 카메라가 조준 방향 앞쪽을 더 보여주면 시야 확보에 유리하다.

```csharp
public class OnionCatCamera : MonoBehaviour
{
    [SerializeField] private CinemachineVirtualCamera vcam;

    public void UpdateAimOffset(Vector2 aimDirection)
    {
        var framing = vcam.GetCinemachineComponent<CinemachineFramingTransposer>();
        float lookAhead = 2f; // 조준 방향으로 2유닛 앞을 보여줌
        framing.m_TrackedObjectOffset = aimDirection.normalized * lookAhead;
    }
}
```

### 방 전환 시 권장 흐름
1. Player가 문 트리거에 진입
2. `CameraRoomManager.TransitionToRoom(nextRoomIndex)` 호출
3. Cinemachine이 0.5초 블렌드로 부드럽게 전환
4. `confiner.InvalidateCache()` 호출로 새 방 경계 적용

### 피격 진동 적용 위치
- Cat이 피격 시: `HitFeedback.OnHit(damage)` → 강도 0.8
- 적 처치 시: → 강도 0.3 (경쾌한 느낌)
- Crop 파리 방어/패리 성공 시: → 방향성 진동 (막은 방향 반대로)

---

## 참고 링크

- [Unity URP Pixel Perfect Camera](https://docs.unity3d.com/6000.1/Documentation/Manual/urp/2d-pixelperfect-intro.html)
- [Cinemachine 공식 문서 (탑다운)](https://docs.unity3d.com/Packages/com.unity.cinemachine@2.2/manual/CinemachineTopDown.html)
- [Cinemachine Confiner2D](https://docs.unity3d.com/Packages/com.unity.cinemachine@3.1/manual/CinemachineConfiner2D.html)
- [Cinemachine Impulse 문서](https://docs.unity3d.com/Packages/com.unity.cinemachine@2.3/manual/CinemachineImpulse.html)
- [YouTube: Screen Shake with Cinemachine](https://www.youtube.com/watch?v=CgyLIWyDXqo)
- [YouTube: Cinemachine Confiner Bounding Box](https://www.youtube.com/watch?v=izumXk-xoEM)
