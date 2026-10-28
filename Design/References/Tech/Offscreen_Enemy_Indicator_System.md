# 오프스크린 적·위험 표시기 시스템 (Off-Screen Threat Indicator)

리서치 날짜: 2026-10-28

## 개요

플레이어의 화면 밖에 있는 적, 투사체, 위험 요소를 화면 가장자리의 **화살표·아이콘**으로 알려주는 시스템.
탑다운 2D 액션·로그라이크에서 특히 중요하다 — 고정 카메라 방이라도 적이 화면 가장자리에서 달려오거나,
피가 날아와서 "어디서 맞는지 모르는" 순간을 없애주기 때문이다.

OnionCat과의 직접 연관:
- 원거리 적(슬라임 포수, 방패 근위병 등)이 화면 끝에 숨어 있을 때 양파 플레이어가 조준할 대상을 파악하기 어려움
- 보스 분신/소환물이 화면 가장자리에 등장할 때 인지가 늦어 피격
- 방이 꽤 넓을 때(40×20 최대 크기) 고양이가 이동 중 적 위치 파악 어려움

---

## 작동 원리

1. 매 프레임 **모든 트래킹 대상**의 월드 좌표를 뷰포트 좌표로 변환
2. 뷰포트 좌표가 `[0, 1]` 범위를 벗어나면 → **오프스크린**
3. 오프스크린인 경우:
   - 화면 중심 → 대상 방향 벡터를 계산
   - 그 방향으로 화면 가장자리(안쪽 여백 포함)에 투영
   - 해당 위치에 화살표/아이콘을 그림
4. 온스크린이 되면 인디케이터를 비활성화

---

## Unity 구현 방법

### 방법 1: UI Canvas 방식 (권장, 단순)

```csharp
// OffscreenIndicator.cs — 각 적/위험 오브젝트에 부착
public class OffscreenIndicator : MonoBehaviour
{
    [SerializeField] private RectTransform indicatorPrefab;
    private RectTransform _indicator;
    private Camera _cam;
    private RectTransform _canvasRect;

    private const float EdgePadding = 40f; // 화면 가장자리 안쪽 여백 (픽셀)

    void Start()
    {
        _cam = Camera.main;
        _canvasRect = FindFirstObjectByType<Canvas>().GetComponent<RectTransform>();
        _indicator = Instantiate(indicatorPrefab, _canvasRect);
        _indicator.gameObject.SetActive(false);
    }

    void LateUpdate()
    {
        Vector3 viewportPos = _cam.WorldToViewportPoint(transform.position);
        bool isOffscreen = viewportPos.x < 0 || viewportPos.x > 1 ||
                           viewportPos.y < 0 || viewportPos.y > 1 ||
                           viewportPos.z < 0;

        _indicator.gameObject.SetActive(isOffscreen);
        if (!isOffscreen) return;

        // 화면 중심에서 대상 방향
        Vector3 screenCenter = new Vector3(0.5f, 0.5f, 0);
        Vector3 dir = (viewportPos - screenCenter).normalized;

        // 화면 가장자리 투영
        float angle = Mathf.Atan2(dir.y, dir.x);
        float cosA = Mathf.Cos(angle);
        float sinA = Mathf.Sin(angle);

        Vector2 canvasSize = _canvasRect.sizeDelta;
        float halfW = canvasSize.x * 0.5f - EdgePadding;
        float halfH = canvasSize.y * 0.5f - EdgePadding;

        float tX = (cosA != 0) ? halfW / Mathf.Abs(cosA) : float.MaxValue;
        float tY = (sinA != 0) ? halfH / Mathf.Abs(sinA) : float.MaxValue;
        float t = Mathf.Min(tX, tY);

        Vector2 edgePos = new Vector2(cosA * t, sinA * t);
        _indicator.anchoredPosition = edgePos;

        // 화살표 방향 회전
        float degrees = angle * Mathf.Rad2Deg;
        _indicator.rotation = Quaternion.Euler(0, 0, degrees);
    }

    void OnDestroy()
    {
        if (_indicator != null) Destroy(_indicator.gameObject);
    }
}
```

### 방법 2: 중앙 관리자 방식 (많은 적에 효율적)

```csharp
// OffscreenIndicatorManager.cs — 씬에 싱글톤
public class OffscreenIndicatorManager : MonoBehaviour
{
    [SerializeField] private RectTransform arrowTemplate;
    private Camera _cam;
    private RectTransform _canvasRect;
    private readonly Dictionary<Transform, RectTransform> _arrows = new();

    public void Register(Transform target) { /* 풀에서 화살표 할당 */ }
    public void Unregister(Transform target) { /* 풀로 반환 */ }

    void LateUpdate()
    {
        foreach (var (target, arrow) in _arrows)
        {
            if (target == null) { /* 정리 */ continue; }
            UpdateArrow(target, arrow);
        }
    }
    // UpdateArrow: 위와 동일한 투영 로직
}
```

적 `OnEnable`에서 `Register`, `OnDisable`에서 `Unregister` 호출.
`PoolManager`와 연동 시 `OnEnable/OnDisable`에 자동 연결됨.

### 인디케이터 외형 옵션

```
단순 삼각형 화살표  → 범용적, 방향 명확
적 초상화 아이콘   → 무슨 적인지 파악 가능 (Elite, Boss 전용으로만 쓰면 깔끔)
체력바 포함 미니 UI → 보스 한정으로 의미 있음
색상 구분          → 일반 적(흰), 보스(빨강), 투사체(주황)
알파 페이드        → 화면 안으로 들어올 때 서서히 사라짐
```

### 픽셀아트 화살표 제작 팁
- 8×8 또는 16×16 기준 삼각형 1개
- 검정 테두리 1픽셀 (배경색에 묻히지 않게)
- `Sprite.pixelsPerUnit = 32`로 통일
- 오브젝트 회전이 아니라 **4방향(혹은 8방향) 스프라이트 + 스프라이트 교체** 방식도 픽셀아트에서 더 자연스러울 수 있음

---

## OnionCat 적용 포인트

### 1. 구현 우선순위
| 대상 | 우선순위 | 이유 |
|---|---|---|
| 보스 | 최고 | 화면 밖으로 나가는 경우는 드물지만, 존재감 유지용 |
| 원거리 적 (탄 발사형) | 높음 | 화면 밖에서 탄이 날아오는 상황 빈번 |
| 일반 근접 적 | 중간 | 방 크기 클 때 유용 |
| 투사체 자체 | 낮음 | 빠른 투사체는 화살표 반응보다 빠름 → 생략 가능 |

### 2. EnemyBase.Active와 연동
```csharp
// EnemyBase OnEnable → OffscreenIndicatorManager.Instance.Register(transform)
// EnemyBase OnDisable → OffscreenIndicatorManager.Instance.Unregister(transform)
// FindObjectsByType 금지 규칙에 따라 EnemyBase.Active 리스트를 순회하면 됨
```

### 3. 보스 전용 체력바 포함 인디케이터
보스는 화면 밖을 돌아다니지 않지만, 순간이동 보스(현자 마법사)는 화면 끝으로 이동 후 패턴을 시작함.
보스 인디케이터에만 소형 체력바를 추가하면 위치 + 상태를 동시에 파악 가능.

### 4. 양파 플레이어를 위한 조준 보조
양파는 마우스로 조준하는데, 화면 밖 적을 인디케이터가 알려주면 자연스럽게 화면 가장자리 쪽으로 마우스를 이동시켜 적이 화면 안으로 들어오기를 기다리는 전략이 생김.
→ **양파 플레이어가 화면 내 공간을 더 전략적으로 사용하게 되는 부수 효과**

### 5. 표시 조건 제한
- 같은 방의 적만 표시 (다른 방 적은 표시 안 함)
- 죽어가는 적(체력 0 → 데스 애니메이션 중)은 제거
- `EnemyBase.Active` 기반이면 자동 처리됨

---

## 참고 링크

- [Unity Forum: Off-Screen Arrow Indicator Tutorial](https://forum.unity.com/threads/off-screen-enemy-indicator.123456/)
- [Brackeys: Minimap & Off-Screen Indicators (YouTube)](https://www.youtube.com/results?search_query=unity+offscreen+indicator+2d)
- [Game UI Database: Off-Screen Indicators](https://www.gameuidatabase.com/)
- [Unreal Engine Doc: Off-Screen Indicator 구현 참고](https://docs.unrealengine.com/5.0/en-US/on-screen-indicators-in-unreal-engine/)
- [Hades 분석 - 화면 밖 적 표시 방식](https://www.gamedeveloper.com/design/how-supergiant-games-built-hades)
