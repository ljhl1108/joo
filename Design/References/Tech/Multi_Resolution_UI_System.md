# 해상도 대응 UI 시스템 (Multi-Resolution UI / Canvas Scaler)

리서치 날짜: 2026-07-27

## 개요

Unity에서 게임을 다양한 해상도와 화면비에서 올바르게 표시하려면 Canvas Scaler 설정과 Anchor/Pivot 배치 전략이 필수다. 잘못 설정하면 1080p에서 완벽해 보이는 UI가 1440p나 울트라와이드 모니터에서 깨지거나 잘린다. OnionCat은 PC 대상 2인 로컬 코옵이므로 16:9 기준 설계하되 16:10, 21:9, 4:3도 깨지지 않아야 한다.

---

## Unity Canvas 기본 구조 이해

```
Canvas (Screen Space - Overlay)
  └── Canvas Scaler (Component)
  └── Canvas Group
  └── HUD Panel
  └── Pause Menu Panel
```

Canvas는 **Screen Space - Overlay** 모드가 가장 일반적 (화면에 항상 위에 렌더링).
3D 공간 UI가 필요하면 World Space 사용.

---

## Canvas Scaler 3가지 모드

### 1. Constant Pixel Size (기본값, 비권장)
- UI 요소 크기가 픽셀 단위로 고정
- 1080p에서는 좋아 보이지만 4K에서 UI가 너무 작아짐
- 대부분의 경우 **사용하지 말 것**

### 2. Scale with Screen Size (권장)
- **Reference Resolution** 기준으로 화면 크기에 맞게 UI 전체가 스케일
- 가장 많이 사용되는 방식
- **Match Width or Height**: 0~1 슬라이더
  - 0 = 너비 기준으로 스케일 (가로를 맞춤)
  - 1 = 높이 기준으로 스케일 (세로를 맞춤)
  - 0.5 = 중간 (대부분의 2D 게임에 적합)

### 3. Constant Physical Size
- 인치/cm 단위로 고정 (모바일 일부 용도)
- PC 게임에서는 거의 사용 안 함

---

## OnionCat 권장 설정

```
Canvas Scaler:
  UI Scale Mode: Scale with Screen Size
  Reference Resolution: 1920 x 1080
  Screen Match Mode: Match Width or Height
  Match: 0.5
```

**이유**: 1920×1080이 PC 게임 표준. Match 0.5는 와이드스크린과 일반 화면 모두에서 균형 있게 동작.

---

## Anchor / Pivot 배치 전략

Anchor는 UI 요소가 부모(화면)의 어느 기준점에 고정될지 결정한다.

### 기본 규칙
| UI 요소 위치 | Anchor 설정 |
|-------------|-------------|
| 화면 좌상단 (체력바) | Min(0,1) Max(0,1) |
| 화면 우상단 (쿨다운) | Min(1,1) Max(1,1) |
| 화면 하단 중앙 (스킬바) | Min(0.5,0) Max(0.5,0) |
| 화면 정중앙 (일시정지 메뉴) | Min(0.5,0.5) Max(0.5,0.5) |
| 전체 화면 스트레치 (배경 패널) | Min(0,0) Max(1,1) |

### Pivot 설정
- Pivot은 요소 자신의 원점 위치
- 우상단 앵커 UI는 Pivot도 (1,1)로 설정해야 올바르게 코너에 고정

---

## 실전 구현 패턴

### Safe Area 처리 (모바일 노치 대응)
PC는 불필요하지만, 향후 모바일 빌드 대비:

```csharp
// SafeAreaHandler.cs
public class SafeAreaHandler : MonoBehaviour
{
    [SerializeField] private RectTransform panel;
    
    private void Start()
    {
        ApplySafeArea();
    }
    
    private void ApplySafeArea()
    {
        Rect safeArea = Screen.safeArea;
        Vector2 anchorMin = safeArea.position;
        Vector2 anchorMax = safeArea.position + safeArea.size;
        
        anchorMin.x /= Screen.width;
        anchorMin.y /= Screen.height;
        anchorMax.x /= Screen.width;
        anchorMax.y /= Screen.height;
        
        panel.anchorMin = anchorMin;
        panel.anchorMax = anchorMax;
    }
}
```

### 해상도 변경 감지

```csharp
// ResolutionManager.cs
public class ResolutionManager : MonoBehaviour
{
    private int lastWidth;
    private int lastHeight;
    
    private void Start()
    {
        lastWidth = Screen.width;
        lastHeight = Screen.height;
    }
    
    private void Update()
    {
        if (Screen.width != lastWidth || Screen.height != lastHeight)
        {
            lastWidth = Screen.width;
            lastHeight = Screen.height;
            OnResolutionChanged();
        }
    }
    
    private void OnResolutionChanged()
    {
        // 필요 시 UI 재정렬 로직
        EventBus.Publish(new ResolutionChangedEvent(Screen.width, Screen.height));
    }
}
```

### 화면비에 따른 레터박스/필러박스

```csharp
// AspectRatioEnforcer.cs
// 카메라에 부착 — 항상 16:9 비율 유지
public class AspectRatioEnforcer : MonoBehaviour
{
    [SerializeField] private float targetAspect = 16f / 9f;
    
    private Camera cam;
    
    private void Awake()
    {
        cam = GetComponent<Camera>();
    }
    
    private void Start()
    {
        ApplyAspectRatio();
    }
    
    private void ApplyAspectRatio()
    {
        float windowAspect = (float)Screen.width / Screen.height;
        float scaleHeight = windowAspect / targetAspect;
        
        if (scaleHeight < 1f)
        {
            // 레터박스 (위아래 검은 띠)
            Rect rect = cam.rect;
            rect.width = 1f;
            rect.height = scaleHeight;
            rect.x = 0;
            rect.y = (1f - scaleHeight) / 2f;
            cam.rect = rect;
        }
        else
        {
            // 필러박스 (좌우 검은 띠)
            float scaleWidth = 1f / scaleHeight;
            Rect rect = cam.rect;
            rect.width = scaleWidth;
            rect.height = 1f;
            rect.x = (1f - scaleWidth) / 2f;
            rect.y = 0;
            cam.rect = rect;
        }
    }
}
```

---

## 설정 메뉴에서 해상도 변경

```csharp
// ResolutionSettingsUI.cs
public class ResolutionSettingsUI : MonoBehaviour
{
    [SerializeField] private TMP_Dropdown resolutionDropdown;
    
    private Resolution[] availableResolutions;
    
    private void Start()
    {
        availableResolutions = Screen.resolutions;
        resolutionDropdown.ClearOptions();
        
        var options = new List<string>();
        int currentIndex = 0;
        
        for (int i = 0; i < availableResolutions.Length; i++)
        {
            var res = availableResolutions[i];
            options.Add($"{res.width} x {res.height} @ {res.refreshRateRatio.numerator}Hz");
            
            if (res.width == Screen.currentResolution.width &&
                res.height == Screen.currentResolution.height)
            {
                currentIndex = i;
            }
        }
        
        resolutionDropdown.AddOptions(options);
        resolutionDropdown.value = currentIndex;
        resolutionDropdown.onValueChanged.AddListener(OnResolutionSelected);
    }
    
    private void OnResolutionSelected(int index)
    {
        var res = availableResolutions[index];
        Screen.SetResolution(res.width, res.height, Screen.fullScreenMode);
        PlayerPrefs.SetInt("ResolutionWidth", res.width);
        PlayerPrefs.SetInt("ResolutionHeight", res.height);
    }
}
```

---

## 전체화면 모드 처리

```csharp
public void SetFullscreen(bool isFullscreen)
{
    Screen.fullScreenMode = isFullscreen 
        ? FullScreenMode.FullScreenWindow  // 보더리스 권장
        : FullScreenMode.Windowed;
    PlayerPrefs.SetInt("Fullscreen", isFullscreen ? 1 : 0);
}
```

`ExclusiveFullScreen`보다 `FullScreenWindow`(보더리스)를 권장 — Alt+Tab이 자연스럽고 멀티모니터 환경 친화적.

---

## 자주 하는 실수

| 실수 | 해결책 |
|------|--------|
| UI 요소가 화면 밖으로 잘림 | Anchor를 화면 코너에 맞추고 Stretch 사용 |
| 4K에서 UI가 너무 작음 | Canvas Scaler를 Constant Pixel Size → Scale with Screen Size로 변경 |
| 울트라와이드에서 UI가 이상함 | Match 0.5 + 중요 UI는 중앙 앵커 사용 |
| 텍스트가 흐림 | TextMeshPro 사용 + 폰트 Atlas 크기 충분히 설정 |
| 화면비 바꿀 때 카메라 영역 이상함 | AspectRatioEnforcer 스크립트 추가 |

---

## OnionCat 적용 포인트

| 상황 | 설정 |
|------|------|
| 기본 타겟 | 1920×1080, 16:9 |
| 16:10 (2560×1600) | Match 0.5로 자동 대응 — 상하에 약간 여백 |
| 21:9 울트라와이드 | 레터박스 처리 또는 UI 좌우 여백 확장 |
| 4K | Scale with Screen Size가 자동 2배 스케일 |
| 2인 분할화면 고려 시 | 각 플레이어 뷰에 별도 Canvas (World Space) 사용 검토 |

### Inspector 설정 순서
1. Canvas 오브젝트 생성
2. Canvas Scaler → Scale with Screen Size → 1920×1080 → Match 0.5
3. 각 UI 요소에 적절한 Anchor Preset 설정 (Inspector Anchor 버튼 클릭)
4. 게임 뷰에서 해상도 드롭다운으로 여러 비율 테스트

---

## 참고 링크

- Unity Canvas Scaler 공식 문서: https://docs.unity3d.com/Manual/script-CanvasScaler.html
- Unity UI Anchors 공식 문서: https://docs.unity3d.com/Manual/UIBasicLayout.html
- Screen.SetResolution: https://docs.unity3d.com/ScriptReference/Screen.SetResolution.html
- TextMeshPro 공식 문서: https://docs.unity3d.com/Packages/com.unity.textmeshpro@3.0/manual/index.html
- Unity Multiple Resolutions 공식 가이드: https://docs.unity3d.com/Manual/HOWTO-UIMultiResolution.html
