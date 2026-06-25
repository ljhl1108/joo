# 접근성 옵션 시스템

리서치 날짜: 2026-06-25

## 개요

OnionCat은 2인 협력 플레이 탑다운 픽셀아트 로그라이크이므로, 접근성 시스템은 다양한 플레이어의 신체 능력과 감각 차이를 수용해야 한다. 색각이상, 전정기관 장애(화면 흔들림 민감), 청각 장애 등을 가진 플레이어들이 동등하게 즐길 수 있도록 설계하면, 일반 플레이어도 더 나은 경험을 얻는다.

Game Accessibility Guidelines(gameaccessibilityguidelines.com)에 따르면 인디 게임에서 가장 자주 요청되는 4가지는 **키 리맵핑, 텍스트 크기, 색각이상 모드, 화면 흔들림 토글**이다.

## Unity 구현 방법

### 1. 설정 저장 — PlayerPrefs 사용

접근성 설정은 런 데이터가 아니라 계정 수준 설정이므로 PlayerPrefs가 적합하다.

```csharp
public class AccessibilityManager : MonoBehaviour
{
    public static AccessibilityManager Instance { get; private set; }
    public static event System.Action OnSettingsChanged;

    public int ColorblindMode { get; private set; }       // 0=Normal 1=Protanopia 2=Deuteranopia 3=Tritanopia
    public float ScreenShakeIntensity { get; private set; } // 0~1
    public bool ScreenShakeEnabled { get; private set; }
    public float TextScale { get; private set; }           // 1.0~2.0

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        Load();
    }

    public void Load()
    {
        ColorblindMode      = PlayerPrefs.GetInt("a11y_colorblind", 0);
        ScreenShakeIntensity = PlayerPrefs.GetFloat("a11y_shake_intensity", 1f);
        ScreenShakeEnabled  = PlayerPrefs.GetInt("a11y_shake_on", 1) == 1;
        TextScale           = PlayerPrefs.GetFloat("a11y_text_scale", 1f);
    }

    public void Save()
    {
        PlayerPrefs.SetInt("a11y_colorblind", ColorblindMode);
        PlayerPrefs.SetFloat("a11y_shake_intensity", ScreenShakeIntensity);
        PlayerPrefs.SetInt("a11y_shake_on", ScreenShakeEnabled ? 1 : 0);
        PlayerPrefs.SetFloat("a11y_text_scale", TextScale);
        PlayerPrefs.Save();
        OnSettingsChanged?.Invoke();
    }

    public void SetColorblindMode(int mode)      { ColorblindMode = mode; Save(); }
    public void SetShakeIntensity(float v)       { ScreenShakeIntensity = v; Save(); }
    public void SetShakeEnabled(bool v)          { ScreenShakeEnabled = v; Save(); }
    public void SetTextScale(float v)            { TextScale = v; Save(); }
}
```

### 2. 화면 흔들림 강도 슬라이더

기존 FeedbackSystem / CinemachineImpulse 연동 예시:

```csharp
// FeedbackSystem.cs 내부 — 기존 TriggerShake 호출부 수정
public void TriggerShake(float duration, float magnitude)
{
    var a11y = AccessibilityManager.Instance;
    if (a11y == null || !a11y.ScreenShakeEnabled) return;

    float finalMagnitude = magnitude * a11y.ScreenShakeIntensity;
    _impulseSource.GenerateImpulse(finalMagnitude); // CinemachineImpulseSource
}
```

### 3. 색각이상 필터 — URP Post-Processing

GitHub의 Colorblindness 패키지가 가장 간편하다 (8가지 유형 지원, URP 호환):

```
// Packages/manifest.json 에 추가
"com.sohne.colorblindness": "https://github.com/SOHNE/Colorblindness.git#upm"
```

직접 셰이더로 구현할 경우 — 색공간 변환 행렬 적용:

```csharp
// 색각이상 필터 행렬값 (Protanopia 예시)
// red: (0.567, 0.433, 0, 0)
// green: (0.558, 0.442, 0, 0)
// blue: (0, 0.242, 0.758, 0)
```

### 4. 텍스트 스케일링

```csharp
[RequireComponent(typeof(TextMeshProUGUI))]
public class AccessibleText : MonoBehaviour
{
    [SerializeField] private float baseSize = 36f;
    private TextMeshProUGUI _tmp;

    private void Awake() => _tmp = GetComponent<TextMeshProUGUI>();
    private void OnEnable() => AccessibilityManager.OnSettingsChanged += Apply;
    private void OnDisable() => AccessibilityManager.OnSettingsChanged -= Apply;
    private void Start() => Apply();

    private void Apply()
    {
        float scale = AccessibilityManager.Instance?.TextScale ?? 1f;
        _tmp.fontSize = baseSize * scale;
    }
}
```

### 5. Assist Mode (Dead Cells / Hades 방식)

```csharp
public class AssistMode : MonoBehaviour
{
    public bool Enabled;
    public float DamageMultiplier = 0.5f; // 받는 데미지 50%
    public bool AutoAim = false;
    public int ExtraLives = 0;            // 로그라이크 특화 — 런 중 부활 횟수

    // PlayerHealth.TakeDamage() 에서 참조
    // damage = Mathf.RoundToInt(damage * (AssistMode.Enabled ? AssistMode.DamageMultiplier : 1f));
}
```

### 6. 접근성 설정 UI

```csharp
public class AccessibilitySettingsUI : MonoBehaviour
{
    [SerializeField] private Slider shakeIntensitySlider;
    [SerializeField] private Toggle shakeToggle;
    [SerializeField] private Slider textScaleSlider;
    [SerializeField] private TMP_Dropdown colorblindDropdown;

    private void Start()
    {
        var a11y = AccessibilityManager.Instance;
        shakeIntensitySlider.value   = a11y.ScreenShakeIntensity;
        shakeToggle.isOn             = a11y.ScreenShakeEnabled;
        textScaleSlider.value        = a11y.TextScale;
        colorblindDropdown.value     = a11y.ColorblindMode;

        shakeIntensitySlider.onValueChanged.AddListener(v => a11y.SetShakeIntensity(v));
        shakeToggle.onValueChanged.AddListener(v => a11y.SetShakeEnabled(v));
        textScaleSlider.onValueChanged.AddListener(v => a11y.SetTextScale(v));
        colorblindDropdown.onValueChanged.AddListener(v => a11y.SetColorblindMode(v));
    }
}
```

## OnionCat 적용 포인트

| 기능 | OnionCat 맥락 | 구현 우선순위 |
|------|--------------|-------------|
| 화면 흔들림 토글/강도 | CinemachineImpulse 이미 사용 중 → 강도 계수만 곱하면 됨 | **즉시 (Phase 1)** |
| 텍스트 크기 | 협력 플레이 시 화면이 복잡 — 큰 텍스트가 중요 | Phase 1 |
| 색각이상 필터 | 고양이(근거리) vs 양파(원거리) 구분이 색상으로 표시될 경우 필수 | Phase 2 |
| Assist Mode | 초보자 친화적 협력 게임 필수 — 데미지 50% 감소로 입문 허들 낮춤 | Phase 2 |
| 컨트롤러 리맵핑 | New Input System 이미 사용 → PerformInteractiveRebinding() API로 쉽게 구현 | Phase 2 |
| 플레이어별 오디오 채널 | P1/P2 사운드 독립 제어 — 한 플레이어가 소리에 민감한 경우 | Phase 3 |

**구현 순서 권장:**
1. `AccessibilityManager` 싱글턴 먼저 구축 (PlayerPrefs 저장/로드)
2. Settings Menu에 탭 추가 — 기존 Settings_Menu.md 참고
3. 화면 흔들림 강도를 FeedbackSystem에 통합
4. 색각이상 필터는 URP Volume Profile에 Post-Process pass로 추가

**중요:** 색각이상 필터를 직접 구현하기보다 GitHub Colorblindness 패키지를 사용하는 것이 시간 대비 효율이 높다.

## 참고 링크

- [Game Accessibility Guidelines](https://gameaccessibilityguidelines.com/full-list/) — 기본/중급/고급 체크리스트
- [GitHub - SOHNE/Colorblindness](https://github.com/SOHNE/Colorblindness) — URP 색각이상 패키지
- [Alan Zucconi - Color Blindness in Games](https://www.alanzucconi.com/2015/12/16/color-blindness/) — 색변환 행렬 수식 설명
- [Dead Cells Breaking Barriers Update](https://www.gamedeveloper.com/design/dead-cells-devs-drop-surprise-accessibility-update) — 인디 Assist Mode 사례
- [Hades Accessibility Report](https://www.familygamingdatabase.com/en-gb/accessibility/Hades) — God Mode 설계 방식
- [Unity PlayerPrefs API](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- [Unity New Input System - Rebinding](https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/ActionBindings.html#interactive-rebinding)
