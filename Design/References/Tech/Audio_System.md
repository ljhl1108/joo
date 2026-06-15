# 사운드 시스템 (Audio System)

리서치 날짜: 2026-06-15

## 개요

사운드 시스템은 BGM(배경음악)과 SFX(효과음)를 체계적으로 관리하는 완성 기능 레이어. 없으면 게임이 무음이거나 AudioSource를 난발해 볼륨 관리가 불가능해짐. OnionCat에서는 Cat 슬래시음, Crop 투사체음, 패리 성공음, 보스 BGM 전환, 방 클리어 효과음 등 다양한 오디오 이벤트를 일관되게 처리해야 함.

잘 설계된 오디오 시스템의 특성:
- **싱글턴 AudioManager**로 어디서든 호출 가능
- **AudioMixer**로 BGM / SFX 볼륨 독립 제어 (설정 메뉴 연동)
- **SFX 풀링** — 동시 재생 충돌 없이 여러 효과음 처리
- **BGM 페이드 인/아웃** — 씬 전환·보스 등장 시 자연스러운 전환

---

## Unity 구현 방법

### 1. AudioMixer 설정 (에디터 작업)

1. Project 창 → Create → Audio → Audio Mixer → 이름: `MainMixer`
2. 기본 `Master` 그룹 아래 두 하위 그룹 생성:
   - `BGM` (배경음악)
   - `SFX` (효과음)
3. 각 그룹의 볼륨 파라미터 노출:
   - BGM 그룹 선택 → Inspector → Volume 우클릭 → **Expose to script** → 파라미터명: `BGMVolume`
   - SFX 그룹 동일하게 → 파라미터명: `SFXVolume`

> **유니티 에디터에서 드래그 앤 드롭 설정 필요**: AudioManager의 `[SerializeField] AudioMixer mixer` 필드에 MainMixer 에셋을 드래그.

### 2. AudioManager 싱글턴

```csharp
// AudioManager.cs
using UnityEngine;
using UnityEngine.Audio;
using System.Collections;
using System.Collections.Generic;

public class AudioManager : MonoBehaviour
{
    public static AudioManager Instance { get; private set; }

    [SerializeField] private AudioMixer mixer;
    [SerializeField] private int sfxPoolSize = 10;

    [Header("BGM Sources")]
    [SerializeField] private AudioSource bgmSourceA;  // 교차 페이드용 소스 A
    [SerializeField] private AudioSource bgmSourceB;  // 교차 페이드용 소스 B
    private bool _usingSourceA = true;

    private readonly Queue<AudioSource> _sfxPool = new();

    private void Awake()
    {
        if (Instance != null) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
        InitSFXPool();
        LoadVolumeSettings();
    }

    // ── SFX ──────────────────────────────────────────────

    private void InitSFXPool()
    {
        for (int i = 0; i < sfxPoolSize; i++)
        {
            var src = gameObject.AddComponent<AudioSource>();
            src.outputAudioMixerGroup = mixer.FindMatchingGroups("SFX")[0];
            _sfxPool.Enqueue(src);
        }
    }

    public void PlaySFX(AudioClip clip, float volumeScale = 1f)
    {
        if (clip == null) return;

        // 풀에서 사용 가능한 소스 찾기
        for (int i = 0; i < _sfxPool.Count; i++)
        {
            var src = _sfxPool.Dequeue();
            _sfxPool.Enqueue(src);
            if (!src.isPlaying)
            {
                src.PlayOneShot(clip, volumeScale);
                return;
            }
        }
        // 풀 소진 시 첫 번째 소스 강제 재사용
        var fallback = _sfxPool.Peek();
        fallback.PlayOneShot(clip, volumeScale);
    }

    // 피치 랜덤화 — 같은 효과음 반복 시 단조로움 방지
    public void PlaySFXRandomPitch(AudioClip clip, float minPitch = 0.9f, float maxPitch = 1.1f)
    {
        if (clip == null) return;
        var src = _sfxPool.Dequeue();
        _sfxPool.Enqueue(src);
        src.pitch = Random.Range(minPitch, maxPitch);
        src.PlayOneShot(clip);
        src.pitch = 1f;
    }

    // ── BGM ──────────────────────────────────────────────

    public void PlayBGM(AudioClip clip, float fadeTime = 1f)
    {
        if (clip == null) return;
        StartCoroutine(CrossFadeBGM(clip, fadeTime));
    }

    public void StopBGM(float fadeTime = 1f)
    {
        StartCoroutine(FadeOutBGM(fadeTime));
    }

    private IEnumerator CrossFadeBGM(AudioClip newClip, float fadeTime)
    {
        AudioSource incoming = _usingSourceA ? bgmSourceB : bgmSourceA;
        AudioSource outgoing = _usingSourceA ? bgmSourceA : bgmSourceB;
        _usingSourceA = !_usingSourceA;

        incoming.clip = newClip;
        incoming.volume = 0f;
        incoming.Play();

        float elapsed = 0f;
        while (elapsed < fadeTime)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / fadeTime;
            incoming.volume = t;
            outgoing.volume = 1f - t;
            yield return null;
        }
        outgoing.Stop();
    }

    private IEnumerator FadeOutBGM(float fadeTime)
    {
        AudioSource current = _usingSourceA ? bgmSourceA : bgmSourceB;
        float startVol = current.volume;
        float elapsed = 0f;
        while (elapsed < fadeTime)
        {
            elapsed += Time.deltaTime;
            current.volume = Mathf.Lerp(startVol, 0f, elapsed / fadeTime);
            yield return null;
        }
        current.Stop();
    }

    // ── 볼륨 설정 (PlayerPrefs 연동) ─────────────────────

    public void SetBGMVolume(float sliderValue)
    {
        // AudioMixer는 dB 단위 — 슬라이더 0~1을 dB로 변환
        float dB = sliderValue > 0.001f ? Mathf.Log10(sliderValue) * 20f : -80f;
        mixer.SetFloat("BGMVolume", dB);
        PlayerPrefs.SetFloat("BGMVolume", sliderValue);
    }

    public void SetSFXVolume(float sliderValue)
    {
        float dB = sliderValue > 0.001f ? Mathf.Log10(sliderValue) * 20f : -80f;
        mixer.SetFloat("SFXVolume", dB);
        PlayerPrefs.SetFloat("SFXVolume", sliderValue);
    }

    private void LoadVolumeSettings()
    {
        SetBGMVolume(PlayerPrefs.GetFloat("BGMVolume", 0.8f));
        SetSFXVolume(PlayerPrefs.GetFloat("SFXVolume", 1.0f));
    }
}
```

### 3. SoundLibrary (클립 중앙 관리)

```csharp
// SoundLibrary.cs — ScriptableObject로 클립 목록 관리
using UnityEngine;

[CreateAssetMenu(menuName = "OnionCat/SoundLibrary")]
public class SoundLibrary : ScriptableObject
{
    [Header("Player - Cat")]
    public AudioClip catSlash;
    public AudioClip catDash;
    public AudioClip catFootstep;

    [Header("Player - Crop")]
    public AudioClip cropShoot;
    public AudioClip cropShieldBlock;
    public AudioClip cropParrySuccess;

    [Header("Shared")]
    public AudioClip playerHit;
    public AudioClip playerDeath;

    [Header("Enemy")]
    public AudioClip enemyHit;
    public AudioClip enemyDeath;
    public AudioClip enemyAlert;

    [Header("BGM")]
    public AudioClip mainMenuBGM;
    public AudioClip dungeonBGM;
    public AudioClip bossBGM;
    public AudioClip victoryBGM;

    [Header("UI")]
    public AudioClip uiClick;
    public AudioClip roomClear;
    public AudioClip upgradeSelect;
}
```

> **유니티 에디터에서 드래그 앤 드롭 설정 필요**: SoundLibrary ScriptableObject를 Project에서 생성하고 각 AudioClip 필드에 클립 에셋 할당. AudioManager의 `[SerializeField] SoundLibrary sounds` 필드에 연결.

### 4. 호출 예시

```csharp
// Cat 슬래시 시
AudioManager.Instance.PlaySFXRandomPitch(sounds.catSlash, 0.85f, 1.15f);

// 보스 등장 시 BGM 전환
AudioManager.Instance.PlayBGM(sounds.bossBGM, fadeTime: 2f);

// 방 클리어
AudioManager.Instance.PlaySFX(sounds.roomClear);

// 설정 메뉴 슬라이더 연결
bgmSlider.onValueChanged.AddListener(AudioManager.Instance.SetBGMVolume);
sfxSlider.onValueChanged.AddListener(AudioManager.Instance.SetSFXVolume);
```

### 5. 씬 전환 시 BGM 유지

AudioManager는 `DontDestroyOnLoad`이므로 씬이 바뀌어도 BGM이 끊기지 않음. 새 씬에서 PlayBGM을 호출하면 크로스페이드로 전환.

---

## OnionCat 적용 포인트

### 1. 근접/원거리 사운드 차별화

Cat의 슬래시(저음, 날카로운 찍는 느낌)와 Crop의 투사체(고음, 탁탁탁)는 명확히 다른 음색으로 구분. 플레이어가 화면을 안 봐도 무슨 공격이 나갔는지 소리로 인지 가능해야 함.

### 2. 패리 성공 사운드의 중요성

패리 성공은 게임에서 가장 극적인 순간 중 하나. 높은 피치의 금속음 + 히트스톱(0.05~0.1초 일시정지)과 결합해 만족감 극대화.

```csharp
// 패리 성공 시 히트스톱 + 사운드
StartCoroutine(HitStop(0.07f));
AudioManager.Instance.PlaySFX(sounds.cropParrySuccess);
```

### 3. 적 약점 공격 사운드 피드백

약점 공격(원거리 전용 적에게 근접 → 무효)은 무음 또는 "둔탁한" 소리로 "뭔가 안 먹혔다"를 알림. 약점 타입 일치 시 특별히 크고 선명한 히트음.

| 상황 | 사운드 피드백 |
|-----|------------|
| 약점 공격 성공 | 선명한 히트음 + 짧은 피치업 |
| 무효 타입 공격 | 둔탁한 "퍽" 소리 |
| 패리 성공 | 금속 충격음 + 에코 |
| 플레이어 피격 | 통증음 + 볼륨 일시 덕킹 |

### 4. AudioMixer Duck 기능 (피격 시 BGM 볼륨 자동 감소)

```csharp
// 플레이어 피격 시 BGM 일시 줄이기 (긴장감 강조)
public void DuckBGM(float duration = 0.3f, float duckAmount = -6f)
{
    StartCoroutine(DuckBGMCoroutine(duration, duckAmount));
}

private IEnumerator DuckBGMCoroutine(float duration, float duckAmount)
{
    mixer.GetFloat("BGMVolume", out float originalDB);
    mixer.SetFloat("BGMVolume", originalDB + duckAmount);
    yield return new WaitForSeconds(duration);
    mixer.SetFloat("BGMVolume", originalDB);
}
```

### 5. 보스 BGM 레이어 전환

보스 체력 페이즈에 따라 BGM 강도 변화:
- 체력 100~50%: 조용한 버전
- 체력 50% 이하: 드럼·베이스 추가된 긴장 버전
- Unity AudioMixer의 **Exposed Parameter**로 각 레이어 볼륨 제어

---

## 참고 링크

- Unity 공식 — AudioMixer: https://docs.unity3d.com/Manual/AudioMixer.html
- Unity 공식 — AudioSource.PlayOneShot: https://docs.unity3d.com/ScriptReference/AudioSource.PlayOneShot.html
- Brackeys — Sound Manager Tutorial: https://www.youtube.com/watch?v=6OT43pvUyfY
- Game Audio 설계 강좌 (GDC): https://www.gdcvault.com/play/1015766
- AudioMixer dB 변환 공식: https://gamedevbeginner.com/the-right-way-to-make-a-volume-slider-in-unity-using-logarithms/
- 피치 랜덤화로 효과음 개선: https://johnleonardfrench.com/the-right-way-to-make-a-volume-slider-in-unity/
- 무료 게임 효과음 리소스 (Freesound): https://freesound.org
- 픽셀아트 게임 BGM 레퍼런스 (itch.io): https://itch.io/game-assets/free/tag-music
