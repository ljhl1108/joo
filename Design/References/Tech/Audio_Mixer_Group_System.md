# 오디오 믹서 그룹 시스템

리서치 날짜: 2026-07-25

## 개요
Unity의 **Audio Mixer**는 사운드를 채널 그룹(Master/BGM/SFX/Voice)으로 분리하고, 각 채널에 독립적인 볼륨 조절, 이펙트(리버브, 컴프레서), 믹싱을 가능하게 한다. OnionCat에서는 플레이어가 설정 메뉴에서 BGM과 SFX를 개별 조절할 수 있어야 하며, 이를 위한 표준 구현 패턴이다.

---

## Unity 구현 방법

### 1. Audio Mixer Asset 생성

1. Project 창 → Create → Audio Mixer → `MainMixer` 로 명명
2. MainMixer Inspector에서 Group 추가:
   ```
   Master
   ├── BGM         (배경음악)
   ├── SFX         (효과음 - 전투, 발소리 등)
   └── UI          (UI 클릭, 알림 소리)
   ```
   Groups 패널에서 Master 선택 → "+" 버튼으로 하위 그룹 추가

### 2. AudioSource에 Mixer Group 연결

```csharp
// AudioSource Inspector에서 Output 필드에 해당 Mixer Group 드래그
// 또는 코드로:
[SerializeField] private AudioMixerGroup bgmGroup;
[SerializeField] private AudioMixerGroup sfxGroup;

AudioSource bgmSource;
bgmSource.outputAudioMixerGroup = bgmGroup;
```

### 3. 볼륨 노출 파라미터 설정 (핵심)

Audio Mixer Group의 볼륨은 **Exposed Parameter**로 공개해야 코드에서 제어 가능.

1. MainMixer Inspector → Master Group 선택 → Attenuation (볼륨) 옆 톱니바퀴 → **Expose to Script**
2. 파라미터 이름 설정: `MasterVolume`, `BGMVolume`, `SFXVolume`, `UIVolume`
3. 확인: Mixer 창 상단 Exposed Parameters 리스트에 추가됨

### 4. 볼륨 제어 코드

```csharp
using UnityEngine;
using UnityEngine.Audio;

public class AudioManager : MonoBehaviour
{
    public static AudioManager Instance { get; private set; }

    [SerializeField] private AudioMixer mainMixer;

    // 볼륨: 0~1 슬라이더 값 → dB 변환 (로그 스케일)
    // Unity Audio Mixer는 dB 단위 사용 (-80 ~ 0 dB)
    public void SetMasterVolume(float sliderValue)
    {
        mainMixer.SetFloat("MasterVolume", LinearToDecibel(sliderValue));
    }

    public void SetBGMVolume(float sliderValue)
    {
        mainMixer.SetFloat("BGMVolume", LinearToDecibel(sliderValue));
    }

    public void SetSFXVolume(float sliderValue)
    {
        mainMixer.SetFloat("SFXVolume", LinearToDecibel(sliderValue));
    }

    // 선형(0~1) → dB 변환 공식
    // 0이면 -80dB(무음), 1이면 0dB(최대)
    private float LinearToDecibel(float linear)
    {
        return linear > 0.001f ? Mathf.Log10(linear) * 20f : -80f;
    }

    // 설정 저장 (PlayerPrefs 연동)
    public void SaveVolumeSettings()
    {
        mainMixer.GetFloat("MasterVolume", out float master);
        mainMixer.GetFloat("BGMVolume", out float bgm);
        mainMixer.GetFloat("SFXVolume", out float sfx);
        PlayerPrefs.SetFloat("Vol_Master", master);
        PlayerPrefs.SetFloat("Vol_BGM", bgm);
        PlayerPrefs.SetFloat("Vol_SFX", sfx);
        PlayerPrefs.Save();
    }

    // 설정 불러오기
    public void LoadVolumeSettings()
    {
        float master = PlayerPrefs.GetFloat("Vol_Master", 0f);
        float bgm = PlayerPrefs.GetFloat("Vol_BGM", 0f);
        float sfx = PlayerPrefs.GetFloat("Vol_SFX", 0f);
        mainMixer.SetFloat("MasterVolume", master);
        mainMixer.SetFloat("BGMVolume", bgm);
        mainMixer.SetFloat("SFXVolume", sfx);
    }

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        LoadVolumeSettings();
    }
}
```

### 5. UI 슬라이더 연결

```csharp
using UnityEngine;
using UnityEngine.UI;

public class VolumeSlider : MonoBehaviour
{
    [SerializeField] private Slider slider;
    [SerializeField] private VolumeType volumeType;

    public enum VolumeType { Master, BGM, SFX, UI }

    private void Start()
    {
        // 저장된 값 불러와서 슬라이더 초기화
        float savedDb = 0f;
        switch (volumeType)
        {
            case VolumeType.Master:
                AudioManager.Instance.GetMixer().GetFloat("MasterVolume", out savedDb); break;
            case VolumeType.BGM:
                AudioManager.Instance.GetMixer().GetFloat("BGMVolume", out savedDb); break;
            case VolumeType.SFX:
                AudioManager.Instance.GetMixer().GetFloat("SFXVolume", out savedDb); break;
        }
        slider.value = DecibelToLinear(savedDb);
        slider.onValueChanged.AddListener(OnSliderChanged);
    }

    private void OnSliderChanged(float value)
    {
        switch (volumeType)
        {
            case VolumeType.Master: AudioManager.Instance.SetMasterVolume(value); break;
            case VolumeType.BGM: AudioManager.Instance.SetBGMVolume(value); break;
            case VolumeType.SFX: AudioManager.Instance.SetSFXVolume(value); break;
        }
    }

    private float DecibelToLinear(float dB) => Mathf.Pow(10f, dB / 20f);
}
```

---

## 고급 기능: Audio Mixer 이펙트

Mixer Group에 DSP 이펙트를 추가해 사운드 품질 향상:

```
BGM Group에 추가 권장:
- Compressor: 배경음 다이나믹스 줄여서 SFX가 묻히지 않게
- Lowpass: 일시정지 시 배경음 뭉개지게 (게임 분위기 강화)

SFX Group에 추가 권장:
- Duck Volume (Send/Receive): BGM 볼륨을 SFX 발생 시 자동 줄임
```

### 일시정지 시 BGM 뭉개기 (Low-pass 제어)
```csharp
// Pause 시 BGM에 Lowpass 이펙트 점진 적용
public void SetPauseLowpass(bool isPaused)
{
    float targetCutoff = isPaused ? 800f : 22000f;  // 800Hz = 뭉개짐, 22000 = 원음
    StartCoroutine(LerpLowpass(targetCutoff, 0.3f));
}

private IEnumerator LerpLowpass(float target, float duration)
{
    mainMixer.GetFloat("BGMLowpassCutoff", out float current);
    float elapsed = 0f;
    while (elapsed < duration)
    {
        mainMixer.SetFloat("BGMLowpassCutoff", Mathf.Lerp(current, target, elapsed / duration));
        elapsed += Time.unscaledDeltaTime;
        yield return null;
    }
    mainMixer.SetFloat("BGMLowpassCutoff", target);
}
```

---

## 씬 전환 시 BGM 처리

```csharp
// BGM은 DontDestroyOnLoad 오브젝트에서 관리
// 씬 전환 시 페이드 아웃 → 새 씬 페이드 인

public IEnumerator CrossfadeBGM(AudioClip newClip, float fadeTime = 1f)
{
    // 현재 BGM 페이드 아웃
    float startVol = bgmSource.volume;
    for (float t = 0; t < fadeTime; t += Time.deltaTime)
    {
        bgmSource.volume = Mathf.Lerp(startVol, 0f, t / fadeTime);
        yield return null;
    }

    bgmSource.clip = newClip;
    bgmSource.Play();

    // 새 BGM 페이드 인
    for (float t = 0; t < fadeTime; t += Time.deltaTime)
    {
        bgmSource.volume = Mathf.Lerp(0f, startVol, t / fadeTime);
        yield return null;
    }
    bgmSource.volume = startVol;
}
```

---

## OnionCat 적용 포인트

### OnionCat 믹서 구조 제안
```
Master
├── BGM           ← 던전 배경음, 보스 BGM
├── SFX
│   ├── Combat    ← 슬래시, 투사체, 폭발
│   ├── Player    ← 발소리, 대시, 피격음
│   └── Enemy     ← 적 공격, 적 피격, 적 사망
└── UI            ← 메뉴 클릭, 업그레이드 선택 소리
```

Combat/Player/Enemy 그룹 분리로:
- 보스 전투 시 SFX 볼륨 자동 조절 (Duck)
- 개발 중 Enemy SFX만 무음 처리해 디버깅

### PlayerPrefs 키 규칙
```csharp
const string MASTER_KEY = "Vol_Master";
const string BGM_KEY    = "Vol_BGM";
const string SFX_KEY    = "Vol_SFX";
```

### Inspector 설정 필요 항목
- `AudioManager` 오브젝트에 `MainMixer` 드래그 (SerializeField)
- 각 AudioSource 컴포넌트의 Output에 해당 Mixer Group 드래그
- VolumeSlider 컴포넌트에 Slider 및 VolumeType 설정

---

## 참고 링크
- Unity 공식 - Audio Mixer: https://docs.unity3d.com/Manual/AudioMixer.html
- Unity 공식 - Exposed Parameters: https://docs.unity3d.com/Manual/AudioMixerExposedParameters.html
- Unity 공식 - Audio Best Practices: https://docs.unity3d.com/Manual/AudioBestPracticeGuide.html
- 실전 튜토리얼: https://www.youtube.com/results?search_query=unity+audio+mixer+volume+control+tutorial
