# 설정 메뉴 (Settings Menu)

## 개요
설정 메뉴는 게임 완성도의 척도다. 음량 조절, 해상도, 전체화면, 키 리바인딩 4가지가 구현되면 대부분의 플레이어 요구를 커버할 수 있다. OnionCat은 2인 플레이 게임이므로 **두 플레이어의 입력 구성을 각각 설정하는 키 리바인딩**이 특히 중요하다. 설정값은 PlayerPrefs에 저장하여 게임 종료 후에도 유지한다.

---

## Unity 구현 방법

### 1. AudioMixer 기반 음량 조절

**설정 순서:**
1. Project 창 우클릭 → Create → Audio → Audio Mixer 생성 (`MainMixer`)
2. Mixer에 `Master`, `BGM`, `SFX` 그룹 생성
3. `BGM Volume` 파라미터를 `Exposed Parameters`에 등록

```csharp
// AudioSettingsController.cs
using UnityEngine;
using UnityEngine.Audio;
using UnityEngine.UI;

public class AudioSettingsController : MonoBehaviour
{
    [SerializeField] private AudioMixer mainMixer;
    [SerializeField] private Slider bgmSlider;
    [SerializeField] private Slider sfxSlider;

    const string BGM_KEY = "BGMVolume";
    const string SFX_KEY = "SFXVolume";

    void Start()
    {
        bgmSlider.value = PlayerPrefs.GetFloat(BGM_KEY, 1f);
        sfxSlider.value = PlayerPrefs.GetFloat(SFX_KEY, 1f);
        ApplyBGMVolume(bgmSlider.value);
        ApplySFXVolume(sfxSlider.value);

        bgmSlider.onValueChanged.AddListener(ApplyBGMVolume);
        sfxSlider.onValueChanged.AddListener(ApplySFXVolume);
    }

    void ApplyBGMVolume(float value)
    {
        // AudioMixer는 dB 단위 — 0~1 슬라이더를 -80~0dB로 변환
        float dB = value > 0.001f ? Mathf.Log10(value) * 20f : -80f;
        mainMixer.SetFloat("BGMVolume", dB);
        PlayerPrefs.SetFloat(BGM_KEY, value);
    }

    void ApplySFXVolume(float value)
    {
        float dB = value > 0.001f ? Mathf.Log10(value) * 20f : -80f;
        mainMixer.SetFloat("SFXVolume", dB);
        PlayerPrefs.SetFloat(SFX_KEY, value);
    }
}
```

**Inspector 설정 필요:** `mainMixer`, `bgmSlider`, `sfxSlider` 드래그

---

### 2. 해상도 및 전체화면 설정

```csharp
// DisplaySettingsController.cs
using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections.Generic;

public class DisplaySettingsController : MonoBehaviour
{
    [SerializeField] private TMP_Dropdown resolutionDropdown;
    [SerializeField] private Toggle fullscreenToggle;

    private List<Resolution> filteredResolutions = new();
    const string RES_KEY = "ResolutionIndex";
    const string FS_KEY  = "Fullscreen";

    void Start()
    {
        // 중복 해상도 제거 (같은 해상도 다른 주사율 필터링)
        var seen = new HashSet<string>();
        foreach (var r in Screen.resolutions)
        {
            string key = $"{r.width}x{r.height}";
            if (seen.Add(key)) filteredResolutions.Add(r);
        }

        resolutionDropdown.ClearOptions();
        var options = new List<string>();
        int savedIndex = PlayerPrefs.GetInt(RES_KEY, filteredResolutions.Count - 1);

        for (int i = 0; i < filteredResolutions.Count; i++)
            options.Add($"{filteredResolutions[i].width} x {filteredResolutions[i].height}");

        resolutionDropdown.AddOptions(options);
        resolutionDropdown.value = savedIndex;
        resolutionDropdown.RefreshShownValue();

        bool isFullscreen = PlayerPrefs.GetInt(FS_KEY, 1) == 1;
        fullscreenToggle.isOn = isFullscreen;
        Screen.fullScreen = isFullscreen;

        resolutionDropdown.onValueChanged.AddListener(SetResolution);
        fullscreenToggle.onValueChanged.AddListener(SetFullscreen);
    }

    void SetResolution(int index)
    {
        var r = filteredResolutions[index];
        Screen.SetResolution(r.width, r.height, Screen.fullScreen);
        PlayerPrefs.SetInt(RES_KEY, index);
    }

    void SetFullscreen(bool isFullscreen)
    {
        Screen.fullScreen = isFullscreen;
        PlayerPrefs.SetInt(FS_KEY, isFullscreen ? 1 : 0);
    }
}
```

**Inspector 설정 필요:** `resolutionDropdown`, `fullscreenToggle` 드래그

---

### 3. 키 리바인딩 (New Input System)

Unity New Input System의 `InputActionAsset`을 런타임에 재바인딩하는 방법.

```csharp
// KeyRebindingUI.cs
using UnityEngine;
using UnityEngine.InputSystem;
using TMPro;
using UnityEngine.UI;

public class KeyRebindingUI : MonoBehaviour
{
    [SerializeField] private InputActionAsset inputActions;
    [SerializeField] private string actionName;       // 예: "Player1/Attack"
    [SerializeField] private TMP_Text bindingText;
    [SerializeField] private Button rebindButton;

    private InputAction action;
    private InputActionRebindingExtensions.RebindingOperation rebindOp;

    const string BINDINGS_KEY = "InputBindings";

    void Start()
    {
        // 저장된 바인딩 불러오기
        string savedBindings = PlayerPrefs.GetString(BINDINGS_KEY, string.Empty);
        if (!string.IsNullOrEmpty(savedBindings))
            inputActions.LoadBindingOverridesFromJson(savedBindings);

        action = inputActions.FindAction(actionName);
        UpdateBindingText();
        rebindButton.onClick.AddListener(StartRebinding);
    }

    void UpdateBindingText()
    {
        bindingText.text = InputControlPath.ToHumanReadableString(
            action.bindings[0].effectivePath,
            InputControlPath.HumanReadableStringOptions.OmitDevice);
    }

    void StartRebinding()
    {
        bindingText.text = "...";
        action.Disable();

        rebindOp = action.PerformInteractiveRebinding()
            .WithCancelingThrough("<Keyboard>/escape")
            .OnComplete(_ =>
            {
                action.Enable();
                UpdateBindingText();
                // 바인딩 저장
                PlayerPrefs.SetString(BINDINGS_KEY, inputActions.SaveBindingOverridesAsJson());
                rebindOp.Dispose();
            })
            .OnCancel(_ =>
            {
                action.Enable();
                UpdateBindingText();
                rebindOp.Dispose();
            })
            .Start();
    }

    void OnDestroy() => rebindOp?.Dispose();
}
```

**Inspector 설정 필요:**
- `inputActions`에 프로젝트의 InputActionAsset 드래그
- `actionName`에 액션 경로 입력 (예: `"Player1/Attack"`)
- `bindingText`, `rebindButton` 드래그

---

### 4. 설정 메뉴 UI 구조

```
SettingsCanvas
├── Panel_Background
├── Tab_Audio
│   ├── Slider_BGM
│   ├── Slider_SFX
│   └── Text_Labels
├── Tab_Display
│   ├── Dropdown_Resolution
│   └── Toggle_Fullscreen
├── Tab_Controls
│   ├── RebindEntry_P1_Attack
│   ├── RebindEntry_P1_Dash
│   ├── RebindEntry_P2_Fire
│   └── RebindEntry_P2_Shield
└── Button_Close
```

**탭 전환:**
```csharp
public void ShowTab(GameObject tab)
{
    tabAudio.SetActive(false);
    tabDisplay.SetActive(false);
    tabControls.SetActive(false);
    tab.SetActive(true);
}
```

---

### 5. 설정값 초기화

```csharp
public void ResetAllSettings()
{
    PlayerPrefs.DeleteKey("BGMVolume");
    PlayerPrefs.DeleteKey("SFXVolume");
    PlayerPrefs.DeleteKey("ResolutionIndex");
    PlayerPrefs.DeleteKey("Fullscreen");
    PlayerPrefs.DeleteKey("InputBindings");
    inputActions.RemoveAllBindingOverrides();
    // UI 재초기화
    Start();
}
```

---

## OnionCat 적용 포인트

### P1/P2 분리 키 설정
- OnionCat은 2인 플레이어 게임 — `Tab_Controls`에 P1(게임패드/키보드)과 P2(마우스) 섹션 분리
- P1: WASD 이동, 슬래시 버튼, 대시 버튼
- P2: 마우스 조준(고정), 우클릭 방패, 좌클릭 발사 → 마우스 버튼 리바인딩 지원

### 설정 씬 or 팝업 패널
- 메인 메뉴에서 접근하는 씬 방식 OR 일시정지 메뉴에서 팝업으로 여는 방식
- **권장**: 일시정지 메뉴 내 팝업 패널 — 런 중에도 접근 가능

### 픽셀아트 UI 스타일
- Slider, Dropdown, Toggle을 커스텀 픽셀아트 스프라이트로 교체
- Canvas Scaler: `Scale With Screen Size`, Reference Resolution `320x180` 또는 `640x360`

### 구현 우선순위
1. **음량 조절** (가장 필수, 구현 쉬움)
2. **전체화면 토글** (두 번째로 쉽고 중요)
3. **해상도 선택** (드롭다운 조금 복잡)
4. **키 리바인딩** (마지막 — 가장 복잡, 개발 후반에 추가)

---

## 참고 링크
- Unity AudioMixer: https://docs.unity3d.com/Manual/AudioMixer.html
- Screen.SetResolution: https://docs.unity3d.com/ScriptReference/Screen.SetResolution.html
- New Input System Rebinding: https://docs.unity3d.com/Packages/com.unity.inputsystem@1.7/manual/ActionBindings.html#interactive-rebinding
- PlayerPrefs: https://docs.unity3d.com/ScriptReference/PlayerPrefs.html
- 유튜브: "Unity settings menu audio mixer resolution fullscreen tutorial"
