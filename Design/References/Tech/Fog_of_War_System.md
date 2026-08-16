# Fog of War System (2D 안개 시스템)

리서치 날짜: 2026-08-16

## 개요

Fog of War(전쟁의 안개)는 플레이어가 **탐험하거나 시야 내에 있는 영역만 밝히고, 나머지는 어둠/안개로 가리는** 시스템이다. 탑다운 로그라이크에서 두 가지 형태로 쓰인다:

1. **탐험 안개 (Exploration Fog)** — 방문한 적 없는 구역을 검은 안개로 가림 (미니맵 연동)
2. **시야 안개 (Sight Fog)** — 플레이어의 현재 시야 범위 밖을 어둠으로 가림 (실시간 갱신)

OnionCat에는 **시야 안개를 특수 방으로 제한 사용**하는 것이 적합하다. P1과 P2의 시야 범위가 서로 다르면 "정보 공유 소통"을 게임플레이로 만들 수 있다.

---

## Unity 구현 방법

### 방법 1: URP 2D Light로 구현 (추천, 초보자 적합)

```csharp
// 1. 전역 조명을 어둡게 설정
// Global Light 2D → Intensity = 0 (또는 0.05f로 약간만 남김)

// 2. 각 플레이어에 Point Light 2D 부착
// P1에 부착할 스크립트:
using UnityEngine;
using UnityEngine.Rendering.Universal;

public class PlayerVisionLight : MonoBehaviour
{
    [SerializeField] private Light2D visionLight;
    [SerializeField] private float normalRadius = 4f;

    void Awake()
    {
        visionLight = GetComponent<Light2D>();
        visionLight.pointLightOuterRadius = normalRadius;
    }
}

// 3. P2(마우스 조준)는 커서 방향 원뿔 조명 사용
using UnityEngine;
using UnityEngine.Rendering.Universal;

public class P2CursorVisionLight : MonoBehaviour
{
    [SerializeField] private Light2D spotLight;
    [SerializeField] private Camera mainCamera;

    void Update()
    {
        Vector3 mousePos = mainCamera.ScreenToWorldPoint(Input.mousePosition);
        mousePos.z = 0;
        Vector2 dir = (mousePos - transform.position).normalized;
        float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg - 90f;
        spotLight.transform.rotation = Quaternion.Euler(0, 0, angle);
    }
}
```

**URP 설정:**
- URP Asset → 2D Renderer → Use Depth/Stencil Buffer: ON
- 각 플레이어 GameObject에 Light 2D (Point 또는 Spot) 추가
- Light Layer를 별도 설정해 P1/P2 조명 독립 제어 가능

---

### 방법 2: RenderTexture + Stencil Shader (고급, 유연)

```csharp
// 안개 마스크용 RenderTexture 기반 접근
// 별도 Camera → FogMask RenderTexture 렌더링
// 쉐이더에서 텍스처를 스크린에 오버레이
// 복잡도 높음 → 중급 이상 권장
```

---

### 방법 3: 오버레이 스프라이트 마스크 (단순, 모바일 적합)

```csharp
// 검은 스프라이트 오버레이 + SpriteMask로 구멍 뚫기
// 퍼포먼스 우수, 부드러운 경계선 어려움
// 2D 모바일 게임에서 자주 사용

public class SimpleVisionMask : MonoBehaviour
{
    [SerializeField] private SpriteMask visionMask;
    [SerializeField] private float visionRadius = 4f;

    void Update()
    {
        visionMask.transform.position = transform.position;
        visionMask.transform.localScale = Vector3.one * (visionRadius * 2f);
    }
}
```

---

### 특수 방 전용 안개 On/Off 시스템

```csharp
// 방 진입/퇴장 시 안개 시스템을 켜고 끄는 관리자
public class FogRoomManager : MonoBehaviour
{
    [SerializeField] private GameObject fogOverlay;      // 어두운 오버레이
    [SerializeField] private Light2D globalLight;        // 전역 조명
    [SerializeField] private float normalIntensity = 1f;
    [SerializeField] private float fogIntensity = 0.05f;
    [SerializeField] private float transitionDuration = 0.5f;

    public void EnterFogRoom()
    {
        fogOverlay.SetActive(true);
        StartCoroutine(LerpLightIntensity(normalIntensity, fogIntensity, transitionDuration));
    }

    public void ExitFogRoom()
    {
        StartCoroutine(LerpLightIntensity(fogIntensity, normalIntensity, transitionDuration));
        fogOverlay.SetActive(false);
    }

    private IEnumerator LerpLightIntensity(float from, float to, float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            globalLight.intensity = Mathf.Lerp(from, to, elapsed / duration);
            yield return null;
        }
        globalLight.intensity = to;
    }
}
```

---

### 탐험 안개 (미니맵용)

```csharp
// 방 단위 탐험 공개 — 복잡한 픽셀 안개 없이 방 아이콘 Show/Hide
public class ExplorationFogController : MonoBehaviour
{
    private Dictionary<string, bool> exploredRooms = new Dictionary<string, bool>();

    public void RevealRoom(string roomId)
    {
        exploredRooms[roomId] = true;
        // MinimapUI에 방 아이콘 표시 이벤트 발행
        EventBus.Publish(new RoomRevealedEvent { RoomId = roomId });
    }

    public bool IsExplored(string roomId)
    {
        return exploredRooms.TryGetValue(roomId, out bool explored) && explored;
    }
}
```

---

## OnionCat 적용 포인트

### 1. 특수 "정보 안개 방" 구현
- 방 ProtoType 중 하나로 **안개 방** 추가
- 방 진입 시 `FogRoomManager.EnterFogRoom()` 호출
- P1은 자신 주변 원형 시야(반경 3.5 유닛), P2는 마우스 커서 방향 원뿔 시야
- 두 플레이어 시야가 서로 다른 위치를 비추기 때문에 "오른쪽에 뭔가 있어!" 소통 필수

### 2. P1/P2 독립 시야 구현 방법 (URP 추천)
```
P1 GameObject → Point Light 2D (반경 3.5, 원형)
P2 GameObject → Spot Light 2D (원뿔 60도, 마우스 방향 회전)
Global Light 2D → Intensity 0.05f (아주 약한 환경광)
```

### 3. 성능 고려사항
- Light 2D는 URP에서 매우 효율적 → 2개 정도는 모바일도 OK
- 방 전용 특수 기능이므로 항상 켜두지 않아도 됨
- 방 진입 시 활성화, 방 퇴장 시 비활성화 → 성능 부담 없음

### 4. 디자인 주의사항
- 안개 방은 **"처음 등장"은 신선함**, 남발하면 피로함 → 런당 최대 1~2회 등장 권장
- P1과 P2가 너무 멀리 떨어지면 양쪽 다 아무것도 못 보는 상황 발생 → 의도된 긴장감이지만 설계 주의
- 미니맵은 안개 방에서도 탐험한 부분 표시 (방 단위 아이콘) 권장

---

## 참고 링크

- Unity 2D Lighting 공식 문서: https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest/manual/2DLighting-intro.html
- URP 2D Light 튜토리얼: https://learn.unity.com/tutorial/2d-lighting-in-urp
- Fog of War with URP: https://www.youtube.com/watch?v=IEqq5ISTsng
- 2D 시야각 구현 (세부): https://www.redblobgames.com/articles/visibility/
