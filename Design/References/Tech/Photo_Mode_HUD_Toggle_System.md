# 포토 모드 / HUD 숨기기 스크린샷 시스템 (Photo Mode & HUD Toggle)

리서치 날짜: 2026-10-28

## 개요

플레이어가 게임 중 멋진 장면을 포착할 수 있도록 HUD를 숨기거나 카메라를 자유롭게 움직이는 **포토 모드** 시스템.
단순 스크린샷(캡처 키)과 달리, 다음 요소를 포함한다:
- HUD 전체 또는 부분 숨기기
- 게임 일시정지(또는 슬로우 모션)
- (선택) 카메라 위치·줌 자유 조정
- (선택) 촬영 후 공유 버튼

OnionCat의 필요성:
- 두 캐릭터의 픽셀아트 연출이 예쁜 순간(합동기, 보스 사망, 방 클리어)을 SNS 공유 가능하게
- 인디 게임 바이럴 마케팅에서 플레이어 스크린샷이 매우 유효
- 구현 비용이 낮아 완성도 높은 게임 느낌을 빠르게 더할 수 있음

---

## 기능 수준별 구현 범위

| 레벨 | 기능 | 구현 시간 |
|---|---|---|
| **Basic** | F12로 HUD 토글 + 시스템 스크린샷 | 1시간 |
| **Standard** | 정지 모드 + HUD 숨기기 + 필터 1~2개 | 반나절 |
| **Full** | 카메라 자유이동 + 줌 + 회전 + SNS 공유 | 2~3일 |

OnionCat 권장: **Standard** 수준. 제작·마케팅 비용 대비 효과 가장 좋음.

---

## Unity 구현 방법

### 1. HUD 숨기기 (가장 단순)

```csharp
// HUDVisibilityController.cs
public class HUDVisibilityController : MonoBehaviour
{
    private Canvas[] _allCanvases;

    void Start()
    {
        _allCanvases = FindObjectsByType<Canvas>(FindObjectsSortMode.None);
    }

    public void SetHUDVisible(bool visible)
    {
        foreach (var c in _allCanvases)
        {
            // World Space 캔버스(적 체력바 등)와 Screen Space 구분
            if (c.renderMode == RenderMode.ScreenSpaceOverlay ||
                c.renderMode == RenderMode.ScreenSpaceCamera)
            {
                c.gameObject.SetActive(visible);
            }
        }
    }
}
```

**OnionCat에서는** `CoreHUD` 캔버스 오브젝트를 직접 토글하는 게 더 안전:
```csharp
GameObject.Find("CoreHUD").SetActive(!visible);
```

### 2. Photo Mode 전체 흐름 (Standard)

```csharp
// PhotoModeManager.cs
public class PhotoModeManager : MonoBehaviour
{
    public bool IsActive { get; private set; }

    [SerializeField] private GameObject hudRoot;
    [SerializeField] private GameObject photoModeUI; // "사진 모드 중" 텍스트 표시용

    void Update()
    {
        // F12 또는 패드 특정 조합으로 토글
        if (Input.GetKeyDown(KeyCode.F12))
            Toggle();
    }

    void Toggle()
    {
        IsActive = !IsActive;

        // 게임 정지 (Time.timeScale은 GameManager 규칙으로 직접 건드리지 않음)
        // → GameManager.ChangeState(IsActive ? GameState.Paused : GameState.Battle)
        // 단, 포토모드 전용 상태를 만들어야 일시정지 메뉴와 분리됨

        hudRoot.SetActive(!IsActive);
        photoModeUI.SetActive(IsActive);

        if (IsActive)
            TakeScreenshot(); // 즉시 찍기 or 플레이어가 찍는 버튼 따로 제공
    }

    IEnumerator TakeScreenshot()
    {
        yield return new WaitForEndOfFrame();
        string path = Application.persistentDataPath + "/screenshot_" +
                      System.DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".png";
        ScreenCapture.CaptureScreenshot(path, 2); // 2x 해상도
        Debug.Log($"Screenshot saved: {path}");
        // TODO: 저장 완료 토스트 알림 표시
    }
}
```

### 3. 픽셀아트 게임 전용 고려사항

```
문제: ScreenCapture.CaptureScreenshot이 게임 해상도(640×360)로 저장되면 너무 작음
해결: 
  - superSize = 4 → 2560×1440 출력 (하지만 픽셀 블러 발생)
  - 또는 게임 해상도 유지 후 공유 시 "원본 픽셀 스타일"로 안내
  
문제: Pixel Perfect Camera가 켜진 상태에서 스크린샷 찍으면 픽셀 격자가 날카롭게 나옴
해결: 이 상태가 오히려 픽셀아트의 매력 → 그대로 유지 권장

문제: Unity의 URP post-processing 효과가 스크린샷에 포함되기도 하고 안 되기도 함
해결: Camera.Render() 직접 호출 방식 또는 RenderTexture 방식 사용
```

### 4. 카메라 자유이동 (Full 수준, 나중에)

```csharp
// 포토모드에서만 활성화되는 카메라 컨트롤러
public class PhotoCameraController : MonoBehaviour
{
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private float zoomSpeed = 2f;

    void Update()
    {
        if (!PhotoModeManager.Instance.IsActive) return;

        // WASD로 카메라 이동
        Vector3 move = new Vector3(Input.GetAxis("Horizontal"), Input.GetAxis("Vertical"), 0);
        transform.position += move * moveSpeed * Time.unscaledDeltaTime;

        // 마우스 휠로 줌
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        Camera.main.orthographicSize -= scroll * zoomSpeed;
        Camera.main.orthographicSize = Mathf.Clamp(Camera.main.orthographicSize, 2f, 15f);
    }
}
```

### 5. 필터 효과 (간단한 버전)

URP 2D Global Volume의 Post-processing 설정을 런타임에 조정:
```csharp
// Bloom, Vignette, Color Grading 강도를 슬라이더로 조절
// Volume.profile.TryGet<Bloom>(out var bloom)
// bloom.intensity.Override(value);
```

픽셀아트 게임에서 가장 인기 있는 필터: **비네트(Vignette)** + **색상 그레이딩(레트로 팔레트)**

---

## OnionCat 적용 포인트

### 1. 포토모드 진입 조건
- **방 클리어 후** (적이 없는 상태) 또는 **일시정지 메뉴**에서만 진입 허용
- 전투 중 포토모드 금지 → `GameManager.IsGameplayActive` 활용

### 2. 이상적인 포토 대상 장면
- 합동기 발동 직후 (ONION STORM 이펙트)
- 보스 사망 연출
- 업그레이드 카드 선택 화면
- 방 클리어 직후 (둘이 나란히 서 있는 장면)

### 3. GameState 확장
```csharp
public enum GameState
{
    // 기존 상태들...
    PhotoMode   // 포토모드 전용 상태: 게임 정지 + 행동 입력 막힘 + HUD 숨김
}
```
`GameManager.ChangeState(GameState.PhotoMode)` 호출 시:
- `Time.timeScale`은 여전히 건드리지 않음
- `IsGameplayActive = false`로 입력 차단
- 별도 포토모드 입력 컨트롤러만 활성화

### 4. 저장 위치
```
Windows: %USERPROFILE%\AppData\LocalLow\<CompanyName>\OnionCat\Screenshots\
```
`Application.persistentDataPath + "/Screenshots/"` 폴더 자동 생성 후 저장.

### 5. 마케팅 활용
- Steam 스크린샷 라이브러리에 자동 업로드: `SteamScreenshots.AddScreenshotToLibrary()`
- 저장 완료 시 "Steam 라이브러리에 추가됨" 토스트 알림
- Steam 페이지의 스크린샷 섹션은 플레이어가 올린 스크린샷으로 채워지면 구매 전환율 ↑

---

## 완성도 체크리스트

```
[ ] F12(또는 패드 조합)으로 HUD 토글
[ ] HUD 없는 상태에서 스크린샷 저장 (persistentDataPath)
[ ] 저장 완료 토스트 알림
[ ] 포토모드 중 일시정지 메뉴 진입 방지
[ ] 포토모드 종료 시 게임 상태 복원 (HUD 복귀, 입력 재활성화)
[ ] (선택) 카메라 자유이동
[ ] (선택) 줌 인/아웃
[ ] (선택) 비네트/색상 필터 1~2개
[ ] (선택) Steam 라이브러리 자동 업로드
```

---

## 참고 링크

- [Unity Docs: ScreenCapture.CaptureScreenshot](https://docs.unity3d.com/ScriptReference/ScreenCapture.CaptureScreenshot.html)
- [Unity Forum: Photo Mode implementation](https://forum.unity.com/threads/photo-mode-hud-toggle.567890/)
- [Steamworks SDK: Steamworks.NET Screenshots](https://steamworks.github.io/SteamScreenshots/)
- [URP 2D Post Processing Runtime](https://docs.unity3d.com/Packages/com.unity.render-pipelines.universal@latest)
- [Hades 2 Photo Mode 예시 참고 (2024)](https://www.polygon.com/hades-2)
