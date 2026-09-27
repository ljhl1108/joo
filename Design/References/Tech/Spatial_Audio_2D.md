# 2D 공간 오디오 (Spatial Audio 2D)

리서치 날짜: 2026-09-27

## 개요

Unity의 `AudioSource`는 2D 게임에서도 **거리 감쇠(distance attenuation)**, **방향 감지(stereo panning)**, **존 기반 앰비언스**를 구현할 수 있다. 탑다운 픽셀아트 로그라이크(OnionCat)에서 공간 오디오를 제대로 설정하면 적의 접근, 보물 방, 보스 출현 등이 소리만으로 전달되어 몰입감과 게임플레이 정보밀도가 올라간다.

### 왜 중요한가
- **정보 전달**: 화면 밖 적이 접근할 때 사운드로 알림 → UI 없이 상황 인지
- **피드백 강화**: 원거리 공격의 거리감, 폭발의 원근감
- **두 플레이어 구분**: Cat(근접)과 Onion(원거리) 각각의 행동음에 공간 위치 부여

---

## Unity 구현 방법

### 1. AudioSource 기본 설정

```
Inspector > AudioSource
  Spatial Blend: 1.0 (3D) 으로 설정  ← 핵심
  Spread: 0
  Doppler Level: 0 (탑다운에서는 도플러 끔)
  Min Distance: 2 (유닛 기준)
  Max Distance: 15
  Volume Rolloff: Logarithmic (자연스러운 감쇠)
```

> **주의**: Spatial Blend = 0이면 완전 2D (거리 무관). 1이면 3D 공간 오디오 작동.
> 탑다운에서는 카메라가 Z=−10이고 게임 오브젝트 Z=0이므로 실제 거리는 10유닛 고정.
> → **AudioListener도 Z 위치를 0으로 맞추거나** 별도 보정 필요.

### 2. 탑다운 2D 해결책 — AudioListener를 Camera가 아닌 Player에 붙이기

```csharp
// AudioListener를 카메라에서 제거하고 플레이어에 추가
// Camera: AudioListener 컴포넌트 제거
// Player GameObject: AudioListener 추가

// 또는 스크립트로 리스너 위치를 매 프레임 플레이어 위치 + Z=0으로 강제
public class AudioListenerFollower : MonoBehaviour
{
    [SerializeField] private Transform target;

    void LateUpdate()
    {
        Vector3 pos = target.position;
        pos.z = 0f;
        transform.position = pos;
    }
}
```

### 3. 스테레오 패닝 (방향 감지)

탑다운에서는 Z 깊이가 없어 좌우(X축)만 의미가 있다.

```csharp
// AudioSource의 panStereo를 적 위치 기반으로 직접 제어
public class EnemySoundPanner : MonoBehaviour
{
    private AudioSource audioSource;
    private Transform player;

    void Start()
    {
        audioSource = GetComponent<AudioSource>();
        player = GameObject.FindWithTag("Player").transform;
    }

    void Update()
    {
        float dx = transform.position.x - player.position.x;
        // -1(왼쪽) ~ +1(오른쪽), 최대 범위 10유닛
        audioSource.panStereo = Mathf.Clamp(dx / 10f, -1f, 1f);
    }
}
```

### 4. 거리 감쇠 커스텀 곡선

Inspector에서 `Volume Rolloff`를 `Custom`으로 설정하고 AnimationCurve로 조절.

```csharp
[SerializeField] private AnimationCurve volumeCurve;

void Start()
{
    AudioSource src = GetComponent<AudioSource>();
    src.SetCustomCurve(AudioSourceCurveType.CustomRolloff, volumeCurve);
    src.rolloffMode = AudioRolloffMode.Custom;
}
```

실용 커브 예시:
- 0~3유닛: 1.0 (완전 볼륨)
- 3~8유닛: 1.0 → 0.4 (완만한 하강)
- 8~15유닛: 0.4 → 0.0 (빠른 소멸)

### 5. 오디오 존 (방 앰비언스)

방에 진입/퇴장 시 앰비언스 사운드 전환.

```csharp
public class AudioZone : MonoBehaviour
{
    [SerializeField] private AudioClip ambience;
    [SerializeField] private float fadeTime = 1f;
    private static AudioSource ambienceSource;

    void OnTriggerEnter2D(Collider2D other)
    {
        if (!other.CompareTag("Player")) return;
        if (ambienceSource == null)
            ambienceSource = Camera.main.GetComponent<AudioSource>();
        StartCoroutine(CrossFade(ambience, fadeTime));
    }

    private IEnumerator CrossFade(AudioClip clip, float duration)
    {
        float t = 0f;
        float startVol = ambienceSource.volume;
        while (t < duration / 2f)
        {
            ambienceSource.volume = Mathf.Lerp(startVol, 0f, t / (duration / 2f));
            t += Time.deltaTime;
            yield return null;
        }
        ambienceSource.clip = clip;
        ambienceSource.Play();
        t = 0f;
        while (t < duration / 2f)
        {
            ambienceSource.volume = Mathf.Lerp(0f, startVol, t / (duration / 2f));
            t += Time.deltaTime;
            yield return null;
        }
        ambienceSource.volume = startVol;
    }
}
```

### 6. 사운드 오컬루전 (벽 너머 소리 차단)

```csharp
// 플레이어와 사운드 소스 사이에 Wall 레이어가 있으면 볼륨 감소
public class SoundOcclusion : MonoBehaviour
{
    [SerializeField] private AudioSource audioSource;
    [SerializeField] private LayerMask wallLayer;
    private Transform player;
    private float baseVolume;

    void Start()
    {
        player = GameObject.FindWithTag("Player").transform;
        baseVolume = audioSource.volume;
    }

    void Update()
    {
        Vector2 dir = player.position - transform.position;
        float dist = dir.magnitude;
        RaycastHit2D hit = Physics2D.Raycast(transform.position, dir.normalized, dist, wallLayer);
        audioSource.volume = hit.collider != null ? baseVolume * 0.3f : baseVolume;
    }
}
```

### 7. AudioMixer 그룹 연결

```
Audio Mixer Groups:
  Master
  ├── SFX
  │   ├── Player        ← Cat, Onion 사운드
  │   ├── Enemy         ← 적 이동/공격/경보음
  │   └── Environment   ← 함정, 문, 오브젝트
  └── Music
      ├── BGM
      └── Ambience      ← 방 앰비언스
```

```csharp
[SerializeField] private AudioMixerGroup sfxGroup;
audioSource.outputAudioMixerGroup = sfxGroup;
```

---

## OnionCat 적용 포인트

### 1. AudioListener를 Cat에 붙이기
Cat이 실제 플레이어 위치이므로 AudioListener를 Camera 대신 Cat GameObject에 배치.
Onion은 Cat 뒤에 있으므로 사실상 같은 위치 → 별도 처리 불필요.

### 2. 적 접근 방향음
화면 밖 적이 오른쪽에서 오면 오른쪽 스피커에서 들림 → P1이 조이스틱으로 방향 인지.
`EnemySoundPanner` 스크립트를 Slime 등 적 프리팹에 추가.

### 3. Onion 투사체 거리감
발사한 씨앗이 멀어질수록 소리가 작아짐. `Spatial Blend=1`, `Min Distance=1`, `Max Distance=12`.

### 4. 방 앰비언스 전환
Room_01 (평범한 방): 조용한 바람 소리
Room_Boss: 저주파 위협음 앰비언스
`AudioZone`을 방 입구 Collider2D에 배치.

### 5. 음량 설정 UI 연동
Settings 메뉴에서 AudioMixer의 `SFX` 그룹 볼륨을 슬라이더로 조절.
```csharp
mixer.SetFloat("SFX_Volume", Mathf.Log10(value) * 20);
```

---

## 참고 링크

- [Unity Manual — AudioSource Spatial Blend](https://docs.unity3d.com/Manual/class-AudioSource.html)
- [Unity Manual — AudioMixer](https://docs.unity3d.com/Manual/AudioMixer.html)
- [Unity Learn — Audio in 2D Games](https://learn.unity.com/tutorial/working-with-audio-components)
- [Game Dev Unlocked — Unity 2D Spatial Sound](https://gamedevunlocked.com/2d-spatial-audio-unity/)
- [Brackeys — AUDIO in Unity (YouTube)](https://www.youtube.com/watch?v=6OT43pvUyfY)
